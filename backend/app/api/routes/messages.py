import asyncio
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.api.routes.websocket import manager
from app.api.routes.season_helpers import update_user_task_progress
from app.gigachat_client import gigachat_client
from app.models import (
    ChatMessage,
    ChatMessageCreate,
    ChatMessagePublic,
    ChatMessageUpdate,
    Message,
    User,
    UserPublic,
    BotExecutionResult,
)


router = APIRouter(prefix="/messages", tags=["messages"])
logger = logging.getLogger(__name__)


async def broadcast_message_to_chat(message_public: ChatMessagePublic, chat_id: int):
    """Транслировать сообщение всем участникам чата через WebSocket"""
    # Используем mode='json' для правильной сериализации datetime
    message_dict = message_public.model_dump(mode="json")
    logger.info(f"Broadcasting message {message_dict.get('id')} to chat {chat_id}")
    try:
        await manager.broadcast_to_chat(
            {
                "type": "new_message",
                "message": message_dict,
            },
            chat_id,
        )
        logger.info(f"Message broadcasted successfully")
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")


@router.post("/{chat_id}", response_model=ChatMessagePublic)
async def create_message(
    chat_id: int,
    message_in: ChatMessageCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Создать сообщение в чате"""
    # Проверяем, что пользователь является участником чата
    chat = crud.get_chat(session=session, chat_id=chat_id, user_id=current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Check if it's a bot chat
    is_bot_chat = chat.chat_type == "bot" and chat.bot_id is not None

    try:
        message = crud.create_message(
            session=session,
            chat_id=chat_id,
            sender_id=current_user.id,
            content=message_in.content,
        )

        sender = session.get(User, message.sender_id)
        if sender:
            sender_public = UserPublic(
                id=sender.id,
                email=sender.email,
                full_name=sender.full_name,
                avatar_url=sender.avatar_url,
                is_active=sender.is_active,
                is_superuser=sender.is_superuser,
            )
        else:
            sender_public = None

        message_public = ChatMessagePublic(
            id=message.id,
            chat_id=message.chat_id,
            sender_id=message.sender_id,
            sender=sender_public,
            content=message.content,
            created_at=message.created_at,
            edited_at=message.edited_at,
        )

        # Транслируем сообщение всем участникам чата через WebSocket (не ждем завершения)
        asyncio.create_task(broadcast_message_to_chat(message_public, chat_id))

        # Handle bot response for bot chats
        if is_bot_chat:
            from app.bot_executor import execute_bot
            from app.models import ChatBot

            bot = session.get(ChatBot, chat.bot_id)
            if bot and bot.is_active:
                user_context = {
                    "id": current_user.id,
                    "full_name": current_user.full_name or current_user.email,
                }
                result = execute_bot(
                    bot.code, bot.language, message_in.content, user_context
                )

                # Create bot's response as a message
                bot_response = crud.create_message(
                    session=session,
                    chat_id=chat_id,
                    sender_id=0,  # System user ID for bot
                    content=result.get("response", ""),
                )
                session.commit()  # Commit immediately

                # Broadcast bot response
                bot_message_public = ChatMessagePublic(
                    id=bot_response.id,
                    chat_id=bot_response.chat_id,
                    sender_id=0,
                    sender=None,
                    content=bot_response.content,
                    created_at=bot_response.created_at,
                    edited_at=bot_response.edited_at,
                )
                asyncio.create_task(
                    broadcast_message_to_chat(bot_message_public, chat_id)
                )

        # Обновляем прогресс сезона
        try:
            update_user_task_progress(session, current_user.id, "messages")
        except Exception as e:
            logger.error(f"Error updating season progress: {e}")

        return message_public
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{message_id}", response_model=ChatMessagePublic)
def update_message(
    message_id: int,
    message_in: ChatMessageUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Обновить сообщение"""
    message = crud.update_message(
        session=session,
        message_id=message_id,
        sender_id=current_user.id,
        content=message_in.content,
    )

    if not message:
        raise HTTPException(
            status_code=404, detail="Message not found or you don't have permission"
        )

    sender = session.get(User, message.sender_id)
    if sender:
        sender_public = UserPublic(
            id=sender.id,
            email=sender.email,
            full_name=sender.full_name,
            avatar_url=sender.avatar_url,
            is_active=sender.is_active,
            is_superuser=sender.is_superuser,
        )
    else:
        sender_public = None

    return ChatMessagePublic(
        id=message.id,
        chat_id=message.chat_id,
        sender_id=message.sender_id,
        sender=sender_public,
        content=message.content,
        created_at=message.created_at,
        edited_at=message.edited_at,
    )


@router.delete("/{message_id}", response_model=Message)
def delete_message(
    message_id: int, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Удалить сообщение (автор или админ группы)"""
    success = crud.delete_message(
        session=session, message_id=message_id, user_id=current_user.id
    )

    if not success:
        success = crud.delete_any_message(
            session=session, message_id=message_id, current_user_id=current_user.id
        )

    if not success:
        raise HTTPException(
            status_code=404, detail="Message not found or you don't have permission"
        )

    return Message(message="Message deleted successfully")


@router.post("/{chat_id}/read")
async def mark_messages_as_read(
    chat_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Отметить сообщения как прочитанные"""
    from sqlmodel import select
    from app.models import ChatMessage

    chat = crud.get_chat(session=session, chat_id=chat_id, user_id=current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages = session.exec(
        select(ChatMessage).where(
            ChatMessage.chat_id == chat_id,
            ChatMessage.sender_id != current_user.id,
            ChatMessage.is_read == False,
        )
    ).all()

    for message in messages:
        message.is_read = True
        session.add(message)
    session.commit()

    return {"status": "ok", "count": len(messages)}


class AIChatRequest(BaseModel):
    message: str


@router.post("/ai/chat")
async def chat_with_ai(
    request: AIChatRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> BotExecutionResult:
    """Отправить сообщение GigaChat AI"""
    response = gigachat_client.chat(request.message)
    return BotExecutionResult(response=response)

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.deps import CurrentUser, SessionDep
from app.bot_executor import execute_bot
from app.models import (
    ChatBot,
    ChatBotCreate,
    ChatBotPublic,
    ChatBotUpdate,
    BotExecutionResult,
    User,
    Chat,
    ChatMember,
)
from app.gigachat_client import gigachat_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bots", tags=["bots"])


@router.get("/", response_model=list[ChatBotPublic])
def get_my_bots(session: SessionDep, current_user: CurrentUser) -> list[ChatBot]:
    """Get all bots owned by current user"""
    statement = select(ChatBot).where(ChatBot.owner_id == current_user.id)
    bots = session.exec(statement).all()
    return bots


@router.get("/all")
def get_all_bots(session: SessionDep) -> list[ChatBotPublic]:
    """Get all public bots"""
    statement = select(ChatBot).where(ChatBot.is_active == True)
    bots = session.exec(statement).all()
    return bots


@router.get("/search")
def search_bots(session: SessionDep, q: str = "") -> list[ChatBotPublic]:
    """Search all bots by name (returns public bots and user's own bots)"""
    if not q.strip():
        return []
    from app.api.deps import get_current_user

    # For now return all active bots matching query
    # In production you'd filter by owner_id for private bots
    statement = select(ChatBot).where(
        ChatBot.name.ilike(f"%{q}%"), ChatBot.is_active == True
    )
    bots = session.exec(statement).all()
    return bots


@router.post("/", response_model=ChatBotPublic)
def create_bot(
    bot_in: ChatBotCreate, session: SessionDep, current_user: CurrentUser
) -> ChatBot:
    """Create a new bot"""
    bot = ChatBot(
        owner_id=current_user.id,
        name=bot_in.name,
        description=bot_in.description,
        avatar_url=bot_in.avatar_url,
        code=bot_in.code,
        language=bot_in.language,
        is_public=bot_in.is_public,
    )
    session.add(bot)
    session.commit()
    session.refresh(bot)
    return bot


@router.get("/{bot_id}", response_model=ChatBotPublic)
def get_bot(bot_id: int, session: SessionDep, current_user: CurrentUser) -> ChatBot:
    """Get a specific bot"""
    bot = session.get(ChatBot, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    if bot.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return bot


@router.patch("/{bot_id}", response_model=ChatBotPublic)
def update_bot(
    bot_id: int,
    bot_update: ChatBotUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> ChatBot:
    """Update a bot"""
    bot = session.get(ChatBot, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    if bot.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = bot_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(bot, key, value)

    session.add(bot)
    session.commit()
    session.refresh(bot)
    return bot


@router.delete("/{bot_id}")
def delete_bot(bot_id: int, session: SessionDep, current_user: CurrentUser) -> dict:
    """Delete a bot"""
    bot = session.get(ChatBot, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    if bot.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    session.delete(bot)
    session.commit()
    return {"message": "Bot deleted"}


@router.post("/{bot_id}/test", response_model=BotExecutionResult)
def test_bot(
    bot_id: int, test_message: str, session: SessionDep, current_user: CurrentUser
) -> BotExecutionResult:
    """Test bot with a message"""
    bot = session.get(ChatBot, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    if bot.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    user_context = {
        "id": current_user.id,
        "full_name": current_user.full_name or current_user.email,
    }

    result = execute_bot(bot.code, bot.language, test_message, user_context)
    return BotExecutionResult(**result)


class SendToBotRequest(BaseModel):
    message: str


@router.post("/chat/{bot_id}", response_model=BotExecutionResult)
def chat_with_bot(
    bot_id: int,
    request: SendToBotRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> BotExecutionResult:
    """Send a message to a bot (creates a chat with the bot)"""
    bot = session.get(ChatBot, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    if not bot.is_active:
        raise HTTPException(status_code=400, detail="Bot is inactive")

    # Check access for private bots
    if not bot.is_public and bot.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bot is private")

    user_context = {
        "id": current_user.id,
        "full_name": current_user.full_name or current_user.email,
    }

    result = execute_bot(bot.code, bot.language, request.message, user_context)
    return BotExecutionResult(**result)


@router.post("/chats/{bot_id}")
def create_bot_chat(
    bot_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    """Create or get a chat with a bot"""
    bot = session.get(ChatBot, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    if not bot.is_active:
        raise HTTPException(status_code=400, detail="Bot is inactive")

    if not bot.is_public and bot.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bot is private")

    # Find existing bot chat or create new one
    from sqlmodel import select

    statement = select(Chat).where(Chat.chat_type == "bot", Chat.bot_id == bot_id)
    existing_chats = session.exec(statement).all()

    # Find chat where current user is member
    user_chat = None
    for chat in existing_chats:
        member_stmt = select(ChatMember).where(
            ChatMember.chat_id == chat.id, ChatMember.user_id == current_user.id
        )
        member = session.exec(member_stmt).first()
        if member:
            user_chat = chat
            break

    if user_chat:
        return {"chat_id": user_chat.id}

    # Create new chat
    new_chat = Chat(chat_type="bot", name=bot.name, bot_id=bot_id)
    session.add(new_chat)
    session.flush()

    # Add user as member
    member = ChatMember(chat_id=new_chat.id, user_id=current_user.id, role="member")
    session.add(member)
    session.commit()
    session.refresh(new_chat)

    return {"chat_id": new_chat.id}

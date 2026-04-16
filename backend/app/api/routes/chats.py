from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.api.routes.season_helpers import update_user_task_progress
from app.models import (
    Chat,
    ChatAddMembers,
    ChatBot,
    ChatBotPublic,
    ChatCreate,
    ChatMember,
    ChatMemberPublic,
    ChatMessage,
    ChatMessagePublic,
    ChatMessagesPublic,
    ChatPublic,
    ChatRoleUpdate,
    ChatsPublic,
    Message,
    User,
    UserPublic,
)

router = APIRouter(prefix="/chats", tags=["chats"])


def _format_chat_public(
    chat: Chat, current_user_id: int, session: SessionDep
) -> ChatPublic:
    """Форматирует чат для API ответа"""
    # Получаем участников
    members_stmt = select(ChatMember).where(ChatMember.chat_id == chat.id)
    members = list(session.exec(members_stmt).all())

    # Для приватного чата определяем собеседника
    chat_name = chat.name
    if chat.chat_type == "private" and not chat_name:
        for member in members:
            if member.user_id != current_user_id:
                user = session.get(User, member.user_id)
                if user:
                    chat_name = user.full_name or user.email

    # Получаем последнее сообщение
    last_msg_stmt = (
        select(ChatMessage)
        .where(ChatMessage.chat_id == chat.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(1)
    )
    last_message = session.exec(last_msg_stmt).first()

    # Форматируем участников
    members_public = []
    for member in members:
        user = session.get(User, member.user_id)
        if user:
            members_public.append(
                ChatMemberPublic(
                    id=member.id,
                    user_id=member.user_id,
                    role=member.role,
                    user=UserPublic(
                        id=user.id,
                        email=user.email,
                        full_name=user.full_name,
                        avatar_url=user.avatar_url,
                        is_active=user.is_active,
                        is_superuser=user.is_superuser,
                        balance=user.balance,
                        is_banned=user.is_banned,
                        ban_reason=user.ban_reason,
                        timezone=user.timezone,
                        last_seen=user.last_seen,
                        is_online=False,
                        is_ultra=getattr(user, "is_ultra", False),
                        ultra_expires_at=getattr(user, "ultra_expires_at", None),
                        ultra_badge=getattr(user, "ultra_badge", None),
                    ),
                    joined_at=member.joined_at,
                    last_read_at=member.last_read_at,
                )
            )

    # Получаем sender для last_message
    last_message_sender = None
    if last_message:
        sender_user = session.get(User, last_message.sender_id)
        if sender_user:
            last_message_sender = UserPublic(
                id=sender_user.id,
                email=sender_user.email,
                full_name=sender_user.full_name,
                avatar_url=sender_user.avatar_url,
                is_active=sender_user.is_active,
                is_superuser=sender_user.is_superuser,
                balance=sender_user.balance,
                is_banned=sender_user.is_banned,
                ban_reason=sender_user.ban_reason,
                timezone=sender_user.timezone,
                last_seen=sender_user.last_seen,
                is_online=False,
                is_ultra=getattr(sender_user, "is_ultra", False),
                ultra_expires_at=getattr(sender_user, "ultra_expires_at", None),
                ultra_badge=getattr(sender_user, "ultra_badge", None),
            )

    # Get bot info for bot chats
    bot_data = None
    if chat.chat_type == "bot" and chat.bot_id:
        bot = session.get(ChatBot, chat.bot_id)
        if bot:
            bot_data = ChatBotPublic(
                id=bot.id,
                owner_id=bot.owner_id,
                name=bot.name,
                description=bot.description,
                avatar_url=bot.avatar_url,
                language=bot.language,
                is_active=bot.is_active,
                is_public=bot.is_public,
                created_at=bot.created_at,
                updated_at=bot.updated_at,
            )

    return ChatPublic(
        id=chat.id,
        chat_type=chat.chat_type,
        name=chat_name,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        members=members_public,
        last_message=(
            ChatMessagePublic(
                id=last_message.id,
                chat_id=last_message.chat_id,
                sender_id=last_message.sender_id,
                sender=last_message_sender,
                content=last_message.content,
                created_at=last_message.created_at,
                edited_at=last_message.edited_at,
            )
            if last_message
            else None
        ),
        bot=bot_data,
    )


@router.get("/", response_model=ChatsPublic)
def get_chats(session: SessionDep, current_user: CurrentUser) -> Any:
    """Получить все чаты текущего пользователя"""
    chats = crud.get_user_chats(session=session, user_id=current_user.id)

    chats_public = []
    for chat in chats:
        chats_public.append(_format_chat_public(chat, current_user.id, session))

    return ChatsPublic(data=chats_public, count=len(chats_public))


@router.get("/{chat_id}", response_model=ChatPublic)
def get_chat(chat_id: int, session: SessionDep, current_user: CurrentUser) -> Any:
    """Получить конкретный чат"""
    chat = crud.get_chat(session=session, chat_id=chat_id, user_id=current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    return _format_chat_public(chat, current_user.id, session)


@router.post("/private/{user_id}", response_model=ChatPublic)
def create_or_get_private_chat(
    user_id: int, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Создать или получить приватный чат с пользователем"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot create chat with yourself")

    # Проверяем, что пользователь существует
    target_user = session.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    chat = crud.get_or_create_private_chat(
        session=session,
        user1_id=current_user.id,
        user2_id=user_id,
    )

    return _format_chat_public(chat, current_user.id, session)


@router.post("/group", response_model=ChatPublic)
def create_group_chat(
    chat_in: ChatCreate, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Создать групповой чат"""
    if chat_in.chat_type != "group":
        raise HTTPException(
            status_code=400, detail="Use /private/{user_id} for private chats"
        )

    if not chat_in.name:
        raise HTTPException(status_code=400, detail="Group chat name is required")

    if not chat_in.member_ids:
        raise HTTPException(status_code=400, detail="At least one member is required")

    # Проверяем, что все пользователи существуют
    for user_id in chat_in.member_ids:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    chat = crud.create_group_chat(
        session=session,
        creator_id=current_user.id,
        name=chat_in.name,
        member_ids=chat_in.member_ids,
    )

    try:
        update_user_task_progress(session, current_user.id, "chats")
    except:
        pass

    return _format_chat_public(chat, current_user.id, session)


@router.post("/{chat_id}/members", response_model=ChatPublic)
def add_members_to_group(
    chat_id: int,
    members_in: ChatAddMembers,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Добавить участников в групповой чат"""
    chat = crud.get_chat(session=session, chat_id=chat_id, user_id=current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if chat.chat_type != "group":
        raise HTTPException(
            status_code=400, detail="Can only add members to group chats"
        )

    # Проверяем, что все пользователи существуют
    for user_id in members_in.member_ids:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    updated_chat = crud.add_members_to_group_chat(
        session=session,
        chat_id=chat_id,
        member_ids=members_in.member_ids,
        current_user_id=current_user.id,
    )

    if not updated_chat:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to add members to this chat",
        )

    return _format_chat_public(updated_chat, current_user.id, session)


@router.post("/{chat_id}/read", response_model=Message)
def mark_chat_read(chat_id: int, session: SessionDep, current_user: CurrentUser) -> Any:
    """Отметить чат как прочитанный"""
    chat = crud.get_chat(session=session, chat_id=chat_id, user_id=current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    crud.mark_chat_as_read(session=session, chat_id=chat_id, user_id=current_user.id)
    return Message(message="Chat marked as read")


@router.get("/{chat_id}/messages", response_model=ChatMessagesPublic)
def get_messages(
    chat_id: int,
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 50,
) -> Any:
    """Получить сообщения чата"""
    chat = crud.get_chat(session=session, chat_id=chat_id, user_id=current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages = crud.get_chat_messages(
        session=session,
        chat_id=chat_id,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )

    messages_public = []
    for msg in messages:
        sender = session.get(User, msg.sender_id)
        if sender:
            sender_public = UserPublic(
                id=sender.id,
                email=sender.email,
                full_name=sender.full_name,
                avatar_url=sender.avatar_url,
                is_active=sender.is_active,
                is_superuser=sender.is_superuser,
                balance=sender.balance,
                is_banned=sender.is_banned,
                ban_reason=sender.ban_reason,
                timezone=sender.timezone,
                last_seen=sender.last_seen,
                is_online=False,
                is_ultra=getattr(sender, "is_ultra", False),
                ultra_expires_at=getattr(sender, "ultra_expires_at", None),
                ultra_badge=getattr(sender, "ultra_badge", None),
            )
        else:
            sender_public = None
        messages_public.append(
            ChatMessagePublic(
                id=msg.id,
                chat_id=msg.chat_id,
                sender_id=msg.sender_id,
                sender=sender_public,
                content=msg.content,
                media_type=msg.media_type,
                media_filename=msg.media_filename,
                media_url=msg.media_url,
                media_size=msg.media_size,
                created_at=msg.created_at,
                edited_at=msg.edited_at,
            )
        )

    return ChatMessagesPublic(data=messages_public, count=len(messages_public))


@router.patch("/{chat_id}/members/{member_id}/role", response_model=ChatMemberPublic)
def update_member_role(
    chat_id: int,
    member_id: int,
    role_in: ChatRoleUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Изменить роль участника (только админ)"""
    chat = crud.get_chat(session=session, chat_id=chat_id, user_id=current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if chat.chat_type != "group":
        raise HTTPException(
            status_code=400, detail="Roles only available in group chats"
        )

    member = crud.set_member_role(
        session=session,
        chat_id=chat_id,
        member_id=member_id,
        role=role_in.role,
        current_user_id=current_user.id,
    )

    if not member:
        raise HTTPException(
            status_code=403, detail="You don't have permission or member not found"
        )

    user = session.get(User, member.user_id)
    if user:
        user_public = UserPublic(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
        )
    else:
        user_public = None

    return ChatMemberPublic(
        id=member.id,
        user_id=member.user_id,
        role=member.role,
        user=user_public,
        joined_at=member.joined_at,
        last_read_at=member.last_read_at,
    )


@router.delete("/{chat_id}/members/{member_id}", response_model=Message)
def remove_chat_member(
    chat_id: int,
    member_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Удалить участника из чата (только админ)"""
    chat = crud.get_chat(session=session, chat_id=chat_id, user_id=current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if chat.chat_type != "group":
        raise HTTPException(status_code=400, detail="Only available in group chats")

    success = crud.remove_member(
        session=session,
        chat_id=chat_id,
        member_id=member_id,
        current_user_id=current_user.id,
    )

    if not success:
        raise HTTPException(
            status_code=403, detail="You don't have permission or member not found"
        )

    return Message(message="Member removed successfully")


@router.post("/{chat_id}/leave", response_model=Message)
def leave_group_chat(
    chat_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Покинуть групповой чат"""
    chat = crud.get_chat(session=session, chat_id=chat_id, user_id=current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if chat.chat_type != "group":
        raise HTTPException(status_code=400, detail="Only available in group chats")

    success = crud.leave_chat(session=session, chat_id=chat_id, user_id=current_user.id)

    if not success:
        raise HTTPException(status_code=400, detail="Failed to leave chat")

    return Message(message="Left chat successfully")


@router.patch("/{chat_id}/name", response_model=ChatPublic)
def update_chat_name(
    chat_id: int,
    session: SessionDep,
    current_user: CurrentUser,
    body: dict,
) -> Any:
    """Изменить название группы (только админ)"""
    name = body.get("name", "")
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")

    chat = crud.get_chat(session=session, chat_id=chat_id, user_id=current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if chat.chat_type != "group":
        raise HTTPException(status_code=400, detail="Only available in group chats")

    updated_chat = crud.update_chat_name(
        session=session,
        chat_id=chat_id,
        name=name,
        current_user_id=current_user.id,
    )

    if not updated_chat:
        raise HTTPException(status_code=403, detail="Only admins can change group name")

    return _format_chat_public(updated_chat, current_user.id, session)

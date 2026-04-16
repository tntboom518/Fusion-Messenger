from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, and_

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Channel,
    ChannelAdmin,
    ChannelPost,
    ChannelCreate,
    ChannelPostCreate,
    ChannelAddAdmin,
    ChannelPublic,
    ChannelPostPublic,
    ChannelsPublic,
    ChannelPostsPublic,
    UserPublic,
)

router = APIRouter(prefix="/channels", tags=["channels"])


def is_channel_admin(session: Session, channel_id: int, user_id: int) -> bool:
    """Проверить, является ли пользователь админом канала"""
    channel = session.get(Channel, channel_id)
    if not channel:
        return False
    if channel.creator_id == user_id:
        return True
    admin = session.exec(
        select(ChannelAdmin).where(
            and_(ChannelAdmin.channel_id == channel_id, ChannelAdmin.user_id == user_id)
        )
    ).first()
    return admin is not None


@router.get("", response_model=ChannelsPublic)
def get_channels(
    session: SessionDep,
    current_user: CurrentUser,
    limit: int = Query(default=20, le=50),
    offset: int = Query(default=0, ge=0),
):
    """Получить все публичные каналы"""
    statement = (
        select(Channel)
        .where(Channel.is_public == True)
        .order_by(Channel.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    channels = session.exec(statement).all()

    result = []
    for ch in channels:
        is_admin = is_channel_admin(session, ch.id, current_user.id)
        result.append(
            ChannelPublic(
                id=ch.id,
                creator_id=ch.creator_id,
                creator=UserPublic(
                    id=ch.creator.id,
                    email=ch.creator.email,
                    full_name=ch.creator.full_name,
                    is_active=ch.creator.is_active,
                    is_superuser=ch.creator.is_superuser,
                    avatar_url=ch.creator.avatar_url,
                    balance=ch.creator.balance,
                    is_banned=ch.creator.is_banned,
                    ban_reason=ch.creator.ban_reason,
                    timezone=ch.creator.timezone,
                    last_seen=ch.creator.last_seen,
                    is_online=False,
                ),
                name=ch.name,
                description=ch.description,
                avatar_url=ch.avatar_url,
                is_public=ch.is_public,
                created_at=ch.created_at,
                is_admin=is_admin,
                is_creator=ch.creator_id == current_user.id,
            )
        )

    return ChannelsPublic(data=result, count=len(result))


@router.get("/my", response_model=ChannelsPublic)
def get_my_channels(
    session: SessionDep,
    current_user: CurrentUser,
):
    """Получить каналы, где пользователь админ или создатель"""
    created = session.exec(
        select(Channel).where(Channel.creator_id == current_user.id)
    ).all()

    admin_channels = session.exec(
        select(Channel)
        .join(ChannelAdmin)
        .where(ChannelAdmin.user_id == current_user.id)
    ).all()

    channels = {ch.id: ch for ch in created + admin_channels}.values()

    result = []
    for ch in channels:
        result.append(
            ChannelPublic(
                id=ch.id,
                creator_id=ch.creator_id,
                creator=UserPublic(
                    id=ch.creator.id,
                    email=ch.creator.email,
                    full_name=ch.creator.full_name,
                    is_active=ch.creator.is_active,
                    is_superuser=ch.creator.is_superuser,
                    avatar_url=ch.creator.avatar_url,
                    balance=ch.creator.balance,
                    is_banned=ch.creator.is_banned,
                    ban_reason=ch.creator.ban_reason,
                    timezone=ch.creator.timezone,
                    last_seen=ch.creator.last_seen,
                    is_online=False,
                ),
                name=ch.name,
                description=ch.description,
                avatar_url=ch.avatar_url,
                is_public=ch.is_public,
                created_at=ch.created_at,
                is_admin=True,
                is_creator=ch.creator_id == current_user.id,
            )
        )

    return ChannelsPublic(data=result, count=len(result))


@router.get("/{channel_id}", response_model=ChannelPublic)
def get_channel(channel_id: int, session: SessionDep, current_user: CurrentUser):
    """Получить информацию о канале"""
    channel = session.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Канал не найден")

    is_admin = is_channel_admin(session, channel_id, current_user.id)

    return ChannelPublic(
        id=channel.id,
        creator_id=channel.creator_id,
        creator=UserPublic(
            id=channel.creator.id,
            email=channel.creator.email,
            full_name=channel.creator.full_name,
            is_active=channel.creator.is_active,
            is_superuser=channel.creator.is_superuser,
            avatar_url=channel.creator.avatar_url,
            balance=channel.creator.balance,
            is_banned=channel.creator.is_banned,
            ban_reason=channel.creator.ban_reason,
            timezone=channel.creator.timezone,
            last_seen=channel.creator.last_seen,
            is_online=False,
        ),
        name=channel.name,
        description=channel.description,
        avatar_url=channel.avatar_url,
        is_public=channel.is_public,
        created_at=channel.created_at,
        is_admin=is_admin,
        is_creator=channel.creator_id == current_user.id,
    )


@router.post("", response_model=ChannelPublic)
def create_channel(
    channel_data: ChannelCreate,
    session: SessionDep,
    current_user: CurrentUser,
):
    """Создать канал"""
    channel = Channel(
        creator_id=current_user.id,
        name=channel_data.name,
        description=channel_data.description,
        avatar_url=channel_data.avatar_url,
        is_public=channel_data.is_public,
    )
    session.add(channel)
    session.commit()
    session.refresh(channel)

    return ChannelPublic(
        id=channel.id,
        creator_id=channel.creator_id,
        creator=UserPublic(
            id=current_user.id,
            email=current_user.email,
            full_name=current_user.full_name,
            is_active=current_user.is_active,
            is_superuser=current_user.is_superuser,
            avatar_url=current_user.avatar_url,
            balance=current_user.balance,
            is_banned=current_user.is_banned,
            ban_reason=current_user.ban_reason,
            timezone=current_user.timezone,
            last_seen=current_user.last_seen,
            is_online=False,
        ),
        name=channel.name,
        description=channel.description,
        avatar_url=channel.avatar_url,
        is_public=channel.is_public,
        created_at=channel.created_at,
        is_admin=True,
        is_creator=True,
    )


@router.delete("/{channel_id}")
def delete_channel(channel_id: int, session: SessionDep, current_user: CurrentUser):
    """Удалить канал (только создатель)"""
    channel = session.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Канал не найден")

    if channel.creator_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Нет прав")

    session.delete(channel)
    session.commit()
    return {"ok": True}


@router.post("/{channel_id}/admins", response_model=ChannelPublic)
def add_admin(
    channel_id: int,
    admin_data: ChannelAddAdmin,
    session: SessionDep,
    current_user: CurrentUser,
):
    """Добавить админа канала (только создатель)"""
    channel = session.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Канал не найден")

    if channel.creator_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Только создатель может добавлять админов"
        )

    # Проверяем, что пользователь существует
    from app.models import User

    user = session.get(User, admin_data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Проверяем, что уже не админ
    existing = session.exec(
        select(ChannelAdmin).where(
            and_(
                ChannelAdmin.channel_id == channel_id,
                ChannelAdmin.user_id == admin_data.user_id,
            )
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Пользователь уже админ канала")

    admin = ChannelAdmin(channel_id=channel_id, user_id=admin_data.user_id)
    session.add(admin)
    session.commit()

    return ChannelPublic(
        id=channel.id,
        creator_id=channel.creator_id,
        creator=UserPublic(
            id=channel.creator.id,
            email=channel.creator.email,
            full_name=channel.creator.full_name,
            is_active=channel.creator.is_active,
            is_superuser=channel.creator.is_superuser,
            avatar_url=channel.creator.avatar_url,
            balance=channel.creator.balance,
            is_banned=channel.creator.is_banned,
            ban_reason=channel.creator.ban_reason,
            timezone=channel.creator.timezone,
            last_seen=channel.creator.last_seen,
            is_online=False,
        ),
        name=channel.name,
        description=channel.description,
        avatar_url=channel.avatar_url,
        is_public=channel.is_public,
        created_at=channel.created_at,
        is_admin=True,
        is_creator=True,
    )


@router.delete("/{channel_id}/admins/{user_id}", response_model=ChannelPublic)
def remove_admin(
    channel_id: int,
    user_id: int,
    session: SessionDep,
    current_user: CurrentUser,
):
    """Удалить админа канала (только создатель)"""
    channel = session.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Канал не найден")

    if channel.creator_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Только создатель может удалять админов"
        )

    admin = session.exec(
        select(ChannelAdmin).where(
            and_(ChannelAdmin.channel_id == channel_id, ChannelAdmin.user_id == user_id)
        )
    ).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Админ не найден")

    session.delete(admin)
    session.commit()

    return ChannelPublic(
        id=channel.id,
        creator_id=channel.creator_id,
        creator=UserPublic(
            id=channel.creator.id,
            email=channel.creator.email,
            full_name=channel.creator.full_name,
            is_active=channel.creator.is_active,
            is_superuser=channel.creator.is_superuser,
            avatar_url=channel.creator.avatar_url,
            balance=channel.creator.balance,
            is_banned=channel.creator.is_banned,
            ban_reason=channel.creator.ban_reason,
            timezone=channel.creator.timezone,
            last_seen=channel.creator.last_seen,
            is_online=False,
        ),
        name=channel.name,
        description=channel.description,
        avatar_url=channel.avatar_url,
        is_public=channel.is_public,
        created_at=channel.created_at,
        is_admin=True,
        is_creator=True,
    )


@router.get("/{channel_id}/posts", response_model=ChannelPostsPublic)
def get_channel_posts(
    channel_id: int,
    session: SessionDep,
    current_user: CurrentUser,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Получить посты канала"""
    channel = session.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Канал не найден")

    statement = (
        select(ChannelPost)
        .where(ChannelPost.channel_id == channel_id)
        .order_by(ChannelPost.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    posts = session.exec(statement).all()

    result = []
    for post in posts:
        result.append(
            ChannelPostPublic(
                id=post.id,
                channel_id=post.channel_id,
                author_id=post.author_id,
                author=UserPublic(
                    id=post.author.id,
                    email=post.author.email,
                    full_name=post.author.full_name,
                    is_active=post.author.is_active,
                    is_superuser=post.author.is_superuser,
                    avatar_url=post.author.avatar_url,
                    balance=post.author.balance,
                    is_banned=post.author.is_banned,
                    ban_reason=post.author.ban_reason,
                    timezone=post.author.timezone,
                    last_seen=post.author.last_seen,
                    is_online=False,
                ),
                content=post.content,
                media_type=post.media_type,
                media_url=post.media_url,
                media_filename=post.media_filename,
                created_at=post.created_at,
            )
        )

    return ChannelPostsPublic(data=result, count=len(result))


@router.post("/{channel_id}/posts", response_model=ChannelPostPublic)
def create_channel_post(
    channel_id: int,
    post_data: ChannelPostCreate,
    session: SessionDep,
    current_user: CurrentUser,
):
    """Создать пост в канале (только создатель и админы)"""
    channel = session.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Канал не найден")

    if not is_channel_admin(session, channel_id, current_user.id):
        raise HTTPException(status_code=403, detail="Нет прав писать в канал")

    post = ChannelPost(
        channel_id=channel_id,
        author_id=current_user.id,
        content=post_data.content,
        media_type=post_data.media_type,
        media_url=post_data.media_url,
        media_filename=post_data.media_filename,
    )
    session.add(post)
    session.commit()
    session.refresh(post)

    return ChannelPostPublic(
        id=post.id,
        channel_id=post.channel_id,
        author_id=post.author_id,
        author=UserPublic(
            id=current_user.id,
            email=current_user.email,
            full_name=current_user.full_name,
            is_active=current_user.is_active,
            is_superuser=current_user.is_superuser,
            avatar_url=current_user.avatar_url,
            balance=current_user.balance,
            is_banned=current_user.is_banned,
            ban_reason=current_user.ban_reason,
            timezone=current_user.timezone,
            last_seen=current_user.last_seen,
            is_online=False,
        ),
        content=post.content,
        media_type=post.media_type,
        media_url=post.media_url,
        media_filename=post.media_filename,
        created_at=post.created_at,
    )


@router.delete("/posts/{post_id}")
def delete_channel_post(post_id: int, session: SessionDep, current_user: CurrentUser):
    """Удалить пост канала (только автор или админ канала)"""
    post = session.get(ChannelPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")

    if post.author_id != current_user.id and not is_channel_admin(
        session, post.channel_id, current_user.id
    ):
        raise HTTPException(status_code=403, detail="Нет прав")

    session.delete(post)
    session.commit()
    return {"ok": True}

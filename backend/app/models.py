from datetime import datetime, timezone
from typing import Literal

from pydantic import EmailStr
from sqlmodel import Column, DateTime, Field, Integer, Relationship, SQLModel, func


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: int | None = Field(
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    hashed_password: str
    avatar_url: str | None = Field(default=None, max_length=500)
    balance: int = Field(default=100)  # Шекели
    is_banned: bool = Field(default=False)
    ban_reason: str | None = Field(default=None, max_length=500)
    timezone: str = Field(default="UTC", max_length=50)
    last_seen: datetime | None = Field(default=None)
    is_ultra: bool = Field(default=False)  # Подписка Ultra
    ultra_expires_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, nullable=True)
    )
    ultra_badge: str | None = Field(default=None, max_length=50)  # Кастомный бейдж
    ultra_profile_color: str | None = Field(default=None, max_length=50)  # Цвет ника
    ultra_avatar_style: str | None = Field(default=None, max_length=50)  # Стиль аватара
    is_verified: bool = Field(default=False)  # Верификация
    chat_members: list["ChatMember"] = Relationship(
        back_populates="user", cascade_delete=True
    )


# Модель для перевода шекелей
class TransferShekels(SQLModel):
    recipient_id: int
    amount: int = Field(gt=0)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: int
    avatar_url: str | None = None
    balance: int = 0
    is_banned: bool = False
    ban_reason: str | None = None
    is_superuser: bool = False
    timezone: str = "UTC"
    last_seen: datetime | None = None
    is_online: bool = False
    is_ultra: bool = False
    ultra_expires_at: datetime | None = None
    ultra_badge: str | None = None
    ultra_profile_color: str | None = None
    ultra_avatar_style: str | None = None
    is_verified: bool = False


class UserAdminPublic(UserBase):
    id: int
    avatar_url: str | None = None
    is_active: bool
    is_superuser: bool
    is_banned: bool
    ban_reason: str | None
    timezone: str = "UTC"
    last_seen: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


class BanUser(SQLModel):
    reason: str | None = Field(default=None, max_length=500)


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


# ========== МОДЕЛИ МЕССЕНДЖЕРА FUSION ==========


# Модель чата (личный или групповой)
class Chat(SQLModel, table=True):
    id: int | None = Field(
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    chat_type: str = Field(
        default="private", max_length=20
    )  # "private", "group" или "bot"
    name: str | None = Field(
        default=None, max_length=255
    )  # Название для групповых чатов
    bot_id: int | None = Field(
        default=None, foreign_key="chatbot.id", nullable=True
    )  # Связь с ботом
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, default=func.now()),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now()),
    )

    # Связи
    members: list["ChatMember"] = Relationship(
        back_populates="chat", cascade_delete=True
    )
    messages: list["ChatMessage"] = Relationship(
        back_populates="chat", cascade_delete=True
    )


# Участники чата
class ChatMember(SQLModel, table=True):
    id: int | None = Field(
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    chat_id: int = Field(foreign_key="chat.id", nullable=False, ondelete="CASCADE")
    user_id: int = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    role: str = Field(default="member", max_length=20)  # "admin" или "member"
    joined_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, default=func.now()),
    )
    last_read_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, nullable=True)
    )

    # Связи
    chat: Chat = Relationship(back_populates="members")
    user: User = Relationship(back_populates="chat_members")


# Сообщения в чате
class ChatMessage(SQLModel, table=True):
    id: int | None = Field(
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    chat_id: int = Field(foreign_key="chat.id", nullable=False, ondelete="CASCADE")
    sender_id: int = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    content: str = Field(max_length=4096)
    media_type: str | None = Field(
        default=None, max_length=50
    )  # "image", "audio", "document"
    media_filename: str | None = Field(default=None, max_length=255)  # Имя файла
    media_url: str | None = Field(
        default=None, max_length=500
    )  # URL для доступа к файлу
    media_size: int | None = Field(default=None)  # Размер файла в байтах
    is_read: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, default=func.now()),
    )
    edited_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, nullable=True)
    )

    # Связи
    chat: Chat = Relationship(back_populates="messages")
    sender: User = Relationship()


# API модели для чатов
class ChatCreate(SQLModel):
    chat_type: str = "private"  # "private" или "group"
    name: str | None = None
    member_ids: list[int] = Field(default_factory=list)


class ChatPublic(SQLModel):
    id: int
    chat_type: str
    name: str | None
    created_at: datetime
    updated_at: datetime
    members: list["ChatMemberPublic"] = Field(default_factory=list)
    last_message: "ChatMessagePublic | None" = None
    bot: "ChatBotPublic | None" = None


class ChatMemberPublic(SQLModel):
    id: int
    user_id: int
    role: str
    user: UserPublic
    joined_at: datetime
    last_read_at: datetime | None


class ChatAddMembers(SQLModel):
    member_ids: list[int] = Field(min_length=1)


class ChatRoleUpdate(SQLModel):
    role: str = Field(min_length=1, max_length=20)


class ChatUpdateName(SQLModel):
    name: str = Field(min_length=1, max_length=255)


class ChatMessageCreate(SQLModel):
    content: str = Field(min_length=1, max_length=4096)
    media_type: str | None = Field(default=None, max_length=50)
    media_filename: str | None = Field(default=None, max_length=255)
    media_url: str | None = Field(default=None, max_length=500)
    media_size: int | None = Field(default=None)


class ChatMessagePublic(SQLModel):
    id: int
    chat_id: int
    sender_id: int
    sender: UserPublic | None = None
    content: str
    media_type: str | None = None
    media_filename: str | None = None
    media_url: str | None = None
    media_size: int | None = None
    is_read: bool = False
    created_at: datetime
    edited_at: datetime | None = None


class ChatMessageUpdate(SQLModel):
    content: str = Field(min_length=1, max_length=4096)


class ChatsPublic(SQLModel):
    data: list[ChatPublic]
    count: int


class ChatMessagesPublic(SQLModel):
    data: list[ChatMessagePublic]
    count: int


class UserSearch(SQLModel):
    query: str = Field(min_length=1, max_length=100)


# NFT модель (предметы для покупки)
class NFTItem(SQLModel, table=True):
    id: int | None = Field(
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)
    image_url: str | None = Field(default=None, max_length=500)
    price: int = Field(ge=0)
    rarity: str = Field(
        default="common", max_length=20
    )  # common, rare, epic, legendary
    is_active: bool = Field(default=True)


class NFTItemPublic(SQLModel):
    id: int
    name: str
    description: str | None
    image_url: str | None
    price: int
    rarity: str


class UserNFT(SQLModel, table=True):
    id: int | None = Field(
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    user_id: int = Field(foreign_key="user.id")
    item_id: int = Field(foreign_key="nftitem.id")
    purchased_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserNFTPublic(SQLModel):
    id: int
    item: NFTItemPublic
    purchased_at: datetime


class BuyNFT(SQLModel):
    item_id: int


# ========== ПОДПИСКА ULTRA ==========


class BuyUltra(SQLModel):
    """Покупка подписки Ultra"""

    days: int = Field(default=1, ge=1, le=365)


class UltraBadge(SQLModel):
    """Доступные бейджи для Ultra"""

    id: str
    name: str
    emoji: str
    description: str


class SetUltraBadge(SQLModel):
    """Установка бейджа"""

    badge_id: str | None = Field(default=None)


# Доступные бейджи
ULTRA_BADGES = [
    UltraBadge(id="star", name="Звезда", emoji="⭐", description="Звездный игрок"),
    UltraBadge(id="fire", name="Огонь", emoji="🔥", description="Горячий игрок"),
    UltraBadge(
        id="diamond", name="Алмаз", emoji="💎", description="Бриллиантовый игрок"
    ),
    UltraBadge(id="crown", name="Корона", emoji="👑", description="Королевский игрок"),
    UltraBadge(id="rocket", name="Ракета", emoji="🚀", description="Скоростной игрок"),
    UltraBadge(id="angel", name="Ангел", emoji="😇", description="Ангельский игрок"),
    UltraBadge(id="devil", name="Дьявол", emoji="😈", description="Демонический игрок"),
    UltraBadge(id="rainbow", name="Радуга", emoji="🌈", description="Радужный игрок"),
]


class Season(SQLModel, table=True):
    id: int | None = Field(
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    name: str = Field(max_length=100)
    number: int = Field(ge=1)
    is_active: bool = Field(default=False)
    start_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_date: datetime | None = Field(default=None)
    tasks: list["SeasonTask"] = Relationship(
        back_populates="season", cascade_delete=True
    )


class SeasonTask(SQLModel, table=True):
    id: int | None = Field(
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    season_id: int = Field(foreign_key="season.id", nullable=False, ondelete="CASCADE")
    name: str = Field(max_length=200)
    description: str | None = Field(default=None, max_length=500)
    target_count: int = Field(ge=1)
    task_type: str = Field(max_length=50)
    base_reward: int = Field(ge=0)
    season: Season = Relationship(back_populates="tasks")


class UserSeasonProgress(SQLModel, table=True):
    id: int | None = Field(
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    user_id: int = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    season_id: int = Field(foreign_key="season.id", nullable=False, ondelete="CASCADE")
    progress: int = Field(default=0)
    completed_tasks: str = Field(default="[]")
    total_reward_earned: int = Field(default=0)
    messages_sent: int = Field(default=0)
    chats_created: int = Field(default=0)
    friends_added: int = Field(default=0)
    media_shared: int = Field(default=0)

    user: User = Relationship()
    season: Season = Relationship()


class SeasonPublic(SQLModel):
    id: int
    name: str
    number: int
    is_active: bool
    start_date: datetime | None = None
    end_date: datetime | None = None


class SeasonTaskPublic(SQLModel):
    id: int
    name: str
    description: str | None
    target_count: int
    task_type: str
    base_reward: int


class UserSeasonProgressPublic(SQLModel):
    id: int
    season_id: int
    progress: int
    completed_tasks: list[int]
    total_reward_earned: int


class ClaimTaskReward(SQLModel):
    task_id: int


# Chat Bot Models
class ChatBot(SQLModel, table=True):
    id: int | None = Field(
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    owner_id: int = Field(foreign_key="user.id")
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)
    avatar_url: str | None = Field(default=None, max_length=500)
    code: str  # Python or JS code for the bot
    language: str = Field(default="python")  # "python" or "javascript"
    is_active: bool = Field(default=True)
    is_public: bool = Field(default=False)  # Public bots can be used by anyone
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatBotPublic(SQLModel):
    id: int
    owner_id: int
    name: str
    description: str | None
    avatar_url: str | None
    language: str
    is_active: bool
    is_public: bool
    created_at: datetime
    updated_at: datetime


class ChatBotCreate(SQLModel):
    name: str
    description: str | None = None
    avatar_url: str | None = None
    code: str
    language: str = "python"
    is_public: bool = False


class ChatBotUpdate(SQLModel):
    name: str | None = None
    description: str | None = None
    avatar_url: str | None = None
    code: str | None = None
    language: str | None = None
    is_active: bool | None = None
    is_public: bool | None = None


class BotExecutionResult(SQLModel):
    response: str
    media_type: str | None = None
    media_url: str | None = None


# ========== ФОРУМ ==========


class ForumPost(SQLModel, table=True):
    id: int | None = Field(
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    author_id: int = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    title: str = Field(max_length=255)
    content: str = Field(max_length=10000)
    media_type: str | None = Field(default=None, max_length=50)
    media_url: str | None = Field(default=None, max_length=500)
    media_filename: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, default=func.now()),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now()),
    )
    likes_count: int = Field(default=0)
    comments_count: int = Field(default=0)

    author: User = Relationship()


class ForumComment(SQLModel, table=True):
    id: int | None = Field(
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    post_id: int = Field(foreign_key="forumpost.id", nullable=False, ondelete="CASCADE")
    author_id: int = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    content: str = Field(max_length=2000)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, default=func.now()),
    )

    post: ForumPost = Relationship()
    author: User = Relationship()


class ForumPostCreate(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1, max_length=10000)
    media_type: str | None = Field(default=None, max_length=50)
    media_url: str | None = Field(default=None, max_length=500)
    media_filename: str | None = Field(default=None, max_length=255)


class ForumCommentCreate(SQLModel):
    content: str = Field(min_length=1, max_length=2000)


class ForumPostPublic(SQLModel):
    id: int
    author_id: int
    author: UserPublic | None = None
    title: str
    content: str
    media_type: str | None = None
    media_url: str | None = None
    media_filename: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    likes_count: int = 0
    comments_count: int = 0
    is_liked: bool = False


class ForumCommentPublic(SQLModel):
    id: int
    post_id: int
    author_id: int
    author: UserPublic | None = None
    content: str
    created_at: datetime


class ForumPostsPublic(SQLModel):
    data: list[ForumPostPublic]
    count: int


class ForumCommentsPublic(SQLModel):
    data: list[ForumCommentPublic]
    count: int


# ========== КАНАЛЫ ==========


class Channel(SQLModel, table=True):
    id: int | None = Field(
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    creator_id: int = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)
    avatar_url: str | None = Field(default=None, max_length=500)
    is_public: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, default=func.now()),
    )

    creator: User = Relationship()
    admins: list["ChannelAdmin"] = Relationship(
        back_populates="channel", cascade_delete=True
    )
    posts: list["ChannelPost"] = Relationship(
        back_populates="channel", cascade_delete=True
    )


class ChannelAdmin(SQLModel, table=True):
    id: int | None = Field(
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    channel_id: int = Field(
        foreign_key="channel.id", nullable=False, ondelete="CASCADE"
    )
    user_id: int = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    added_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, default=func.now()),
    )

    channel: Channel = Relationship()
    user: User = Relationship()


class ChannelPost(SQLModel, table=True):
    id: int | None = Field(
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    channel_id: int = Field(
        foreign_key="channel.id", nullable=False, ondelete="CASCADE"
    )
    author_id: int = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    content: str = Field(max_length=5000)
    media_type: str | None = Field(default=None, max_length=50)
    media_url: str | None = Field(default=None, max_length=500)
    media_filename: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, default=func.now()),
    )

    channel: Channel = Relationship()
    author: User = Relationship()


class ChannelCreate(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    avatar_url: str | None = Field(default=None, max_length=500)
    is_public: bool = True


class ChannelPostCreate(SQLModel):
    content: str = Field(min_length=1, max_length=5000)
    media_type: str | None = Field(default=None, max_length=50)
    media_url: str | None = Field(default=None, max_length=500)
    media_filename: str | None = Field(default=None, max_length=255)


class ChannelAddAdmin(SQLModel):
    user_id: int


class ChannelPublic(SQLModel):
    id: int
    creator_id: int
    creator: UserPublic | None = None
    name: str
    description: str | None = None
    avatar_url: str | None = None
    is_public: bool = True
    created_at: datetime
    is_admin: bool = False
    is_creator: bool = False


class ChannelPostPublic(SQLModel):
    id: int
    channel_id: int
    author_id: int
    author: UserPublic | None = None
    content: str
    media_type: str | None = None
    media_url: str | None = None
    media_filename: str | None = None
    created_at: datetime


class ChannelsPublic(SQLModel):
    data: list[ChannelPublic]
    count: int


class ChannelPostsPublic(SQLModel):
    data: list[ChannelPostPublic]
    count: int

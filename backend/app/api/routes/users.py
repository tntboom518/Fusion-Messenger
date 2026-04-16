import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Annotated

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Query
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, func, select

from app import crud
from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models import (
    BanUser,
    BuyNFT,
    Message,
    NFTItem,
    NFTItemPublic,
    TransferShekels,
    UpdatePassword,
    User,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
    UserAdminPublic,
    UserNFT,
    UserNFTPublic,
)
from app.utils import generate_new_account_email, send_email

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/search", response_model=UsersPublic)
def search_users(
    query: str, session: SessionDep, current_user: CurrentUser, limit: int = 20
) -> Any:
    """Поиск пользователей по email или имени"""
    from app import crud

    users = crud.search_users(
        session=session, query=query, current_user_id=current_user.id, limit=limit
    )

    return UsersPublic(data=users, count=len(users))


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
def read_users(
    session: SessionDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> Any:
    """
    Retrieve users.
    """

    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()

    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()

    return UsersPublic(data=users, count=count)


@router.post(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic
)
def create_user(*, session: SessionDep, user_in: UserCreate) -> Any:
    """
    Create new user.
    """
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    user = crud.create_user(session=session, user_create=user_in)
    if settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user


@router.patch("/me", response_model=UserPublic)
def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """
    Update own user.
    """

    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


class UpdateTimezone(BaseModel):
    timezone: str


@router.post("/me/timezone", response_model=UserPublic)
def update_timezone(
    session: SessionDep,
    current_user: CurrentUser,
    tz_data: UpdateTimezone,
) -> Any:
    """Обновить часовой пояс"""
    current_user.timezone = tz_data.timezone
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


@router.patch("/me/password", response_model=Message)
def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    """
    Update own password.
    """
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    session.commit()
    return Message(message="Password updated successfully")


@router.post("/me/avatar", response_model=UserPublic)
async def upload_avatar(
    session: SessionDep,
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> Any:
    """Загрузить аватарку"""
    import os
    from pathlib import Path

    logger.info("upload_avatar called")

    # Проверяем тип файла
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only images allowed")

    # Проверяем размер (макс 2 МБ)
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 2MB)")

    # Получаем путь к медиа директории
    base_path = Path(__file__).parent.parent.parent
    avatar_dir = base_path / settings.MEDIA_UPLOAD_DIR / "avatars"
    avatar_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving avatar to: {avatar_dir}")

    # Генерируем имя файла
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"user_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
    filepath = avatar_dir / filename

    # Сохраняем файл
    with open(filepath, "wb") as f:
        f.write(content)
    logger.info(f"Saved avatar: {filepath}")

    # Удаляем старую аватарку
    if current_user.avatar_url:
        old_path = (
            base_path
            / settings.MEDIA_UPLOAD_DIR
            / current_user.avatar_url.lstrip("/media/avatars/")
        )
        if old_path.exists():
            try:
                os.remove(old_path)
            except:
                pass

    # Обновляем URL аватарки
    avatar_url = f"/api/v1/media/avatars/{filename}"
    current_user.avatar_url = avatar_url
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    logger.info(f"Avatar URL set to: {avatar_url}")

    return current_user


@router.delete("/me/avatar", response_model=UserPublic)
def delete_avatar(
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Удалить аватарку"""
    import os
    from pathlib import Path

    if current_user.avatar_url:
        base_path = Path(__file__).parent.parent.parent
        expected_dir = base_path / settings.MEDIA_UPLOAD_DIR / "avatars"
        filename = current_user.avatar_url.lstrip("/media/avatars/")
        filename = filename.replace("..", "").replace("/", "").replace("\\", "")
        old_path = expected_dir / filename
        old_path = old_path.resolve()
        if (
            old_path.exists()
            and old_path.is_file()
            and old_path.parent.resolve() == expected_dir.resolve()
        ):
            try:
                os.remove(old_path)
            except:
                pass

    current_user.avatar_url = None
    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return current_user


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    # Superusers are always verified
    if current_user.is_superuser:
        current_user.is_verified = True
    return current_user


@router.post("/me/transfer", response_model=UserPublic)
def transfer_shekels(
    session: SessionDep,
    current_user: CurrentUser,
    transfer_data: TransferShekels,
) -> Any:
    """Перевести шекели другому пользователю"""
    if current_user.id == transfer_data.recipient_id:
        raise HTTPException(status_code=400, detail="Нельзя перевести себе")

    if transfer_data.amount <= 0:
        raise HTTPException(status_code=400, detail="Сумма должна быть больше 0")

    if current_user.balance < transfer_data.amount:
        raise HTTPException(status_code=400, detail="Недостаточно шекелей")

    recipient = session.get(User, transfer_data.recipient_id)
    if not recipient:
        raise HTTPException(status_code=404, detail="Получатель не найден")

    sender = session.exec(
        select(User).where(User.id == current_user.id).with_for_update()
    ).first()
    recipient_locked = session.exec(
        select(User).where(User.id == recipient.id).with_for_update()
    ).first()

    if not sender or not recipient_locked:
        raise HTTPException(status_code=404, detail="User not found")

    if sender.balance < transfer_data.amount:
        raise HTTPException(status_code=400, detail="Недостаточно шекелей")

    sender.balance -= transfer_data.amount
    recipient_locked.balance += transfer_data.amount

    session.add(sender)
    session.add(recipient_locked)
    session.commit()
    session.refresh(sender)

    return sender


@router.delete("/me", response_model=Message)
def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Delete own user.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    session.delete(current_user)
    session.commit()
    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserPublic)
def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """
    Create new user without the need to be logged in.
    """
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    user_create = UserCreate.model_validate(user_in)
    user = crud.create_user(session=session, user_create=user_create)
    return user


@router.get(
    "/all",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
def get_all_users(
    session: SessionDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> Any:
    """Получить всех пользователей (для админа)"""
    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()
    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()
    return UsersPublic(data=users, count=count)


# NFT эндпоинты
@router.get("/shop", response_model=list[NFTItemPublic])
def get_shop_items(session: SessionDep) -> Any:
    """Получить все доступные NFT в магазине"""
    items = session.exec(select(NFTItem).where(NFTItem.is_active == True)).all()
    return items


@router.get("/me/nfts", response_model=list[UserNFTPublic])
def get_user_nfts(
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Получить NFT пользователя"""
    user_nfts = session.exec(
        select(UserNFT).where(UserNFT.user_id == current_user.id)
    ).all()

    result = []
    for user_nft in user_nfts:
        item = session.get(NFTItem, user_nft.item_id)
        if item:
            result.append(
                UserNFTPublic(
                    id=user_nft.id,
                    item=NFTItemPublic(
                        id=item.id,
                        name=item.name,
                        description=item.description,
                        image_url=item.image_url,
                        price=item.price,
                        rarity=item.rarity,
                    ),
                    purchased_at=user_nft.purchased_at,
                )
            )
    return result


@router.post("/me/buy", response_model=UserNFTPublic)
def buy_nft(
    session: SessionDep,
    current_user: CurrentUser,
    buy_data: BuyNFT,
) -> Any:
    """Купить NFT"""
    item = session.get(NFTItem, buy_data.item_id)
    if not item or not item.is_active:
        raise HTTPException(status_code=404, detail="Item not found")

    if current_user.balance < item.price:
        raise HTTPException(status_code=400, detail="Not enough shekels")

    existing = session.exec(
        select(UserNFT).where(
            UserNFT.user_id == current_user.id, UserNFT.item_id == item.id
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already owned")

    current_user.balance -= item.price
    session.add(current_user)

    user_nft = UserNFT(user_id=current_user.id, item_id=item.id)
    session.add(user_nft)
    session.commit()
    session.refresh(user_nft)

    return UserNFTPublic(
        id=user_nft.id,
        item=NFTItemPublic(
            id=item.id,
            name=item.name,
            description=item.description,
            image_url=item.image_url,
            price=item.price,
            rarity=item.rarity,
        ),
        purchased_at=user_nft.purchased_at,
    )


@router.get(
    "/all",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
def get_all_users(
    session: SessionDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> Any:
    """Получить всех пользователей (для админа)"""
    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()
    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()
    return UsersPublic(data=users, count=count)


@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(
    user_id: int, session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get a specific user by id.
    """
    user = session.get(User, user_id)
    if user == current_user:
        return user
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    return user


# Admin NFT management
class CreateNFT(SQLModel):
    name: str
    description: str | None = None
    image_url: str | None = None
    price: int = Field(ge=0)
    rarity: str = "common"
    is_active: bool = True


class UpdateNFT(SQLModel):
    name: str | None = None
    description: str | None = None
    image_url: str | None = None
    price: int | None = Field(default=None, ge=0)
    rarity: str | None = None
    is_active: bool | None = None


@router.post(
    "/nft",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=NFTItemPublic,
)
def create_nft(
    session: SessionDep,
    nft_data: CreateNFT,
) -> Any:
    """Создать NFT предмет (админ)"""
    nft = NFTItem(
        name=nft_data.name,
        description=nft_data.description,
        image_url=nft_data.image_url,
        price=nft_data.price,
        rarity=nft_data.rarity,
        is_active=nft_data.is_active,
    )
    session.add(nft)
    session.commit()
    session.refresh(nft)
    return nft


@router.get(
    "/nft/{nft_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=NFTItemPublic,
)
def get_nft(
    nft_id: int,
    session: SessionDep,
) -> Any:
    """Получить NFT предмет (админ)"""
    nft = session.get(NFTItem, nft_id)
    if not nft:
        raise HTTPException(status_code=404, detail="NFT not found")
    return nft


@router.put(
    "/nft/{nft_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=NFTItemPublic,
)
def update_nft(
    nft_id: int,
    session: SessionDep,
    nft_data: UpdateNFT,
) -> Any:
    """Обновить NFT предмет (админ)"""
    nft = session.get(NFTItem, nft_id)
    if not nft:
        raise HTTPException(status_code=404, detail="NFT not found")

    update_data = nft_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(nft, key, value)

    session.add(nft)
    session.commit()
    session.refresh(nft)
    return nft


@router.delete(
    "/nft/{nft_id}",
    dependencies=[Depends(get_current_active_superuser)],
)
def delete_nft(
    nft_id: int,
    session: SessionDep,
) -> Message:
    """Удалить NFT предмет (админ)"""
    nft = session.get(NFTItem, nft_id)
    if not nft:
        raise HTTPException(status_code=404, detail="NFT not found")

    session.delete(nft)
    session.commit()
    return Message(message="NFT deleted successfully")
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    return user


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
def update_user(
    *,
    session: SessionDep,
    user_id: int,
    user_in: UserUpdate,
) -> Any:
    """
    Update a user.
    """

    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )

    db_user = crud.update_user(session=session, db_user=db_user, user_in=user_in)
    return db_user


@router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: int
) -> Message:
    """
    Delete a user.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    session.delete(user)
    session.commit()
    return Message(message="User deleted successfully")


@router.post("/{user_id}/ban", dependencies=[Depends(get_current_active_superuser)])
def ban_user(
    user_id: int,
    session: SessionDep,
    current_user: CurrentUser,
    ban_in: BanUser | None = None,
) -> Message:
    """Забанить пользователя"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(status_code=400, detail="Cannot ban yourself")
    if user.is_superuser:
        raise HTTPException(status_code=400, detail="Cannot ban superuser")

    user.is_banned = True
    user.ban_reason = ban_in.reason if ban_in and ban_in.reason else None
    session.add(user)
    session.commit()
    return Message(message=f"User {user.email} has been banned")


@router.post("/{user_id}/unban", dependencies=[Depends(get_current_active_superuser)])
def unban_user(
    user_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> Message:
    """Разбанить пользователя"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_banned = False
    user.ban_reason = None
    session.add(user)
    session.commit()
    return Message(message=f"User {user.email} has been unbanned")


@router.get(
    "/all",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
def get_all_users(
    session: SessionDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> Any:
    """Получить всех пользователей (для админа)"""
    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()
    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()
    return UsersPublic(data=users, count=count)


# NFT эндпоинты
@router.get("/me/nfts", response_model=list[UserNFTPublic])
def get_user_nfts(
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Получить NFT пользователя"""
    user_nfts = session.exec(
        select(UserNFT).where(UserNFT.user_id == current_user.id)
    ).all()

    result = []
    for user_nft in user_nfts:
        item = session.get(NFTItem, user_nft.item_id)
        if item:
            result.append(
                UserNFTPublic(
                    id=user_nft.id,
                    item=NFTItemPublic(
                        id=item.id,
                        name=item.name,
                        description=item.description,
                        image_url=item.image_url,
                        price=item.price,
                        rarity=item.rarity,
                    ),
                    purchased_at=user_nft.purchased_at,
                )
            )
    return result


@router.get("/shop", response_model=list[NFTItemPublic])
def get_shop_items(session: SessionDep) -> Any:
    """Получить все доступные NFT в магазине"""
    items = session.exec(select(NFTItem).where(NFTItem.is_active == True)).all()
    return items


@router.post("/me/buy", response_model=UserNFTPublic)
def buy_nft(
    session: SessionDep,
    current_user: CurrentUser,
    buy_data: BuyNFT,
) -> Any:
    """Купить NFT"""
    item = session.get(NFTItem, buy_data.item_id)
    if not item or not item.is_active:
        raise HTTPException(status_code=404, detail="Item not found")

    if current_user.balance < item.price:
        raise HTTPException(status_code=400, detail="Not enough shekels")

    # Проверяем, не куплен ли уже этот предмет
    existing = session.exec(
        select(UserNFT).where(
            UserNFT.user_id == current_user.id, UserNFT.item_id == item.id
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already owned")

    # Списываем баланс
    current_user.balance -= item.price
    session.add(current_user)

    # Создаём NFT
    user_nft = UserNFT(user_id=current_user.id, item_id=item.id)
    session.add(user_nft)
    session.commit()
    session.refresh(user_nft)

    return UserNFTPublic(
        id=user_nft.id,
        item=NFTItemPublic(
            id=item.id,
            name=item.name,
            description=item.description,
            image_url=item.image_url,
            price=item.price,
            rarity=item.rarity,
        ),
        purchased_at=user_nft.purchased_at,
    )


@router.post(
    "/{user_id}/award-nft", dependencies=[Depends(get_current_active_superuser)]
)
def award_nft(
    user_id: int,
    session: SessionDep,
    current_user: CurrentUser,
    award_data: BuyNFT,
) -> Any:
    """Выдать NFT пользователю (админ)"""
    item = session.get(NFTItem, award_data.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Проверяем, не куплен ли уже
    existing = session.exec(
        select(UserNFT).where(UserNFT.user_id == user_id, UserNFT.item_id == item.id)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already has this NFT")

    user_nft = UserNFT(user_id=user_id, item_id=item.id)
    session.add(user_nft)
    session.commit()
    session.refresh(user_nft)

    return UserNFTPublic(
        id=user_nft.id,
        item=NFTItemPublic(
            id=item.id,
            name=item.name,
            description=item.description,
            image_url=item.image_url,
            price=item.price,
            rarity=item.rarity,
        ),
        purchased_at=user_nft.purchased_at,
    )


@router.post(
    "/{user_id}/add-balance", dependencies=[Depends(get_current_active_superuser)]
)
def admin_add_balance(
    user_id: int,
    session: SessionDep,
    current_user: CurrentUser,
    amount: dict,
) -> Any:
    """Добавить шекели пользователю (админ)"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    add_amount = amount.get("amount", 0)
    if add_amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    user.balance += add_amount
    session.add(user)
    session.commit()
    session.refresh(user)

    return user


@router.post("/{user_id}/verify", dependencies=[Depends(get_current_active_superuser)])
def verify_user(
    user_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Верифицировать пользователя (админ)"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    session.add(user)
    session.commit()
    session.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_verified": user.is_verified,
    }


@router.post(
    "/{user_id}/unverify", dependencies=[Depends(get_current_active_superuser)]
)
def unverify_user(
    user_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Убрать верификацию пользователя (админ)"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = False
    session.add(user)
    session.commit()
    session.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_verified": user.is_verified,
    }

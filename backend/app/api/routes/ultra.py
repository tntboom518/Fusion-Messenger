from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.api.deps import CurrentUser, SessionDep
from app.models import User, UserPublic, ULTRA_BADGES, UltraBadge, SetUltraBadge

router = APIRouter(prefix="/ultra", tags=["ultra"])


@router.get("/status")
def get_ultra_status(
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    """Получить статус Ultra подписки"""
    user = session.get(User, current_user.id)

    # Безопасная проверка полей (если миграция не запущена)
    is_ultra = getattr(user, "is_ultra", False)
    expires_at = getattr(user, "ultra_expires_at", None)
    ultra_badge = getattr(user, "ultra_badge", None)

    # Конвертируем в timezone-aware datetime если нужно
    if expires_at:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

    # Проверяем, истекла ли подписка
    if is_ultra and expires_at and expires_at < datetime.now(timezone.utc):
        user.is_ultra = False
        user.ultra_expires_at = None
        user.ultra_badge = None
        session.commit()
        # Используем обновлённые значения
        is_ultra = False
        expires_at = None
        ultra_badge = None

    return {
        "is_ultra": is_ultra,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "badge": ultra_badge,
        "badges": [
            {"id": b.id, "name": b.name, "emoji": b.emoji, "description": b.description}
            for b in ULTRA_BADGES
        ],
    }


@router.post("/buy")
def buy_ultra(
    session: SessionDep,
    current_user: CurrentUser,
    days: int = Query(default=1, ge=1, le=365),
) -> dict:
    """Купить подписку Ultra за 1000 шекелей в день"""
    user = session.get(User, current_user.id)

    cost = days * 1000

    if user.balance < cost:
        raise HTTPException(
            status_code=400,
            detail=f"Недостаточно шекелей. Нужно {cost}, у вас {user.balance}",
        )

    # Списываем деньги
    user.balance -= cost

    # Добавляем время к подписке
    now = datetime.now(timezone.utc)

    # Безопасная проверка полей (если миграция не запущена)
    is_ultra = getattr(user, "is_ultra", False)
    ultra_expires_at = getattr(user, "ultra_expires_at", None)
    ultra_badge = getattr(user, "ultra_badge", None)

    # Конвертируем в timezone-aware datetime если нужно
    if ultra_expires_at:
        if ultra_expires_at.tzinfo is None:
            ultra_expires_at = ultra_expires_at.replace(tzinfo=timezone.utc)

    if is_ultra and ultra_expires_at and ultra_expires_at > now:
        # Продлеваем существующую подписку
        user.ultra_expires_at = ultra_expires_at + timedelta(days=days)
    else:
        # Новая подписка
        user.is_ultra = True
        user.ultra_expires_at = now + timedelta(days=days)
        user.ultra_badge = None

    session.commit()
    session.refresh(user)

    # Снова безопасно получаем значения после коммита
    final_ultra = getattr(user, "is_ultra", False)
    final_expires = getattr(user, "ultra_expires_at", None)
    final_badge = getattr(user, "ultra_badge", None)

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "avatar_url": user.avatar_url,
        "balance": user.balance,
        "is_banned": user.is_banned,
        "ban_reason": user.ban_reason,
        "timezone": user.timezone,
        "last_seen": user.last_seen.isoformat() if user.last_seen else None,
        "is_online": False,
        "is_ultra": final_ultra,
        "ultra_expires_at": final_expires.isoformat() if final_expires else None,
        "ultra_badge": final_badge,
    }


@router.post("/badge")
def set_badge(
    badge_data: SetUltraBadge,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    """Установить бейдж (только для Ultra)"""
    user = session.get(User, current_user.id)

    # Проверяем подписку
    if not user.is_ultra:
        raise HTTPException(status_code=403, detail="Нужен Ultra для установки бейджа")

    # Проверяем, что бейдж существует
    if badge_data.badge_id:
        badge = next((b for b in ULTRA_BADGES if b.id == badge_data.badge_id), None)
        if not badge:
            raise HTTPException(status_code=400, detail="Бейдж не найден")
        user.ultra_badge = badge_data.badge_id
    else:
        user.ultra_badge = None

    session.commit()

    return {"badge": user.ultra_badge}


@router.post("/grant")
def grant_ultra(
    session: SessionDep,
    current_user: CurrentUser,
    user_id: int = Query(..., ge=1),
    hours: int = Query(default=2, ge=1, le=8760),
) -> dict:
    """Выдать Ultra (для админа)"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Только админ может выдавать Ultra")

    target_user = session.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    now = datetime.now(timezone.utc)
    hours_delta = timedelta(hours=hours)

    # Безопасная проверка полей
    is_ultra = getattr(target_user, "is_ultra", False)
    ultra_expires_at = getattr(target_user, "ultra_expires_at", None)

    # Конвертируем в timezone-aware datetime если нужно
    if ultra_expires_at:
        if ultra_expires_at.tzinfo is None:
            ultra_expires_at = ultra_expires_at.replace(tzinfo=timezone.utc)

    if is_ultra and ultra_expires_at and ultra_expires_at > now:
        target_user.ultra_expires_at = ultra_expires_at + hours_delta
    else:
        target_user.is_ultra = True
        target_user.ultra_expires_at = now + hours_delta

    session.commit()

    # Безопасно получаем итоговое значение
    final_expires = getattr(target_user, "ultra_expires_at", None)

    return {
        "ok": True,
        "user_id": user_id,
        "new_expires": final_expires.isoformat() if final_expires else None,
    }


@router.post("/revoke")
def revoke_ultra(
    session: SessionDep,
    current_user: CurrentUser,
    user_id: int = Query(..., ge=1),
) -> dict:
    """Забрать Ultra (для админа)"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Только админ может забирать Ultra")

    target_user = session.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    target_user.is_ultra = False
    target_user.ultra_expires_at = None
    target_user.ultra_badge = None

    session.commit()

    return {"ok": True}

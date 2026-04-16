from fastapi import APIRouter

from app.api.routes import (
    chats,
    login,
    messages,
    private,
    users,
    utils,
    websocket,
    media,
    seasons,
    bots,
    forum,
    channels,
    ultra,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(chats.router)
api_router.include_router(messages.router)
api_router.include_router(media.router)
api_router.include_router(websocket.router)
api_router.include_router(seasons.router)
api_router.include_router(bots.router)
api_router.include_router(forum.router)
api_router.include_router(channels.router)
api_router.include_router(ultra.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)

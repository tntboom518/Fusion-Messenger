import logging
import os
import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from sqlmodel import Session, SQLModel, select
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

from app import crud
from app.api.main import api_router
from app.core.config import settings
from app.core.db import engine
from app.models import User, UserCreate, NFTItem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


limiter = Limiter(key_func=get_remote_address)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)


# Создаем таблицы при старте, если их нет
def create_tables():
    """Создает таблицы в БД, если их еще нет"""
    try:
        logger.info("Checking and creating database tables if needed...")
        # SQLModel.create_all безопасно создает только отсутствующие таблицы
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables ready")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        # Не падаем, если таблицы уже существуют
        pass


def create_initial_user():
    """Создает начального пользователя, если его нет"""
    try:
        with Session(engine) as session:
            user = session.exec(
                select(User).where(User.email == settings.FIRST_SUPERUSER)
            ).first()
            if not user:
                logger.info("Creating initial superuser...")
                user_in = UserCreate(
                    email=settings.FIRST_SUPERUSER,
                    password=settings.FIRST_SUPERUSER_PASSWORD,
                    is_superuser=True,
                )
                crud.create_user(session=session, user_create=user_in)
                logger.info("Initial superuser created successfully")
            else:
                logger.info("Initial superuser already exists")
    except Exception as e:
        logger.error(f"Error creating initial user: {e}")


def create_initial_nfts():
    """Создает начальные NFT предметы, если их нет"""
    try:
        with Session(engine) as session:
            nfts = session.exec(select(NFTItem)).all()
            if not nfts:
                logger.info("Creating initial NFT items...")
                items = [
                    NFTItem(
                        name="Базовая аватарка",
                        description="Простая аватарка для вашего профиля",
                        price=100,
                        rarity="common",
                        is_active=True,
                        image_url="https://via.placeholder.com/150/4a5568/ffffff?text=Avatar",
                    ),
                    NFTItem(
                        name="Неоновый огонь",
                        description="Яркая неоновая аватарка с эффектом пламени",
                        price=500,
                        rarity="rare",
                        is_active=True,
                        image_url="https://via.placeholder.com/150/f97316/ffffff?text=Fire",
                    ),
                    NFTItem(
                        name="Космический путешественник",
                        description="Аватарка в стиле космического исследователя",
                        price=1500,
                        rarity="epic",
                        is_active=True,
                        image_url="https://via.placeholder.com/150/6366f1/ffffff?text=Space",
                    ),
                    NFTItem(
                        name="Легендарный дракон",
                        description="Редчайшая аватарка с изображением могущественного дракона",
                        price=5000,
                        rarity="legendary",
                        is_active=True,
                        image_url="https://via.placeholder.com/150/dc2626/ffffff?text=Dragon",
                    ),
                    NFTItem(
                        name="Кристальное сердце",
                        description="Вибрирующее сердце из магических кристаллов",
                        price=800,
                        rarity="rare",
                        is_active=True,
                        image_url="https://via.placeholder.com/150/ec4899/ffffff?text=Heart",
                    ),
                    NFTItem(
                        name="Галактический страж",
                        description="Загадочный страж из далёкой галактики",
                        price=3000,
                        rarity="epic",
                        is_active=True,
                        image_url="https://via.placeholder.com/150/0ea5e9/ffffff?text=Guardian",
                    ),
                ]
                for item in items:
                    session.add(item)
                session.commit()
                logger.info(f"Created {len(items)} initial NFT items")
            else:
                logger.info("NFT items already exist")
    except Exception as e:
        logger.error(f"Error creating initial NFTs: {e}")


# Создаем таблицы и начального пользователя при импорте модуля
create_tables()
create_initial_user()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."},
    )


# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

# Примечание: статические файлы для медиа больше не монтируем отдельно
# Теперь они обслуживаются через API эндпоинт в media.py (без авторизации)

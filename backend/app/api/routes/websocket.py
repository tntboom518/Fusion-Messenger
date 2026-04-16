import json
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlmodel import Session

from app import crud
from app.core.security import decode_access_token
from app.core.db import engine
from app.models import ChatMessage, ChatMessagePublic, User, UserPublic

router = APIRouter()


# Хранилище активных WebSocket соединений
class ConnectionManager:
    def __init__(self):
        # chat_id -> set of websockets
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # user_id -> set of websockets
        self.user_connections: Dict[int, Set[WebSocket]] = {}
        # user_id -> set of user_ids who are typing in each chat
        self.typing_users: Dict[int, Set[int]] = {}

    async def connect(self, websocket: WebSocket, chat_id: int, user_id: int):
        await websocket.accept()

        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = set()
        self.active_connections[chat_id].add(websocket)

        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)

        # Если это глобальный чат (chat_id=0), отправляем список всех онлайн
        if chat_id == 0:
            online_users = list(self.user_connections.keys())
            await websocket.send_json({"type": "online_users", "users": online_users})
            # Также уведомляем всех в глобальном чате о новом пользователе
            for conn in self.active_connections.get(0, set()):
                if conn != websocket:
                    await conn.send_json({"type": "user_online", "user_id": user_id})
        else:
            # Для обычных чатов - уведомляем участников чата
            await self.broadcast_to_chat(
                {"type": "user_online", "user_id": user_id},
                chat_id,
                exclude_user=user_id,
            )
            # Также уведомляем всех в глобальном чате (chat_id=0)
            for conn in self.active_connections.get(0, set()):
                await conn.send_json({"type": "user_online", "user_id": user_id})

    async def disconnect(self, websocket: WebSocket, chat_id: int, user_id: int):
        if chat_id in self.active_connections:
            self.active_connections[chat_id].discard(websocket)
            if not self.active_connections[chat_id]:
                del self.active_connections[chat_id]

        was_online = False
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
                was_online = True

        # Уведомляем о выходе пользователя
        import asyncio

        async def notify_offline():
            if chat_id != 0:
                await self.broadcast_to_chat(
                    {"type": "user_offline", "user_id": user_id}, chat_id
                )
            # Также уведомляем глобальный чат
            for conn in self.active_connections.get(0, set()):
                await conn.send_json({"type": "user_offline", "user_id": user_id})

        if was_online:
            asyncio.create_task(notify_offline())

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast_to_chat(
        self, message: dict, chat_id: int, exclude_user: int = None
    ):
        import logging

        logger = logging.getLogger(__name__)
        if chat_id in self.active_connections:
            logger.info(
                f"Broadcasting to {len(self.active_connections[chat_id])} connections in chat {chat_id}"
            )
            disconnected = set()
            for connection in self.active_connections[chat_id]:
                try:
                    await connection.send_json(message)
                    logger.info(f"Message sent to connection in chat {chat_id}")
                except Exception as e:
                    logger.error(f"Error sending message to connection: {e}")
                    disconnected.add(connection)

            # Удаляем отключенные соединения
            for conn in disconnected:
                self.active_connections[chat_id].discard(conn)
        else:
            logger.warning(f"No active connections for chat {chat_id}")

    def is_user_online(self, user_id: int) -> bool:
        return user_id in self.user_connections

    async def send_to_user(self, message: dict, user_id: int):
        """Отправить сообщение конкретному пользователю"""
        if user_id in self.user_connections:
            for conn in self.user_connections[user_id]:
                try:
                    await conn.send_json(message)
                except Exception:
                    pass


manager = ConnectionManager()


async def get_user_from_websocket(websocket: WebSocket, token: str) -> User | None:
    """Получить пользователя из токена WebSocket"""
    try:
        payload = decode_access_token(token)
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            return None

        with Session(engine) as session:
            user = session.get(User, user_id)
            return user
    except Exception:
        return None


@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: int):
    """WebSocket endpoint для чата"""
    # Получаем токен из query параметров
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Token required")
        return

    user = await get_user_from_websocket(websocket, token)
    if not user:
        await websocket.close(code=1008, reason="Invalid token")
        return

    if user.is_banned:
        await websocket.close(code=1008, reason="User is banned")
        return

    if not user.is_active:
        await websocket.close(code=1008, reason="Inactive user")
        return

    # Проверяем, что пользователь является участником чата
    if chat_id != 0:
        with Session(engine) as session:
            from sqlmodel import select
            from app.models import Chat, ChatMember

            # Сначала получаем чат чтобы узнать его тип
            chat = session.get(Chat, chat_id)

            # Для ботов пропускаем проверку member - просто разрешаем доступ
            if not (chat and chat.chat_type == "bot"):
                # Для обычных чатов проверяем членство
                member_stmt = select(ChatMember).where(
                    ChatMember.chat_id == chat_id, ChatMember.user_id == user.id
                )
                member = session.exec(member_stmt).first()

                if not member:
                    await websocket.close(
                        code=1008, reason="Chat not found or access denied"
                    )
                    return

    await manager.connect(websocket, chat_id, user.id)

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            if message_data.get("type") == "message":
                # Создаем сообщение
                with Session(engine) as session:
                    try:
                        message = crud.create_message(
                            session=session,
                            chat_id=chat_id,
                            sender_id=user.id,
                            content=message_data.get("content", ""),
                            media_type=message_data.get("media_type"),
                            media_filename=message_data.get("media_filename"),
                            media_url=message_data.get("media_url"),
                            media_size=message_data.get("media_size"),
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
                            media_type=message.media_type,
                            media_filename=message.media_filename,
                            media_url=message.media_url,
                            media_size=message.media_size,
                            created_at=message.created_at,
                            edited_at=message.edited_at,
                        )

                        # Отправляем сообщение всем участникам чата
                        # Используем mode='json' для правильной сериализации datetime
                        await manager.broadcast_to_chat(
                            {
                                "type": "new_message",
                                "message": message_public.model_dump(mode="json"),
                            },
                            chat_id,
                        )

                        # Handle bot response for bot chats
                        from app.models import Chat
                        from sqlmodel import select

                        chat_stmt = select(Chat).where(Chat.id == chat_id)
                        chat = session.exec(chat_stmt).first()
                        if chat and chat.chat_type == "bot" and chat.bot_id:
                            from app.bot_executor import execute_bot
                            from app.models import ChatBot

                            bot = session.get(ChatBot, chat.bot_id)
                            if bot and bot.is_active:
                                user_context = {
                                    "id": user.id,
                                    "full_name": user.full_name or user.email,
                                }
                                result = execute_bot(
                                    bot.code,
                                    bot.language,
                                    message_data.get("content", ""),
                                    user_context,
                                )
                                bot_msg = crud.create_message(
                                    session=session,
                                    chat_id=chat_id,
                                    sender_id=0,
                                    content=result.get("response", ""),
                                )
                                session.commit()
                                bot_msg_public = ChatMessagePublic(
                                    id=bot_msg.id,
                                    chat_id=bot_msg.chat_id,
                                    sender_id=0,
                                    sender=None,
                                    content=bot_msg.content,
                                    created_at=bot_msg.created_at,
                                    edited_at=bot_msg.edited_at,
                                )
                                await manager.broadcast_to_chat(
                                    {
                                        "type": "new_message",
                                        "message": bot_msg_public.model_dump(
                                            mode="json"
                                        ),
                                    },
                                    chat_id,
                                )
                    except Exception as e:
                        await websocket.send_json(
                            {
                                "type": "error",
                                "message": str(e),
                            }
                        )

            elif message_data.get("type") == "typing":
                # Уведомление о печати
                await manager.broadcast_to_chat(
                    {
                        "type": "typing",
                        "user_id": user.id,
                        "user_name": user.full_name or user.email,
                    },
                    chat_id,
                )

            elif message_data.get("type") == "call_offer":
                # Входящий звонок - отправляем через broadcast в конкретный чат
                # Это работает даже если пользователь не в глобальном мониторинге
                target_user_id = message_data.get("target_user_id")
                if target_user_id:
                    # Отправляем всем в чате, включая целевого пользователя
                    await manager.broadcast_to_chat(
                        {
                            "type": "call_offer",
                            "from_user_id": user.id,
                            "from_user_name": user.full_name or user.email,
                            "chat_id": chat_id,
                            "sdp": message_data.get("sdp"),
                            "target_user_id": target_user_id,
                        },
                        chat_id,
                    )

            elif message_data.get("type") == "call_answer":
                # Ответ на звонок
                target_user_id = message_data.get("target_user_id")
                if target_user_id:
                    await manager.broadcast_to_chat(
                        {
                            "type": "call_answer",
                            "from_user_id": user.id,
                            "accepted": message_data.get("accepted"),
                            "sdp": message_data.get("sdp"),
                            "target_user_id": target_user_id,
                        },
                        chat_id,
                    )

            elif message_data.get("type") == "call_ice":
                # ICE кандидаты
                target_user_id = message_data.get("target_user_id")
                if target_user_id:
                    await manager.broadcast_to_chat(
                        {
                            "type": "call_ice",
                            "from_user_id": user.id,
                            "candidate": message_data.get("candidate"),
                            "target_user_id": target_user_id,
                        },
                        chat_id,
                    )

            elif message_data.get("type") == "call_end":
                # Завершение звонка
                target_user_id = message_data.get("target_user_id")
                if target_user_id:
                    await manager.broadcast_to_chat(
                        {
                            "type": "call_end",
                            "from_user_id": user.id,
                            "target_user_id": target_user_id,
                        },
                        chat_id,
                    )

    except WebSocketDisconnect:
        manager.disconnect(websocket, chat_id, user.id)

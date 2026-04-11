import asyncio
import logging
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request, UploadFile
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlmodel import Session, func, select

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.api.routes.websocket import manager
from app.core.config import settings
from app.models import (
    ChatMessage,
    ChatMessagePublic,
    ChatMessageCreate,
    ChatMessageUpdate,
    Message,
    User,
    UserPublic,
)

router = APIRouter(prefix="/media", tags=["media"])
logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/wav", "audio/ogg", "audio/mp3"}
ALLOWED_DOCUMENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}

ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_AUDIO_TYPES | ALLOWED_DOCUMENT_TYPES

ALLOWED_EXTENSIONS = {
    "jpg", "jpeg", "png", "gif", "webp",
    "mp3", "wav", "ogg",
    "pdf", "doc", "docx", "txt"
}

MAGIC_BYTES = {
    b'\xff\xd8\xff': 'image/jpeg',
    b'\x89PNG\r\n\x1a\n': 'image/png',
    b'GIF87a': 'image/gif',
    b'GIF89a': 'image/gif',
    b'RIFF': 'audio/wav',
    b'ID3': 'audio/mpeg',
    b'\x1aE\xdf\xa3': 'audio/mpeg',
    b'%PDF': 'application/pdf',
    b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1': 'application/msword',
}

MAX_MESSAGE_CONTENT_LENGTH = 4096


def get_media_dir() -> Path:
    """Получить путь к директории для медиа файлов"""
    base_path = Path(__file__).parent.parent.parent
    media_dir = base_path / settings.MEDIA_UPLOAD_DIR
    media_dir.mkdir(parents=True, exist_ok=True)
    return media_dir


def validate_filename(filename: str) -> str:
    """Валидировать имя файла для предотвращения Path Traversal"""
    if not filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    filename = os.path.basename(filename)
    
    # Разрешаем буквы, цифры, пробелы, дефисы, точки, подчёркивания
    # Запрещаем спецсимволы которые могут использоваться для атак
    if not re.match(r'^[\w\s\-\.]+$', filename):
        raise HTTPException(status_code=400, detail="Invalid filename format")
    
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="File extension not allowed")
    
    return filename


def validate_file_content(file_path: Path, content_type: str) -> bool:
    """Верифицировать содержимое файла по magic bytes"""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(16)
        
        if not header:
            return False
        
        for magic, mime_type in MAGIC_BYTES.items():
            if header.startswith(magic):
                if content_type != mime_type:
                    logger.warning(f"Content-type mismatch: declared {content_type}, detected {mime_type}")
                    return False
                return True
        
        if content_type in ALLOWED_IMAGE_TYPES:
            # Для изображений - мягкая проверка, не отклоняем если magic bytes не найдены
            # Многие современные PNG/JPG имеют особенности сжатия
            logger.warning(f"Image declared, magic bytes not found - allowing (soft check)")
            return True
        
        if content_type in ALLOWED_AUDIO_TYPES:
            # Для аудио - мягкая проверка
            logger.warning(f"Audio declared, magic bytes not found - allowing (soft check)")
            return True
        
        if content_type in ALLOWED_DOCUMENT_TYPES:
            if not _validate_document_content(header, content_type):
                logger.warning(f"Document declared but content doesn't match")
                return False
            return True
        
        return False
    except Exception as e:
        logger.error(f"Error validating file content: {e}")
        return False


def _validate_document_content(header: bytes, content_type: str) -> bool:
    """Валидировать содержимое документа"""
    if content_type == "application/pdf" and not header.startswith(b'%PDF'):
        return False
    if content_type == "application/msword" and not header.startswith(b'\xd0\xcf\x11\xe0'):
        return False
    if content_type == "text/plain":
        try:
            header.decode('utf-8')
            return True
        except UnicodeDecodeError:
            return False
    return True


def is_path_traversal_attempt(filename: str, media_dir: Path) -> bool:
    """Проверить на попытку Path Traversal"""
    try:
        safe_path = (media_dir / filename).resolve()
        return not str(safe_path).startswith(str(media_dir.resolve()))
    except Exception:
        return True


def get_storage_size() -> int:
    """Получить общий размер хранилища в байтах"""
    media_dir = get_media_dir()
    total_size = 0
    if media_dir.exists():
        for dirpath, dirnames, filenames in os.walk(media_dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total_size += os.path.getsize(fp)
    return total_size


def cleanup_old_files(limit_bytes: int = None) -> int:
    """Очистить старые файлы, если хранилище превысило лимит"""
    if limit_bytes is None:
        limit_bytes = settings.MEDIA_STORAGE_LIMIT

    media_dir = get_media_dir()
    if not media_dir.exists():
        return 0

    files_with_time = []
    for file_path in media_dir.rglob("*"):
        if file_path.is_file():
            try:
                mtime = file_path.stat().st_mtime
                files_with_time.append((mtime, file_path))
            except Exception:
                pass

    files_with_time.sort(key=lambda x: x[0])

    freed_bytes = 0
    current_size = get_storage_size()
    target_reduction = current_size - limit_bytes + (100 * 1024 * 1024)

    for mtime, file_path in files_with_time:
        if current_size - freed_bytes <= limit_bytes:
            break
        try:
            file_size = file_path.stat().st_size
            file_path.unlink()
            freed_bytes += file_size
            logger.info(f"Deleted old media file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to delete {file_path}: {e}")

    return freed_bytes


async def broadcast_message_to_chat(message_public: ChatMessagePublic, chat_id: int):
    """Транслировать сообщение всем участникам чата через WebSocket"""
    message_dict = message_public.model_dump(mode='json')
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


def determine_media_type(content_type: str) -> str | None:
    """Определить тип медиа по MIME-типу"""
    if content_type in ALLOWED_IMAGE_TYPES:
        return "image"
    elif content_type in ALLOWED_AUDIO_TYPES:
        return "audio"
    elif content_type in ALLOWED_DOCUMENT_TYPES:
        return "document"
    return None


@router.post("/upload")
@limiter.limit("10/minute")
async def upload_media(
    request: Request,
    file: UploadFile,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Загрузить медиа файл"""
    if file.size and file.size > settings.MEDIA_MAX_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {settings.MEDIA_MAX_SIZE // (1024*1024)}MB"
        )

    content_type = file.content_type
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="File type not allowed. Allowed: images (jpg, png, gif, webp), audio (mp3, wav, ogg), documents (pdf, doc, txt)"
        )

    current_size = get_storage_size()
    if current_size >= settings.MEDIA_STORAGE_LIMIT:
        cleanup_old_files()
        current_size = get_storage_size()
        if current_size >= settings.MEDIA_STORAGE_LIMIT:
            raise HTTPException(
                status_code=507,
                detail="Storage limit exceeded. Please try again later."
            )

    media_type = determine_media_type(content_type)
    if not media_type:
        raise HTTPException(status_code=400, detail="Unable to determine media type")

    original_filename = file.filename or "unknown"
    safe_filename = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{current_user.id}_{original_filename}"
    
    safe_filename = validate_filename(safe_filename)

    media_dir = get_media_dir()
    file_path = media_dir / safe_filename

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file")
    
    if not validate_file_content(file_path, content_type):
        file_path.unlink()
        raise HTTPException(status_code=400, detail="File content does not match declared type")

    file_size = file_path.stat().st_size

    media_url = f"/api/v1/media/files/{safe_filename}"

    return {
        "media_type": media_type,
        "media_filename": original_filename,
        "media_url": media_url,
        "media_size": file_size,
    }


@router.get("/files/{filename}")
async def serve_media_file(
    filename: str,
    session: SessionDep,
    current_user: User = None,
):
    """Служить медиа файлы (без авторизации для публичного доступа)"""
    safe_filename = validate_filename(filename)
    
    media_dir = get_media_dir()
    
    if is_path_traversal_attempt(safe_filename, media_dir):
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = media_dir / safe_filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Файлы доступны без авторизации
    
    content_type = None
    ext = safe_filename.lower().split(".")[-1] if "." in safe_filename else ""

    if ext in ("jpg", "jpeg"):
        content_type = "image/jpeg"
    elif ext == "png":
        content_type = "image/png"
    elif ext == "gif":
        content_type = "image/gif"
    elif ext == "webp":
        content_type = "image/webp"
    elif ext in ("mp3",):
        content_type = "audio/mpeg"
    elif ext == "wav":
        content_type = "audio/wav"
    elif ext == "ogg":
        content_type = "audio/ogg"
    elif ext == "pdf":
        content_type = "application/pdf"
    elif ext in ("doc",):
        content_type = "application/msword"
    elif ext in ("docx",):
        content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif ext == "txt":
        content_type = "text/plain"
    else:
        content_type = "application/octet-stream"

    from fastapi.responses import FileResponse
    return FileResponse(
        path=file_path,
        media_type=content_type,
        filename=safe_filename,
    )


def _get_chat_id_from_filename(filename: str) -> int | None:
    """Извлечь chat_id из имени файла (формат: timestamp_userid_*)"""
    try:
        parts = filename.split('_')
        if len(parts) >= 2:
            return int(parts[1])
    except (ValueError, IndexError):
        pass
    return None


@router.post("/{chat_id}", response_model=ChatMessagePublic)
@limiter.limit("30/minute")
async def create_message(
    request: Request,
    chat_id: int,
    message_in: ChatMessageCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Создать сообщение в чате (текстовое или с медиа)"""
    if message_in.content and len(message_in.content) > MAX_MESSAGE_CONTENT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Message content exceeds maximum length of {MAX_MESSAGE_CONTENT_LENGTH} characters"
        )
    
    chat = crud.get_chat(session=session, chat_id=chat_id, user_id=current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    try:
        message = crud.create_message(
            session=session,
            chat_id=chat_id,
            sender_id=current_user.id,
            content=message_in.content,
            media_type=message_in.media_type,
            media_filename=message_in.media_filename,
            media_url=message_in.media_url,
            media_size=message_in.media_size,
        )

        sender = session.get(User, message.sender_id)
        message_public = ChatMessagePublic(
            id=message.id,
            chat_id=message.chat_id,
            sender_id=message.sender_id,
            sender=UserPublic.model_validate(sender) if sender else None,
            content=message.content,
            media_type=message.media_type,
            media_filename=message.media_filename,
            media_url=message.media_url,
            media_size=message.media_size,
            created_at=message.created_at,
            edited_at=message.edited_at,
        )

        asyncio.create_task(broadcast_message_to_chat(message_public, chat_id))

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
        raise HTTPException(status_code=404, detail="Message not found or you don't have permission")

    sender = session.get(User, message.sender_id)
    return ChatMessagePublic(
        id=message.id,
        chat_id=message.chat_id,
        sender_id=message.sender_id,
        sender=UserPublic.model_validate(sender) if sender else None,
        content=message.content,
        media_type=message.media_type,
        media_filename=message.media_filename,
        media_url=message.media_url,
        media_size=message.media_size,
        created_at=message.created_at,
        edited_at=message.edited_at,
    )


@router.delete("/{message_id}", response_model=Message)
def delete_message(
    message_id: int, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Удалить сообщение"""
    message = session.get(ChatMessage, message_id)
    if not message or message.sender_id != current_user.id:
        raise HTTPException(status_code=404, detail="Message not found or you don't have permission")

    if message.media_filename:
        media_dir = get_media_dir()
        filename = message.media_url.split("/")[-1] if message.media_url else None
        if filename:
            file_path = media_dir / filename
            try:
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted media file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete media file: {e}")

    success = crud.delete_message(
        session=session, message_id=message_id, user_id=current_user.id
    )

    if not success:
        raise HTTPException(status_code=404, detail="Message not found or you don't have permission")

    return Message(message="Message deleted successfully")
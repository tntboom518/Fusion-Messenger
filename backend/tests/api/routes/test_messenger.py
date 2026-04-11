import io
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select, delete

from app.core.db import init_db
from app.models import Chat, ChatMember, ChatMessage, User
from tests.utils.utils import get_superuser_token_headers


@pytest.fixture(scope="module")
def db_session():
    from app.core.db import engine
    with Session(engine) as session:
        init_db(session)
        yield session


@pytest.fixture(scope="module")
def client() -> TestClient:
    from app.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture
def superuser_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture
def test_user(db_session: Session) -> User:
    user = User(
        email="testuser@example.com",
        full_name="Test User",
        hashed_password="$2b$12$test_hash_placeholder",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    yield user
    # Cleanup
    db_session.exec(delete(ChatMessage).where(ChatMessage.sender_id == user.id))
    db_session.exec(delete(ChatMember).where(ChatMember.user_id == user.id))
    db_session.exec(delete(User).where(User.id == user.id))
    db_session.commit()


@pytest.fixture
def second_test_user(db_session: Session) -> User:
    user = User(
        email="seconduser@example.com",
        full_name="Second User",
        hashed_password="$2b$12$test_hash_placeholder",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    yield user
    # Cleanup
    db_session.exec(delete(ChatMessage).where(ChatMessage.sender_id == user.id))
    db_session.exec(delete(ChatMember).where(ChatMember.user_id == user.id))
    db_session.exec(delete(User).where(User.id == user.id))
    db_session.commit()


class TestAuth:
    def test_login_success(self, client: TestClient):
        response = client.post(
            "/api/v1/login/access-token",
            data={"username": "admin@example.com", "password": "Sos222666"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_password(self, client: TestClient):
        response = client.post(
            "/api/v1/login/access-token",
            data={"username": "admin@example.com", "password": "wrongpassword"}
        )
        assert response.status_code in [400, 401]
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client: TestClient):
        response = client.post(
            "/api/v1/login/access-token",
            data={"username": "nonexistent@example.com", "password": "password"}
        )
        assert response.status_code in [400, 401]


class TestChats:
    def test_get_chats(self, client: TestClient, superuser_headers: dict):
        response = client.get("/api/v1/chats/", headers=superuser_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_create_private_chat(self, client: TestClient, superuser_headers: dict, test_user: User):
        response = client.post(
            f"/api/v1/chats/private/{test_user.id}",
            headers=superuser_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["chat_type"] == "private"
        assert len(data["members"]) == 2

    def test_create_private_chat_with_self(self, client: TestClient, superuser_headers: dict):
        response = client.post(
            "/api/v1/chats/private/1",
            headers=superuser_headers
        )
        assert response.status_code == 400
        assert "Cannot create chat with yourself" in response.json()["detail"]


class TestMessages:
    def test_send_text_message(
        self, client: TestClient, superuser_headers: dict,
        db_session: Session, test_user: User
    ):
        # Create a chat first
        chat = Chat(chat_type="private")
        db_session.add(chat)
        db_session.flush()
        
        member1 = ChatMember(chat_id=chat.id, user_id=1)
        member2 = ChatMember(chat_id=chat.id, user_id=test_user.id)
        db_session.add_all([member1, member2])
        db_session.commit()
        
        # Send message
        response = client.post(
            f"/api/v1/media/{chat.id}",
            headers=superuser_headers,
            json={"content": "Hello, World!"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Hello, World!"
        assert data["media_type"] is None
        
        # Cleanup
        db_session.delete(member1)
        db_session.delete(member2)
        db_session.delete(chat)
        db_session.commit()


class TestMediaUpload:
    def test_upload_image(self, client: TestClient, superuser_headers: dict):
        # Create a simple PNG image (1x1 pixel)
        import struct
        import zlib
        
        def create_minimal_png():
            # PNG signature
            signature = b'\x89PNG\r\n\x1a\n'
            # IHDR chunk (13 bytes)
            ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
            ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
            ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
            # IDAT chunk
            raw_data = b'\x00\xff\x00\x00'  # row filter + RGB
            compressed = zlib.compress(raw_data, 9)
            idat_crc = zlib.crc32(b'IDAT' + compressed) & 0xffffffff
            idat = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)
            # IEND chunk
            iend_crc = zlib.crc32(b'IEND') & 0xffffffff
            iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
            return signature + ihdr + idat + iend
        
        png_data = create_minimal_png()
        files = {"file": ("test.png", io.BytesIO(png_data), "image/png")}
        
        response = client.post(
            "/api/v1/media/upload",
            headers=superuser_headers,
            files=files
        )
        assert response.status_code == 200
        data = response.json()
        assert data["media_type"] == "image"
        assert data["media_filename"] == "test.png"
        assert "media_url" in data

    def test_upload_document(self, client: TestClient, superuser_headers: dict):
        files = {"file": ("test.txt", io.BytesIO(b"Hello World"), "text/plain")}
        
        response = client.post(
            "/api/v1/media/upload",
            headers=superuser_headers,
            files=files
        )
        assert response.status_code == 200
        data = response.json()
        assert data["media_type"] == "document"
        assert data["media_filename"] == "test.txt"

    def test_upload_audio(self, client: TestClient, superuser_headers: dict):
        # Simple MP3 file (minimal valid header)
        mp3_data = b'\xff\xfb\x90\x00' + b'\x00' * 100
        files = {"file": ("test.mp3", io.BytesIO(mp3_data), "audio/mpeg")}
        
        response = client.post(
            "/api/v1/media/upload",
            headers=superuser_headers,
            files=files
        )
        assert response.status_code == 200
        data = response.json()
        assert data["media_type"] == "audio"
        assert data["media_filename"] == "test.mp3"

    def test_upload_file_too_large(self, client: TestClient, superuser_headers: dict):
        # Create a file larger than 10MB
        large_content = b'x' * (11 * 1024 * 1024)
        files = {"file": ("large.txt", io.BytesIO(large_content), "text/plain")}
        
        response = client.post(
            "/api/v1/media/upload",
            headers=superuser_headers,
            files=files
        )
        assert response.status_code == 400
        assert "exceeds maximum" in response.json()["detail"]

    def test_upload_invalid_type(self, client: TestClient, superuser_headers: dict):
        files = {"file": ("test.exe", io.BytesIO(b"malicious"), "application/x-executable")}
        
        response = client.post(
            "/api/v1/media/upload",
            headers=superuser_headers,
            files=files
        )
        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"]


class TestMediaMessage:
    def test_send_message_with_media(
        self, client: TestClient, superuser_headers: dict,
        db_session: Session, test_user: User
    ):
        # Create a chat first
        chat = Chat(chat_type="private")
        db_session.add(chat)
        db_session.flush()
        
        member1 = ChatMember(chat_id=chat.id, user_id=1)
        member2 = ChatMember(chat_id=chat.id, user_id=test_user.id)
        db_session.add_all([member1, member2])
        db_session.commit()
        
        # First upload a file
        files = {"file": ("test.txt", io.BytesIO(b"Test content"), "text/plain")}
        upload_response = client.post(
            "/api/v1/media/upload",
            headers=superuser_headers,
            files=files
        )
        media_data = upload_response.json()
        
        # Send message with media
        response = client.post(
            f"/api/v1/media/{chat.id}",
            headers=superuser_headers,
            json={
                "content": "Check this file!",
                "media_type": media_data["media_type"],
                "media_filename": media_data["media_filename"],
                "media_url": media_data["media_url"],
                "media_size": media_data["media_size"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Check this file!"
        assert data["media_type"] == "document"
        assert data["media_filename"] == "test.txt"
        
        # Cleanup
        db_session.delete(member1)
        db_session.delete(member2)
        db_session.delete(chat)
        db_session.commit()

    def test_get_messages_with_media(
        self, client: TestClient, superuser_headers: dict,
        db_session: Session, test_user: User
    ):
        # Create a chat
        chat = Chat(chat_type="private")
        db_session.add(chat)
        db_session.flush()
        
        member1 = ChatMember(chat_id=chat.id, user_id=1)
        member2 = ChatMember(chat_id=chat.id, user_id=test_user.id)
        db_session.add_all([member1, member2])
        
        # Add a message with media
        message = ChatMessage(
            chat_id=chat.id,
            sender_id=1,
            content="Test message with media content",
            media_type="document",
            media_filename="test.txt",
            media_url="/api/v1/media/files/test.txt",
            media_size=100
        )
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)
        
        # Get messages
        response = client.get(
            f"/api/v1/chats/{chat.id}/messages",
            headers=superuser_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        
        # Check that we received our message with media
        found_message = next(
            (m for m in data["data"] if m.get("content") == "Test message with media content"),
            None
        )
        assert found_message is not None, f"Message not found in {data['data']}"
        assert found_message["media_type"] == "document"
        assert found_message["media_filename"] == "test.txt"
        
        # Cleanup
        db_session.delete(message)
        db_session.delete(member1)
        db_session.delete(member2)
        db_session.delete(chat)
        db_session.commit()


class TestStorageLimit:
    def test_storage_limit(self, client: TestClient, superuser_headers: dict):
        """Test that storage size is calculated correctly"""
        from app.api.routes.media import get_storage_size, settings
        
        size = get_storage_size()
        assert size >= 0
        # Check it's within limits
        assert size <= settings.MEDIA_STORAGE_LIMIT


class TestMediaServing:
    def test_serve_media_file(self, client: TestClient, superuser_headers: dict):
        # Upload a file first
        files = {"file": ("serve_test.txt", io.BytesIO(b"Test content"), "text/plain")}
        response = client.post(
            "/api/v1/media/upload",
            headers=superuser_headers,
            files=files
        )
        media_url = response.json()["media_url"]
        
        # Try to serve the file
        file_path = media_url.replace("/api/v1/media/files/", "")
        serve_response = client.get(f"/api/v1/media/files/{file_path}")
        assert serve_response.status_code == 200
        assert serve_response.content == b"Test content"
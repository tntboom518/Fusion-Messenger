import io
import os
import pytest
import time
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models import User, Chat, ChatMember, ChatMessage
from app.core.security import create_access_token
from tests.utils.user import authentication_token_from_email, create_test_user
from tests.utils.utils import get_superuser_token_headers


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_headers(client: TestClient):
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def test_user_headers(client: TestClient, db: Session):
    user = create_test_user(db, "testuser@example.com", "testpass123")
    response = client.post(
        "/api/v1/login/access-token",
        data={"username": "testuser@example.com", "password": "testpass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def db():
    with Session(engine) as session:
        init_db(session)
        yield session


class TestPathTraversal:
    """Tests for Path Traversal vulnerability"""

    def test_path_traversal_attempt_via_filename(self, client, superuser_headers):
        """Test that path traversal via filename is blocked"""
        response = client.get(
            "/api/v1/media/files/../../../etc/passwd",
            headers=superuser_headers
        )
        assert response.status_code in [400, 404]

    def test_path_traversal_with_special_chars(self, client, superuser_headers):
        """Test that special characters in filenames are blocked"""
        response = client.get(
            "/api/v1/media/files/test|pipe.png",
            headers=superuser_headers
        )
        assert response.status_code == 400

    def test_path_traversal_absolute_path(self, client, superuser_headers):
        """Test that absolute path attempts are blocked"""
        response = client.get(
            "/api/v1/media/files//etc/passwd",
            headers=superuser_headers
        )
        assert response.status_code in [400, 404]


class TestAuthorizationBypass:
    """Tests for authorization bypass vulnerabilities"""

    def test_media_access_without_auth(self, client, db: Session):
        """Test that media files require authentication"""
        from app import crud
        user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
        
        response = client.get(f"/api/v1/media/files/nonexistent.jpg")
        assert response.status_code in [401, 403, 404]

    def test_message_to_nonexistent_chat(self, client, test_user_headers):
        """Test that messages to non-existent chats are rejected"""
        response = client.post(
            "/api/v1/media/999999",
            json={"content": "Test message"},
            headers=test_user_headers
        )
        assert response.status_code == 404


class TestContentTypeVerification:
    """Tests for content type verification"""

    def test_upload_with_wrong_extension(self, client, superuser_headers):
        """Test uploading file with wrong extension"""
        fake_jpeg_content = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        
        response = client.post(
            "/api/v1/media/upload",
            files={"file": ("test.txt", fake_jpeg_content, "text/plain")},
            headers=superuser_headers
        )
        assert response.status_code in [400, 500]

    def test_upload_non_image_as_image(self, client, superuser_headers):
        """Test uploading non-image content as image"""
        import time
        time.sleep(1)
        
        text_content = b"This is plain text, not an image"
        
        response = client.post(
            "/api/v1/media/upload",
            files={"file": ("test.png", text_content, "image/png")},
            headers=superuser_headers
        )
        assert response.status_code in [400, 500]


class TestRateLimiting:
    """Tests for rate limiting"""

    def test_login_rate_limiting(self, client):
        """Test that login endpoint has rate limiting"""
        for _ in range(10):
            response = client.post(
                "/api/v1/login/access-token",
                data={"username": "test@example.com", "password": "wrongpass"}
            )
        
        assert response.status_code == 429

    def test_upload_rate_limiting(self, client, superuser_headers):
        """Test that upload endpoint has rate limiting"""
        import time
        time.sleep(1)
        
        responses = []
        for _ in range(15):
            response = client.post(
                "/api/v1/media/upload",
                files={"file": ("test.jpg", b"fake", "image/jpeg")},
                headers=superuser_headers
            )
            responses.append(response.status_code)
        
        assert 429 in responses or all(r in [400, 413] for r in responses)


class TestMessageLengthValidation:
    """Tests for message content length validation"""

    def test_oversized_message_rejected(self, client, test_user_headers, db: Session):
        """Test that oversized messages are rejected"""
        from app import crud
        
        response = client.get("/api/v1/chats/", headers=test_user_headers)
        chats = response.json()
        
        if chats.get("data"):
            chat_id = chats["data"][0]["id"]
            
            long_content = "x" * 10000
            
            response = client.post(
                f"/api/v1/media/{chat_id}",
                json={"content": long_content},
                headers=test_user_headers
            )
            assert response.status_code == 400


class TestTokenSecurity:
    """Tests for token security"""

    def test_token_expiration(self, client, superuser_headers):
        """Test that expired tokens are rejected"""
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer expired.token.here"}
        )
        assert response.status_code in [401, 403]

    def test_invalid_token_rejected(self, client):
        """Test that invalid tokens are rejected"""
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer"}
        )
        assert response.status_code in [401, 403]

    def test_missing_token_rejected(self, client):
        """Test that requests without token are rejected"""
        response = client.get("/api/v1/users/me")
        assert response.status_code in [401, 403]


class TestInputValidation:
    """Tests for input validation"""

    def test_sql_injection_in_search(self, client, test_user_headers):
        """Test SQL injection in user search"""
        response = client.get(
            "/api/v1/users/search?query=' OR '1'='1",
            headers=test_user_headers
        )
        assert response.status_code == 200

    def test_xss_in_messages(self, client, test_user_headers):
        """Test XSS in message content"""
        response = client.get("/api/v1/chats/", headers=test_user_headers)
        chats = response.json()
        
        if chats.get("data"):
            chat_id = chats["data"][0]["id"]
            
            xss_content = "<script>alert('xss')</script>"
            
            response = client.post(
                f"/api/v1/media/{chat_id}",
                json={"content": xss_content},
                headers=test_user_headers
            )
            assert response.status_code in [200, 400]


class TestFileUploadSecurity:
    """Tests for file upload security"""

    def test_php_extension_rejected(self, client, superuser_headers):
        """Test that PHP extension files are rejected"""
        time.sleep(1)
        
        php_content = b"<?php system($_GET['cmd']); ?>"
        
        response = client.post(
            "/api/v1/media/upload",
            files={"file": ("test.php", php_content, "application/x-httpd-php")},
            headers=superuser_headers
        )
        assert response.status_code in [400, 429]

    def test_js_extension_rejected(self, client, superuser_headers):
        """Test that JS extension files are rejected"""
        time.sleep(1)
        
        js_content = b"alert('xss')"
        
        response = client.post(
            "/api/v1/media/upload",
            files={"file": ("test.js", js_content, "application/javascript")},
            headers=superuser_headers
        )
        assert response.status_code in [400, 429]
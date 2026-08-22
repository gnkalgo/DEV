"""Auth HTTP tests. Never place live orders or use real broker credentials."""

from collections.abc import Iterator
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_auth_service
from app.core.config import Settings
from app.core.errors import AuthError
from app.main import create_app
from app.schemas.auth import LoginRequest, RegisterRequest, UserPublic


def _settings() -> Settings:
    return Settings(
        APP_NAME="GNK Algo",
        APP_ENV="test",
        DEBUG=True,
        DATABASE_URL="postgresql+asyncpg://gnkalgo:password@localhost:5432/gnkalgo",
        REDIS_URL="redis://localhost:6379/0",
        JWT_SECRET="test-secret",
        ENCRYPTION_KEY="test-encryption-key",
        TRADING_MODE="PAPER",
        CORS_ORIGINS="http://localhost:3000",
    )


def _public_user() -> UserPublic:
    return UserPublic(
        id=uuid4(),
        email="trader@example.com",
        mobile="9876543210",
        full_name="Test Trader",
        is_active=True,
        is_verified=False,
        created_at=datetime.now(UTC),
    )


class StubAuthService:
    def __init__(self) -> None:
        self.user = _public_user()
        self.token = "test-session-token"

    async def register(self, payload: RegisterRequest, **_kwargs: object) -> UserPublic:
        if str(payload.email).lower() == "taken@example.com":
            raise AuthError(409, "EMAIL_TAKEN", "An account with this email already exists")
        return self.user

    async def login(self, payload: LoginRequest, **_kwargs: object) -> tuple[UserPublic, str]:
        if payload.password == "WrongPass!2345":
            raise AuthError(401, "INVALID_CREDENTIALS", "Invalid email or password")
        return self.user, self.token

    async def logout(self, token: str | None, **_kwargs: object) -> None:
        return None

    async def user_from_session_token(self, token: str | None) -> SimpleNamespace:
        if token != self.token:
            raise AuthError(401, "UNAUTHORIZED", "Authentication required")
        return SimpleNamespace(**self.user.model_dump())


@pytest.fixture
def stub() -> StubAuthService:
    return StubAuthService()


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, stub: StubAuthService) -> Iterator[TestClient]:
    settings = _settings()
    monkeypatch.setattr("app.main.init_engine", lambda _s: None)
    monkeypatch.setattr("app.main.init_redis", lambda _s: None)
    monkeypatch.setattr("app.main.dispose_engine", AsyncMock())
    monkeypatch.setattr("app.main.close_redis", AsyncMock())
    app = create_app(settings)
    app.dependency_overrides[get_auth_service] = lambda: stub
    with TestClient(app) as test_client:
        yield test_client


def _register_body(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "full_name": "Test Trader",
        "email": "trader@example.com",
        "mobile": "9876543210",
        "password": "StrongPass!2345",
        "confirm_password": "StrongPass!2345",
    }
    body.update(overrides)
    return body


def test_register_success(client: TestClient) -> None:
    response = client.post("/api/v1/auth/register", json=_register_body())
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["user"]["email"] == "trader@example.com"
    assert "password" not in body["user"]
    assert "password_hash" not in body["user"]


def test_register_weak_password(client: TestClient) -> None:
    response = client.post("/api/v1/auth/register", json=_register_body(password="short", confirm_password="short"))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_register_duplicate_email(client: TestClient) -> None:
    response = client.post("/api/v1/auth/register", json=_register_body(email="taken@example.com"))
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EMAIL_TAKEN"


def test_login_sets_httponly_cookie(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "trader@example.com", "password": "StrongPass!2345"},
    )
    assert response.status_code == 200
    cookie = response.cookies.get("gnkalgo_session")
    assert cookie == "test-session-token"
    header = response.headers.get("set-cookie", "")
    assert "HttpOnly" in header
    assert "password" not in response.text


def test_login_invalid_credentials(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "trader@example.com", "password": "WrongPass!2345"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_me_requires_session(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_me_and_logout_with_cookie(client: TestClient) -> None:
    client.post("/api/v1/auth/login", json={"email": "trader@example.com", "password": "StrongPass!2345"})
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["user"]["email"] == "trader@example.com"
    logout = client.post("/api/v1/auth/logout")
    assert logout.status_code == 200
    assert logout.json()["success"] is True

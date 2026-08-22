"""Phase 1 health and readiness tests. These tests never contact a real broker."""

from collections.abc import Iterator
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def settings() -> Settings:
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


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, settings: Settings) -> Iterator[TestClient]:
    monkeypatch.setattr("app.main.init_engine", lambda _s: None)
    monkeypatch.setattr("app.main.init_redis", lambda _s: None)
    monkeypatch.setattr("app.main.dispose_engine", AsyncMock())
    monkeypatch.setattr("app.main.close_redis", AsyncMock())
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client


def test_root(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "gnkalgo-api"
    assert body["status"] == "ok"
    assert body["trading_mode"] == "PAPER"


def test_health(client: TestClient) -> None:
    for path in ("/health", "/api/v1/health"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "service": "gnkalgo-api"}
        assert "X-Request-ID" in response.headers


def test_ready_ok(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.api.v1.health.ping_database", AsyncMock())
    monkeypatch.setattr("app.api.v1.health.ping_redis", AsyncMock())
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"]["database"] == "ok"
    assert body["checks"]["redis"] == "ok"


def test_ready_unavailable(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.api.v1.health.ping_database", AsyncMock(side_effect=RuntimeError("down")))
    monkeypatch.setattr("app.api.v1.health.ping_redis", AsyncMock())
    response = client.get("/api/v1/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "SERVICE_UNAVAILABLE"


def test_trading_mode_field_default_is_paper() -> None:
    assert Settings.model_fields["trading_mode"].default == "PAPER"

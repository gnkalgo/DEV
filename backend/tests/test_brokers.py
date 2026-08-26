"""Broker API tests with stub service."""

from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_broker_service
from app.schemas.broker import BrokerCreateRequest, BrokerPublic
from tests.test_auth import StubAuthService, _settings


class StubBrokerService:
    async def list_brokers(self, user_id):
        return [
            BrokerPublic(
                id=uuid4(),
                broker="MOCK",
                client_id="MOCK-1",
                status="DISCONNECTED",
                has_api_key=False,
                has_api_secret=False,
                has_totp=False,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        ]

    async def save_broker(self, user_id, payload: BrokerCreateRequest):
        return (await self.list_brokers(user_id))[0]

    async def connect(self, user_id, broker_account_id, payload=None):
        broker = (await self.list_brokers(user_id))[0]
        return broker.model_copy(update={"status": "CONNECTED"}), {"broker": "MOCK"}

    async def disconnect(self, user_id, broker_account_id):
        return (await self.list_brokers(user_id))[0]

    async def test_connection(self, user_id, broker_account_id):
        broker = (await self.list_brokers(user_id))[0]
        return broker, {"broker": "MOCK"}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    settings = _settings()
    monkeypatch.setattr("app.main.init_engine", lambda _s: None)
    monkeypatch.setattr("app.main.init_redis", lambda _s: None)
    monkeypatch.setattr("app.main.dispose_engine", AsyncMock())
    monkeypatch.setattr("app.main.close_redis", AsyncMock())
    from app.api.deps import get_auth_service
    from app.main import create_app

    app = create_app(settings)
    app.dependency_overrides[get_auth_service] = lambda: StubAuthService()
    app.dependency_overrides[get_broker_service] = lambda: StubBrokerService()
    with TestClient(app) as test_client:
        yield test_client


def _login(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "trader@example.com", "password": "StrongPass!2345"},
    )
    assert response.status_code == 200


def test_brokers_require_auth(client: TestClient) -> None:
    response = client.get("/api/v1/brokers")
    assert response.status_code == 401


def test_list_brokers(client: TestClient) -> None:
    _login(client)
    response = client.get("/api/v1/brokers")
    assert response.status_code == 200
    assert response.json()["brokers"][0]["broker"] == "MOCK"
    broker = response.json()["brokers"][0]
    assert "api_key" not in broker
    assert "api_secret" not in broker


def test_save_broker(client: TestClient) -> None:
    _login(client)
    response = client.post(
        "/api/v1/brokers",
        json={"broker": "MOCK", "client_id": "MOCK-1"},
    )
    assert response.status_code == 201
    assert response.json()["success"] is True

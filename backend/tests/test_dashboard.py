"""Dashboard auth tests. Never contact a broker."""

from collections.abc import Iterator
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_auth_service
from tests.test_auth import StubAuthService, _settings


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    settings = _settings()
    stub = StubAuthService()
    monkeypatch.setattr("app.main.init_engine", lambda _s: None)
    monkeypatch.setattr("app.main.init_redis", lambda _s: None)
    monkeypatch.setattr("app.main.dispose_engine", AsyncMock())
    monkeypatch.setattr("app.main.close_redis", AsyncMock())
    from app.main import create_app

    app = create_app(settings)
    app.dependency_overrides[get_auth_service] = lambda: stub
    with TestClient(app) as test_client:
        yield test_client


def test_dashboard_requires_auth(client: TestClient) -> None:
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_dashboard_snapshot_is_mock_labeled(client: TestClient) -> None:
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "trader@example.com", "password": "StrongPass!2345"},
    )
    assert login.status_code == 200
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200
    body = response.json()
    assert body["trading_mode"] == "PAPER"
    assert body["capital"]["mock_labeled"] is True
    assert body["broker"]["status"] == "DISCONNECTED"
    assert body["order_book"]["source"] == "MOCK"
    assert body["signals"][0]["status"] == "PLACEHOLDER"
    assert "api_secret" not in response.text
    assert "access_token" not in response.text

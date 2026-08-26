"""Dashboard auth tests. Never contact a broker."""

from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_auth_service, get_db_session, get_redis
from app.schemas.dashboard import (
    BrokerStatus,
    CapitalBlock,
    DashboardResponse,
    IpDetails,
    MarketStatus,
    OrderBook,
    OrderBookLevel,
    SignalRow,
)
from tests.test_auth import StubAuthService, _settings


class _StubDashboardService:
    def __init__(self, *_args: object, **_kwargs: object) -> None:
        pass

    async def build(self, user_id):
        return DashboardResponse(
            trading_mode="PAPER",
            environment="test",
            market=MarketStatus(status="CLOSED", segment="NSE", note="test"),
            broker=BrokerStatus(status="DISCONNECTED", broker=None, note="test"),
            capital=CapitalBlock(
                mock_labeled=True,
                available="0.00",
                margin_used="0.00",
                day_pnl="0.00",
                exposure="0.00",
            ),
            ip_details=IpDetails(
                application_ip="not configured",
                broker_api_ip="not configured",
                connection_status="UNKNOWN",
                last_verified=None,
                environment="test",
            ),
            signals=[
                SignalRow(
                    ticker="—",
                    segment="EQ",
                    ai_trend="—",
                    confidence="—",
                    strategy_state="SHELL",
                    entry="—",
                    sl="—",
                    target="—",
                    status="PLACEHOLDER",
                )
            ],
            positions=[],
            orders=[],
            order_book=OrderBook(
                symbol="NIFTY",
                source="MOCK",
                bids=[OrderBookLevel(price="0.00", quantity=0)],
                asks=[OrderBookLevel(price="0.00", quantity=0)],
            ),
        )


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    settings = _settings()
    monkeypatch.setattr("app.main.init_engine", lambda _s: None)
    monkeypatch.setattr("app.main.init_redis", lambda _s: None)
    monkeypatch.setattr("app.main.dispose_engine", AsyncMock())
    monkeypatch.setattr("app.main.close_redis", AsyncMock())
    monkeypatch.setattr("app.api.v1.dashboard.DashboardService", _StubDashboardService)
    from app.main import create_app

    app = create_app(settings)
    app.dependency_overrides[get_auth_service] = lambda: StubAuthService()

    async def _session():
        yield MagicMock()

    app.dependency_overrides[get_db_session] = _session
    app.dependency_overrides[get_redis] = lambda: MagicMock()
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

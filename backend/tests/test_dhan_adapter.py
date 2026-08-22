"""Dhan adapter tests with mocked HTTP. Never call live Dhan APIs in CI."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.brokers.dhan import DhanBrokerAdapter
from app.brokers.exceptions import BrokerUnsupportedError
from app.brokers.models import BrokerCredentials, OrderRequest


@pytest.fixture
def adapter() -> DhanBrokerAdapter:
    return DhanBrokerAdapter(
        BrokerCredentials(client_id="1000000001", access_token="test-jwt-token")
    )


@pytest.mark.asyncio
async def test_dhan_profile_authenticate(adapter: DhanBrokerAdapter) -> None:
    response = httpx.Response(
        200,
        json={"dhanClientId": "1000000001", "tokenValidity": "tomorrow", "activeSegment": "Equity"},
    )
    with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock, return_value=response):
        meta = await adapter.authenticate()
    assert meta["client_id"] == "1000000001"


@pytest.mark.asyncio
async def test_dhan_unsupported_ltp(adapter: DhanBrokerAdapter) -> None:
    with pytest.raises(BrokerUnsupportedError):
        await adapter.get_ltp("NIFTY", "NSE")


@pytest.mark.asyncio
async def test_dhan_place_order_maps_response(adapter: DhanBrokerAdapter) -> None:
    response = httpx.Response(200, json={"orderId": "112111182198", "orderStatus": "PENDING"})
    with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock, return_value=response):
        result = await adapter.place_order(
            OrderRequest(
                symbol="RELIANCE",
                exchange="NSE",
                side="BUY",
                order_type="MARKET",
                quantity=1,
                security_id="11536",
            )
        )
    assert result.broker_order_id == "112111182198"
    assert result.status == "PENDING"

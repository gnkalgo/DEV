"""Mock broker adapter unit tests. Never place live orders."""

import pytest

from app.brokers.exceptions import BrokerError
from app.brokers.mock import MockBrokerAdapter
from app.brokers.models import BrokerCredentials, OrderRequest


@pytest.fixture
def adapter() -> MockBrokerAdapter:
    return MockBrokerAdapter(BrokerCredentials(client_id="MOCK-1"))


@pytest.mark.asyncio
async def test_mock_authenticate(adapter: MockBrokerAdapter) -> None:
    meta = await adapter.authenticate()
    assert meta["broker"] == "MOCK"


@pytest.mark.asyncio
async def test_mock_market_order_fills(adapter: MockBrokerAdapter) -> None:
    await adapter.authenticate()
    response = await adapter.place_order(
        OrderRequest(symbol="NIFTY", exchange="NSE", side="BUY", order_type="MARKET", quantity=1)
    )
    assert response.success is True
    assert response.status == "FILLED"
    positions = await adapter.get_positions()
    assert len(positions) == 1


@pytest.mark.asyncio
async def test_mock_reject_symbol(adapter: MockBrokerAdapter) -> None:
    await adapter.authenticate()
    with pytest.raises(BrokerError) as exc:
        await adapter.place_order(
            OrderRequest(symbol="REJECT", exchange="NSE", side="BUY", order_type="MARKET", quantity=1)
        )
    assert exc.value.code == "ORDER_REJECTED"


@pytest.mark.asyncio
async def test_mock_partial_fill(adapter: MockBrokerAdapter) -> None:
    await adapter.authenticate()
    response = await adapter.place_order(
        OrderRequest(symbol="PARTIAL", exchange="NSE", side="BUY", order_type="LIMIT", quantity=10, price=100)
    )
    assert response.status == "PARTIALLY_FILLED"
    assert response.filled_quantity == 5


@pytest.mark.asyncio
async def test_mock_cancel_order(adapter: MockBrokerAdapter) -> None:
    await adapter.authenticate()
    placed = await adapter.place_order(
        OrderRequest(symbol="RELIANCE", exchange="NSE", side="BUY", order_type="LIMIT", quantity=1, price=100)
    )
    cancelled = await adapter.cancel_order(placed.broker_order_id or "")
    assert cancelled.status == "CANCELLED"

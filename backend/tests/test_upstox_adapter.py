from app.brokers.base import OrderRequest
from app.brokers.upstox import UpstoxAdapter


def test_upstox_requires_oauth_access_token():
    adapter = UpstoxAdapter("")
    assert adapter.access_token == ""


def test_upstox_order_uses_instrument_token(monkeypatch):
    captured = {}

    async def fake_request(method, path, **kwargs):
        captured.update(method=method, path=path, **kwargs)
        return {"data": {"order_id": "UP-123"}}

    adapter = UpstoxAdapter("oauth-token")
    monkeypatch.setattr(adapter, "_request", fake_request)

    import asyncio
    response = asyncio.run(adapter.place_order(OrderRequest(
        symbol="RELIANCE",
        exchange="NSE",
        side="BUY",
        quantity=1,
        order_type="MARKET",
        product_type="INTRADAY",
        instrument_token="NSE_EQ|INE002A01018",
    )))
    assert response.broker_order_id == "UP-123"
    assert captured["path"] == "/v2/order/place"
    assert captured["json"]["instrument_token"] == "NSE_EQ|INE002A01018"
    assert captured["json"]["product"] == "I"

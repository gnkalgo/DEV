import httpx

from app.brokers.base import BrokerAdapter, OrderRequest, OrderResponse
from app.config import settings


class UpstoxAdapter(BrokerAdapter):
    """Upstox OAuth access-token adapter. Never accepts broker passwords."""

    def __init__(self, access_token: str):
        self.access_token = access_token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, path: str, *, order_api: bool = False, **kwargs) -> dict:
        base = settings.upstox_order_base_url if order_api else settings.upstox_api_base_url
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method, f"{base}{path}", headers=self._headers(), **kwargs)
        if response.status_code >= 400:
            detail = response.text[:500]
            raise RuntimeError(f"Upstox API error {response.status_code}: {detail}")
        return response.json() if response.content else {}

    async def authenticate(self, credentials: dict) -> bool:
        self.access_token = credentials.get("access_token") or ""
        if not self.access_token:
            raise ValueError("Upstox OAuth access token is required")
        await self._request("GET", "/v2/user/profile")
        return True

    async def get_funds(self) -> dict:
        return await self._request("GET", "/v2/user/get-funds-and-margin")

    async def get_holdings(self) -> list[dict]:
        data = await self._request("GET", "/v2/portfolio/long-term-holdings")
        return data.get("data", [])

    async def get_positions(self) -> list[dict]:
        data = await self._request("GET", "/v2/portfolio/short-term-positions")
        return data.get("data", [])

    async def get_orders(self) -> list[dict]:
        data = await self._request("GET", "/v2/order/retrieve-all")
        return data.get("data", [])

    async def place_order(self, order: OrderRequest) -> OrderResponse:
        if not order.instrument_token:
            raise RuntimeError("Upstox orders require an instrument token")
        product = "I" if order.product_type.upper() in ("INTRADAY", "INTRA") else "D"
        payload = {
            "quantity": order.quantity,
            "product": product,
            "validity": "DAY",
            "price": order.price or 0,
            "tag": (order.correlation_id or "gnkalgo")[:20],
            "instrument_token": order.instrument_token,
            "order_type": order.order_type,
            "transaction_type": order.side,
            "disclosed_quantity": 0,
            "trigger_price": 0,
            "is_amo": False,
            "market_protection": -1,
        }
        data = await self._request("POST", "/v2/order/place", order_api=True, json=payload)
        result = data.get("data", {})
        order_id = str(result.get("order_id", ""))
        return OrderResponse(order_id=order_id, broker_order_id=order_id, status="PENDING")

    async def modify_order(self, order_id: str, changes: dict) -> OrderResponse:
        data = await self._request("PUT", "/v2/order/modify", order_api=True, json={**changes, "order_id": order_id})
        result = data.get("data", {})
        return OrderResponse(order_id=order_id, broker_order_id=str(result.get("order_id", order_id)), status="MODIFIED")

    async def cancel_order(self, order_id: str) -> OrderResponse:
        await self._request("DELETE", "/v2/order/cancel", order_api=True, params={"order_id": order_id})
        return OrderResponse(order_id=order_id, broker_order_id=order_id, status="CANCELLED")

    async def get_market_quote(self, symbols: list[str]) -> dict:
        return await self._request("GET", "/v2/market-quote/ltp", params={"instrument_key": ",".join(symbols)})

    async def health_check(self) -> bool:
        try:
            await self._request("GET", "/v2/user/profile")
            return True
        except Exception:
            return False

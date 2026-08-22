"""DhanHQ v2 adapter. Official documented endpoints only — no invented URLs."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode

import httpx

from app.brokers.base import BrokerAdapter
from app.brokers.exceptions import BrokerAuthError, BrokerError, BrokerUnsupportedError
from app.brokers.models import (
    BrokerCredentials,
    HoldingInfo,
    MarginInfo,
    OrderRequest,
    OrderResponse,
    PositionInfo,
    Quote,
)

_DHAN_API_BASE = "https://api.dhan.co/v2"
_DHAN_AUTH_BASE = "https://auth.dhan.co"


class DhanBrokerAdapter(BrokerAdapter):
    """Wraps documented DhanHQ v2 HTTP APIs.

    Auth: https://dhanhq.co/docs/v2/authentication/
    Orders: https://dhanhq.co/docs/v2/orders/

    Market data helpers (LTP/OHLCV/option chain) return UNSUPPORTED_OPERATION unless
    backed by official docs in a future phase. Data API subscription may be required.
    """

    broker_code = "DHAN"

    def __init__(self, credentials: BrokerCredentials) -> None:
        super().__init__(credentials)
        self._access_token = credentials.access_token
        self._client: httpx.AsyncClient | None = None

    def _headers(self) -> dict[str, str]:
        if not self._access_token:
            raise BrokerAuthError("Access token is required for Dhan API calls")
        return {
            "access-token": self._access_token,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def _client_instance(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def _request(
        self,
        method: str,
        url: str,
        *,
        json_body: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        client = await self._client_instance()
        response = await client.request(
            method,
            url,
            headers=self._headers(),
            json=json_body,
            params=params,
        )
        text = response.text
        try:
            payload = response.json() if text else {}
        except json.JSONDecodeError:
            payload = {"raw": text}
        if response.status_code >= 400:
            message = payload.get("message") or payload.get("error") or "Dhan API request failed"
            if response.status_code in {401, 403}:
                raise BrokerAuthError(str(message))
            raise BrokerError("BROKER_API_ERROR", str(message))
        if isinstance(payload, dict):
            return payload
        return {"data": payload}

    async def authenticate(self) -> dict[str, Any]:
        if self._access_token:
            profile = await self._request("GET", f"{_DHAN_API_BASE}/profile")
            return {
                "broker": self.broker_code,
                "client_id": profile.get("dhanClientId", self.credentials.client_id),
                "token_validity": profile.get("tokenValidity"),
                "active_segment": profile.get("activeSegment"),
            }

        if self.credentials.totp and self.credentials.api_key:
            query = urlencode(
                {
                    "dhanClientId": self.credentials.client_id,
                    "pin": self.credentials.api_key,
                    "totp": self.credentials.totp,
                }
            )
            client = await self._client_instance()
            response = await client.post(f"{_DHAN_AUTH_BASE}/app/generateAccessToken?{query}")
            payload = response.json()
            if response.status_code >= 400 or "accessToken" not in payload:
                raise BrokerAuthError("Failed to generate Dhan access token")
            self._access_token = str(payload["accessToken"])
            return {
                "broker": self.broker_code,
                "client_id": payload.get("dhanClientId", self.credentials.client_id),
                "expiry_time": payload.get("expiryTime"),
            }

        raise BrokerAuthError(
            "Provide an access token or enable TOTP with client ID and trading PIN"
        )

    async def refresh_session(self) -> dict[str, Any]:
        if not self._access_token:
            raise BrokerAuthError("No access token to renew")
        client = await self._client_instance()
        response = await client.post(
            f"{_DHAN_API_BASE}/RenewToken",
            headers={
                "access-token": self._access_token,
                "dhanClientId": self.credentials.client_id,
            },
        )
        payload = response.json() if response.text else {}
        if response.status_code >= 400:
            raise BrokerAuthError("Failed to renew Dhan token")
        if "accessToken" in payload:
            self._access_token = str(payload["accessToken"])
        return await self.authenticate()

    async def disconnect(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def get_ltp(self, symbol: str, exchange: str) -> Quote:
        raise BrokerUnsupportedError("get_ltp")

    async def get_ohlcv(
        self,
        symbol: str,
        exchange: str,
        *,
        interval: str,
        start: datetime,
        end: datetime,
    ) -> list[dict[str, Any]]:
        raise BrokerUnsupportedError("get_ohlcv")

    async def get_option_chain(self, symbol: str, exchange: str) -> dict[str, Any]:
        raise BrokerUnsupportedError("get_option_chain")

    async def get_margin(self) -> MarginInfo:
        raise BrokerUnsupportedError("get_margin")

    async def get_positions(self) -> list[PositionInfo]:
        raise BrokerUnsupportedError("get_positions")

    async def get_holdings(self) -> list[HoldingInfo]:
        raise BrokerUnsupportedError("get_holdings")

    def _map_exchange_segment(self, exchange: str, segment: str) -> str:
        exchange = exchange.upper()
        segment = segment.upper()
        if segment in {"FNO", "DERIVATIVE"}:
            return f"{exchange}_FNO"
        return f"{exchange}_EQ"

    def _map_order_type(self, order_type: str) -> str:
        mapping = {
            "MARKET": "MARKET",
            "LIMIT": "LIMIT",
            "SL": "STOP_LOSS",
            "SL-M": "STOP_LOSS_MARKET",
        }
        return mapping.get(order_type.upper(), order_type.upper())

    async def place_order(self, order: OrderRequest) -> OrderResponse:
        if not order.security_id:
            raise BrokerError("MISSING_SECURITY_ID", "security_id is required for Dhan orders")
        body = {
            "dhanClientId": self.credentials.client_id,
            "transactionType": order.side,
            "exchangeSegment": self._map_exchange_segment(order.exchange, order.segment),
            "productType": order.product_type,
            "orderType": self._map_order_type(order.order_type),
            "validity": order.validity,
            "securityId": order.security_id,
            "quantity": order.quantity,
            "price": float(order.price or 0),
            "triggerPrice": 0,
            "afterMarketOrder": False,
        }
        payload = await self._request("POST", f"{_DHAN_API_BASE}/orders", json_body=body)
        return OrderResponse(
            success=True,
            broker_order_id=str(payload.get("orderId", "")),
            status=str(payload.get("orderStatus", "SUBMITTED")),
            raw=payload,
        )

    async def modify_order(
        self,
        broker_order_id: str,
        *,
        quantity: int | None = None,
        price: float | None = None,
        order_type: str | None = None,
    ) -> OrderResponse:
        body: dict[str, Any] = {
            "dhanClientId": self.credentials.client_id,
            "orderId": broker_order_id,
            "orderType": self._map_order_type(order_type or "LIMIT"),
            "validity": "DAY",
        }
        if quantity is not None:
            body["quantity"] = quantity
        if price is not None:
            body["price"] = price
        payload = await self._request(
            "PUT",
            f"{_DHAN_API_BASE}/orders/{broker_order_id}",
            json_body=body,
        )
        return OrderResponse(
            success=True,
            broker_order_id=str(payload.get("orderId", broker_order_id)),
            status=str(payload.get("orderStatus", "SUBMITTED")),
            raw=payload,
        )

    async def cancel_order(self, broker_order_id: str) -> OrderResponse:
        payload = await self._request("DELETE", f"{_DHAN_API_BASE}/orders/{broker_order_id}")
        return OrderResponse(
            success=True,
            broker_order_id=str(payload.get("orderId", broker_order_id)),
            status=str(payload.get("orderStatus", "CANCELLED")),
            raw=payload,
        )

    async def get_order_status(self, broker_order_id: str) -> OrderResponse:
        payload = await self._request("GET", f"{_DHAN_API_BASE}/orders/{broker_order_id}")
        status = str(payload.get("orderStatus", payload.get("status", "UNKNOWN")))
        filled = int(payload.get("filledQty") or payload.get("filledQuantity") or 0)
        return OrderResponse(
            success=True,
            broker_order_id=broker_order_id,
            status=status,
            filled_quantity=filled,
            raw=payload,
        )

    @property
    def access_token(self) -> str | None:
        return self._access_token

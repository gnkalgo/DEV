"""Broker adapter contract. Application code depends only on these methods."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from app.brokers.models import (
    BrokerCredentials,
    HoldingInfo,
    MarginInfo,
    OrderRequest,
    OrderResponse,
    PositionInfo,
    Quote,
)


class BrokerAdapter(ABC):
    broker_code: str

    def __init__(self, credentials: BrokerCredentials) -> None:
        self.credentials = credentials

    @abstractmethod
    async def authenticate(self) -> dict[str, Any]:
        """Establish or validate a session. Returns non-secret metadata only."""

    @abstractmethod
    async def refresh_session(self) -> dict[str, Any]:
        """Refresh an expiring session when supported."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Tear down adapter-local session state."""

    @abstractmethod
    async def get_ltp(self, symbol: str, exchange: str) -> Quote:
        ...

    @abstractmethod
    async def get_ohlcv(
        self,
        symbol: str,
        exchange: str,
        *,
        interval: str,
        start: datetime,
        end: datetime,
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def get_option_chain(self, symbol: str, exchange: str) -> dict[str, Any]:
        ...

    @abstractmethod
    async def get_margin(self) -> MarginInfo:
        ...

    @abstractmethod
    async def get_positions(self) -> list[PositionInfo]:
        ...

    @abstractmethod
    async def get_holdings(self) -> list[HoldingInfo]:
        ...

    @abstractmethod
    async def place_order(self, order: OrderRequest) -> OrderResponse:
        ...

    @abstractmethod
    async def modify_order(
        self,
        broker_order_id: str,
        *,
        quantity: int | None = None,
        price: float | None = None,
        order_type: str | None = None,
    ) -> OrderResponse:
        ...

    @abstractmethod
    async def cancel_order(self, broker_order_id: str) -> OrderResponse:
        ...

    @abstractmethod
    async def get_order_status(self, broker_order_id: str) -> OrderResponse:
        ...

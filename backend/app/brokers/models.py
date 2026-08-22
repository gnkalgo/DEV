"""Normalized broker models. Vendor payloads map into these shapes inside adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass(slots=True)
class Quote:
    symbol: str
    exchange: str
    ltp: Decimal
    timestamp: datetime


@dataclass(slots=True)
class OrderRequest:
    symbol: str
    exchange: str
    side: str
    order_type: str
    quantity: int
    price: Decimal | None = None
    segment: str = "EQ"
    security_id: str | None = None
    product_type: str = "INTRADAY"
    validity: str = "DAY"


@dataclass(slots=True)
class OrderResponse:
    success: bool
    broker_order_id: str | None
    status: str
    message: str | None = None
    filled_quantity: int = 0
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class MarginInfo:
    available: Decimal
    used: Decimal
    currency: str = "INR"


@dataclass(slots=True)
class PositionInfo:
    symbol: str
    exchange: str
    quantity: int
    average_price: Decimal
    unrealized_pnl: Decimal = Decimal("0")


@dataclass(slots=True)
class HoldingInfo:
    symbol: str
    exchange: str
    quantity: int
    average_price: Decimal


@dataclass(slots=True)
class BrokerCredentials:
    client_id: str
    api_key: str | None = None
    api_secret: str | None = None
    totp: str | None = None
    access_token: str | None = None

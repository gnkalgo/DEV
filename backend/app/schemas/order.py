"""Order API schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.models.enums import OrderSide, OrderType


class OrderCreateRequest(BaseModel):
    broker_account_id: UUID
    symbol: str = Field(min_length=1, max_length=64)
    exchange: str = Field(default="NSE", max_length=16)
    segment: str = Field(default="EQ", max_length=32)
    side: OrderSide
    order_type: OrderType
    quantity: int = Field(gt=0)
    price: float | None = None
    security_id: str | None = Field(default=None, max_length=32)
    product_type: str = Field(default="INTRADAY", max_length=16)
    idempotency_key: str | None = Field(default=None, max_length=128)


class OrderPublic(BaseModel):
    id: UUID
    broker_account_id: UUID
    symbol: str
    exchange: str
    segment: str
    side: str
    order_type: str
    quantity: int
    price: str | None
    status: str
    broker_order_id: str | None
    source: str
    created_at: datetime
    updated_at: datetime


class OrderListResponse(BaseModel):
    orders: list[OrderPublic]


class OrderDetailResponse(BaseModel):
    order: OrderPublic
    events: list[dict[str, object]]


class PositionPublic(BaseModel):
    id: UUID
    symbol: str
    exchange: str
    quantity: int
    average_price: str
    unrealized_pnl: str
    updated_at: datetime


class PositionListResponse(BaseModel):
    positions: list[PositionPublic]


class PortfolioResponse(BaseModel):
    trading_mode: str
    mock_labeled: bool
    available: str
    margin_used: str
    day_pnl: str
    exposure: str
    positions_count: int
    orders_count: int

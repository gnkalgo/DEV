"""Dashboard DTOs. Capital and book data are mock-labeled until a broker is connected."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class MarketStatus(BaseModel):
    status: str
    segment: str = "NSE"
    note: str


class BrokerStatus(BaseModel):
    status: str
    broker: str | None = None
    note: str


class CapitalBlock(BaseModel):
    mock_labeled: bool = True
    currency: str = "INR"
    available: str
    margin_used: str
    day_pnl: str
    exposure: str


class IpDetails(BaseModel):
    application_ip: str
    broker_api_ip: str
    connection_status: str
    last_verified: datetime | None
    environment: str


class SignalRow(BaseModel):
    ticker: str
    segment: str
    ai_trend: str
    confidence: str
    strategy_state: str
    entry: str
    sl: str
    target: str
    status: str


class PositionRow(BaseModel):
    symbol: str
    exchange: str
    quantity: int
    average_price: str
    unrealized_pnl: str


class OrderRow(BaseModel):
    id: str
    symbol: str
    side: str
    order_type: str
    quantity: int
    status: str
    source: str = "MOCK"


class OrderBookLevel(BaseModel):
    price: str
    quantity: int


class OrderBook(BaseModel):
    symbol: str
    source: str = "MOCK"
    bids: list[OrderBookLevel]
    asks: list[OrderBookLevel]


class DashboardResponse(BaseModel):
    trading_mode: str
    environment: str
    market: MarketStatus
    broker: BrokerStatus
    capital: CapitalBlock
    ip_details: IpDetails
    signals: list[SignalRow]
    positions: list[PositionRow]
    orders: list[OrderRow]
    order_book: OrderBook

"""SQLAlchemy ORM models. Alembic is the only production schema path."""

from app.db.models.audit import AuditLog
from app.db.models.broker import BrokerAccount, BrokerToken
from app.db.models.enums import (
    BrokerCode,
    BrokerConnectionStatus,
    OrderSide,
    OrderStatus,
    OrderType,
)
from app.db.models.order import Order, OrderEvent
from app.db.models.position import Position
from app.db.models.timescale import MarketOhlcv, MarketTick, MlFeature, MlPrediction, PortfolioSnapshot
from app.db.models.user import User, UserSession

OLTP_TABLES = (
    "users",
    "user_sessions",
    "broker_accounts",
    "broker_tokens",
    "orders",
    "order_events",
    "positions",
    "audit_logs",
)

HYPERTABLES = (
    "market_ticks",
    "market_ohlcv",
    "ml_features",
    "ml_predictions",
    "portfolio_snapshots",
)

__all__ = [
    "AuditLog",
    "BrokerAccount",
    "BrokerCode",
    "BrokerConnectionStatus",
    "BrokerToken",
    "HYPERTABLES",
    "MarketOhlcv",
    "MarketTick",
    "MlFeature",
    "MlPrediction",
    "OLTP_TABLES",
    "Order",
    "OrderEvent",
    "OrderSide",
    "OrderStatus",
    "OrderType",
    "PortfolioSnapshot",
    "Position",
    "User",
    "UserSession",
]

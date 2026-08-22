"""Order state machine transitions per architecture §10."""

from __future__ import annotations

from app.core.errors import ServiceError
from app.db.models.enums import OrderStatus

_ALLOWED: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.CREATED: {OrderStatus.VALIDATING, OrderStatus.REJECTED, OrderStatus.FAILED},
    OrderStatus.VALIDATING: {OrderStatus.APPROVED, OrderStatus.REJECTED, OrderStatus.FAILED},
    OrderStatus.APPROVED: {OrderStatus.SUBMITTED, OrderStatus.REJECTED, OrderStatus.FAILED},
    OrderStatus.SUBMITTED: {
        OrderStatus.ACKNOWLEDGED,
        OrderStatus.REJECTED,
        OrderStatus.FAILED,
        OrderStatus.EXPIRED,
    },
    OrderStatus.ACKNOWLEDGED: {
        OrderStatus.PARTIALLY_FILLED,
        OrderStatus.FILLED,
        OrderStatus.CANCEL_REQUESTED,
        OrderStatus.REJECTED,
        OrderStatus.EXPIRED,
    },
    OrderStatus.PARTIALLY_FILLED: {
        OrderStatus.PARTIALLY_FILLED,
        OrderStatus.FILLED,
        OrderStatus.CANCEL_REQUESTED,
        OrderStatus.EXPIRED,
    },
    OrderStatus.CANCEL_REQUESTED: {
        OrderStatus.CANCELLED,
        OrderStatus.FILLED,
        OrderStatus.PARTIALLY_FILLED,
        OrderStatus.FAILED,
    },
}

_TERMINAL = {
    OrderStatus.FILLED,
    OrderStatus.CANCELLED,
    OrderStatus.REJECTED,
    OrderStatus.FAILED,
    OrderStatus.EXPIRED,
}


def assert_transition(current: str, new: str) -> None:
    cur = OrderStatus(current)
    nxt = OrderStatus(new)
    if cur in _TERMINAL:
        raise ServiceError(409, "INVALID_TRANSITION", f"Order is terminal at {current}")
    allowed = _ALLOWED.get(cur, set())
    if nxt not in allowed:
        raise ServiceError(
            409,
            "INVALID_TRANSITION",
            f"Cannot transition order from {current} to {new}",
        )


def map_broker_status(status: str) -> str:
    normalized = status.upper().replace("-", "_")
    mapping = {
        "SUBMITTED": OrderStatus.SUBMITTED.value,
        "PENDING": OrderStatus.ACKNOWLEDGED.value,
        "TRANSIT": OrderStatus.SUBMITTED.value,
        "ACKNOWLEDGED": OrderStatus.ACKNOWLEDGED.value,
        "PARTIALLY_FILLED": OrderStatus.PARTIALLY_FILLED.value,
        "FILLED": OrderStatus.FILLED.value,
        "TRADED": OrderStatus.FILLED.value,
        "CANCELLED": OrderStatus.CANCELLED.value,
        "REJECTED": OrderStatus.REJECTED.value,
        "FAILED": OrderStatus.FAILED.value,
        "EXPIRED": OrderStatus.EXPIRED.value,
    }
    return mapping.get(normalized, OrderStatus.ACKNOWLEDGED.value)

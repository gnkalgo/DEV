"""Constrained string values stored as VARCHAR + CHECK (easier to migrate than native PG enums)."""

from enum import StrEnum


class BrokerCode(StrEnum):
    MOCK = "MOCK"
    DHAN = "DHAN"
    ZERODHA = "ZERODHA"
    ANGEL_ONE = "ANGEL_ONE"
    GROWW = "GROWW"
    ALICE_BLUE = "ALICE_BLUE"


class BrokerConnectionStatus(StrEnum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    ERROR = "ERROR"


class OrderSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(StrEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    SL = "SL"
    SL_M = "SL-M"


class OrderStatus(StrEnum):
    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    APPROVED = "APPROVED"
    SUBMITTED = "SUBMITTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


def sql_in_list(values: type[StrEnum]) -> str:
    quoted = ", ".join(f"'{item.value}'" for item in values)
    return f"({quoted})"

"""Dhan exchange segment mapping for instruments."""

SEGMENT_ENUM_TO_NAME: dict[int, str] = {
    0: "IDX_I",
    1: "NSE_EQ",
    2: "NSE_FNO",
    3: "NSE_CURRENCY",
    4: "BSE_EQ",
    5: "MCX_COMM",
    7: "BSE_CURRENCY",
    8: "BSE_FNO",
}

NAME_TO_SEGMENT_ENUM: dict[str, int] = {v: k for k, v in SEGMENT_ENUM_TO_NAME.items()}


def dhan_exchange_segment(exchange: str, segment: str) -> str:
    exchange = exchange.upper()
    segment = segment.upper()
    if segment == "INDEX":
        return "IDX_I"
    if exchange == "BSE":
        if segment == "EQUITY":
            return "BSE_EQ"
        return "IDX_I"
    if segment in ("FNO", "FUTURES", "OPTIONS"):
        return "NSE_FNO"
    return "NSE_EQ"


def feed_key(exchange_segment: str, security_id: str) -> str:
    return f"{exchange_segment}:{security_id}"

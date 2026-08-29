"""In-memory LTP / prev-close cache updated from Dhan live feed."""

from datetime import datetime, timezone

from app.services.instrument_segments import feed_key

_store: dict[str, dict] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def update_ltp(
    exchange_segment: str,
    security_id: str,
    ltp: float,
    ltt: int | None = None,
    volume: int | None = None,
    symbol: str | None = None,
) -> None:
    key = feed_key(exchange_segment, security_id)
    row = _store.get(key, {})
    prev_close = row.get("prev_close")
    change = round(ltp - prev_close, 2) if prev_close else row.get("change", 0.0)
    change_pct = round((change / prev_close) * 100, 2) if prev_close else row.get("change_pct", 0.0)
    _store[key] = {
        **row,
        "exchange_segment": exchange_segment,
        "security_id": security_id,
        "symbol": symbol or row.get("symbol"),
        "ltp": ltp,
        "ltt": ltt,
        "volume": volume if volume is not None else row.get("volume"),
        "change": change,
        "change_pct": change_pct,
        "updated_at": _now_iso(),
        "source": "dhan_live",
    }


def update_prev_close(exchange_segment: str, security_id: str, prev_close: float) -> None:
    key = feed_key(exchange_segment, security_id)
    row = _store.get(key, {})
    ltp = row.get("ltp", prev_close)
    change = round(ltp - prev_close, 2)
    change_pct = round((change / prev_close) * 100, 2) if prev_close else 0.0
    _store[key] = {
        **row,
        "exchange_segment": exchange_segment,
        "security_id": security_id,
        "prev_close": prev_close,
        "change": change,
        "change_pct": change_pct,
        "updated_at": _now_iso(),
    }


def bind_symbol(exchange_segment: str, security_id: str, symbol: str) -> None:
    key = feed_key(exchange_segment, security_id)
    row = _store.get(key, {})
    _store[key] = {**row, "symbol": symbol}


def get_by_symbol(symbol: str) -> dict | None:
    sym = symbol.upper()
    for row in _store.values():
        if row.get("symbol") == sym:
            return row
    return None


def get_by_feed_key(exchange_segment: str, security_id: str) -> dict | None:
    return _store.get(feed_key(exchange_segment, security_id))


def all_snapshots() -> list[dict]:
    return list(_store.values())

"""Map Dhan compact CSV rows to normalized instrument fields."""

from datetime import date, datetime

from app.services.instrument_segments import dhan_exchange_segment

# NSE/BSE focus for Phase 2
_ALLOWED_EXCHANGES = {"NSE", "BSE"}

# SEM_INSTRUMENT_NAME values we ingest
_ALLOWED_INSTRUMENT_NAMES = {
    "EQUITY",
    "INDEX",
    "FUTIDX",
    "OPTIDX",
    "FUTSTK",
    "OPTSTK",
}

_INDEX_SYMBOL_ALIASES = {
    "NIFTY": "NIFTY50",
    "NIFTY BANK": "BANKNIFTY",
    "BANK NIFTY": "BANKNIFTY",
    "NIFTY FIN SERVICE": "FINNIFTY",
    "NIFTY FINANCIAL SERVICES": "FINNIFTY",
}


def _parse_date(raw: str) -> date | None:
    if not raw or raw.startswith("0001"):
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _parse_float(raw: str) -> float | None:
    if not raw or raw in ("-0.01000", "XX", "NA"):
        return None
    try:
        val = float(raw)
        return val if val > 0 else None
    except ValueError:
        return None


def _segment_label(sem_segment: str, instrument_name: str) -> str:
    if instrument_name == "INDEX" or sem_segment == "I":
        return "INDEX"
    if instrument_name in ("FUTIDX", "OPTIDX", "FUTSTK", "OPTSTK"):
        return "FNO"
    return "EQUITY"


def _map_exchange_segment(exch_id: str, sem_segment: str, instrument_name: str) -> str:
    exch = exch_id.upper()
    if instrument_name == "INDEX" or sem_segment == "I":
        return "IDX_I"
    if sem_segment == "D" or instrument_name in ("FUTIDX", "OPTIDX", "FUTSTK", "OPTSTK"):
        return "NSE_FNO" if exch == "NSE" else "BSE_FNO"
    return dhan_exchange_segment(exch, _segment_label(sem_segment, instrument_name))


def _normalize_symbol(trading_symbol: str, instrument_name: str, custom_symbol: str) -> str:
    sym = (trading_symbol or custom_symbol or "").strip().upper()
    if instrument_name == "INDEX":
        alias = _INDEX_SYMBOL_ALIASES.get(custom_symbol.strip().upper())
        if alias:
            return alias
        if sym == "NIFTY":
            return "NIFTY50"
    return sym.replace(" ", "")


def _underlying_symbol(trading_symbol: str, instrument_name: str, custom_symbol: str) -> str | None:
    if instrument_name not in ("FUTIDX", "OPTIDX", "FUTSTK", "OPTSTK"):
        return None
    base = (trading_symbol or "").split("-")[0].upper()
    if base:
        return base
    return custom_symbol.split()[0].upper() if custom_symbol else None


def parse_csv_row(row: dict[str, str]) -> dict | None:
    exch = (row.get("SEM_EXM_EXCH_ID") or "").strip().upper()
    if exch not in _ALLOWED_EXCHANGES:
        return None

    sem_segment = (row.get("SEM_SEGMENT") or "").strip().upper()
    instrument_name = (row.get("SEM_INSTRUMENT_NAME") or "").strip().upper()
    if instrument_name not in _ALLOWED_INSTRUMENT_NAMES:
        return None

    security_id = (row.get("SEM_SMST_SECURITY_ID") or "").strip()
    if not security_id:
        return None

    trading_symbol = (row.get("SEM_TRADING_SYMBOL") or "").strip()
    custom_symbol = (row.get("SEM_CUSTOM_SYMBOL") or row.get("SM_SYMBOL_NAME") or trading_symbol).strip()
    symbol = _normalize_symbol(trading_symbol, instrument_name, custom_symbol)
    if not symbol:
        return None

    exchange_segment = _map_exchange_segment(exch, sem_segment, instrument_name)
    segment = _segment_label(sem_segment, instrument_name)
    display_name = custom_symbol or trading_symbol or symbol

    expiry = _parse_date(row.get("SEM_EXPIRY_DATE") or "")
    strike = _parse_float(row.get("SEM_STRIKE_PRICE") or "")
    option_type = (row.get("SEM_OPTION_TYPE") or "").strip().upper()
    if option_type in ("XX", "NA", ""):
        option_type = None

    lot_raw = row.get("SEM_LOT_UNITS") or ""
    try:
        lot_size = int(float(lot_raw)) if lot_raw else None
    except ValueError:
        lot_size = None

    tick_size = _parse_float(row.get("SEM_TICK_SIZE") or "")
    underlying = _underlying_symbol(trading_symbol, instrument_name, custom_symbol)

    exch_type = (row.get("SEM_EXCH_INSTRUMENT_TYPE") or instrument_name).strip().upper()
    search_parts = [symbol, display_name, trading_symbol, underlying or "", exch, segment]
    search_text = " ".join(p for p in search_parts if p).upper()

    return {
        "symbol": symbol,
        "display_name": display_name[:256],
        "exchange": exch,
        "segment": segment,
        "instrument_type": exch_type or instrument_name,
        "security_id": security_id,
        "instrument_token": security_id,
        "exchange_segment": exchange_segment,
        "isin": None,
        "expiry": expiry,
        "strike": strike,
        "option_type": option_type,
        "underlying_symbol": underlying,
        "lot_size": lot_size,
        "tick_size": tick_size,
        "trading_symbol": trading_symbol[:64] if trading_symbol else None,
        "is_active": True,
        "search_text": search_text,
    }

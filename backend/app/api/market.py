import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.brokers.factory import get_broker_adapter
from app.brokers.dhan import DhanAdapter
from app.core.deps import get_current_user, user_from_access_token
from app.core.security import decrypt_data
from app.database import AsyncSessionLocal, get_db
from app.models import User
from app.services.candle_service import candle_service
from app.services.instrument_service import instrument_service
from app.services.market_service import get_indices, market_session
from app.services.market_ws_manager import subscribe_ws, unsubscribe_all, unsubscribe_ws
from app.services.portfolio_service import portfolio_service

router = APIRouter(prefix="/market", tags=["Market"])


async def _dhan_credentials(db: AsyncSession, user: User) -> dict | None:
    conn = await portfolio_service._active_connection(db, user, "dhan")
    if not conn:
        return None
    try:
        creds = json.loads(decrypt_data(conn.encrypted_credentials))
        if conn.client_id:
            creds.setdefault("client_id", conn.client_id)
        return creds
    except Exception:
        return None


@router.get("/indices")
async def market_indices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    snapshot = get_indices()
    credentials = await _dhan_credentials(db, current_user)
    if not credentials:
        return snapshot

    # Dhan index security IDs from its instrument master. Fetch in one request
    # to avoid rate-limit pressure from per-index polling.
    security_ids = {
        "NIFTY50": "13",
        "BANKNIFTY": "25",
        "NIFTYFINSERVICE": "27",
        "NIFTYNEXT50": "38",
        "NIFTYMIDCAP100": "442",
        "INDIAVIX": "21",
    }
    try:
        adapter = DhanAdapter(
            access_token=credentials.get("access_token") or credentials.get("api_key") or "",
            client_id=credentials.get("client_id"),
        )
        payload = await adapter.get_market_ohlc({"IDX_I": list(security_ids.values())})
        quotes = payload.get("data", {}).get("IDX_I", {})
        live_count = 0
        for item in snapshot["indices"]:
            quote = quotes.get(security_ids.get(item["symbol"], ""))
            if not quote:
                continue
            ltp = float(quote.get("last_price", 0) or 0)
            previous = float((quote.get("ohlc") or {}).get("close", 0) or 0)
            if not ltp:
                continue
            change = ltp - previous if previous else 0.0
            item.update(
                ltp=round(ltp, 2),
                change=round(change, 2),
                change_pct=round(change / previous * 100, 2) if previous else 0.0,
                is_live=True,
            )
            live_count += 1
        if live_count:
            snapshot["source"] = "dhan_live" if live_count == len(snapshot["indices"]) else "dhan_live_partial"
            snapshot["updated_at"] = datetime.now(timezone.utc).isoformat()
    except Exception:
        # Keep the last/reference snapshot available, but never mislabel it live.
        pass
    return snapshot


@router.get("/status")
async def market_status():
    return market_session()


@router.get("/instruments/search")
async def search_instruments(
    q: str = Query(default="", max_length=64),
    limit: int = Query(default=20, le=50),
    exchange: str | None = Query(default=None, max_length=8),
    segment: str | None = Query(default=None, max_length=16),
    db: AsyncSession = Depends(get_db),
):
    items = await instrument_service.search(db, q, limit=limit, exchange=exchange, segment=segment)
    return {"items": items, "total": len(items), "source": "db"}


@router.get("/instruments/{symbol}")
async def get_instrument(
    symbol: str,
    exchange: str = Query(default="NSE"),
    db: AsyncSession = Depends(get_db),
):
    inst = await instrument_service.get(db, symbol, exchange)
    if not inst:
        raise HTTPException(status_code=404, detail="Instrument not found")
    return inst


@router.get("/candles")
async def market_candles(
    symbol: str = Query(..., min_length=1, max_length=64),
    exchange: str = Query(default="NSE"),
    interval: str = Query(default="5m"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    adapter = None
    conn = await portfolio_service._active_connection(db, current_user, "dhan")
    if conn:
        try:
            adapter = get_broker_adapter(conn)
        except Exception:
            adapter = None
    return await candle_service.get_candles(db, symbol, exchange, interval, adapter=adapter)


@router.get("/quote")
async def market_quote(
    symbol: str = Query(..., min_length=1),
    exchange: str = Query(default="NSE"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    inst = await instrument_service.get(db, symbol, exchange)
    if not inst:
        inst = instrument_service.curated_fallback(symbol)
    if not inst:
        raise HTTPException(status_code=404, detail="Instrument not found")

    ltp = None
    change = 0.0
    change_pct = 0.0
    source = "cache"

    from app.services.market_quote_cache import get_by_symbol

    cached = get_by_symbol(inst["symbol"])
    if cached and cached.get("ltp"):
        ltp = float(cached["ltp"])
        change = float(cached.get("change", 0))
        change_pct = float(cached.get("change_pct", 0))
        source = cached.get("source", "dhan_live")

    conn = await portfolio_service._active_connection(db, current_user, "dhan")
    if conn and ltp is None:
        try:
            adapter = get_broker_adapter(conn)
            data = await adapter.get_market_quote_for_instrument(
                inst["security_id"],
                inst.get("exchange", exchange),
                inst.get("segment", "EQUITY"),
            )
            if data:
                ltp = float(data.get("last_price", 0) or 0)
                ohlc = data.get("ohlc") or {}
                prev = float(ohlc.get("close", 0) or 0)
                if prev and ltp:
                    change = round(ltp - prev, 2)
                    change_pct = round((change / prev) * 100, 2)
                source = "dhan"
        except Exception:
            pass

    if ltp is None:
        from app.services.candle_service import BASE_PRICES

        ltp = BASE_PRICES.get(inst["symbol"], 1000.0)
        source = "fallback"

    return {
        "symbol": inst["symbol"],
        "display_name": inst["display_name"],
        "exchange": inst["exchange"],
        "ltp": ltp,
        "change": change,
        "change_pct": change_pct,
        "security_id": inst["security_id"],
        "source": source,
    }


@router.websocket("/ws")
async def market_websocket(ws: WebSocket):
    await ws.accept()
    try:
        first = await asyncio.wait_for(ws.receive_text(), timeout=15)
        auth = json.loads(first)
    except Exception:
        await ws.close(code=4401)
        return
    token = (auth.get("token") if isinstance(auth, dict) else None) or ws.cookies.get("gnk_access")
    if auth.get("action") != "auth" or not token:
        await ws.close(code=4401)
        return

    dhan_creds: dict | None = None
    user_id = ""
    async with AsyncSessionLocal() as db:
        try:
            user = await user_from_access_token(db, token)
            user_id = str(user.id)
            dhan_creds = await _dhan_credentials(db, user)
            await db.commit()
        except Exception:
            await ws.close(code=4401)
            return

    try:
        while True:
            raw = await ws.receive_text()
            data = json.loads(raw)
            action = data.get("action")
            symbol = data.get("symbol", "").upper()
            exchange = data.get("exchange", "NSE").upper()
            if action == "subscribe" and symbol:
                await subscribe_ws(ws, user_id, symbol, exchange, dhan_creds)
            elif action == "unsubscribe" and symbol:
                await unsubscribe_ws(ws, user_id, symbol, exchange)
                await ws.send_text(json.dumps({"type": "unsubscribed", "symbol": symbol}))
    except WebSocketDisconnect:
        await unsubscribe_all(ws, user_id)
    except Exception:
        await unsubscribe_all(ws, user_id)
        await ws.close()

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.brokers.factory import get_broker_adapter
from app.core.deps import get_current_user
from app.core.security import decrypt_data, decode_token
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
async def market_indices():
    return get_indices()


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
    token = ws.query_params.get("token")
    if not token:
        await ws.close(code=4401)
        return
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        await ws.close(code=4401)
        return

    user_id = str(payload.get("sub", ""))
    if not user_id:
        await ws.close(code=4401)
        return

    await ws.accept()
    dhan_creds: dict | None = None
    async with AsyncSessionLocal() as db:
        try:
            uid = uuid.UUID(user_id)
            result = await db.execute(select(User).where(User.id == uid))
            user = result.scalar_one_or_none()
            if user:
                dhan_creds = await _dhan_credentials(db, user)
        except Exception:
            dhan_creds = None

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

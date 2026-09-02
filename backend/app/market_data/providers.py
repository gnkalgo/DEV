from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from app.config import settings


def _yahoo_symbol(symbol: str, exchange: str = "NSE") -> str:
    aliases = {
        "NIFTY50": "^NSEI",
        "NIFTY": "^NSEI",
        "BANKNIFTY": "^NSEBANK",
        "SENSEX": "^BSESN",
        "INDIAVIX": "^INDIAVIX",
    }
    key = symbol.upper()
    if key in aliases:
        return aliases[key]
    if key.startswith("^") or "." in key:
        return key
    return f"{key}.BO" if exchange.upper() == "BSE" else f"{key}.NS"


class YahooFinanceProvider:
    """Best-effort Yahoo Finance reference-data fallback (not an execution feed)."""

    async def quote(self, symbol: str, exchange: str = "NSE") -> dict[str, Any] | None:
        ticker = _yahoo_symbol(symbol, exchange)
        url = f"{settings.yahoo_finance_base_url}/v8/finance/chart/{ticker}"
        async with httpx.AsyncClient(timeout=15, headers={"User-Agent": "GnKAlgo/1.0"}) as client:
            response = await client.get(url, params={"interval": "1m", "range": "1d"})
        response.raise_for_status()
        result = (response.json().get("chart", {}).get("result") or [None])[0]
        if not result:
            return None
        meta = result.get("meta", {})
        price = meta.get("regularMarketPrice")
        previous = meta.get("chartPreviousClose") or meta.get("previousClose")
        if price is None:
            return None
        change = float(price) - float(previous) if previous else 0.0
        return {
            "ltp": float(price),
            "change": change,
            "change_pct": change / float(previous) * 100 if previous else 0.0,
            "source": "yahoo_reference",
        }


class RapidApiDataProvider:
    """Configurable RapidAPI quote fallback; host and URL depend on the subscription."""

    @property
    def configured(self) -> bool:
        return bool(settings.rapidapi_key and settings.rapidapi_host and settings.rapidapi_quotes_url)

    async def quote(self, symbol: str, exchange: str = "NSE") -> dict[str, Any] | None:
        if not self.configured:
            return None
        ticker = _yahoo_symbol(symbol, exchange)
        headers = {"X-RapidAPI-Key": settings.rapidapi_key, "X-RapidAPI-Host": settings.rapidapi_host}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                settings.rapidapi_quotes_url,
                headers=headers,
                params={"symbols": ticker, "region": "IN"},
            )
        response.raise_for_status()
        payload = response.json()
        rows = payload.get("quoteResponse", {}).get("result", [])
        row = rows[0] if rows else None
        if not row:
            return None
        return {
            "ltp": float(row.get("regularMarketPrice", 0)),
            "change": float(row.get("regularMarketChange", 0)),
            "change_pct": float(row.get("regularMarketChangePercent", 0)),
            "source": "rapidapi_reference",
        }


class FyersDataProvider:
    """FYERS API V3 quote client used only as a live market-data source."""

    def __init__(self, access_token: str, client_id: str):
        self.access_token = access_token
        self.client_id = client_id

    @property
    def authorization(self) -> str:
        token = self.access_token
        return token if ":" in token else f"{self.client_id}:{token}"

    async def quote(self, symbol: str, exchange: str = "NSE") -> dict[str, Any] | None:
        aliases = {
            "NIFTY50": "NSE:NIFTY50-INDEX", "NIFTY": "NSE:NIFTY50-INDEX",
            "BANKNIFTY": "NSE:NIFTYBANK-INDEX", "INDIAVIX": "NSE:INDIAVIX-INDEX",
            "SENSEX": "BSE:SENSEX-INDEX",
        }
        fyers_symbol = aliases.get(symbol.upper(), symbol if ":" in symbol else f"{exchange.upper()}:{symbol.upper()}-EQ")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"{settings.fyers_api_base_url}/data/quotes",
                headers={"Authorization": self.authorization},
                params={"symbols": fyers_symbol},
            )
        response.raise_for_status()
        payload = response.json()
        if payload.get("s") == "error":
            raise RuntimeError(payload.get("message") or "FYERS rejected the request")
        rows = payload.get("d") or []
        values = (rows[0].get("v") if rows else None) or {}
        ltp = values.get("lp")
        if ltp is None:
            return None
        return {
            "ltp": float(ltp),
            "change": float(values.get("ch", 0)),
            "change_pct": float(values.get("chp", 0)),
            "timestamp": int(values.get("tt") or datetime.now().timestamp()),
            "source": "fyers_live",
        }

    async def authenticate(self, credentials: dict | None = None) -> bool:
        # A liquid index quote validates both token format and market-data permission.
        return (await self.quote("NSE:NIFTY50-INDEX")) is not None

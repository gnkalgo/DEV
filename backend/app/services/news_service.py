from datetime import datetime, timedelta, timezone

import httpx

from app.config import settings
from app.services.redis_cache import cache_get, cache_set

_MOCK_NEWS = [
    {
        "id": "mock-1",
        "headline": "Nifty trades higher as banking stocks gain momentum",
        "summary": "Indian benchmarks rose in early trade led by financials.",
        "source": "Market News",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "url": "https://www.gnkalgo.com",
        "category": "market",
        "symbol": None,
        "thumbnail": None,
    },
    {
        "id": "mock-2",
        "headline": "RBI maintains stance on liquidity; focus on inflation",
        "summary": "Policy commentary shapes rate expectations.",
        "source": "Economy",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "url": "https://www.gnkalgo.com",
        "category": "economy",
        "symbol": None,
        "thumbnail": None,
    },
    {
        "id": "mock-3",
        "headline": "Reliance Industries expands digital services footprint",
        "summary": "Conglomerate updates on Jio and retail segments.",
        "source": "Stocks",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "url": "https://www.gnkalgo.com",
        "category": "stocks",
        "symbol": "RELIANCE",
        "thumbnail": None,
    },
    {
        "id": "mock-4",
        "headline": "FII activity remains mixed amid global cues",
        "summary": "Overseas investors watch US macro data.",
        "source": "Market News",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "url": "https://www.gnkalgo.com",
        "category": "market",
        "symbol": None,
        "thumbnail": None,
    },
    {
        "id": "mock-5",
        "headline": "TCS reports steady enterprise demand",
        "summary": "IT sector outlook in focus for investors.",
        "source": "Company",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "url": "https://www.gnkalgo.com",
        "category": "company",
        "symbol": "TCS",
        "thumbnail": None,
    },
]

_SYMBOL_KEYWORDS = {
    "RELIANCE": ["reliance", "jio", "oil", "energy"],
    "TCS": ["tcs", "tata consultancy"],
    "HDFCBANK": ["hdfc bank", "hdfcbank"],
    "INFY": ["infosys", "infy"],
    "NIFTY": ["nifty", "sensex", "indian market", "rbi", "fii", "dii"],
}


def _filter_by_symbol(items: list[dict], symbol: str | None) -> list[dict]:
    if not symbol:
        return items
    sym = symbol.upper()
    keywords = _SYMBOL_KEYWORDS.get(sym, [sym.lower()])
    filtered = [
        n for n in items
        if n.get("symbol") == sym
        or any(k in n.get("headline", "").lower() for k in keywords)
        or any(k in (n.get("summary") or "").lower() for k in keywords)
    ]
    if filtered:
        return filtered + [n for n in items if n not in filtered]
    return items


async def _fetch_finnhub(symbol: str | None, limit: int) -> list[dict] | None:
    if not settings.finnhub_api_key:
        return None
    cache_key = f"news:finnhub:{symbol or 'general'}:{limit}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    items: list[dict] = []
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            if symbol:
                today = datetime.now(timezone.utc).date()
                start = (today - timedelta(days=7)).isoformat()
                url = (
                    f"{settings.finnhub_base_url}/company-news"
                    f"?symbol={symbol.upper()}&from={start}&to={today.isoformat()}"
                    f"&token={settings.finnhub_api_key}"
                )
            else:
                url = (
                    f"{settings.finnhub_base_url}/news"
                    f"?category=general&token={settings.finnhub_api_key}"
                )
            res = await client.get(url)
            if res.status_code != 200:
                return None
            raw = res.json()
            if not isinstance(raw, list):
                return None
            for row in raw[:limit]:
                items.append({
                    "id": str(row.get("id", row.get("datetime", ""))),
                    "headline": row.get("headline") or row.get("title") or "News",
                    "summary": row.get("summary") or "",
                    "source": row.get("source") or "Finnhub",
                    "published_at": datetime.fromtimestamp(
                        int(row.get("datetime", 0)), tz=timezone.utc
                    ).isoformat()
                    if row.get("datetime")
                    else datetime.now(timezone.utc).isoformat(),
                    "url": row.get("url") or "https://www.gnkalgo.com",
                    "category": row.get("category") or "market",
                    "symbol": symbol,
                    "thumbnail": row.get("image"),
                    "is_mock": False,
                })
    except Exception:
        return None

    if items:
        await cache_set(cache_key, items, settings.cache_news_ttl_seconds)
    return items


class NewsService:
    async def latest(self, limit: int = 10, symbol: str | None = None) -> dict:
        use_mock = settings.app_env != "production" or settings.debug
        source_label = "mock_dev"
        items: list[dict] = []

        if settings.news_provider == "finnhub" and settings.finnhub_api_key:
            fetched = await _fetch_finnhub(symbol, limit)
            if fetched:
                items = fetched
                source_label = "finnhub"
                use_mock = False

        if not items:
            items = list(_MOCK_NEWS)
            source_label = "mock_dev"
            use_mock = True

        items = _filter_by_symbol(items, symbol)
        items = items[:limit]
        for item in items:
            item["is_mock"] = use_mock

        return {
            "items": items,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "source": source_label,
            "symbol": symbol,
        }


news_service = NewsService()

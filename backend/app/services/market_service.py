"""Indian market indices and session status. Mock ticks only in development."""

import random
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

from app.config import settings
from app.services.market_quote_cache import get_by_symbol

IST = ZoneInfo("Asia/Kolkata")

# Base snapshot — not live; dev mock drifts slightly. Production should use a real feed.
_INDEX_BASE = [
    ("NIFTY 50", "NIFTY50", 24175.65, 84.80, 0.35),
    ("BANKNIFTY", "BANKNIFTY", 57496.30, -13.65, -0.02),
    ("NIFTY FIN SERVICE", "NIFTYFINSERVICE", 27420.10, 112.45, 0.41),
    ("NIFTY NEXT 50", "NIFTYNEXT50", 74159.15, -188.30, -0.25),
    ("NIFTY MIDCAP 50", "NIFTYMIDCAP50", 16245.80, 45.20, 0.28),
    ("NIFTY MIDCAP 100", "NIFTYMIDCAP100", 58420.55, -62.10, -0.11),
    ("NIFTY SMALLCAP 100", "NIFTYSMALLCAP100", 19840.25, 78.90, 0.40),
    ("NIFTY IT", "NIFTYIT", 41280.00, 320.15, 0.78),
    ("NIFTY AUTO", "NIFTYAUTO", 23890.40, -95.60, -0.40),
    ("NIFTY FMCG", "NIFTYFMCG", 58210.30, 42.10, 0.07),
    ("NIFTY PHARMA", "NIFTYPHARMA", 22150.75, 18.55, 0.08),
    ("NIFTY METAL", "NIFTYMETAL", 9120.45, -124.30, -1.34),
    ("NIFTY REALTY", "NIFTYREALTY", 10245.60, 56.80, 0.56),
    ("NIFTY ENERGY", "NIFTYENERGY", 35680.90, -28.40, -0.08),
    ("INDIA VIX", "INDIAVIX", 10.68, -0.39, -3.52),
    ("SENSEX", "SENSEX", 79820.45, 285.30, 0.36),
    ("BSE BANKEX", "BSEBANKEX", 61240.15, -45.20, -0.07),
]


def market_session() -> dict:
    now = datetime.now(IST)
    weekday = now.weekday()
    t = now.time()
    pre_open = time(9, 0)
    open_start = time(9, 15)
    close = time(15, 30)

    if weekday >= 5:
        return {"status": "closed", "label": "Market Closed", "session": "weekend"}

    if t < pre_open:
        return {"status": "closed", "label": "Market Closed", "session": "pre_market"}
    if pre_open <= t < open_start:
        return {"status": "pre_open", "label": "Pre-Open", "session": "pre_open"}
    if open_start <= t <= close:
        return {"status": "open", "label": "Market Open", "session": "regular"}
    return {"status": "closed", "label": "Market Closed", "session": "post_market"}


def get_indices() -> dict:
    use_mock_drift = settings.app_env != "production" or settings.debug
    items = []
    live_count = 0
    for name, key, base_ltp, base_chg, base_chg_pct in _INDEX_BASE:
        cached = get_by_symbol(key)
        if cached and cached.get("ltp"):
            ltp = float(cached["ltp"])
            chg = float(cached.get("change", 0))
            chg_pct = float(cached.get("change_pct", 0))
            live_count += 1
        else:
            ltp, chg, chg_pct = base_ltp, base_chg, base_chg_pct
            if use_mock_drift:
                drift = random.uniform(-0.15, 0.15)
                ltp = round(ltp * (1 + drift / 100), 2)
                chg = round(chg + drift, 2)
                chg_pct = round(chg_pct + drift / 10, 2)
        items.append(
            {
                "name": name,
                "symbol": key,
                "ltp": ltp,
                "change": chg,
                "change_pct": chg_pct,
            }
        )

    if live_count > 0:
        source = "dhan_live"
    elif use_mock_drift:
        source = "mock_dev"
    else:
        source = "static"

    return {
        "indices": items,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "disclaimer": "Not investment advice.",
    }

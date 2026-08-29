import json

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Signal, User


class SignalService:
    async def fetch_and_store(self, db: AsyncSession, user: User, symbols: str = "RELIANCE,TCS,INFY,HDFCBANK") -> list[Signal]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                response = await client.get(
                    f"{settings.ml_service_url}/ml/v1/signals/batch",
                    params={"symbols": symbols},
                )
                response.raise_for_status()
                payload = response.json()
            except Exception:
                payload = {
                    "signals": [
                        {"symbol": "RELIANCE", "action": "HOLD", "confidence": 0.0, "price": 0, "features": {}},
                    ]
                }

        stored: list[Signal] = []
        for item in payload.get("signals", []):
            signal = Signal(
                user_id=user.id,
                symbol=item.get("symbol", ""),
                action=item.get("action", "HOLD"),
                confidence=float(item.get("confidence") or 0),
                price=item.get("price"),
                features_json=json.dumps(item.get("features") or {}),
            )
            db.add(signal)
            stored.append(signal)
        await db.flush()
        return stored


signal_service = SignalService()

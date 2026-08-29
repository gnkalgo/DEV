import csv
import io
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import func, select, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.data.instrument_master import INSTRUMENTS
from app.database import engine
from app.models.instrument import Instrument, InstrumentSyncRun, InstrumentSyncStatus
from app.services.instrument_csv_parser import parse_csv_row

logger = logging.getLogger(__name__)

BATCH_SIZE = 500


class InstrumentSyncService:
    async def count_instruments(self, db: AsyncSession) -> int:
        return await db.scalar(select(func.count()).select_from(Instrument)) or 0

    async def seed_from_curated(self, db: AsyncSession) -> int:
        from app.services.instrument_segments import dhan_exchange_segment

        rows = []
        for item in INSTRUMENTS:
            seg = dhan_exchange_segment(item["exchange"], item["segment"])
            symbol = item["symbol"]
            display = item["display_name"]
            search_text = f"{symbol} {display} {item['exchange']} {item['segment']}".upper()
            rows.append(
                {
                    "symbol": symbol,
                    "display_name": display,
                    "exchange": item["exchange"],
                    "segment": item["segment"],
                    "instrument_type": item["segment"],
                    "security_id": item["security_id"],
                    "instrument_token": item.get("instrument_token", item["security_id"]),
                    "exchange_segment": seg,
                    "isin": None,
                    "expiry": None,
                    "strike": None,
                    "option_type": None,
                    "underlying_symbol": None,
                    "lot_size": None,
                    "tick_size": None,
                    "trading_symbol": symbol,
                    "is_active": True,
                    "search_text": search_text,
                }
            )
        return await self._upsert_batch(db, rows)

    async def sync_from_url(self, db: AsyncSession, url: str | None = None) -> InstrumentSyncRun:
        source = url or settings.instrument_master_url
        run = InstrumentSyncRun(status=InstrumentSyncStatus.RUNNING.value, source_url=source)
        db.add(run)
        await db.commit()
        await db.refresh(run)

        try:
            text = await self._download_csv(source)
            upserted, deactivated = await self._ingest_csv(db, text)
            run.status = InstrumentSyncStatus.SUCCESS.value
            run.rows_upserted = upserted
            run.rows_deactivated = deactivated
        except Exception as exc:
            logger.exception("Instrument sync failed")
            run.status = InstrumentSyncStatus.FAILED.value
            run.error = str(exc)[:2000]
            # Ensure curated seed exists if DB still empty
            if await self.count_instruments(db) == 0:
                await self.seed_from_curated(db)

        run.finished_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(run)
        return run

    async def latest_run(self, db: AsyncSession) -> InstrumentSyncRun | None:
        result = await db.execute(
            select(InstrumentSyncRun).order_by(InstrumentSyncRun.started_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def _download_csv(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            response = await client.get(url)
            if response.status_code >= 400:
                raise RuntimeError(f"Instrument CSV download failed: {response.status_code}")
            return response.text

    async def _ingest_csv(self, db: AsyncSession, text: str) -> tuple[int, int]:
        reader = csv.DictReader(io.StringIO(text))
        batch: list[dict] = []
        seen_keys: set[str] = set()
        upserted = 0

        for row in reader:
            parsed = parse_csv_row(row)
            if not parsed:
                continue
            key = f"{parsed['exchange']}:{parsed['exchange_segment']}:{parsed['security_id']}"
            if key in seen_keys:
                continue
            seen_keys.add(key)
            batch.append(parsed)
            if len(batch) >= BATCH_SIZE:
                upserted += await self._upsert_batch(db, batch)
                batch = []

        if batch:
            upserted += await self._upsert_batch(db, batch)

        # Deactivate instruments not seen in this sync (only NSE/BSE universe)
        deactivated = 0
        if seen_keys:
            result = await db.execute(
                select(Instrument).where(
                    Instrument.exchange.in_(("NSE", "BSE")),
                    Instrument.is_active.is_(True),
                )
            )
            stale_ids = []
            for inst in result.scalars():
                key = f"{inst.exchange}:{inst.exchange_segment}:{inst.security_id}"
                if key not in seen_keys:
                    stale_ids.append(inst.id)
            if stale_ids:
                await db.execute(
                    update(Instrument).where(Instrument.id.in_(stale_ids)).values(is_active=False)
                )
                deactivated = len(stale_ids)
            await db.commit()

        return upserted, deactivated

    async def _upsert_batch(self, db: AsyncSession, rows: list[dict]) -> int:
        if not rows:
            return 0
        # Core insert() does not apply ORM Python defaults — ensure primary keys exist.
        import uuid as _uuid

        for row in rows:
            if not row.get("id"):
                row["id"] = _uuid.uuid4()

        dialect = engine.dialect.name
        if dialect == "postgresql":
            from sqlalchemy.dialects.postgresql import insert as pg_insert

            stmt = pg_insert(Instrument).values(rows)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_instrument_feed_key",
                set_={
                    "symbol": stmt.excluded.symbol,
                    "display_name": stmt.excluded.display_name,
                    "segment": stmt.excluded.segment,
                    "instrument_type": stmt.excluded.instrument_type,
                    "instrument_token": stmt.excluded.instrument_token,
                    "isin": stmt.excluded.isin,
                    "expiry": stmt.excluded.expiry,
                    "strike": stmt.excluded.strike,
                    "option_type": stmt.excluded.option_type,
                    "underlying_symbol": stmt.excluded.underlying_symbol,
                    "lot_size": stmt.excluded.lot_size,
                    "tick_size": stmt.excluded.tick_size,
                    "trading_symbol": stmt.excluded.trading_symbol,
                    "is_active": stmt.excluded.is_active,
                    "search_text": stmt.excluded.search_text,
                    "updated_at": datetime.now(timezone.utc),
                },
            )
            await db.execute(stmt)
        else:
            stmt = sqlite_insert(Instrument).values(rows)
            stmt = stmt.on_conflict_do_update(
                index_elements=["exchange", "exchange_segment", "security_id"],
                set_={
                    "symbol": stmt.excluded.symbol,
                    "display_name": stmt.excluded.display_name,
                    "segment": stmt.excluded.segment,
                    "instrument_type": stmt.excluded.instrument_type,
                    "instrument_token": stmt.excluded.instrument_token,
                    "isin": stmt.excluded.isin,
                    "expiry": stmt.excluded.expiry,
                    "strike": stmt.excluded.strike,
                    "option_type": stmt.excluded.option_type,
                    "underlying_symbol": stmt.excluded.underlying_symbol,
                    "lot_size": stmt.excluded.lot_size,
                    "tick_size": stmt.excluded.tick_size,
                    "trading_symbol": stmt.excluded.trading_symbol,
                    "is_active": stmt.excluded.is_active,
                    "search_text": stmt.excluded.search_text,
                },
            )
            await db.execute(stmt)
        await db.commit()
        return len(rows)


instrument_sync_service = InstrumentSyncService()

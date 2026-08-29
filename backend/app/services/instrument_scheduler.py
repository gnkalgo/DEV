import asyncio
import logging

from app.config import settings
from app.database import AsyncSessionLocal
from app.services.instrument_sync_service import instrument_sync_service

logger = logging.getLogger(__name__)


async def _run_sync():
    async with AsyncSessionLocal() as db:
        try:
            await instrument_sync_service.sync_from_url(db)
        except Exception as exc:
            logger.warning("Scheduled instrument sync failed: %s", exc)


async def _instrument_scheduler_loop():
    interval_sec = max(settings.instrument_sync_interval_hours, 1) * 3600
    while True:
        await asyncio.sleep(interval_sec)
        if settings.instrument_sync_enabled:
            await _run_sync()


def start_instrument_scheduler() -> asyncio.Task:
    return asyncio.create_task(_instrument_scheduler_loop())


async def bootstrap_instruments():
    async with AsyncSessionLocal() as db:
        count = await instrument_sync_service.count_instruments(db)
        if count == 0:
            logger.info("Seeding instruments from curated list")
            await instrument_sync_service.seed_from_curated(db)
    if settings.instrument_sync_enabled:
        asyncio.create_task(_run_sync())

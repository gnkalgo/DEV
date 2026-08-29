import asyncio
import logging

from app.config import settings
from app.database import AsyncSessionLocal
from app.services.billing_service import process_auto_renewals

logger = logging.getLogger(__name__)


async def billing_scheduler_loop() -> None:
    tick = max(300, settings.billing_scheduler_tick_seconds)
    logger.info("Billing auto-renew scheduler started (tick=%ss)", tick)
    while True:
        try:
            async with AsyncSessionLocal() as session:
                count = await process_auto_renewals(session)
                await session.commit()
                if count:
                    logger.info("Created %d auto-renewal payment(s)", count)
        except Exception:
            logger.exception("Billing scheduler tick failed")
        await asyncio.sleep(tick)


def start_billing_scheduler() -> asyncio.Task:
    return asyncio.create_task(billing_scheduler_loop())

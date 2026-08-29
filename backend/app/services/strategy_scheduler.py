import asyncio
import logging

from app.config import settings
from app.database import AsyncSessionLocal
from app.services.strategy_service import strategy_service

logger = logging.getLogger(__name__)


async def strategy_scheduler_loop() -> None:
    tick = max(15, settings.strategy_scheduler_tick_seconds)
    logger.info("Strategy scheduler started (tick=%ss)", tick)
    while True:
        try:
            async with AsyncSessionLocal() as session:
                ran = await strategy_service.run_due_scheduled(session)
                await session.commit()
                if ran:
                    logger.info("Scheduled %d strategy run(s)", ran)
        except Exception:
            logger.exception("Strategy scheduler tick failed")
        await asyncio.sleep(tick)


def start_strategy_scheduler() -> asyncio.Task:
    return asyncio.create_task(strategy_scheduler_loop())

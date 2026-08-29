from fastapi import APIRouter, Query

from app.services.news_service import news_service

router = APIRouter(prefix="/news", tags=["News"])


@router.get("/latest")
async def latest_news(
    limit: int = Query(default=10, ge=1, le=50),
    symbol: str | None = Query(default=None, max_length=32),
):
    return await news_service.latest(limit=limit, symbol=symbol)

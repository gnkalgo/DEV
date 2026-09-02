from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import MarketCandle


async def persist_candles(
    db: AsyncSession, provider: str, symbol: str, exchange: str, interval: str, candles: list[dict]
) -> int:
    if not candles:
        return 0
    times = [int(row["time"]) for row in candles]
    result = await db.execute(select(MarketCandle.timestamp).where(
        MarketCandle.provider == provider,
        MarketCandle.symbol == symbol,
        MarketCandle.exchange == exchange,
        MarketCandle.interval == interval,
        MarketCandle.timestamp.in_(times),
    ))
    existing = set(result.scalars().all())
    new_rows = [row for row in candles if int(row["time"]) not in existing]
    for row in new_rows:
        db.add(MarketCandle(
            provider=provider, symbol=symbol, exchange=exchange, interval=interval,
            timestamp=int(row["time"]), open=float(row["open"]), high=float(row["high"]),
            low=float(row["low"]), close=float(row["close"]), volume=row.get("volume"),
            open_interest=row.get("open_interest"),
        ))
    await db.flush()
    _write_parquet(provider, symbol, exchange, interval, candles)
    return len(new_rows)


def _write_parquet(provider: str, symbol: str, exchange: str, interval: str, candles: list[dict]) -> None:
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq

        root = Path(settings.market_data_lake_path) / provider / exchange / symbol
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{interval}.parquet"
        incoming = pa.Table.from_pylist(candles)
        if path.exists():
            incoming = pa.concat_tables([pq.read_table(path), incoming], promote_options="default")
            frame = incoming.to_pandas().drop_duplicates(subset=["time"], keep="last").sort_values("time")
            incoming = pa.Table.from_pandas(frame, preserve_index=False)
        pq.write_table(incoming, path, compression="zstd")
    except Exception:
        # PostgreSQL remains authoritative if optional file export is unavailable.
        return

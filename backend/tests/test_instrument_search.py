import asyncio
import pathlib

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.services.instrument_csv_parser import parse_csv_row
from app.services.instrument_service import instrument_service
from app.services.instrument_sync_service import instrument_sync_service


def test_parse_csv_equity_row():
    row = {
        "SEM_EXM_EXCH_ID": "NSE",
        "SEM_SEGMENT": "E",
        "SEM_SMST_SECURITY_ID": "2885",
        "SEM_INSTRUMENT_NAME": "EQUITY",
        "SEM_TRADING_SYMBOL": "RELIANCE",
        "SEM_CUSTOM_SYMBOL": "Reliance Industries",
        "SEM_EXPIRY_DATE": "",
        "SEM_STRIKE_PRICE": "",
        "SEM_OPTION_TYPE": "XX",
        "SEM_LOT_UNITS": "1.0",
        "SEM_TICK_SIZE": "10.0000",
        "SEM_EXCH_INSTRUMENT_TYPE": "ES",
        "SM_SYMBOL_NAME": "RELIANCE INDUSTRIES LTD",
    }
    parsed = parse_csv_row(row)
    assert parsed is not None
    assert parsed["symbol"] == "RELIANCE"
    assert parsed["exchange_segment"] == "NSE_EQ"
    assert parsed["security_id"] == "2885"


def test_parse_csv_index_nifty_alias():
    row = {
        "SEM_EXM_EXCH_ID": "NSE",
        "SEM_SEGMENT": "I",
        "SEM_SMST_SECURITY_ID": "13",
        "SEM_INSTRUMENT_NAME": "INDEX",
        "SEM_TRADING_SYMBOL": "NIFTY",
        "SEM_CUSTOM_SYMBOL": "Nifty 50",
        "SEM_EXPIRY_DATE": "0001-01-01",
        "SEM_STRIKE_PRICE": "",
        "SEM_OPTION_TYPE": "XX",
        "SEM_LOT_UNITS": "1.0",
        "SEM_TICK_SIZE": "0.0500",
        "SEM_EXCH_INSTRUMENT_TYPE": "INDEX",
        "SM_SYMBOL_NAME": "NIFTY",
    }
    parsed = parse_csv_row(row)
    assert parsed is not None
    assert parsed["symbol"] == "NIFTY50"
    assert parsed["exchange_segment"] == "IDX_I"


def test_seed_and_search():
    async def _run():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            await instrument_sync_service.seed_from_curated(session)
            items = await instrument_service.search(session, "RELIANCE", limit=5)
            assert any(i["symbol"] == "RELIANCE" for i in items)
        await engine.dispose()

    asyncio.run(_run())


FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "sample_instruments.csv"


def test_ingest_sample_csv():
    async def _run():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            with open(FIXTURE, encoding="utf-8") as f:
                text = f.read()
            upserted, _ = await instrument_sync_service._ingest_csv(session, text)
            assert upserted >= 3
            inst = await instrument_service.get(session, "RELIANCE", "NSE")
            assert inst is not None
            assert inst["security_id"] == "2885"
            nifty = await instrument_service.get(session, "NIFTY50", "NSE")
            assert nifty is not None
        await engine.dispose()

    asyncio.run(_run())

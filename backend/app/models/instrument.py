import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Index, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class InstrumentSyncStatus(str, enum.Enum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class Instrument(Base):
    __tablename__ = "instruments"
    __table_args__ = (
        UniqueConstraint("exchange", "exchange_segment", "security_id", name="uq_instrument_feed_key"),
        Index("ix_instruments_symbol", "symbol"),
        Index("ix_instruments_search_text", "search_text"),
        Index("ix_instruments_active_symbol", "is_active", "symbol"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(256), nullable=False)
    exchange: Mapped[str] = mapped_column(String(8), nullable=False)
    segment: Mapped[str] = mapped_column(String(16), nullable=False)
    instrument_type: Mapped[str] = mapped_column(String(16), nullable=False, default="EQUITY")
    security_id: Mapped[str] = mapped_column(String(32), nullable=False)
    instrument_token: Mapped[str] = mapped_column(String(32), nullable=False)
    exchange_segment: Mapped[str] = mapped_column(String(16), nullable=False)
    isin: Mapped[str | None] = mapped_column(String(16), nullable=True)
    expiry: Mapped[date | None] = mapped_column(Date, nullable=True)
    strike: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)
    option_type: Mapped[str | None] = mapped_column(String(4), nullable=True)
    underlying_symbol: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lot_size: Mapped[int | None] = mapped_column(nullable=True)
    tick_size: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    trading_symbol: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    search_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class InstrumentSyncRun(Base):
    __tablename__ = "instrument_sync_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=InstrumentSyncStatus.RUNNING.value)
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    rows_upserted: Mapped[int] = mapped_column(default=0)
    rows_deactivated: Mapped[int] = mapped_column(default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

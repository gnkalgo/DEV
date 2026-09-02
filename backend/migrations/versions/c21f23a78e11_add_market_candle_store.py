"""add persistent market candle store

Revision ID: c21f23a78e11
Revises: 91a5c3ef7b20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c21f23a78e11"
down_revision: Union[str, Sequence[str], None] = "91a5c3ef7b20"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "market_candles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("symbol", sa.String(64), nullable=False),
        sa.Column("exchange", sa.String(8), nullable=False),
        sa.Column("interval", sa.String(8), nullable=False),
        sa.Column("timestamp", sa.BigInteger(), nullable=False),
        sa.Column("open", sa.Float(), nullable=False),
        sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=True),
        sa.Column("open_interest", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "symbol", "exchange", "interval", "timestamp", name="uq_market_candle"),
    )
    op.create_index("ix_market_candles_lookup", "market_candles", ["symbol", "exchange", "interval", "timestamp"])


def downgrade() -> None:
    op.drop_index("ix_market_candles_lookup", table_name="market_candles")
    op.drop_table("market_candles")

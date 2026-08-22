"""Phase 2 future-ready Timescale hypertables (no writers until Phase 7+)."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_phase2_timescale"
down_revision: Union[str, Sequence[str], None] = "0002_phase2_oltp"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

HYPERTABLES = (
    "market_ticks",
    "market_ohlcv",
    "ml_features",
    "ml_predictions",
    "portfolio_snapshots",
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")

    op.create_table(
        "market_ticks",
        sa.Column("time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("symbol", sa.String(length=64), nullable=False),
        sa.Column("exchange", sa.String(length=16), nullable=False),
        sa.Column("ltp", sa.Numeric(18, 6), nullable=True),
        sa.Column("bid", sa.Numeric(18, 6), nullable=True),
        sa.Column("ask", sa.Numeric(18, 6), nullable=True),
        sa.Column("volume", sa.Numeric(20, 4), nullable=True),
        sa.PrimaryKeyConstraint("time", "symbol", "exchange", name="pk_market_ticks"),
    )
    op.create_index("ix_market_ticks_symbol_time", "market_ticks", ["symbol", "time"], unique=False)

    op.create_table(
        "market_ohlcv",
        sa.Column("time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("symbol", sa.String(length=64), nullable=False),
        sa.Column("exchange", sa.String(length=16), nullable=False),
        sa.Column("interval", sa.String(length=16), nullable=False),
        sa.Column("open", sa.Numeric(18, 6), nullable=True),
        sa.Column("high", sa.Numeric(18, 6), nullable=True),
        sa.Column("low", sa.Numeric(18, 6), nullable=True),
        sa.Column("close", sa.Numeric(18, 6), nullable=True),
        sa.Column("volume", sa.Numeric(20, 4), nullable=True),
        sa.PrimaryKeyConstraint("time", "symbol", "exchange", "interval", name="pk_market_ohlcv"),
    )
    op.create_index("ix_market_ohlcv_symbol_time", "market_ohlcv", ["symbol", "time"], unique=False)

    op.create_table(
        "ml_features",
        sa.Column("time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("symbol", sa.String(length=64), nullable=False),
        sa.Column("feature_set", sa.String(length=64), nullable=False),
        sa.Column(
            "features",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("time", "symbol", "feature_set", name="pk_ml_features"),
    )

    op.create_table(
        "ml_predictions",
        sa.Column("time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("symbol", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("prediction", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("confidence", sa.Numeric(8, 6), nullable=True),
        sa.PrimaryKeyConstraint("time", "symbol", "model_name", name="pk_ml_predictions"),
    )

    op.create_table(
        "portfolio_snapshots",
        sa.Column("time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("broker_account_id", sa.Uuid(), nullable=True),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("time", "user_id", name="pk_portfolio_snapshots"),
    )

    for table in HYPERTABLES:
        op.execute(sa.text(f"SELECT create_hypertable('{table}', 'time', if_not_exists => TRUE)"))


def downgrade() -> None:
    for table in reversed(HYPERTABLES):
        op.drop_table(table)

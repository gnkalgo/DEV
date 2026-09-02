"""add persistent kill switch

Revision ID: 91a5c3ef7b20
Revises: 3ddb4ef93c32
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "91a5c3ef7b20"
down_revision: Union[str, Sequence[str], None] = "3ddb4ef93c32"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trading_controls",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("kill_switch_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute("INSERT INTO trading_controls (id, kill_switch_active, reason) VALUES (1, true, 'Safe default after migration')")


def downgrade() -> None:
    op.drop_table("trading_controls")

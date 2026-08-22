"""Baseline revision: Alembic is wired; application tables arrive in Phase 2."""

from typing import Sequence, Union

revision: str = "0001_phase1_baseline"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

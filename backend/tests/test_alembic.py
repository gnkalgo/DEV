"""Alembic revision chain for Phase 2. Does not run against a live database."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_phase2_revision_chain() -> None:
    ini = Path(__file__).resolve().parents[1] / "alembic.ini"
    config = Config(str(ini))
    script = ScriptDirectory.from_config(config)
    revisions = {rev.revision: rev for rev in script.walk_revisions()}
    assert "0001_phase1_baseline" in revisions
    assert "0002_phase2_oltp" in revisions
    assert "0003_phase2_timescale" in revisions
    assert revisions["0002_phase2_oltp"].down_revision == "0001_phase1_baseline"
    assert revisions["0003_phase2_timescale"].down_revision == "0002_phase2_oltp"
    heads = script.get_heads()
    assert heads == ["0003_phase2_timescale"]

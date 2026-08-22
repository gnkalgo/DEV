"""Phase 2 schema contract tests. These tests never contact a broker or live database."""

from sqlalchemy import UniqueConstraint

from app.db.database import Base
from app.db.models import HYPERTABLES, OLTP_TABLES, AuditLog
from app.db.models.enums import BrokerCode, OrderStatus, OrderType


def _unique_column_sets(table_name: str) -> set[tuple[str, ...]]:
    table = Base.metadata.tables[table_name]
    return {tuple(col.name for col in cons.columns) for cons in table.constraints if isinstance(cons, UniqueConstraint)}


def _index_column_sets(table_name: str) -> set[tuple[str, ...]]:
    table = Base.metadata.tables[table_name]
    return {tuple(col.name for col in idx.columns) for idx in table.indexes}


def test_oltp_and_hypertable_names_match_architecture() -> None:
    assert OLTP_TABLES == (
        "users",
        "user_sessions",
        "broker_accounts",
        "broker_tokens",
        "orders",
        "order_events",
        "positions",
        "audit_logs",
    )
    assert HYPERTABLES == (
        "market_ticks",
        "market_ohlcv",
        "ml_features",
        "ml_predictions",
        "portfolio_snapshots",
    )
    for name in (*OLTP_TABLES, *HYPERTABLES):
        assert name in Base.metadata.tables


def test_users_never_store_plaintext_password_column() -> None:
    columns = set(Base.metadata.tables["users"].c.keys())
    assert "password_hash" in columns
    assert "password" not in columns


def test_broker_secrets_are_ciphertext_columns() -> None:
    broker_cols = set(Base.metadata.tables["broker_accounts"].c.keys())
    token_cols = set(Base.metadata.tables["broker_tokens"].c.keys())
    assert {"encrypted_api_key", "encrypted_api_secret", "encrypted_totp"} <= broker_cols
    assert "api_key" not in broker_cols
    assert "encrypted_access_token" in token_cols
    assert "access_token" not in token_cols


def test_required_unique_and_indexes() -> None:
    assert ("user_id", "expires_at") in _index_column_sets("user_sessions")
    assert ("user_id", "broker", "client_id") in _unique_column_sets("broker_accounts")
    assert ("user_id", "created_at") in _index_column_sets("orders")
    assert ("broker_account_id", "status") in _index_column_sets("orders")
    assert ("broker_account_id", "symbol", "exchange") in _unique_column_sets("positions")
    assert ("idempotency_key",) in _unique_column_sets("orders")


def test_audit_logs_metadata_column_is_not_mapper_collision() -> None:
    assert "metadata" in Base.metadata.tables["audit_logs"].c
    assert AuditLog.__table__.c["metadata"].name == "metadata"


def test_order_and_broker_enums_match_architecture() -> None:
    assert {item.value for item in BrokerCode} == {
        "MOCK",
        "DHAN",
        "ZERODHA",
        "ANGEL_ONE",
        "GROWW",
        "ALICE_BLUE",
    }
    assert OrderType.SL_M.value == "SL-M"
    assert {"CREATED", "EXPIRED", "FILLED", "CANCELLED"} <= {item.value for item in OrderStatus}


def test_hypertables_partition_on_time() -> None:
    for name in HYPERTABLES:
        pk_cols = [col.name for col in Base.metadata.tables[name].primary_key.columns]
        assert pk_cols[0] == "time"

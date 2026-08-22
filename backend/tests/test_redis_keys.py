"""Redis key helper tests. Values must stay non-secret."""

from uuid import uuid4

import pytest

from app.utils.redis_keys import (
    assert_non_secret_mapping,
    broker_session_key,
    broker_status_key,
    latest_ltp_key,
    order_idempotency_key,
    rate_limit_key,
    signal_lock_key,
    ws_presence_key,
)


def test_architecture_key_shapes() -> None:
    account_id = uuid4()
    user_id = uuid4()
    assert latest_ltp_key("NIFTY") == "latest:ltp:NIFTY"
    assert broker_session_key(account_id) == f"broker:session:{account_id}"
    assert broker_status_key(account_id) == f"broker:status:{account_id}"
    assert signal_lock_key("NIFTY") == "signal:lock:NIFTY"
    assert order_idempotency_key("abc-1") == "order:idempotency:abc-1"
    assert rate_limit_key(user_id) == f"rate-limit:{user_id}"
    assert ws_presence_key(user_id) == f"ws:presence:{user_id}"


def test_empty_symbol_rejected() -> None:
    with pytest.raises(ValueError):
        latest_ltp_key("  ")


def test_secret_mappings_rejected() -> None:
    with pytest.raises(ValueError, match="must not store secret"):
        assert_non_secret_mapping({"access_token": "should-never-land-in-redis"})
    with pytest.raises(ValueError):
        assert_non_secret_mapping({"encrypted_totp": "nope"})
    assert_non_secret_mapping({"status": "CONNECTED", "ltp": 1})

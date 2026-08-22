"""Redis key namespaces. Redis is not the system of record and must not hold plaintext secrets."""

from __future__ import annotations

from uuid import UUID

from app.core.logging import REDACT_KEYS

IdLike = UUID | str


def _part(value: IdLike, *, field: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field} is required for Redis key")
    return text


def latest_ltp_key(symbol: str) -> str:
    return f"latest:ltp:{_part(symbol, field='symbol')}"


def broker_session_key(broker_account_id: IdLike) -> str:
    return f"broker:session:{_part(broker_account_id, field='broker_account_id')}"


def broker_status_key(broker_account_id: IdLike) -> str:
    return f"broker:status:{_part(broker_account_id, field='broker_account_id')}"


def signal_lock_key(symbol: str) -> str:
    return f"signal:lock:{_part(symbol, field='symbol')}"


def order_idempotency_key(idempotency_key: str) -> str:
    return f"order:idempotency:{_part(idempotency_key, field='idempotency_key')}"


def rate_limit_key(user_id: IdLike) -> str:
    return f"rate-limit:{_part(user_id, field='user_id')}"


def login_rate_limit_key(email: str) -> str:
    return f"rate-limit:login:{_part(email.lower(), field='email')}"


def login_lockout_key(email: str) -> str:
    return f"lockout:login:{_part(email.lower(), field='email')}"


def ws_presence_key(user_id: IdLike) -> str:
    return f"ws:presence:{_part(user_id, field='user_id')}"


def assert_non_secret_mapping(payload: dict[str, object]) -> None:
    """Refuse to cache mappings that look like credentials (API secrets, TOTP, tokens)."""
    for raw_key in payload:
        key = str(raw_key).lower()
        if key in REDACT_KEYS or any(secret in key for secret in REDACT_KEYS):
            raise ValueError("Redis must not store secret fields; keep tokens in PostgreSQL ciphertext")

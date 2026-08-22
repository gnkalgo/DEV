"""Resolve broker adapters by code. Only place that instantiates vendor SDKs/HTTP clients."""

from __future__ import annotations

import uuid
from typing import Any

from redis.asyncio import Redis

from app.brokers.base import BrokerAdapter
from app.brokers.dhan import DhanBrokerAdapter
from app.brokers.exceptions import BrokerError
from app.brokers.mock import MockBrokerAdapter
from app.brokers.models import BrokerCredentials
from app.db.models.enums import BrokerCode
from app.utils.redis_keys import assert_non_secret_mapping, broker_session_key, broker_status_key

_STUB_BROKERS = {BrokerCode.ZERODHA, BrokerCode.ANGEL_ONE, BrokerCode.GROWW, BrokerCode.ALICE_BLUE}

_mock_sessions: dict[str, MockBrokerAdapter] = {}


class BrokerManager:
    def __init__(self, redis: Redis | None = None) -> None:
        self.redis = redis

    def create_adapter(self, broker: str, credentials: BrokerCredentials) -> BrokerAdapter:
        code = BrokerCode(broker)
        if code == BrokerCode.MOCK:
            session_key = credentials.client_id or "default"
            if session_key not in _mock_sessions:
                _mock_sessions[session_key] = MockBrokerAdapter(credentials)
            return _mock_sessions[session_key]
        if code == BrokerCode.DHAN:
            return DhanBrokerAdapter(credentials)
        if code in _STUB_BROKERS:
            raise BrokerError("BROKER_NOT_IMPLEMENTED", f"{broker} adapter is not implemented yet")
        raise BrokerError("UNKNOWN_BROKER", f"Unknown broker: {broker}")

    async def cache_session(
        self,
        broker_account_id: uuid.UUID,
        *,
        status: str,
        metadata: dict[str, Any],
    ) -> None:
        if self.redis is None:
            return
        assert_non_secret_mapping(metadata)
        await self.redis.hset(broker_status_key(broker_account_id), mapping={"status": status})
        await self.redis.hset(
            broker_session_key(broker_account_id),
            mapping={k: str(v) for k, v in metadata.items()},
        )

    async def clear_session(self, broker_account_id: uuid.UUID) -> None:
        if self.redis is None:
            return
        await self.redis.delete(broker_status_key(broker_account_id), broker_session_key(broker_account_id))

    async def read_status(self, broker_account_id: uuid.UUID) -> str | None:
        if self.redis is None:
            return None
        value = await self.redis.hget(broker_status_key(broker_account_id), "status")
        return str(value) if value else None

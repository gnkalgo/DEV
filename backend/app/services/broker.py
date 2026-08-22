"""Broker save/connect/disconnect/test. Encrypts secrets; never returns tokens to clients."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.brokers.dhan import DhanBrokerAdapter
from app.brokers.exceptions import BrokerAuthError, BrokerError
from app.brokers.manager import BrokerManager
from app.brokers.models import BrokerCredentials
from app.core.config import Settings
from app.core.errors import ServiceError
from app.core.security import decrypt_secret, encrypt_secret
from app.db.models import BrokerAccount, BrokerToken
from app.db.models.enums import BrokerCode, BrokerConnectionStatus
from app.db.repositories.brokers import BrokerRepository
from app.db.repositories.users import AuditRepository
from app.schemas.broker import BrokerConnectRequest, BrokerCreateRequest, BrokerPublic
from app.utils.redis_keys import assert_non_secret_mapping


class BrokerService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        redis: Redis,
    ) -> None:
        self.session = session
        self.settings = settings
        self.redis = redis
        self.repo = BrokerRepository(session)
        self.audit = AuditRepository(session)
        self.manager = BrokerManager(redis)

    def _to_public(self, account: BrokerAccount) -> BrokerPublic:
        return BrokerPublic(
            id=account.id,
            broker=account.broker,
            client_id=account.client_id,
            status=account.status,
            has_api_key=bool(account.encrypted_api_key),
            has_api_secret=bool(account.encrypted_api_secret),
            has_totp=bool(account.encrypted_totp),
            created_at=account.created_at,
            updated_at=account.updated_at,
        )

    async def list_brokers(self, user_id: uuid.UUID) -> list[BrokerPublic]:
        rows = await self.repo.list_for_user(user_id)
        return [self._to_public(row) for row in rows]

    async def save_broker(self, user_id: uuid.UUID, payload: BrokerCreateRequest) -> BrokerPublic:
        if payload.broker not in {BrokerCode.MOCK, BrokerCode.DHAN}:
            raise ServiceError(501, "BROKER_NOT_IMPLEMENTED", f"{payload.broker.value} is not implemented yet")

        existing = await self.repo.get_by_unique(user_id, payload.broker.value, payload.client_id)
        if existing is None:
            account = BrokerAccount(
                user_id=user_id,
                broker=payload.broker.value,
                client_id=payload.client_id,
                status=BrokerConnectionStatus.DISCONNECTED.value,
            )
        else:
            account = existing

        if payload.api_key:
            account.encrypted_api_key = encrypt_secret(payload.api_key, self.settings.encryption_key)
        if payload.api_secret:
            account.encrypted_api_secret = encrypt_secret(payload.api_secret, self.settings.encryption_key)
        if payload.totp:
            account.encrypted_totp = encrypt_secret(payload.totp, self.settings.encryption_key)

        if existing is None:
            account = await self.repo.add(account)
        else:
            await self.session.flush()
            await self.session.refresh(account)

        await self.audit.add(
            event_type="broker.saved",
            user_id=user_id,
            ip_address=None,
            user_agent=None,
            metadata={"broker": account.broker, "client_id": account.client_id},
        )
        return self._to_public(account)

    def _credentials_from_account(
        self,
        account: BrokerAccount,
        *,
        access_token: str | None = None,
    ) -> BrokerCredentials:
        key = self.settings.encryption_key

        def _decrypt(value: str | None) -> str | None:
            if not value:
                return None
            return decrypt_secret(value, key)

        return BrokerCredentials(
            client_id=account.client_id,
            api_key=_decrypt(account.encrypted_api_key),
            api_secret=_decrypt(account.encrypted_api_secret),
            totp=_decrypt(account.encrypted_totp),
            access_token=access_token,
        )

    async def _load_access_token(self, account: BrokerAccount) -> str | None:
        token_row = await self.repo.latest_token(account.id)
        if token_row is None:
            return None
        return decrypt_secret(token_row.encrypted_access_token, self.settings.encryption_key)

    async def _store_access_token(self, account: BrokerAccount, access_token: str) -> None:
        expires = datetime.now(UTC) + timedelta(hours=24)
        await self.repo.add_token(
            BrokerToken(
                broker_account_id=account.id,
                encrypted_access_token=encrypt_secret(access_token, self.settings.encryption_key),
                token_expires_at=expires,
            )
        )

    async def connect(
        self,
        user_id: uuid.UUID,
        broker_account_id: uuid.UUID,
        payload: BrokerConnectRequest | None = None,
    ) -> tuple[BrokerPublic, dict[str, str]]:
        account = await self._require_account(user_id, broker_account_id)
        account.status = BrokerConnectionStatus.CONNECTING.value
        await self.session.flush()

        access_token = payload.access_token if payload else None
        if not access_token and account.broker == BrokerCode.DHAN.value:
            access_token = await self._load_access_token(account)

        credentials = self._credentials_from_account(account, access_token=access_token)
        adapter = self.manager.create_adapter(account.broker, credentials)
        try:
            metadata = await adapter.authenticate()
        except BrokerError as exc:
            account.status = BrokerConnectionStatus.ERROR.value
            await self.session.flush()
            raise ServiceError(400, exc.code, exc.message) from exc

        if isinstance(adapter, DhanBrokerAdapter) and adapter.access_token:
            await self._store_access_token(account, adapter.access_token)

        account.status = BrokerConnectionStatus.CONNECTED.value
        await self.session.flush()
        await self.session.refresh(account)

        safe_meta = {k: str(v) for k, v in metadata.items() if k != "accessToken"}
        assert_non_secret_mapping(safe_meta)
        await self.manager.cache_session(account.id, status=account.status, metadata=safe_meta)

        await self.audit.add(
            event_type="broker.connected",
            user_id=user_id,
            ip_address=None,
            user_agent=None,
            metadata={"broker": account.broker, "broker_account_id": str(account.id)},
        )
        return self._to_public(account), safe_meta

    async def disconnect(self, user_id: uuid.UUID, broker_account_id: uuid.UUID) -> BrokerPublic:
        account = await self._require_account(user_id, broker_account_id)
        credentials = self._credentials_from_account(account)
        adapter = self.manager.create_adapter(account.broker, credentials)
        await adapter.disconnect()
        account.status = BrokerConnectionStatus.DISCONNECTED.value
        await self.session.flush()
        await self.manager.clear_session(account.id)
        await self.audit.add(
            event_type="broker.disconnected",
            user_id=user_id,
            ip_address=None,
            user_agent=None,
            metadata={"broker": account.broker, "broker_account_id": str(account.id)},
        )
        return self._to_public(account)

    async def test_connection(
        self,
        user_id: uuid.UUID,
        broker_account_id: uuid.UUID,
    ) -> tuple[BrokerPublic, dict[str, str]]:
        account = await self._require_account(user_id, broker_account_id)
        access_token = await self._load_access_token(account)
        credentials = self._credentials_from_account(account, access_token=access_token)
        adapter = self.manager.create_adapter(account.broker, credentials)
        try:
            metadata = await adapter.authenticate()
        except BrokerAuthError as exc:
            raise ServiceError(400, exc.code, exc.message) from exc
        except BrokerError as exc:
            raise ServiceError(400, exc.code, exc.message) from exc
        safe_meta = {k: str(v) for k, v in metadata.items()}
        return self._to_public(account), safe_meta

    async def connected_account_for_user(self, user_id: uuid.UUID) -> BrokerAccount | None:
        rows = await self.repo.list_for_user(user_id)
        for row in rows:
            if row.status == BrokerConnectionStatus.CONNECTED.value:
                return row
        return None

    async def _require_account(self, user_id: uuid.UUID, broker_account_id: uuid.UUID) -> BrokerAccount:
        account = await self.repo.get_for_user(user_id, broker_account_id)
        if account is None:
            raise ServiceError(404, "BROKER_NOT_FOUND", "Broker account not found")
        return account

    async def credentials_for_execution(self, account: BrokerAccount) -> BrokerCredentials:
        access_token = await self._load_access_token(account)
        return self._credentials_from_account(account, access_token=access_token)

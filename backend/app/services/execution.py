"""Execution routing: PAPER uses Mock; LIVE uses real broker adapters."""

from __future__ import annotations

import uuid

from app.brokers.base import BrokerAdapter
from app.brokers.exceptions import BrokerError
from app.brokers.manager import BrokerManager
from app.brokers.models import BrokerCredentials, OrderRequest, OrderResponse
from app.core.config import Settings
from app.core.errors import ServiceError
from app.db.models import BrokerAccount
from app.db.models.enums import BrokerCode, BrokerConnectionStatus


class PaperExecutor:
    def __init__(self, manager: BrokerManager) -> None:
        self.manager = manager

    async def submit(
        self,
        account: BrokerAccount,
        order: OrderRequest,
        *,
        credentials: BrokerCredentials,
    ) -> OrderResponse:
        adapter = self._adapter_for_paper(account, credentials)
        return await adapter.place_order(order)

    async def cancel(
        self,
        account: BrokerAccount,
        broker_order_id: str,
        *,
        credentials: BrokerCredentials,
    ) -> OrderResponse:
        adapter = self._adapter_for_paper(account, credentials)
        return await adapter.cancel_order(broker_order_id)

    def _adapter_for_paper(self, account: BrokerAccount, credentials: BrokerCredentials) -> BrokerAdapter:
        if account.broker != BrokerCode.MOCK.value:
            return self.manager.create_adapter(BrokerCode.MOCK.value, credentials)
        return self.manager.create_adapter(account.broker, credentials)


class LiveExecutor:
    def __init__(self, manager: BrokerManager, settings: Settings) -> None:
        self.manager = manager
        self.settings = settings

    def _ensure_live(self) -> None:
        if self.settings.trading_mode != "LIVE":
            raise ServiceError(
                403,
                "LIVE_TRADING_DISABLED",
                "LIVE trading is disabled. Set TRADING_MODE=LIVE explicitly to enable.",
            )

    async def submit(
        self,
        account: BrokerAccount,
        order: OrderRequest,
        *,
        credentials: BrokerCredentials,
    ) -> OrderResponse:
        self._ensure_live()
        if account.broker == BrokerCode.MOCK.value:
            raise ServiceError(400, "INVALID_BROKER", "Mock broker cannot be used in LIVE mode")
        if account.status != BrokerConnectionStatus.CONNECTED.value:
            raise ServiceError(400, "BROKER_NOT_CONNECTED", "Broker must be connected before LIVE orders")
        adapter = self.manager.create_adapter(account.broker, credentials)
        try:
            return await adapter.place_order(order)
        except BrokerError:
            raise

    async def cancel(
        self,
        account: BrokerAccount,
        broker_order_id: str,
        *,
        credentials: BrokerCredentials,
    ) -> OrderResponse:
        self._ensure_live()
        adapter = self.manager.create_adapter(account.broker, credentials)
        return await adapter.cancel_order(broker_order_id)


class ExecutionRouter:
    def __init__(self, settings: Settings, manager: BrokerManager) -> None:
        self.settings = settings
        self.paper = PaperExecutor(manager)
        self.live = LiveExecutor(manager, settings)

    async def submit(
        self,
        account: BrokerAccount,
        order: OrderRequest,
        *,
        credentials: BrokerCredentials,
    ) -> OrderResponse:
        if self.settings.trading_mode == "LIVE" and account.broker != BrokerCode.MOCK.value:
            return await self.live.submit(account, order, credentials=credentials)
        return await self.paper.submit(account, order, credentials=credentials)

    async def cancel(
        self,
        account: BrokerAccount,
        broker_order_id: str,
        *,
        credentials: BrokerCredentials,
    ) -> OrderResponse:
        if self.settings.trading_mode == "LIVE" and account.broker != BrokerCode.MOCK.value:
            return await self.live.cancel(account, broker_order_id, credentials=credentials)
        return await self.paper.cancel(account, broker_order_id, credentials=credentials)

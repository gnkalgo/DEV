"""Mock broker for PAPER mode. Simulates outcomes; never places real trades."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any

from app.brokers.base import BrokerAdapter
from app.brokers.exceptions import BrokerError
from app.brokers.models import (
    BrokerCredentials,
    HoldingInfo,
    MarginInfo,
    OrderRequest,
    OrderResponse,
    PositionInfo,
    Quote,
)

_IST = timezone(timedelta(hours=5, minutes=30))
_OPEN = time(9, 15)
_CLOSE = time(15, 30)
_MOCK_PRICES = {
    "NIFTY": Decimal("24500.00"),
    "BANKNIFTY": Decimal("52000.00"),
    "RELIANCE": Decimal("2850.50"),
    "TCS": Decimal("4100.00"),
}


class MockBrokerAdapter(BrokerAdapter):
    broker_code = "MOCK"

    def __init__(self, credentials: BrokerCredentials) -> None:
        super().__init__(credentials)
        self._orders: dict[str, dict[str, Any]] = {}
        self._positions: dict[tuple[str, str], PositionInfo] = {}
        self._available_margin = Decimal("1000000.00")
        self._connected = False

    def _market_open(self) -> bool:
        now = datetime.now(_IST)
        return now.weekday() < 5 and _OPEN <= now.time() <= _CLOSE

    def _ltp_for(self, symbol: str) -> Decimal:
        return _MOCK_PRICES.get(symbol.upper(), Decimal("100.00"))

    async def authenticate(self) -> dict[str, Any]:
        self._connected = True
        return {
            "broker": self.broker_code,
            "client_id": self.credentials.client_id or "MOCK-CLIENT",
            "session": "mock-paper",
        }

    async def refresh_session(self) -> dict[str, Any]:
        return await self.authenticate()

    async def disconnect(self) -> None:
        self._connected = False

    async def get_ltp(self, symbol: str, exchange: str) -> Quote:
        return Quote(
            symbol=symbol.upper(),
            exchange=exchange.upper(),
            ltp=self._ltp_for(symbol),
            timestamp=datetime.now(UTC),
        )

    async def get_ohlcv(
        self,
        symbol: str,
        exchange: str,
        *,
        interval: str,
        start: datetime,
        end: datetime,
    ) -> list[dict[str, Any]]:
        ltp = self._ltp_for(symbol)
        return [
            {
                "symbol": symbol.upper(),
                "exchange": exchange.upper(),
                "interval": interval,
                "open": str(ltp),
                "high": str(ltp),
                "low": str(ltp),
                "close": str(ltp),
                "volume": 0,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        ]

    async def get_option_chain(self, symbol: str, exchange: str) -> dict[str, Any]:
        return {
            "symbol": symbol.upper(),
            "exchange": exchange.upper(),
            "source": "MOCK",
            "strikes": [],
            "note": "Mock option chain placeholder",
        }

    async def get_margin(self) -> MarginInfo:
        used = sum(
            (abs(p.quantity) * p.average_price for p in self._positions.values()),
            Decimal("0"),
        )
        return MarginInfo(available=self._available_margin - used, used=used)

    async def get_positions(self) -> list[PositionInfo]:
        return list(self._positions.values())

    async def get_holdings(self) -> list[HoldingInfo]:
        return [
            HoldingInfo(
                symbol=p.symbol,
                exchange=p.exchange,
                quantity=p.quantity,
                average_price=p.average_price,
            )
            for p in self._positions.values()
            if p.quantity > 0
        ]

    async def _validate_order(self, order: OrderRequest) -> None:
        symbol = order.symbol.upper()
        if order.quantity <= 0:
            raise BrokerError("INVALID_QUANTITY", "Quantity must be positive")
        if order.quantity > 10000:
            raise BrokerError("INVALID_QUANTITY", "Quantity exceeds mock limit")
        if symbol == "REJECT":
            raise BrokerError("ORDER_REJECTED", "Mock broker rejected this symbol")
        if symbol == "MARGIN_FAIL":
            raise BrokerError("INSUFFICIENT_MARGIN", "Mock insufficient margin")
        if symbol == "MARKET_CLOSED":
            raise BrokerError("MARKET_CLOSED", "Mock market closed")
        notional = self._ltp_for(symbol) * order.quantity
        margin = await self.get_margin()
        if notional > margin.available:
            raise BrokerError("INSUFFICIENT_MARGIN", "Mock insufficient margin")

    async def place_order(self, order: OrderRequest) -> OrderResponse:
        await self._validate_order(order)
        broker_order_id = f"MOCK-{uuid.uuid4().hex[:12].upper()}"
        symbol = order.symbol.upper()
        status = "ACKNOWLEDGED"
        filled_qty = 0
        if symbol == "PARTIAL":
            status = "PARTIALLY_FILLED"
            filled_qty = max(1, order.quantity // 2)
        elif order.order_type == "MARKET":
            status = "FILLED"
            filled_qty = order.quantity

        self._orders[broker_order_id] = {
            "request": order,
            "status": status,
            "filled_quantity": filled_qty,
        }

        if filled_qty > 0:
            self._apply_fill(order, filled_qty)

        return OrderResponse(
            success=True,
            broker_order_id=broker_order_id,
            status=status,
            filled_quantity=filled_qty,
            raw={"source": "MOCK"},
        )

    def _apply_fill(self, order: OrderRequest, quantity: int) -> None:
        key = (order.symbol.upper(), order.exchange.upper())
        price = order.price or self._ltp_for(order.symbol)
        existing = self._positions.get(key)
        signed_qty = quantity if order.side == "BUY" else -quantity
        if existing is None:
            self._positions[key] = PositionInfo(
                symbol=order.symbol.upper(),
                exchange=order.exchange.upper(),
                quantity=signed_qty,
                average_price=price,
            )
            return
        new_qty = existing.quantity + signed_qty
        if new_qty == 0:
            self._positions.pop(key, None)
            return
        if (existing.quantity > 0 and signed_qty > 0) or (existing.quantity < 0 and signed_qty < 0):
            total_cost = existing.average_price * abs(existing.quantity) + price * quantity
            avg = total_cost / abs(new_qty)
        else:
            avg = existing.average_price
        self._positions[key] = PositionInfo(
            symbol=existing.symbol,
            exchange=existing.exchange,
            quantity=new_qty,
            average_price=avg,
        )

    async def modify_order(
        self,
        broker_order_id: str,
        *,
        quantity: int | None = None,
        price: float | None = None,
        order_type: str | None = None,
    ) -> OrderResponse:
        record = self._orders.get(broker_order_id)
        if record is None:
            raise BrokerError("ORDER_NOT_FOUND", "Mock order not found")
        if record["status"] in {"FILLED", "CANCELLED", "REJECTED"}:
            raise BrokerError("ORDER_NOT_MODIFIABLE", "Order cannot be modified")
        req: OrderRequest = record["request"]
        if quantity is not None:
            req.quantity = quantity
        if price is not None:
            req.price = Decimal(str(price))
        if order_type is not None:
            req.order_type = order_type
        record["status"] = "ACKNOWLEDGED"
        return OrderResponse(
            success=True,
            broker_order_id=broker_order_id,
            status=record["status"],
            filled_quantity=record["filled_quantity"],
            raw={"source": "MOCK", "modified": True},
        )

    async def cancel_order(self, broker_order_id: str) -> OrderResponse:
        record = self._orders.get(broker_order_id)
        if record is None:
            raise BrokerError("ORDER_NOT_FOUND", "Mock order not found")
        if record["status"] in {"FILLED", "CANCELLED"}:
            raise BrokerError("ORDER_NOT_CANCELLABLE", "Order cannot be cancelled")
        record["status"] = "CANCELLED"
        return OrderResponse(
            success=True,
            broker_order_id=broker_order_id,
            status="CANCELLED",
            filled_quantity=record["filled_quantity"],
            raw={"source": "MOCK"},
        )

    async def get_order_status(self, broker_order_id: str) -> OrderResponse:
        record = self._orders.get(broker_order_id)
        if record is None:
            raise BrokerError("ORDER_NOT_FOUND", "Mock order not found")
        return OrderResponse(
            success=True,
            broker_order_id=broker_order_id,
            status=record["status"],
            filled_quantity=record["filled_quantity"],
            raw={"source": "MOCK"},
        )

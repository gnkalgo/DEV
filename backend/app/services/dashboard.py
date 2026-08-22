"""Dashboard assembly from config. Does not call brokers or invent live quotes."""

from datetime import UTC, datetime, time, timedelta, timezone

from app.core.config import Settings
from app.schemas.dashboard import (
    BrokerStatus,
    CapitalBlock,
    DashboardResponse,
    IpDetails,
    MarketStatus,
    OrderBook,
    OrderBookLevel,
    SignalRow,
)

_IST = timezone(timedelta(hours=5, minutes=30))
_OPEN = time(9, 15)
_CLOSE = time(15, 30)


def _indicative_market_status() -> MarketStatus:
    now = datetime.now(_IST)
    weekday = now.weekday() < 5
    in_session = _OPEN <= now.time() <= _CLOSE
    status = "OPEN" if weekday and in_session else "CLOSED"
    return MarketStatus(
        status=status,
        segment="NSE",
        note="Indicative NSE cash session window only — not exchange or broker data",
    )


class DashboardService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build(self) -> DashboardResponse:
        app_ip = (self.settings.server_public_ip or "").strip()
        broker_ip = (self.settings.broker_api_ip or "").strip()
        connected = bool(app_ip and broker_ip)
        return DashboardResponse(
            trading_mode=self.settings.trading_mode,
            environment=self.settings.app_env,
            market=_indicative_market_status(),
            broker=BrokerStatus(
                status="DISCONNECTED",
                broker=None,
                note="Mock/Dhan connect arrives in Phase 5–6",
            ),
            capital=CapitalBlock(
                mock_labeled=True,
                available="0.00",
                margin_used="0.00",
                day_pnl="0.00",
                exposure="0.00",
            ),
            ip_details=IpDetails(
                application_ip=app_ip or "not configured",
                broker_api_ip=broker_ip or "not configured",
                connection_status="CONFIGURED" if connected else "UNKNOWN",
                last_verified=datetime.now(UTC) if connected else None,
                environment=self.settings.app_env,
            ),
            signals=[
                SignalRow(
                    ticker="—",
                    segment="EQ",
                    ai_trend="—",
                    confidence="—",
                    strategy_state="SHELL",
                    entry="—",
                    sl="—",
                    target="—",
                    status="PLACEHOLDER",
                )
            ],
            positions=[],
            orders=[],
            order_book=OrderBook(
                symbol="NIFTY",
                source="MOCK",
                bids=[
                    OrderBookLevel(price="0.00", quantity=0),
                    OrderBookLevel(price="0.00", quantity=0),
                ],
                asks=[
                    OrderBookLevel(price="0.00", quantity=0),
                    OrderBookLevel(price="0.00", quantity=0),
                ],
            ),
        )

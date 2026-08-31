from app.brokers.base import OrderRequest
from app.brokers.dhan import DhanAdapter


def test_dhan_payload_uses_numeric_security_id_and_nse_eq():
    payload = DhanAdapter.order_payload(
        OrderRequest(
            symbol="RELIANCE",
            exchange="NSE",
            side="BUY",
            quantity=1,
            order_type="MARKET",
            product_type="INTRADAY",
            security_id="2885",
            exchange_segment="NSE_EQ",
        )
    )
    assert payload["securityId"] == "2885"
    assert payload["exchangeSegment"] == "NSE_EQ"
    assert payload["productType"] == "INTRA"
    assert payload["transactionType"] == "BUY"

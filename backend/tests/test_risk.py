from datetime import datetime

import pytest

from app.schemas.auth import RegisterRequest
from app.services.risk import RiskRejection, is_market_hours, validate_order


def test_password_rules_reject_weak():
    with pytest.raises(Exception):
        RegisterRequest(email="a@b.com", password="short", full_name="Test User")


def test_password_rules_accept_strong():
    data = RegisterRequest(
        email="trader@gnkalgo.com",
        password="SecurePass1!",
        full_name="Test Trader",
        phone="9876543210",
    )
    assert data.email == "trader@gnkalgo.com"


def test_paper_order_allowed_off_hours():
    validate_order(quantity=10, paper_mode=True, now=datetime(2026, 8, 23, 22, 0))


def test_live_order_blocked_weekend():
    weekend = datetime(2026, 8, 23, 11, 0)  # Sunday
    with pytest.raises(RiskRejection):
        validate_order(quantity=10, paper_mode=False, now=weekend)


def test_quantity_cap():
    with pytest.raises(RiskRejection):
        validate_order(quantity=9999, max_quantity=500, paper_mode=True)


def test_market_hours_weekday_open():
    open_time = datetime(2026, 8, 24, 10, 0)  # Monday
    assert is_market_hours(open_time) is True

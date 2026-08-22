"""Order state machine tests."""

import pytest

from app.core.errors import ServiceError
from app.db.models.enums import OrderStatus
from app.services.order_state import assert_transition, map_broker_status


def test_valid_transition_created_to_validating() -> None:
    assert_transition(OrderStatus.CREATED.value, OrderStatus.VALIDATING.value)


def test_invalid_terminal_transition() -> None:
    with pytest.raises(ServiceError) as exc:
        assert_transition(OrderStatus.FILLED.value, OrderStatus.CANCELLED.value)
    assert exc.value.code == "INVALID_TRANSITION"


def test_map_broker_status_traded() -> None:
    assert map_broker_status("TRADED") == OrderStatus.FILLED.value

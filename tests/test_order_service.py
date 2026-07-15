from datetime import datetime, timezone

import pytest

from sampleorder.exceptions import ValidationError
from sampleorder.models import OrderStatus
from sampleorder.services.order_service import (
    QUANTITY_ERROR,
    SAMPLE_NOT_FOUND_ERROR,
    OrderService,
)


@pytest.fixture
def order_service(order_repository, sample_repository):
    return OrderService(order_repository, sample_repository)


def test_create_order_fails_for_unknown_sample_id(order_service, order_repository):
    with pytest.raises(ValidationError) as excinfo:
        order_service.create_order("S-999", "고객A", 10)
    assert str(excinfo.value) == SAMPLE_NOT_FOUND_ERROR
    assert order_repository.list_all() == []


@pytest.mark.parametrize("invalid_quantity", [0, -1, 1.5])
def test_create_order_fails_for_invalid_quantity(order_service, sample_repository, invalid_quantity):
    sample_repository.create("A", 0.5, 0.9)
    with pytest.raises(ValidationError) as excinfo:
        order_service.create_order("S-001", "고객A", invalid_quantity)
    assert str(excinfo.value) == QUANTITY_ERROR


def test_create_order_succeeds_with_reserved_status(order_service, sample_repository):
    sample_repository.create("A", 0.5, 0.9)
    order = order_service.create_order("S-001", "고객A", 10)
    assert order.status == OrderStatus.RESERVED
    assert order.order_id.startswith("ORD-")
    assert datetime.fromisoformat(order.created_at).tzinfo is not None

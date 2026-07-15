from datetime import datetime, timezone

import pytest

from sampleorder.models import OrderStatus
from sampleorder.services.shipping_service import ShippingService


@pytest.fixture
def shipping_service(order_repository, sample_repository):
    return ShippingService(order_repository, sample_repository)


def test_release_deducts_stock_and_transitions_to_release(
    shipping_service, sample_repository, order_repository, fixed_now
):
    sample_repository.create("A", 0.5, 0.9)
    sample_repository.update("S-001", stock=200)
    order = order_repository.create("S-001", "고객A", 150)
    order_repository.update(order.order_id, status=OrderStatus.CONFIRMED)

    result = shipping_service.release(order.order_id, now_fn=lambda: fixed_now)

    assert sample_repository.get("S-001").stock == 50
    assert result.order.status == OrderStatus.RELEASE
    assert result.processed_at == fixed_now


def test_list_confirmed_orders_excludes_other_statuses(
    shipping_service, sample_repository, order_repository
):
    sample_repository.create("A", 0.5, 0.9)
    sample_repository.update("S-001", stock=200)
    reserved = order_repository.create("S-001", "고객A", 10)
    confirmed = order_repository.create("S-001", "고객B", 20)
    order_repository.update(confirmed.order_id, status=OrderStatus.CONFIRMED)

    result = shipping_service.list_confirmed_orders()

    assert [o.order_id for o in result] == [confirmed.order_id]

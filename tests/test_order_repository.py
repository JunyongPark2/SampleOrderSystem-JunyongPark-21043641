from datetime import datetime, timezone

import pytest

from sampleorder.exceptions import NotFoundError
from sampleorder.json_store import JsonFileStore
from sampleorder.models import OrderStatus
from sampleorder.repositories.order_repository import OrderRepository


def test_order_ids_increment_within_same_date(order_repository):
    first = order_repository.create("S-001", "고객A", 10)
    second = order_repository.create("S-001", "고객B", 20)
    assert first.order_id == "ORD-20260416-0001"
    assert second.order_id == "ORD-20260416-0002"


def test_order_id_sequence_restarts_on_new_date(tmp_path):
    store = JsonFileStore(tmp_path / "orders.json")
    day1 = datetime(2026, 4, 16, 9, 0, 0, tzinfo=timezone.utc)
    day2 = datetime(2026, 4, 17, 9, 0, 0, tzinfo=timezone.utc)

    repo_day1 = OrderRepository(store, now_fn=lambda: day1)
    repo_day1.create("S-001", "고객A", 10)

    repo_day2 = OrderRepository(store, now_fn=lambda: day2)
    second_order = repo_day2.create("S-001", "고객B", 20)

    assert second_order.order_id == "ORD-20260417-0001"


def test_created_order_has_reserved_status(order_repository):
    order = order_repository.create("S-001", "고객A", 10)
    assert order.status == OrderStatus.RESERVED


def test_get_raises_not_found_for_unknown_id(order_repository):
    with pytest.raises(NotFoundError):
        order_repository.get("ORD-20260416-9999")


def test_list_by_status_filters_correctly(order_repository):
    reserved = order_repository.create("S-001", "고객A", 10)
    to_confirm = order_repository.create("S-001", "고객B", 20)
    order_repository.update(to_confirm.order_id, status=OrderStatus.CONFIRMED)

    reserved_orders = order_repository.list_by_status(OrderStatus.RESERVED)
    confirmed_orders = order_repository.list_by_status(OrderStatus.CONFIRMED)

    assert [o.order_id for o in reserved_orders] == [reserved.order_id]
    assert [o.order_id for o in confirmed_orders] == [to_confirm.order_id]

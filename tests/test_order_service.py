from datetime import datetime, timezone

import pytest

from sampleorder.exceptions import ValidationError
from sampleorder.models import OrderStatus
from sampleorder.services.order_service import (
    APPROVAL_SHORTAGE,
    APPROVAL_SUFFICIENT,
    QUANTITY_ERROR,
    SAMPLE_NOT_FOUND_ERROR,
    OrderService,
)
from sampleorder.services.production_service import ProductionService


@pytest.fixture
def production_service(order_repository, sample_repository):
    return ProductionService(order_repository, sample_repository)


@pytest.fixture
def order_service(order_repository, sample_repository, production_service):
    return OrderService(order_repository, sample_repository, production_service)


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


def test_preview_approval_sufficient_stock(order_service, sample_repository):
    sample_repository.create("A", 0.8, 0.92)
    sample_repository.update("S-001", stock=100)
    order = order_service.create_order("S-001", "고객A", 50)

    preview = order_service.preview_approval(order.order_id)

    assert preview.kind == APPROVAL_SUFFICIENT
    assert preview.shortage_qty == 0


def test_confirm_approval_sufficient_transitions_to_confirmed_without_stock_change(
    order_service, sample_repository, order_repository
):
    sample_repository.create("A", 0.8, 0.92)
    sample_repository.update("S-001", stock=100)
    order = order_service.create_order("S-001", "고객A", 50)
    preview = order_service.preview_approval(order.order_id)

    updated = order_service.confirm_approval(order.order_id, preview)

    assert updated.status == OrderStatus.CONFIRMED
    assert sample_repository.get("S-001").stock == 100


def test_preview_approval_shortage_computes_actual_yield_and_time(order_service, sample_repository):
    sample_repository.create("SiC 파워기판-6인치", 0.8, 0.92)
    sample_repository.update("S-001", stock=30)
    order = order_service.create_order("S-001", "고객A", 200)

    preview = order_service.preview_approval(order.order_id)

    assert preview.kind == APPROVAL_SHORTAGE
    assert preview.shortage_qty == 170
    assert preview.actual_yield_qty == 185  # ceil(170 / 0.92)
    assert preview.total_time == pytest.approx(0.8 * 185)


def test_confirm_approval_shortage_transitions_to_producing_and_enqueues(
    order_service, production_service, sample_repository
):
    sample_repository.create("SiC 파워기판-6인치", 0.8, 0.92)
    sample_repository.update("S-001", stock=30)
    order = order_service.create_order("S-001", "고객A", 200)
    preview = order_service.preview_approval(order.order_id)

    updated = order_service.confirm_approval(order.order_id, preview)

    assert updated.status == OrderStatus.PRODUCING
    assert production_service.queue_length() == 1


def test_reject_order_transitions_to_rejected(order_service, sample_repository):
    sample_repository.create("A", 0.5, 0.9)
    order = order_service.create_order("S-001", "고객A", 10)

    rejected = order_service.reject_order(order.order_id)

    assert rejected.status == OrderStatus.REJECTED


def test_list_reserved_orders_excludes_other_statuses(order_service, sample_repository):
    sample_repository.create("A", 0.5, 0.9)
    sample_repository.update("S-001", stock=100)
    reserved = order_service.create_order("S-001", "고객A", 10)
    to_reject = order_service.create_order("S-001", "고객B", 10)
    order_service.reject_order(to_reject.order_id)

    reserved_orders = order_service.list_reserved_orders()

    assert [o.order_id for o in reserved_orders] == [reserved.order_id]

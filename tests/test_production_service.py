from datetime import datetime, timedelta, timezone

import pytest

from sampleorder.json_store import JsonFileStore
from sampleorder.models import OrderStatus
from sampleorder.services.production_service import ProductionService


@pytest.fixture
def production_service(order_repository, sample_repository):
    return ProductionService(order_repository, sample_repository)


def test_enqueue_sets_started_at_for_first_item(production_service, fixed_now):
    item = production_service.enqueue(
        order_id="ORD-1",
        sample_id="S-001",
        sample_name="시료A",
        quantity=200,
        shortage_qty=170,
        actual_yield_qty=185,
        total_time=148.0,
        now_fn=lambda: fixed_now,
    )
    assert item.started_at == fixed_now
    assert production_service.queue_length() == 1


def test_enqueue_leaves_started_at_none_for_subsequent_items(production_service, fixed_now):
    production_service.enqueue(
        order_id="ORD-1",
        sample_id="S-001",
        sample_name="시료A",
        quantity=200,
        shortage_qty=170,
        actual_yield_qty=185,
        total_time=148.0,
        now_fn=lambda: fixed_now,
    )
    second = production_service.enqueue(
        order_id="ORD-2",
        sample_id="S-002",
        sample_name="시료B",
        quantity=100,
        shortage_qty=80,
        actual_yield_qty=90,
        total_time=45.0,
        now_fn=lambda: fixed_now,
    )
    assert second.started_at is None
    assert production_service.queue_length() == 2


def test_advance_does_nothing_before_total_time_elapses(
    production_service, sample_repository, order_repository, fixed_now
):
    sample_repository.create("A", 0.8, 0.92)
    order = order_repository.create("S-001", "고객A", 200)
    production_service.enqueue(
        order.order_id, "S-001", "A", 200, 170, 185, 148.0, now_fn=lambda: fixed_now
    )

    almost_done = fixed_now + timedelta(minutes=147)
    production_service.advance(now_fn=lambda: almost_done)

    assert production_service.queue_length() == 1
    assert order_repository.get(order.order_id).status == OrderStatus.RESERVED


def test_advance_completes_item_and_updates_stock_and_status(
    production_service, sample_repository, order_repository, fixed_now
):
    sample_repository.create("A", 0.8, 0.92)
    order = order_repository.create("S-001", "고객A", 200)
    production_service.enqueue(
        order.order_id, "S-001", "A", 200, 170, 185, 148.0, now_fn=lambda: fixed_now
    )

    completion_time = fixed_now + timedelta(minutes=148)
    production_service.advance(now_fn=lambda: completion_time)

    assert production_service.queue_length() == 0
    assert order_repository.get(order.order_id).status == OrderStatus.CONFIRMED
    assert sample_repository.get("S-001").stock == 185


def test_advance_processes_multiple_completions_in_one_call(
    production_service, sample_repository, order_repository, fixed_now
):
    sample_repository.create("A", 0.8, 0.92)
    order1 = order_repository.create("S-001", "고객A", 100)
    order2 = order_repository.create("S-001", "고객B", 50)
    production_service.enqueue(order1.order_id, "S-001", "A", 100, 100, 109, 10.0, now_fn=lambda: fixed_now)
    production_service.enqueue(order2.order_id, "S-001", "A", 50, 50, 55, 5.0, now_fn=lambda: fixed_now)

    far_future = fixed_now + timedelta(minutes=100)
    production_service.advance(now_fn=lambda: far_future)

    assert production_service.queue_length() == 0
    assert order_repository.get(order1.order_id).status == OrderStatus.CONFIRMED
    assert order_repository.get(order2.order_id).status == OrderStatus.CONFIRMED
    assert sample_repository.get("S-001").stock == 109 + 55


def test_advance_sets_next_item_started_at_to_previous_completion_time(
    production_service, sample_repository, order_repository, fixed_now
):
    sample_repository.create("A", 0.8, 0.92)
    order1 = order_repository.create("S-001", "고객A", 100)
    order2 = order_repository.create("S-001", "고객B", 50)
    production_service.enqueue(order1.order_id, "S-001", "A", 100, 100, 109, 10.0, now_fn=lambda: fixed_now)
    second_item = production_service.enqueue(
        order2.order_id, "S-001", "A", 50, 50, 55, 5.0, now_fn=lambda: fixed_now
    )
    assert second_item.started_at is None

    completion_time = fixed_now + timedelta(minutes=10)
    production_service.advance(now_fn=lambda: completion_time)

    assert production_service.queue_length() == 1
    remaining = production_service.current_item(now_fn=lambda: completion_time)
    assert remaining.item.order_id == order2.order_id
    assert remaining.item.started_at == completion_time


def test_current_item_progress_clamps_between_zero_and_one(
    production_service, sample_repository, order_repository, fixed_now
):
    sample_repository.create("A", 0.8, 0.92)
    order = order_repository.create("S-001", "고객A", 200)
    production_service.enqueue(
        order.order_id, "S-001", "A", 200, 170, 185, 148.0, now_fn=lambda: fixed_now
    )

    at_start = production_service.current_item(now_fn=lambda: fixed_now)
    at_half = production_service.current_item(now_fn=lambda: fixed_now + timedelta(minutes=74))
    after_end = production_service.current_item(now_fn=lambda: fixed_now + timedelta(minutes=300))

    assert at_start.progress == pytest.approx(0.0)
    assert at_half.progress == pytest.approx(0.5)
    assert after_end.progress == 1.0


def test_current_item_returns_none_when_queue_empty(production_service, fixed_now):
    assert production_service.current_item(now_fn=lambda: fixed_now) is None


def test_pending_queue_excludes_head_and_accumulates_completion_time(
    production_service, sample_repository, order_repository, fixed_now
):
    sample_repository.create("A", 0.8, 0.92)
    order1 = order_repository.create("S-001", "고객A", 100)
    order2 = order_repository.create("S-001", "고객B", 50)
    order3 = order_repository.create("S-001", "고객C", 30)
    production_service.enqueue(order1.order_id, "S-001", "A", 100, 100, 109, 10.0, now_fn=lambda: fixed_now)
    production_service.enqueue(order2.order_id, "S-001", "A", 50, 50, 55, 5.0, now_fn=lambda: fixed_now)
    production_service.enqueue(order3.order_id, "S-001", "A", 30, 30, 33, 3.0, now_fn=lambda: fixed_now)

    pending = production_service.pending_queue(now_fn=lambda: fixed_now)

    assert [p.item.order_id for p in pending] == [order2.order_id, order3.order_id]
    assert pending[0].expected_completion == fixed_now + timedelta(minutes=10 + 5)
    assert pending[1].expected_completion == fixed_now + timedelta(minutes=10 + 5 + 3)


def test_pending_queue_empty_when_only_head_present(
    production_service, sample_repository, order_repository, fixed_now
):
    sample_repository.create("A", 0.8, 0.92)
    order = order_repository.create("S-001", "고객A", 200)
    production_service.enqueue(
        order.order_id, "S-001", "A", 200, 170, 185, 148.0, now_fn=lambda: fixed_now
    )
    assert production_service.pending_queue(now_fn=lambda: fixed_now) == []


def test_queue_survives_restart_via_store(
    queue_store, sample_repository, order_repository, fixed_now
):
    sample_repository.create("A", 0.8, 0.92)
    order = order_repository.create("S-001", "고객A", 200)

    first_instance = ProductionService(order_repository, sample_repository, store=queue_store)
    first_instance.enqueue(
        order.order_id, "S-001", "A", 200, 170, 185, 148.0, now_fn=lambda: fixed_now
    )

    second_instance = ProductionService(order_repository, sample_repository, store=queue_store)
    assert second_instance.queue_length() == 1

    completion_time = fixed_now + timedelta(minutes=148)
    second_instance.advance(now_fn=lambda: completion_time)
    assert second_instance.queue_length() == 0
    assert order_repository.get(order.order_id).status == OrderStatus.CONFIRMED

    third_instance = ProductionService(order_repository, sample_repository, store=queue_store)
    assert third_instance.queue_length() == 0


def test_queue_restores_started_at_and_pending_order(
    queue_store, sample_repository, order_repository, fixed_now
):
    sample_repository.create("A", 0.8, 0.92)
    order1 = order_repository.create("S-001", "고객A", 100)
    order2 = order_repository.create("S-001", "고객B", 50)

    first_instance = ProductionService(order_repository, sample_repository, store=queue_store)
    first_instance.enqueue(order1.order_id, "S-001", "A", 100, 100, 109, 10.0, now_fn=lambda: fixed_now)
    first_instance.enqueue(order2.order_id, "S-001", "A", 50, 50, 55, 5.0, now_fn=lambda: fixed_now)

    restored = ProductionService(order_repository, sample_repository, store=queue_store)
    current = restored.current_item(now_fn=lambda: fixed_now)
    assert current.item.order_id == order1.order_id
    assert current.item.started_at == fixed_now
    pending = restored.pending_queue(now_fn=lambda: fixed_now)
    assert [p.item.order_id for p in pending] == [order2.order_id]


def test_store_none_keeps_in_memory_only_behavior(sample_repository, order_repository, fixed_now):
    service = ProductionService(order_repository, sample_repository)
    order = order_repository.create("S-001", "고객A", 200)
    service.enqueue(order.order_id, "S-001", "A", 200, 170, 185, 148.0, now_fn=lambda: fixed_now)
    assert service.queue_length() == 1

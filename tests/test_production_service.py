from datetime import datetime, timezone

import pytest

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

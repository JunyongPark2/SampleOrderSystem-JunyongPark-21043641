import math

from sampleorder.models import Order, OrderStatus
from sampleorder.services.calculations import (
    STOCK_DEPLETED,
    STOCK_SHORTAGE,
    STOCK_SUFFICIENT,
    actual_yield,
    pending_demand,
    shortage,
    stock_status,
    total_production_time,
)


def test_shortage_is_zero_when_stock_covers_quantity():
    assert shortage(quantity=100, stock=150) == 0
    assert shortage(quantity=100, stock=100) == 0


def test_shortage_is_positive_when_stock_insufficient():
    assert shortage(quantity=200, stock=30) == 170


def test_actual_yield_is_zero_when_no_shortage():
    assert actual_yield(0, 0.92) == 0


def test_actual_yield_equals_shortage_when_yield_rate_is_one():
    assert actual_yield(170, 1.0) == 170


def test_actual_yield_rounds_up_on_fraction():
    assert actual_yield(170, 0.92) == math.ceil(170 / 0.92)


def test_total_production_time_multiplies():
    assert total_production_time(0.8, 185) == 0.8 * 185


def _order(sample_id, quantity, status):
    return Order(
        order_id="ORD-1",
        sample_id=sample_id,
        customer_name="고객",
        quantity=quantity,
        created_at="2026-04-16T00:00:00Z",
        status=status,
    )


def test_pending_demand_excludes_rejected_and_release():
    orders = [
        _order("S-001", 10, OrderStatus.RESERVED),
        _order("S-001", 20, OrderStatus.PRODUCING),
        _order("S-001", 30, OrderStatus.CONFIRMED),
        _order("S-001", 999, OrderStatus.REJECTED),
        _order("S-001", 999, OrderStatus.RELEASE),
        _order("S-002", 999, OrderStatus.RESERVED),
    ]
    assert pending_demand(orders, "S-001") == 60


def test_stock_status_depleted_when_stock_non_positive():
    assert stock_status(stock=0, pending_demand_qty=10) == STOCK_DEPLETED
    assert stock_status(stock=-1, pending_demand_qty=0) == STOCK_DEPLETED


def test_stock_status_shortage_when_stock_below_demand():
    assert stock_status(stock=9, pending_demand_qty=10) == STOCK_SHORTAGE


def test_stock_status_sufficient_when_stock_meets_demand():
    assert stock_status(stock=10, pending_demand_qty=10) == STOCK_SUFFICIENT

from sampleorder.exceptions import DuplicateError, NotFoundError, ValidationError
from sampleorder.models import Order, OrderStatus, Sample


def test_sample_default_stock_is_zero():
    sample = Sample(sample_id="S-001", name="시료", avg_production_time=0.5, yield_rate=0.9)
    assert sample.stock == 0


def test_order_default_status_is_reserved():
    order = Order(
        order_id="ORD-20260416-0001",
        sample_id="S-001",
        customer_name="고객",
        quantity=10,
        created_at="2026-04-16T00:00:00Z",
    )
    assert order.status == OrderStatus.RESERVED


def test_order_status_has_exactly_five_values():
    assert {s.value for s in OrderStatus} == {
        "RESERVED",
        "REJECTED",
        "PRODUCING",
        "CONFIRMED",
        "RELEASE",
    }


def test_not_found_error_message_contains_entity_info():
    error = NotFoundError("Sample", "S-999")
    assert "Sample" in str(error)
    assert "S-999" in str(error)


def test_duplicate_error_message_contains_entity_info():
    error = DuplicateError("Order", "ORD-20260416-0001")
    assert "Order" in str(error)
    assert "ORD-20260416-0001" in str(error)


def test_validation_error_message():
    error = ValidationError("수율은 0 초과 1 이하 값이어야 합니다.")
    assert "수율" in str(error)

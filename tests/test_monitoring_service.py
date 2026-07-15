import pytest

from sampleorder.models import OrderStatus
from sampleorder.services.calculations import STOCK_DEPLETED, STOCK_SHORTAGE, STOCK_SUFFICIENT
from sampleorder.services.monitoring_service import MonitoringService


@pytest.fixture
def monitoring_service(order_repository, sample_repository):
    return MonitoringService(order_repository, sample_repository)


def test_order_status_counts_excludes_rejected(monitoring_service, sample_repository, order_repository):
    sample_repository.create("A", 0.5, 0.9)
    sample_repository.update("S-001", stock=100)
    o1 = order_repository.create("S-001", "고객A", 10)
    o2 = order_repository.create("S-001", "고객B", 20)
    o3 = order_repository.create("S-001", "고객C", 30)
    order_repository.update(o2.order_id, status=OrderStatus.REJECTED)
    order_repository.update(o3.order_id, status=OrderStatus.CONFIRMED)

    counts = monitoring_service.order_status_counts()

    assert counts[OrderStatus.RESERVED] == 1
    assert counts[OrderStatus.CONFIRMED] == 1
    assert counts[OrderStatus.PRODUCING] == 0
    assert counts[OrderStatus.RELEASE] == 0
    assert OrderStatus.REJECTED not in counts


def test_stock_report_classifies_depleted_shortage_sufficient(
    monitoring_service, sample_repository, order_repository
):
    sample_repository.create("고갈시료", 0.5, 0.9)  # S-001, stock=0
    sample_repository.create("부족시료", 0.5, 0.9)  # S-002
    sample_repository.update("S-002", stock=5)
    sample_repository.create("여유시료", 0.5, 0.9)  # S-003
    sample_repository.update("S-003", stock=100)

    order_repository.create("S-002", "고객A", 10)  # pending demand 10 > stock 5
    order_repository.create("S-003", "고객A", 10)  # pending demand 10 <= stock 100

    report = {row.sample_id: row for row in monitoring_service.stock_report()}

    assert report["S-001"].status == STOCK_DEPLETED
    assert report["S-002"].status == STOCK_SHORTAGE
    assert report["S-003"].status == STOCK_SUFFICIENT


def test_stock_report_pending_demand_excludes_rejected_and_release(
    monitoring_service, sample_repository, order_repository
):
    sample_repository.create("A", 0.5, 0.9)
    sample_repository.update("S-001", stock=5)
    rejected = order_repository.create("S-001", "고객A", 999)
    order_repository.update(rejected.order_id, status=OrderStatus.REJECTED)
    released = order_repository.create("S-001", "고객B", 999)
    order_repository.update(released.order_id, status=OrderStatus.RELEASE)

    report = {row.sample_id: row for row in monitoring_service.stock_report()}

    assert report["S-001"].status == STOCK_SUFFICIENT

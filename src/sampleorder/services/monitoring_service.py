from dataclasses import dataclass

from sampleorder.models import OrderStatus
from sampleorder.repositories.order_repository import OrderRepository
from sampleorder.repositories.sample_repository import SampleRepository
from sampleorder.services import calculations

_COUNTED_STATUSES = (
    OrderStatus.RESERVED,
    OrderStatus.CONFIRMED,
    OrderStatus.PRODUCING,
    OrderStatus.RELEASE,
)


@dataclass
class StockReportRow:
    sample_id: str
    name: str
    stock: int
    status: str


class MonitoringService:
    def __init__(self, order_repository: OrderRepository, sample_repository: SampleRepository):
        self._order_repo = order_repository
        self._sample_repo = sample_repository

    def order_status_counts(self) -> dict:
        orders = self._order_repo.list_all()
        return {
            status: sum(1 for order in orders if order.status == status)
            for status in _COUNTED_STATUSES
        }

    def stock_report(self) -> list:
        orders = self._order_repo.list_all()
        rows = []
        for sample in self._sample_repo.list_all():
            demand = calculations.pending_demand(orders, sample.sample_id)
            status = calculations.stock_status(sample.stock, demand)
            rows.append(
                StockReportRow(
                    sample_id=sample.sample_id,
                    name=sample.name,
                    stock=sample.stock,
                    status=status,
                )
            )
        return rows

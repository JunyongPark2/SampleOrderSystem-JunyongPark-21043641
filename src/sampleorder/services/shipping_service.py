from dataclasses import dataclass
from datetime import datetime

from sampleorder.clock import utc_now
from sampleorder.exceptions import InsufficientStockError
from sampleorder.models import Order, OrderStatus
from sampleorder.repositories.order_repository import OrderRepository
from sampleorder.repositories.sample_repository import SampleRepository

INSUFFICIENT_STOCK_ERROR = "재고가 부족하여 출고할 수 없습니다. 재고를 확인해주세요."


@dataclass
class ReleaseResult:
    order: Order
    processed_at: datetime


class ShippingService:
    def __init__(self, order_repository: OrderRepository, sample_repository: SampleRepository):
        self._order_repo = order_repository
        self._sample_repo = sample_repository

    def list_confirmed_orders(self) -> list:
        return self._order_repo.list_by_status(OrderStatus.CONFIRMED)

    def release(self, order_id: str, now_fn=utc_now) -> ReleaseResult:
        order = self._order_repo.get(order_id)
        sample = self._sample_repo.get(order.sample_id)
        if sample.stock < order.quantity:
            raise InsufficientStockError(INSUFFICIENT_STOCK_ERROR)
        self._sample_repo.update(order.sample_id, stock=sample.stock - order.quantity)
        updated_order = self._order_repo.update(order_id, status=OrderStatus.RELEASE)
        return ReleaseResult(order=updated_order, processed_at=now_fn())

    def sample_name_map(self, orders: list) -> dict:
        return {order.sample_id: self._sample_repo.get(order.sample_id).name for order in orders}

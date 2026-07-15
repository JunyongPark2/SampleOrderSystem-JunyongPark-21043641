from dataclasses import dataclass
from typing import Optional

from sampleorder.clock import utc_now
from sampleorder.exceptions import NotFoundError, ValidationError
from sampleorder.models import Order, OrderStatus, Sample
from sampleorder.repositories.order_repository import OrderRepository
from sampleorder.repositories.sample_repository import SampleRepository
from sampleorder.services import calculations
from sampleorder.services.production_service import ProductionService
from sampleorder.services.sample_lookup import sample_name_map
from sampleorder.services.validation import validate_int

SAMPLE_NOT_FOUND_ERROR = "존재하지 않는 시료 ID입니다. 주문을 생성하지 않았습니다."
QUANTITY_ERROR = "주문 수량은 1 이상의 정수여야 합니다. 다시 입력해주세요."

APPROVAL_SUFFICIENT = "SUFFICIENT"
APPROVAL_SHORTAGE = "SHORTAGE"


@dataclass
class ApprovalPreview:
    kind: str
    order: Order
    sample: Sample
    shortage_qty: int
    actual_yield_qty: int
    total_time: float


class OrderService:
    def __init__(
        self,
        order_repository: OrderRepository,
        sample_repository: SampleRepository,
        production_service: Optional[ProductionService] = None,
    ):
        self._order_repo = order_repository
        self._sample_repo = sample_repository
        self._production_service = production_service

    def validate_sample_id(self, sample_id: str) -> Sample:
        try:
            return self._sample_repo.get(sample_id)
        except NotFoundError:
            raise ValidationError(SAMPLE_NOT_FOUND_ERROR)

    def validate_quantity(self, quantity) -> int:
        return validate_int(quantity, 1, QUANTITY_ERROR)

    def create_order(self, sample_id: str, customer_name: str, quantity: int) -> Order:
        self.validate_sample_id(sample_id)
        self.validate_quantity(quantity)
        return self._order_repo.create(sample_id, customer_name, quantity)

    def list_reserved_orders(self) -> list:
        return self._order_repo.list_by_status(OrderStatus.RESERVED)

    def list_all_orders(self) -> list:
        return self._order_repo.list_all()

    def preview_approval(self, order_id: str) -> ApprovalPreview:
        order = self._order_repo.get(order_id)
        sample = self._sample_repo.get(order.sample_id)
        other_orders = [o for o in self._order_repo.list_all() if o.order_id != order_id]
        reserved = calculations.reserved_qty(other_orders, order.sample_id)
        available = calculations.available_stock(sample.stock, reserved)
        shortage_qty = calculations.shortage(order.quantity, available)
        if shortage_qty <= 0:
            return ApprovalPreview(
                kind=APPROVAL_SUFFICIENT,
                order=order,
                sample=sample,
                shortage_qty=0,
                actual_yield_qty=0,
                total_time=0.0,
            )
        actual_yield_qty = calculations.actual_yield(shortage_qty, sample.yield_rate)
        total_time = calculations.total_production_time(sample.avg_production_time, actual_yield_qty)
        return ApprovalPreview(
            kind=APPROVAL_SHORTAGE,
            order=order,
            sample=sample,
            shortage_qty=shortage_qty,
            actual_yield_qty=actual_yield_qty,
            total_time=total_time,
        )

    def confirm_approval(self, order_id: str, preview: ApprovalPreview, now_fn=utc_now) -> Order:
        if preview.kind == APPROVAL_SUFFICIENT:
            return self._order_repo.update(order_id, status=OrderStatus.CONFIRMED)

        self._order_repo.update(order_id, status=OrderStatus.PRODUCING)
        self._production_service.enqueue(
            order_id=order_id,
            sample_id=preview.sample.sample_id,
            sample_name=preview.sample.name,
            quantity=preview.order.quantity,
            shortage_qty=preview.shortage_qty,
            actual_yield_qty=preview.actual_yield_qty,
            total_time=preview.total_time,
            now_fn=now_fn,
        )
        return self._order_repo.get(order_id)

    def reject_order(self, order_id: str) -> Order:
        return self._order_repo.update(order_id, status=OrderStatus.REJECTED)

    def sample_name_map(self, orders: list) -> dict:
        return sample_name_map(orders, self._sample_repo)

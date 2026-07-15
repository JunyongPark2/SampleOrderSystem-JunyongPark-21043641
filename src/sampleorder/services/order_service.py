from sampleorder.exceptions import NotFoundError, ValidationError
from sampleorder.models import Order, Sample
from sampleorder.repositories.order_repository import OrderRepository
from sampleorder.repositories.sample_repository import SampleRepository

SAMPLE_NOT_FOUND_ERROR = "존재하지 않는 시료 ID입니다. 주문을 생성하지 않았습니다."
QUANTITY_ERROR = "주문 수량은 1 이상의 정수여야 합니다. 다시 입력해주세요."


class OrderService:
    def __init__(self, order_repository: OrderRepository, sample_repository: SampleRepository):
        self._order_repo = order_repository
        self._sample_repo = sample_repository

    def validate_sample_id(self, sample_id: str) -> Sample:
        try:
            return self._sample_repo.get(sample_id)
        except NotFoundError:
            raise ValidationError(SAMPLE_NOT_FOUND_ERROR)

    def validate_quantity(self, quantity) -> int:
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
            raise ValidationError(QUANTITY_ERROR)
        return quantity

    def create_order(self, sample_id: str, customer_name: str, quantity: int) -> Order:
        self.validate_sample_id(sample_id)
        self.validate_quantity(quantity)
        return self._order_repo.create(sample_id, customer_name, quantity)

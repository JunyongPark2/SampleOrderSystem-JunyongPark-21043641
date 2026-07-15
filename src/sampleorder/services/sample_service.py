from sampleorder.exceptions import ValidationError
from sampleorder.models import Sample
from sampleorder.repositories.sample_repository import SampleRepository

AVG_PRODUCTION_TIME_ERROR = "평균 생산시간은 0보다 커야 합니다. 다시 입력해주세요."
YIELD_RATE_ERROR = "수율은 0 초과 1 이하 값이어야 합니다. 다시 입력해주세요."
STOCK_ERROR = "재고는 0 이상의 정수여야 합니다. 다시 입력해주세요."


class SampleService:
    def __init__(self, repository: SampleRepository):
        self._repo = repository

    def validate_avg_production_time(self, avg_production_time: float) -> float:
        if avg_production_time <= 0:
            raise ValidationError(AVG_PRODUCTION_TIME_ERROR)
        return avg_production_time

    def validate_yield_rate(self, yield_rate: float) -> float:
        if not (0 < yield_rate <= 1):
            raise ValidationError(YIELD_RATE_ERROR)
        return yield_rate

    def validate_stock(self, stock) -> int:
        if not isinstance(stock, int) or isinstance(stock, bool) or stock < 0:
            raise ValidationError(STOCK_ERROR)
        return stock

    def register(
        self, name: str, avg_production_time: float, yield_rate: float, stock: int = 0
    ) -> Sample:
        self.validate_avg_production_time(avg_production_time)
        self.validate_yield_rate(yield_rate)
        self.validate_stock(stock)
        return self._repo.create(name, avg_production_time, yield_rate, stock=stock)

    def list_all(self) -> list:
        return self._repo.list_all()

    def search(self, keyword: str) -> list:
        return self._repo.search(keyword)

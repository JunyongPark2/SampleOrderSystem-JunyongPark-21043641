import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sampleorder.json_store import JsonFileStore
from sampleorder.models import OrderStatus
from sampleorder.repositories.order_repository import OrderRepository
from sampleorder.repositories.sample_repository import SampleRepository

DATA_DIR = Path(__file__).parent.parent / "data"

SAMPLE_POOL = [
    ("실리콘 웨이퍼-8인치", 0.5, 0.92),
    ("GaN 에피택셜-4인치", 0.3, 0.78),
    ("SiC 파워기판-6인치", 0.8, 0.92),
    ("산화막 웨이퍼-SiO2", 0.4, 0.85),
    ("포토레지스트-PR7", 0.6, 0.88),
    ("질화막 웨이퍼-Si3N4", 0.45, 0.9),
    ("GaAs 에피택셜-3인치", 0.35, 0.75),
    ("InP 기판-2인치", 0.7, 0.8),
    ("사파이어 기판-4인치", 0.9, 0.83),
    ("석영 웨이퍼-6인치", 0.55, 0.87),
    ("도핑 웨이퍼-p형", 0.5, 0.91),
    ("도핑 웨이퍼-n형", 0.5, 0.91),
]

CUSTOMER_POOL = [
    "삼성전자 파운드리",
    "SK하이닉스",
    "LG이노텍",
    "DB하이텍",
    "매그나칩반도체",
    "네패스",
    "한양대학교 연구실",
    "서울대학교 반도체공동연구소",
]

ORDER_STATUS_WEIGHTS = [
    (OrderStatus.RESERVED, 0.15),
    (OrderStatus.CONFIRMED, 0.2),
    (OrderStatus.PRODUCING, 0.15),
    (OrderStatus.RELEASE, 0.4),
    (OrderStatus.REJECTED, 0.1),
]


class DummyDataGenerator:
    SAMPLE_POOL = SAMPLE_POOL
    CUSTOMER_POOL = CUSTOMER_POOL
    ORDER_STATUS_WEIGHTS = ORDER_STATUS_WEIGHTS

    def __init__(
        self,
        sample_repo: SampleRepository,
        order_repo: OrderRepository,
        rng: random.Random = None,
    ):
        self._sample_repo = sample_repo
        self._order_repo = order_repo
        self._rng = rng or random.Random()

    def generate_samples(self, count: int) -> list:
        created = []
        for i in range(count):
            name, avg_time, yield_rate = self.SAMPLE_POOL[i % len(self.SAMPLE_POOL)]
            if i >= len(self.SAMPLE_POOL):
                name = f"{name} #{i + 1}"
            sample = self._sample_repo.create(name, avg_time, yield_rate)
            stock = self._rng.randint(0, 500)
            sample = self._sample_repo.update(sample.sample_id, stock=stock)
            created.append(sample)
        return created

    def _weighted_status(self) -> OrderStatus:
        roll = self._rng.random()
        cumulative = 0.0
        for status, weight in self.ORDER_STATUS_WEIGHTS:
            cumulative += weight
            if roll <= cumulative:
                return status
        return self.ORDER_STATUS_WEIGHTS[-1][0]

    def generate_orders(self, count: int, within_days: int = 30) -> list:
        samples = self._sample_repo.list_all()
        created = []
        for _ in range(count):
            sample = self._rng.choice(samples)
            customer = self._rng.choice(self.CUSTOMER_POOL)
            quantity = self._rng.randint(10, 300)
            order = self._order_repo.create(sample.sample_id, customer, quantity)
            status = self._weighted_status()
            if status != OrderStatus.RESERVED:
                order = self._order_repo.update(order.order_id, status=status)
            created.append(order)
        return created

    def generate(self, sample_count: int, order_count: int) -> None:
        self.generate_samples(sample_count)
        self.generate_orders(order_count)


def main() -> None:
    parser = argparse.ArgumentParser(description="더미 시료/주문 데이터 생성 도구")
    parser.add_argument("--samples", type=int, default=12, help="생성할 시료 종수")
    parser.add_argument("--orders", type=int, default=36, help="생성할 주문 건수")
    parser.add_argument("--seed", type=int, default=None, help="난수 시드(재현 가능한 데이터 생성용)")
    args = parser.parse_args()

    sample_repo = SampleRepository(JsonFileStore(DATA_DIR / "samples.json"))
    order_repo = OrderRepository(JsonFileStore(DATA_DIR / "orders.json"))
    generator = DummyDataGenerator(sample_repo, order_repo, rng=random.Random(args.seed))
    generator.generate(args.samples, args.orders)

    print(f"더미 데이터 생성 완료: 시료 {args.samples}종, 주문 {args.orders}건")


if __name__ == "__main__":
    main()

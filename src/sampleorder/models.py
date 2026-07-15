from dataclasses import dataclass
from enum import Enum


class OrderStatus(Enum):
    RESERVED = "RESERVED"
    REJECTED = "REJECTED"
    PRODUCING = "PRODUCING"
    CONFIRMED = "CONFIRMED"
    RELEASE = "RELEASE"


@dataclass
class Sample:
    sample_id: str
    name: str
    avg_production_time: float
    yield_rate: float
    stock: int = 0


@dataclass
class Order:
    order_id: str
    sample_id: str
    customer_name: str
    quantity: int
    created_at: str
    status: OrderStatus = OrderStatus.RESERVED

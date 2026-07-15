import math

from sampleorder.models import Order, OrderStatus

_PENDING_STATUSES = {OrderStatus.RESERVED, OrderStatus.PRODUCING, OrderStatus.CONFIRMED}
_RESERVED_STATUSES = {OrderStatus.CONFIRMED, OrderStatus.PRODUCING}

STOCK_DEPLETED = "고갈"
STOCK_SHORTAGE = "부족"
STOCK_SUFFICIENT = "여유"


def shortage(quantity: int, stock: int) -> int:
    return max(quantity - stock, 0)


def actual_yield(shortage_qty: int, yield_rate: float) -> int:
    if shortage_qty == 0:
        return 0
    return math.ceil(shortage_qty / yield_rate)


def total_production_time(avg_production_time: float, actual_yield_qty: int) -> float:
    return avg_production_time * actual_yield_qty


def pending_demand(orders: list, sample_id: str) -> int:
    return sum(
        order.quantity
        for order in orders
        if order.sample_id == sample_id and order.status in _PENDING_STATUSES
    )


def reserved_qty(orders: list, sample_id: str) -> int:
    return sum(
        order.quantity
        for order in orders
        if order.sample_id == sample_id and order.status in _RESERVED_STATUSES
    )


def available_stock(stock: int, reserved_qty: int) -> int:
    return max(stock - reserved_qty, 0)


def stock_status(stock: int, pending_demand_qty: int) -> str:
    if stock <= 0:
        return STOCK_DEPLETED
    if stock < pending_demand_qty:
        return STOCK_SHORTAGE
    return STOCK_SUFFICIENT

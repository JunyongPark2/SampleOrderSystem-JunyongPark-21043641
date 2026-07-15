from collections import deque
from dataclasses import dataclass
from datetime import datetime

from sampleorder.clock import utc_now


@dataclass
class QueueItem:
    order_id: str
    sample_id: str
    sample_name: str
    quantity: int
    shortage_qty: int
    actual_yield_qty: int
    total_time: float
    started_at: datetime


class ProductionService:
    def __init__(self, order_repository, sample_repository):
        self._order_repo = order_repository
        self._sample_repo = sample_repository
        self._queue = deque()

    def queue_length(self) -> int:
        return len(self._queue)

    def enqueue(
        self,
        order_id: str,
        sample_id: str,
        sample_name: str,
        quantity: int,
        shortage_qty: int,
        actual_yield_qty: int,
        total_time: float,
        now_fn=utc_now,
    ) -> QueueItem:
        is_first = len(self._queue) == 0
        item = QueueItem(
            order_id=order_id,
            sample_id=sample_id,
            sample_name=sample_name,
            quantity=quantity,
            shortage_qty=shortage_qty,
            actual_yield_qty=actual_yield_qty,
            total_time=total_time,
            started_at=now_fn() if is_first else None,
        )
        self._queue.append(item)
        return item

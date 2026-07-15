from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta

from sampleorder.clock import utc_now
from sampleorder.models import OrderStatus


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


@dataclass
class CurrentItem:
    item: QueueItem
    progress: float
    eta: datetime


@dataclass
class PendingItem:
    item: QueueItem
    expected_completion: datetime


def _item_to_dict(item: QueueItem) -> dict:
    return {
        "order_id": item.order_id,
        "sample_id": item.sample_id,
        "sample_name": item.sample_name,
        "quantity": item.quantity,
        "shortage_qty": item.shortage_qty,
        "actual_yield_qty": item.actual_yield_qty,
        "total_time": item.total_time,
        "started_at": item.started_at.isoformat() if item.started_at else None,
    }


def _dict_to_item(record: dict) -> QueueItem:
    return QueueItem(
        order_id=record["order_id"],
        sample_id=record["sample_id"],
        sample_name=record["sample_name"],
        quantity=record["quantity"],
        shortage_qty=record["shortage_qty"],
        actual_yield_qty=record["actual_yield_qty"],
        total_time=record["total_time"],
        started_at=datetime.fromisoformat(record["started_at"]) if record["started_at"] else None,
    )


class ProductionService:
    def __init__(self, order_repository, sample_repository, store=None):
        self._order_repo = order_repository
        self._sample_repo = sample_repository
        self._store = store
        if store is not None:
            self._queue = deque(_dict_to_item(record) for record in store.load())
        else:
            self._queue = deque()

    def _persist(self) -> None:
        if self._store is not None:
            self._store.save([_item_to_dict(item) for item in self._queue])

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
        self._persist()
        return item

    def _elapsed_minutes(self, item: QueueItem, now: datetime) -> float:
        return (now - item.started_at).total_seconds() / 60

    def advance(self, now_fn=utc_now) -> None:
        now = now_fn()
        changed = False
        while self._queue and self._elapsed_minutes(self._queue[0], now) >= self._queue[0].total_time:
            item = self._queue.popleft()
            sample = self._sample_repo.get(item.sample_id)
            self._sample_repo.update(item.sample_id, stock=sample.stock + item.actual_yield_qty)
            self._order_repo.update(item.order_id, status=OrderStatus.CONFIRMED)
            if self._queue:
                self._queue[0].started_at = item.started_at + timedelta(minutes=item.total_time)
            changed = True
        if changed:
            self._persist()

    def current_item(self, now_fn=utc_now):
        if not self._queue:
            return None
        head = self._queue[0]
        now = now_fn()
        if head.total_time <= 0:
            progress = 1.0
        else:
            progress = min(1.0, self._elapsed_minutes(head, now) / head.total_time)
        eta = head.started_at + timedelta(minutes=head.total_time)
        return CurrentItem(item=head, progress=progress, eta=eta)

    def pending_queue(self, now_fn=utc_now) -> list:
        if len(self._queue) <= 1:
            return []
        current = self.current_item(now_fn)
        cumulative = current.eta
        results = []
        for item in list(self._queue)[1:]:
            cumulative = cumulative + timedelta(minutes=item.total_time)
            results.append(PendingItem(item=item, expected_completion=cumulative))
        return results

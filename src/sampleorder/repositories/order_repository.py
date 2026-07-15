from datetime import datetime, timezone

from sampleorder.exceptions import NotFoundError
from sampleorder.json_store import JsonFileStore
from sampleorder.models import Order, OrderStatus


def _to_dict(order: Order) -> dict:
    return {
        "order_id": order.order_id,
        "sample_id": order.sample_id,
        "customer_name": order.customer_name,
        "quantity": order.quantity,
        "created_at": order.created_at,
        "status": order.status.value,
    }


def _to_order(record: dict) -> Order:
    return Order(
        order_id=record["order_id"],
        sample_id=record["sample_id"],
        customer_name=record["customer_name"],
        quantity=record["quantity"],
        created_at=record["created_at"],
        status=OrderStatus(record["status"]),
    )


class OrderRepository:
    def __init__(self, store: JsonFileStore, now_fn=lambda: datetime.now(timezone.utc)):
        self._store = store
        self._now_fn = now_fn

    def _next_id(self, records: list, date_str: str) -> str:
        prefix = f"ORD-{date_str}-"
        max_seq = 0
        for record in records:
            order_id = record["order_id"]
            if order_id.startswith(prefix):
                seq = int(order_id[len(prefix) :])
                max_seq = max(max_seq, seq)
        return f"{prefix}{max_seq + 1:04d}"

    def create(self, sample_id: str, customer_name: str, quantity: int) -> Order:
        records = self._store.load()
        now = self._now_fn()
        date_str = now.strftime("%Y%m%d")
        order = Order(
            order_id=self._next_id(records, date_str),
            sample_id=sample_id,
            customer_name=customer_name,
            quantity=quantity,
            created_at=now.isoformat(),
            status=OrderStatus.RESERVED,
        )
        records.append(_to_dict(order))
        self._store.save(records)
        return order

    def get(self, order_id: str) -> Order:
        for record in self._store.load():
            if record["order_id"] == order_id:
                return _to_order(record)
        raise NotFoundError("Order", order_id)

    def list_all(self) -> list:
        return [_to_order(record) for record in self._store.load()]

    def list_by_status(self, status: OrderStatus) -> list:
        return [order for order in self.list_all() if order.status == status]

    def update(self, order_id: str, **fields) -> Order:
        records = self._store.load()
        for record in records:
            if record["order_id"] == order_id:
                if "status" in fields and isinstance(fields["status"], OrderStatus):
                    fields = {**fields, "status": fields["status"].value}
                record.update(fields)
                self._store.save(records)
                return _to_order(record)
        raise NotFoundError("Order", order_id)

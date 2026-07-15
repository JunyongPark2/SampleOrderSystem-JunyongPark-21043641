from sampleorder.models import Order
from sampleorder.services.order_service import ApprovalPreview
from sampleorder.views.formatting import INVALID_CHOICE_MESSAGE, ljust, rjust

NO_PENDING_ORDERS_MESSAGE = "승인 대기 중인 주문이 없습니다."


class ApprovalView:
    def show_reserved_table(self, orders: list, sample_names: dict) -> None:
        print("승인 대기 중인 예약 목록 (RESERVED)")
        header = (
            ljust("번호", 6)
            + ljust("주문번호", 20)
            + ljust("고객", 18)
            + ljust("시료", 24)
            + rjust("수량", 10)
            + ljust("  상태", 12)
        )
        print(header)
        for idx, order in enumerate(orders, start=1):
            row = (
                ljust(f"[{idx}]", 6)
                + ljust(order.order_id, 20)
                + ljust(order.customer_name, 18)
                + ljust(sample_names[order.sample_id], 24)
                + rjust(f"{order.quantity} ea", 10)
                + ljust(f"  {order.status.value}", 12)
            )
            print(row)

    def show_no_pending_orders(self) -> None:
        print(NO_PENDING_ORDERS_MESSAGE)

    def prompt_order_choice(self) -> str:
        return input("승인/거절할 번호 > ").strip()

    def show_invalid_choice(self) -> None:
        print(INVALID_CHOICE_MESSAGE)

    def prompt_approve_or_reject(self) -> str:
        while True:
            choice = input("[Y] 승인   [N] 거절\n선택 > ").strip().upper()
            if choice in ("Y", "N"):
                return choice
            self.show_invalid_choice()

    def show_shortage_preview(self, preview: ApprovalPreview) -> None:
        print("재고 확인 중...")
        print(f" 시료      {preview.sample.name}   현재 재고  {preview.sample.stock} ea")
        print(
            f" 주문 수량 {preview.order.quantity} ea               "
            f"부족분     {preview.shortage_qty} ea  ← 이 수량만 생산"
        )
        print()
        print(
            f"재고 부족. 부족분 {preview.shortage_qty} ea 승인하시겠습니까? "
            f"(실생산량 {preview.actual_yield_qty} ea / {preview.total_time:g} min)"
        )
        print()

    def prompt_shortage_confirm(self) -> str:
        while True:
            choice = input("[Y] 승인   [N] 주문 거절\n선택 > ").strip().upper()
            if choice in ("Y", "N"):
                return choice
            self.show_invalid_choice()

    def show_approval_result(self, order: Order, previous_status: str) -> None:
        print("승인 완료.")
        print(f" 상태 변경   {previous_status} → {order.status.value}")
        print(f" 주문번호    {order.order_id}")

    def show_rejection_result(self, order: Order) -> None:
        print("거절 처리 완료.")
        print(f" 상태 변경   RESERVED → {order.status.value}")
        print(f" 주문번호    {order.order_id}")

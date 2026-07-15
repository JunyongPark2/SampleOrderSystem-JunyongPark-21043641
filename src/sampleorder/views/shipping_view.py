from sampleorder.services.shipping_service import ReleaseResult
from sampleorder.views.formatting import INVALID_CHOICE_MESSAGE, ljust, rjust

NO_SHIPPABLE_ORDERS_MESSAGE = "출고 가능한 주문이 없습니다."


class ShippingView:
    def show_confirmed_table(self, orders: list, sample_names: dict) -> None:
        print("출고 가능 주문 (CONFIRMED)")
        header = (
            ljust("번호", 6)
            + ljust("주문번호", 20)
            + ljust("고객", 18)
            + ljust("시료", 22)
            + rjust("수량", 10)
        )
        print(header)
        for idx, order in enumerate(orders, start=1):
            row = (
                ljust(f"[{idx}]", 6)
                + ljust(order.order_id, 20)
                + ljust(order.customer_name, 18)
                + ljust(sample_names[order.sample_id], 22)
                + rjust(f"{order.quantity} ea", 10)
            )
            print(row)

    def show_no_shippable_orders(self) -> None:
        print(NO_SHIPPABLE_ORDERS_MESSAGE)

    def prompt_order_choice(self) -> str:
        return input("출고할 번호 > ").strip()

    def show_invalid_choice(self) -> None:
        print(INVALID_CHOICE_MESSAGE)

    def show_insufficient_stock_error(self, message: str) -> None:
        print(message)

    def show_release_result(self, result: ReleaseResult) -> None:
        print("출고 처리 완료.")
        print(f" 주문번호   {result.order.order_id}")
        print(f" 출고수량   {result.order.quantity} ea")
        print(f" 처리일시   {result.processed_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f" 상태       CONFIRMED → {result.order.status.value}")

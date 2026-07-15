from sampleorder.models import Order, Sample

INVALID_CHOICE_MESSAGE = "잘못된 입력입니다. 다시 선택해주세요."


class OrderView:
    def show_menu_title(self) -> None:
        print("[2] 시료 주문")
        print("------------------------------------------------")

    def prompt_sample_id(self) -> str:
        return input("시료 ID   > ").strip()

    def show_error(self, message: str) -> None:
        print(message)

    def prompt_customer_name(self) -> str:
        return input("고객명    > ").strip()

    def prompt_quantity(self) -> str:
        return input("주문 수량 > ").strip()

    def confirm_order(self, sample: Sample, customer_name: str, quantity: int) -> bool:
        print()
        print("입력 내용 확인")
        print(f" 시료   {sample.name} ({sample.sample_id})")
        print(f" 고객   {customer_name}")
        print(f" 수량   {quantity} ea")
        print()
        while True:
            choice = input("[Y] 예약 접수   [N] 취소\n선택 > ").strip().upper()
            if choice in ("Y", "N"):
                return choice == "Y"
            print(INVALID_CHOICE_MESSAGE)

    def show_intake_result(self, order: Order) -> None:
        print()
        print("예약 접수 완료.")
        print(f" 주문번호  {order.order_id}")
        print(f" 현재 상태 {order.status.value}")

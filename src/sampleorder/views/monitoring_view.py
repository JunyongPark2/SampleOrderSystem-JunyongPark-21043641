from sampleorder.views.formatting import INVALID_CHOICE_MESSAGE, ljust, rjust


class MonitoringView:
    def show_menu(self) -> None:
        print("[4] 모니터링")
        print("------------------------------------------------")
        print(" [1] 주문량 확인   [2] 재고량 확인   [0] 뒤로")

    def prompt_menu_choice(self) -> str:
        return input(" 선택 > ").strip()

    def show_invalid_choice(self) -> None:
        print(INVALID_CHOICE_MESSAGE)

    def show_order_status_counts(self, counts: dict) -> None:
        print("상태별 주문 현황")
        for status, count in counts.items():
            print(f" {ljust(status.value, 11)} {count}건")

    def show_stock_report(self, rows: list) -> None:
        print("재고 현황")
        header = ljust("시료명", 22) + rjust("재고", 10) + ljust("  상태", 8)
        print(header)
        for row in rows:
            print(ljust(row.name, 22) + rjust(f"{row.stock} ea", 10) + ljust(f"  {row.status}", 8))

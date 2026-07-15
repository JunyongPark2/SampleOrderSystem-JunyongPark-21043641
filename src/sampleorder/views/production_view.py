from sampleorder.views.formatting import ljust, rjust

NO_CURRENT_ITEM_MESSAGE = "생산라인 대기 중인 주문이 없습니다."
PROGRESS_BAR_WIDTH = 10


def _progress_bar(progress: float) -> str:
    filled = round(progress * PROGRESS_BAR_WIDTH)
    return "█" * filled + "░" * (PROGRESS_BAR_WIDTH - filled)


class ProductionView:
    def show_title(self) -> None:
        print("[5] 생산라인 조회   FIFO 방식")
        print("------------------------------------------------")
        print("생산라인 1개 (단일 라인)   현재 상태: RUNNING")
        print()

    def show_no_current_item(self) -> None:
        print(NO_CURRENT_ITEM_MESSAGE)

    def show_current_item(self, current) -> None:
        item = current.item
        print("현재 처리 중")
        print(f" 주문번호  {item.order_id}   시료  {item.sample_name}")
        print(
            f" 주문량    {item.quantity} ea   "
            f"부족 {item.shortage_qty} ea → 실생산량 {item.actual_yield_qty} ea"
        )
        percent = round(current.progress * 100)
        eta_str = current.eta.strftime("%H:%M")
        print(
            f" 진행률    [{_progress_bar(current.progress)}] {percent}%   완료 예정 {eta_str}"
        )

    def show_pending_queue(self, pending: list) -> None:
        print()
        print("대기 중인 주문 (FIFO 순)")
        header = (
            ljust("순서", 6)
            + ljust("주문번호", 20)
            + ljust("시료", 22)
            + rjust("주문량", 10)
            + rjust("부족분", 10)
            + rjust("실생산량", 10)
            + ljust("  예상 완료", 12)
        )
        print(header)
        for idx, pending_item in enumerate(pending, start=1):
            item = pending_item.item
            row = (
                ljust(str(idx), 6)
                + ljust(item.order_id, 20)
                + ljust(item.sample_name, 22)
                + rjust(f"{item.quantity} ea", 10)
                + rjust(f"{item.shortage_qty} ea", 10)
                + rjust(f"{item.actual_yield_qty} ea", 10)
                + ljust(f"  {pending_item.expected_completion.strftime('%H:%M')}", 12)
            )
            print(row)
        print()
        print("* 부족분 = 주문량 - 재고,  실생산량 = ceil(부족분 / 수율)")
        print("* 선입선출(FIFO) 방식으로 처리됩니다.")

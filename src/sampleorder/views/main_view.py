from datetime import datetime

from sampleorder.services.monitoring_service import DashboardSummary
from sampleorder.views.formatting import INVALID_CHOICE_MESSAGE

NOT_IMPLEMENTED_MESSAGE = "아직 구현되지 않은 기능입니다."


class MainView:
    def show_main_menu(self, summary: DashboardSummary, now: datetime) -> None:
        print("================================================================")
        print("              반도체 시료 생산주문관리 시스템")
        print("================================================================")
        print(f" 시스템 현황   {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print(f" 등록 시료  {summary.sample_count}종     총 재고     {summary.total_stock:,} ea")
        print(f" 전체 주문  {summary.total_order_count}건     생산라인    {summary.production_queue_count}건 대기")
        print("----------------------------------------------------------------")
        print(" [1] 시료 관리        [2] 시료 주문")
        print(" [3] 주문 승인/거절    [4] 모니터링")
        print(" [5] 생산라인 조회     [6] 출고 처리")
        print(" [0] 종료")
        print("----------------------------------------------------------------")

    def prompt_menu_choice(self) -> str:
        return input(" 선택 > ").strip()

    def show_invalid_choice(self) -> None:
        print(INVALID_CHOICE_MESSAGE)

    def show_not_implemented(self) -> None:
        print(NOT_IMPLEMENTED_MESSAGE)

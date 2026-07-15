from sampleorder.models import Sample
from sampleorder.views.formatting import INVALID_CHOICE_MESSAGE, ljust, rjust

NO_SEARCH_RESULT_MESSAGE = "일치하는 시료가 없습니다."


class SampleView:
    def show_menu(self) -> None:
        print("[1] 시료 관리")
        print("------------------------------------------------")
        print(" [1] 시료 등록   [2] 시료 목록   [3] 시료 검색   [0] 뒤로")

    def prompt_menu_choice(self) -> str:
        return input(" 선택 > ").strip()

    def show_invalid_choice(self) -> None:
        print(INVALID_CHOICE_MESSAGE)

    def prompt_name(self) -> str:
        return input("시료명 > ").strip()

    def prompt_avg_production_time(self) -> str:
        return input("평균 생산시간(분) > ").strip()

    def prompt_yield_rate(self) -> str:
        return input("수율 > ").strip()

    def prompt_stock(self) -> str:
        return input("재고(ea) > ").strip()

    def show_validation_error(self, message: str) -> None:
        print(message)

    def show_registration_result(self, sample: Sample) -> None:
        print("등록 완료.")
        print(f" 시료 ID   {sample.sample_id}")
        print(f" 시료명    {sample.name}")
        print(f" 재고      {sample.stock} ea")

    def prompt_search_keyword(self) -> str:
        return input("검색어 > ").strip()

    def show_no_search_result(self) -> None:
        print(NO_SEARCH_RESULT_MESSAGE)

    def show_sample_table(self, samples: list, title: str) -> None:
        print(f"{title} (총 {len(samples)}종)")
        header = (
            ljust("ID", 8)
            + ljust("시료명", 20)
            + ljust("평균 생산시간", 16)
            + ljust("수율", 8)
            + rjust("현재 재고", 10)
        )
        print(header)
        for sample in samples:
            row = (
                ljust(sample.sample_id, 8)
                + ljust(sample.name, 20)
                + ljust(f"{sample.avg_production_time} min/ea", 16)
                + ljust(f"{sample.yield_rate}", 8)
                + rjust(f"{sample.stock} ea", 10)
            )
            print(row)

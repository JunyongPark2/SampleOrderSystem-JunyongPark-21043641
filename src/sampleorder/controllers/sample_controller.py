from sampleorder.controllers._prompting import prompt_until_valid
from sampleorder.services.sample_service import SampleService
from sampleorder.views.sample_view import SampleView

_NOT_A_NUMBER_MESSAGE = "숫자를 입력해주세요."


class SampleController:
    def __init__(self, service: SampleService, view: SampleView):
        self._service = service
        self._view = view

    def run(self) -> None:
        while True:
            self._view.show_menu()
            choice = self._view.prompt_menu_choice()
            if choice == "0":
                return
            elif choice == "1":
                self._register()
            elif choice == "2":
                self._list_all()
            elif choice == "3":
                self._search()
            else:
                self._view.show_invalid_choice()

    def _register(self) -> None:
        name = self._view.prompt_name()
        avg_production_time = self._prompt_avg_production_time()
        yield_rate = self._prompt_yield_rate()
        stock = self._prompt_stock()
        sample = self._service.register(name, avg_production_time, yield_rate, stock)
        self._view.show_registration_result(sample)

    def _prompt_avg_production_time(self) -> float:
        return prompt_until_valid(
            self._view.prompt_avg_production_time,
            float,
            self._service.validate_avg_production_time,
            self._view.show_validation_error,
            _NOT_A_NUMBER_MESSAGE,
        )

    def _prompt_yield_rate(self) -> float:
        return prompt_until_valid(
            self._view.prompt_yield_rate,
            float,
            self._service.validate_yield_rate,
            self._view.show_validation_error,
            _NOT_A_NUMBER_MESSAGE,
        )

    def _prompt_stock(self) -> int:
        return prompt_until_valid(
            self._view.prompt_stock,
            int,
            self._service.validate_stock,
            self._view.show_validation_error,
            _NOT_A_NUMBER_MESSAGE,
        )

    def _list_all(self) -> None:
        samples = self._service.list_all()
        self._view.show_sample_table(samples, "등록 시료 목록")

    def _search(self) -> None:
        keyword = self._view.prompt_search_keyword()
        results = self._service.search(keyword)
        if not results:
            self._view.show_no_search_result()
            return
        self._view.show_sample_table(results, "검색 결과")

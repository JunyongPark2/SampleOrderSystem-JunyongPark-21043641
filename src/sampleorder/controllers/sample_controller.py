from sampleorder.exceptions import ValidationError
from sampleorder.services.sample_service import SampleService
from sampleorder.views.sample_view import SampleView


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
        while True:
            raw = self._view.prompt_avg_production_time()
            try:
                value = float(raw)
                self._service.validate_avg_production_time(value)
                return value
            except (ValueError, ValidationError) as error:
                self._view.show_validation_error(self._error_message(error))

    def _prompt_yield_rate(self) -> float:
        while True:
            raw = self._view.prompt_yield_rate()
            try:
                value = float(raw)
                self._service.validate_yield_rate(value)
                return value
            except (ValueError, ValidationError) as error:
                self._view.show_validation_error(self._error_message(error))

    def _prompt_stock(self) -> int:
        while True:
            raw = self._view.prompt_stock()
            try:
                value = int(raw)
                self._service.validate_stock(value)
                return value
            except (ValueError, ValidationError) as error:
                self._view.show_validation_error(self._error_message(error))

    def _error_message(self, error: Exception) -> str:
        if isinstance(error, ValidationError):
            return error.message
        return "숫자를 입력해주세요."

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

import pytest

from sampleorder.controllers.sample_controller import SampleController
from sampleorder.services.sample_service import SampleService


class _ScriptedSampleView:
    def __init__(self, choices=(), fields=None):
        self._choices = iter(choices)
        self._fields = dict(fields or {})
        self.invalid_choice_shown = 0
        self.validation_errors = []
        self.registration_result = None
        self.tables_shown = []
        self.no_search_result_shown = 0

    def show_menu(self):
        pass

    def prompt_menu_choice(self):
        return next(self._choices)

    def show_invalid_choice(self):
        self.invalid_choice_shown += 1

    def prompt_name(self):
        return self._fields["name"]

    def prompt_avg_production_time(self):
        return next(self._fields["avg_production_time"])

    def prompt_yield_rate(self):
        return next(self._fields["yield_rate"])

    def prompt_stock(self):
        return next(self._fields["stock"])

    def show_validation_error(self, message):
        self.validation_errors.append(message)

    def show_registration_result(self, sample):
        self.registration_result = sample

    def prompt_search_keyword(self):
        return self._fields["keyword"]

    def show_no_search_result(self):
        self.no_search_result_shown += 1

    def show_sample_table(self, samples, title):
        self.tables_shown.append((samples, title))


@pytest.fixture
def sample_service(sample_repository):
    return SampleService(sample_repository)


def _controller(sample_service, choices=(), fields=None):
    view = _ScriptedSampleView(choices, fields)
    return SampleController(sample_service, view), view


def test_register_success(sample_service):
    fields = {
        "name": "A",
        "avg_production_time": iter(["0.8"]),
        "yield_rate": iter(["0.9"]),
        "stock": iter(["10"]),
    }
    controller, view = _controller(sample_service, ["1", "0"], fields)
    controller.run()
    assert view.registration_result.name == "A"
    assert view.registration_result.stock == 10


def test_register_reprompts_on_invalid_avg_production_time(sample_service):
    fields = {
        "name": "A",
        "avg_production_time": iter(["not-a-number", "0.8"]),
        "yield_rate": iter(["0.9"]),
        "stock": iter(["10"]),
    }
    controller, view = _controller(sample_service, ["1", "0"], fields)
    controller.run()
    assert view.validation_errors == ["숫자를 입력해주세요."]
    assert view.registration_result.avg_production_time == 0.8


def test_list_all_shows_table(sample_service):
    sample_service.register("A", 0.8, 0.9, 10)
    controller, view = _controller(sample_service, ["2", "0"])
    controller.run()
    samples, title = view.tables_shown[0]
    assert title == "등록 시료 목록"
    assert len(samples) == 1


def test_search_with_no_results(sample_service):
    controller, view = _controller(sample_service, ["3", "0"], {"keyword": "nope"})
    controller.run()
    assert view.no_search_result_shown == 1


def test_search_with_results(sample_service):
    sample_service.register("Alpha", 0.8, 0.9, 10)
    controller, view = _controller(sample_service, ["3", "0"], {"keyword": "Alpha"})
    controller.run()
    samples, title = view.tables_shown[0]
    assert title == "검색 결과"
    assert samples[0].name == "Alpha"


def test_invalid_choice(sample_service):
    controller, view = _controller(sample_service, ["9", "0"])
    controller.run()
    assert view.invalid_choice_shown == 1

import pytest

from sampleorder.controllers.monitoring_controller import MonitoringController
from sampleorder.services.monitoring_service import MonitoringService
from sampleorder.services.sample_service import SampleService


class _ScriptedMonitoringView:
    def __init__(self, choices):
        self._choices = iter(choices)
        self.invalid_choice_shown = 0
        self.order_status_counts = None
        self.stock_report = None

    def show_menu(self):
        pass

    def prompt_menu_choice(self):
        return next(self._choices)

    def show_invalid_choice(self):
        self.invalid_choice_shown += 1

    def show_order_status_counts(self, counts):
        self.order_status_counts = counts

    def show_stock_report(self, rows):
        self.stock_report = rows


@pytest.fixture
def monitoring_service(order_repository, sample_repository):
    return MonitoringService(order_repository, sample_repository)


@pytest.fixture
def sample_service(sample_repository):
    return SampleService(sample_repository)


def test_show_order_status_counts(monitoring_service):
    view = _ScriptedMonitoringView(["1", "0"])
    controller = MonitoringController(monitoring_service, view)
    controller.run()
    assert view.order_status_counts is not None


def test_show_stock_report(monitoring_service, sample_service):
    sample_service.register("A", 0.8, 0.9, 10)
    view = _ScriptedMonitoringView(["2", "0"])
    controller = MonitoringController(monitoring_service, view)
    controller.run()
    assert len(view.stock_report) == 1


def test_invalid_choice_then_exit(monitoring_service):
    view = _ScriptedMonitoringView(["9", "0"])
    controller = MonitoringController(monitoring_service, view)
    controller.run()
    assert view.invalid_choice_shown == 1

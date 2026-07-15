from datetime import datetime, timezone

import pytest

from sampleorder.controllers.main_controller import MainController
from sampleorder.services.monitoring_service import MonitoringService
from sampleorder.services.production_service import ProductionService
from sampleorder.views.main_view import MainView


class _CallRecorder:
    def __init__(self):
        self.calls = 0

    def run(self) -> None:
        self.calls += 1


class _ScriptedMainView(MainView):
    def __init__(self, choices):
        self._choices = iter(choices)
        self.invalid_choice_shown = 0

    def show_main_menu(self, summary, now) -> None:
        pass

    def prompt_menu_choice(self) -> str:
        return next(self._choices)

    def show_invalid_choice(self) -> None:
        self.invalid_choice_shown += 1


@pytest.fixture
def monitoring_service(order_repository, sample_repository):
    return MonitoringService(order_repository, sample_repository)


@pytest.fixture
def production_service(order_repository, sample_repository):
    return ProductionService(order_repository, sample_repository)


def _build_controller(choices, monitoring_service, production_service):
    recorders = {
        key: _CallRecorder()
        for key in (
            "sample",
            "order",
            "approval",
            "production",
            "monitoring",
            "shipping",
        )
    }
    controller = MainController(
        view=_ScriptedMainView(choices),
        monitoring_service=monitoring_service,
        production_service=production_service,
        sample_controller=recorders["sample"],
        order_controller=recorders["order"],
        approval_controller=recorders["approval"],
        production_controller=recorders["production"],
        monitoring_controller=recorders["monitoring"],
        shipping_controller=recorders["shipping"],
        now_fn=lambda: datetime(2026, 4, 16, 9, 0, 0, tzinfo=timezone.utc),
    )
    return controller, recorders


@pytest.mark.parametrize(
    "choice,key",
    [
        ("1", "sample"),
        ("2", "order"),
        ("3", "approval"),
        ("4", "monitoring"),
        ("5", "production"),
        ("6", "shipping"),
    ],
)
def test_menu_choice_dispatches_to_matching_controller(
    choice, key, monitoring_service, production_service
):
    controller, recorders = _build_controller([choice, "0"], monitoring_service, production_service)
    controller.run()
    assert recorders[key].calls == 1
    for other_key, recorder in recorders.items():
        if other_key != key:
            assert recorder.calls == 0


def test_invalid_choice_shows_message_and_redisplays_menu(monitoring_service, production_service):
    controller, recorders = _build_controller(["9", "0"], monitoring_service, production_service)
    controller.run()
    assert controller._view.invalid_choice_shown == 1
    assert all(recorder.calls == 0 for recorder in recorders.values())


def test_entering_menu_4_advances_production_queue(
    monitoring_service, production_service, sample_repository, order_repository, fixed_now
):
    from datetime import timedelta

    sample_repository.create("A", 0.8, 0.92)
    order = order_repository.create("S-001", "고객A", 200)
    production_service.enqueue(
        order.order_id, "S-001", "A", 200, 170, 185, 148.0, now_fn=lambda: fixed_now
    )

    completion_time = fixed_now + timedelta(minutes=200)
    controller, _ = _build_controller(["4", "0"], monitoring_service, production_service)
    controller._now_fn = lambda: completion_time

    controller.run()

    assert production_service.queue_length() == 0

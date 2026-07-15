from datetime import timedelta

import pytest

from sampleorder.controllers.production_controller import ProductionController
from sampleorder.services.production_service import ProductionService


class _ScriptedProductionView:
    def __init__(self):
        self.title_shown = 0
        self.no_current_item_shown = 0
        self.current_item = None
        self.pending_queue = None

    def show_title(self):
        self.title_shown += 1

    def show_no_current_item(self):
        self.no_current_item_shown += 1

    def show_current_item(self, current):
        self.current_item = current

    def show_pending_queue(self, pending):
        self.pending_queue = pending


@pytest.fixture
def production_service(order_repository, sample_repository):
    return ProductionService(order_repository, sample_repository)


def test_no_current_item(production_service, fixed_now):
    view = _ScriptedProductionView()
    controller = ProductionController(production_service, view, now_fn=lambda: fixed_now)
    controller.run()
    assert view.no_current_item_shown == 1
    assert view.current_item is None


def test_current_and_pending_items_shown(production_service, sample_repository, order_repository, fixed_now):
    sample_repository.create("A", 0.8, 0.92)
    order1 = order_repository.create("S-001", "고객A", 200)
    order2 = order_repository.create("S-001", "고객B", 100)
    production_service.enqueue(
        order1.order_id, "S-001", "A", 200, 170, 185, 148.0, now_fn=lambda: fixed_now
    )
    production_service.enqueue(
        order2.order_id, "S-001", "A", 100, 80, 90, 72.0, now_fn=lambda: fixed_now
    )

    later = fixed_now + timedelta(minutes=50)
    view = _ScriptedProductionView()
    controller = ProductionController(production_service, view, now_fn=lambda: later)
    controller.run()

    assert view.title_shown == 1
    assert view.current_item.item.order_id == order1.order_id
    assert len(view.pending_queue) == 1
    assert view.pending_queue[0].item.order_id == order2.order_id

import pytest

from sampleorder.controllers.shipping_controller import ShippingController
from sampleorder.services.order_service import OrderService
from sampleorder.services.production_service import ProductionService
from sampleorder.services.sample_service import SampleService
from sampleorder.services.shipping_service import ShippingService


class _ScriptedShippingView:
    def __init__(self, order_choice="1"):
        self._order_choice = order_choice
        self.no_shippable_shown = 0
        self.invalid_choice_shown = 0
        self.insufficient_stock_message = None
        self.release_result = None
        self.confirmed_table = None

    def show_no_shippable_orders(self):
        self.no_shippable_shown += 1

    def show_confirmed_table(self, orders, sample_names):
        self.confirmed_table = (orders, sample_names)

    def prompt_order_choice(self):
        return self._order_choice

    def show_invalid_choice(self):
        self.invalid_choice_shown += 1

    def show_insufficient_stock_error(self, message):
        self.insufficient_stock_message = message

    def show_release_result(self, result):
        self.release_result = result


@pytest.fixture
def production_service(order_repository, sample_repository):
    return ProductionService(order_repository, sample_repository)


@pytest.fixture
def order_service(order_repository, sample_repository, production_service):
    return OrderService(order_repository, sample_repository, production_service)


@pytest.fixture
def sample_service(sample_repository):
    return SampleService(sample_repository)


@pytest.fixture
def shipping_service(order_repository, sample_repository):
    return ShippingService(order_repository, sample_repository)


def _confirm_order(order_service, sample_service, stock=10, quantity=5):
    sample_service.register("A", 0.8, 0.9, stock)
    order = order_service.create_order(sample_service.list_all()[0].sample_id, "고객A", quantity)
    preview = order_service.preview_approval(order.order_id)
    order_service.confirm_approval(order.order_id, preview)
    return order


def test_no_shippable_orders(shipping_service):
    view = _ScriptedShippingView()
    controller = ShippingController(shipping_service, view)
    controller.run()
    assert view.no_shippable_shown == 1


def test_invalid_order_choice(shipping_service, order_service, sample_service):
    _confirm_order(order_service, sample_service)
    view = _ScriptedShippingView(order_choice="9")
    controller = ShippingController(shipping_service, view)
    controller.run()
    assert view.invalid_choice_shown == 1


def test_successful_release(shipping_service, order_service, sample_service):
    order = _confirm_order(order_service, sample_service, stock=10, quantity=5)
    view = _ScriptedShippingView(order_choice="1")
    controller = ShippingController(shipping_service, view)
    controller.run()
    assert view.release_result.order.order_id == order.order_id
    assert view.release_result.order.status.value == "RELEASE"


def test_insufficient_stock_shows_error(shipping_service, order_service, sample_service):
    order = _confirm_order(order_service, sample_service, stock=5, quantity=5)
    sample_id = sample_service.list_all()[0].sample_id
    sample_service._repo.update(sample_id, stock=0)
    view = _ScriptedShippingView(order_choice="1")
    controller = ShippingController(shipping_service, view)
    controller.run()
    assert view.insufficient_stock_message == "재고가 부족하여 출고할 수 없습니다. 재고를 확인해주세요."
    assert view.release_result is None

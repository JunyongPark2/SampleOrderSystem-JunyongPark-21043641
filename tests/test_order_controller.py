import pytest

from sampleorder.controllers.order_controller import OrderController
from sampleorder.services.order_service import OrderService
from sampleorder.services.sample_service import SampleService


class _ScriptedOrderView:
    def __init__(self, sample_id, customer_name="고객A", quantities=("100",), confirm=True):
        self._sample_id = sample_id
        self._customer_name = customer_name
        self._quantities = iter(quantities)
        self._confirm = confirm
        self.errors = []
        self.confirm_called_with = None
        self.intake_result = None

    def show_menu_title(self):
        pass

    def prompt_sample_id(self):
        return self._sample_id

    def show_error(self, message):
        self.errors.append(message)

    def prompt_customer_name(self):
        return self._customer_name

    def prompt_quantity(self):
        return next(self._quantities)

    def confirm_order(self, sample, customer_name, quantity):
        self.confirm_called_with = (sample, customer_name, quantity)
        return self._confirm

    def show_intake_result(self, order):
        self.intake_result = order


@pytest.fixture
def order_service(order_repository, sample_repository):
    return OrderService(order_repository, sample_repository)


@pytest.fixture
def sample_service(sample_repository):
    return SampleService(sample_repository)


def test_invalid_sample_id_shows_error_and_stops(order_service):
    view = _ScriptedOrderView(sample_id="NOPE")
    controller = OrderController(order_service, view)
    controller.run()
    assert view.errors == ["존재하지 않는 시료 ID입니다. 주문을 생성하지 않았습니다."]
    assert view.intake_result is None


def test_quantity_reprompts_until_valid(order_service, sample_service):
    sample = sample_service.register("A", 0.8, 0.9, 10)
    view = _ScriptedOrderView(sample_id=sample.sample_id, quantities=("0", "5"))
    controller = OrderController(order_service, view)
    controller.run()
    assert view.confirm_called_with[2] == 5
    assert view.intake_result.quantity == 5


def test_cancelling_confirmation_creates_no_order(order_service, sample_service):
    sample = sample_service.register("A", 0.8, 0.9, 10)
    view = _ScriptedOrderView(sample_id=sample.sample_id, quantities=("5",), confirm=False)
    controller = OrderController(order_service, view)
    controller.run()
    assert view.intake_result is None
    assert order_service.list_all_orders() == []


def test_confirmed_order_is_created(order_service, sample_service):
    sample = sample_service.register("A", 0.8, 0.9, 10)
    view = _ScriptedOrderView(sample_id=sample.sample_id, quantities=("5",), confirm=True)
    controller = OrderController(order_service, view)
    controller.run()
    assert view.intake_result is not None
    assert len(order_service.list_all_orders()) == 1

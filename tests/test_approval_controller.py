import pytest

from sampleorder.controllers.approval_controller import ApprovalController
from sampleorder.services.order_service import OrderService
from sampleorder.services.production_service import ProductionService
from sampleorder.services.sample_service import SampleService


class _ScriptedApprovalView:
    def __init__(self, order_choice="1", decision="Y", shortage_confirm="Y"):
        self._order_choice = order_choice
        self._decision = decision
        self._shortage_confirm = shortage_confirm
        self.no_pending_shown = 0
        self.invalid_choice_shown = 0
        self.approval_result = None
        self.rejection_result = None
        self.shortage_preview = None
        self.reserved_table = None

    def show_no_pending_orders(self):
        self.no_pending_shown += 1

    def show_reserved_table(self, orders, sample_names):
        self.reserved_table = (orders, sample_names)

    def prompt_order_choice(self):
        return self._order_choice

    def show_invalid_choice(self):
        self.invalid_choice_shown += 1

    def prompt_approve_or_reject(self):
        return self._decision

    def show_shortage_preview(self, preview):
        self.shortage_preview = preview

    def prompt_shortage_confirm(self):
        return self._shortage_confirm

    def show_approval_result(self, order, previous_status):
        self.approval_result = (order, previous_status)

    def show_rejection_result(self, order):
        self.rejection_result = order


@pytest.fixture
def production_service(order_repository, sample_repository):
    return ProductionService(order_repository, sample_repository)


@pytest.fixture
def order_service(order_repository, sample_repository, production_service):
    return OrderService(order_repository, sample_repository, production_service)


@pytest.fixture
def sample_service(sample_repository):
    return SampleService(sample_repository)


def test_no_pending_orders(order_service):
    view = _ScriptedApprovalView()
    controller = ApprovalController(order_service, view)
    controller.run()
    assert view.no_pending_shown == 1


def test_invalid_order_choice(order_service, sample_service):
    sample_service.register("A", 0.8, 0.9, 10)
    order_service.create_order(sample_service.list_all()[0].sample_id, "고객A", 5)
    view = _ScriptedApprovalView(order_choice="9")
    controller = ApprovalController(order_service, view)
    controller.run()
    assert view.invalid_choice_shown == 1
    assert view.approval_result is None


def test_reject_before_approval_decision(order_service, sample_service):
    sample_service.register("A", 0.8, 0.9, 10)
    order = order_service.create_order(sample_service.list_all()[0].sample_id, "고객A", 5)
    view = _ScriptedApprovalView(order_choice="1", decision="N")
    controller = ApprovalController(order_service, view)
    controller.run()
    assert view.rejection_result.status.value == "REJECTED"
    assert order_service.list_all_orders()[0].order_id == order.order_id


def test_sufficient_stock_approves_immediately(order_service, sample_service):
    sample_service.register("A", 0.8, 0.9, 10)
    order_service.create_order(sample_service.list_all()[0].sample_id, "고객A", 5)
    view = _ScriptedApprovalView(order_choice="1", decision="Y")
    controller = ApprovalController(order_service, view)
    controller.run()
    order, previous_status = view.approval_result
    assert previous_status == "RESERVED"
    assert order.status.value == "CONFIRMED"


def test_shortage_rejected_by_user(order_service, sample_service):
    sample_service.register("A", 0.8, 0.9, 2)
    order_service.create_order(sample_service.list_all()[0].sample_id, "고객A", 5)
    view = _ScriptedApprovalView(order_choice="1", decision="Y", shortage_confirm="N")
    controller = ApprovalController(order_service, view)
    controller.run()
    assert view.shortage_preview is not None
    assert view.rejection_result.status.value == "REJECTED"


def test_shortage_confirmed_enqueues_production(order_service, sample_service, production_service):
    sample_service.register("A", 0.8, 0.9, 2)
    order_service.create_order(sample_service.list_all()[0].sample_id, "고객A", 5)
    view = _ScriptedApprovalView(order_choice="1", decision="Y", shortage_confirm="Y")
    controller = ApprovalController(order_service, view)
    controller.run()
    order, previous_status = view.approval_result
    assert previous_status == "RESERVED"
    assert order.status.value == "PRODUCING"
    assert production_service.queue_length() == 1

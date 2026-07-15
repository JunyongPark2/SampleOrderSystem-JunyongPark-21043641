from sampleorder.clock import utc_now
from sampleorder.controllers.approval_controller import ApprovalController
from sampleorder.controllers.monitoring_controller import MonitoringController
from sampleorder.controllers.order_controller import OrderController
from sampleorder.controllers.production_controller import ProductionController
from sampleorder.controllers.sample_controller import SampleController
from sampleorder.controllers.shipping_controller import ShippingController
from sampleorder.services.monitoring_service import MonitoringService
from sampleorder.services.production_service import ProductionService
from sampleorder.views.main_view import MainView


class MainController:
    def __init__(
        self,
        view: MainView,
        monitoring_service: MonitoringService,
        production_service: ProductionService,
        sample_controller: SampleController,
        order_controller: OrderController,
        approval_controller: ApprovalController,
        production_controller: ProductionController,
        monitoring_controller: MonitoringController,
        shipping_controller: ShippingController,
        now_fn=utc_now,
    ):
        self._view = view
        self._monitoring_service = monitoring_service
        self._production_service = production_service
        self._now_fn = now_fn
        self._actions = {
            "1": sample_controller.run,
            "2": order_controller.run,
            "3": approval_controller.run,
            "4": self._enter_monitoring(monitoring_controller),
            "5": production_controller.run,
            "6": self._enter_shipping(shipping_controller),
        }

    def _enter_monitoring(self, monitoring_controller: MonitoringController):
        def _run() -> None:
            self._production_service.advance(self._now_fn)
            monitoring_controller.run()

        return _run

    def _enter_shipping(self, shipping_controller: ShippingController):
        def _run() -> None:
            self._production_service.advance(self._now_fn)
            shipping_controller.run()

        return _run

    def run(self) -> None:
        while True:
            summary = self._monitoring_service.dashboard_summary(self._production_service.queue_length())
            self._view.show_main_menu(summary, self._now_fn())
            choice = self._view.prompt_menu_choice()
            if choice == "0":
                return
            action = self._actions.get(choice)
            if action is None:
                self._view.show_invalid_choice()
                continue
            action()

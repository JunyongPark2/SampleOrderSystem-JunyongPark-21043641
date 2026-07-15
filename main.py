import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from sampleorder.controllers.approval_controller import ApprovalController
from sampleorder.controllers.main_controller import MainController
from sampleorder.controllers.monitoring_controller import MonitoringController
from sampleorder.controllers.order_controller import OrderController
from sampleorder.controllers.production_controller import ProductionController
from sampleorder.controllers.sample_controller import SampleController
from sampleorder.controllers.shipping_controller import ShippingController
from sampleorder.json_store import JsonFileStore
from sampleorder.repositories.order_repository import OrderRepository
from sampleorder.repositories.sample_repository import SampleRepository
from sampleorder.services.monitoring_service import MonitoringService
from sampleorder.services.order_service import OrderService
from sampleorder.services.production_service import ProductionService
from sampleorder.services.sample_service import SampleService
from sampleorder.services.shipping_service import ShippingService
from sampleorder.views.approval_view import ApprovalView
from sampleorder.views.main_view import MainView
from sampleorder.views.monitoring_view import MonitoringView
from sampleorder.views.order_view import OrderView
from sampleorder.views.production_view import ProductionView
from sampleorder.views.sample_view import SampleView
from sampleorder.views.shipping_view import ShippingView

DATA_DIR = Path(__file__).parent / "data"


def build_main_controller() -> MainController:
    sample_store = JsonFileStore(DATA_DIR / "samples.json")
    order_store = JsonFileStore(DATA_DIR / "orders.json")
    sample_repo = SampleRepository(sample_store)
    order_repo = OrderRepository(order_store)

    production_service = ProductionService(order_repo, sample_repo)
    sample_service = SampleService(sample_repo)
    order_service = OrderService(order_repo, sample_repo, production_service)
    monitoring_service = MonitoringService(order_repo, sample_repo)
    shipping_service = ShippingService(order_repo, sample_repo)

    sample_controller = SampleController(sample_service, SampleView())
    order_controller = OrderController(order_service, OrderView())
    approval_controller = ApprovalController(order_service, ApprovalView(), sample_repo)
    production_controller = ProductionController(production_service, ProductionView())
    monitoring_controller = MonitoringController(monitoring_service, MonitoringView())
    shipping_controller = ShippingController(shipping_service, ShippingView(), sample_repo)

    return MainController(
        view=MainView(),
        monitoring_service=monitoring_service,
        production_service=production_service,
        sample_controller=sample_controller,
        order_controller=order_controller,
        approval_controller=approval_controller,
        production_controller=production_controller,
        monitoring_controller=monitoring_controller,
        shipping_controller=shipping_controller,
    )


def main() -> None:
    build_main_controller().run()


if __name__ == "__main__":
    main()

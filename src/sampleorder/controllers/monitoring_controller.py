from sampleorder.services.monitoring_service import MonitoringService
from sampleorder.views.monitoring_view import MonitoringView


class MonitoringController:
    def __init__(self, service: MonitoringService, view: MonitoringView):
        self._service = service
        self._view = view

    def run(self) -> None:
        while True:
            self._view.show_menu()
            choice = self._view.prompt_menu_choice()
            if choice == "0":
                return
            elif choice == "1":
                self._view.show_order_status_counts(self._service.order_status_counts())
            elif choice == "2":
                self._view.show_stock_report(self._service.stock_report())
            else:
                self._view.show_invalid_choice()

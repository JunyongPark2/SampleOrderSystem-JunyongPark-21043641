from sampleorder.services.shipping_service import ShippingService
from sampleorder.views.shipping_view import ShippingView


class ShippingController:
    def __init__(self, service: ShippingService, view: ShippingView, sample_repository):
        self._service = service
        self._view = view
        self._sample_repo = sample_repository

    def run(self) -> None:
        orders = self._service.list_confirmed_orders()
        if not orders:
            self._view.show_no_shippable_orders()
            return

        sample_names = {order.sample_id: self._sample_repo.get(order.sample_id).name for order in orders}
        self._view.show_confirmed_table(orders, sample_names)

        choice = self._view.prompt_order_choice()
        if not choice.isdigit() or not (1 <= int(choice) <= len(orders)):
            self._view.show_invalid_choice()
            return

        order = orders[int(choice) - 1]
        result = self._service.release(order.order_id)
        self._view.show_release_result(result)

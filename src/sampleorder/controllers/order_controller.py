from sampleorder.exceptions import ValidationError
from sampleorder.services.order_service import QUANTITY_ERROR, OrderService
from sampleorder.views.order_view import OrderView


class OrderController:
    def __init__(self, service: OrderService, view: OrderView):
        self._service = service
        self._view = view

    def run(self) -> None:
        self._view.show_menu_title()
        sample_id = self._view.prompt_sample_id()
        try:
            sample = self._service.validate_sample_id(sample_id)
        except ValidationError as error:
            self._view.show_error(error.message)
            return

        customer_name = self._view.prompt_customer_name()
        quantity = self._prompt_quantity()

        if not self._view.confirm_order(sample, customer_name, quantity):
            return

        order = self._service.create_order(sample_id, customer_name, quantity)
        self._view.show_intake_result(order)

    def _prompt_quantity(self) -> int:
        while True:
            raw = self._view.prompt_quantity()
            try:
                quantity = int(raw)
                self._service.validate_quantity(quantity)
                return quantity
            except ValueError:
                self._view.show_error(QUANTITY_ERROR)
            except ValidationError as error:
                self._view.show_error(error.message)

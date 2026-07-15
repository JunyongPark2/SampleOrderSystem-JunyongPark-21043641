from sampleorder.controllers._prompting import prompt_until_valid
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
        return prompt_until_valid(
            self._view.prompt_quantity,
            int,
            self._service.validate_quantity,
            self._view.show_error,
            QUANTITY_ERROR,
        )

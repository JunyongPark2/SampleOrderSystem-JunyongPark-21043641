from sampleorder.services.order_service import APPROVAL_SUFFICIENT, OrderService
from sampleorder.views.approval_view import ApprovalView


class ApprovalController:
    def __init__(self, service: OrderService, view: ApprovalView):
        self._service = service
        self._view = view

    def run(self) -> None:
        orders = self._service.list_reserved_orders()
        if not orders:
            self._view.show_no_pending_orders()
            return

        sample_names = self._service.sample_name_map(orders)
        self._view.show_reserved_table(orders, sample_names)

        choice = self._view.prompt_order_choice()
        if not choice.isdigit() or not (1 <= int(choice) <= len(orders)):
            self._view.show_invalid_choice()
            return

        order = orders[int(choice) - 1]
        decision = self._view.prompt_approve_or_reject()
        if decision == "N":
            rejected = self._service.reject_order(order.order_id)
            self._view.show_rejection_result(rejected)
            return

        self._approve(order.order_id)

    def _approve(self, order_id: str) -> None:
        preview = self._service.preview_approval(order_id)
        if preview.kind == APPROVAL_SUFFICIENT:
            updated = self._service.confirm_approval(order_id, preview)
            self._view.show_approval_result(updated, "RESERVED")
            return

        self._view.show_shortage_preview(preview)
        confirm = self._view.prompt_shortage_confirm()
        if confirm == "N":
            rejected = self._service.reject_order(order_id)
            self._view.show_rejection_result(rejected)
            return
        updated = self._service.confirm_approval(order_id, preview)
        self._view.show_approval_result(updated, "RESERVED")

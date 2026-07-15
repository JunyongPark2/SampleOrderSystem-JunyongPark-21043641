from sampleorder.clock import utc_now
from sampleorder.services.production_service import ProductionService
from sampleorder.views.production_view import ProductionView


class ProductionController:
    def __init__(self, service: ProductionService, view: ProductionView, now_fn=utc_now):
        self._service = service
        self._view = view
        self._now_fn = now_fn

    def run(self) -> None:
        self._service.advance(self._now_fn)
        self._view.show_title()

        current = self._service.current_item(self._now_fn)
        if current is None:
            self._view.show_no_current_item()
            return

        self._view.show_current_item(current)
        pending = self._service.pending_queue(self._now_fn)
        self._view.show_pending_queue(pending)

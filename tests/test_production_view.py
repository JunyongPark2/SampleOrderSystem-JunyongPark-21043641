from datetime import datetime, timezone

from sampleorder.services.production_service import CurrentItem, PendingItem, QueueItem
from sampleorder.views.production_view import ProductionView


def _item(order_id="O-001", sample_name="Alpha"):
    return QueueItem(
        order_id=order_id,
        sample_id="S-001",
        sample_name=sample_name,
        quantity=200,
        shortage_qty=170,
        actual_yield_qty=185,
        total_time=148.0,
        started_at=datetime(2026, 4, 16, 9, 0, 0, tzinfo=timezone.utc),
    )


def test_show_title(capsys):
    ProductionView().show_title()
    out = capsys.readouterr().out
    assert "FIFO 방식" in out
    assert "RUNNING" in out


def test_show_no_current_item(capsys):
    ProductionView().show_no_current_item()
    assert "생산라인 대기 중인 주문이 없습니다." in capsys.readouterr().out


def test_show_current_item_renders_progress_bar_and_eta(capsys):
    current = CurrentItem(
        item=_item(),
        progress=0.5,
        eta=datetime(2026, 4, 16, 11, 28, 0, tzinfo=timezone.utc),
    )
    ProductionView().show_current_item(current)
    out = capsys.readouterr().out
    assert "O-001" in out
    assert "Alpha" in out
    assert "170 ea" in out
    assert "185 ea" in out
    assert "50%" in out
    assert "11:28" in out
    assert "█████░░░░░" in out


def test_show_pending_queue(capsys):
    pending = [
        PendingItem(
            item=_item(order_id="O-002", sample_name="Beta"),
            expected_completion=datetime(2026, 4, 16, 13, 56, 0, tzinfo=timezone.utc),
        )
    ]
    ProductionView().show_pending_queue(pending)
    out = capsys.readouterr().out
    assert "O-002" in out
    assert "Beta" in out
    assert "13:56" in out
    assert "FIFO" in out

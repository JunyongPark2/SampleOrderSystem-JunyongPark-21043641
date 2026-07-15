from sampleorder.models import OrderStatus
from sampleorder.services.monitoring_service import StockReportRow
from sampleorder.views.monitoring_view import MonitoringView


def test_show_menu(capsys):
    MonitoringView().show_menu()
    out = capsys.readouterr().out
    assert "모니터링" in out


def test_prompt_menu_choice(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "  1  ")
    assert MonitoringView().prompt_menu_choice() == "1"


def test_show_invalid_choice(capsys):
    MonitoringView().show_invalid_choice()
    assert "잘못된 입력" in capsys.readouterr().out


def test_show_order_status_counts(capsys):
    counts = {OrderStatus.RESERVED: 2, OrderStatus.CONFIRMED: 1}
    MonitoringView().show_order_status_counts(counts)
    out = capsys.readouterr().out
    assert "RESERVED" in out
    assert "2건" in out
    assert "CONFIRMED" in out
    assert "1건" in out


def test_show_stock_report(capsys):
    rows = [StockReportRow(sample_id="S-001", name="Alpha", stock=10, status="OK")]
    MonitoringView().show_stock_report(rows)
    out = capsys.readouterr().out
    assert "Alpha" in out
    assert "10 ea" in out
    assert "OK" in out

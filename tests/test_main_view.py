from datetime import datetime, timezone

from sampleorder.services.monitoring_service import DashboardSummary
from sampleorder.views.main_view import MainView


def test_show_main_menu_prints_summary(capsys):
    view = MainView()
    summary = DashboardSummary(
        sample_count=3, total_stock=100, total_order_count=5, production_queue_count=2
    )
    view.show_main_menu(summary, datetime(2026, 4, 16, 9, 0, 0, tzinfo=timezone.utc))
    out = capsys.readouterr().out
    assert "3종" in out
    assert "100" in out
    assert "5건" in out
    assert "2건 대기" in out


def test_prompt_menu_choice_strips_input(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "  1  ")
    assert MainView().prompt_menu_choice() == "1"


def test_show_invalid_choice(capsys):
    MainView().show_invalid_choice()
    assert "잘못된 입력" in capsys.readouterr().out


def test_show_not_implemented(capsys):
    MainView().show_not_implemented()
    assert "구현되지 않은" in capsys.readouterr().out

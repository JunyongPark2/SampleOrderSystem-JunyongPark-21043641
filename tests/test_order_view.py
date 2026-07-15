from sampleorder.models import Order, OrderStatus, Sample
from sampleorder.views.order_view import OrderView


def test_prompts_strip_input(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "  value  ")
    view = OrderView()
    assert view.prompt_sample_id() == "value"
    assert view.prompt_customer_name() == "value"
    assert view.prompt_quantity() == "value"


def test_show_menu_title(capsys):
    OrderView().show_menu_title()
    out = capsys.readouterr().out
    assert "시료 주문" in out


def test_show_error(capsys):
    OrderView().show_error("존재하지 않는 시료 ID입니다.")
    assert "존재하지 않는 시료 ID입니다." in capsys.readouterr().out


def test_confirm_order_accepts_yes(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "Y")
    sample = Sample("S-001", "Alpha", 0.8, 0.9, stock=10)
    assert OrderView().confirm_order(sample, "고객A", 5) is True
    out = capsys.readouterr().out
    assert "Alpha" in out
    assert "고객A" in out
    assert "5 ea" in out


def test_confirm_order_accepts_no(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "N")
    sample = Sample("S-001", "Alpha", 0.8, 0.9, stock=10)
    assert OrderView().confirm_order(sample, "고객A", 5) is False


def test_confirm_order_reprompts_on_invalid_choice(monkeypatch, capsys):
    responses = iter(["X", "Y"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    sample = Sample("S-001", "Alpha", 0.8, 0.9, stock=10)
    assert OrderView().confirm_order(sample, "고객A", 5) is True
    assert "잘못된 입력" in capsys.readouterr().out


def test_show_intake_result(capsys):
    order = Order("O-001", "S-001", "고객A", 5, "2026-04-16T09:00:00", OrderStatus.RESERVED)
    OrderView().show_intake_result(order)
    out = capsys.readouterr().out
    assert "O-001" in out
    assert "RESERVED" in out

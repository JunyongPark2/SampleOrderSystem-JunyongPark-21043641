from datetime import datetime, timezone

from sampleorder.models import Order, OrderStatus
from sampleorder.services.shipping_service import ReleaseResult
from sampleorder.views.shipping_view import ShippingView


def _order(status=OrderStatus.CONFIRMED):
    return Order("O-001", "S-001", "고객A", 5, "2026-04-16T09:00:00", status)


def test_show_confirmed_table(capsys):
    ShippingView().show_confirmed_table([_order()], {"S-001": "Alpha"})
    out = capsys.readouterr().out
    assert "O-001" in out
    assert "Alpha" in out


def test_show_no_shippable_orders(capsys):
    ShippingView().show_no_shippable_orders()
    assert "출고 가능한 주문이 없습니다." in capsys.readouterr().out


def test_prompt_order_choice(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "  2  ")
    assert ShippingView().prompt_order_choice() == "2"


def test_show_invalid_choice(capsys):
    ShippingView().show_invalid_choice()
    assert "잘못된 입력" in capsys.readouterr().out


def test_show_insufficient_stock_error(capsys):
    ShippingView().show_insufficient_stock_error("재고가 부족하여 출고할 수 없습니다.")
    assert "재고가 부족하여 출고할 수 없습니다." in capsys.readouterr().out


def test_show_release_result(capsys):
    result = ReleaseResult(
        order=_order(status=OrderStatus.RELEASE),
        processed_at=datetime(2026, 4, 16, 9, 30, 0, tzinfo=timezone.utc),
    )
    ShippingView().show_release_result(result)
    out = capsys.readouterr().out
    assert "O-001" in out
    assert "5 ea" in out
    assert "CONFIRMED → RELEASE" in out

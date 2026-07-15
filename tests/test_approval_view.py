from sampleorder.models import Order, OrderStatus, Sample
from sampleorder.services.order_service import APPROVAL_SHORTAGE, ApprovalPreview
from sampleorder.views.approval_view import ApprovalView


def _order():
    return Order("O-001", "S-001", "고객A", 5, "2026-04-16T09:00:00", OrderStatus.RESERVED)


def test_show_reserved_table(capsys):
    order = _order()
    ApprovalView().show_reserved_table([order], {"S-001": "Alpha"})
    out = capsys.readouterr().out
    assert "O-001" in out
    assert "Alpha" in out
    assert "고객A" in out


def test_show_no_pending_orders(capsys):
    ApprovalView().show_no_pending_orders()
    assert "승인 대기 중인 주문이 없습니다." in capsys.readouterr().out


def test_prompt_order_choice(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "  1  ")
    assert ApprovalView().prompt_order_choice() == "1"


def test_prompt_approve_or_reject_reprompts_on_invalid(monkeypatch, capsys):
    responses = iter(["x", "y"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    assert ApprovalView().prompt_approve_or_reject() == "Y"
    assert "잘못된 입력" in capsys.readouterr().out


def test_show_shortage_preview(capsys):
    order = _order()
    sample = Sample("S-001", "Alpha", 0.8, 0.9, stock=2)
    preview = ApprovalPreview(
        kind=APPROVAL_SHORTAGE,
        order=order,
        sample=sample,
        shortage_qty=3,
        actual_yield_qty=4,
        total_time=3.2,
    )
    ApprovalView().show_shortage_preview(preview)
    out = capsys.readouterr().out
    assert "Alpha" in out
    assert "3 ea" in out
    assert "4 ea" in out


def test_prompt_shortage_confirm_reprompts_on_invalid(monkeypatch, capsys):
    responses = iter(["z", "n"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    assert ApprovalView().prompt_shortage_confirm() == "N"
    assert "잘못된 입력" in capsys.readouterr().out


def test_show_approval_result(capsys):
    order = Order("O-001", "S-001", "고객A", 5, "2026-04-16T09:00:00", OrderStatus.CONFIRMED)
    ApprovalView().show_approval_result(order, "RESERVED")
    out = capsys.readouterr().out
    assert "RESERVED → CONFIRMED" in out
    assert "O-001" in out


def test_show_rejection_result(capsys):
    order = Order("O-001", "S-001", "고객A", 5, "2026-04-16T09:00:00", OrderStatus.REJECTED)
    ApprovalView().show_rejection_result(order)
    out = capsys.readouterr().out
    assert "RESERVED → REJECTED" in out
    assert "O-001" in out

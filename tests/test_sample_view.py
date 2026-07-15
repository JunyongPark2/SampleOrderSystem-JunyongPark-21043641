from sampleorder.models import Sample
from sampleorder.views.sample_view import SampleView


def test_show_menu(capsys):
    SampleView().show_menu()
    out = capsys.readouterr().out
    assert "시료 관리" in out


def test_prompts_strip_input(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "  value  ")
    view = SampleView()
    assert view.prompt_menu_choice() == "value"
    assert view.prompt_name() == "value"
    assert view.prompt_avg_production_time() == "value"
    assert view.prompt_yield_rate() == "value"
    assert view.prompt_stock() == "value"
    assert view.prompt_search_keyword() == "value"


def test_show_invalid_choice(capsys):
    SampleView().show_invalid_choice()
    assert "잘못된 입력" in capsys.readouterr().out


def test_show_validation_error(capsys):
    SampleView().show_validation_error("custom error")
    assert "custom error" in capsys.readouterr().out


def test_show_registration_result(capsys):
    sample = Sample("S-001", "A", 0.8, 0.9, stock=10)
    SampleView().show_registration_result(sample)
    out = capsys.readouterr().out
    assert "S-001" in out
    assert "A" in out
    assert "10 ea" in out


def test_show_no_search_result(capsys):
    SampleView().show_no_search_result()
    assert "일치하는 시료가 없습니다." in capsys.readouterr().out


def test_show_sample_table(capsys):
    samples = [Sample("S-001", "Alpha", 0.8, 0.9, stock=10)]
    SampleView().show_sample_table(samples, "제목")
    out = capsys.readouterr().out
    assert "제목 (총 1종)" in out
    assert "S-001" in out
    assert "Alpha" in out

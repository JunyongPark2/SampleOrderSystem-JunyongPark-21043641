from sampleorder.views.formatting import ljust, rjust


def test_ljust_pads_ascii_text():
    assert ljust("AB", 5) == "AB   "


def test_ljust_accounts_for_wide_characters():
    assert ljust("가", 5) == "가   "


def test_ljust_returns_text_unchanged_when_width_exceeded():
    assert ljust("ABCDEF", 3) == "ABCDEF"


def test_rjust_pads_ascii_text():
    assert rjust("AB", 5) == "   AB"


def test_rjust_accounts_for_wide_characters():
    assert rjust("가", 5) == "   가"

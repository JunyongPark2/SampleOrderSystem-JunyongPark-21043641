import pytest

from sampleorder.controllers._prompting import prompt_until_valid
from sampleorder.exceptions import ValidationError


def test_returns_first_valid_value():
    result = prompt_until_valid(
        prompt_fn=lambda: "5",
        parse_fn=int,
        validate_fn=lambda v: None,
        show_error_fn=lambda msg: pytest.fail("should not show error"),
        invalid_parse_message="not a number",
    )
    assert result == 5


def test_reprompts_on_parse_error_then_succeeds():
    raw_values = iter(["abc", "7"])
    errors = []
    result = prompt_until_valid(
        prompt_fn=lambda: next(raw_values),
        parse_fn=int,
        validate_fn=lambda v: None,
        show_error_fn=errors.append,
        invalid_parse_message="not a number",
    )
    assert result == 7
    assert errors == ["not a number"]


def test_reprompts_on_validation_error_then_succeeds():
    raw_values = iter(["-1", "3"])
    errors = []

    def validate(value):
        if value < 0:
            raise ValidationError("must be positive")

    result = prompt_until_valid(
        prompt_fn=lambda: next(raw_values),
        parse_fn=int,
        validate_fn=validate,
        show_error_fn=errors.append,
        invalid_parse_message="not a number",
    )
    assert result == 3
    assert errors == ["must be positive"]

from sampleorder.exceptions import ValidationError


def validate_int(value, min_value: int, error_message: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < min_value:
        raise ValidationError(error_message)
    return value

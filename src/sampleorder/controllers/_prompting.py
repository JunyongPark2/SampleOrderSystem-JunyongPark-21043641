from sampleorder.exceptions import ValidationError


def prompt_until_valid(prompt_fn, parse_fn, validate_fn, show_error_fn, invalid_parse_message):
    while True:
        raw = prompt_fn()
        try:
            value = parse_fn(raw)
            validate_fn(value)
            return value
        except ValueError:
            show_error_fn(invalid_parse_message)
        except ValidationError as error:
            show_error_fn(error.message)

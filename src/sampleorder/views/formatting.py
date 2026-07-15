import unicodedata


def _display_width(text: str) -> int:
    return sum(2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1 for ch in text)


def ljust(text: str, width: int) -> str:
    padding = max(width - _display_width(text), 0)
    return text + " " * padding


def rjust(text: str, width: int) -> str:
    padding = max(width - _display_width(text), 0)
    return " " * padding + text

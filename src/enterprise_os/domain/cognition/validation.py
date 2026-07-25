from collections.abc import Mapping, Sequence
from datetime import datetime
from math import isfinite

from enterprise_os.domain.cognition.types import CONFIDENCE_LEVELS, Confidence


def require_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def require_items(values: Sequence[object], field_name: str) -> None:
    if len(values) == 0:
        raise ValueError(f"{field_name} must contain at least one item")


def require_confidence(value: Confidence, field_name: str = "confidence") -> None:
    if value not in CONFIDENCE_LEVELS:
        raise ValueError(f"{field_name} must be one of {CONFIDENCE_LEVELS}")


def require_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")
    return value


def require_text_items(
    value: object,
    field_name: str,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise TypeError(f"{field_name} must be a sequence of text values")

    items = tuple(str(item) for item in value)
    for index, item in enumerate(items):
        if not item.strip():
            raise ValueError(f"{field_name}[{index}] must not be empty")

    if not allow_empty:
        require_items(items, field_name)

    return items


def require_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


def require_non_negative_float(value: object, field_name: str) -> float:
    if not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a number")

    numeric_value = float(value)
    if not isfinite(numeric_value) or numeric_value < 0:
        raise ValueError(f"{field_name} must be a finite, non-negative number")

    return numeric_value

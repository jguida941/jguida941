"""Closed numeric geometry validators for rendered browser facts."""
from __future__ import annotations

import math


BOX_FIELDS = {"x", "y", "left", "top", "right", "bottom", "width", "height"}
SCROLL_FIELDS = {"client_width", "client_height", "scroll_width", "scroll_height"}
ROUNDING_TOLERANCE = 0.02
MAX_SAFE_INTEGER = 2**53 - 1


def finite_number(value: object, *, label: str, nonnegative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(f"{label}: expected a numeric value")
    number = float(value)
    if (not math.isfinite(number) or abs(number) > MAX_SAFE_INTEGER
            or (nonnegative and number < 0)):
        raise RuntimeError(f"{label}: numeric value is nonfinite or negative")
    return number


def nonnegative_integer(value: object, *, label: str) -> int:
    if (isinstance(value, bool) or not isinstance(value, int)
            or value < 0 or value > MAX_SAFE_INTEGER):
        raise RuntimeError(f"{label}: expected a nonnegative integer")
    return value


def validate_box(value: object, *, label: str) -> None:
    if not isinstance(value, dict) or set(value) != BOX_FIELDS:
        raise RuntimeError(f"{label}: box fields are not closed")
    numbers = {
        key: finite_number(
            value[key], label=f"{label}/{key}", nonnegative=key in {"width", "height"}
        )
        for key in BOX_FIELDS
    }
    if any(abs(number * 100 - round(number * 100)) > 1e-7
           for number in numbers.values()):
        raise RuntimeError(f"{label}: box geometry exceeds two-decimal precision")
    identities = (
        (numbers["x"], numbers["left"], "x/left"),
        (numbers["y"], numbers["top"], "y/top"),
        (numbers["right"] - numbers["left"], numbers["width"], "horizontal"),
        (numbers["bottom"] - numbers["top"], numbers["height"], "vertical"),
    )
    if any(abs(left - right) > ROUNDING_TOLERANCE for left, right, _ in identities):
        bad = next(name for left, right, name in identities
                   if abs(left - right) > ROUNDING_TOLERANCE)
        raise RuntimeError(f"{label}: inconsistent {bad} box geometry")


def validate_scroll(value: object, *, label: str) -> None:
    if not isinstance(value, dict) or set(value) != SCROLL_FIELDS:
        raise RuntimeError(f"{label}: scroll fields are not closed")
    for key in SCROLL_FIELDS:
        nonnegative_integer(value[key], label=f"{label}/{key}")
    if (value["scroll_width"] < value["client_width"]
            or value["scroll_height"] < value["client_height"]):
        raise RuntimeError(f"{label}: scroll extent is smaller than its client extent")

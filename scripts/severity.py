"""Severity helpers for checks and triage findings."""

from __future__ import annotations

from typing import Any


SEVERITY_ORDER = {
    "info": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def severity_value(level: str | None) -> int:
    if not isinstance(level, str):
        return -1
    return SEVERITY_ORDER.get(level.lower(), -1)


def is_at_or_above(level: str | None, threshold: str) -> bool:
    threshold_value = SEVERITY_ORDER.get(threshold.lower(), 999)
    return severity_value(level) >= threshold_value


def any_at_or_above(
    items: list[dict[str, Any]],
    threshold: str,
    *,
    severity_key: str = "severity",
) -> bool:
    for item in items:
        if is_at_or_above(item.get(severity_key), threshold):
            return True
    return False

"""Data contracts used across validation, triage, and diagnostics."""

from __future__ import annotations

from typing import Any

from scripts.profile_contract import SNAPSHOT_METRICS


REQUIRED_README_SECTIONS = (
    "By The Numbers",
    "Builder Scorecard",
    "Contribution Calendar",
    "Current Focus",
    "Raw Data Snapshot (Python Pull)",
    "Deep Dive Data",
)


REQUIRED_PROFILE_SNAPSHOT_KEYS = {
    "generated_at",
    "username",
    "dashboard_url",
    "snapshot",
    "snapshot_rows",
    "snapshot_cards",
    "scorecard",
    "scorecard_cards",
    "data_scope",
    "data_quality",
    "focus",
    "top_languages",
    "repo_language_matrix",
    "activity_feed",
    "recent_created",
}


def expected_snapshot_metric_keys() -> set[str]:
    return {entry["key"] for entry in SNAPSHOT_METRICS}


def missing_required_keys(payload: dict[str, Any], required_keys: set[str]) -> list[str]:
    return sorted(key for key in required_keys if key not in payload)


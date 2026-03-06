"""Shared required keys and README checks."""

from __future__ import annotations

from typing import Any, TypedDict

from scripts.profile_contract import SNAPSHOT_METRICS


# ---------------------------------------------------------------------------
# Typed contracts for key data shapes
# ---------------------------------------------------------------------------


class Snapshot(TypedDict):
    last_year_contributions: int | None
    public_scope_commits: int | None
    total_repos: int
    public_forks: int
    private_owned_repos: int | None
    total_stars: int
    languages_count: int
    prs_merged: int
    releases: int | None
    ci_repos: int | None
    streak_days: int


class DataQuality(TypedDict):
    ci_status: str
    ci_note: str
    commits_status: str
    commits_note: str
    releases_status: str
    releases_note: str
    events_status: str
    events_note: str
    token_mode: str


class DataScope(TypedDict):
    repos_included: str
    activity_metric_scope: str
    public_owned_repos_total: int
    public_owned_forks_total: int
    public_owned_nonfork_repos_total: int
    private_owned_repos_total: int | None


class FocusItem(TypedDict):
    title: str
    detail: str
    url: str


class FocusLanes(TypedDict):
    now: list[FocusItem]
    next: list[FocusItem]
    shipped: list[FocusItem]


class ScorecardCard(TypedDict):
    key: str
    label: str
    detail: str
    value: object
    display_value: str
    accent: str


class SnapshotRow(TypedDict):
    key: str
    label: str
    dashboard_label: str
    value: object
    display_value: str


REQUIRED_README_MARKERS = (
    "metrics.general.svg",
    "assets/streak_summary.svg",
    "assets/badges.svg",
    "assets/builder_scorecard.svg",
    "assets/contribution_calendar.svg",
    "assets/now_next_shipped.svg",
    "assets/currently_working.svg",
    "assets/lang_breakdown.svg",
    "assets/activity_heatmap.svg",
    "assets/repo_spotlight.svg",
    "assets/raw_snapshot.svg",
    "### Deep Dive Data",
    "site/data/profile_snapshot.json",
)


DISALLOWED_README_HEADINGS = (
    "### By The Numbers",
    "### Builder Scorecard",
    "### Contribution Calendar",
    "### Current Focus",
    "### Currently Working On",
    "### Language Breakdown",
    "### Raw Data Snapshot (Python Pull)",
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

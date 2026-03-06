"""Metric definitions and formatting rules for profile outputs."""

from __future__ import annotations

from typing import Any


SCORECARD_METRICS = [
    {
        "key": "releases_30d",
        "label": "Release Velocity (30d)",
        "detail": "published releases across public repos",
        "format": "int_or_na",
        "accent": "ORANGE",
    },
    {
        "key": "active_repos_7d",
        "label": "Active Repos (7d)",
        "detail": "pushed in last week",
        "format": "int",
        "accent": "CYAN",
    },
    {
        "key": "avg_release_gap_days",
        "label": "Avg Release Gap",
        "detail": "days between release events",
        "format": "fixed",
        "digits": 1,
        "suffix": "d",
        "accent": "GREEN",
    },
    {
        "key": "stars_per_public_repo",
        "label": "Stars / Public Repo",
        "detail": "signal density",
        "format": "fixed",
        "digits": 2,
        "accent": "BLUE",
    },
    {
        "key": "ci_coverage_pct",
        "label": "CI Coverage",
        "detail": "repos with workflows",
        "format": "fixed_or_na",
        "digits": 1,
        "suffix": "%",
        "accent": "ORANGE",
    },
    {
        "key": "last_year_contributions",
        "label": "12mo Contributions",
        "detail": "contribution calendar",
        "format": "int_or_na",
        "accent": "CYAN",
    },
]


SNAPSHOT_METRICS = [
    {
        "key": "last_year_contributions",
        "label": "Last 12 Months Contributions",
        "dashboard_label": "12mo Contributions",
        "format": "int_or_na",
    },
    {
        "key": "public_scope_commits",
        "label": "Public Repo Commits (Owned Non-Fork)",
        "dashboard_label": "Public Scope Commits",
        "format": "int_or_na",
    },
    {
        "key": "total_repos",
        "label": "Public Non-Fork Repos",
        "dashboard_label": "Public Non-Fork Repos",
        "format": "int",
    },
    {
        "key": "public_forks",
        "label": "Public Fork Repos",
        "dashboard_label": "Public Fork Repos",
        "format": "int",
    },
    {
        "key": "private_owned_repos",
        "label": "Private Owned Repos",
        "dashboard_label": "Private Owned Repos",
        "format": "int_or_na",
    },
    {
        "key": "total_stars",
        "label": "Repo Stargazers (Received)",
        "dashboard_label": "Repo Stargazers (Received)",
        "format": "int",
    },
    {
        "key": "languages_count",
        "label": "Languages Detected",
        "dashboard_label": "Languages Detected",
        "format": "int",
    },
    {
        "key": "prs_merged",
        "label": "PRs Merged (Last 12 Months)",
        "dashboard_label": "PRs Merged (12mo)",
        "format": "int",
    },
    {
        "key": "releases",
        "label": "Releases (30 Days)",
        "dashboard_label": "Releases (30d)",
        "format": "int_or_na",
    },
    {
        "key": "ci_repos",
        "label": "Repos With CI/CD",
        "dashboard_label": "Repos With CI",
        "format": "int_or_na",
    },
    {
        "key": "streak_days",
        "label": "Current Streak Days",
        "dashboard_label": "Current Streak Days",
        "format": "int",
    },
]


def format_metric_value(value: Any, definition: dict[str, Any]) -> str:
    fmt = definition.get("format", "int")
    suffix = str(definition.get("suffix", ""))

    if fmt == "fixed_or_na":
        if value is None:
            return "n/a"
        digits = int(definition.get("digits", 1))
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return "n/a"
        return f"{numeric:.{digits}f}{suffix}"

    if fmt == "fixed":
        if value is None:
            return "n/a"
        digits = int(definition.get("digits", 1))
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return "n/a"
        return f"{numeric:.{digits}f}{suffix}"

    if fmt == "int_or_na":
        if value is None:
            return "n/a"
        try:
            numeric = int(value)
        except (TypeError, ValueError):
            return "n/a"
        return f"{numeric:,}{suffix}"

    try:
        numeric = int(value)
    except (TypeError, ValueError):
        numeric = 0
    return f"{numeric:,}{suffix}"

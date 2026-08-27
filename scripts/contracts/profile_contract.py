"""Metric definitions, claim carriers, and formatting rules for profile outputs."""

from __future__ import annotations

from typing import Any

from scripts.rendering.svg_utils import xml_escape


# Curated backend-developer scorecard (8 tiles -> clean 4x2 grid). Each value is
# wired in compute_metrics.compute_profile_model's `scorecard` dict.
SCORECARD_METRICS = [
    {
        "key": "last_year_contributions",
        "label": "12mo Contributions",
        "detail": "contribution calendar",
        "format": "int_or_na",
        "accent": "CYAN",
        "icon": "fire",
    },
    {
        "key": "active_days_last_year",
        "label": "Active Days",
        "detail": "days shipped in last 12mo",
        "format": "int",
        "accent": "GREEN",
        "icon": "calendar",
    },
    {
        "key": "active_repos_7d",
        "label": "Active Repos (7d)",
        "detail": "pushed in last week",
        "format": "int",
        "accent": "CYAN",
        "icon": "commit",
    },
    {
        "key": "ci_coverage_pct",
        "label": "CI Coverage",
        "detail": "repos with pipelines",
        "format": "fixed_or_na",
        "digits": 1,
        "suffix": "%",
        "accent": "ORANGE",
        "icon": "ci_check",
    },
    {
        "key": "automation_workflows",
        "label": "CI Pipelines",
        "detail": "workflow files across repos",
        "format": "int",
        "accent": "BLUE",
        "icon": "workflow",
    },
    {
        "key": "releases_30d",
        "label": "Releases (30d)",
        "detail": "published in last month",
        "format": "int_or_na",
        "accent": "ORANGE",
        "icon": "release_tag",
    },
    {
        "key": "primary_lang_share_pct",
        "label": "Primary Language",
        "detail": "share of code by bytes",
        "format": "fixed",
        "digits": 1,
        "suffix": "%",
        "accent": "BLUE",
        "icon": "code",
    },
    {
        "key": "days_since_last_push",
        "label": "Last Push",
        "detail": "days since your most recent commit",
        "format": "fixed",
        "digits": 0,
        "suffix": "d",
        "accent": "GREEN",
        "icon": "clock",
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


# --- Machine-readable metric claims -------------------------------------------
# A card that repeats a published number carries the claim itself: metric key,
# the exact value it displays, the population scope, and the completeness status.
# The visible text and the declared display value are the same string, so a card
# can never drift from the JSON it repeats.

METRIC_CLAIM_KEY_ATTRIBUTE = "data-metric-key"
METRIC_CLAIM_VALUE_ATTRIBUTE = "data-metric-display-value"
METRIC_CLAIM_SCOPE_ATTRIBUTE = "data-metric-scope"
METRIC_CLAIM_STATUS_ATTRIBUTE = "data-metric-status"


# --- Field-specific qualification of retained partial values -------------------
# A partial family keeps its known value only where every registered visible
# consumer names that exact field's partial basis. A generic "partial" word in
# scope metadata is not disclosure: the reader sees the card, so the card says it.
#
# `line` is what a card renders. `disclosures` is what one visible line must
# actually mean, stated independently of that string: the field it is about, its
# partial status, and each meaning the retained number owes. Validation proves the
# meanings, never the string, so weakening the rendered line to a bare word cannot
# also weaken the proof that the line was a real qualification.

PARTIAL_QUALIFICATION_CONSUMERS: dict[str, dict[str, Any]] = {
    "active_repos_7d": {
        "line": "Active repos · Partial · known minimum · unknown pushes",
        "consumers": ("assets/builder_scorecard.svg",),
        "disclosures": (
            (
                "the active-repository field",
                ("active repos", "active repositories", "repository activity"),
            ),
            ("partial status", ("partial",)),
            ("the retained known minimum", ("known minimum", "minimum known")),
            (
                "the unobserved pushes behind it",
                ("unknown push", "unobserved push", "missing push"),
            ),
        ),
    },
    "ci_coverage_pct": {
        "line": "CI · Partial · known minimum · unknown repositories",
        "consumers": (
            "assets/builder_scorecard.svg",
            "assets/engineering_cadence.svg",
        ),
        "disclosures": (
            ("the CI coverage field", ("ci",)),
            ("partial status", ("partial",)),
            ("the retained known minimum", ("known minimum", "minimum known")),
            (
                "the unobserved repositories behind it",
                ("unknown repositor", "unobserved repositor", "missing repositor"),
            ),
        ),
    },
    "primary_lang_share_pct": {
        "line": "Language · Partial · observed bytes",
        "consumers": (
            "assets/builder_scorecard.svg",
            "assets/engineering_cadence.svg",
        ),
        "disclosures": (
            ("the language field", ("language",)),
            ("partial status", ("partial",)),
            ("the observed byte basis", ("observed bytes",)),
        ),
    },
}


def partial_qualification_line(metric_key: str) -> str:
    """The exact visible line a partial value owes its readers, or an empty string."""
    registered = PARTIAL_QUALIFICATION_CONSUMERS.get(metric_key)
    return str(registered["line"]) if registered else ""


def partial_qualification_consumers(metric_key: str) -> tuple[str, ...]:
    """The rendered surfaces that display this metric's known value."""
    registered = PARTIAL_QUALIFICATION_CONSUMERS.get(metric_key)
    return tuple(registered["consumers"]) if registered else ()


def partial_qualification_disclosures(
    metric_key: str,
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Each meaning one visible line must carry, independent of its wording."""
    registered = PARTIAL_QUALIFICATION_CONSUMERS.get(metric_key)
    if not registered:
        return ()
    return tuple(
        (str(meaning), tuple(str(phrase) for phrase in phrases))
        for meaning, phrases in registered.get("disclosures", ())
    )


# The visible source label. Fixture output is a legitimate local surface, but it
# never presents its values as a live provider observation.
SOURCE_PROVENANCE_LABELS = {
    "github-api": "GitHub API",
    "fixture": "fixture data",
}


def source_provenance_label(source_kind: Any) -> str:
    return SOURCE_PROVENANCE_LABELS.get(
        str(source_kind or ""), SOURCE_PROVENANCE_LABELS["github-api"]
    )


def gauge_display_value(value: Any) -> str:
    """The gauge centre label: one whole percent, or an honest n/a."""
    if value is None:
        return "n/a"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "n/a"
    return f"{round(numeric)}%"


def metric_claim(key: str, *, value: Any, scope: Any, status: Any) -> dict[str, Any]:
    """One published claim, shared by every surface that repeats the metric."""
    return {
        "metric_key": str(key),
        "value": value,
        "display_value": gauge_display_value(value),
        "scope": str(scope or ""),
        "status": str(status or ""),
    }


def metric_claim_group(claim: dict[str, Any] | None, inner_svg: str) -> str:
    """Wrap a rendered value in its machine-readable claim, when one exists."""
    if not claim or not claim.get("scope"):
        return inner_svg
    return (
        f'<g {METRIC_CLAIM_KEY_ATTRIBUTE}="{xml_escape(claim["metric_key"])}" '
        f'{METRIC_CLAIM_VALUE_ATTRIBUTE}="{xml_escape(claim["display_value"])}" '
        f'{METRIC_CLAIM_SCOPE_ATTRIBUTE}="{xml_escape(claim["scope"])}" '
        f'{METRIC_CLAIM_STATUS_ATTRIBUTE}="{xml_escape(claim["status"])}">'
        f"{inner_svg}</g>"
    )


def format_metric_value(value: Any, definition: dict[str, Any]) -> str:
    if type(definition) is not dict:
        return "n/a"
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

    if type(value) is not int or value < 0:
        return "n/a"
    groups = []
    remaining = value
    while remaining:
        remaining, group = divmod(remaining, 1000)
        groups.append(f"{group:03d}" if remaining else f"{group:d}")
    grouped = ",".join(reversed(groups)) if groups else "0"
    return f"{grouped}{suffix}"

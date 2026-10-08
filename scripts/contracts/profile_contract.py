"""Metric definitions, claim carriers, and formatting rules for profile outputs."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from scripts.rendering.svg_utils import xml_escape


# Workflow configuration describes files present at observed default-branch HEAD.
# These labels and display strings do not calculate an alternative aggregate.
AUTOMATION_REPOS_LABEL = "Workflow repos"
AUTOMATION_FILES_LABEL = "Workflow files"
AUTOMATION_ADOPTION_LABEL = "Repo adoption"
AUTOMATION_SCOPE = "Owned public + private nonfork repositories; profile excluded."
AUTOMATION_MEANING = (
    "GitHub workflow configuration at observed default-branch HEAD. "
    "Configuration does not imply successful runs."
)


def automation_display(automation: dict | None) -> dict[str, Any]:
    """Prepare honest display text once for SVG and browser consumers."""
    summary = automation if isinstance(automation, dict) else {}
    displays = {}
    for key in ("public", "private", "combined"):
        row = summary.get(key) or {}
        status = row.get("status", "unavailable")
        eligible = row.get("eligible_repos")
        if status == "unavailable":
            qualification = "Workflow · Unavailable · n/a"
        elif status == "partial" and eligible is None:
            qualification = "Workflow · Partial · observed subtotal · eligible inventory unknown"
        elif status == "partial":
            qualification = "Workflow · Partial · known minimum · unknown repositories"
        elif eligible == 0:
            qualification = "No eligible repositories"
        else:
            qualification = "Workflow observation complete"
        counts = {name: format_metric_value(row.get(name), {"format": "int_or_na"})
                  for name in ("configured_repos", "eligible_repos", "workflow_files",
                               "unknown_workflow_repos", "observed_eligible_repos")}
        displays[key] = {
            **counts,
            "status": str(status).title(),
            "qualification": qualification,
            "adoption": gauge_display_value(row.get("adoption_pct")),
            "gauge_detail": (f'{counts["configured_repos"]}/{counts["eligible_repos"]} repos'
                             if eligible else "No eligible" if eligible == 0 else "Unknown total"),
        }
    return {"scope": AUTOMATION_SCOPE, "meaning": AUTOMATION_MEANING, **displays}


def automation_description(automation: dict | None) -> str:
    display = automation_display(automation)
    return " ".join((display["scope"], display["meaning"], display["combined"]["qualification"]))


CONTRIBUTION_WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
CONTRIBUTION_RHYTHM_REASONS = {
    "calendar_unavailable": "Calendar data unavailable",
    "no_dated_days": "No dated calendar observations",
    "invalid_calendar": "Calendar dates or counts could not be verified",
    "observation_unavailable": "Current calendar observation could not be verified",
}
CONTRIBUTION_RHYTHM_SCOPE = (
    "Counts reported by the GitHub contribution calendar. Private contributions are included "
    "only when returned; no public/private split or coding hours are inferred."
)


def contribution_rhythm_unavailable(reason: str = "calendar_unavailable") -> dict[str, Any]:
    """Unavailable evidence carries no numerical distribution."""
    if reason not in CONTRIBUTION_RHYTHM_REASONS:
        raise ValueError("unknown contribution rhythm reason")
    return {
        "status": "unavailable", "reason": reason,
        "source": "github_contribution_calendar", "unit": "contributions", "bucket": "weekday",
        "timezone": "UTC", "completeness": "unknown", "window_start": None, "window_end": None,
        "days_observed": None, "total": None, "weekdays": [], "last_day_in_progress": None,
    }


def contribution_rhythm_errors(rhythm: object) -> list[str]:
    """Validate weekday counts and their date-interval coverage before display."""
    if not isinstance(rhythm, dict):
        return ["contribution rhythm missing"]
    if any(rhythm.get(key) != value for key, value in (
        ("source", "github_contribution_calendar"), ("unit", "contributions"),
        ("bucket", "weekday"), ("timezone", "UTC"),
    )) or rhythm.get("completeness") not in ("known", "unknown"):
        return ["invalid contribution rhythm meaning"]
    if rhythm.get("status") == "unavailable":
        expected = contribution_rhythm_unavailable()
        return ([] if rhythm.get("reason") in tuple(CONTRIBUTION_RHYTHM_REASONS)
                and all(rhythm.get(key) == value for key, value in expected.items() if key != "reason")
                else ["unavailable contribution rhythm contains values"])
    try:
        if rhythm.get("status") != "available" or rhythm.get("reason") != "dated_calendar":
            raise ValueError("invalid status")
        first, last = [date.fromisoformat(rhythm[key]) for key in ("window_start", "window_end")]
        if first.isoformat() != rhythm["window_start"] or last.isoformat() != rhythm["window_end"] or first > last:
            raise ValueError("invalid window")
        total, observed = rhythm["total"], rhythm["days_observed"]
        size = (last - first).days + 1
        if type(total) is not int or total < 0 or type(observed) is not int or observed != size:
            raise ValueError("invalid totals")
        progress = rhythm["last_day_in_progress"]
        if ((rhythm["completeness"] == "known" and type(progress) is not bool)
                or (rhythm["completeness"] == "unknown" and progress is not None)):
            raise ValueError("unsupported day completion")
        rows = rhythm["weekdays"]
        if not isinstance(rows, list) or len(rows) != 7:
            raise ValueError("invalid weekdays")
        for i, (name, row) in enumerate(zip(CONTRIBUTION_WEEKDAYS, rows)):
            coverage = size // 7 + int((i - first.weekday()) % 7 < size % 7)
            if (not isinstance(row, dict) or row.get("weekday") != name
                    or type(row.get("contributions")) is not int or row["contributions"] < 0
                    or type(row.get("days_observed")) is not int or row["days_observed"] != coverage
                    or coverage == 0 and row["contributions"] != 0):
                raise ValueError("invalid weekday counts")
        if sum(row["contributions"] for row in rows) != total:
            raise ValueError("weekday sum disagrees")
    except (KeyError, ValueError, TypeError):
        return ["invalid contribution rhythm dates or counts"]
    return []


def contribution_rhythm_display(rhythm: object) -> dict[str, Any]:
    """Shared wording and formatted rows; no second calculation of contributions."""
    if contribution_rhythm_errors(rhythm):
        rhythm = contribution_rhythm_unavailable("invalid_calendar")
    available = rhythm["status"] == "available"
    display = {
        "available": available, "title": "Contribution Rhythm", "subtitle": "Contributions by weekday",
        "scope": CONTRIBUTION_RHYTHM_SCOPE,
        "explanation": ("These bars show contribution totals, not daily averages. "
                        "Weekdays may occur a different number of times in this date window."),
        "coverage_summary": "", "caption": "", "qualification": "", "message": "", "rows": [],
    }
    if not available:
        return {**display, "message": "Contribution rhythm unavailable",
                "qualification": CONTRIBUTION_RHYTHM_REASONS[rhythm["reason"]]}
    qualification = ("Completeness unknown" if rhythm["completeness"] == "unknown" else
                     "Last date may be in progress" if rhythm["last_day_in_progress"] else "")
    return {
        **display,
        "caption": f'{rhythm["window_start"]} – {rhythm["window_end"]} · UTC calendar dates',
        "qualification": qualification,
        "message": "No contributions in the observed dates" if rhythm["total"] == 0 else "",
        "coverage_summary": "Observed dates — " + "; ".join(
            f'{row["weekday"]}: {row["days_observed"]}' for row in rhythm["weekdays"]) + ".",
        "rows": [{**row, "count_text": f'{row["contributions"]:,}'} for row in rhythm["weekdays"]],
    }


def contribution_trend_errors(trend: object) -> list[str]:
    """Validate the small public dated-series shape before a consumer trusts it."""
    if not isinstance(trend, dict):
        return ["dated contribution trend missing"]
    if any(trend.get(key) != value for key, value in (
        ("unit", "contributions"), ("bucket", "iso_week"),
        ("week_start_day", "Monday"), ("timezone", "UTC"),
    )) or trend.get("completeness") not in {"known", "unknown"}:
        return ["invalid contribution trend meaning"]
    points = trend.get("points")
    if trend.get("status") == "unavailable":
        return ([] if points == [] and trend.get("window_start") is None
                and trend.get("window_end") is None else ["unavailable trend contains values"])
    if trend.get("status") != "available" or not isinstance(points, list) or not 1 <= len(points) <= 12:
        return ["invalid contribution trend points"]
    try:
        previous_end = None
        previous_monday = None
        for point in points:
            start, end, first, last = [date.fromisoformat(point[key]) for key in (
                "week_start", "week_end", "observed_start", "observed_end")]
            if any(value.isoformat() != point[key] for value, key in zip(
                (start, end, first, last), ("week_start", "week_end", "observed_start", "observed_end"))):
                raise ValueError("noncanonical date")
            count, size, partial = point["contributions"], point["days_observed"], point["partial"]
            if (start.weekday() != 0 or end != start + timedelta(days=6)
                    or not start <= first <= last <= end
                    or type(size) is not int or size != (last - first).days + 1
                    or type(count) is not int or count < 0 or type(partial) is not bool
                    or (size != 7 or trend["completeness"] == "unknown") and not partial
                    or previous_end is not None and first != previous_end + timedelta(days=1)
                    or previous_monday is not None and start != previous_monday + timedelta(days=7)):
                raise ValueError("inconsistent point")
            previous_end, previous_monday = last, start
        if (trend.get("window_start") != points[0]["observed_start"]
                or trend.get("window_end") != points[-1]["observed_end"]):
            raise ValueError("inconsistent window")
    except (KeyError, ValueError, TypeError):
        return ["invalid contribution trend dates or counts"]
    return []


def contribution_trend_display(trend: object) -> dict[str, Any]:
    """Shared wording, not an independent contribution calculator."""
    if contribution_trend_errors(trend) or trend["status"] != "available":
        return {"available": False, "title": "Contribution trend unavailable",
                "qualification": "Dated calendar data required", "values": []}
    start, end = (date.fromisoformat(trend[key]) for key in ("window_start", "window_end"))
    # Explicit English month names avoid host-locale-dependent public captions.
    months = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
    first = f"{months[start.month - 1]} {start.day}" + (f", {start.year}" if start.year != end.year else "")
    last = f"{months[end.month - 1]} {end.day}, {end.year}"
    points = trend["points"]
    values = [point["contributions"] for point in points]
    completeness = ("completeness unknown" if trend["completeness"] == "unknown" else
                    "partial weeks included" if any(point["partial"] for point in points) else "complete weeks")
    description = "; ".join(
        f'{point["observed_start"]} to {point["observed_end"]}: {point["contributions"]} contributions'
        + (" (partial)" if point["partial"] else " (complete)") for point in points
    )
    return {"available": True, "title": "Weekly contributions", "values": values,
            "peak": f"Peak {max(values):,} contributions/week",
            "window": f"{first} – {last} · {len(points)} {'week' if len(points) == 1 else 'weeks'}",
            "qualification": "Mon–Sun · UTC · " + completeness,
            "description": "UTC contribution calendar. " + description}


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
        "label": AUTOMATION_ADOPTION_LABEL,
        "detail": "owned public + private nonfork repositories",
        "format": "fixed_or_na",
        "digits": 1,
        "suffix": "%",
        "accent": "ORANGE",
        "icon": "ci_check",
    },
    {
        "key": "automation_workflows",
        "label": AUTOMATION_FILES_LABEL,
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
        "label": AUTOMATION_REPOS_LABEL,
        "dashboard_label": AUTOMATION_REPOS_LABEL,
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
        "line": "Workflow · Partial · known minimum · unknown repositories",
        "consumers": (
            "assets/builder_scorecard.svg",
            "assets/engineering_cadence.svg",
        ),
        "disclosures": (
            ("the workflow adoption field", ("workflow", "repo adoption", "ci")),
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

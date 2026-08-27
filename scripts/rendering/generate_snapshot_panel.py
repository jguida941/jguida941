"""Build the Raw Data Snapshot card.

Power BI information architecture (DESIGN_SPEC): one dominant KPI (12-month
contributions) top-left, a curated set of <=4 secondary metric tiles (not the
full raw-row dump), and a pipeline-status row where each source's health reads
by a distinct icon SHAPE + label (never hue alone). An honest empty state
renders when there is no snapshot data.
"""

from __future__ import annotations

from scripts.core.config import SPACE, SVG_WIDTH, TEXT_DIM
from scripts.rendering.components import (
    empty_state,
    metric_tile,
    primary_kpi,
    section_header,
    status_chip,
    text,
)
from scripts.rendering.glass_kit import chip_width, glass_panel
from scripts.rendering.svg_utils import truncate, xml_escape

# Neutral monochrome icon per snapshot metric key (icon color is set by the kit).
_KEY_ICON = {
    "last_year_contributions": "calendar",
    "public_scope_commits": "commit",
    "total_repos": "code",
    "public_forks": "fork",
    "private_owned_repos": "lock",
    "total_stars": "star",
    "languages_count": "globe",
    "prs_merged": "pr_merged",
    "releases": "release_tag",
    "ci_repos": "workflow",
    "streak_days": "fire",
}

# Curated secondary tiles (in priority order) — the card shows at most four.
_SECONDARY_KEYS = (
    "public_scope_commits",
    "total_repos",
    "private_owned_repos",
    "total_stars",
    "languages_count",
    "prs_merged",
)

# Short, human tile labels that FIT the tile (the snapshot rows carry long
# audit-grade names like "Public Repo Commits (Owned Non-Fork)"; a tile is a
# glance, not an audit row, so it gets a concise noun — never a clipped one).
_TILE_LABEL = {
    "public_scope_commits": "Commits",
    "total_repos": "Public Repos",
    "private_owned_repos": "Private",
    "total_stars": "Stars",
    "languages_count": "Languages",
    "prs_merged": "PRs Merged",
    "public_forks": "Forks",
    "ci_repos": "CI Repos",
    "releases": "Releases",
    "streak_days": "Streak",
}

_STATUS_DISPLAY = {
    "ok": "OK", "pass": "OK", "passing": "OK", "healthy": "OK", "complete": "OK",
    "partial": "Partial", "fallback": "Fallback", "degraded": "Degraded", "limited": "Limited",
    "empty": "None", "none": "None", "missing": "Missing", "unknown": "Unknown",
    "exact": "Exact", "unavailable": "Unavailable",
    "error": "Error", "failed": "Failed", "fail": "Failed",
}


def _status_name(status: str) -> str:
    """Map a pipeline status word to a design-system status (DESIGN_SPEC 3.6)."""
    n = str(status or "").strip().lower()
    if n in {"ok", "pass", "passing", "healthy", "complete", "available", "exact"}:
        return "success"
    if n in {
        "warn",
        "warning",
        "partial",
        "degraded",
        "fallback",
        "limited",
        "unavailable",
    }:
        return "warning"
    if n in {"error", "failed", "fail", "missing"}:
        return "danger"
    return "neutral"


def _status_display(status: str) -> str:
    n = str(status or "").strip().lower()
    return _STATUS_DISPLAY.get(n, (status or "n/a").strip().title())


def _provider_evidence_label(
    name: str,
    status: object,
    carrier: object,
) -> str:
    """Describe provider evidence without promoting a fallback to exact truth."""
    status_text = str(status or "")
    parts = [name, _status_display(status_text)]
    if not isinstance(carrier, dict) or status_text.casefold() not in {
        "fallback",
        "partial",
    }:
        return " · ".join(parts)

    if name == "PRs" and (
        carrier.get("source_metric_id")
        == "merged_prs_public_visible_population"
        or carrier.get("population_id")
        == "owned-public-repositories-visible-to-public-pr-search"
    ):
        parts.append("Public Scope")
    elif name == "Contributions" and (
        carrier.get("source_mode") == "previous_snapshot"
        or carrier.get("completion_reason") == "previous_snapshot"
    ):
        parts.append("Previous")
    return " · ".join(parts)


def generate(
    snapshot_rows: list,
    data_quality: dict,
    data_scope: dict | None = None,
    output_path: str = "assets/raw_snapshot.svg",
) -> str:
    width = SVG_WIDTH
    pad = 28
    rows = [r for r in (snapshot_rows or []) if isinstance(r, dict)]

    header_svg, content_top = section_header(
        pad, 46, "Raw Data Snapshot", width=width, eyebrow="Live GitHub Data", pad=pad
    )

    # Honest empty state: no snapshot rows -> one explanatory line, no fabricated tiles.
    if not rows:
        height = int(content_top + 92)
        parts = [glass_panel(width, height), header_svg]
        parts.append(
            empty_state(
                width / 2, content_top + 48, "No snapshot data available", icon_name="code"
            )
        )
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">{"".join(parts)}</svg>'
        )
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg)
        return output_path

    by_key = {str(r.get("key", "")): r for r in rows}
    kpi_row = by_key.get("last_year_contributions") or rows[0]
    secondary = [
        by_key[k] for k in _SECONDARY_KEYS if k in by_key and by_key[k] is not kpi_row
    ][:4]
    if not secondary:
        secondary = [r for r in rows if r is not kpi_row][:4]

    quality = data_quality if isinstance(data_quality, dict) else {}
    metric_statuses = quality.get("metric_statuses", {})
    if not isinstance(metric_statuses, dict):
        metric_statuses = {}
    status_items = [
        ("CI", quality.get("ci_status")),
        ("Commits", quality.get("commits_status")),
        ("Releases", quality.get("releases_status")),
        ("Events", quality.get("events_status")),
    ]
    non_exact_metrics = quality.get("non_exact_metrics", {})
    if not isinstance(non_exact_metrics, dict):
        non_exact_metrics = {}
    provider_status_items = [
        (
            _provider_evidence_label(
                "PRs",
                quality.get("prs_status"),
                non_exact_metrics.get("prs_merged"),
            ),
            quality.get("prs_status"),
        ),
        (
            _provider_evidence_label(
                "Contributions",
                quality.get("contributions_status"),
                non_exact_metrics.get("last_year_contributions"),
            ),
            quality.get("contributions_status"),
        ),
    ]
    family_status_items = [
        ("Private", quality.get("private_aggregate_status")),
        ("Push", metric_statuses.get("active_repos_7d")),
        ("Automation", metric_statuses.get("automation_repos")),
        ("Language", metric_statuses.get("top_languages")),
    ]
    scope = data_scope if isinstance(data_scope, dict) else {}
    population = str(scope.get("repos_included") or "repository scope unavailable")
    evidence_notes = []
    ci_family_status = str(metric_statuses.get("automation_repos", "")).casefold()
    if ci_family_status == "partial":
        evidence_notes.append(
            str(quality.get("ci_note") or "CI Partial: known minimum; unknown repositories remain.")
        )
    elif ci_family_status == "unavailable":
        evidence_notes.append("CI Unavailable: no usable repository observation.")
    language_status = str(metric_statuses.get("top_languages", "")).casefold()
    if language_status == "partial":
        evidence_notes.append(
            str(quality.get("language_note") or "Language Partial: observed bytes only.")
        )
    elif language_status == "unavailable":
        evidence_notes.append("Language Unavailable: no usable byte observation.")

    # --- geometry ---
    tile_y = content_top + 24
    tile_h = 66
    status_label_y = tile_y + tile_h + 34
    chips_y = status_label_y + 12
    chip_h = 24
    provider_label_y = chips_y + chip_h + 28
    provider_chips_y = provider_label_y + 12
    family_label_y = provider_chips_y + chip_h + 28
    family_chips_y = family_label_y + 12
    scope_y = family_chips_y + chip_h + 22
    notes_start_y = scope_y + 18
    height = int(notes_start_y + len(evidence_notes) * 16 + 18)

    parts: list[str] = [glass_panel(width, height), header_svg]

    # PrimaryKpiCard top-left.
    kpi_y = content_top + 58
    parts.append(
        primary_kpi(
            pad,
            kpi_y,
            value=xml_escape(str(kpi_row.get("display_value", "n/a"))),
            label="contributions",
            sublabel="last 12 months",
        )
    )
    kpi_w = 244
    parts.append(
        f'<rect x="{pad + kpi_w:g}" y="{content_top + 6:g}" width="1" '
        f'height="84" fill="{TEXT_DIM}" fill-opacity="0.16"/>'
    )

    # Curated secondary metric tiles (neutral icons).
    grid_x = pad + kpi_w + SPACE["xl"]
    cols = max(len(secondary), 1)
    gap = SPACE["md"]
    col_w = (width - pad - grid_x - gap * (cols - 1)) / cols
    for i, row in enumerate(secondary):
        x = grid_x + i * (col_w + gap)
        parts.append(
            metric_tile(
                x,
                tile_y,
                col_w,
                tile_h,
                value=xml_escape(str(row.get("display_value", "n/a"))),
                label=_TILE_LABEL.get(
                    str(row.get("key", "")),
                    truncate(xml_escape(str(row.get("label", "Metric"))), 14),
                ),
                icon_name=_KEY_ICON.get(str(row.get("key", "")), "code"),
            )
        )

    # Pipeline status row: status by distinct icon shape + label.
    parts.append(text("PIPELINE STATUS", pad, status_label_y, token="eyebrow", color=TEXT_DIM, tracking=1.2))
    cx = pad
    for name, status in status_items:
        label = f"{name} · {_status_display(status)}"
        parts.append(status_chip(cx, chips_y, label=label, status=_status_name(status), height=chip_h))
        cx += chip_width(label, icon=True) + SPACE["md"]

    parts.append(
        text(
            "PROVIDER EVIDENCE",
            pad,
            provider_label_y,
            token="eyebrow",
            color=TEXT_DIM,
            tracking=1.2,
        )
    )
    cx = pad
    for label, status in provider_status_items:
        parts.append(
            status_chip(
                cx,
                provider_chips_y,
                label=label,
                status=_status_name(status),
                height=chip_h,
            )
        )
        cx += chip_width(label, icon=True) + SPACE["md"]

    parts.append(
        text(
            "REPOSITORY EVIDENCE",
            pad,
            family_label_y,
            token="eyebrow",
            color=TEXT_DIM,
            tracking=1.2,
        )
    )
    cx = pad
    for name, status in family_status_items:
        label = f"{name} · {_status_display(status)}"
        parts.append(
            status_chip(
                cx,
                family_chips_y,
                label=label,
                status=_status_name(status),
                height=chip_h,
            )
        )
        cx += chip_width(label, icon=True) + SPACE["md"]

    parts.append(
        text(
            f"Observed population · {xml_escape(population)}",
            pad,
            scope_y,
            token="caption",
            color=TEXT_DIM,
        )
    )
    for index, note in enumerate(evidence_notes):
        parts.append(
            text(
                xml_escape(truncate(note, 112)),
                pad,
                notes_start_y + index * 16,
                token="caption",
                color=TEXT_DIM,
            )
        )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">{"".join(parts)}</svg>'
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    return output_path

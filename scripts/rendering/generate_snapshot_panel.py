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
    "error": "Error", "failed": "Failed", "fail": "Failed",
}


def _status_name(status: str) -> str:
    """Map a pipeline status word to a design-system status (DESIGN_SPEC 3.6)."""
    n = str(status or "").strip().lower()
    if n in {"ok", "pass", "passing", "healthy", "complete", "available"}:
        return "success"
    if n in {"warn", "warning", "partial", "degraded", "fallback", "limited"}:
        return "warning"
    if n in {"error", "failed", "fail", "missing"}:
        return "danger"
    return "neutral"


def _status_display(status: str) -> str:
    n = str(status or "").strip().lower()
    return _STATUS_DISPLAY.get(n, (status or "n/a").strip().title())


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
    status_items = [
        ("CI", quality.get("ci_status")),
        ("Commits", quality.get("commits_status")),
        ("Releases", quality.get("releases_status")),
        ("Events", quality.get("events_status")),
    ]

    # --- geometry ---
    tile_y = content_top + 24
    tile_h = 66
    status_label_y = tile_y + tile_h + 34
    chips_y = status_label_y + 12
    chip_h = 24
    height = int(chips_y + chip_h + 22)

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

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">{"".join(parts)}</svg>'
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    return output_path

"""Build the Builder Scorecard card.

Power BI information architecture (DESIGN_SPEC): one dominant KPI (12-month
contributions) top-left, a supporting grid of uniform secondary metric tiles
with neutral monochrome icons, and CI coverage rendered as a token-labeled donut
gauge (the one sanctioned circular chart — comparisons use the tiles). An honest
empty state renders when there is no scorecard data.
"""

from __future__ import annotations

from scripts.contracts.profile_contract import SCORECARD_METRICS, format_metric_value
from scripts.core.config import SPACE, SVG_WIDTH, TEXT, TEXT_DIM
from scripts.rendering.components import (
    donut_gauge,
    empty_state,
    metric_tile,
    primary_kpi,
    section_header,
    text,
)
from scripts.rendering.glass_kit import glass_panel, glass_tile

# Neutral monochrome icon per scorecard metric key (icon color is set by the kit).
ICON_BY_KEY = {
    "last_year_contributions": "calendar",
    "active_days_last_year": "fire",
    "active_repos_7d": "commit",
    "ci_coverage_pct": "ci_check",
    "automation_workflows": "workflow",
    "releases_30d": "release_tag",
    "primary_lang_share_pct": "code",
    "median_days_since_push": "clock",
}

# The single dominant KPI, and the curated supporting grid (CI coverage = gauge).
_KPI_KEY = "last_year_contributions"
_GRID_KEYS = (
    "active_days_last_year",
    "active_repos_7d",
    "ci_coverage_pct",
    "automation_workflows",
    "releases_30d",
    "primary_lang_share_pct",
)
_DEFS = {m["key"]: m for m in SCORECARD_METRICS}


def _fmt(scorecard: dict, key: str) -> str:
    defn = _DEFS.get(key, {"key": key})
    return str(format_metric_value(scorecard.get(key), defn))


def _gauge_cell(x: float, y: float, w: float, h: float, *, value: float, detail: str) -> str:
    """A grid cell whose value is a single goal gauge (DESIGN_SPEC 3.9)."""
    parts = [glass_tile(x, y, w, h)]
    cx = x + 32
    cy = y + h / 2
    parts.append(donut_gauge(cx, cy, value=float(value or 0), radius=24, stroke=6))
    parts.append(text("CI coverage", x + 64, y + h / 2 - 2, token="caption", color=TEXT))
    parts.append(text(detail, x + 64, y + h / 2 + 14, token="caption", color=TEXT_DIM))
    return "".join(parts)


def generate(
    scorecard: dict,
    output_path: str = "assets/builder_scorecard.svg",
    tiles: list | None = None,
    primary_language: str = "",
) -> str:
    _ = tiles  # back-compat; the card is driven by the scorecard + metric contract
    data = scorecard if isinstance(scorecard, dict) else {}
    width = SVG_WIDTH
    pad = 28

    header_svg, content_top = section_header(
        pad,
        46,
        "Builder Scorecard",
        width=width,
        eyebrow="GitHub Signals · Last 12 Months",
        right_text="GitHub API",
        pad=pad,
    )

    # Honest empty state: no real signal -> one explanatory line, no fabricated tiles.
    if not any(data.get(k) for k in (_KPI_KEY, *_GRID_KEYS)):
        empty_header, _ = section_header(
            pad, 46, "Builder Scorecard", width=width, eyebrow="GitHub Signals", pad=pad
        )
        height = int(content_top + 92)
        parts = [glass_panel(width, height), empty_header]
        parts.append(
            empty_state(width / 2, content_top + 48, "No builder signals available yet", icon_name="workflow")
        )
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">{"".join(parts)}</svg>'
        )
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg)
        return output_path

    # --- geometry (KPI top-left + 3x2 supporting grid) ---
    cols, row_gap = 3, SPACE["md"]
    tile_h = 66
    kpi_w = 244
    grid_x = pad + kpi_w + SPACE["xl"]
    gap = SPACE["md"]
    col_w = (width - pad - grid_x - gap * (cols - 1)) / cols
    rows = 2
    grid_bottom = content_top + rows * tile_h + (rows - 1) * row_gap
    height = int(grid_bottom + 30)

    parts: list[str] = [glass_panel(width, height), header_svg]

    # PrimaryKpiCard: contributions, top-left.
    kpi_y = content_top + 58
    parts.append(
        primary_kpi(
            pad,
            kpi_y,
            value=_fmt(data, _KPI_KEY),
            label="contributions",
            sublabel="last 12 months",
        )
    )
    parts.append(
        f'<rect x="{pad + kpi_w:g}" y="{content_top + 6:g}" width="1" '
        f'height="{grid_bottom - content_top - 6:g}" fill="{TEXT_DIM}" fill-opacity="0.16"/>'
    )

    # Supporting grid: 5 uniform metric tiles + 1 donut gauge (CI coverage).
    for i, key in enumerate(_GRID_KEYS):
        col, row = i % cols, i // cols
        x = grid_x + col * (col_w + gap)
        y = content_top + row * (tile_h + row_gap)
        defn = _DEFS.get(key, {})
        if key == "ci_coverage_pct":
            # The gauge cell shares its row with a donut, so its detail line gets a
            # concise context phrase that fits the cell (the metric's long-form
            # "repos with pipelines" detail belongs to the wide README table, not here).
            parts.append(
                _gauge_cell(x, y, col_w, tile_h, value=data.get(key) or 0, detail="of public repos")
            )
        else:
            # The primary-language tile reads clearest when the tile names the
            # language itself ("Python / 50.0%") rather than the generic noun.
            label = str(defn.get("label", key))
            if key == "primary_lang_share_pct" and primary_language:
                label = primary_language
            parts.append(
                metric_tile(
                    x, y, col_w, tile_h,
                    value=_fmt(data, key),
                    label=label,
                    icon_name=ICON_BY_KEY.get(key, "code"),
                )
            )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">{"".join(parts)}</svg>'
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    return output_path

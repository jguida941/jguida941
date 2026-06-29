"""Build the Engineering Cadence card.

Power BI information architecture (DESIGN_SPEC): active days is the one dominant
KPI top-left, the weekly cadence renders as a restrained TrendPanel, CI coverage
as a labeled DonutGauge, and the remaining signals as uniform secondary metric
tiles. An honest empty state renders when there is no engineering data.
"""

from __future__ import annotations

from scripts.core.config import SPACE, SVG_WIDTH, TEXT, TEXT_DIM
from scripts.rendering.components import (
    donut_gauge,
    empty_state,
    metric_tile,
    primary_kpi,
    section_header,
    text,
    trend_panel,
)
from scripts.rendering.glass_kit import glass_panel, glass_tile
from scripts.rendering.svg_utils import fmt_int


def _int(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _gauge_cell(x: float, y: float, w: float, h: float, *, value: float, detail: str) -> str:
    parts = [glass_tile(x, y, w, h)]
    parts.append(donut_gauge(x + 32, y + h / 2, value=float(value or 0), radius=24, stroke=6))
    parts.append(text("CI coverage", x + 64, y + h / 2 - 2, token="caption", color=TEXT))
    parts.append(text(detail, x + 64, y + h / 2 + 14, token="caption", color=TEXT_DIM))
    return "".join(parts)


def generate(engineering: dict, output_path: str = "assets/engineering_cadence.svg") -> str:
    data = engineering if isinstance(engineering, dict) else {}
    cadence = [float(v) for v in (data.get("weekly_cadence") or []) if v is not None]
    active_days = _int(data.get("active_days_last_year"))
    workflows = _int(data.get("automation_workflows"))
    automation_repos = _int(data.get("automation_repos"))
    primary_share = float(data.get("primary_lang_share_pct") or 0.0)
    langs_over_5 = _int(data.get("languages_over_5pct"))
    public_total = _int(data.get("public_repos_total"))
    public_nonfork = _int(data.get("public_nonfork_repos"))
    private_total = data.get("private_repos_total")
    private_total = _int(private_total) if private_total is not None else None

    ci_pct = automation_repos / max(public_nonfork, 1) * 100.0

    width = SVG_WIDTH
    pad = 28

    header_svg, content_top = section_header(
        pad, 46, "Engineering Cadence", width=width,
        eyebrow="Workflow Analytics", right_text="automation-first", pad=pad,
    )

    # Honest empty state.
    if not any((cadence, active_days, workflows, public_total, private_total)):
        empty_header, _ = section_header(
            pad, 46, "Engineering Cadence", width=width, eyebrow="Workflow Analytics", pad=pad
        )
        height = int(content_top + 92)
        parts = [glass_panel(width, height), empty_header]
        parts.append(empty_state(width / 2, content_top + 48, "No engineering activity recorded", icon_name="workflow"))
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">{"".join(parts)}</svg>'
        )
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg)
        return output_path

    # --- geometry ---
    kpi_w = 200
    gap = SPACE["md"]
    tile_h = 76
    row2_y = content_top + 116
    height = int(row2_y + tile_h + 30)

    parts: list[str] = [glass_panel(width, height), header_svg]

    # Row 1: KPI (active days) + weekly-cadence TrendPanel.
    parts.append(
        primary_kpi(
            pad, content_top + 58,
            value=fmt_int(active_days), label="active days", sublabel="last 12 months",
        )
    )
    parts.append(
        f'<rect x="{pad + kpi_w:g}" y="{content_top + 6:g}" width="1" height="90" '
        f'fill="{TEXT_DIM}" fill-opacity="0.16"/>'
    )
    trend_x = pad + kpi_w + SPACE["xl"]
    trend_w = width - pad - trend_x
    peak = f"peak {fmt_int(int(max(cadence)))} / wk" if cadence else None
    parts.append(
        trend_panel(
            trend_x, content_top + 18, trend_w, 80,
            series=cadence, axis_label="weekly commits", peak_label=peak, uid="eng-spark",
        )
    )

    # Row 2: CI-coverage gauge + 3 secondary metric tiles.
    cols, gap = 4, SPACE["md"]
    col_w = (width - pad * 2 - gap * (cols - 1)) / cols
    parts.append(
        _gauge_cell(pad, row2_y, col_w, tile_h, value=ci_pct, detail=f"{fmt_int(automation_repos)} repos automated")
    )
    parts.append(
        metric_tile(
            pad + (col_w + gap), row2_y, col_w, tile_h,
            value=fmt_int(workflows), label="CI pipelines",
            caption=f"{fmt_int(automation_repos)} repos", icon_name="workflow",
        )
    )
    parts.append(
        metric_tile(
            pad + (col_w + gap) * 2, row2_y, col_w, tile_h,
            value=fmt_int(public_total), label="public repos",
            caption=(f"{fmt_int(private_total)} private" if private_total is not None else "owned"),
            icon_name="globe",
        )
    )
    parts.append(
        metric_tile(
            pad + (col_w + gap) * 3, row2_y, col_w, tile_h,
            value=f"{round(primary_share)}%", label="primary language",
            caption=f"{fmt_int(langs_over_5)} langs > 5%", icon_name="code",
        )
    )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">{"".join(parts)}</svg>'
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    return output_path

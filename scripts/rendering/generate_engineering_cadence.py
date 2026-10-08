"""Build the Engineering Cadence card.

Power BI information architecture (DESIGN_SPEC): active days is the one dominant
KPI top-left, the dated contributions render on a zero-based weekly chart, CI coverage
as a labeled DonutGauge, and the remaining signals as uniform secondary metric
tiles. An honest empty state renders when there is no engineering data.
"""

from __future__ import annotations

from datetime import date

from scripts.contracts.profile_contract import (
    AUTOMATION_REPOS_LABEL, AUTOMATION_FILES_LABEL, AUTOMATION_ADOPTION_LABEL,
    AUTOMATION_SCOPE, AUTOMATION_MEANING,
    automation_description, automation_display, contribution_trend_display,
)

from scripts.contracts.profile_contract import metric_claim_group
from scripts.core.config import BG_DARK, CYAN, SPACE, SVG_WIDTH, TEXT, TEXT_DIM
from scripts.rendering.components import (
    donut_gauge,
    empty_state,
    metric_tile,
    primary_kpi,
    section_header,
    text,
)
from scripts.rendering.glass_kit import glass_panel, glass_tile
from scripts.rendering.svg_utils import fmt_int, xml_escape


def _int(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _gauge_cell(
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    value: float,
    detail: str,
    display_value: str | None = None,
) -> str:
    parts = [glass_tile(x, y, w, h)]
    parts.append(
        donut_gauge(
            x + 33,
            y + h / 2,
            value=float(value or 0),
            label=display_value,
            radius=21.5,
            stroke=4,
            label_size=12,
        )
    )
    parts.append(text(AUTOMATION_ADOPTION_LABEL, x + 69, y + h / 2 - 2, token="caption", color=TEXT))
    parts.append(text(detail, x + 69, y + h / 2 + 14, token="caption", color=TEXT_DIM))
    return "".join(parts)


def _contribution_chart(trend: dict, points: list[dict]) -> str:
    """Draw the dated series against zero; missing weeks never become intervals."""
    parts = ['<g data-series="weekly-contributions">']
    parts.append(text(xml_escape(trend["title"]), 252, 108, token="body", color=TEXT_DIM))
    if trend["available"]:
        parts.append(f'<desc>{xml_escape(trend["description"])}</desc>')
        values = trend["values"]
        required = max(1, (max(values) + 2) // 3)
        magnitude = 1
        while 10 * magnitude < required:
            magnitude *= 10
        step = next(multiplier * magnitude for multiplier in (1, 2, 5, 10)
                    if multiplier * magnitude >= required)
        top = 3 * step
        coordinates = [(546 if len(values) == 1 else 312 + index * 468 / (len(values) - 1),
                        272 - value * 112 / top) for index, value in enumerate(values)]
        for tick in (0, step, 2 * step, top):
            y = 272 - tick * 112 / top
            parts.append(f'<line x1="312" x2="780" y1="{y:.2f}" y2="{y:.2f}" '
                         f'stroke="{TEXT_DIM}" stroke-opacity="0.18" stroke-width="1"/>')
            label = str(tick)
            if len(label) > 6:
                coefficient = label.rstrip("0")
                label = f"{coefficient}e{len(label) - len(coefficient)}"
            parts.append(text(label, 300, y + 4.76, token="body", color=TEXT_DIM,
                              anchor="end").replace("<text ", '<text data-role="y-tick" ', 1))
        if len(values) >= 2:
            line_points = " ".join(f"{x:.2f},{y:.2f}" for x, y in coordinates)
            parts.append(f'<linearGradient id="eng-contribution-area" x1="0" y1="0" x2="0" y2="1">'
                         f'<stop offset="0%" stop-color="{CYAN}" stop-opacity="0.16"/>'
                         f'<stop offset="100%" stop-color="{CYAN}" stop-opacity="0"/></linearGradient>')
            parts.append(f'<polygon data-role="trend-area" points="312,272 {line_points} 780,272" '
                         'fill="url(#eng-contribution-area)"/>')
            parts.append(f'<polyline data-role="trend-line" points="{line_points}" '
                         f'fill="none" stroke="{CYAN}" stroke-width="2.5"/>')
        for (x, y), point in zip(coordinates, points):
            fill = BG_DARK if point["partial"] else CYAN
            parts.append(f'<circle data-role="week-point" cx="{x:.2f}" cy="{y:.2f}" r="3" '
                         f'fill="{fill}" stroke="{CYAN}" stroke-width="1.5"/>')
        months = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
        for index in sorted({0, (len(points) - 1) // 2, len(points) - 1}):
            day = date.fromisoformat(points[index]["week_start"])
            label = f"{months[day.month - 1]} {day.day}"
            parts.append(text(label, coordinates[index][0], 296, token="body", color=TEXT_DIM,
                              anchor="middle").replace("<text ", '<text data-role="x-tick" ', 1))
        # Keep the full dated window and qualification as real final text nodes.
        parts.append(text(xml_escape(trend["window"]), 252, 132, token="body", color=TEXT_DIM))
    parts.append(text(xml_escape(trend["qualification"]), 252, 320, token="body", color=TEXT_DIM))
    parts.append("</g>")
    return "".join(parts)


def generate(
    engineering: dict,
    output_path: str = "assets/engineering_cadence.svg",
    primary_language: str = "",
    data_quality: dict | None = None,
    ci_claim: dict | None = None,
    automation: dict | None = None,
) -> str:
    data = engineering if isinstance(engineering, dict) else {}
    quality = data_quality if isinstance(data_quality, dict) else {}
    metric_statuses = quality.get("metric_statuses", {})
    if not isinstance(metric_statuses, dict):
        metric_statuses = {}
    ci_status = str(metric_statuses.get("automation_repos", "exact")).casefold()
    language_status = str(
        metric_statuses.get("primary_lang_share_pct", "exact")
    ).casefold()
    display = automation_display(automation)
    workflow_display = display["combined"]
    quality_lines = ["Workflow: owned public + private nonfork; profile excluded",
                     workflow_display["qualification"]]
    if automation is None and ci_status == "partial":
        quality_lines[-1] = "Workflow · Partial · known minimum · unknown repositories"
    if language_status == "partial":
        quality_lines.append("Language · Partial · observed bytes")
    elif language_status == "unavailable":
        quality_lines.append("Language · Unavailable · n/a")
    trend = contribution_trend_display(data.get("contribution_trend"))
    cadence = trend["values"]
    active_days = _int(data.get("active_days_last_year"))
    workflows = _int(data.get("automation_workflows"))
    automation_repos = _int(data.get("automation_repos"))
    primary_share = float(data.get("primary_lang_share_pct") or 0.0)
    public_total = _int(data.get("public_repos_total"))
    public_nonfork = _int(data.get("public_nonfork_repos"))
    private_nonfork = _int(data.get("private_nonfork_repos"))
    private_total = data.get("private_repos_total")
    private_total = _int(private_total) if private_total is not None else None

    # Production receives the owning summary and its exact prepared claim.
    # Standalone compatibility values require an explicit claim to show a ratio.
    ci_pct = float((ci_claim or {}).get("value") or 0.0)
    if automation is not None:
        workflows = automation["combined"]["workflow_files"]
        automation_repos = automation["combined"]["configured_repos"]

    width = SVG_WIDTH
    pad = 28

    header_svg, content_top = section_header(
        pad, 46, "Engineering Cadence", width=width,
        eyebrow="Workflow Analytics", right_text="automation-first", pad=pad,
    )

    # Honest empty state.
    if automation is None and not any((cadence, active_days, workflows, public_total, private_total)):
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
    tile_h = 84
    row2_y = 344
    row2_bottom = row2_y + tile_h
    height = int(row2_bottom + 30 + len(quality_lines) * 18)

    parts: list[str] = [glass_panel(width, height), header_svg,
        f"<desc>{xml_escape(automation_description(automation))}</desc>"]

    # Row 1: KPI (active days) + dated contribution chart.
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
    parts.append(_contribution_chart(trend, (data.get("contribution_trend") or {}).get("points", [])))

    # Row 2: CI-coverage gauge + 3 secondary metric tiles.
    cols, gap = 4, SPACE["md"]
    col_w = (width - pad * 2 - gap * (cols - 1)) / cols
    parts.append(
        metric_claim_group(
            ci_claim,
            _gauge_cell(
                pad,
                row2_y,
                col_w,
                tile_h,
                value=ci_pct,
                detail=workflow_display["gauge_detail"],
                display_value=(
                    ci_claim["display_value"]
                    if ci_claim
                    else "n/a"
                ),
            ),
        )
    )
    parts.append(
        metric_tile(
            pad + (col_w + gap), row2_y, col_w, tile_h,
            value=("n/a" if ci_status == "unavailable" else fmt_int(workflows)),
            label=AUTOMATION_FILES_LABEL,
            caption=(
                "Unavailable"
                if ci_status == "unavailable"
                else f"{fmt_int(automation_repos)} repos"
            ),
            icon_name="workflow",
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
            value=(
                "n/a"
                if language_status == "unavailable"
                else f"{round(primary_share)}%"
            ),
            label=(primary_language or "primary language"),
            caption=(
                "observed bytes"
                if language_status == "partial"
                else "share of code"
            ),
            icon_name="code",
        )
    )

    for index, quality_line in enumerate(quality_lines):
        parts.append(
            text(
                quality_line,
                pad,
                row2_bottom + 20 + index * 18,
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

"""Contribution Calendar card — KPI + GitHub-style heatmap (DESIGN_SPEC, governed glass).

12-month contributions promoted to the dominant KPI; the week x 7-day grid keeps the
familiar contribution-graph shape; current/longest streak demote to neutral metric
tiles. All labels on the locked type ladder (>=11). Glass kept.
"""

from __future__ import annotations

from datetime import datetime, timezone

from scripts.core.config import (
    CONTRIB_EMPTY,
    CONTRIB_RAMP,
    GLASS_SHEEN_HEX,
    SPACE,
    SVG_WIDTH,
    TEXT_DIM,
)
from scripts.rendering.components import empty_state, metric_tile, primary_kpi, section_header, text
from scripts.rendering.glass_kit import glass_panel
from scripts.rendering.svg_utils import fmt_compact, fmt_int

_EMPTY_HEX = CONTRIB_EMPTY
_EMPTY_OP = 0.06
_RAMP = CONTRIB_RAMP
_MONTHS = {f"{i:02d}": m for i, m in enumerate(
    ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}


def _month_label(date_str: str) -> str:
    return _MONTHS.get(date_str[5:7], "") if date_str and len(date_str) >= 7 else ""


def _compute_streaks(days: list[dict]) -> tuple[int, int]:
    if not days:
        return 0, 0
    today = datetime.now(timezone.utc).date()
    counts = []
    for day in days:
        try:
            parsed = datetime.fromisoformat(str(day.get("date", ""))).date()
        except ValueError:
            parsed = None
        if parsed is None or parsed <= today:
            try:
                counts.append(int(day.get("contributionCount", 0)))
            except (TypeError, ValueError):
                counts.append(0)
    longest = run = 0
    for c in counts:
        run = run + 1 if c > 0 else 0
        longest = max(longest, run)
    current = 0
    for c in reversed(counts):
        if c > 0:
            current += 1
        else:
            break
    return current, longest


def _level(count: int, max_count: int) -> int:
    if count <= 0 or max_count <= 0:
        return 0
    r = count / max_count
    return 4 if r >= 0.75 else 3 if r >= 0.5 else 2 if r >= 0.25 else 1


def _cell(x: float, y: float, size: float, level: int) -> str:
    rx = 3
    if level <= 0:
        return (f'<rect x="{x:g}" y="{y:g}" width="{size:g}" height="{size:g}" rx="{rx}" '
                f'fill="{_EMPTY_HEX}" fill-opacity="{_EMPTY_OP}"/>')
    return (
        f'<rect x="{x:g}" y="{y:g}" width="{size:g}" height="{size:g}" rx="{rx}" fill="{_RAMP[level - 1]}"/>'
        f'<rect x="{x + 0.5:g}" y="{y + 0.5:g}" width="{size - 1:g}" height="{size - 1:g}" '
        f'rx="{rx - 0.5:g}" fill="none" stroke="{GLASS_SHEEN_HEX}" stroke-opacity="0.10" stroke-width="0.75"/>'
    )


def generate(calendar: dict | None, output_path: str = "assets/contribution_calendar.svg") -> str:
    width = SVG_WIDTH
    pad = 28
    weeks = calendar.get("weeks") if isinstance(calendar, dict) and isinstance(calendar.get("weeks"), list) else []
    try:
        total = int(calendar.get("totalContributions", 0)) if isinstance(calendar, dict) else 0
    except (TypeError, ValueError):
        total = 0

    header_svg, content_top = section_header(
        pad, 46, "Contribution Calendar", width=width, eyebrow="Last 12 Months", pad=pad
    )

    if not weeks:
        empty_header, _ = section_header(pad, 46, "Contribution Calendar", width=width, eyebrow="Last 12 Months", pad=pad)
        height = int(content_top + 92)
        body = "".join([glass_panel(width, height), empty_header,
                        empty_state(width / 2, content_top + 48, "No contribution calendar available", icon_name="calendar")])
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
                    f'viewBox="0 0 {width} {height}">{body}</svg>')
        return output_path

    all_days = [d for wk in weeks if isinstance(wk, dict) for d in (wk.get("contributionDays") or []) if isinstance(d, dict)]
    max_count = max((int(d.get("contributionCount", 0)) for d in all_days if str(d.get("contributionCount", 0)).lstrip("-").isdigit()), default=0)
    current_streak, longest_streak = _compute_streaks(all_days)

    cell, gap = 11, 3
    cols = len(weeks)
    grid_w = cols * cell + max(0, cols - 1) * gap
    grid_x = round((width - grid_w) / 2)
    grid_y = content_top + 124
    grid_bottom = grid_y + 7 * cell + 6 * gap
    legend_y = grid_bottom + 18
    height = int(legend_y + 24)

    parts = [glass_panel(width, height), header_svg]

    # KPI (top-left) + two neutral streak tiles
    parts.append(primary_kpi(pad, content_top + 58, value=fmt_compact(total), label="contributions", sublabel="last 12 months"))
    grid_tx = pad + 244 + SPACE["xl"]
    col_w = (width - pad - grid_tx - SPACE["md"]) / 2
    for i, (val, label, icon_name) in enumerate(
        [(fmt_int(current_streak), "current streak", "fire"), (fmt_int(longest_streak), "longest streak", "trend_up")]
    ):
        parts.append(metric_tile(grid_tx + i * (col_w + SPACE["md"]), content_top + 24, col_w, 66,
                                 value=val, label=label, icon_name=icon_name))

    # month labels (>=12, sparse so they don't crowd)
    prev, last_x = "", -1e9
    for idx, wk in enumerate(weeks):
        days = wk.get("contributionDays") or [] if isinstance(wk, dict) else []
        month = _month_label(days[0].get("date", "") if days and isinstance(days[0], dict) else "")
        if month and month != prev:
            prev = month
            lx = grid_x + idx * (cell + gap)
            if lx - last_x >= 46:
                last_x = lx
                parts.append(text(month, lx, grid_y - 8, token="caption", color=TEXT_DIM))

    for w_idx, wk in enumerate(weeks):
        days = wk.get("contributionDays") if isinstance(wk, dict) else []
        if not isinstance(days, list):
            continue
        cx = grid_x + w_idx * (cell + gap)
        for d_idx, day in enumerate(days[:7]):
            try:
                count = int(day.get("contributionCount", 0))
            except (TypeError, ValueError):
                count = 0
            parts.append(_cell(cx, grid_y + d_idx * (cell + gap), cell, _level(count, max_count)))

    # legend: Less [ramp] More (>=12)
    sw, sgap, n = 12, 4, 5
    legend_w = n * sw + (n - 1) * sgap
    right = grid_x + grid_w
    sx = right - 36 - legend_w
    parts.append(text("Less", sx - 8, legend_y + sw - 2, token="caption", color=TEXT_DIM, anchor="end"))
    for i in range(n):
        parts.append(_cell(sx + i * (sw + sgap), legend_y, sw, i))
    parts.append(text("More", sx + legend_w + 8, legend_y + sw - 2, token="caption", color=TEXT_DIM))

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
           f'viewBox="0 0 {width} {height}">{"".join(parts)}</svg>')
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    return output_path

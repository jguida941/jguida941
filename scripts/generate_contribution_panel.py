"""Build the contribution calendar SVG panel (Apple/glass styling)."""

from __future__ import annotations

from datetime import datetime, timezone

from scripts.config import (
    BLUE,
    CYAN,
    FONT_SANS,
    GLASS_INSET,
    GREEN,
    SVG_WIDTH,
    TEXT,
    TEXT_BRIGHT,
    TEXT_DIM,
)
from scripts.glass_kit import (
    accent_ribbon,
    glass_panel,
    glass_tile,
    icon,
)
from scripts.card_theme import title_left
from scripts.svg_utils import fmt_int

# Refined 5-step intensity ramp: idle slot + cool blue -> cyan -> mint (low -> high).
_EMPTY_HEX = "#c0caf5"
_EMPTY_OP = 0.06
_RAMP = ["#34528a", "#5b86d4", "#7dcfff", "#9ece6a"]  # levels 1..4


def _month_label(date_str: str) -> str:
    months = {
        "01": "Jan",
        "02": "Feb",
        "03": "Mar",
        "04": "Apr",
        "05": "May",
        "06": "Jun",
        "07": "Jul",
        "08": "Aug",
        "09": "Sep",
        "10": "Oct",
        "11": "Nov",
        "12": "Dec",
    }
    if not date_str or len(date_str) < 7:
        return ""
    return months.get(date_str[5:7], "")


def _compute_streaks(days: list[dict]) -> tuple[int, int]:
    if not days:
        return 0, 0

    today_utc = datetime.now(timezone.utc).date()
    filtered_days = []
    for day in days:
        raw_date = str(day.get("date", ""))
        try:
            parsed = datetime.fromisoformat(raw_date).date()
        except ValueError:
            parsed = None
        if parsed is None or parsed <= today_utc:
            filtered_days.append(day)

    if not filtered_days:
        return 0, 0

    longest = 0
    current_run = 0
    for day in filtered_days:
        try:
            count = int(day.get("contributionCount", 0))
        except (TypeError, ValueError):
            count = 0
        if count > 0:
            current_run += 1
            if current_run > longest:
                longest = current_run
        else:
            current_run = 0

    current = 0
    for day in reversed(filtered_days):
        try:
            count = int(day.get("contributionCount", 0))
        except (TypeError, ValueError):
            count = 0
        if count > 0:
            current += 1
        else:
            break

    return current, longest


def _level(count: int, max_count: int) -> int:
    if count <= 0 or max_count <= 0:
        return 0
    ratio = count / max_count
    if ratio >= 0.75:
        return 4
    if ratio >= 0.5:
        return 3
    if ratio >= 0.25:
        return 2
    return 1


def _cell(x: float, y: float, size: float, level: int) -> str:
    """One rounded heatmap cell: faint frosted slot when idle, ramp color when active."""
    rx = 3
    if level <= 0:
        return (
            f'<rect x="{x:g}" y="{y:g}" width="{size:g}" height="{size:g}" rx="{rx}" '
            f'fill="{_EMPTY_HEX}" fill-opacity="{_EMPTY_OP}"/>'
        )
    color = _RAMP[level - 1]
    return (
        f'<rect x="{x:g}" y="{y:g}" width="{size:g}" height="{size:g}" rx="{rx}" '
        f'fill="{color}"/>'
        f'<rect x="{x + 0.5:g}" y="{y + 0.5:g}" width="{size - 1:g}" height="{size - 1:g}" '
        f'rx="{rx - 0.5:g}" fill="none" stroke="#ffffff" stroke-opacity="0.10" stroke-width="0.75"/>'
    )


def _stat_tile(
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    accent: str,
    icon_name: str,
    value: str,
    unit: str,
    label: str,
) -> str:
    parts = [glass_tile(x, y, w, h, accent=accent)]
    parts.append(icon(icon_name, x + 16, y + 24, size=15, color=accent))
    num_x = x + 41
    num_baseline = y + 40
    parts.append(
        f'<text x="{num_x:g}" y="{num_baseline:g}" fill="{TEXT_BRIGHT}" font-size="21" '
        f'font-family="{FONT_SANS}" font-weight="700">{value}</text>'
    )
    if unit:
        unit_x = num_x + len(value) * 21 * 0.6 + 6
        parts.append(
            f'<text x="{unit_x:g}" y="{num_baseline:g}" fill="{TEXT_DIM}" font-size="11" '
            f'font-family="{FONT_SANS}" font-weight="500">{unit}</text>'
        )
    parts.append(
        f'<text x="{x + 16:g}" y="{y + 55:g}" fill="{TEXT_DIM}" font-size="9.5" '
        f'font-family="{FONT_SANS}" font-weight="600" letter-spacing="1.1">{label}</text>'
    )
    return "".join(parts)


def generate(calendar: dict | None, output_path: str = "assets/contribution_calendar.svg") -> str:
    title = "Contribution Calendar"

    weeks = []
    total_contributions = 0
    if isinstance(calendar, dict):
        weeks = calendar.get("weeks") if isinstance(calendar.get("weeks"), list) else []
        try:
            total_contributions = int(calendar.get("totalContributions", 0))
        except (TypeError, ValueError):
            total_contributions = 0

    if not weeks:
        svg_h = 150
        body = (
            glass_panel(SVG_WIDTH, svg_h)
            + title_left(title, x=30, y=44)
            + accent_ribbon(SVG_WIDTH, pad=30, y=56)
            + f'<text x="30" y="96" fill="{TEXT}" font-size="13" '
            f'font-family="{FONT_SANS}">Calendar data unavailable for this run.</text>'
        )
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{svg_h}" '
            f'viewBox="0 0 {SVG_WIDTH} {svg_h}">{body}</svg>'
        )
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg)
        return output_path

    all_days = []
    for week in weeks:
        if not isinstance(week, dict):
            continue
        for day in week.get("contributionDays", []):
            if isinstance(day, dict):
                all_days.append(day)

    max_count = 0
    for day in all_days:
        try:
            max_count = max(max_count, int(day.get("contributionCount", 0)))
        except (TypeError, ValueError):
            continue

    current_streak, longest_streak = _compute_streaks(all_days)

    # --- Grid geometry (centered, with ~38px breathing room from the panel rim) ---
    cell = 11
    gap = 3
    cols = len(weeks)
    grid_w = cols * cell + max(0, cols - 1) * gap
    grid_h = 7 * cell + 6 * gap
    grid_x = round((SVG_WIDTH - grid_w) / 2)
    grid_y = 88
    grid_bottom = grid_y + grid_h
    left = grid_x
    right = grid_x + grid_w

    # --- Vertical layout ---
    title_y = 42
    ribbon_y = 53
    legend_y = grid_bottom + 22
    tiles_y = grid_bottom + 44
    tile_h = 64
    svg_h = tiles_y + tile_h + GLASS_INSET + 12

    parts: list[str] = [glass_panel(SVG_WIDTH, svg_h)]

    # Title + eyebrow caption
    parts.append(title_left(title, x=left, y=title_y))
    parts.append(
        f'<text x="{right:g}" y="{title_y - 1:g}" fill="{TEXT_DIM}" font-size="10" '
        f'font-family="{FONT_SANS}" font-weight="600" letter-spacing="1.5" '
        f'text-anchor="end">LAST 12 MONTHS</text>'
    )
    parts.append(accent_ribbon(SVG_WIDTH, pad=left, y=ribbon_y))

    # Month labels above the grid (skip a new month if it would crowd the prior label)
    prev_month = ""
    last_label_x = -1e9
    for idx, week in enumerate(weeks):
        days = week.get("contributionDays") or [] if isinstance(week, dict) else []
        first_date = days[0].get("date", "") if days and isinstance(days[0], dict) else ""
        month = _month_label(first_date)
        if month and month != prev_month:
            prev_month = month
            lx = grid_x + idx * (cell + gap)
            if lx - last_label_x < 34:
                continue
            last_label_x = lx
            parts.append(
                f'<text x="{lx:g}" y="{grid_y - 9:g}" fill="{TEXT_DIM}" font-size="9.5" '
                f'font-family="{FONT_SANS}" font-weight="500">{month}</text>'
            )

    # Heatmap cells
    for w_idx, week in enumerate(weeks):
        days = week.get("contributionDays") if isinstance(week, dict) else []
        if not isinstance(days, list):
            continue
        cx = grid_x + w_idx * (cell + gap)
        for d_idx, day in enumerate(days[:7]):
            try:
                count = int(day.get("contributionCount", 0))
            except (TypeError, ValueError):
                count = 0
            level = _level(count, max_count)
            cy = grid_y + d_idx * (cell + gap)
            parts.append(_cell(cx, cy, cell, level))

    # Legend: Less [ramp swatches] More (right-aligned to the grid)
    sw = 12
    sgap = 4
    swatches = 5
    legend_w = swatches * sw + (swatches - 1) * sgap
    text_pad = 8
    less_w = 30
    more_w = 32
    sw_x = right - more_w - legend_w
    parts.append(
        f'<text x="{sw_x - text_pad:g}" y="{legend_y + sw - 2.5:g}" fill="{TEXT_DIM}" '
        f'font-size="9.5" font-family="{FONT_SANS}" text-anchor="end">Less</text>'
    )
    for i in range(swatches):
        lx = sw_x + i * (sw + sgap)
        parts.append(_cell(lx, legend_y, sw, i))
    parts.append(
        f'<text x="{sw_x + legend_w + text_pad:g}" y="{legend_y + sw - 2.5:g}" fill="{TEXT_DIM}" '
        f'font-size="9.5" font-family="{FONT_SANS}">More</text>'
    )

    # Stat tiles (frosted) — Total / Current streak / Longest streak
    t_gap = 16
    tile_w = (grid_w - 2 * t_gap) / 3
    streak_unit = "day" if current_streak == 1 else "days"
    longest_unit = "day" if longest_streak == 1 else "days"
    stats = [
        (BLUE, "calendar", fmt_int(total_contributions), "", "TOTAL CONTRIBUTIONS"),
        (CYAN, "fire", str(current_streak), streak_unit, "CURRENT STREAK"),
        (GREEN, "trend_up", str(longest_streak), longest_unit, "LONGEST STREAK"),
    ]
    for i, (accent, icon_name, value, unit, label) in enumerate(stats):
        tx = grid_x + i * (tile_w + t_gap)
        parts.append(
            _stat_tile(
                tx,
                tiles_y,
                tile_w,
                tile_h,
                accent=accent,
                icon_name=icon_name,
                value=value,
                unit=unit,
                label=label,
            )
        )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{svg_h}" '
        f'viewBox="0 0 {SVG_WIDTH} {svg_h}">{"".join(parts)}</svg>'
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    return output_path

"""Generate a themed contribution calendar SVG panel."""

from __future__ import annotations

from datetime import datetime, timezone

from scripts.config import (
    BG_CARD,
    BG_DARK,
    BG_HIGHLIGHT,
    BLUE,
    CYAN,
    GREEN,
    TEXT,
    TEXT_BRIGHT,
    TEXT_DIM,
    BORDER,
    SVG_WIDTH,
    FONT_SANS,
)


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


def generate(calendar: dict | None, output_path: str = "assets/contribution_calendar.svg") -> str:
    pad = 20
    header_h = 44
    grid_y = 58
    cell = 10
    gap = 2

    weeks = []
    total_contributions = 0
    if isinstance(calendar, dict):
        weeks = calendar.get("weeks") if isinstance(calendar.get("weeks"), list) else []
        try:
            total_contributions = int(calendar.get("totalContributions", 0))
        except (TypeError, ValueError):
            total_contributions = 0

    if not weeks:
        svg_h = 170
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{svg_h}" viewBox="0 0 {SVG_WIDTH} {svg_h}">
  <rect width="{SVG_WIDTH}" height="{svg_h}" rx="14" fill="{BG_CARD}" stroke="{BORDER}" stroke-width="1"/>
  <rect x="0" y="0" width="{SVG_WIDTH}" height="{header_h}" rx="14" fill="{BG_DARK}"/>
  <text x="{pad}" y="29" fill="{TEXT_BRIGHT}" font-size="16" font-family="{FONT_SANS}" font-weight="700">Contribution Calendar</text>
  <text x="{SVG_WIDTH - pad}" y="29" fill="{TEXT_DIM}" font-size="11" font-family="{FONT_SANS}" text-anchor="end">last 12 months</text>
  <text x="{pad}" y="86" fill="{TEXT}" font-size="13" font-family="{FONT_SANS}">Calendar data unavailable for this run.</text>
</svg>'''
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg)
        return output_path

    all_days = []
    for week in weeks:
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

    cols = len(weeks)
    grid_w = cols * cell + max(0, cols - 1) * gap
    grid_h = 7 * cell + 6 * gap

    month_markers = []
    prev_month = ""
    for idx, week in enumerate(weeks):
        days = week.get("contributionDays") or []
        first_date = days[0].get("date", "") if days and isinstance(days[0], dict) else ""
        month = _month_label(first_date)
        if month and month != prev_month:
            month_markers.append((idx, month))
            prev_month = month

    stats_y = grid_y + grid_h + 28
    svg_h = stats_y + 58

    palette = [BG_HIGHLIGHT, "#33456a", BLUE, GREEN, CYAN]

    parts = []
    parts.append(
        f'<text x="{pad}" y="29" fill="{TEXT_BRIGHT}" font-size="16" '
        f'font-family="{FONT_SANS}" font-weight="700">Contribution Calendar</text>'
    )
    parts.append(
        f'<text x="{SVG_WIDTH - pad}" y="29" fill="{TEXT_DIM}" font-size="11" '
        f'font-family="{FONT_SANS}" text-anchor="end">last 12 months</text>'
    )

    for idx, month in month_markers:
        x = pad + idx * (cell + gap)
        parts.append(
            f'<text x="{x}" y="51" fill="{TEXT_DIM}" font-size="9" '
            f'font-family="{FONT_SANS}">{month}</text>'
        )

    for w_idx, week in enumerate(weeks):
        days = week.get("contributionDays") if isinstance(week, dict) else []
        if not isinstance(days, list):
            continue
        for d_idx, day in enumerate(days[:7]):
            try:
                count = int(day.get("contributionCount", 0))
            except (TypeError, ValueError):
                count = 0
            level = _level(count, max_count)
            x = pad + w_idx * (cell + gap)
            y = grid_y + d_idx * (cell + gap)
            parts.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" '
                f'fill="{palette[level]}" stroke="{BORDER}" stroke-width="0.4"/>'
            )

    parts.append(
        f'<text x="{pad}" y="{stats_y}" fill="{TEXT}" font-size="11" font-family="{FONT_SANS}">'
        f'Total: {total_contributions:,} contributions</text>'
    )
    parts.append(
        f'<text x="{pad + 250}" y="{stats_y}" fill="{TEXT}" font-size="11" font-family="{FONT_SANS}">'
        f'Current streak: {current_streak} days</text>'
    )
    parts.append(
        f'<text x="{pad + 490}" y="{stats_y}" fill="{TEXT}" font-size="11" font-family="{FONT_SANS}">'
        f'Longest streak: {longest_streak} days</text>'
    )

    legend_y = stats_y + 18
    parts.append(
        f'<text x="{pad}" y="{legend_y + 10}" fill="{TEXT_DIM}" font-size="9" font-family="{FONT_SANS}">Less</text>'
    )
    legend_x = pad + 30
    for idx, color in enumerate(palette):
        lx = legend_x + idx * (cell + 4)
        parts.append(
            f'<rect x="{lx}" y="{legend_y}" width="{cell}" height="{cell}" rx="2" '
            f'fill="{color}" stroke="{BORDER}" stroke-width="0.4"/>'
        )
    parts.append(
        f'<text x="{legend_x + len(palette) * (cell + 4) + 4}" y="{legend_y + 10}" fill="{TEXT_DIM}" '
        f'font-size="9" font-family="{FONT_SANS}">More</text>'
    )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{svg_h}" viewBox="0 0 {SVG_WIDTH} {svg_h}">
  <rect width="{SVG_WIDTH}" height="{svg_h}" rx="14" fill="{BG_CARD}" stroke="{BORDER}" stroke-width="1"/>
  <rect x="0" y="0" width="{SVG_WIDTH}" height="{header_h}" rx="14" fill="{BG_DARK}"/>
  {''.join(parts)}
</svg>'''

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    return output_path

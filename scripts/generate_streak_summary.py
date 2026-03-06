"""Generate a streak summary SVG with a classic center-ring layout."""

from __future__ import annotations

from datetime import date, datetime, timezone

from scripts.config import BG_CARD, BG_DARK, BG_HIGHLIGHT, BLUE, BORDER, CYAN, ORANGE, TEXT, TEXT_BRIGHT, TEXT_DIM, FONT_SANS, SVG_WIDTH


def _parse_day_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def _esc(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _fmt_int(value: int | None) -> str:
    if value is None:
        return "n/a"
    return f"{int(value):,}"


def _fmt_day(value: date, with_year: bool = False) -> str:
    fmt = "%b %d, %Y" if with_year else "%b %d"
    return value.strftime(fmt).replace(" 0", " ")


def _fmt_range(start: date | None, end: date | None) -> str:
    if start is None or end is None:
        return "n/a"
    if start.year == end.year:
        return f"{_fmt_day(start)} - {_fmt_day(end)}"
    return f"{_fmt_day(start, with_year=True)} - {_fmt_day(end, with_year=True)}"


def _collect_days(calendar: dict | None, today_utc: date) -> list[tuple[date, int]]:
    rows: list[tuple[date, int]] = []
    if not isinstance(calendar, dict):
        return rows

    weeks = calendar.get("weeks") if isinstance(calendar.get("weeks"), list) else []
    for week in weeks:
        if not isinstance(week, dict):
            continue
        days = week.get("contributionDays")
        if not isinstance(days, list):
            continue
        for day in days:
            if not isinstance(day, dict):
                continue
            parsed = _parse_day_date(str(day.get("date", "")))
            if parsed is None or parsed > today_utc:
                continue
            try:
                count = int(day.get("contributionCount", 0))
            except (TypeError, ValueError):
                count = 0
            rows.append((parsed, max(0, count)))
    rows.sort(key=lambda item: item[0])
    return rows


def _streak_ranges(days: list[tuple[date, int]]) -> tuple[int, date | None, date | None, int, date | None, date | None]:
    if not days:
        return 0, None, None, 0, None, None

    best_len = 0
    best_start: date | None = None
    best_end: date | None = None

    run_len = 0
    run_start: date | None = None
    run_end: date | None = None

    for day, count in days:
        if count > 0:
            if run_len == 0:
                run_start = day
            run_len += 1
            run_end = day
            if run_len > best_len:
                best_len = run_len
                best_start = run_start
                best_end = run_end
        else:
            run_len = 0
            run_start = None
            run_end = None

    current_len = 0
    current_start: date | None = None
    current_end: date | None = None
    for day, count in reversed(days):
        if count > 0:
            current_len += 1
            current_start = day
            if current_end is None:
                current_end = day
        else:
            break

    return current_len, current_start, current_end, best_len, best_start, best_end


def generate(
    *,
    calendar: dict | None,
    current_streak_days: int,
    total_contributions: int | None,
    output_path: str = "assets/streak_summary.svg",
) -> str:
    today_utc = datetime.now(timezone.utc).date()
    day_rows = _collect_days(calendar, today_utc)
    (
        streak_days_computed,
        current_start,
        current_end,
        longest_days,
        longest_start,
        longest_end,
    ) = _streak_ranges(day_rows)

    current_days = max(int(current_streak_days or 0), streak_days_computed)
    contrib_start = day_rows[0][0] if day_rows else None
    contrib_end = day_rows[-1][0] if day_rows else None

    width = SVG_WIDTH
    height = 226
    pad = 24
    header_h = 44
    content_top = 58
    content_bottom = height - 16
    col_w = int((width - pad * 2) / 3)
    sep_left = pad + col_w
    sep_right = pad + col_w * 2
    center_x = pad + int(col_w * 1.5)

    parts = [
        f'<rect width="{width}" height="{height}" rx="14" fill="{BG_CARD}" stroke="{BORDER}" stroke-width="1"/>',
        f'<rect x="0" y="0" width="{width}" height="{header_h}" rx="14" fill="{BG_DARK}"/>',
        f'<text x="{pad}" y="29" fill="{TEXT_BRIGHT}" font-size="16" font-family="{FONT_SANS}" font-weight="700">Streak Summary</text>',
        f'<text x="{width - pad}" y="29" fill="{TEXT_DIM}" font-size="11" font-family="{FONT_SANS}" text-anchor="end">from contribution calendar</text>',
        f'<line x1="{sep_left}" y1="{content_top}" x2="{sep_left}" y2="{content_bottom}" stroke="{BORDER}" stroke-width="1"/>',
        f'<line x1="{sep_right}" y1="{content_top}" x2="{sep_right}" y2="{content_bottom}" stroke="{BORDER}" stroke-width="1"/>',
    ]

    # Left: contributions
    left_cx = pad + int(col_w * 0.5)
    parts.extend(
        [
            f'<circle cx="{left_cx}" cy="86" r="10" fill="{BG_HIGHLIGHT}" stroke="{CYAN}" stroke-width="2"/>',
            f'<line x1="{left_cx - 5}" y1="86" x2="{left_cx + 5}" y2="86" stroke="{CYAN}" stroke-width="1.5"/>',
            f'<line x1="{left_cx}" y1="81" x2="{left_cx}" y2="91" stroke="{CYAN}" stroke-width="1.5"/>',
            f'<text x="{left_cx}" y="130" fill="{TEXT_BRIGHT}" font-size="48" font-family="{FONT_SANS}" text-anchor="middle" font-weight="700">{_esc(_fmt_int(total_contributions))}</text>',
            f'<text x="{left_cx}" y="162" fill="{TEXT}" font-size="28" font-family="{FONT_SANS}" text-anchor="middle" font-weight="600">Total Contributions</text>',
            f'<text x="{left_cx}" y="188" fill="{TEXT_DIM}" font-size="15" font-family="{FONT_SANS}" text-anchor="middle">{_esc(_fmt_range(contrib_start, contrib_end))}</text>',
        ]
    )

    # Middle: current streak ring
    parts.extend(
        [
            f'<circle cx="{center_x}" cy="118" r="58" fill="{BG_HIGHLIGHT}" stroke="{BLUE}" stroke-width="6"/>',
            f'<circle cx="{center_x}" cy="67" r="7" fill="{ORANGE}"/>',
            f'<path d="M {center_x - 4} 61 C {center_x - 2} 54, {center_x + 2} 54, {center_x + 4} 61" fill="{ORANGE}"/>',
            f'<text x="{center_x}" y="131" fill="{BLUE}" font-size="56" font-family="{FONT_SANS}" text-anchor="middle" font-weight="700">{_esc(_fmt_int(current_days))}</text>',
            f'<text x="{center_x}" y="186" fill="{BLUE}" font-size="34" font-family="{FONT_SANS}" text-anchor="middle" font-weight="700">Current Streak</text>',
            f'<text x="{center_x}" y="210" fill="{TEXT_DIM}" font-size="15" font-family="{FONT_SANS}" text-anchor="middle">{_esc(_fmt_range(current_start, current_end))}</text>',
        ]
    )

    # Right: longest streak
    right_cx = pad + int(col_w * 2.5)
    parts.extend(
        [
            f'<circle cx="{right_cx}" cy="86" r="10" fill="{BG_HIGHLIGHT}" stroke="{BLUE}" stroke-width="2"/>',
            f'<polygon points="{right_cx},{78} {right_cx + 5},{86} {right_cx},{94} {right_cx - 5},{86}" fill="{BLUE}"/>',
            f'<text x="{right_cx}" y="130" fill="{TEXT_BRIGHT}" font-size="48" font-family="{FONT_SANS}" text-anchor="middle" font-weight="700">{_esc(_fmt_int(longest_days))}</text>',
            f'<text x="{right_cx}" y="162" fill="{TEXT}" font-size="28" font-family="{FONT_SANS}" text-anchor="middle" font-weight="600">Longest Streak</text>',
            f'<text x="{right_cx}" y="188" fill="{TEXT_DIM}" font-size="15" font-family="{FONT_SANS}" text-anchor="middle">{_esc(_fmt_range(longest_start, longest_end))}</text>',
        ]
    )

    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">{"".join(parts)}</svg>'
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(svg)
    return output_path

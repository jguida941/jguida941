"""Build the streak summary SVG."""

from __future__ import annotations

from datetime import date, datetime, timezone

from scripts.config import (
    FONT_SANS,
    GRAD_ORANGE_PINK,
    ORANGE,
    SVG_WIDTH,
    TEXT,
    TEXT_BRIGHT,
    TEXT_DIM,
)
from scripts.render.card_theme import title_left
from scripts.render.glass_kit import accent_ribbon, eyebrow_text, glass_panel, glass_tile, icon
from scripts.render.svg_utils import xml_escape, fmt_int


def _parse_day_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


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

    # --- Geometry (12px glass inset reserved for the drop shadow) ----------- #
    width = SVG_WIDTH
    pad = 24
    gap = 16
    inner_w = width - pad * 2
    tile_w = (inner_w - gap * 2) / 3

    tiles_top = 94
    tile_h = 150
    height = tiles_top + tile_h + 20  # +20 -> 12px shadow margin + breathing room

    # Shared baselines (the test asserts each row shares one y across columns).
    icon_y = tiles_top + 26
    value_y = tiles_top + 82
    label_y = tiles_top + 110
    date_y = tiles_top + 134

    columns = [
        (
            "calendar",
            TEXT_DIM,
            fmt_int(total_contributions),
            "Total Contributions",
            _fmt_range(contrib_start, contrib_end),
            False,
        ),
        (
            "fire",
            ORANGE,
            fmt_int(current_days),
            "Current Streak",
            _fmt_range(current_start, current_end),
            True,
        ),
        (
            "trend_up",
            TEXT_DIM,
            fmt_int(longest_days),
            "Longest Streak",
            _fmt_range(longest_start, longest_end),
            False,
        ),
    ]

    parts: list[str] = [
        glass_panel(width, height),
        eyebrow_text("Contribution Calendar", x=pad, y=40),
        title_left("Streak Summary", x=pad, y=66, size=20),
        f'<text x="{width - pad}" y="40" fill="{TEXT_DIM}" font-size="10" '
        f'font-family="{FONT_SANS}" font-weight="600" letter-spacing="1.2" '
        f'text-anchor="end">LAST 12 MONTHS</text>',
        accent_ribbon(width, pad=pad, y=78, grad=GRAD_ORANGE_PINK),
    ]

    for col, (ico, ico_color, number, label, drange, hero) in enumerate(columns):
        tx = pad + col * (tile_w + gap)
        cx = tx + tile_w / 2
        parts.append(glass_tile(tx, tiles_top, tile_w, tile_h))
        # category icon, centered above the number
        isize = 22
        parts.append(icon(ico, cx - isize / 2, icon_y, size=isize, color=ico_color))
        num_color = ORANGE if hero else TEXT_BRIGHT
        parts.extend(
            [
                f'<text x="{cx:.1f}" y="{value_y}" fill="{num_color}" font-size="42" '
                f'font-family="{FONT_SANS}" text-anchor="middle" font-weight="700">'
                f'{xml_escape(number)}</text>',
                f'<text x="{cx:.1f}" y="{label_y}" fill="{TEXT}" font-size="14" '
                f'font-family="{FONT_SANS}" text-anchor="middle" font-weight="600" '
                f'letter-spacing="0.2">{label}</text>',
                f'<text x="{cx:.1f}" y="{date_y}" fill="{TEXT_DIM}" font-size="12" '
                f'font-family="{FONT_SANS}" text-anchor="middle">'
                f'{xml_escape(drange)}</text>',
            ]
        )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">{"".join(parts)}</svg>'
    )
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(svg)
    return output_path

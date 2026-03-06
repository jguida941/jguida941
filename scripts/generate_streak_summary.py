"""Generate a streak summary SVG using canonical calendar data."""

from __future__ import annotations

from datetime import datetime, timezone

from scripts.config import BG_CARD, BG_DARK, BG_HIGHLIGHT, BORDER, CYAN, TEXT, TEXT_BRIGHT, TEXT_DIM, FONT_SANS, SVG_WIDTH


def _parse_day_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _longest_streak(days: list[dict], now_utc: datetime) -> int:
    filtered = []
    for day in days:
        parsed = _parse_day_date(str(day.get("date", "")))
        if parsed is None or parsed.date() > now_utc.date():
            continue
        filtered.append(day)

    streak = 0
    best = 0
    for day in filtered:
        try:
            count = int(day.get("contributionCount", 0))
        except (TypeError, ValueError):
            count = 0
        if count > 0:
            streak += 1
            best = max(best, streak)
        else:
            streak = 0
    return best


def _fmt_int(value: int | None) -> str:
    if value is None:
        return "n/a"
    return f"{int(value):,}"


def _esc(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _tile(x: int, y: int, w: int, h: int, label: str, value: str, detail: str) -> str:
    return (
        f'<g transform="translate({x}, {y})">'
        f'<rect width="{w}" height="{h}" rx="12" fill="{BG_HIGHLIGHT}" stroke="{BORDER}" stroke-width="1"/>'
        f'<text x="16" y="28" fill="{TEXT_DIM}" font-size="11" font-family="{FONT_SANS}" font-weight="600">{_esc(label)}</text>'
        f'<text x="16" y="58" fill="{TEXT_BRIGHT}" font-size="26" font-family="{FONT_SANS}" font-weight="700">{_esc(value)}</text>'
        f'<text x="16" y="80" fill="{TEXT}" font-size="11" font-family="{FONT_SANS}">{_esc(detail)}</text>'
        "</g>"
    )


def generate(
    *,
    calendar: dict | None,
    current_streak_days: int,
    total_contributions: int | None,
    output_path: str = "assets/streak_summary.svg",
) -> str:
    all_days = []
    if isinstance(calendar, dict):
        weeks = calendar.get("weeks") if isinstance(calendar.get("weeks"), list) else []
        for week in weeks:
            days = week.get("contributionDays", []) if isinstance(week, dict) else []
            if not isinstance(days, list):
                continue
            all_days.extend(day for day in days if isinstance(day, dict))

    now_utc = datetime.now(timezone.utc)
    longest_days = _longest_streak(all_days, now_utc)

    width = SVG_WIDTH
    height = 188
    pad = 20
    header_h = 44
    gap = 14
    tile_w = int((width - pad * 2 - gap * 2) / 3)
    tile_h = 94

    parts = [
        f'<rect width="{width}" height="{height}" rx="14" fill="{BG_CARD}" stroke="{BORDER}" stroke-width="1"/>',
        f'<rect x="0" y="0" width="{width}" height="{header_h}" rx="14" fill="{BG_DARK}"/>',
        f'<text x="{pad}" y="29" fill="{TEXT_BRIGHT}" font-size="16" font-family="{FONT_SANS}" font-weight="700">Streak Summary</text>',
        f'<text x="{width - pad}" y="29" fill="{TEXT_DIM}" font-size="11" font-family="{FONT_SANS}" text-anchor="end">from contribution calendar</text>',
        _tile(
            pad,
            header_h + 18,
            tile_w,
            tile_h,
            "Current Streak",
            _fmt_int(current_streak_days),
            "consecutive days",
        ),
        _tile(
            pad + tile_w + gap,
            header_h + 18,
            tile_w,
            tile_h,
            "Longest Streak",
            _fmt_int(longest_days),
            "best run in window",
        ),
        _tile(
            pad + (tile_w + gap) * 2,
            header_h + 18,
            tile_w,
            tile_h,
            "12mo Contributions",
            _fmt_int(total_contributions),
            "GitHub contributionCalendar",
        ),
        f'<text x="{width - pad}" y="{height - 10}" fill="{CYAN}" font-size="10" font-family="{FONT_SANS}" text-anchor="end">Canonical CLI data source</text>',
    ]

    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">{"".join(parts)}</svg>'
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(svg)
    return output_path


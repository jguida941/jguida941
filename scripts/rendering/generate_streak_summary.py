"""Build the streak summary SVG."""

from __future__ import annotations

from datetime import date, datetime, timezone

from scripts.core.config import SPACE, SVG_WIDTH, TEXT_DIM
from scripts.rendering.components import empty_state, metric_tile, primary_kpi, section_header
from scripts.rendering.glass_kit import glass_panel
from scripts.rendering.svg_utils import fmt_compact


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

    width = SVG_WIDTH
    pad = 28

    header_svg, content_top = section_header(
        pad,
        46,
        "Streak Summary",
        width=width,
        eyebrow="Contribution Calendar",
        right_text="Last 12 months",
        pad=pad,
    )

    # Honest empty state: no contribution days -> one explanatory line, no zeros.
    if not day_rows:
        empty_header, _ = section_header(
            pad, 46, "Streak Summary", width=width, eyebrow="Contribution Calendar", pad=pad
        )
        height = int(content_top + 92)
        parts = [glass_panel(width, height), empty_header]
        parts.append(
            empty_state(
                width / 2,
                content_top + 48,
                "No recent contribution activity recorded",
                icon_name="calendar",
            )
        )
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">{"".join(parts)}</svg>'
        )
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(svg)
        return output_path

    height = int(content_top + 130)
    parts = [glass_panel(width, height), header_svg]

    # PrimaryKpiCard: Current Streak is the one dominant metric, top-left.
    kpi_y = content_top + 58
    parts.append(
        primary_kpi(
            pad,
            kpi_y,
            value=fmt_compact(current_days),
            label="current streak",
            sublabel=_fmt_range(current_start, current_end),
        )
    )
    kpi_w = 244
    parts.append(
        f'<rect x="{pad + kpi_w:g}" y="{content_top + 6:g}" width="1" '
        f'height="90" fill="{TEXT_DIM}" fill-opacity="0.16"/>'
    )

    # Two secondary tiles (neutral icons + date-range caption).
    grid_x = pad + kpi_w + SPACE["xl"]
    gap = SPACE["md"]
    col_w = (width - pad - grid_x - gap) / 2
    tile_h = 88
    tile_y = content_top + 24
    secondary = [
        ("calendar", fmt_compact(total_contributions), "total contributions",
         _fmt_range(contrib_start, contrib_end)),
        ("trend_up", fmt_compact(longest_days), "longest streak",
         _fmt_range(longest_start, longest_end)),
    ]
    for i, (icon_name, value, label, caption) in enumerate(secondary):
        x = grid_x + i * (col_w + gap)
        parts.append(
            metric_tile(
                x, tile_y, col_w, tile_h,
                value=value, label=label, icon_name=icon_name, caption=caption,
            )
        )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">{"".join(parts)}</svg>'
    )
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(svg)
    return output_path

"""Build a glassmorphism SVG heatmap for coding time and event mix."""

import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from scripts.config import (
    BLUE,
    CYAN,
    FONT_SANS,
    GLASS_HAIRLINE_HEX,
    SVG_WIDTH,
    TEXT,
    TEXT_BRIGHT,
    TEXT_DIM,
)
from scripts.render.card_theme import title_left
from scripts.render.glass_kit import (
    chip,
    chip_width,
    eyebrow_text,
    glass_panel,
    glass_tile,
    icon,
    progress_bar,
)

EVENT_LABELS = {
    "PushEvent": "push",
    "PullRequestEvent": "pull request",
    "PullRequestReviewEvent": "pr review",
    "IssuesEvent": "issue",
    "IssueCommentEvent": "comment",
    "ReleaseEvent": "release",
    "CreateEvent": "create",
}

TIME_BLOCKS = [
    ("Night", range(0, 6)),
    ("Morning", range(6, 12)),
    ("Afternoon", range(12, 18)),
    ("Evening", range(18, 24)),
]

DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Refined cool ramp: faint frost (empty) -> deep blue -> bright cyan.
# Each level is (hex, fill_opacity) so we never emit rgba() in fills.
_RAMP = [
    ("#c0caf5", 0.06),  # 0  empty cell (cool frost)
    ("#35507a", 0.92),  # 1  low
    ("#4574b8", 0.96),  # 2  med
    ("#5ea6e8", 1.00),  # 3  high
    ("#7dcfff", 1.00),  # 4  peak (CYAN)
]


def _ramp_level(count: int, max_count: int) -> int:
    """Map a cell count to a 0..4 ramp index."""
    if count <= 0:
        return 0
    ratio = count / max(max_count, 1)
    if ratio <= 0.25:
        return 1
    if ratio <= 0.50:
        return 2
    if ratio <= 0.75:
        return 3
    return 4


def _timezone() -> tuple[timezone | ZoneInfo, str]:
    tz_name = (os.environ.get("PROFILE_ACTIVITY_TZ") or "America/New_York").strip()
    try:
        return ZoneInfo(tz_name), tz_name
    except Exception:
        return timezone.utc, "UTC"


def generate(events: list, output_path: str = "assets/activity_heatmap.svg"):
    """Render activity heatmap + right panel with time blocks and event mix."""
    tz, tz_label = _timezone()
    grid = defaultdict(lambda: defaultdict(int))  # grid[weekday][hour]
    block_totals = Counter()
    event_mix = Counter()

    for event in events:
        event_type = event.get("type", "")
        event_label = EVENT_LABELS.get(event_type)
        if event_label is None:
            continue
        ts = event.get("created_at", "")
        if not ts:
            continue
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(tz)
        except ValueError:
            continue

        wd = dt.weekday()  # 0=Mon, 6=Sun
        hr = dt.hour
        grid[wd][hr] += 1
        event_mix[event_label] += 1

        for block_name, block_hours in TIME_BLOCKS:
            if hr in block_hours:
                block_totals[block_name] += 1
                break

    total_events = sum(event_mix.values())
    max_count = max((grid[d][h] for d in range(7) for h in range(24)), default=1)

    # Peak summary stats.
    hour_totals = [sum(grid[d][h] for d in range(7)) for h in range(24)]
    day_totals = [sum(grid[d][h] for h in range(24)) for d in range(7)]
    peak_hour = max(range(24), key=lambda h: hour_totals[h]) if total_events else None
    peak_day = max(range(7), key=lambda d: day_totals[d]) if total_events else None
    busiest_block = block_totals.most_common(1)[0][0] if block_totals else None

    # ---- Layout geometry -------------------------------------------------- #
    W = SVG_WIDTH                       # 840
    margin = 12                         # glass_panel inset / shadow band
    content_top = 78

    # Heatmap grid metrics.
    cell, gap = 14, 3
    step = cell + gap
    grid_w = 24 * step - gap            # 405
    grid_h = 7 * step - gap             # 116

    # Left tile (heatmap).
    hm_x, hm_y, hm_w = 24, content_top, 460
    grid_x = hm_x + 44                  # 68
    grid_y = hm_y + 40                  # space for hour labels
    grid_bottom = grid_y + grid_h
    legend_y = grid_bottom + 22

    # Right column tiles.
    r_x = 500
    r_w = (W - margin - 12) - r_x       # right edge sits 12px inside the panel
    a_y, a_h = content_top, 118
    a_bottom = a_y + a_h
    b_y = a_bottom + 14
    mix_items = event_mix.most_common(5)
    n_mix = max(len(mix_items), 1)
    b_h = 30 + n_mix * 20 + 12
    b_bottom = b_y + b_h

    content_bottom = max(b_bottom, legend_y + 60)
    hm_h = content_bottom - hm_y
    b_h = content_bottom - b_y          # stretch event-mix tile to align bottoms
    summary_y = content_bottom - 36     # footer chips pinned near tile bottom
    svg_h = content_bottom + 18         # bottom shadow margin

    # ---- Build SVG body --------------------------------------------------- #
    parts = [glass_panel(W, svg_h)]

    # Header: eyebrow + title + timezone chip (top-right).
    parts.append(eyebrow_text("ACTIVITY RHYTHM", x=hm_x, y=36))
    parts.append(title_left("When I Code", x=hm_x, y=58, size=18))
    tz_short = tz_label.rsplit("/", 1)[-1].replace("_", " ") if "/" in tz_label else tz_label
    cw = chip_width(tz_short, size=11, icon=True)
    parts.append(
        chip(W - margin - 12 - cw, 33, tz_short, color=BLUE, icon_name="globe", filled=True)
    )

    # ---- Left tile: heatmap ---------------------------------------------- #
    parts.append(glass_tile(hm_x, hm_y, hm_w, hm_h))

    if total_events == 0:
        parts.append(
            f'<text x="{hm_x + hm_w / 2:.1f}" y="{hm_y + hm_h / 2:.1f}" fill="{TEXT_DIM}" '
            f'font-size="11" font-family="{FONT_SANS}" text-anchor="middle">'
            "No recent public events returned by GitHub API</text>"
        )
    else:
        # Hour axis labels (every 3 hours).
        for h in range(0, 24, 3):
            lx = grid_x + h * step + cell / 2
            parts.append(
                f'<text x="{lx:.1f}" y="{grid_y - 11:.1f}" fill="{TEXT_DIM}" font-size="8.5" '
                f'font-family="{FONT_SANS}" text-anchor="middle">{h:02d}</text>'
            )

        # Halos behind peak (level-4) cells for a soft cool glow.
        halos, cells = [], []
        for d in range(7):
            cy = grid_y + d * step
            for h in range(24):
                cx = grid_x + h * step
                c = grid[d][h]
                lvl = _ramp_level(c, max_count)
                if lvl == 4:
                    halos.append(
                        f'<rect x="{cx - 2:.1f}" y="{cy - 2:.1f}" width="{cell + 4}" '
                        f'height="{cell + 4}" rx="5" fill="{CYAN}" fill-opacity="0.20"/>'
                    )
                hexc, op = _RAMP[lvl]
                cells.append(
                    f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cell}" height="{cell}" rx="3.2" '
                    f'fill="{hexc}" fill-opacity="{op}">'
                    f"<title>{DAY_LABELS[d]} {h:02d}:00 ({tz_label}) - {c} events</title></rect>"
                )
        parts.extend(halos)
        parts.extend(cells)

        # Day-of-week labels (right-aligned into the grid).
        for d in range(7):
            ly = grid_y + d * step + cell - 2
            parts.append(
                f'<text x="{grid_x - 12:.1f}" y="{ly:.1f}" fill="{TEXT}" font-size="10" '
                f'font-family="{FONT_SANS}" text-anchor="end">{DAY_LABELS[d]}</text>'
            )

        # Legend: Less -> More ramp swatches.
        leg_x = grid_x - 12
        parts.append(
            f'<text x="{leg_x:.1f}" y="{legend_y + 9:.1f}" fill="{TEXT_DIM}" font-size="9" '
            f'font-family="{FONT_SANS}">Less</text>'
        )
        sx = leg_x + 30
        for lvl, (hexc, op) in enumerate(_RAMP):
            parts.append(
                f'<rect x="{sx:.1f}" y="{legend_y:.1f}" width="11" height="11" rx="2.5" '
                f'fill="{hexc}" fill-opacity="{op}"/>'
            )
            sx += 15
        parts.append(
            f'<text x="{sx + 2:.1f}" y="{legend_y + 9:.1f}" fill="{TEXT_DIM}" font-size="9" '
            f'font-family="{FONT_SANS}">More</text>'
        )

        # Hairline divider framing the footer chips.
        parts.append(
            f'<rect x="{hm_x + 16}" y="{summary_y - 15:.1f}" width="{hm_w - 32}" height="1" '
            f'fill="{GLASS_HAIRLINE_HEX}" fill-opacity="0.10"/>'
        )

        # Summary chips: peak slot, busiest block, total events.
        chips = []
        if peak_day is not None and peak_hour is not None:
            chips.append(("clock", f"Peak {DAY_LABELS[peak_day]} {peak_hour:02d}:00", CYAN))
        if busiest_block:
            chips.append(("fire", busiest_block, BLUE))
        chips.append(("workflow", f"{total_events} events", TEXT))
        chx = hm_x + 16
        for icon_name, text, col in chips:
            cwid = chip_width(text, size=10.5, icon=True)
            parts.append(
                chip(chx, summary_y, text, color=col, icon_name=icon_name, size=10.5, height=23)
            )
            chx += cwid + 10

    # ---- Right tile A: By Time Block ------------------------------------- #
    parts.append(glass_tile(r_x, a_y, r_w, a_h, accent=BLUE))
    parts.append(icon("clock", r_x + 16, a_y + 16, size=14, color=BLUE))
    parts.append(
        f'<text x="{r_x + 38:.1f}" y="{a_y + 27:.1f}" fill="{TEXT_BRIGHT}" font-size="12.5" '
        f'font-family="{FONT_SANS}" font-weight="700">By Time Block</text>'
    )
    max_block = max(block_totals.values(), default=1)
    a_label_x = r_x + 16
    a_bar_x = r_x + 96
    a_value_x = r_x + r_w - 16
    a_bar_w = (a_value_x - 70) - a_bar_x
    a_rows_y = a_y + 46
    a_rowh = 18
    for idx, (block_name, _) in enumerate(TIME_BLOCKS):
        cy = a_rows_y + idx * a_rowh
        count = block_totals.get(block_name, 0)
        pct = (count / total_events * 100.0) if total_events else 0.0
        bar_pct = (count / max(max_block, 1)) * 100.0
        parts.append(
            f'<text x="{a_label_x:.1f}" y="{cy + 3.5:.1f}" fill="{TEXT}" font-size="10.5" '
            f'font-family="{FONT_SANS}">{block_name}</text>'
        )
        parts.append(progress_bar(a_bar_x, cy - 4, a_bar_w, 8, bar_pct, color=BLUE))
        parts.append(
            f'<text x="{a_value_x - 32:.1f}" y="{cy + 3.5:.1f}" fill="{TEXT_BRIGHT}" '
            f'font-size="12" font-family="{FONT_SANS}" font-weight="700" '
            f'text-anchor="end">{count}</text>'
        )
        parts.append(
            f'<text x="{a_value_x:.1f}" y="{cy + 3.5:.1f}" fill="{TEXT_DIM}" font-size="9.5" '
            f'font-family="{FONT_SANS}" text-anchor="end">{pct:.0f}%</text>'
        )

    # ---- Right tile B: Event Mix ----------------------------------------- #
    parts.append(glass_tile(r_x, b_y, r_w, b_h, accent=CYAN))
    parts.append(icon("workflow", r_x + 16, b_y + 16, size=14, color=CYAN))
    parts.append(
        f'<text x="{r_x + 38:.1f}" y="{b_y + 27:.1f}" fill="{TEXT_BRIGHT}" font-size="12.5" '
        f'font-family="{FONT_SANS}" font-weight="700">Event Mix</text>'
    )
    max_mix = max((count for _, count in mix_items), default=1)
    b_bar_x = r_x + 96
    b_value_x = r_x + r_w - 16
    b_bar_w = (b_value_x - 70) - b_bar_x
    b_rows_y = b_y + 46
    avail = (b_y + b_h - 14) - b_rows_y
    b_rowh = max(18.0, min(24.0, avail / max(n_mix, 1)))
    if total_events == 0:
        parts.append(
            f'<text x="{r_x + 16:.1f}" y="{b_rows_y + 6:.1f}" fill="{TEXT_DIM}" font-size="10.5" '
            f'font-family="{FONT_SANS}">No events yet</text>'
        )
    for idx, (label, count) in enumerate(mix_items):
        cy = b_rows_y + idx * b_rowh
        pct = (count / total_events * 100.0) if total_events else 0.0
        bar_pct = (count / max(max_mix, 1)) * 100.0
        parts.append(
            f'<text x="{r_x + 16:.1f}" y="{cy + 3.5:.1f}" fill="{TEXT}" font-size="10.5" '
            f'font-family="{FONT_SANS}">{label}</text>'
        )
        parts.append(progress_bar(b_bar_x, cy - 4, b_bar_w, 8, bar_pct, color=CYAN))
        parts.append(
            f'<text x="{b_value_x - 32:.1f}" y="{cy + 3.5:.1f}" fill="{TEXT_BRIGHT}" '
            f'font-size="12" font-family="{FONT_SANS}" font-weight="700" '
            f'text-anchor="end">{count}</text>'
        )
        parts.append(
            f'<text x="{b_value_x:.1f}" y="{cy + 3.5:.1f}" fill="{TEXT_DIM}" font-size="9.5" '
            f'font-family="{FONT_SANS}" text-anchor="end">{pct:.0f}%</text>'
        )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{svg_h}" '
        f'viewBox="0 0 {W} {svg_h}">{"".join(parts)}</svg>'
    )

    with open(output_path, "w") as f:
        f.write(svg)
    return output_path

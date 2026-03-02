"""Generate a readable coding-activity heatmap + workflow breakdown panel."""

import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from scripts.config import BG_CARD, GREEN, TEXT, TEXT_DIM, BORDER, SVG_WIDTH, FONT_SANS

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


def _intensity_color(count: int, max_count: int) -> str:
    if count == 0:
        return "#1e2030"
    ratio = count / max(max_count, 1)
    if ratio < 0.25:
        return "#2d4a3e"
    if ratio < 0.5:
        return "#3b6b4f"
    if ratio < 0.75:
        return "#6aa05e"
    return "#9ece6a"


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

    # Layout
    pad = 24
    title_y = 34
    day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    label_w = 36
    cell = 12
    gap = 2
    grid_w = 24 * (cell + gap) - gap
    grid_h = 7 * (cell + gap) - gap
    heatmap_x = pad + label_w
    heatmap_y = 58

    panel_x = heatmap_x + grid_w + 34
    panel_w = SVG_WIDTH - panel_x - pad

    parts = []
    parts.append(
        f'<text x="{pad}" y="{title_y}" fill="{TEXT}" font-size="14" '
        f'font-family="{FONT_SANS}" font-weight="700">When I Code</text>'
    )
    parts.append(
        f'<text x="{pad + 108}" y="{title_y}" fill="{TEXT_DIM}" font-size="10" '
        f'font-family="{FONT_SANS}">(public events, {tz_label})</text>'
    )

    # Heatmap hour labels
    for h in range(24):
        if h % 3 == 0:
            x = heatmap_x + h * (cell + gap) + cell / 2
            parts.append(
                f'<text x="{x}" y="{heatmap_y - 6}" fill="{TEXT_DIM}" font-size="9" '
                f'font-family="{FONT_SANS}" text-anchor="middle">{h:02d}</text>'
            )

    # Heatmap cells
    for d in range(7):
        y = heatmap_y + d * (cell + gap)
        parts.append(
            f'<text x="{pad}" y="{y + cell - 1}" fill="{TEXT_DIM}" font-size="10" '
            f'font-family="{FONT_SANS}">{day_labels[d]}</text>'
        )
        for h in range(24):
            x = heatmap_x + h * (cell + gap)
            c = grid[d][h]
            color = _intensity_color(c, max_count)
            parts.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{color}">'
                f'<title>{day_labels[d]} {h:02d}:00 ({tz_label}) - {c} events</title></rect>'
            )

    # Right panel A: time-of-day blocks
    parts.append(
        f'<text x="{panel_x}" y="{title_y}" fill="{TEXT}" font-size="12" '
        f'font-family="{FONT_SANS}" font-weight="600">By Time Block</text>'
    )
    max_block = max(block_totals.values(), default=1)
    block_row_h = 18
    block_label_w = 64
    block_bar_x = panel_x + block_label_w
    block_bar_w = max(40, panel_w - block_label_w - 66)
    block_start_y = heatmap_y + 2
    for idx, (block_name, _) in enumerate(TIME_BLOCKS):
        y = block_start_y + idx * block_row_h
        count = block_totals.get(block_name, 0)
        pct = (count / total_events * 100.0) if total_events else 0.0
        w = (count / max(max_block, 1)) * block_bar_w
        parts.append(
            f'<text x="{panel_x}" y="{y + 10}" fill="{TEXT_DIM}" font-size="10" font-family="{FONT_SANS}">{block_name}</text>'
        )
        parts.append(
            f'<rect x="{block_bar_x}" y="{y}" width="{max(w, 2):.1f}" height="12" rx="2" fill="{GREEN}" opacity="0.75"/>'
        )
        parts.append(
            f'<text x="{block_bar_x + max(w, 2) + 6:.1f}" y="{y + 10}" fill="{TEXT_DIM}" font-size="10" '
            f'font-family="{FONT_SANS}">{count} ({pct:.0f}%)</text>'
        )

    # Right panel B: event mix
    mix_title_y = block_start_y + len(TIME_BLOCKS) * block_row_h + 22
    parts.append(
        f'<text x="{panel_x}" y="{mix_title_y}" fill="{TEXT}" font-size="12" '
        f'font-family="{FONT_SANS}" font-weight="600">Event Mix</text>'
    )
    mix_items = event_mix.most_common(5)
    max_mix = max((count for _, count in mix_items), default=1)
    mix_row_h = 16
    mix_label_w = 72
    mix_bar_x = panel_x + mix_label_w
    mix_bar_w = max(40, panel_w - mix_label_w - 58)
    mix_start_y = mix_title_y + 8
    for idx, (label, count) in enumerate(mix_items):
        y = mix_start_y + idx * mix_row_h
        pct = (count / total_events * 100.0) if total_events else 0.0
        w = (count / max(max_mix, 1)) * mix_bar_w
        parts.append(
            f'<text x="{panel_x}" y="{y + 10}" fill="{TEXT_DIM}" font-size="10" font-family="{FONT_SANS}">{label}</text>'
        )
        parts.append(
            f'<rect x="{mix_bar_x}" y="{y}" width="{max(w, 2):.1f}" height="10" rx="2" fill="{GREEN}" opacity="0.55"/>'
        )
        parts.append(
            f'<text x="{mix_bar_x + max(w, 2) + 6:.1f}" y="{y + 9}" fill="{TEXT_DIM}" font-size="9" '
            f'font-family="{FONT_SANS}">{count} ({pct:.0f}%)</text>'
        )

    footer_y = max(heatmap_y + grid_h + 16, mix_start_y + len(mix_items) * mix_row_h + 10)
    if total_events == 0:
        parts.append(
            f'<text x="{SVG_WIDTH / 2}" y="{footer_y}" fill="{TEXT_DIM}" '
            f'font-size="10" font-family="{FONT_SANS}" text-anchor="middle">'
            "No recent public events returned by GitHub API"
            "</text>"
        )

    svg_h = footer_y + 18
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{svg_h}" viewBox="0 0 {SVG_WIDTH} {svg_h}">
  <rect width="{SVG_WIDTH}" height="{svg_h}" rx="12" fill="{BG_CARD}" stroke="{BORDER}" stroke-width="1"/>
  {"".join(parts)}
</svg>"""

    with open(output_path, "w") as f:
        f.write(svg)
    return output_path

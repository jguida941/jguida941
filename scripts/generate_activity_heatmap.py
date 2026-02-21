"""Generate a day-of-week x hour-of-day activity heatmap + day-of-week bar chart."""

from collections import defaultdict
from datetime import datetime

from scripts.config import (
    BG_CARD, BLUE, GREEN, TEXT, TEXT_DIM, TEXT_BRIGHT, BORDER,
    SVG_WIDTH, FONT_SANS,
)


def _intensity_color(count: int, max_count: int) -> str:
    """Map count to a green intensity (Tokyo Night style)."""
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


def generate(
    events: list,
    output_path: str = "assets/activity_heatmap.svg",
):
    """events: list of GitHub event dicts with 'created_at' field."""
    # Build hour x day grid
    grid = defaultdict(lambda: defaultdict(int))  # grid[weekday][hour]
    day_totals = defaultdict(int)

    for event in events:
        ts = event.get("created_at", "")
        if not ts:
            continue
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            continue
        wd = dt.weekday()  # 0=Mon, 6=Sun
        hr = dt.hour
        grid[wd][hr] += 1
        day_totals[wd] += 1

    total_events = sum(day_totals.values())

    max_count = max(
        (grid[d][h] for d in range(7) for h in range(24)),
        default=1,
    )

    # Layout
    pad = 30
    title_h = 36
    day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    label_w = 36
    cell = 12
    gap = 2
    grid_w = 24 * (cell + gap) - gap
    grid_h = 7 * (cell + gap) - gap
    heatmap_x = pad + label_w
    heatmap_y = title_h + 24  # room for hour labels

    # Bar chart on the right
    bar_section_x = heatmap_x + grid_w + 40
    bar_w_max = SVG_WIDTH - bar_section_x - pad
    max_day_total = max(day_totals.values(), default=1)

    svg_h = heatmap_y + grid_h + 30

    parts = []

    # Title
    parts.append(
        f'<text x="{pad}" y="{title_h}" fill="{TEXT}" font-size="14" '
        f'font-family="{FONT_SANS}" font-weight="700">When I Code</text>'
    )
    parts.append(
        f'<text x="{pad + 110}" y="{title_h}" fill="{TEXT_DIM}" font-size="10" '
        f'font-family="{FONT_SANS}">(last 300 public events, UTC)</text>'
    )

    # Hour labels (top)
    for h in range(24):
        if h % 3 == 0:
            x = heatmap_x + h * (cell + gap) + cell / 2
            parts.append(
                f'<text x="{x}" y="{heatmap_y - 6}" fill="{TEXT_DIM}" font-size="9" '
                f'font-family="{FONT_SANS}" text-anchor="middle">{h:02d}</text>'
            )

    # Day labels + heatmap cells
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
                f'<title>{day_labels[d]} {h:02d}:00 - {c} events</title></rect>'
            )

    # Day-of-week bar chart
    parts.append(
        f'<text x="{bar_section_x}" y="{title_h}" fill="{TEXT}" font-size="12" '
        f'font-family="{FONT_SANS}" font-weight="600">By Day</text>'
    )
    for d in range(7):
        y = heatmap_y + d * (cell + gap)
        total = day_totals[d]
        w = (total / max(max_day_total, 1)) * bar_w_max * 0.85
        parts.append(
            f'<rect x="{bar_section_x}" y="{y}" width="{max(w, 2):.1f}" height="{cell}" '
            f'rx="2" fill="{GREEN}" opacity="0.7"/>'
        )
        parts.append(
            f'<text x="{bar_section_x + max(w, 2) + 6:.1f}" y="{y + cell - 1}" '
            f'fill="{TEXT_DIM}" font-size="10" font-family="{FONT_SANS}">{total}</text>'
        )

    if total_events == 0:
        parts.append(
            f'<text x="{SVG_WIDTH / 2}" y="{heatmap_y + grid_h + 18}" fill="{TEXT_DIM}" '
            f'font-size="10" font-family="{FONT_SANS}" text-anchor="middle">'
            "No recent public events returned by GitHub API"
            "</text>"
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{svg_h}" viewBox="0 0 {SVG_WIDTH} {svg_h}">
  <rect width="{SVG_WIDTH}" height="{svg_h}" rx="12" fill="{BG_CARD}" stroke="{BORDER}" stroke-width="1"/>
  {"".join(parts)}
</svg>"""

    with open(output_path, "w") as f:
        f.write(svg)
    return output_path

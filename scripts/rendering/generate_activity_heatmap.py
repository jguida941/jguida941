"""When-I-Code activity heatmap — hour x day matrix + time-block / event-mix bars.

Governed glass + locked type ladder (>=11), single accent (no rainbow), no decorative
halos. The day x hour intensity matrix keeps the heatmap shape; the two side panels
are on-ladder bar lists. Section header carries the total + timezone.
"""

import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from scripts.core.config import (
    CYAN,
    FONT_SANS,
    GLASS_HAIRLINE_HEX,
    HEATMAP_RAMP,
    SVG_WIDTH,
    TEXT,
    TEXT_BRIGHT,
    TEXT_DIM,
)
from scripts.rendering.components import empty_state, section_header
from scripts.rendering.glass_kit import glass_panel, glass_tile, icon, progress_bar

EVENT_LABELS = {
    "PushEvent": "push", "PullRequestEvent": "pull request", "PullRequestReviewEvent": "pr review",
    "IssuesEvent": "issue", "IssueCommentEvent": "comment", "ReleaseEvent": "release", "CreateEvent": "create",
}
TIME_BLOCKS = [("Night", range(0, 6)), ("Morning", range(6, 12)), ("Afternoon", range(12, 18)), ("Evening", range(18, 24))]
DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_RAMP = HEATMAP_RAMP


def _ramp_level(count: int, max_count: int) -> int:
    if count <= 0:
        return 0
    r = count / max(max_count, 1)
    return 1 if r <= 0.25 else 2 if r <= 0.5 else 3 if r <= 0.75 else 4


def _timezone() -> tuple[timezone | ZoneInfo, str]:
    tz_name = (os.environ.get("PROFILE_ACTIVITY_TZ") or "America/New_York").strip()
    try:
        return ZoneInfo(tz_name), tz_name
    except Exception:
        return timezone.utc, "UTC"


def _txt(s, x, y, *, size, fill, weight=400, anchor="start") -> str:
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    w = f' font-weight="{weight}"' if weight != 400 else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" font-size="{size}" font-family="{FONT_SANS}"{w}{a}>{s}</text>'


def _bar_panel(parts, x, y, w, h, title, rows, total_events):
    parts.append(glass_tile(x, y, w, h))
    parts.append(_txt(title.upper(), x + 16, y + 24, size=11, fill=TEXT_DIM, weight=600))
    parts.append(f'<rect x="{x + 16}" y="{y + 32}" width="{w - 32}" height="1" fill="{GLASS_HAIRLINE_HEX}" fill-opacity="0.14"/>')
    if not rows:
        parts.append(_txt("No events yet", x + 16, y + 58, size=12, fill=TEXT_DIM))
        return
    max_v = max((c for _, c in rows), default=1)
    bar_x, val_x = x + 104, x + w - 16
    bar_w = (val_x - 64) - bar_x
    ry = y + 52
    pitch = min(26.0, max(20.0, (y + h - 16 - ry) / max(len(rows), 1)))
    for i, (label, count) in enumerate(rows):
        cy = ry + i * pitch
        pct = (count / total_events * 100.0) if total_events else 0.0
        parts.append(_txt(label, x + 16, cy + 4, size=12, fill=TEXT))
        parts.append(progress_bar(bar_x, cy - 4, bar_w, 8, (count / max_v) * 100.0, color=CYAN))
        parts.append(_txt(str(count), val_x - 34, cy + 4, size=14, fill=TEXT_BRIGHT, weight=600, anchor="end"))
        parts.append(_txt(f"{pct:.0f}%", val_x, cy + 4, size=12, fill=TEXT_DIM, anchor="end"))


def generate(events: list, output_path: str = "assets/activity_heatmap.svg"):
    tz, tz_label = _timezone()
    grid = defaultdict(lambda: defaultdict(int))
    block_totals, event_mix = Counter(), Counter()
    for event in events or []:
        label = EVENT_LABELS.get(event.get("type", ""))
        ts = event.get("created_at", "")
        if label is None or not ts:
            continue
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(tz)
        except ValueError:
            continue
        grid[dt.weekday()][dt.hour] += 1
        event_mix[label] += 1
        for name, hrs in TIME_BLOCKS:
            if dt.hour in hrs:
                block_totals[name] += 1
                break

    total_events = sum(event_mix.values())
    max_count = max((grid[d][h] for d in range(7) for h in range(24)), default=1)
    tz_short = tz_label.rsplit("/", 1)[-1].replace("_", " ")

    width, pad = SVG_WIDTH, 28
    header_svg, content_top = section_header(
        pad, 46, "When I Code", width=width, eyebrow="Activity Rhythm",
        right_text=f"{total_events} events · {tz_short}", pad=pad,
    )

    if total_events == 0:
        empty_header, _ = section_header(pad, 46, "When I Code", width=width, eyebrow="Activity Rhythm", pad=pad)
        height = int(content_top + 92)
        body = "".join([glass_panel(width, height), empty_header,
                        empty_state(width / 2, content_top + 48, "No recent public activity returned", icon_name="clock")])
        with open(output_path, "w") as f:
            f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">{body}</svg>')
        return output_path

    # geometry: heatmap tile (left) + two bar panels (right)
    cell, gap = 14, 3
    step = cell + gap
    hm_x, hm_y, hm_w = pad, content_top + 8, 452
    grid_x, grid_y = hm_x + 44, hm_y + 44
    grid_bottom = grid_y + 7 * step - gap
    legend_y = grid_bottom + 20

    r_x = hm_x + hm_w + 16
    r_w = width - pad - r_x
    a_h = 132
    b_y = hm_y + a_h + 14

    content_bottom = max(legend_y + 24, b_y + 150)
    hm_h = content_bottom - hm_y
    height = int(content_bottom + 18)

    parts = [glass_panel(width, height), header_svg, glass_tile(hm_x, hm_y, hm_w, hm_h)]

    # hour axis (every 3h, >=11)
    for h in range(0, 24, 3):
        parts.append(_txt(f"{h:02d}", grid_x + h * step + cell / 2, grid_y - 12, size=11, fill=TEXT_DIM, anchor="middle"))
    # day labels (>=11)
    for d in range(7):
        parts.append(_txt(DAY_LABELS[d], grid_x - 12, grid_y + d * step + cell - 3, size=11, fill=TEXT_DIM, anchor="end"))
    # cells (ramp = data intensity; no decorative halos)
    for d in range(7):
        cy = grid_y + d * step
        for h in range(24):
            c = grid[d][h]
            hexc, op = _RAMP[_ramp_level(c, max_count)]
            parts.append(
                f'<rect x="{grid_x + h * step:.1f}" y="{cy:.1f}" width="{cell}" height="{cell}" rx="3" '
                f'fill="{hexc}" fill-opacity="{op}"><title>{DAY_LABELS[d]} {h:02d}:00 — {c} events</title></rect>'
            )
    # legend (>=11)
    parts.append(_txt("Less", grid_x - 12, legend_y + 9, size=11, fill=TEXT_DIM))
    sx = grid_x + 20
    for hexc, op in _RAMP:
        parts.append(f'<rect x="{sx:.1f}" y="{legend_y:.1f}" width="11" height="11" rx="2" fill="{hexc}" fill-opacity="{op}"/>')
        sx += 15
    parts.append(_txt("More", sx + 2, legend_y + 9, size=11, fill=TEXT_DIM))

    # right panels
    _bar_panel(parts, r_x, hm_y, r_w, a_h, "By Time Block",
               [(n, block_totals.get(n, 0)) for n, _ in TIME_BLOCKS], total_events)
    _bar_panel(parts, r_x, b_y, r_w, content_bottom - b_y, "Event Mix",
               event_mix.most_common(5), total_events)

    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">{"".join(parts)}</svg>'
    with open(output_path, "w") as f:
        f.write(svg)
    return output_path

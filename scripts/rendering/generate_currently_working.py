"""Build the Currently Working On card.

Power BI information architecture (DESIGN_SPEC): the count of repos pushed in the
window is the one dominant KPI top-left, and the repos list as uniform repository
rows (language by dot AND label). An honest empty state renders when nothing was
pushed in the window.
"""

from __future__ import annotations

from datetime import datetime, timezone

from scripts.core.config import SPACE, SVG_WIDTH, TEXT_DIM
from scripts.rendering.components import (
    empty_state,
    primary_kpi,
    repository_row,
    section_header,
)
from scripts.rendering.glass_kit import glass_panel

PAD = 28
KPI_W = 200
ROW_PITCH = 56
ROW_H = 50


def _time_ago(iso_str: str) -> str:
    """Compact relative time ('just now' / 'Xh ago' / 'Xd ago') from an ISO ts."""
    try:
        dt = datetime.fromisoformat((iso_str or "").replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return ""
    delta = datetime.now(timezone.utc) - dt
    hours = delta.total_seconds() / 3600
    if hours < 1:
        return "just now"
    if hours < 24:
        return f"{int(hours)}h ago"
    return f"{int(hours // 24)}d ago"


def generate(repos: list, output_path: str = "assets/currently_working.svg"):
    width = SVG_WIDTH
    repos = list(repos or [])

    header_svg, content_top = section_header(
        PAD, 46, "Currently Working On", width=width,
        eyebrow="Active Development", right_text="Last 7 days", pad=PAD,
    )

    if not repos:
        empty_header, _ = section_header(
            PAD, 46, "Currently Working On", width=width, eyebrow="Active Development", pad=PAD
        )
        height = int(content_top + 92)
        body = "".join(
            [
                glass_panel(width, height),
                empty_header,
                empty_state(width / 2, content_top + 48, "No repositories pushed recently", icon_name="clock"),
            ]
        )
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">{body}</svg>'
        )
        with open(output_path, "w") as f:
            f.write(svg)
        return output_path

    rows_x = PAD + KPI_W + SPACE["xl"]
    rows_w = width - PAD - rows_x
    rows_top = content_top + 4
    rows_bottom = rows_top + len(repos) * ROW_PITCH
    height = int(max(rows_bottom, content_top + 100) + 22)

    parts = [glass_panel(width, height), header_svg]
    parts.append(
        primary_kpi(
            PAD, content_top + 58,
            value=str(len(repos)), label="active repos", sublabel="last 7 days",
        )
    )
    parts.append(
        f'<rect x="{PAD + KPI_W:g}" y="{content_top + 6:g}" width="1" '
        f'height="{rows_bottom - content_top - 6:g}" fill="{TEXT_DIM}" fill-opacity="0.16"/>'
    )
    for i, repo in enumerate(repos):
        is_private = bool(repo.get("is_private"))
        parts.append(
            repository_row(
                rows_x,
                rows_top + i * ROW_PITCH,
                rows_w,
                name=str(repo.get("name", "")),
                language=repo.get("language"),
                timestamp=_time_ago(repo.get("pushed_at", "")),
                detail=None if is_private else (repo.get("last_commit_msg") or None),
                is_private=is_private,
                url=(repo.get("html_url") or "").strip() or None,
                row_h=ROW_H,
            )
        )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">{"".join(parts)}</svg>'
    )
    with open(output_path, "w") as f:
        f.write(svg)
    return output_path

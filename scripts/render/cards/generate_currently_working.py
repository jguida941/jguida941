"""Generate an Apple/glass SVG card of repos pushed in the last 7 days."""

from __future__ import annotations

from datetime import datetime, timezone

from scripts.config import (
    CYAN,
    FONT_SANS,
    GLASS_INSET,
    SVG_WIDTH,
    TEXT,
    TEXT_BRIGHT,
    TEXT_DIM,
)
from scripts.render.card_theme import title_left, title_right
from scripts.render.glass_kit import accent_ribbon, glass_panel, glass_tile, icon
from scripts.render.svg_utils import lang_color, truncate, xml_escape

TITLE = "Currently Working On"
SUBTITLE = "pushed in the last 7 days"

# --- Layout (px) ---------------------------------------------------------- #
W = SVG_WIDTH            # 840
PAD = 30                # text inset from the SVG edge
TITLE_Y = 44            # title / subtitle baseline
RIBBON_Y = 58           # accent ribbon
HEADER_H = 78           # top of the first row tile
ROW_H = 58              # vertical pitch per repo row
TILE_H = 48             # row tile height (ROW_H - TILE_H = inter-row gap)
TILE_X = 28             # row tile left edge (inside the panel inset of 12)
TILE_W = W - TILE_X * 2  # row tile width


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


def _header() -> str:
    """Header icon + exactly-one title node + subtitle + calm accent ribbon."""
    return "".join(
        [
            icon("code", PAD, 30, size=16, color=CYAN),
            title_left(TITLE, x=PAD + 24, y=TITLE_Y),
            title_right(SUBTITLE, width=W, pad=PAD, y=TITLE_Y),
            accent_ribbon(W, pad=PAD, y=RIBBON_Y),
        ]
    )


def _row(repo: dict, tile_y: float) -> str:
    """One frosted row tile for a single repo."""
    name = truncate(str(repo.get("name", "")), 42)
    lang = repo.get("language")
    color = lang_color(lang)
    is_private = bool(repo.get("is_private"))
    url = (repo.get("html_url") or "").strip()
    ago = _time_ago(repo.get("pushed_at", ""))
    # Private repos carry no commit message; show language + time only.
    msg = "" if is_private else truncate(str(repo.get("last_commit_msg") or ""), 64)

    name_y = tile_y + 21          # name baseline (line 1, aligned across rows)
    meta_y = tile_y + 38          # commit / language baseline (line 2)
    dot_r = 4.5
    name_x = TILE_X + 36
    right_x = TILE_X + TILE_W - 18

    parts = [
        glass_tile(TILE_X, tile_y, TILE_W, TILE_H),
        # language dot (always), vertically centered on the name line
        icon("lang_dot", TILE_X + 21 - dot_r, name_y - 4 - dot_r, size=9, color=color),
    ]

    text_x = name_x
    if is_private:
        parts.append(icon("lock", name_x, name_y - 11, size=12, color=TEXT_DIM))
        text_x = name_x + 18

    name_node = (
        f'<text x="{text_x}" y="{name_y}" fill="{TEXT_BRIGHT}" font-size="13.5" '
        f'font-family="{FONT_SANS}" font-weight="700">{xml_escape(name)}</text>'
    )
    if url and not is_private:
        name_node = f'<a href="{xml_escape(url)}">{name_node}</a>'
    parts.append(name_node)

    if msg:
        parts.append(
            f'<text x="{name_x}" y="{meta_y}" fill="{TEXT}" font-size="11.5" '
            f'font-family="{FONT_SANS}">{xml_escape(msg)}</text>'
        )

    if ago:
        parts.append(
            f'<text x="{right_x}" y="{name_y}" fill="{TEXT_BRIGHT}" font-size="12.5" '
            f'font-family="{FONT_SANS}" font-weight="700" text-anchor="end">{ago}</text>'
        )
    parts.append(
        f'<text x="{right_x}" y="{meta_y}" fill="{TEXT_DIM}" font-size="10.5" '
        f'font-family="{FONT_SANS}" text-anchor="end">{xml_escape(lang) if lang else "—"}</text>'
    )
    return "".join(parts)


def _empty_state() -> str:
    """Tasteful empty card when nothing was pushed in the window."""
    h = 152
    cx = W / 2
    body = "".join(
        [
            glass_panel(W, h),
            _header(),
            glass_tile(TILE_X, 86, TILE_W, 46),
            icon("clock", cx - 150, 99, size=16, color=TEXT_DIM),
            f'<text x="{cx - 128}" y="114" fill="{TEXT}" font-size="13" '
            f'font-family="{FONT_SANS}">No repositories pushed in the last 7 days</text>',
        ]
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" '
        f'viewBox="0 0 {W} {h}">{body}</svg>'
    )


def generate(repos: list, output_path: str = "assets/currently_working.svg"):
    """repos: list of dicts with keys name, html_url, language, pushed_at,
    last_commit_msg, is_private."""
    if not repos:
        svg = _empty_state()
        with open(output_path, "w") as f:
            f.write(svg)
        return output_path

    # Data-driven height: header + rows (each ROW_H includes its trailing gap) +
    # a small inner pad + the GLASS_INSET shadow margin so nothing clips.
    svg_h = HEADER_H + len(repos) * ROW_H + 4 + GLASS_INSET

    rows = "".join(_row(repo, HEADER_H + i * ROW_H) for i, repo in enumerate(repos))
    body = "".join([glass_panel(W, svg_h), _header(), rows])
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{svg_h}" '
        f'viewBox="0 0 {W} {svg_h}">{body}</svg>'
    )

    with open(output_path, "w") as f:
        f.write(svg)
    return output_path

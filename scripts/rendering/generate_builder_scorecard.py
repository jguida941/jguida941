"""Build the builder scorecard SVG (Apple glass / frosted look).

Data-length-driven 4-column grid of frosted metric tiles. Each tile shows a
leading line-icon, the headline ``display_value`` as a big bold number, the
metric label, and a dim caption. The grid height is sized from the number of
tiles (rows = ceil(len(tiles) / cols)), never hardcoded.
"""

from __future__ import annotations

import math

from scripts.core.config import (
    BLUE,
    CYAN,
    FONT_SANS,
    GREEN,
    ORANGE,
    PURPLE,
    SVG_WIDTH,
    TEXT,
    TEXT_BRIGHT,
    TEXT_DIM,
)
from scripts.rendering.card_theme import title_left
from scripts.rendering.glass_kit import (
    accent_ribbon,
    chip,
    chip_width,
    eyebrow_text,
    glass_panel,
    glass_tile,
    icon,
    progress_ring,
)
from scripts.contracts.profile_contract import SCORECARD_METRICS, format_metric_value
from scripts.rendering.svg_utils import truncate, xml_escape

TITLE = "Builder Scorecard"

# A sensible SF-Symbols-style icon per scorecard metric (fallback: lang_dot).
ICON_BY_KEY = {
    "last_year_contributions": "fire",
    "active_days_last_year": "calendar",
    "active_repos_7d": "commit",
    "ci_coverage_pct": "ci_check",
    "automation_workflows": "workflow",
    "releases_30d": "release_tag",
    "primary_lang_share_pct": "code",
    "median_days_since_push": "clock",
}

_ACCENT_MAP = {"BLUE": BLUE, "CYAN": CYAN, "GREEN": GREEN, "ORANGE": ORANGE, "PURPLE": PURPLE}


def _default_tiles(scorecard: dict) -> list[dict]:
    """Build the 8-tile list straight from the metric contract (fallback path)."""
    tiles: list[dict] = []
    for definition in SCORECARD_METRICS:
        key = definition["key"]
        tiles.append(
            {
                "key": key,
                "label": definition["label"],
                "detail": definition["detail"],
                "value": scorecard.get(key, 0),
                "display_value": format_metric_value(scorecard.get(key), definition),
                "accent": _ACCENT_MAP.get(definition.get("accent", "CYAN"), CYAN),
            }
        )
    return tiles


def _render_tile(x: float, y: float, w: float, h: float, tile: dict) -> str:
    """One frosted metric tile: accent bar + icon + big number + label + caption."""
    key = str(tile.get("key", ""))
    accent = str(tile.get("accent") or CYAN)
    label = xml_escape(truncate(str(tile.get("label", "")), 22))
    detail = xml_escape(truncate(str(tile.get("detail", "")), 32))

    display_value = tile.get("display_value")
    if display_value is None:
        display_value = tile.get("value", "0")
    value = xml_escape(str(display_value))

    icon_name = ICON_BY_KEY.get(key, "lang_dot")
    ix = x + 16

    parts = [glass_tile(x, y, w, h)]
    # leading line-icon — neutral secondary (Apple: color isn't a per-tile
    # decoration; the big number leads, color is reserved for one signal)
    parts.append(icon(icon_name, ix, y + 24, size=16, color=TEXT_DIM))

    is_ring = key == "ci_coverage_pct"
    if is_ring:
        # CI coverage reads as a small donut gauge instead of a plain number.
        try:
            pct = float(tile.get("value"))
        except (TypeError, ValueError):
            pct = 0.0
        ring_cx = x + w - 32
        ring_cy = y + 50
        parts.append(
            progress_ring(
                ring_cx,
                ring_cy,
                19,
                pct,
                color=accent,
                stroke=5,
                label=value,
                label_size=10,
            )
        )
    else:
        parts.append(
            f'<text x="{ix:g}" y="{y + 63:g}" fill="{TEXT_BRIGHT}" font-size="29" '
            f'font-family="{FONT_SANS}" font-weight="700">{value}</text>'
        )

    parts.append(
        f'<text x="{ix:g}" y="{y + 86:g}" fill="{TEXT}" font-size="11.5" '
        f'font-family="{FONT_SANS}" font-weight="600">{label}</text>'
    )
    parts.append(
        f'<text x="{ix:g}" y="{y + 103:g}" fill="{TEXT_DIM}" font-size="10" '
        f'font-family="{FONT_SANS}">{detail}</text>'
    )
    return "".join(parts)


def generate(scorecard: dict, output_path: str = "assets/builder_scorecard.svg", tiles: list | None = None) -> str:
    """Render the Builder Scorecard card.

    scorecard: raw metric dict (used to build tiles when ``tiles`` is omitted).
    tiles: list of ``{key,label,detail,value,display_value,accent}`` dicts. The
    grid is data-length-driven (cols=4, rows=ceil(n/4)) and the SVG height is
    sized from the row count plus a margin so the glass shadow never clips.
    """
    width = SVG_WIDTH
    pad = 24
    gap = 14
    cols = 4

    card_tiles = tiles or _default_tiles(scorecard)
    count = len(card_tiles)
    rows = max(1, math.ceil(count / cols))

    tile_w = (width - pad * 2 - gap * (cols - 1)) / cols
    tile_h = 120
    header_h = 90          # eyebrow + title + ribbon (top 12px is the glass inset)
    bottom_pad = 22        # below the grid (includes the 12px glass inset margin)
    svg_h = int(header_h + rows * tile_h + (rows - 1) * gap + bottom_pad)

    parts: list[str] = [glass_panel(width, svg_h)]

    # Header: eyebrow caption, single title node, calm ribbon, source chip.
    parts.append(eyebrow_text("GitHub Signals · Last 12 Months", x=pad, y=33))
    parts.append(title_left(TITLE, x=pad, y=57, size=17))
    parts.append(accent_ribbon(width, pad=pad, y=68))

    chip_text = "GitHub API"
    cw = chip_width(chip_text, size=10, icon=True)
    parts.append(
        chip(width - pad - cw, 41, chip_text, color=CYAN, icon_name="globe", filled=True, size=10, width=cw)
    )

    # Data-length-driven grid of frosted tiles.
    for i, tile in enumerate(card_tiles):
        row = i // cols
        col = i % cols
        x = pad + col * (tile_w + gap)
        y = header_h + row * (tile_h + gap)
        parts.append(_render_tile(x, y, tile_w, tile_h, tile))

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{svg_h}" '
        f'viewBox="0 0 {width} {svg_h}">'
        + "".join(parts)
        + "</svg>"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    return output_path

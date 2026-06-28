"""Build a Now/Next/Shipped focus board SVG (Apple glass re-skin)."""

from __future__ import annotations

from scripts.config import (
    CYAN,
    GREEN,
    ORANGE,
    FONT_SANS,
    SVG_WIDTH,
    TEXT,
    TEXT_BRIGHT,
    TEXT_DIM,
    GLASS_HAIRLINE_HEX,
    GLASS_HAIRLINE_OP,
)
from scripts.render.card_theme import title_left
from scripts.render.glass_kit import (
    accent_ribbon,
    chip,
    chip_width,
    glass_panel,
    glass_tile,
    icon,
)
from scripts.render.svg_utils import xml_escape, truncate

# Layout constants -----------------------------------------------------------
_PAD = 24                 # content margin (sits inside the 12px glass inset)
_GAP = 14                 # gap between lane columns
_TITLE_Y = 34
_RIBBON_Y = 46
_LANE_Y = 64
_LANE_H = 188
_SVG_H = _LANE_Y + _LANE_H + 28   # +28 reserves the glass drop-shadow margin

_SLOT_H = 44              # vertical pitch between item rows
_ITEM_TOP = 64           # first title baseline, relative to lane top


def _lane(x: float, items: list[dict], label: str, accent: str) -> str:
    """Render one frosted lane column (header + up to 3 items)."""
    col_w = (SVG_WIDTH - _PAD * 2 - _GAP * 2) / 3
    parts: list[str] = [glass_tile(x, _LANE_Y, col_w, _LANE_H)]

    # --- lane header: accent dot + label + count chip ----------------------
    parts.append(icon("lang_dot", x + 14, _LANE_Y + 16, size=8, color=accent))
    parts.append(
        f'<text x="{x + 28:.2f}" y="{_LANE_Y + 25}" fill="{accent}" font-size="12" '
        f'font-family="{FONT_SANS}" font-weight="700" '
        f'letter-spacing="1.2">{label.upper()}</text>'
    )
    count = str(len(items))
    cw = chip_width(count, size=11)
    parts.append(
        chip(
            x + col_w - 12 - cw,
            _LANE_Y + 9,
            count,
            color=accent,
            filled=True,
            size=11,
            height=22,
            width=cw,
        )
    )

    # --- divider under header ----------------------------------------------
    parts.append(
        f'<rect x="{x + 14:.2f}" y="{_LANE_Y + 38}" width="{col_w - 28:.2f}" '
        f'height="1" fill="{GLASS_HAIRLINE_HEX}" fill-opacity="{GLASS_HAIRLINE_OP}"/>'
    )

    # --- empty lane --------------------------------------------------------
    if not items:
        parts.append(
            f'<text x="{x + col_w / 2:.2f}" y="{_LANE_Y + 118}" fill="{TEXT_DIM}" '
            f'font-size="11" font-family="{FONT_SANS}" text-anchor="middle">'
            f'No items in this lane.</text>'
        )
        return "".join(parts)

    title_x = x + 32
    for i, item in enumerate(items[:3]):
        ty = _LANE_Y + _ITEM_TOP + i * _SLOT_H
        is_private = bool(item.get("is_private"))
        title = truncate(xml_escape(item.get("title", "item")), 30)
        detail = truncate(xml_escape(item.get("detail", "")), 36)
        url = xml_escape(item.get("url", "") or "")

        # leading marker: lock (private) or accent dot (public)
        if is_private:
            parts.append(icon("lock", x + 12, ty - 11, size=13, color=accent))
        else:
            parts.append(icon("lang_dot", x + 13, ty - 7.5, size=7, color=accent))

        title_node = (
            f'<text x="{title_x:.2f}" y="{ty}" fill="{TEXT_BRIGHT}" font-size="12" '
            f'font-family="{FONT_SANS}" font-weight="600">{title}</text>'
        )
        # link only non-private items that carry a url
        if url and not is_private:
            parts.append(f'<a href="{url}">{title_node}</a>')
        else:
            parts.append(title_node)

        if detail:
            parts.append(
                f'<text x="{title_x:.2f}" y="{ty + 17}" fill="{TEXT_DIM}" '
                f'font-size="10.5" font-family="{FONT_SANS}">{detail}</text>'
            )

    return "".join(parts)


def generate(focus: dict, output_path: str = "assets/now_next_shipped.svg") -> str:
    lanes = [
        ("now", "Now", CYAN),
        ("next", "Next", ORANGE),
        ("shipped", "Shipped", GREEN),
    ]
    col_w = (SVG_WIDTH - _PAD * 2 - _GAP * 2) / 3

    parts: list[str] = [glass_panel(SVG_WIDTH, _SVG_H)]

    # header: title + calm ribbon + flow caption
    parts.append(title_left("Current Focus", x=_PAD, y=_TITLE_Y))
    parts.append(
        f'<text x="{SVG_WIDTH - _PAD}" y="{_TITLE_Y}" fill="{TEXT_DIM}" font-size="11" '
        f'font-family="{FONT_SANS}" text-anchor="end" letter-spacing="0.4">'
        f'now &#47; next &#47; shipped</text>'
    )
    parts.append(accent_ribbon(SVG_WIDTH, pad=_PAD, y=_RIBBON_Y, h=3))

    for idx, (key, label, accent) in enumerate(lanes):
        x = _PAD + idx * (col_w + _GAP)
        items = focus.get(key, []) if isinstance(focus, dict) else []
        if not isinstance(items, list):
            items = []
        parts.append(_lane(x, items, label, accent))

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" '
        f'height="{_SVG_H}" viewBox="0 0 {SVG_WIDTH} {_SVG_H}">'
        f'{"".join(parts)}'
        f'</svg>'
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    return output_path

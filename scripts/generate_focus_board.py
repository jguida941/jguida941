"""Build a Now/Next/Shipped focus board SVG."""

from __future__ import annotations

from scripts.config import (
    BG_HIGHLIGHT,
    BLUE,
    CYAN,
    GREEN,
    ORANGE,
    TEXT,
    BORDER,
    SVG_WIDTH,
    FONT_SANS,
)
from scripts.card_theme import card_bg, title_left, title_right


def _esc(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _truncate(value: str, max_len: int) -> str:
    text = (value or "").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def generate(focus: dict, output_path: str = "assets/now_next_shipped.svg") -> str:
    columns = [
        ("now", "Now", CYAN),
        ("next", "Next", ORANGE),
        ("shipped", "Shipped", GREEN),
    ]

    pad = 20
    header_h = 52
    col_gap = 14
    col_w = (SVG_WIDTH - pad * 2 - col_gap * 2) / 3
    col_h = 198
    svg_h = header_h + col_h + pad

    parts = [
        title_left("Current Focus", x=pad, y=29),
        title_right("now / next / shipped lanes", width=SVG_WIDTH, pad=pad, y=29),
    ]

    for idx, (key, label, accent) in enumerate(columns):
        x = pad + idx * (col_w + col_gap)
        y = header_h
        parts.append(
            f'<rect x="{x}" y="{y}" width="{col_w}" height="{col_h}" rx="12" '
            f'fill="{BG_HIGHLIGHT}" stroke="{BORDER}" stroke-width="1"/>'
        )
        parts.append(
            f'<rect x="{x}" y="{y}" width="{col_w}" height="4" rx="12" fill="{accent}"/>'
        )
        parts.append(
            f'<text x="{x + 14}" y="{y + 24}" fill="{accent}" font-size="12" '
            f'font-family="{FONT_SANS}" font-weight="700">{label}</text>'
        )

        items = focus.get(key, []) if isinstance(focus, dict) else []
        if not items:
            parts.append(
                f'<text x="{x + 14}" y="{y + 50}" fill="{TEXT}" font-size="11" '
                f'font-family="{FONT_SANS}">No items in this lane.</text>'
            )
            continue

        for item_idx, item in enumerate(items[:3]):
            iy = y + 42 + item_idx * 48
            title = _truncate(_esc(item.get("title", "item")), 35)
            detail = _truncate(_esc(item.get("detail", "")), 52)
            url = _esc(item.get("url", ""))

            parts.append(f'<circle cx="{x + 14}" cy="{iy + 4}" r="3" fill="{accent}"/>')
            if url:
                parts.append(
                    f'<a href="{url}"><text x="{x + 23}" y="{iy + 8}" fill="{BLUE}" '
                    f'font-size="12" font-family="{FONT_SANS}" font-weight="600">{title}</text></a>'
                )
            else:
                parts.append(
                    f'<text x="{x + 23}" y="{iy + 8}" fill="{BLUE}" '
                    f'font-size="12" font-family="{FONT_SANS}" font-weight="600">{title}</text>'
                )
            parts.append(
                f'<text x="{x + 23}" y="{iy + 24}" fill="{TEXT}" '
                f'font-size="11" font-family="{FONT_SANS}">{detail}</text>'
            )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{svg_h}" viewBox="0 0 {SVG_WIDTH} {svg_h}">
  {card_bg(SVG_WIDTH, svg_h)}
  {''.join(parts)}
</svg>'''

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    return output_path

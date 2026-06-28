"""Build a language usage bar chart SVG (Apple/glassmorphism style)."""

from scripts.core.config import (
    FONT_SANS,
    GLASS_HAIRLINE_HEX,
    GLASS_INSET,
    GLASS_SHEEN_HEX,
    GLASS_TILE_SHADE_HEX,
    SVG_WIDTH,
    TEXT,
    TEXT_BRIGHT,
    TEXT_DIM,
)
from scripts.rendering.card_theme import title_left
from scripts.rendering.glass_kit import eyebrow_text, glass_panel
from scripts.rendering.svg_utils import fmt_int, lang_color, truncate, xml_escape

TITLE = "Language Breakdown"

# Layout constants (content padding sits comfortably inside the 12px glass inset).
PAD = 34
BAR_X = PAD
BAR_W = SVG_WIDTH - 2 * PAD
BAR_Y = 70
BAR_H = 34
BAR_RX = 10
LEGEND_COLS = 3
LEGEND_ROW_H = 30
LEGEND_TOP = BAR_Y + BAR_H + 36  # baseline of the first legend row
BOTTOM_MARGIN = 34               # >= glass inset so the drop shadow never clips


def _human_bytes(n: float) -> str:
    """Compact, human-readable byte size (decimal units, e.g. '24.4 MB')."""
    n = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1000:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1000.0
    return f"{n:.1f} TB"


def _empty_card(output_path: str) -> str:
    """Frosted fallback when there is no language data."""
    height = 108
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" '
        f'height="{height}" viewBox="0 0 {SVG_WIDTH} {height}">'
        f"{glass_panel(SVG_WIDTH, height)}"
        f"{title_left(TITLE, x=PAD, y=46)}"
        f'<text x="{SVG_WIDTH / 2}" y="78" fill="{TEXT_DIM}" font-size="13" '
        f'font-family="{FONT_SANS}" text-anchor="middle">'
        f"No language data available</text>"
        f"</svg>"
    )
    with open(output_path, "w") as f:
        f.write(svg)
    return output_path


def generate(
    language_bytes: dict,
    output_path: str = "assets/lang_breakdown.svg",
    top_n: int = 8,
):
    total = sum(language_bytes.values())
    if total <= 0:
        return _empty_card(output_path)

    sorted_langs = sorted(language_bytes.items(), key=lambda x: x[1], reverse=True)
    top = sorted_langs[:top_n]
    other_bytes = sum(b for _, b in sorted_langs[top_n:])
    if other_bytes > 0:
        top.append(("Other", other_bytes))

    items = [(lang, b, b / total * 100.0) for lang, b in top]

    # --- Data-driven height (add the glass inset margin) -------------------- #
    rows = (len(items) + LEGEND_COLS - 1) // LEGEND_COLS
    last_baseline = LEGEND_TOP + (rows - 1) * LEGEND_ROW_H
    svg_h = last_baseline + BOTTOM_MARGIN

    # --- Header ------------------------------------------------------------- #
    subtitle = f"{fmt_int(len(language_bytes))} languages · {_human_bytes(total)}"

    header = (
        eyebrow_text("REPOSITORY COMPOSITION", x=PAD, y=30)
        + title_left(TITLE, x=PAD, y=52)
        + f'<text x="{SVG_WIDTH - PAD}" y="52" fill="{TEXT_DIM}" font-size="11.5" '
        f'font-family="{FONT_SANS}" text-anchor="end">{xml_escape(subtitle)}</text>'
    )

    # --- Defs: rounded clip for the bar + glossy sheen --------------------- #
    defs = (
        '<defs>'
        f'<clipPath id="langBarClip">'
        f'<rect x="{BAR_X}" y="{BAR_Y}" width="{BAR_W}" height="{BAR_H}" rx="{BAR_RX}"/>'
        f'</clipPath>'
        '<linearGradient id="langBarSheen" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{GLASS_SHEEN_HEX}" stop-opacity="0.26"/>'
        f'<stop offset="0.45" stop-color="{GLASS_SHEEN_HEX}" stop-opacity="0.04"/>'
        f'<stop offset="0.55" stop-color="{GLASS_TILE_SHADE_HEX}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="{GLASS_TILE_SHADE_HEX}" stop-opacity="0.28"/>'
        '</linearGradient>'
        '</defs>'
    )

    # --- Stacked bar -------------------------------------------------------- #
    # Track underlay so the rounded ends read even at sub-pixel edges.
    seg_parts = [
        f'<rect x="{BAR_X}" y="{BAR_Y}" width="{BAR_W}" height="{BAR_H}" '
        f'rx="{BAR_RX}" fill="{GLASS_TILE_SHADE_HEX}" fill-opacity="0.45"/>'
    ]
    x = float(BAR_X)
    n = len(items)
    for i, (lang, _b, pct) in enumerate(items):
        # Last segment snaps to the bar end to avoid a sliver gap.
        seg_end = BAR_X + BAR_W if i == n - 1 else x + BAR_W * pct / 100.0
        w = max(0.0, seg_end - x)
        seg_parts.append(
            f'<rect x="{x:.2f}" y="{BAR_Y}" width="{w:.2f}" height="{BAR_H}" '
            f'fill="{lang_color(lang)}"><title>{xml_escape(lang)}: {pct:.1f}%</title></rect>'
        )
        # Thin separator between segments (subtle dark hairline gap).
        if i < n - 1 and w > 0:
            seg_parts.append(
                f'<rect x="{seg_end - 0.75:.2f}" y="{BAR_Y}" width="1.5" '
                f'height="{BAR_H}" fill="{GLASS_TILE_SHADE_HEX}" fill-opacity="0.55"/>'
            )
        x = seg_end

    bar = (
        f'<g clip-path="url(#langBarClip)">'
        + "".join(seg_parts)
        # glossy sheen over the whole bar
        + f'<rect x="{BAR_X}" y="{BAR_Y}" width="{BAR_W}" height="{BAR_H}" '
        f'fill="url(#langBarSheen)"/>'
        + '</g>'
        # crisp hairline rim around the bar
        + f'<rect x="{BAR_X + 0.5}" y="{BAR_Y + 0.5}" width="{BAR_W - 1}" '
        f'height="{BAR_H - 1}" rx="{BAR_RX}" fill="none" stroke="{GLASS_HAIRLINE_HEX}" '
        f'stroke-opacity="0.18" stroke-width="1"/>'
    )

    # --- Legend (multi-column: dot + name + right-aligned percent) --------- #
    col_w = BAR_W / LEGEND_COLS
    legend_parts = []
    for i, (lang, _b, pct) in enumerate(items):
        col = i % LEGEND_COLS
        row = i // LEGEND_COLS
        cell_x = PAD + col * col_w
        base_y = LEGEND_TOP + row * LEGEND_ROW_H
        color = lang_color(lang)
        name = xml_escape(truncate(lang, 16))
        legend_parts.append(
            # swatch dot with a faint rim for that glassy bevel
            f'<circle cx="{cell_x + 6:.1f}" cy="{base_y - 4:.1f}" r="5" fill="{color}"/>'
            f'<circle cx="{cell_x + 6:.1f}" cy="{base_y - 4:.1f}" r="5" fill="none" '
            f'stroke="{GLASS_SHEEN_HEX}" stroke-opacity="0.22" stroke-width="1"/>'
            # language name (secondary text)
            f'<text x="{cell_x + 19:.1f}" y="{base_y:.1f}" fill="{TEXT}" font-size="12.5" '
            f'font-family="{FONT_SANS}" font-weight="500">{name}</text>'
            # percent (primary: bright + bold), right-aligned in the column
            f'<text x="{cell_x + col_w - 16:.1f}" y="{base_y:.1f}" fill="{TEXT_BRIGHT}" '
            f'font-size="12.5" font-family="{FONT_SANS}" font-weight="700" '
            f'text-anchor="end">{pct:.1f}%</text>'
        )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" '
        f'height="{svg_h}" viewBox="0 0 {SVG_WIDTH} {svg_h}">'
        f"{glass_panel(SVG_WIDTH, svg_h)}"
        f"{defs}"
        f"{header}"
        f"{bar}"
        f"{''.join(legend_parts)}"
        f"</svg>"
    )

    with open(output_path, "w") as f:
        f.write(svg)
    return output_path

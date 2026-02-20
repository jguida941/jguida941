"""Generate a horizontal stacked bar + legend for language usage by bytes."""

from scripts.config import (
    BG_DARK, BG_CARD, TEXT, TEXT_DIM, TEXT_BRIGHT, BORDER,
    SVG_WIDTH, FONT_SANS, LANG_COLORS,
)


def _lang_color(lang: str) -> str:
    return LANG_COLORS.get(lang, "#8b8b8b")


def generate(
    language_bytes: dict,
    output_path: str = "assets/lang_breakdown.svg",
    top_n: int = 8,
):
    total = sum(language_bytes.values())
    if total == 0:
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="80" viewBox="0 0 {SVG_WIDTH} 80">
  <rect width="{SVG_WIDTH}" height="80" rx="12" fill="{BG_CARD}" stroke="{BORDER}" stroke-width="1"/>
  <text x="420" y="45" fill="{TEXT_DIM}" font-size="13" font-family="{FONT_SANS}" text-anchor="middle">No language data available</text>
</svg>"""
        with open(output_path, "w") as f:
            f.write(svg)
        return output_path

    sorted_langs = sorted(language_bytes.items(), key=lambda x: x[1], reverse=True)
    top = sorted_langs[:top_n]
    other_bytes = sum(b for _, b in sorted_langs[top_n:])
    if other_bytes > 0:
        top.append(("Other", other_bytes))

    # Percentages
    items = [(lang, bytes_, bytes_ / total * 100) for lang, bytes_ in top]

    # Layout
    pad = 30
    bar_y = 40
    bar_h = 24
    bar_w = SVG_WIDTH - 2 * pad
    legend_y = bar_y + bar_h + 30
    cols = 3
    col_w = bar_w // cols
    row_h = 24
    rows = (len(items) + cols - 1) // cols
    svg_h = legend_y + rows * row_h + 20

    # Stacked bar with clipPath for rounded corners
    clip_def = (
        f'<defs><clipPath id="barClip">'
        f'<rect x="{pad}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="6"/>'
        f'</clipPath></defs>'
    )

    bar_parts = []
    x = pad
    for lang, _, pct in items:
        w = bar_w * pct / 100
        bar_parts.append(
            f'<rect x="{x:.1f}" y="{bar_y}" width="{w:.1f}" height="{bar_h}" '
            f'fill="{_lang_color(lang)}">'
            f'<title>{lang}: {pct:.1f}%</title></rect>'
        )
        x += w

    # Legend
    legend_parts = []
    for i, (lang, bytes_, pct) in enumerate(items):
        col = i % cols
        row = i // cols
        lx = pad + col * col_w
        ly = legend_y + row * row_h

        legend_parts.append(
            f'<circle cx="{lx + 6}" cy="{ly + 8}" r="5" fill="{_lang_color(lang)}"/>'
            f'<text x="{lx + 16}" y="{ly + 12}" fill="{TEXT_BRIGHT}" font-size="12" '
            f'font-family="{FONT_SANS}" font-weight="600">{lang}</text>'
            f'<text x="{lx + 16 + len(lang) * 7.5 + 6}" y="{ly + 12}" fill="{TEXT_DIM}" '
            f'font-size="11" font-family="{FONT_SANS}">{pct:.1f}%</text>'
        )

    # Title
    title = (
        f'<text x="{pad}" y="24" fill="{TEXT}" font-size="14" '
        f'font-family="{FONT_SANS}" font-weight="700">Language Breakdown</text>'
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{svg_h}" viewBox="0 0 {SVG_WIDTH} {svg_h}">
  <rect width="{SVG_WIDTH}" height="{svg_h}" rx="12" fill="{BG_CARD}" stroke="{BORDER}" stroke-width="1"/>
  {clip_def}
  {title}
  <g clip-path="url(#barClip)">{"".join(bar_parts)}</g>
  {"".join(legend_parts)}
</svg>"""

    with open(output_path, "w") as f:
        f.write(svg)
    return output_path

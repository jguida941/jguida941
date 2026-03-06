"""Build the builder scorecard SVG."""

from scripts.config import BG_HIGHLIGHT, BLUE, CYAN, GREEN, ORANGE, TEXT, TEXT_BRIGHT, BORDER, SVG_WIDTH, FONT_SANS
from scripts.card_theme import card_bg, title_accent, title_left, title_right
from scripts.profile_contract import SCORECARD_METRICS, format_metric_value


def _tile(
    x: int,
    y: int,
    width: int,
    height: int,
    label: str,
    value: str,
    detail: str,
    accent: str,
) -> str:
    return f"""<g transform="translate({x}, {y})">
  <rect width="{width}" height="{height}" rx="12" fill="{BG_HIGHLIGHT}" stroke="{BORDER}" stroke-width="1"/>
  <rect x="0" y="0" width="{width}" height="4" rx="12" fill="{accent}"/>
  <text x="16" y="30" fill="{TEXT}" font-size="11" font-family="{FONT_SANS}" font-weight="600">{label}</text>
  <text x="16" y="62" fill="{TEXT_BRIGHT}" font-size="28" font-family="{FONT_SANS}" font-weight="700">{value}</text>
  <text x="16" y="86" fill="{TEXT}" font-size="11" font-family="{FONT_SANS}">{detail}</text>
</g>"""


def _default_tiles(scorecard: dict) -> list[dict]:
    accent_map = {
        "BLUE": BLUE,
        "CYAN": CYAN,
        "GREEN": GREEN,
        "ORANGE": ORANGE,
    }
    tiles = []
    for definition in SCORECARD_METRICS:
        key = definition["key"]
        tiles.append({
            "label": definition["label"],
            "value": format_metric_value(scorecard.get(key, 0), definition),
            "detail": definition["detail"],
            "accent": accent_map.get(definition.get("accent", "CYAN"), CYAN),
        })
    return tiles


def generate(scorecard: dict, output_path: str = "assets/builder_scorecard.svg", tiles: list | None = None) -> str:
    """
    scorecard fields:
      - releases_30d
      - active_repos_7d
      - avg_release_gap_days
      - stars_per_public_repo
      - ci_coverage_pct
      - last_year_contributions
    """
    rows = 2
    cols = 3
    gap = 16
    pad = 20
    tile_w = int((SVG_WIDTH - pad * 2 - gap * (cols - 1)) / cols)
    tile_h = 106
    title_h = 52
    svg_h = title_h + rows * tile_h + (rows - 1) * gap + pad

    card_tiles = tiles or _default_tiles(scorecard)

    parts = []
    definition_by_key = {definition["key"]: definition for definition in SCORECARD_METRICS}
    for i, tile in enumerate(card_tiles):
        row = i // cols
        col = i % cols
        x = pad + col * (tile_w + gap)
        y = title_h + row * (tile_h + gap)
        key = str(tile.get("key", ""))
        display_value = tile.get("display_value")
        if display_value is None and key in definition_by_key:
            display_value = format_metric_value(tile.get("value"), definition_by_key[key])
        if display_value is None:
            display_value = tile.get("value", "0")
        parts.append(
            _tile(
                x,
                y,
                tile_w,
                tile_h,
                str(tile.get("label", "")),
                str(display_value),
                str(tile.get("detail", "")),
                str(tile.get("accent", CYAN)),
            )
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{svg_h}" viewBox="0 0 {SVG_WIDTH} {svg_h}">
  {card_bg(SVG_WIDTH, svg_h)}
  {title_left("Builder Scorecard", x=pad, y=30)}
  {title_right("auto-generated from GitHub API", width=SVG_WIDTH, pad=pad, y=30)}
  {title_accent(width=SVG_WIDTH, pad=pad, y=35)}
  {"".join(parts)}
</svg>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    return output_path

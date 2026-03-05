"""Generate a compact builder scorecard SVG for profile credibility metrics."""

from scripts.config import (
    BG_CARD,
    BG_DARK,
    BG_HIGHLIGHT,
    BLUE,
    CYAN,
    GREEN,
    ORANGE,
    TEXT,
    TEXT_BRIGHT,
    TEXT_DIM,
    BORDER,
    SVG_WIDTH,
    FONT_SANS,
)


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
  <text x="16" y="30" fill="{TEXT_DIM}" font-size="11" font-family="{FONT_SANS}" font-weight="600">{label}</text>
  <text x="16" y="62" fill="{TEXT_BRIGHT}" font-size="28" font-family="{FONT_SANS}" font-weight="700">{value}</text>
  <text x="16" y="86" fill="{TEXT}" font-size="11" font-family="{FONT_SANS}">{detail}</text>
</g>"""


def generate(scorecard: dict, output_path: str = "assets/builder_scorecard.svg") -> str:
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
    title_h = 44
    svg_h = title_h + rows * tile_h + (rows - 1) * gap + pad

    tiles = [
        (
            "Release Velocity (30d)",
            str(scorecard.get("releases_30d", 0)),
            "public release events",
            ORANGE,
        ),
        (
            "Active Repos (7d)",
            str(scorecard.get("active_repos_7d", 0)),
            "pushed in last week",
            CYAN,
        ),
        (
            "Avg Release Gap",
            f"{scorecard.get('avg_release_gap_days', 0):.1f}d",
            "recent cadence",
            GREEN,
        ),
        (
            "Stars / Public Repo",
            f"{scorecard.get('stars_per_public_repo', 0):.2f}",
            "signal density",
            BLUE,
        ),
        (
            "CI Coverage",
            f"{scorecard.get('ci_coverage_pct', 0):.1f}%",
            "repos with workflows",
            ORANGE,
        ),
        (
            "12mo Contributions",
            f"{scorecard.get('last_year_contributions', 0):,}",
            "GitHub contribution calendar",
            CYAN,
        ),
    ]

    parts = []
    for i, (label, value, detail, accent) in enumerate(tiles):
        row = i // cols
        col = i % cols
        x = pad + col * (tile_w + gap)
        y = title_h + row * (tile_h + gap)
        parts.append(_tile(x, y, tile_w, tile_h, label, value, detail, accent))

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{svg_h}" viewBox="0 0 {SVG_WIDTH} {svg_h}">
  <rect width="{SVG_WIDTH}" height="{svg_h}" rx="14" fill="{BG_CARD}" stroke="{BORDER}" stroke-width="1"/>
  <rect x="0" y="0" width="{SVG_WIDTH}" height="{title_h}" rx="14" fill="{BG_DARK}"/>
  <text x="{pad}" y="29" fill="{TEXT_BRIGHT}" font-size="16" font-family="{FONT_SANS}" font-weight="700">Builder Scorecard</text>
  <text x="{SVG_WIDTH - pad}" y="29" fill="{TEXT_DIM}" font-size="11" font-family="{FONT_SANS}" text-anchor="end">auto-generated from GitHub API</text>
  {"".join(parts)}
</svg>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    return output_path

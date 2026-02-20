"""Generate a self-contained badge strip SVG (no shields.io dependency)."""

from scripts.config import (
    BG_DARK, BLUE, ORANGE, TEXT, YELLOW, TEXT_DIM, SVG_WIDTH, FONT_SANS,
)


def _badge(x: int, label: str, value: str, color: str) -> str:
    """Render a single rounded-rectangle badge."""
    label_w = max(len(label) * 7.5 + 16, 80)
    value_w = max(len(str(value)) * 8.5 + 16, 50)
    total_w = label_w + value_w
    r = 6

    return f"""<g transform="translate({x}, 0)">
  <rect width="{total_w}" height="32" rx="{r}" fill="{BG_DARK}" stroke="{color}" stroke-width="1"/>
  <rect width="{label_w}" height="32" rx="{r}" fill="{BG_DARK}"/>
  <rect x="{label_w}" width="{value_w}" height="32" rx="{r}" fill="{color}"/>
  <rect x="{label_w - r}" width="{r}" height="32" fill="{BG_DARK}"/>
  <rect x="{label_w}" width="{r}" height="32" fill="{color}"/>
  <text x="{label_w / 2}" y="21" fill="{TEXT}" font-size="11" font-family="{FONT_SANS}"
        font-weight="600" text-anchor="middle">{label}</text>
  <text x="{label_w + value_w / 2}" y="21" fill="{BG_DARK}" font-size="12" font-family="{FONT_SANS}"
        font-weight="700" text-anchor="middle">{value}</text>
</g>"""


def generate(
    total_repos: int,
    ci_count: int,
    lang_count: int,
    stars: int,
    total_commits: int,
    output_path: str = "assets/badges.svg",
):
    badges_data = [
        ("Original Repos", str(total_repos), BLUE),
        ("CI/CD Pipelines", str(ci_count), ORANGE),
        ("Languages", str(lang_count), TEXT),
        ("Stars Earned", str(stars), YELLOW),
        ("Total Commits", str(total_commits), TEXT_DIM),
    ]

    badge_svgs = []
    x = 0
    gap = 8
    for label, value, color in badges_data:
        badge_svgs.append(_badge(x, label, value, color))
        label_w = max(len(label) * 7.5 + 16, 80)
        value_w = max(len(str(value)) * 8.5 + 16, 50)
        x += label_w + value_w + gap

    total_w = x - gap
    offset_x = (SVG_WIDTH - total_w) / 2

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="60" viewBox="0 0 {SVG_WIDTH} 60">
  <g transform="translate({offset_x}, 14)">
    {"".join(badge_svgs)}
  </g>
</svg>"""

    with open(output_path, "w") as f:
        f.write(svg)
    return output_path

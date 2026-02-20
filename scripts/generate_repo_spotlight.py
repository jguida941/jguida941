"""Generate a 2x2 grid of featured project cards with sparklines."""

from scripts.config import (
    BG_CARD, BG_HIGHLIGHT, BLUE, CYAN, GREEN, ORANGE, TEXT, TEXT_DIM,
    TEXT_BRIGHT, BORDER, SVG_WIDTH, FONT_SANS, LANG_COLORS,
)


def _lang_color(lang: str | None) -> str:
    if not lang:
        return "#8b8b8b"
    return LANG_COLORS.get(lang, "#8b8b8b")


def _sparkline(data: list, x: float, y: float, w: float, h: float, color: str) -> str:
    """Generate an SVG sparkline polyline from weekly commit data."""
    if not data or max(data) == 0:
        return ""
    n = len(data)
    max_val = max(data)
    points = []
    for i, v in enumerate(data):
        px = x + (i / max(n - 1, 1)) * w
        py = y + h - (v / max(max_val, 1)) * h
        points.append(f"{px:.1f},{py:.1f}")
    return (
        f'<polyline points="{" ".join(points)}" fill="none" '
        f'stroke="{color}" stroke-width="1.5" stroke-linecap="round"/>'
    )


def _truncate(text: str, max_len: int) -> str:
    if not text:
        return "No description"
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    if len(text) > max_len:
        return text[:max_len - 3] + "..."
    return text


def generate(
    repos_data: list,
    output_path: str = "assets/repo_spotlight.svg",
):
    """
    repos_data: list of dicts with keys:
        name, description, language, stars, forks, html_url,
        weekly_commits (list of 12 ints), has_ci (bool)
    """
    card_w = (SVG_WIDTH - 60) / 2  # 2 columns with gaps
    card_h = 160
    pad = 20
    gap = 20
    title_h = 40

    cols = 2
    rows_count = (len(repos_data) + cols - 1) // cols
    svg_h = title_h + rows_count * (card_h + gap) + pad

    parts = []

    # Section title
    parts.append(
        f'<text x="{pad + 10}" y="28" fill="{TEXT}" font-size="14" '
        f'font-family="{FONT_SANS}" font-weight="700">Featured Projects</text>'
    )

    for i, repo in enumerate(repos_data):
        col = i % cols
        row = i // cols
        cx = pad + col * (card_w + gap)
        cy = title_h + row * (card_h + gap)

        name = repo.get("name", "unknown")
        desc = _truncate(repo.get("description", ""), 70)
        lang = repo.get("language")
        stars = repo.get("stars", 0)
        forks = repo.get("forks", 0)
        has_ci = repo.get("has_ci", False)
        weekly = repo.get("weekly_commits", [])

        name_esc = name.replace("&", "&amp;").replace("<", "&lt;")

        # Card background
        parts.append(
            f'<rect x="{cx}" y="{cy}" width="{card_w}" height="{card_h}" '
            f'rx="10" fill="{BG_HIGHLIGHT}" stroke="{BORDER}" stroke-width="1"/>'
        )

        # Repo name
        parts.append(
            f'<text x="{cx + 16}" y="{cy + 28}" fill="{BLUE}" font-size="14" '
            f'font-family="{FONT_SANS}" font-weight="700">{name_esc}</text>'
        )

        # CI badge
        if has_ci:
            badge_x = cx + card_w - 60
            parts.append(
                f'<rect x="{badge_x}" y="{cy + 14}" width="44" height="18" rx="9" fill="{GREEN}" opacity="0.2"/>'
                f'<text x="{badge_x + 22}" y="{cy + 27}" fill="{GREEN}" font-size="9" '
                f'font-family="{FONT_SANS}" font-weight="600" text-anchor="middle">CI/CD</text>'
            )

        # Description
        parts.append(
            f'<text x="{cx + 16}" y="{cy + 48}" fill="{TEXT_DIM}" font-size="11" '
            f'font-family="{FONT_SANS}">{desc}</text>'
        )

        # Language dot + label
        parts.append(
            f'<circle cx="{cx + 22}" cy="{cy + 70}" r="4" fill="{_lang_color(lang)}"/>'
            f'<text x="{cx + 32}" y="{cy + 74}" fill="{TEXT}" font-size="11" '
            f'font-family="{FONT_SANS}">{lang or "n/a"}</text>'
        )

        # Stars + Forks
        star_x = cx + 120
        parts.append(
            f'<text x="{star_x}" y="{cy + 74}" fill="{TEXT_DIM}" font-size="11" '
            f'font-family="{FONT_SANS}">\u2605 {stars}  Forks: {forks}</text>'
        )

        # Sparkline
        spark_x = cx + 16
        spark_y = cy + 90
        spark_w = card_w - 32
        spark_h = 50
        # Sparkline background
        parts.append(
            f'<rect x="{spark_x}" y="{spark_y}" width="{spark_w}" height="{spark_h}" '
            f'rx="4" fill="{BG_CARD}" opacity="0.5"/>'
        )
        parts.append(_sparkline(weekly, spark_x + 4, spark_y + 4, spark_w - 8, spark_h - 8, CYAN))

        # "12 weeks" label
        parts.append(
            f'<text x="{spark_x + spark_w - 4}" y="{spark_y + spark_h + 12}" fill="{TEXT_DIM}" '
            f'font-size="9" font-family="{FONT_SANS}" text-anchor="end">12 weeks</text>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{int(svg_h)}" viewBox="0 0 {SVG_WIDTH} {int(svg_h)}">
  <rect width="{SVG_WIDTH}" height="{int(svg_h)}" rx="12" fill="{BG_CARD}" stroke="{BORDER}" stroke-width="1"/>
  {"".join(parts)}
</svg>"""

    with open(output_path, "w") as f:
        f.write(svg)
    return output_path

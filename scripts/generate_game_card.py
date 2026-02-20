"""Generate an RPG 'Developer Quest' character sheet SVG with real GitHub stats."""

import math

from scripts.config import (
    BG_DARK, BG_CARD, BG_HIGHLIGHT, BLUE, CYAN, GREEN, ORANGE, PURPLE,
    RED, YELLOW, TEXT, TEXT_DIM, TEXT_BRIGHT, BORDER,
    FONT_MONO, FONT_SANS, LANG_COLORS, USERNAME,
    LEVEL_XP_BASE, LEVEL_XP_SCALE,
)

W = 840
H = 520


def _calc_level(total_xp: int) -> tuple:
    """Return (level, xp_into_level, xp_needed_for_next)."""
    level = 1
    xp_remaining = total_xp
    while True:
        needed = int(LEVEL_XP_BASE * (LEVEL_XP_SCALE ** (level - 1)))
        if xp_remaining < needed:
            return level, xp_remaining, needed
        xp_remaining -= needed
        level += 1


def _class_name(lang_count: int, top_lang: str) -> str:
    if lang_count >= 8:
        return "Polyglot Architect"
    if lang_count >= 5:
        return "Full-Stack Mage"
    if top_lang == "Python":
        return "Python Sorcerer"
    if top_lang == "Java":
        return "Java Knight"
    if top_lang in ("C++", "C", "Rust"):
        return "Systems Warlock"
    return "Code Wanderer"


def _title(stars: int) -> str:
    if stars >= 100:
        return "Legendary Developer"
    if stars >= 50:
        return "Master Craftsman"
    if stars >= 20:
        return "Senior Artisan"
    if stars >= 5:
        return "Apprentice Builder"
    return "Novice Coder"


def _stat_bar(x: int, y: int, label: str, value: int, max_val: int, color: str) -> str:
    """Render a single RPG stat bar."""
    bar_w = 140
    fill_w = min(value / max(max_val, 1), 1.0) * bar_w
    return f"""<g transform="translate({x}, {y})">
  <text x="0" y="12" fill="{YELLOW}" font-size="10" font-family="{FONT_MONO}" font-weight="700">{label}</text>
  <rect x="42" y="2" width="{bar_w}" height="14" rx="3" fill="{BG_DARK}"/>
  <rect x="42" y="2" width="{fill_w:.1f}" height="14" rx="3" fill="{color}" opacity="0.85"/>
  <text x="{42 + bar_w + 6}" y="13" fill="{TEXT_DIM}" font-size="10" font-family="{FONT_MONO}">{value}</text>
</g>"""


def _pixel_border(w: int, h: int) -> str:
    """Draw a pixel-art double border."""
    parts = []
    # Outer border
    parts.append(f'<rect x="4" y="4" width="{w-8}" height="{h-8}" rx="2" fill="none" stroke="{BORDER}" stroke-width="2"/>')
    # Inner border
    parts.append(f'<rect x="10" y="10" width="{w-20}" height="{h-20}" rx="2" fill="none" stroke="{TEXT_DIM}" stroke-width="1" stroke-dasharray="4 2"/>')
    return "".join(parts)


def _scanlines(w: int, h: int) -> str:
    """Subtle CRT scanline effect."""
    lines = []
    for y in range(0, h, 4):
        lines.append(f'<line x1="0" y1="{y}" x2="{w}" y2="{y}" stroke="{BG_DARK}" stroke-width="1" opacity="0.1"/>')
    return "".join(lines)


def generate(
    total_commits: int,
    total_repos: int,
    total_stars: int,
    language_data: dict,  # {lang: byte_count}
    prs_merged: int,
    releases: int,
    ci_pipelines: int,
    streak_days: int,
    output_path: str = "assets/game_card.svg",
):
    # XP = commits + repos * 5 + stars * 10 + PRs * 3
    total_xp = total_commits + total_repos * 5 + total_stars * 10 + prs_merged * 3
    level, xp_current, xp_next = _calc_level(total_xp)

    # Determine class and title
    sorted_langs = sorted(language_data.items(), key=lambda x: x[1], reverse=True)
    top_lang = sorted_langs[0][0] if sorted_langs else "Unknown"
    lang_count = len(sorted_langs)
    char_class = _class_name(lang_count, top_lang)
    char_title = _title(total_stars)

    # Map stats to RPG attributes (0-99 scale)
    def scale(val, low, high):
        return max(1, min(99, int((val - low) / max(high - low, 1) * 99)))

    stats = {
        "STR": scale(total_commits, 0, 5000),       # Raw output
        "DEX": scale(lang_count, 0, 15),             # Language diversity
        "INT": scale(sum(language_data.values()), 0, 50_000_000),  # Code volume
        "WIS": scale(total_repos, 0, 200),           # Breadth
        "CHA": scale(total_stars, 0, 100),           # Community impact
        "CON": scale(streak_days, 0, 365),           # Consistency
    }
    stat_colors = {
        "STR": RED,
        "DEX": GREEN,
        "INT": BLUE,
        "WIS": PURPLE,
        "CHA": YELLOW,
        "CON": CYAN,
    }

    parts = []

    # Background
    parts.append(f'<rect width="{W}" height="{H}" rx="12" fill="{BG_CARD}"/>')

    # Pixel border + scanlines
    parts.append(_pixel_border(W, H))
    parts.append(_scanlines(W, H))

    # Title banner
    parts.append(
        f'<rect x="20" y="20" width="{W-40}" height="40" rx="4" fill="{BG_DARK}" opacity="0.7"/>'
        f'<text x="{W/2}" y="46" fill="{YELLOW}" font-size="18" font-family="{FONT_MONO}" '
        f'font-weight="700" text-anchor="middle" letter-spacing="4">'
        f'DEVELOPER QUEST</text>'
    )

    # Character info section (left)
    info_x = 30
    info_y = 80
    parts.append(
        f'<text x="{info_x}" y="{info_y}" fill="{TEXT_BRIGHT}" font-size="16" '
        f'font-family="{FONT_MONO}" font-weight="700">{USERNAME}</text>'
    )
    parts.append(
        f'<text x="{info_x}" y="{info_y + 20}" fill="{CYAN}" font-size="12" '
        f'font-family="{FONT_MONO}">Lv.{level} {char_class}</text>'
    )
    parts.append(
        f'<text x="{info_x}" y="{info_y + 38}" fill="{YELLOW}" font-size="11" '
        f'font-family="{FONT_MONO}" opacity="0.8">&lt; {char_title} &gt;</text>'
    )

    # XP Bar
    xp_y = info_y + 52
    xp_bar_w = 250
    xp_fill = (xp_current / max(xp_next, 1)) * xp_bar_w
    parts.append(
        f'<text x="{info_x}" y="{xp_y}" fill="{TEXT_DIM}" font-size="10" font-family="{FONT_MONO}">EXP</text>'
        f'<rect x="{info_x + 30}" y="{xp_y - 10}" width="{xp_bar_w}" height="12" rx="3" fill="{BG_DARK}"/>'
        f'<rect x="{info_x + 30}" y="{xp_y - 10}" width="{xp_fill:.1f}" height="12" rx="3" fill="{ORANGE}"/>'
        f'<text x="{info_x + 30 + xp_bar_w + 8}" y="{xp_y}" fill="{TEXT_DIM}" font-size="9" '
        f'font-family="{FONT_MONO}">{xp_current}/{xp_next}</text>'
    )

    # Stat bars (left column)
    stat_x = 30
    stat_y = 170
    stat_labels = ["STR", "DEX", "INT", "WIS", "CHA", "CON"]
    for i, label in enumerate(stat_labels):
        parts.append(
            _stat_bar(stat_x, stat_y + i * 26, label, stats[label], 99, stat_colors[label])
        )

    # Inventory section (right side)
    inv_x = 440
    inv_y = 80
    parts.append(
        f'<text x="{inv_x}" y="{inv_y}" fill="{YELLOW}" font-size="13" '
        f'font-family="{FONT_MONO}" font-weight="700" letter-spacing="2">INVENTORY</text>'
    )
    # Top 5 languages
    for i, (lang, bytes_) in enumerate(sorted_langs[:5]):
        ly = inv_y + 22 + i * 22
        lang_esc = lang.replace("&", "&amp;").replace("<", "&lt;")
        color = LANG_COLORS.get(lang, "#8b8b8b")
        repo_count = ""  # Will be passed in if available
        parts.append(
            f'<rect x="{inv_x}" y="{ly - 12}" width="8" height="8" rx="2" fill="{color}"/>'
            f'<text x="{inv_x + 14}" y="{ly - 3}" fill="{TEXT}" font-size="11" '
            f'font-family="{FONT_MONO}">{lang_esc}</text>'
        )

    # Quests section (right, below inventory)
    quest_x = inv_x
    quest_y = inv_y + 145
    parts.append(
        f'<text x="{quest_x}" y="{quest_y}" fill="{YELLOW}" font-size="13" '
        f'font-family="{FONT_MONO}" font-weight="700" letter-spacing="2">QUESTS COMPLETED</text>'
    )

    quests = [
        ("Repos Created", total_repos, GREEN),
        ("PRs Merged", prs_merged, BLUE),
        ("Releases Shipped", releases, PURPLE),
        ("CI Pipelines", ci_pipelines, ORANGE),
    ]
    for i, (quest_name, count, color) in enumerate(quests):
        qy = quest_y + 22 + i * 24
        parts.append(
            f'<text x="{quest_x}" y="{qy}" fill="{color}" font-size="11" font-family="{FONT_MONO}">'
            f'[{"x" if count > 0 else " "}]</text>'
            f'<text x="{quest_x + 28}" y="{qy}" fill="{TEXT}" font-size="11" '
            f'font-family="{FONT_MONO}">{quest_name}</text>'
            f'<text x="{quest_x + 200}" y="{qy}" fill="{TEXT_DIM}" font-size="11" '
            f'font-family="{FONT_MONO}" text-anchor="end">{count}</text>'
        )

    # Total XP at bottom
    parts.append(
        f'<rect x="20" y="{H - 50}" width="{W - 40}" height="30" rx="4" fill="{BG_DARK}" opacity="0.5"/>'
        f'<text x="{W / 2}" y="{H - 30}" fill="{TEXT_DIM}" font-size="11" '
        f'font-family="{FONT_MONO}" text-anchor="middle" letter-spacing="1">'
        f'TOTAL XP: {total_xp:,}  |  COMMITS: {total_commits:,}  |  '
        f'REPOS: {total_repos}  |  STARS: {total_stars}</text>'
    )

    # Decorative corner pixels
    for cx, cy in [(16, 16), (W - 20, 16), (16, H - 20), (W - 20, H - 20)]:
        parts.append(f'<rect x="{cx}" y="{cy}" width="4" height="4" fill="{YELLOW}" opacity="0.5"/>')

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  {"".join(parts)}
</svg>"""

    with open(output_path, "w") as f:
        f.write(svg)
    return output_path

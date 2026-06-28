"""Flagship Projects card — Apple/glassmorphism re-skin.

Renders a 2-column grid of frosted ``glass_tile`` project cards. Each card shows a
linked repo name, a status chip ("last active <ago>") so a stale flagship never
implies current work, an optional CI/CD chip, a wrapped description, a
language/star/fork footer with line icons, and a glowing weekly-commit sparkline.
Height is data-driven; an inset margin keeps the glass drop-shadow from clipping.
"""

from __future__ import annotations

from scripts.core.config import (
    BLUE,
    FONT_SANS,
    GLASS_HAIRLINE_HEX,
    GREEN,
    SVG_WIDTH,
    TEXT,
    TEXT_BRIGHT,
    TEXT_DIM,
)
from scripts.rendering.card_theme import title_left, title_right
from scripts.rendering.glass_kit import (
    accent_ribbon,
    eyebrow_text,
    glass_panel,
    glass_tile,
    icon,
    metadata,
    sparkline,
)
from scripts.rendering.svg_utils import fmt_int, lang_color, truncate, xml_escape

# --- layout constants ---------------------------------------------------------
PAD_X = 28          # interior left/right margin (>= GLASS_INSET so nothing clips)
HEADER_H = 88       # title block height; grid starts here
BOTTOM_PAD = 28     # below the grid: GLASS_INSET (12) + breathing room
COLS = 2
CARD_H = 190
CARD_GAP = 18
IP = 16             # inner padding inside each project tile

# active = green, maintained = calm gray-blue (so "maintained" never reads as live work)
STATUS_COLOR = {"active": GREEN, "maintained": BLUE}


def _n(value: float) -> str:
    """Compact coordinate formatting."""
    return f"{round(float(value), 2):g}"


def _tw(text: str, size: float) -> float:
    """Rough proportional text width estimate for layout."""
    return len(text) * size * 0.6


def _text(
    s: str,
    x: float,
    y: float,
    *,
    size: float,
    fill: str,
    weight: int | None = None,
    anchor: str | None = None,
) -> str:
    w = f' font-weight="{weight}"' if weight else ""
    a = f' text-anchor="{anchor}"' if anchor else ""
    return (
        f'<text x="{_n(x)}" y="{_n(y)}" fill="{fill}" font-size="{_n(size)}" '
        f'font-family="{FONT_SANS}"{w}{a}>{s}</text>'
    )


def _wrap2(text: str, max_chars: int) -> list[str]:
    """Word-wrap into at most two lines; ellipsize overflow on the second line."""
    text = (text or "").strip()
    if not text:
        return ["No description provided."]
    words = text.split()
    lines: list[str] = []
    cur = ""
    for word in words:
        cand = f"{cur} {word}".strip()
        if len(cand) <= max_chars:
            cur = cand
            continue
        if cur:
            lines.append(cur)
            cur = word
        else:  # single very long word
            cur = word
        if len(lines) == 2:
            break
    if cur and len(lines) < 2:
        lines.append(cur)
    lines = lines[:2]
    if len(" ".join(lines)) < len(text):  # something was dropped -> mark truncated
        last = lines[-1].rstrip()
        if len(last) > max_chars - 1:
            last = last[: max_chars - 1].rstrip()
        lines[-1] = last + "…"
    return lines


def _project_card(repo: dict, cx: float, cy: float, card_w: float, idx: int) -> str:
    inner_w = card_w - IP * 2
    status = str(repo.get("status") or "maintained").lower()
    accent = STATUS_COLOR.get(status, BLUE)

    parts: list[str] = [glass_tile(cx, cy, card_w, CARD_H, accent=accent)]

    # --- repo name (linked) ---
    name = str(repo.get("name") or "unknown")
    name = truncate(name, 36)
    name_esc = xml_escape(name, quote=False)
    url = str(repo.get("html_url") or "")
    name_node = _text(
        name_esc, cx + IP, cy + 32, size=15, fill=TEXT_BRIGHT, weight=700
    )
    if url:
        parts.append(f'<a href="{xml_escape(url)}">{name_node}</a>')
    else:
        parts.append(name_node)

    # --- recency + CI as inline metadata (Apple: recency is text, not a pill;
    #     status color lives only on the CI checkmark) ---
    meta_y = cy + 54
    ago = str(repo.get("pushed_ago") or "").strip()
    ago = truncate(ago, 22) if ago else "date unknown"
    parts.append(
        metadata(cx + IP, meta_y, f"Updated {ago}", icon_name="clock", color=TEXT_DIM, size=12)
    )
    if repo.get("has_ci"):
        ci_label = "CI/CD"
        ci_w = 13 + 5 + _tw(ci_label, 12)
        parts.append(
            metadata(
                cx + card_w - IP - ci_w,
                meta_y,
                ci_label,
                icon_name="ci_check",
                color=TEXT_DIM,
                icon_color=GREEN,
                size=12,
            )
        )

    # --- description (up to 2 wrapped lines) ---
    desc_lines = _wrap2(str(repo.get("description") or ""), 56)
    desc_y = cy + 90
    for line in desc_lines:
        parts.append(
            _text(xml_escape(line, quote=False), cx + IP, desc_y, size=11, fill=TEXT)
        )
        desc_y += 18

    # --- footer: language . stars . forks (line icons) ---
    fy = cy + 138
    fs = 11.5
    lang = repo.get("language")
    lang_label = str(lang) if lang else "n/a"
    fx = cx + IP
    # language dot
    dot_y = fy - fs * 0.35 - 4.5
    parts.append(icon("lang_dot", fx, dot_y, size=9, color=lang_color(lang)))
    parts.append(_text(xml_escape(lang_label, quote=False), fx + 15, fy, size=fs, fill=TEXT))
    fx += 15 + _tw(lang_label, fs) + 22
    # stars
    icon_y = fy - fs * 0.35 - 6.5
    stars = fmt_int(repo.get("stars", 0))
    parts.append(icon("star", fx, icon_y, size=13, color=TEXT_DIM))
    parts.append(_text(stars, fx + 17, fy, size=fs, fill=TEXT_BRIGHT, weight=600))
    fx += 17 + _tw(stars, fs) + 22
    # forks
    forks = fmt_int(repo.get("forks", 0))
    parts.append(icon("fork", fx, icon_y, size=13, color=TEXT_DIM))
    parts.append(_text(forks, fx + 17, fy, size=fs, fill=TEXT_BRIGHT, weight=600))

    # --- weekly-commit sparkline band (only when there is REAL activity) ---
    # The participation API often returns zeros (still computing / no data); never
    # claim "0 commits" or draw a fake-flat line — just omit the band honestly.
    weekly = [int(v) for v in (repo.get("weekly_commits") or []) if v is not None]
    total = sum(weekly)
    if total > 0:
        band_y = cy + 150
        parts.append(
            f'<rect x="{_n(cx + IP)}" y="{_n(band_y)}" width="{_n(inner_w)}" height="1" '
            f'fill="{GLASS_HAIRLINE_HEX}" fill-opacity="0.10"/>'
        )
        parts.append(
            eyebrow_text(f"{total} commits · 12 wk", x=cx + IP, y=band_y + 18, color=TEXT_DIM, size=9)
        )
        spark_x = cx + IP + 110
        spark_w = inner_w - 110
        spark_y = band_y + 8
        spark_h = 22
        parts.append(
            f'<rect x="{_n(spark_x)}" y="{_n(spark_y + spark_h)}" width="{_n(spark_w)}" '
            f'height="1" fill="{GLASS_HAIRLINE_HEX}" fill-opacity="0.10"/>'
        )
        parts.append(
            sparkline(weekly, spark_x, spark_y, spark_w, spark_h, color=accent, uid=f"spk{idx}")
        )
    return "".join(parts)


def generate(
    repos_data: list,
    output_path: str = "assets/repo_spotlight.svg",
):
    """Render the Flagship Projects spotlight card.

    repos_data: list of dicts with keys:
        name, description, language, stars, forks, html_url, pushed_at,
        pushed_ago, status ("active"|"maintained"), weekly_commits (list[int]),
        has_ci (bool)
    """
    repos = list(repos_data or [])
    n = len(repos)
    rows = max((n + COLS - 1) // COLS, 1)

    grid_w = SVG_WIDTH - PAD_X * 2
    card_w = (grid_w - CARD_GAP * (COLS - 1)) / COLS
    gaps = max(rows - 1, 0)
    svg_h = int(HEADER_H + rows * CARD_H + gaps * CARD_GAP + BOTTOM_PAD)

    parts: list[str] = [glass_panel(SVG_WIDTH, svg_h)]

    # header
    parts.append(eyebrow_text("SHOWCASE · BEST WORK", x=PAD_X, y=34))
    parts.append(title_left("Flagship Projects", x=PAD_X, y=58, size=18))
    parts.append(
        title_right(f"{n} repositories", width=SVG_WIDTH, pad=PAD_X, y=58, size=11)
    )
    parts.append(accent_ribbon(SVG_WIDTH, pad=PAD_X, y=70))

    if not repos:
        parts.append(glass_tile(PAD_X, HEADER_H, grid_w, CARD_H))
        parts.append(
            _text(
                "No flagship repositories to show yet.",
                SVG_WIDTH / 2,
                HEADER_H + CARD_H / 2,
                size=13,
                fill=TEXT_DIM,
                anchor="middle",
            )
        )
    else:
        for i, repo in enumerate(repos):
            col = i % COLS
            row = i // COLS
            cx = PAD_X + col * (card_w + CARD_GAP)
            cy = HEADER_H + row * (CARD_H + CARD_GAP)
            parts.append(_project_card(repo, cx, cy, card_w, i))

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" '
        f'height="{svg_h}" viewBox="0 0 {SVG_WIDTH} {svg_h}">'
        f'{"".join(parts)}'
        f"</svg>"
    )

    with open(output_path, "w") as f:
        f.write(svg)
    return output_path

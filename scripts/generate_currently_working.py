"""Generate an SVG card showing repos with commits in the last 7 days."""

from datetime import datetime, timezone

from scripts.config import (
    BLUE, TEXT, TEXT_DIM,
    SVG_WIDTH, FONT_SANS, LANG_COLORS,
)
from scripts.card_theme import card_bg, title_left, title_right


def _time_ago(iso_str: str) -> str:
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    delta = datetime.now(timezone.utc) - dt
    hours = delta.total_seconds() / 3600
    if hours < 1:
        return "just now"
    if hours < 24:
        return f"{int(hours)}h ago"
    days = int(hours / 24)
    if days == 1:
        return "1 day ago"
    return f"{days} days ago"


def _lang_color(lang: str | None) -> str:
    if lang is None:
        return "#8b8b8b"
    return LANG_COLORS.get(lang, "#8b8b8b")


def _esc_attr(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def generate(
    repos: list,
    output_path: str = "assets/currently_working.svg",
):
    """repos: list of dicts with keys: name, html_url, language, pushed_at, last_commit_msg"""
    if not repos:
        # Empty state
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="108" viewBox="0 0 {SVG_WIDTH} 108">
  {card_bg(SVG_WIDTH, 108)}
  {title_left("Currently Working On", x=24, y=29)}
  {title_right("pushed in the last 7 days", width=SVG_WIDTH, pad=24, y=29)}
  <text x="420" y="72" fill="{TEXT}" font-size="13" font-family="{FONT_SANS}" text-anchor="middle">No recent activity in the last 7 days</text>
</svg>"""
        with open(output_path, "w") as f:
            f.write(svg)
        return output_path

    pad = 24
    row_h = 36
    header_h = 52
    svg_h = header_h + len(repos) * row_h + 16

    rows = []
    for i, repo in enumerate(repos):
        y = header_h + i * row_h
        name = repo["name"]
        lang = repo.get("language")
        pushed = _time_ago(repo["pushed_at"])
        msg = repo.get("last_commit_msg", "")
        if len(msg) > 60:
            msg = msg[:57] + "..."
        # Escape XML
        msg = msg.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        name_esc = name.replace("&", "&amp;").replace("<", "&lt;")
        repo_url = _esc_attr(repo.get("html_url", ""))
        name_svg = (
            f'<a href="{repo_url}"><text x="{pad + 16}" y="14" fill="{BLUE}" font-size="13" font-family="{FONT_SANS}" font-weight="600">{name_esc}</text></a>'
            if repo_url
            else f'<text x="{pad + 16}" y="14" fill="{BLUE}" font-size="13" font-family="{FONT_SANS}" font-weight="600">{name_esc}</text>'
        )

        rows.append(f"""<g transform="translate(0, {y})">
  <circle cx="{pad + 5}" cy="18" r="4" fill="{_lang_color(lang)}"/>
  {name_svg}
  <text x="{pad + 16}" y="30" fill="{TEXT}" font-size="11" font-family="{FONT_SANS}">{msg}</text>
  <text x="{SVG_WIDTH - pad}" y="14" fill="{TEXT}" font-size="11" font-family="{FONT_SANS}" text-anchor="end">{pushed}</text>
  <text x="{SVG_WIDTH - pad}" y="30" fill="{TEXT_DIM}" font-size="10" font-family="{FONT_SANS}" text-anchor="end">{lang or "n/a"}</text>
</g>""")

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{svg_h}" viewBox="0 0 {SVG_WIDTH} {svg_h}">
  {card_bg(SVG_WIDTH, svg_h)}
  {title_left("Currently Working On", x=pad, y=29)}
  {title_right("pushed in the last 7 days", width=SVG_WIDTH, pad=pad, y=29)}
  {"".join(rows)}
</svg>"""

    with open(output_path, "w") as f:
        f.write(svg)
    return output_path

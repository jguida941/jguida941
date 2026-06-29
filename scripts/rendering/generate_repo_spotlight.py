"""Flagship Projects card — aligned repository rows (DESIGN_SPEC 3.12).

A curated list of flagship repos as uniform rows: linked name + status chip on top,
a one-line description, then a footer of language (dot AND label) + stars + forks
with neutral Lucide icons. On the locked type ladder; status by chip (icon + label),
never by row tint. Glass kept.
"""

from __future__ import annotations

from scripts.core.config import SPACE, SVG_WIDTH, TEXT, TEXT_BRIGHT, TEXT_DIM
from scripts.rendering.components import empty_state, section_header, status_chip, text
from scripts.rendering.glass_kit import chip_width, glass_panel, glass_tile, icon
from scripts.rendering.svg_utils import fmt_compact, lang_color, truncate, xml_escape

PAD = 28
ROW_H = 86
ROW_GAP = 12
MAX_REPOS = 4

# active -> a positive status; maintained -> calm neutral (never reads as "live work").
_STATUS = {"active": ("success", "Active"), "maintained": ("neutral", "Maintained")}


def _footer_metric(parts: list, x: float, y: float, icon_name: str, value: str) -> float:
    parts.append(icon(icon_name, x, y - 12, size=15, color=TEXT_DIM))
    parts.append(text(value, x + 20, y, token="caption", color=TEXT))
    return x + 20 + len(value) * 7 + 22


def _row(repo: dict, x: float, y: float, w: float) -> str:
    parts = [glass_tile(x, y, w, ROW_H)]
    pad = SPACE["lg"]
    name = truncate(str(repo.get("name") or "unknown"), 40)
    url = str(repo.get("html_url") or "").strip()
    name_node = text(xml_escape(name), x + pad, y + 26, token="body", color=TEXT_BRIGHT)
    parts.append(f'<a href="{xml_escape(url)}">{name_node}</a>' if url else name_node)

    # status chip, right-aligned on the name row
    status, slabel = _STATUS.get(str(repo.get("status") or "maintained").lower(), ("neutral", "Maintained"))
    cw = chip_width(slabel, icon=True)
    parts.append(status_chip(x + w - pad - cw, y + 12, label=slabel, status=status))

    # one-line description
    desc = truncate(str(repo.get("description") or "").strip(), 72)
    if desc:
        parts.append(text(xml_escape(desc), x + pad, y + 48, token="caption", color=TEXT_DIM))

    # footer: language dot + label, stars, forks
    fy = y + 72
    lang = repo.get("language")
    parts.append(
        f'<circle cx="{x + pad + 4:g}" cy="{fy - 4:g}" r="4.5" fill="{lang_color(lang)}"/>'
    )
    parts.append(text(xml_escape(str(lang) if lang else "n/a"), x + pad + 15, fy, token="caption", color=TEXT))
    fx = x + pad + 15 + (len(str(lang) if lang else "n/a")) * 7 + 22
    fx = _footer_metric(parts, fx, fy, "star", fmt_compact(repo.get("stars", 0)))
    _footer_metric(parts, fx, fy, "fork", fmt_compact(repo.get("forks", 0)))
    return "".join(parts)


def generate(repos_data: list, output_path: str = "assets/repo_spotlight.svg"):
    width = SVG_WIDTH
    repos = [r for r in (repos_data or []) if isinstance(r, dict)][:MAX_REPOS]

    header_svg, content_top = section_header(
        PAD, 46, "Flagship Projects", width=width,
        eyebrow="Showcase · Best Work", right_text=f"{len(repos)} repositories", pad=PAD,
    )

    if not repos:
        empty_header, _ = section_header(PAD, 46, "Flagship Projects", width=width,
                                         eyebrow="Showcase · Best Work", pad=PAD)
        height = int(content_top + 92)
        body = "".join([glass_panel(width, height), empty_header,
                        empty_state(width / 2, content_top + 48, "No flagship repositories yet", icon_name="star")])
        with open(output_path, "w") as f:
            f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
                    f'viewBox="0 0 {width} {height}">{body}</svg>')
        return output_path

    rows_top = content_top + 6
    height = int(rows_top + len(repos) * ROW_H + (len(repos) - 1) * ROW_GAP + 22)
    parts = [glass_panel(width, height), header_svg]
    for i, repo in enumerate(repos):
        parts.append(_row(repo, PAD, rows_top + i * (ROW_H + ROW_GAP), width - PAD * 2))

    with open(output_path, "w") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
                f'viewBox="0 0 {width} {height}">{"".join(parts)}</svg>')
    return output_path

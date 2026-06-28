"""Build the "By The Numbers" stat row as a frosted-glass SVG card."""

from __future__ import annotations

from scripts.config import (
    BLUE,
    CYAN,
    FONT_SANS,
    GRAD_BLUE_CYAN,
    PURPLE,
    SVG_WIDTH,
    TEXT_BRIGHT,
)
from scripts.card_theme import title_left
from scripts.glass_kit import eyebrow_text, glass_panel, glass_tile, icon
from scripts.svg_utils import fmt_int

# Card geometry (one row of stat tiles + a margin for the glass drop shadow).
_W = SVG_WIDTH
_H = 132
_PAD = 28          # content inset inside the 12px glass band
_TILE_Y = 58
_TILE_H = 58
_GAP = 14
_N = 5


def _stat_tile(x: float, y: float, w: float, h: float, name: str, value: str, label: str, accent: str) -> str:
    """One frosted stat cell: accent icon + bold value on top, tiny label beneath."""
    return "".join(
        (
            glass_tile(x, y, w, h),
            icon(name, x + 16, y + 14, size=16, color=accent),
            f'<text x="{x + 41:g}" y="{y + 33:g}" fill="{TEXT_BRIGHT}" '
            f'font-size="22" font-family="{FONT_SANS}" font-weight="700">{value}</text>',
            eyebrow_text(label, x=x + 16, y=y + 50, size=9),
        )
    )


def generate(
    public_nonfork_repos: int,
    public_forks: int,
    private_owned_repos: int | None,
    ci_count: int | None,
    last_year_contributions: int | None,
    output_path: str = "assets/badges.svg",
):
    # value, label, icon, accent — contributions leads as the hero metric.
    stats = [
        (fmt_int(last_year_contributions), "CONTRIBUTIONS", "commit", CYAN),
        (fmt_int(public_nonfork_repos), "PUBLIC REPOS", "code", BLUE),
        (fmt_int(public_forks), "FORKS", "fork", BLUE),
        (fmt_int(private_owned_repos), "PRIVATE", "lock", PURPLE),
        (fmt_int(ci_count), "CI PIPELINES", "workflow", CYAN),
    ]

    avail = _W - _PAD * 2
    tile_w = (avail - _GAP * (_N - 1)) / _N

    tiles = []
    for i, (value, label, name, accent) in enumerate(stats):
        tx = _PAD + i * (tile_w + _GAP)
        tiles.append(_stat_tile(tx, _TILE_Y, tile_w, _TILE_H, name, value, label, accent))

    # One calm accent: a short blue->cyan underline beneath the title.
    g0, g1 = GRAD_BLUE_CYAN
    accent = (
        '<linearGradient id="bn-accent" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{g0}" stop-opacity="0.95"/>'
        f'<stop offset="1" stop-color="{g1}" stop-opacity="0.85"/>'
        "</linearGradient>"
        f'<rect x="{_PAD}" y="45" width="46" height="3" rx="1.5" fill="url(#bn-accent)"/>'
    )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_W}" height="{_H}" '
        f'viewBox="0 0 {_W} {_H}">'
        f"{glass_panel(_W, _H)}"
        f"{title_left('By The Numbers', x=_PAD, y=37)}"
        f"{accent}"
        f"{''.join(tiles)}"
        "</svg>"
    )

    with open(output_path, "w") as f:
        f.write(svg)
    return output_path

"""Red-first ICON SYSTEM contract (semantic-TDD) — governing authority: Apple HIG / Lucide.

Encodes the canonical icon-system target for the secondary metric tiles (rendered
via ``generate_metrics_general``):
  * ONE shared render size across every tile (size variance == 0).
  * Tile icons use the MUTED text token only (TEXT_DIM), never an accent hue.
  * Each icon sits INLINE-LEFT of its label, on the label's row — NOT a lone glyph
    stacked above the value.
  * Canonical Lucide LINE geometry with round caps/joins (no solid-fill glyphs).
  * Constant ~1.5px ON-SCREEN stroke (stroke-width = 36/renderPx), so the stroke
    matches the label weight and survives GitHub's column downscaling.

Driven GREEN by the Lucide icon-system refactor; RED on the current hand-drawn set.
"""
from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from scripts.core.config import BLUE, CYAN, GREEN, ORANGE, PURPLE, RED, TEXT_DIM

# Tile icons render as `<g transform="translate(X,Y) scale(S)" ...>BODY</g>` —
# scale*24 is the on-screen box size (glass_kit.icon).
_ICON_RE = re.compile(
    r'<g transform="translate\(([-0-9.]+),([-0-9.]+)\) scale\(([-0-9.]+)\)"([^>]*)>(.*?)</g>',
    re.S,
)
_TEXT_RE = re.compile(
    r'<text x="([-0-9.]+)" y="([-0-9.]+)" fill="([^"]+)" font-size="([0-9.]+)"[^>]*>(.*?)</text>',
    re.S,
)
_STROKE_W = re.compile(r'stroke-width="([0-9.]+)"')
# Decorative accent hues that tile icons must never use (color = status/data only).
_ACCENTS = (CYAN, BLUE, GREEN, ORANGE, PURPLE, RED)


def _icons(svg: str) -> list[dict]:
    out = []
    for m in _ICON_RE.finditer(svg):
        scale = float(m.group(3))
        out.append(
            {
                "x": float(m.group(1)),
                "y": float(m.group(2)),
                "scale": m.group(3),
                "size": scale * 24.0,
                "attrs": m.group(4),
                "body": m.group(5),
            }
        )
    return out


def _texts(svg: str) -> list[dict]:
    return [
        {"x": float(m.group(1)), "y": float(m.group(2)), "fill": m.group(3),
         "size": float(m.group(4)), "text": m.group(5)}
        for m in _TEXT_RE.finditer(svg)
    ]


def _render_hero(out: str) -> str:
    from scripts.rendering.generate_metrics_general import generate

    snapshot = {
        "last_year_contributions": 8104, "public_scope_commits": 4264, "total_repos": 67,
        "private_owned_repos": 146, "total_stars": 78, "languages_count": 24,
        "prs_merged": 35, "releases": 0, "ci_repos": 16, "streak_days": 2,
    }
    generate(username="jguida941", snapshot=snapshot, generated_at="2026-06-28T00:00:00Z", output_path=out)
    return Path(out).read_text(encoding="utf-8")


class IconSystemContract(unittest.TestCase):
    """The secondary-tile icon set must read as one Lucide-style system: one shared
    size, muted ink, inline-left of the label (never above the number), canonical
    round-cap line geometry, and a constant ~1.5px on-screen stroke."""

    def _hero(self) -> str:
        with tempfile.TemporaryDirectory() as d:
            return _render_hero(str(Path(d) / "hero.svg"))

    def _tile_icons(self, svg: str) -> list[dict]:
        icons = _icons(svg)
        self.assertGreaterEqual(len(icons), 6, "hero must render one tile icon per secondary metric")
        return icons

    def _tile_band(self, icons: list[dict]) -> float:
        xs = sorted({round(i["x"], 1) for i in icons})
        gaps = [b - a for a, b in zip(xs, xs[1:]) if b - a > 1.0]
        return (min(gaps) * 0.5) if gaps else 80.0

    def test_icons_share_one_render_size(self):
        icons = self._tile_icons(self._hero())
        scales = {i["scale"] for i in icons}
        self.assertEqual(1, len(scales), f"every tile icon must render at ONE shared size; got {sorted(scales)}")

    def test_icons_use_muted_token_only(self):
        icons = self._tile_icons(self._hero())
        offenders = []
        for i in icons:
            chunk = i["attrs"] + i["body"]
            if TEXT_DIM not in chunk:
                offenders.append(f"icon@({i['x']:g},{i['y']:g}) is not the muted token {TEXT_DIM}")
            for hue in _ACCENTS:
                if hue in chunk:
                    offenders.append(f"icon@({i['x']:g},{i['y']:g}) uses decorative accent {hue}")
        self.assertEqual([], offenders, "tile icons must use the muted token only:\n  " + "\n  ".join(offenders))

    def test_icon_inline_left_of_label_not_stacked_above_value(self):
        svg = self._hero()
        icons = self._tile_icons(svg)
        texts = _texts(svg)
        band = self._tile_band(icons)
        offenders = []
        for i in icons:
            ix, iy, size = i["x"], i["y"], i["size"]
            row_lo, row_hi = iy - 4.0, iy + size + 6.0
            inline_right = [t for t in texts if ix + 2.0 < t["x"] < ix + band and row_lo <= t["y"] <= row_hi]
            if not inline_right:
                below = sorted((t for t in texts if abs(t["x"] - ix) <= 2.0 and t["y"] > iy), key=lambda t: t["y"])
                near = below[0]["text"] if below else "—"
                offenders.append(
                    f"icon@({ix:g},{iy:g}) has no inline-left label on its row — lone glyph stacked above '{near}'"
                )
        self.assertEqual(
            [], offenders,
            "each tile icon must sit INLINE-LEFT of its label, never stacked above the value:\n  "
            + "\n  ".join(offenders),
        )

    def test_icons_are_canonical_round_cap_line_icons(self):
        icons = self._tile_icons(self._hero())
        offenders = [
            f"icon@({i['x']:g},{i['y']:g}) lacks round line-caps (solid-fill / hand-drawn glyph)"
            for i in icons
            if 'stroke-linecap="round"' not in (i["attrs"] + i["body"])
        ]
        self.assertEqual(
            [], offenders,
            "every tile icon must be a canonical Lucide LINE icon with round caps/joins:\n  " + "\n  ".join(offenders),
        )

    def test_icon_stroke_constant_on_screen(self):
        """On-screen stroke = stroke-width * scale must be ~1.5px on every icon
        (stroke-width = 36/renderPx) so it matches the label weight and does not
        thin/blunt under the SVG scale or GitHub's column downscaling."""
        icons = self._tile_icons(self._hero())
        offenders = []
        for i in icons:
            m = _STROKE_W.search(i["attrs"] + i["body"])
            if not m:  # fill-only glyphs have no stroke; the round-cap test governs those
                continue
            on_screen = float(m.group(1)) * float(i["scale"])
            if abs(on_screen - 1.5) > 0.15:
                offenders.append(f"icon@({i['x']:g},{i['y']:g}) on-screen stroke {on_screen:.2f}px != ~1.5px")
        self.assertEqual(
            [], offenders,
            "tile icon stroke must be a constant ~1.5px on screen (stroke-width = 36/renderPx):\n  "
            + "\n  ".join(offenders),
        )


if __name__ == "__main__":
    unittest.main()

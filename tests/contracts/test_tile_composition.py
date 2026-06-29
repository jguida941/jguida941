"""Red-first TILE / KPI COMPOSITION contract — authority: premium-dashboard KPI anatomy.

Encodes the premium KPI anatomy on the RENDERED SVG of the real generators:
  * label-top / value-below (stacking order label -> value).
  * tile VALUE font-size >= 2x the LABEL font-size.
  * exactly ONE number per tile value (value split from its noun).
  * hero KPI: unique largest text, >= 2.5x its label, in neutral ink (never accent).

Palette-agnostic: all colors import from the token source (theme = one edit).
The CURRENT metric_tile renders value-above-label at metric(22) over caption(12) =
1.83x, so the first two assertions fire RED on the live code.
"""
from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from scripts.core.config import (
    BLUE,
    CYAN,
    GREEN,
    ORANGE,
    PURPLE,
    RED,
    TEXT_BRIGHT,
    TEXT_DIM,
)

TEXT_DIM_HEX = TEXT_DIM.lower()
TEXT_BRIGHT_HEX = TEXT_BRIGHT.lower()
ACCENT_HUES = {c.lower() for c in (CYAN, BLUE, GREEN, ORANGE, PURPLE, RED)}

_METRIC_SIZES = {22.0, 26.0}
_LABEL_SIZE = 12.0
_DISPLAY_SIZE = 46.0
_BODY_SIZE = 14.0

_TEXT = re.compile(
    r'<text x="(-?[0-9.]+)" y="(-?[0-9.]+)" fill="(#[0-9a-fA-F]+)" font-size="([0-9.]+)"[^>]*>(.*?)</text>',
    re.S,
)
_NUMBER = re.compile(r"\d[\d,\.]*")
_CLEAN_VALUE = re.compile(r"^\s*[\d,\.]+\s*[kKmMbB%]{0,1}\s*$")


class _Node:
    __slots__ = ("x", "y", "color", "size", "text")

    def __init__(self, x, y, color, size, text):
        self.x = float(x)
        self.y = float(y)
        self.color = color.lower()
        self.size = float(size)
        self.text = text


def _nodes(svg: str):
    return [_Node(*m) for m in _TEXT.findall(svg)]


def _tiles(svg: str):
    """Pair each secondary-metric VALUE (size 22/26, bright ink, holds a number)
    with its tile's LABEL — the muted caption indented past the tile's inline-left
    icon (label.x ~= value.x + icon_width + gap). The indent distinguishes the label
    from any same-size caption (which is full-left at value.x), so the assertions
    (label-above-value, value >= 2x label) read the real label, not the caption."""
    nodes = _nodes(svg)
    values = [n for n in nodes if n.size in _METRIC_SIZES and n.color == TEXT_BRIGHT_HEX and _NUMBER.search(n.text)]
    labels = [n for n in nodes if n.size == _LABEL_SIZE and n.color == TEXT_DIM_HEX]
    tiles = []
    for v in values:
        cands = [l for l in labels if 10.0 <= (l.x - v.x) <= 40.0]
        if not cands:
            continue
        label = min(cands, key=lambda l: abs(l.y - v.y))
        tiles.append((v, label))
    return tiles


class TileKpiCompositionContract(unittest.TestCase):
    """Premium KPI anatomy on the rendered cards: label-top/value-below tiles,
    value >= 2x label, one number per tile, unique neutral hero KPI."""

    def _badges(self, out: str) -> str:
        from scripts.rendering.generate_badges import generate

        generate(output_path=out, public_nonfork_repos=42, public_forks=8,
                 private_owned_repos=146, ci_count=16, last_year_contributions=8104)
        return Path(out).read_text(encoding="utf-8")

    def _scorecard(self, out: str) -> str:
        from scripts.rendering.generate_builder_scorecard import generate

        generate({"last_year_contributions": 8104, "active_days_last_year": 287, "active_repos_7d": 5,
                  "ci_coverage_pct": 82, "automation_workflows": 16, "releases_30d": 3,
                  "primary_lang_share_pct": 61.4, "median_days_since_push": 4}, output_path=out)
        return Path(out).read_text(encoding="utf-8")

    def _hero(self, out: str) -> str:
        from scripts.rendering.generate_metrics_general import generate

        generate(username="jguida941", snapshot={
            "last_year_contributions": 8104, "public_scope_commits": 4264, "total_repos": 67,
            "private_owned_repos": 146, "total_stars": 78, "languages_count": 24,
            "prs_merged": 35, "releases": 0, "ci_repos": 16, "streak_days": 2,
        }, generated_at="2026-06-28T00:00:00Z", output_path=out)
        return Path(out).read_text(encoding="utf-8")

    def _cards(self):
        return (("badges", self._badges), ("builder_scorecard", self._scorecard))

    def test_secondary_tile_label_sits_above_value(self):
        for name, render in self._cards():
            with tempfile.TemporaryDirectory() as d:
                svg = render(str(Path(d) / "card.svg"))
            tiles = _tiles(svg)
            self.assertGreaterEqual(len(tiles), 4, f"{name}: expected >=4 tiles, paired {len(tiles)}")
            for value, label in tiles:
                self.assertLess(
                    label.y, value.y,
                    f"{name}: tile label '{label.text}' (y={label.y}) must sit ABOVE its value "
                    f"'{value.text}' (y={value.y}) — premium tiles are label-top/value-below",
                )

    def test_secondary_tile_value_at_least_2x_label(self):
        for name, render in self._cards():
            with tempfile.TemporaryDirectory() as d:
                svg = render(str(Path(d) / "card.svg"))
            tiles = _tiles(svg)
            self.assertGreaterEqual(len(tiles), 4, f"{name}: expected >=4 tiles, paired {len(tiles)}")
            for value, label in tiles:
                self.assertGreaterEqual(
                    value.size, 2.0 * label.size,
                    f"{name}: value '{value.text}' {value.size:g}px must be >=2x label "
                    f"'{label.text}' {label.size:g}px",
                )

    def test_one_number_per_tile(self):
        for name, render in self._cards():
            with tempfile.TemporaryDirectory() as d:
                svg = render(str(Path(d) / "card.svg"))
            tiles = _tiles(svg)
            self.assertGreaterEqual(len(tiles), 4, f"{name}: expected >=4 tiles, paired {len(tiles)}")
            for value, _label in tiles:
                self.assertEqual(len(_NUMBER.findall(value.text)), 1,
                                 f"{name}: tile value '{value.text}' must be exactly ONE number")
                self.assertRegex(value.text, _CLEAN_VALUE,
                                 f"{name}: tile value '{value.text}' must be a bare number (+unit), not value+noun")

    def test_hero_kpi_unique_largest_2_5x_label_neutral_ink(self):
        with tempfile.TemporaryDirectory() as d:
            svg = self._hero(str(Path(d) / "hero.svg"))
        nodes = _nodes(svg)
        self.assertTrue(nodes, "hero emitted no text")
        top = max(n.size for n in nodes)
        biggest = [n for n in nodes if n.size == top]
        self.assertEqual(len(biggest), 1, "exactly one dominant hero KPI value (unique largest font)")
        kpi = biggest[0]
        self.assertEqual(kpi.size, _DISPLAY_SIZE, "hero KPI must render at the display token (46)")
        label = next((n for n in nodes if abs(n.x - kpi.x) < 0.5 and n.size == _BODY_SIZE and n.y > kpi.y), None)
        self.assertIsNotNone(label, "hero KPI must carry a body-size label below the value")
        self.assertGreaterEqual(kpi.size, 2.5 * label.size,
                                f"hero KPI {kpi.size:g}px must be >=2.5x its label {label.size:g}px")
        self.assertEqual(kpi.color, TEXT_BRIGHT_HEX, "hero KPI value must use neutral bright ink")
        self.assertNotIn(kpi.color, ACCENT_HUES, "hero KPI value must never be an accent hue")


if __name__ == "__main__":
    unittest.main()

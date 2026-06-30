"""P5-1 — the CHARACTER law: each theme must POSITIVELY express its design language.

test_design_distinctness proves themes DIFFER; CHARACTER proves each is unmistakably ITS
language — the answer to "where are the invariants for their respective proper styles."
Measured on the per-theme IA (design_tokens density/radius/type), grounded in the design-
language research (the workflow that read Apple HIG Layout + Power BI report-design docs):

  * Apple HIG: AIRY — generous card padding + gaps, large soft corners, large display type.
  * Power BI: TIGHT — compact data-ink density, small padding/gaps, sharp bordered tiles.
  * Liquid Glass: the MEDIUM anchor between them.

These are the structural (box) invariants. The richer rendered-DOM signals (≤1 table for
Apple, multi-series bars + a data table for Power BI, the categorical palette, the 8px snap
grid) + the per-component anatomy land in P5-2/P5-3 as the chart/component library grows.
Mutation-proven: collapsing a theme's density to another's reddens the ordering law.
"""
from __future__ import annotations

import unittest

from scripts.core import config
from scripts.rendering import design_tokens as dt


class DesignCharacterContract(unittest.TestCase):
    def test_apple_is_airy(self):
        """Apple HIG > Foundations > Layout: comfortable margins, generous spacing."""
        d = dt.density("apple-dark")
        self.assertEqual("airy", d["band"])
        self.assertGreaterEqual(d["panel_pad"], 24, "Apple: generous card padding (HIG Layout)")
        self.assertGreaterEqual(d["gap"], 20, "Apple: comfortable spacing between cards")
        self.assertGreaterEqual(dt.radius("apple-dark")["panel"], 18, "Apple: large soft corners")
        self.assertGreaterEqual(dt.type_scale("apple-dark")["display"][0], 48, "Apple: large-title hero")

    def test_power_bi_is_tight_and_sharp(self):
        """Power BI report design: dense data-ink grid, sharp bordered tiles, tabular type."""
        d = dt.density("power-bi")
        self.assertEqual("tight", d["band"])
        self.assertLessEqual(d["panel_pad"], 18, "Power BI: dense data-ink panels")
        self.assertLessEqual(d["gap"], 10, "Power BI: tight snap grid")
        self.assertLessEqual(dt.radius("power-bi")["panel"], 6, "Power BI: sharp, near-square tiles")

    def test_density_bands_are_ordered_and_distinct(self):
        """Airy > Medium > Tight, all distinct (mutation-proof: collapse one and this reds)."""
        pads = {n: dt.density(n)["panel_pad"] for n in dt.THEMES}
        self.assertGreater(pads["apple-dark"], pads["liquid-glass"], "Apple must be airier than the anchor")
        self.assertGreater(pads["liquid-glass"], pads["power-bi"], "Power BI must be tighter than the anchor")
        self.assertEqual(len(set(pads.values())), len(pads), "each theme's density must be distinct")

    def test_power_bi_is_table_forward_apple_is_not(self):
        """Per the research: Power BI favors a data table/matrix (tabular encoding); Apple is
        stat/bar-forward and AVOIDS dense tables. So the languages section becomes a DATA TABLE
        only under [data-theme="power-bi"]; every other theme keeps the bar (table hidden)."""
        from scripts.pipeline.web_render import render_dashboard
        html = render_dashboard()
        self.assertIn('class="lang-table"', html, "Power BI needs a languages data-table option")
        self.assertIn('[data-theme="power-bi"] .lang-table', html, "the table is shown under Power BI")
        self.assertRegex(html, r"\.lang-table\s*\{[^}]*display:\s*none",
                         "the table is hidden by default — Apple/Liquid Glass stay bar/stat-forward")
        self.assertIn('[data-theme="power-bi"] .lang-bars { display: none', html,
                      "Power BI replaces the bar with the table (the matrix look)")

    def test_density_is_web_only_and_preserves_svg_parity(self):
        """Density is a web concern; the DEFAULT theme's type/radius still equal config."""
        self.assertEqual(dt.type_scale(dt.DEFAULT_THEME), {k: tuple(v) for k, v in config.TYPE_SCALE.items()})
        dr = dt.radius(dt.DEFAULT_THEME)
        self.assertEqual((dr["panel"], dr["tile"]), (config.GLASS_RX, config.GLASS_TILE_RX))


if __name__ == "__main__":
    unittest.main()

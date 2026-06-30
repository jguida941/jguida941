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

    # RETIRED test_kpi_grid_density_is_inverted_from_padding (codex must-fix): it guarded the
    # per-theme `.tiles` KPI-grid density via dt.density()["tile_min"], but the readout is now the
    # grouped inset-LIST (single column, no tile_min consumer), so the test guarded an inert value
    # and gave false confidence a rendered grid invariant existed. The `tile_min` field stays in
    # THEME_IA as a RESERVED density spec for the future per-theme showcase GRID layouts (where
    # Power-BI-dense vs Apple-spread will matter again), and `--tile-min` is no longer emitted into
    # the scorecard CSS. When the showcase grids land, a real rendered-grid density invariant
    # replaces this — tested against that surface, not as latent data.

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

    # RETIRED test_apple_drops_the_dense_heatmap_grid: that invariant told Apple to HIDE the
    # activity heatmap ("summary-forward, avoids dense grids"), but deleting the rhythm
    # visualization left a near-empty "When I Code" panel — the content-to-chrome anti-pattern the
    # owner caught. A distinctness invariant must never trump content-to-chrome. Apple now shows the
    # rhythm like every theme; its distinctness comes from colour/type/density/material. The
    # forthcoming GROUPED_DENSE_READOUT pattern invariant (docs/design/liquid-glass.md) is the guard
    # that forbids under-filled surfaces going forward.

    # RETIRED test_kpi_density_character_survives_on_mobile + test_kpi_grid_never_overflows_a_narrow_
    # viewport: both governed the `.tiles` auto-fit KPI GRID (per-theme tile_min density + the
    # minmax(min(),100%) overflow clamp). The de-AI readout refactor replaced that card grid with the
    # Apple grouped inset-LIST (.mgroup of bare .mrow Value-1 rows) — a single column of dense rows
    # that has no per-theme tile_min and cannot overflow, so these two invariants no longer have a
    # subject. They are SUPERSEDED by test_metric_readout_is_grouped_not_giant_boxes below (a stronger
    # pattern invariant). Not silently dropped: recorded here + in docs/plans/ACTIVE.md.

    def test_metric_readout_is_grouped_not_giant_boxes(self):
        """PATTERN invariant (docs/design/liquid-glass.md, cited Apple HIG): a readout of >=3 sibling
        scalar metrics is ONE inset-grouped container of hairline-divided 'Value 1' rows — NOT N
        independently-chromed cards (the giant-empty-box AI tell: 'huge blocks around stuff … Apple
        designers and pros don't do this'). The FIRST pattern invariant — composition, not a padding
        token (a tall rounded card with one number PASSES `panel_pad>=24` while ~70% dead space).
        The deterministic gate is STRUCTURAL + COLUMN-INDEPENDENT, closing the two escapes codex
        found: a 2-up grid of chromed tiles AND a short chromed dead-space box both carry per-metric
        chrome, so both FAIL regardless of columns/height. The geometric ink-fill is the visual-
        receipt judgment, not faked here. Mutation-proof: re-add border-radius/background to `.mrow`."""
        import re
        from scripts.pipeline.web_render import render_dashboard
        html = render_dashboard()
        self.assertIn('class="mgroup"', html, "the metric readout must be ONE grouped container")
        self.assertIn('class="mrow"', html, "metrics must be Value-1 rows inside the group, not cards")
        self.assertRegex(html, r"\.mgroup\s*\{[^}]*border-radius:",
                         "the group container carries the rounded chrome")
        mrow = re.search(r"\.mrow\s*\{([^}]*)\}", html)
        self.assertIsNotNone(mrow, ".mrow rule must exist")
        body = mrow.group(1)
        for chrome in ("border-radius", "background", "border:"):
            self.assertNotIn(chrome, body,
                             f".mrow must carry NO independent {chrome} — only the group is chromed")
        self.assertRegex(html, r"\.mrow\s*\+\s*\.mrow\s*\{[^}]*border-top:",
                         "adjacent metric rows are divided by a hairline, not gapped cards")
        self.assertRegex(html, r"\.mrow\s*\{[^}]*display:\s*(grid|flex)",
                         "rows are inline label+value (Value-1), not a tall stacked box")

    def test_density_is_web_only_and_preserves_svg_parity(self):
        """Density is a web concern; the DEFAULT theme's type/radius still equal config."""
        self.assertEqual(dt.type_scale(dt.DEFAULT_THEME), {k: tuple(v) for k, v in config.TYPE_SCALE.items()})
        dr = dt.radius(dt.DEFAULT_THEME)
        self.assertEqual((dr["panel"], dr["tile"]), (config.GLASS_RX, config.GLASS_TILE_RX))


if __name__ == "__main__":
    unittest.main()

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

    def test_kpi_grid_density_is_inverted_from_padding(self):
        """The KPI grid packs INVERSELY to padding: Power BI's tile_min is smallest (4-6 KPIs/row,
        Power BI report design), Apple's is largest (few large cards, HIG Layout). Distinct."""
        mins = {n: dt.density(n)["tile_min"] for n in dt.THEMES}
        self.assertLess(mins["power-bi"], mins["liquid-glass"], "Power BI packs a denser KPI grid")
        self.assertGreater(mins["apple-dark"], mins["liquid-glass"], "Apple spreads to few large cards")
        self.assertEqual(len(set(mins.values())), len(mins), "each theme's KPI-grid density must be distinct")

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

    def test_kpi_density_character_survives_on_mobile(self):
        """Mobile must NOT flatten the per-language KPI grid to one column for everyone — that
        would erase the density CHARACTER exactly where phones make it matter most. A Power BI
        report stays multi-column data-dense on a phone (small tile_min => >=2 KPIs/row at ~390px);
        Apple collapses to one large card (tile_min ~ the viewport). So `.tiles` must keep its
        auto-fit minmax(var(--tile-min)) grid at EVERY width — only section-level layout
        (.bento/.lanes/.langlegend) may collapse to a single column on a narrow screen.
        Mutation-proof: put `.tiles` back in the mobile `grid-template-columns: 1fr` list and
        Power BI flattens to Apple's single column — this reds."""
        import re
        from scripts.pipeline.web_render import render_dashboard
        html = render_dashboard()
        # the base KPI grid stays per-theme: auto-fit on each language's own tile-min
        self.assertRegex(html, r"\.tiles\s*\{[^}]*minmax\([^}]*var\(--tile-min",
                         "the KPI grid must remain auto-fit on the per-theme --tile-min")
        # For every SINGLE-column collapse (`grid-template-columns: 1fr;` — NOT the `1fr 1fr`
        # bento base), walk back to the selector that owns it; `.tiles` must never be one of them.
        for hit in re.finditer(r"grid-template-columns:\s*1fr\s*;", html):
            brace = html.rfind("{", 0, hit.start())          # the { opening this rule's body
            prev = max(html.rfind("}", 0, brace), html.rfind("{", 0, brace))  # boundary before selector
            selector = html[prev + 1: brace]
            self.assertNotRegex(
                selector, r"\.tiles(\s|,|$)",
                ".tiles must keep its per-theme auto-fit grid on mobile (Power BI stays dense, "
                "Apple goes to one card) — it must never collapse to a fixed single column")

    def test_kpi_grid_never_overflows_a_narrow_viewport(self):
        """A theme's tile_min can legitimately EXCEED a phone's width (Apple's is 380px > a ~390px
        viewport, and the airy panel padding leaves only ~300px inside). A raw
        minmax(380px, 1fr) then forces a track WIDER than the screen, so the cards overflow
        horizontally — exactly the Apple-Dark / iOS-Safari bug. The KPI grid must CLAMP its
        minimum track to the container: minmax(min(var(--tile-min), 100%), 1fr) keeps the airy
        large-card density on a wide screen but collapses to one FITTING card on a phone, so NO
        theme — whatever its tile_min — can overflow. Mutation-proof: drop the `min(...,100%)`
        clamp and Apple Dark overflows ~390px again."""
        from scripts.pipeline.web_render import render_dashboard
        html = render_dashboard()
        self.assertRegex(
            html, r"\.tiles\s*\{[^}]*minmax\(\s*min\(\s*var\(--tile-min[^)]*\)\s*,\s*100%\s*\)",
            "the KPI grid must clamp its track to the viewport — "
            "minmax(min(var(--tile-min), 100%), 1fr) — or a theme whose tile_min exceeds the screen "
            "(Apple 380px) overflows horizontally on a phone")

    # DEFERRED to its own slice (the de-AI readout refactor): test_metric_readout_is_grouped_not_
    # giant_boxes — the first PATTERN invariant (grouped .mgroup container of bare hairline-divided
    # .mrow Value-1 rows; per-metric chrome forbidden, column-independent). Doc-grounded + codex-
    # reviewed in docs/design/liquid-glass.md §7; it lands RED-first WITH the web_render refactor +
    # the before/after visual receipt, so it is not committed ahead of the implementation it gates.

    def test_density_is_web_only_and_preserves_svg_parity(self):
        """Density is a web concern; the DEFAULT theme's type/radius still equal config."""
        self.assertEqual(dt.type_scale(dt.DEFAULT_THEME), {k: tuple(v) for k, v in config.TYPE_SCALE.items()})
        dr = dt.radius(dt.DEFAULT_THEME)
        self.assertEqual((dr["panel"], dr["tile"]), (config.GLASS_RX, config.GLASS_TILE_RX))


if __name__ == "__main__":
    unittest.main()

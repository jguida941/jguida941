"""P5-COMPONENTS-GROW instance #3: the CARD / grouped metric surface (authority: webkit).

The card is the direct answer to the owner's reframe — "giant KPI boxes, one number floating in
70% dead space, each stat in its own full-width chromed card" is the AI tell; a real system groups
related metrics as ROWS in ONE container. Doc-grounded (see docs/design/<lang>.md card section):

- liquid-glass / apple-dark  Apple grouped INSET list (UIKit `insetGrouped`, HIG lists-and-tables):
  ONE rounded inset container; rows are chrome-less content; leading label + trailing value inline;
  1px hairline divider; hierarchy from TYPE (value vs secondary label), not from per-stat boxes.
  liquid-glass frosted vs apple-dark OPAQUE — the honest material wall.
- carbon  IBM Carbon Tile / structured list: ONE FLAT SQUARE (radius 0) container; rows split by
  full-bleed 1px `$border-subtle` gridlines; NO elevation ("do not add a drop shadow to tiles"); IBM Plex.

The STRUCTURAL composition is deterministic (single container, >=2 rows, chrome-less rows, hairline
divider, inline row AXIS). "Content fills the card / no dead space" is JUDGMENT — it ships `candidate`
+ a visual receipt (a static parser sees declared boxes, not rendered ink), NEVER a fake-green number.
candidate_only.
"""
from __future__ import annotations

import re
import unittest


def _rows(html: str) -> int:
    return html.count('class="card-row"')


def _row_rule(css: str) -> str:
    m = re.search(r"\.card-row\s*\{([^}]*)\}", css)
    return m.group(1) if m else ""


class DesignCardContract(unittest.TestCase):
    def test_render_card_groups_multiple_rows_in_one_container(self):
        """Every active profile's card is ONE container holding >=2 chrome-less rows (the
        anti-'grid of chromed tiles' / anti-'one stat per full-width card' law)."""
        from scripts.rendering.design import loader
        from scripts.rendering.webkit.components import render_card
        for name in loader.load("_index")["active_design_profiles"]:
            variant = loader.load(name)["components"]["card"]["variants"][0]
            html, css = render_card(name, variant, "rest")
            self.assertGreaterEqual(_rows(html), 2, f"{name}: a metric card groups >=2 rows")
            row = _row_rule(css)
            self.assertNotIn("border-radius", row, f"{name}: rows carry NO independent radius (chrome-less)")
            self.assertNotRegex(row, r"background:\s*(?!transparent|none)[^;\s]",
                                f"{name}: rows carry NO independent background (chrome-less)")
            self.assertRegex(css, r"\.card-row\s*\+\s*\.card-row\s*\{[^}]*border-top:\s*1px",
                             f"{name}: adjacent rows divided by a 1px hairline, not 4-side chrome")
            self.assertIn("display: flex", row, f"{name}: a row is a horizontal label+value axis")
            self.assertNotIn("flex-direction: column", row, f"{name}: a row is NOT stacked (column)")

    def test_liquid_glass_card_is_a_rounded_frosted_grouped_list(self):
        """docs/design/liquid-glass.md — Apple inset grouped list in Liquid Glass: rounded container,
        frosted backdrop-filter, hairline-divided rows."""
        from scripts.rendering.webkit.components import render_card
        _, css = render_card("liquid-glass", "metrics", "rest")
        self.assertIn("border-radius: 14px", css, "liquid-glass card is rounded (inset grouped list)")
        self.assertIn("backdrop-filter", css, "liquid-glass card is frosted glass")

    def test_carbon_card_is_a_flat_square_gridlined_tile(self):
        """docs/design/carbon.md — IBM Carbon Tile/structured list: square (radius 0), flat (NO
        shadow — 'do not add a drop shadow to tiles'), IBM Plex, gridline-divided rows."""
        from scripts.rendering.webkit.components import render_card
        _, css = render_card("carbon", "metrics", "rest")
        self.assertIn("border-radius: 0px", css, "carbon Tile is square (radius 0)")
        self.assertNotIn("backdrop-filter", css, "carbon Tile is flat-fill, not glass")
        self.assertNotIn("box-shadow", css, "carbon Tile has NO elevation (no drop shadow)")
        self.assertIn("IBM Plex", css, "carbon Tile is IBM Plex Sans")

    def test_apple_dark_card_is_a_rounded_opaque_grouped_list(self):
        """docs/design/apple-dark.md — Apple grouped list on an OPAQUE dark surface (the material
        wall vs liquid-glass): rounded, hairline-divided, NO backdrop-filter."""
        from scripts.rendering.webkit.components import render_card
        _, css = render_card("apple-dark", "metrics", "rest")
        self.assertIn("border-radius: 14px", css, "apple-dark card is rounded")
        self.assertNotIn("backdrop-filter", css, "apple-dark card is OPAQUE, not frosted glass")

    def test_card_distinctness_rests_on_the_two_honest_walls(self):
        """Distinctness for the card is declared on the REAL deterministic walls, NOT a padded
        numeric quorum (the near-pair liquid-glass↔apple-dark share radius+divider — both are Apple
        rounded grouped lists — so their ONLY honest separator is MATERIAL; the research warned
        against inventing a second axis). The two walls together separate all three:
          - MATERIAL wall: liquid-glass is glass (backdrop-filter); carbon + apple-dark are opaque.
          - SHAPE wall:    carbon is square (radius 0); liquid-glass + apple-dark are rounded (>0)."""
        from scripts.rendering.webkit.components import render_card

        def facts(name):
            _, css = render_card(name, "metrics", "rest")
            base = re.search(r"\.card-[\w-]+\s*\{([^}]*)\}", css).group(1)
            radius = int(re.search(r"border-radius:\s*(\d+)px", base).group(1))
            return {"glass": "backdrop-filter" in base, "radius": radius}

        lg, cb, ad = facts("liquid-glass"), facts("carbon"), facts("apple-dark")
        # MATERIAL wall: glass is the ONLY frosted card
        self.assertTrue(lg["glass"], "liquid-glass card is glass")
        self.assertFalse(cb["glass"], "carbon card is opaque/flat")
        self.assertFalse(ad["glass"], "apple-dark card is opaque")
        # SHAPE wall: carbon is the ONLY square card
        self.assertEqual(cb["radius"], 0, "carbon card is square")
        self.assertGreater(lg["radius"], 0, "liquid-glass card is rounded")
        self.assertGreater(ad["radius"], 0, "apple-dark card is rounded")
        # every PAIR separated by >=1 real wall: lg≠cb (material+shape), lg≠ad (material), cb≠ad (shape)
        self.assertNotEqual((lg["glass"], lg["radius"] == 0), (ad["glass"], ad["radius"] == 0),
                            "liquid-glass and apple-dark must differ (material wall)")
        self.assertNotEqual((cb["glass"], cb["radius"] == 0), (ad["glass"], ad["radius"] == 0),
                            "carbon and apple-dark must differ (shape wall)")


class CardAdapterFailsClosed(unittest.TestCase):
    """codex card fold: the STATIC card parser must not manufacture a pass on the exact evasions the
    owner was burned by — a static green while the render is wrong. Each degenerate input must fail."""

    def _facts(self, html, css):
        from scripts.rendering.webkit.design_render_adapter import card_facts
        return card_facts(html, css)

    def test_two_single_row_containers_do_not_pass_single_container(self):
        from scripts.contracts.design_predicates import card_single_container
        html = ('<div class="card-x card-group"><div class="card-row"></div></div>'
                '<div class="card-x card-group"><div class="card-row"></div></div>')
        css = (".card-x { border-radius: 14px; }\n.card-x .card-row { display: flex; background: transparent; }\n"
               ".card-x .card-row + .card-row { border-top: 1px solid #000; }")
        f = self._facts(html, css)
        self.assertEqual(f["container_count"], 2)
        self.assertFalse(card_single_container(f), "two 1-row containers is a grid-of-tiles, not one card")

    def test_row_background_color_longhand_is_not_chromeless(self):
        f = self._facts('<div class="card-x card-group"><div class="card-row"></div></div>',
                        ".card-x { } \n.card-x .card-row { display: flex; background-color: #fff; }")
        self.assertFalse(f["rows_chromeless"], "a background-color longhand is still row chrome")

    def test_row_radius_longhand_is_not_chromeless(self):
        f = self._facts('<div class="card-x card-group"><div class="card-row"></div></div>',
                        ".card-x { }\n.card-x .card-row { display: flex; border-top-left-radius: 8px; }")
        self.assertFalse(f["rows_chromeless"], "a *-radius longhand is still row chrome")

    def test_flex_flow_column_is_not_a_horizontal_axis(self):
        f = self._facts('<div class="card-x card-group"><div class="card-row"></div></div>',
                        ".card-x { }\n.card-x .card-row { display: flex; flex-flow: column nowrap; }")
        self.assertFalse(f["rows_horizontal"], "flex-flow column is a stacked axis, not inline")

    def test_invisible_border_is_not_a_divider(self):
        f = self._facts('<div class="card-x card-group"><div class="card-row"></div><div class="card-row"></div></div>',
                        ".card-x { }\n.card-x .card-row { display: flex; }\n"
                        ".card-x .card-row + .card-row { border-top: 1px none transparent; }")
        self.assertFalse(f["divider_1px"], "border-top: 1px none transparent is not a visible hairline")

    def test_solid_transparent_border_is_not_a_divider(self):
        """codex: `border-top: 1px solid transparent` (and a 0-alpha rgba, 2nd pass) HAS `solid` but
        an invisible colour — not a hairline. The gatherer requires a colour that actually paints."""
        for color in ("transparent", "rgba(0,0,0,0)"):
            f = self._facts('<div class="card-x card-group"><div class="card-row"></div><div class="card-row"></div></div>',
                            ".card-x { }\n.card-x .card-row { display: flex; }\n"
                            ".card-x .card-row + .card-row { border-top: 1px solid %s; }" % color)
            self.assertFalse(f["divider_1px"], f"an invisible 1px solid {color} border is not a hairline")

    def test_empty_css_fails_every_card_predicate(self):
        from scripts.contracts.design_predicates import (
            card_single_container, card_hairline_divided, card_rows_inline)
        f = self._facts("", "")
        self.assertFalse(card_single_container(f))
        self.assertFalse(card_hairline_divided(f))
        self.assertFalse(card_rows_inline(f))


if __name__ == "__main__":
    unittest.main()

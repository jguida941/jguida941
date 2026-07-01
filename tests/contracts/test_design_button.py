"""P5-WEBKIT-BUTTON instance #1 (authority: webkit) — the rendered button.

`scripts.rendering.webkit.components.render_button(profile, variant, state) -> (html, css)`
reads a profile's DATA (the DTCG token block + the components.button anatomy block) and emits
HTML+CSS, branching on the per-profile ANATOMY so STRUCTURE differs across languages (not just
tokens). 1a-i stands up the render path + the liquid-glass character; carbon + apple-dark
(the distinctness contrast) and the conformance predicates land in the following greens.
candidate_only.
"""
from __future__ import annotations

import unittest


class DesignButtonContract(unittest.TestCase):
    def test_render_button_emits_html_and_css_for_every_state(self):
        from scripts.rendering.webkit.components import render_button
        for variant in ("prominent", "plain"):
            for state in ("rest", "hover", "active", "focus-visible", "disabled"):
                html, css = render_button("liquid-glass", variant, state)
                self.assertIn("<button", html, f"{variant}/{state}: must emit a <button>")
                self.assertTrue(css.strip(), f"{variant}/{state}: must emit CSS")

    def test_liquid_glass_button_expresses_its_cited_anatomy(self):
        """Cited liquid-glass button (docs/design/liquid-glass.md — Apple Materials + WWDC25
        'Adopting Liquid Glass'): capsule `border-radius:999px`, frosted-glass `backdrop-filter`,
        centered, and a glass-brightness active state (brightness UP, NOT opacity-dim). True
        single-source: the blur/saturate come from `design_tokens.material('liquid-glass')`, never
        a literal baked into render."""
        from scripts.rendering.webkit.components import render_button
        _, rest_css = render_button("liquid-glass", "prominent", "rest")
        self.assertIn("border-radius: 999px", rest_css, "liquid-glass button is a 999px capsule")
        self.assertIn("backdrop-filter", rest_css, "liquid-glass button is frosted glass (material on the button)")
        self.assertRegex(rest_css, r"justify-content:\s*center", "centered-capsule anatomy")
        _, active_css = render_button("liquid-glass", "prominent", "active")
        self.assertIn("brightness(1.18)", active_css, "the glass-brightness state mechanic (brightness UP)")
        self.assertNotIn("opacity: 0.4", active_css, "must NOT use the apple-dark opacity-dim mechanic")

    def test_carbon_button_is_a_genuinely_different_component(self):
        """Cited carbon button (docs/design/carbon.md — IBM Carbon v11): radius 0, label-left /
        icon-right DOM (`space-between`, a trailing icon SIBLING after the label), flat (zero
        box-shadow), token-swap press (a background-color step, NOT a filter/opacity/transform),
        2px SQUARE inset focus. Structurally a DIFFERENT COMPONENT from the Apple capsules — the
        anatomy hook emits a different DOM, not a token swap of one template."""
        from scripts.rendering.webkit.components import render_button
        html, rest_css = render_button("carbon", "primary", "rest")
        self.assertIn("border-radius: 0px", rest_css, "carbon button is square")
        self.assertRegex(rest_css, r"justify-content:\s*space-between", "carbon anatomy is label-left/icon-right")
        self.assertIn("btn-label", html, "carbon emits a label node")
        self.assertIn("btn-icon", html, "carbon emits a trailing icon node")
        self.assertLess(html.index("btn-label"), html.index("btn-icon"), "label precedes the trailing icon")
        self.assertNotIn("backdrop-filter", rest_css, "carbon is flat-fill, not glass")
        self.assertNotIn("box-shadow", rest_css, "carbon button is flat — zero elevation")
        _, active_css = render_button("carbon", "primary", "active")
        self.assertIn("background-color: #002d9c", active_css, "carbon press is a token-swap")
        self.assertNotIn("opacity", active_css, "carbon press is NOT an opacity-dim (the apple tell)")
        self.assertNotIn("brightness", active_css, "carbon press is NOT glass-brightness (the liquid tell)")
        _, focus_css = render_button("carbon", "primary", "focus-visible")
        self.assertIn("inset", focus_css, "carbon focus is a 2px square inset ring (not a rounded halo)")

    def test_apple_dark_button_is_a_capsule_that_dims_not_glows(self):
        """Cited apple-dark button (docs/design/apple-dark.md — Apple HIG Buttons + Materials): a
        capsule (`border-radius:999px`) on an OPAQUE fill (NO `backdrop-filter` — apple-dark is not
        glass), ZERO box-shadow, a rounded system focus ring (NOT a square inset), and an
        opacity-DIM press (`opacity:0.4` + scale — dims DOWN), NOT liquid's brightness-UP nor
        carbon's token-swap. It SHARES the capsule with liquid-glass but is a distinct COMPONENT via
        material + mechanic + elevation + focus (codex H2 — clears the quorum with margin)."""
        from scripts.rendering.webkit.components import render_button
        _, rest = render_button("apple-dark", "filled", "rest")
        self.assertIn("border-radius: 999px", rest, "apple-dark button is a capsule")
        self.assertNotIn("backdrop-filter", rest, "apple-dark is OPAQUE, not frosted glass")
        self.assertNotIn("box-shadow", rest, "apple-dark button has ZERO elevation")
        _, active = render_button("apple-dark", "filled", "active")
        self.assertIn("opacity: 0.4", active, "apple-dark press is an opacity-dim (dims DOWN)")
        self.assertNotIn("brightness", active, "NOT the liquid-glass brightness-UP mechanic")
        self.assertNotIn("background-color", active, "NOT the carbon token-swap mechanic")
        _, focus = render_button("apple-dark", "filled", "focus-visible")
        self.assertNotIn("inset", focus, "apple-dark focus is a rounded ring, not a square inset")

    def test_button_fingerprints_are_pairwise_distinct(self):
        """The component-level distinctness law: each active profile's button `fingerprint`
        ({radius_px, state_mechanic, focus_recipe, anatomy, material, elevation}) must differ from
        every other on a QUORUM of >=3 axes — so two languages can never render the same button.
        (Extends the web-IA test_design_distinctness quorum to the component granularity.)"""
        from scripts.rendering.design import loader
        active = loader.load("_index")["active_design_profiles"]
        self.assertGreaterEqual(len(active), 2, "need >=2 active profiles to prove distinctness")
        fps = {p: loader.load(p)["components"]["button"]["fingerprint"] for p in active}
        names = sorted(fps)
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = fps[names[i]], fps[names[j]]
                axes = set(a) | set(b)
                differing = sum(1 for ax in axes if a.get(ax) != b.get(ax))
                self.assertGreaterEqual(
                    differing, 3,
                    f"{names[i]} vs {names[j]}: button fingerprints must differ on >=3 axes (got {differing})")


if __name__ == "__main__":
    unittest.main()

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


if __name__ == "__main__":
    unittest.main()

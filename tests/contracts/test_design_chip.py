"""P5-COMPONENTS-GROW instance #2: the chip/tag (authority: webkit).

`scripts.rendering.webkit.components.render_chip(profile, variant, state) -> (html, css)` reads a
profile's DATA (`components.chip`) and emits HTML+CSS, branching on ANATOMY so a Carbon *dismissible
Tag* (label + trailing `×`) is a DIFFERENT component from an Apple centered pill. Doc-grounded from
each language's PRIMARY docs (see docs/design/<lang>.md chip section):

- liquid-glass  Apple pill = capsule (radius = ½ height), frosted Liquid Glass, sentence-case SF,
  centered label, illuminate-from-within (glass-brightness) press, capsule halo focus.
- carbon        IBM Carbon v11 **Tag**: fixed 16px radius token (NOT the button's 0!), flat fill
  (no blur/shadow), IBM Plex `label-01` 12px/400 sentence case, dismissible trailing `×`, token-swap
  hover, `outline: 2px` focus (NOT the button's inset square ring).
- apple-dark    Apple pill on an OPAQUE system fill (no glass), opacity-dim press, rounded ring.

candidate_only.
"""
from __future__ import annotations

import unittest


class DesignChipContract(unittest.TestCase):
    def test_render_chip_emits_html_and_css_for_every_state(self):
        from scripts.rendering.webkit.components import render_chip
        for variant in ("regular", "prominent"):
            for state in ("rest", "hover", "active", "focus-visible", "disabled"):
                html, css = render_chip("liquid-glass", variant, state)
                self.assertIn("<span", html, f"{variant}/{state}: a chip is a <span> pill")
                self.assertTrue(css.strip(), f"{variant}/{state}: must emit CSS")

    def test_liquid_glass_chip_is_a_frosted_capsule_pill(self):
        """docs/design/liquid-glass.md (Apple Materials + WWDC25 Liquid Glass): capsule
        `border-radius:999px`, frosted `backdrop-filter`, centered label (no dismiss), sentence
        case (no ALL-CAPS), glass-brightness press."""
        from scripts.rendering.webkit.components import render_chip
        html, rest = render_chip("liquid-glass", "regular", "rest")
        self.assertIn("border-radius: 999px", rest, "liquid-glass chip is a capsule pill")
        self.assertIn("backdrop-filter", rest, "liquid-glass chip is frosted glass")
        self.assertNotIn("chip-dismiss", html, "an Apple pill has no trailing dismiss ×")
        self.assertNotIn("text-transform: uppercase", rest, "Apple is sentence case, never ALL-CAPS")
        _, active = render_chip("liquid-glass", "regular", "active")
        self.assertIn("brightness", active, "glass-brightness press (illuminate-from-within)")

    def test_carbon_tag_is_a_flat_dismissible_16px_token_pill(self):
        """docs/design/carbon.md (IBM Carbon v11 Tag): fixed 16px radius token — DISTINCT from the
        Carbon BUTTON's 0 (proof the component, not just the theme, carries shape), flat (no blur or
        shadow), IBM Plex sentence case, a trailing dismiss `×` (label-dismiss anatomy), token-swap
        hover, and an `outline:2px` focus (NOT the button's inset square ring)."""
        from scripts.rendering.webkit.components import render_chip
        html, rest = render_chip("carbon", "gray", "rest")
        self.assertIn("border-radius: 16px", rest, "Carbon Tag is the fixed 16px radius token")
        self.assertNotIn("backdrop-filter", rest, "Carbon Tag is flat-fill, not glass")
        self.assertNotIn("box-shadow", rest, "Carbon Tag is flat — zero elevation")
        self.assertIn("chip-dismiss", html, "Carbon dismissible Tag has a trailing × close button")
        self.assertIn("IBM Plex", rest, "Carbon Tag is IBM Plex Sans")
        self.assertNotIn("text-transform: uppercase", rest, "Carbon Tag is sentence case")
        _, focus = render_chip("carbon", "gray", "focus-visible")
        self.assertIn("outline:", focus, "Carbon Tag focus is a 2px outline (not an inset ring)")
        self.assertNotIn("inset", focus, "Carbon Tag focus is NOT the button's inset square ring")

    def test_apple_dark_chip_is_an_opaque_capsule_that_dims(self):
        """docs/design/apple-dark.md (Apple HIG dark mode + system fills): a capsule on an OPAQUE
        system fill (NO backdrop-filter — the deliberate contrast to liquid-glass), centered label,
        opacity-dim press, rounded system ring focus. Shares the capsule with liquid-glass but is a
        distinct component via material + mechanic + focus (the same honest wall as its button)."""
        from scripts.rendering.webkit.components import render_chip
        html, rest = render_chip("apple-dark", "regular", "rest")
        self.assertIn("border-radius: 999px", rest, "apple-dark chip is a capsule")
        self.assertNotIn("backdrop-filter", rest, "apple-dark chip is OPAQUE, not frosted glass")
        self.assertNotIn("chip-dismiss", html, "an Apple pill has no trailing dismiss ×")
        _, active = render_chip("apple-dark", "regular", "active")
        self.assertIn("opacity", active, "apple-dark press is an opacity-dim")
        self.assertNotIn("brightness", active, "NOT the liquid-glass brightness mechanic")

    def test_chip_fingerprints_are_pairwise_distinct(self):
        """The component-level distinctness law for the chip is RENDER-derived: each active
        profile's rendered chip fingerprint must differ from every other on a QUORUM of >=3 axes —
        two languages can never render the same chip even if the declared JSON claims otherwise."""
        from scripts.rendering.design import loader
        from scripts.quality.design_invariants import rendered_component_fingerprint
        active = loader.load("_index")["active_design_profiles"]
        fps = {p: rendered_component_fingerprint(p, "chip") for p in active}
        names = sorted(fps)
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = fps[names[i]], fps[names[j]]
                axes = set(a) | set(b)
                differing = sum(1 for ax in axes if a.get(ax) != b.get(ax))
                self.assertGreaterEqual(
                    differing, 3,
                    f"{names[i]} vs {names[j]}: chip fingerprints must differ on >=3 axes (got {differing})")

    def test_declared_chip_fingerprints_match_rendered_facts(self):
        """The committed `components.chip.fingerprint` must stay consistent with rendered facts on
        every facts-observable axis; it is not allowed to self-certify distinctness."""
        from scripts.rendering.design import loader
        from scripts.quality.design_invariants import fingerprint_matches_rendered, rendered_component_fingerprint
        for name in loader.load("_index")["active_design_profiles"]:
            declared = loader.load(name)["components"]["chip"]["fingerprint"]
            rendered = rendered_component_fingerprint(name, "chip")
            self.assertTrue(fingerprint_matches_rendered(declared, rendered, "chip"),
                            f"{name}: declared chip fingerprint drifted from rendered facts: {rendered}")

    def test_rendered_chip_fingerprint_ignores_declared_fingerprint_field(self):
        import copy
        from scripts.rendering.design import loader
        from scripts.quality.design_invariants import rendered_component_fingerprint
        prof = copy.deepcopy(loader.load("carbon"))
        prof["components"]["chip"]["fingerprint"] = {"radius_px": 999, "anatomy": "centered-label"}
        self.assertEqual(
            rendered_component_fingerprint("carbon", "chip"),
            rendered_component_fingerprint("carbon", "chip", profile_data=prof),
        )


if __name__ == "__main__":
    unittest.main()

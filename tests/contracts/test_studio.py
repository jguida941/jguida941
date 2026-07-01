"""P5-STUDIO (authority: studio) — the interactive design-system studio.

`render_archetype(profile, profile_data=None)` builds a REAL mini-website (nav + hero + grouped
metric card + buttons + chips) in ONE design language, composed from the SAME token-only renderers
(render_button/chip/card) on that language's own backdrop — so each language reads as ITSELF
(Apple looks Apple, Carbon looks Carbon), not the scorecard reskinned. Slice 1: the static archetype
+ that it morphs between languages. Later slices add the governed component swap (one Python decider,
embedded + looked-up, never a second verdict), persistence, and the drift-guarded page. candidate_only.
"""
from __future__ import annotations

import re
import unittest


def _active():
    from scripts.rendering.design import loader
    return loader.load("_index")["active_design_profiles"]


class StudioArchetypeContract(unittest.TestCase):
    def test_archetype_is_a_full_site_composed_from_the_language(self):
        """Every active language renders a full site: a nav, a hero headline, its OWN button, chip,
        and grouped card — each from the language's own renderers, on the language's own backdrop
        token (no hardcoded canvas)."""
        from scripts.rendering.design import loader
        from scripts.rendering.webkit.archetype import render_archetype
        for name in _active():
            html, css = render_archetype(name)
            self.assertIn("<nav", html, f"{name}: archetype has a nav bar")
            self.assertIn("<h1", html, f"{name}: archetype has a hero headline")
            self.assertIn(f'"btn-{name}-', html, f"{name}: composes the language's OWN button")
            self.assertIn(f'"chip-{name}-', html, f"{name}: composes the language's OWN chip")
            self.assertIn(f'card-{name}-', html, f"{name}: composes the language's OWN grouped card")
            backdrop = loader.resolve_tokens(name)["color"]["backdrop"]
            # the CANVAS specifically (the .arch-<name> shell rule) must use the backdrop token,
            # not just any component recipe that happens to reference it
            self.assertRegex(css, rf"\.arch-{re.escape(name)}\s*\{{[^}}]*background:\s*{re.escape(backdrop)}",
                             f"{name}: the archetype canvas (.arch-{name}) uses the language's backdrop token")

    def test_archetype_morphs_between_languages(self):
        """Different languages render genuinely different sites — the button shape alone flips
        (Carbon square 0 vs the Apple/liquid capsule 999), and the whole CSS differs."""
        from scripts.rendering.webkit.archetype import render_archetype
        _, carbon = render_archetype("carbon")
        _, glass = render_archetype("liquid-glass")
        self.assertNotEqual(carbon, glass, "different languages must render different archetypes")
        self.assertIn("border-radius: 0px", carbon, "carbon button is square")
        self.assertIn("border-radius: 999px", glass, "liquid-glass button is a capsule")

    def test_archetype_has_multiple_chips_and_two_buttons(self):
        """The hero shows a row of tag chips + a primary/secondary button pair — a real page, not a
        single specimen."""
        from scripts.rendering.webkit.archetype import render_archetype
        html, _ = render_archetype("liquid-glass")
        self.assertGreaterEqual(html.count('"chip-liquid-glass-'), 2, "a row of chips")
        self.assertGreaterEqual(html.count('"btn-liquid-glass-'), 2, "a primary + secondary button")


if __name__ == "__main__":
    unittest.main()

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


def _repo_root():
    from pathlib import Path
    for p in Path(__file__).resolve().parents:
        if (p / "scripts").is_dir() and (p / "site").is_dir():
            return p
    raise RuntimeError("repo root not found")


class StudioPageContract(unittest.TestCase):
    def test_studio_page_is_generated_not_handwritten(self):
        """Drift guard: site/studio.html bytes == render_studio() — a hand edit reddens; the page
        can only change by changing the generator + regenerating."""
        from scripts.rendering.studio.studio import render_studio
        page = _repo_root() / "site" / "studio.html"
        self.assertTrue(page.is_file(), "site/studio.html must be generated + committed")
        self.assertEqual(page.read_text(encoding="utf-8"), render_studio(),
                         "studio drift — regenerate via scripts.rendering.studio.studio.write_studio")

    def test_studio_has_a_pure_css_language_switcher_over_every_active_language(self):
        """A live switcher (radio + tab) for EVERY active language, each language's archetype
        embedded — and it is PURE CSS (no <script>), so there is no verdict logic to audit and every
        visible byte is drift-guarded."""
        from scripts.rendering.studio.studio import render_studio
        html = render_studio()
        self.assertNotIn("<script", html, "slice 2 is pure-CSS: no JS on the studio page")
        for name in _active():
            self.assertIn(f'id="lang-{name}"', html, f"{name}: a switcher radio")
            self.assertIn(f'for="lang-{name}"', html, f"{name}: a switcher tab")
            self.assertIn(f'data-lang="{name}"', html, f"{name}: its archetype stage is embedded")
            self.assertIn(f'#lang-{name}:checked ~ .stages', html, f"{name}: pure-CSS reveal rule")

    def test_studio_page_carries_no_decider_logic(self):
        """The studio DISPLAYS; it never re-decides. The generated page contains no admissibility /
        conformance verdict logic (that stays in Python; the governed swap slice embeds DATA + looks
        it up, never recomputes)."""
        from scripts.rendering.studio.studio import render_studio
        html = render_studio()
        for banned in ("is_admissible", "def conform", "compose(", "matching_languages", "admissible_space("):
            self.assertNotIn(banned, html, f"studio page must not carry decider logic: {banned}")

    def test_index_links_to_the_studio(self):
        """The studio must be REACHABLE — the generated front page links to it (else the design
        system stays invisible, the operator's exact complaint)."""
        from scripts.pipeline.web_render import render_dashboard
        self.assertIn("studio.html", render_dashboard(), "index.html must link to the studio")


if __name__ == "__main__":
    unittest.main()

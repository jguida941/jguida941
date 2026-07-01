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
        """The LANGUAGE switch is PURE CSS (radio :checked reveal rules) — no JS decides which
        language shows; a live switcher radio + tab for EVERY active language, its archetype
        embedded. (The component SWAP adds a frozen, verdict-free toggle script, tested separately.)"""
        from scripts.rendering.studio.studio import render_studio
        html = render_studio()
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


class StudioSwapContract(unittest.TestCase):
    """The governed component swap: ONE Python decider embedded + looked up; fragments only for
    admissible cells; inadmissible sources disabled; no property-level controls; the JS re-indexes,
    never re-decides."""

    def test_studio_embeds_the_admissible_space_verbatim(self):
        """STUDIO_SPACE in the page is EXACTLY admissible_space() — the one decider embedded (the JS
        only looks it up)."""
        import json
        import re as _re
        from scripts.quality.settings_admissibility import admissible_space
        from scripts.rendering.studio.studio import render_studio
        m = _re.search(r"window\.STUDIO_SPACE = (\[.*?\]);", render_studio(), _re.S)
        self.assertIsNotNone(m, "the studio must embed STUDIO_SPACE")
        self.assertEqual(json.loads(m.group(1)), admissible_space(),
                         "embedded space must equal the Python admissible_space() verbatim")

    def test_swap_variants_exist_only_for_admissible_cells(self):
        """A pre-rendered archetype variant exists for a swap IFF that cell is admissible; an
        inadmissible source is rendered disabled (no variant target) — no fake-green construction."""
        from scripts.quality.settings_admissibility import admissible_space
        from scripts.rendering.studio.studio import render_studio
        html = render_studio()
        for c in admissible_space():
            if c["source"] == c["base"]:
                continue
            key = f'data-variant="{c["base"]}-{c["component"]}-{c["source"]}"'
            if c["admissible"]:
                self.assertIn(key, html, f"admissible {c} must have a rendered swap variant")
            else:
                self.assertNotIn(key, html, f"inadmissible {c} must NOT have a swap variant")

    def test_inadmissible_swap_is_disabled_and_marked_unconstructable(self):
        """The live proof it's honest: base=carbon, button/chip <- liquid-glass are DISABLED with an
        'unconstructable' reason (a frosted component in a flat Carbon base is a valid instance of no
        language — the 2 inadmissible cells of the space)."""
        from scripts.rendering.studio.studio import render_studio
        html = render_studio()
        for comp in ("button", "chip"):
            self.assertRegex(
                html,
                rf'data-base="carbon"\s+data-component="{comp}"\s+data-source="liquid-glass"\s+disabled\s+title="unconstructable',
                f"carbon {comp} <- liquid-glass must be a disabled/unconstructable option")

    def test_studio_has_no_property_level_or_token_controls(self):
        """codex: the composer offers ONLY wholesale component swaps (base/button/chip/card named by
        active-profile id). It must carry NO property-level or token controls — a partial property
        mix is exactly what the decider rejects, so it is never exposed."""
        import re as _re
        from scripts.rendering.studio.studio import render_studio
        html = render_studio()
        # the ONLY inputs are the language-switch radios — no text/number/range property editors
        for m in _re.finditer(r'<input[^>]*type="([^"]+)"', html):
            self.assertEqual(m.group(1), "radio", "the studio has only language-switch radios, no property editors")
        self.assertNotIn("data-token", html)
        self.assertNotIn("data-property", html)
        # swap options name ONLY a known component + an active profile id (never a raw property value)
        actives = set(_active())
        for m in _re.finditer(r'data-component="([^"]+)"\s+data-source="([^"]+)"', html):
            self.assertIn(m.group(1), ("button", "chip", "card"), "swap targets a known component")
            self.assertIn(m.group(2), actives, f"swap source {m.group(2)!r} must be an active profile id")

    def test_studio_swap_script_is_frozen_and_carries_no_verdict(self):
        """The toggle is a FROZEN blob (== the committed _STUDIO_JS) and re-indexes STUDIO_SPACE by
        lookup — never a second verdict (no is_admissible/conform/compose/matching_languages/
        admissible_space arithmetic)."""
        from scripts.rendering.studio.studio import _STUDIO_JS, render_studio
        html = render_studio()
        self.assertIn(_STUDIO_JS, html, "the swap script must be the committed frozen blob")
        for banned in ("is_admissible", "conform(", "compose(", "matching_languages", "admissible_space("):
            self.assertNotIn(banned, html, f"the studio must carry no decider arithmetic: {banned}")

    def test_composition_admissibility_is_the_AND_of_the_per_slot_cells(self):
        """The honesty pin: whole-composition admissibility == the AND of the per-slot admissible
        cells, over ALL base/source tuples — so the studio ANDing per-slot booleans is RE-INDEXING
        the one Python decider, not a second verdict (and if a cross-component rule is ever added,
        this reddens)."""
        import copy
        from scripts.quality.settings_admissibility import admissible_space, is_admissible
        from scripts.rendering.design import loader
        import itertools
        cell = {(c["base"], c["component"], c["source"]): c["admissible"] for c in admissible_space()}
        actives = _active()
        for base in actives:
            for b_src, c_src, d_src in itertools.product(actives, actives, actives):
                overrides, srcs = {}, {"button": b_src, "chip": c_src, "card": d_src}
                for comp, src in srcs.items():
                    if src != base:
                        overrides[comp] = copy.deepcopy(loader.load(src)["components"][comp])
                expected = all(cell[(base, comp, src)] for comp, src in srcs.items())
                self.assertEqual(is_admissible(base, overrides), bool(expected),
                                 f"AND-decomposition broke: base={base} button<-{b_src} chip<-{c_src} card<-{d_src}")


if __name__ == "__main__":
    unittest.main()

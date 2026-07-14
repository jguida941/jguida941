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


class StudioChromeContract(unittest.TestCase):
    """P5-CHROME A5: the studio CHROME is the governed page-shell (apple-dark house), not hand CSS.
    The design-language studio is itself a rendered instance of a design language, and its switcher
    tabs / swap options derive from that language's tokens — so the design surface follows the same
    process it showcases (the design twin of A3/A4's showcase- and settings-frame-themselves). The
    pure-CSS switcher radios move INSIDE the shell root as its first children (prefix_html) so their
    `:checked ~` sibling selectors keep reaching the switcher + stages that follow."""

    HOUSE = "apple-dark"

    def test_studio_chrome_is_the_governed_page_shell(self):
        """The page frame is render_page_shell(apple-dark): the shell root class + its exact host-chrome
        CSS are present (so the studio is drift-tied to the governed shell, not a hand copy)."""
        from scripts.rendering.pageshell.pageshell import shell_css
        from scripts.rendering.studio.studio import render_studio
        html = render_studio()
        self.assertIn(f'class="ps-{self.HOUSE}"', html, "studio must frame itself in the governed shell")
        self.assertIn(shell_css(self.HOUSE), html, "studio must embed the exact governed shell CSS")

    def test_studio_carries_no_hand_chrome_palette(self):
        """The old hand-written dark chrome (body/h1/.sub/.crumbs) + the copied switcher/swap palette are
        GONE — the frame + the switcher tabs + swap options derive from the shell's tokens
        (var(--surface)/var(--hairline)/var(--accent)/var(--status-danger)), no raw chrome hex. The one
        exception is a hand hex that COINCIDES with a real active design token (the old chrome had
        borrowed liquid-glass's accent #7dcfff as its link colour): that colour is skipped here, because
        the specimen archetypes legitimately render each language's OWN tokens (arch_css, which the brief
        does NOT scan) — banning it would forbid liquid-glass from rendering itself. Every OTHER hand hex
        is not any active token, so it must be gone from the entire page (chrome, switcher, and specimens)."""
        from scripts.rendering.design import loader
        from scripts.rendering.studio.studio import render_studio
        html = render_studio()
        tokens = {v.lower() for name in _active()
                  for v in loader.resolve_tokens(name).get("color", {}).values()}
        for banned in ("#08080c", "#e8e8ee", "#9a9aa6", "#7f7f8c", "#7dcfff", "#23232e", "#c9c9d6",
                       "#12121a", "#101018", "#16161c", "#6b1f2b", "#1a1013", "#3a1a20"):
            if banned.lower() in tokens:                 # a genuine design-language token, not hand chrome
                continue
            self.assertNotIn(banned, html, f"the hand chrome literal {banned} must be gone")
        for tok in ("var(--accent)", "var(--surface)", "var(--status-danger)"):
            self.assertIn(tok, html, f"the studio chrome must derive from {tok}")

    def test_studio_breadcrumb_orients_across_the_surfaces(self):
        """Explainability/IA: the shell breadcrumb links the sibling surfaces so a viewer can navigate —
        the studio previously carried no link home + no showcase/settings orientation via the shell row."""
        from scripts.rendering.studio.studio import render_studio
        html = render_studio()
        self.assertRegex(html, r'class="ps-crumbs"')
        for href in ("index.html", "showcase.html", "settings.html"):
            self.assertIn(href, html, f"the studio page must link {href}")

    def test_studio_radios_render_inside_the_shell_root_before_the_title(self):
        """The pure-CSS switcher constraint: the radios are the shell root's FIRST children (prefix_html),
        rendered BEFORE ps-title, so the generated `#lang-*:checked ~ .switcher`/`~ .stages` sibling
        selectors keep reaching the switcher + stages that follow inside the same root."""
        from scripts.rendering.studio.studio import render_studio
        html = render_studio()
        self.assertRegex(
            html,
            rf'<div class="ps-{self.HOUSE}"[^>]*><div class="ps-main"[^>]*>'
            rf'(?:<input type="radio"[^>]*class="lang-radio"[^>]*>)+'
            r'(?:<nav class="site-nav.*?</nav>)?<h1 class="ps-title"[^>]*>',
            "the switcher radios must render inside the content column as its first children, before ps-title")

    def test_studio_content_css_is_token_only_beyond_the_explicit_allowlist(self):
        """codex A3 #1: `_CONTENT_CSS` is page CONTENT (the switcher + swap surfaces), so the A1 shell
        gate never sees it — without its own scan it is a laundering hole for chrome-like decisions.
        Every colour is a var(); the ONLY bare literals are the module's DECLARED structural allowlist
        (layout px + layout keywords, no colour of any form)."""
        from scripts.rendering.studio.studio import (_CONTENT_ALLOWED_PX,
                                                     _CONTENT_ALLOWED_WORDS, _CONTENT_CSS)
        from scripts.rendering.webkit.design_render_adapter import content_offtokens
        self.assertEqual(
            content_offtokens(_CONTENT_CSS, _CONTENT_ALLOWED_PX, _CONTENT_ALLOWED_WORDS), [],
            "studio content CSS must be token-only beyond its declared structural allowlist")

    def test_content_scanner_catches_a_smuggled_decision(self):
        """Non-vacuity: a colour in ANY form (hex / colour fn / named / system) or an off-allowlist px
        pushed into `_CONTENT_CSS` is flagged — the allowlist is the only escape, and it admits no colour."""
        from scripts.rendering.studio.studio import (_CONTENT_ALLOWED_PX,
                                                     _CONTENT_ALLOWED_WORDS, _CONTENT_CSS)
        from scripts.rendering.webkit.design_render_adapter import content_offtokens
        target = "color: var(--status-danger);"
        self.assertIn(target, _CONTENT_CSS, "the mutation target must exist")
        for smuggle in ("color: #ff0000", "background: rgb(1,2,3)", "color: rebeccapurple",
                        "padding: 8px", "border-color: CanvasText", "color: initial"):
            css = _CONTENT_CSS.replace(target, smuggle + ";")
            self.assertTrue(
                content_offtokens(css, _CONTENT_ALLOWED_PX, _CONTENT_ALLOWED_WORDS),
                f"a smuggled {smuggle!r} must be flagged")

    def test_content_cannot_mint_or_override_tokens(self):
        """codex A3b #1: token DECLARATION belongs to the shell (`root_block`, provenance-pinned) —
        content may only REFERENCE vars. A `:root` block in content (which would OVERRIDE shell tokens,
        since content CSS loads after the shell's) or a custom-property declaration in any content rule
        is flagged — even a non-colour one (minting a token is itself the violation)."""
        from scripts.rendering.studio.studio import (_CONTENT_ALLOWED_PX,
                                                     _CONTENT_ALLOWED_WORDS, _CONTENT_CSS)
        from scripts.rendering.webkit.design_render_adapter import content_offtokens
        for mint in (":root { --evil: #ff0000; }\n" + _CONTENT_CSS,
                     _CONTENT_CSS + "\n.swap-opt { --backdrop: #ff0000; }",
                     _CONTENT_CSS + "\n.swap-opt { --pad: 31px; }"):
            self.assertTrue(
                content_offtokens(mint, _CONTENT_ALLOWED_PX, _CONTENT_ALLOWED_WORDS),
                "content minting/overriding a token must be flagged")

    def test_content_css_is_atrule_free(self):
        """codex A3c: an at-rule PRELUDE is CSS the body-scan never reads — `@media (min-width: 8px)`
        or `@supports (background: #ff0000)` would smuggle literals past the allowlist. Content CSS is
        therefore @-rule-free entirely (the same closed-structure law as the shell)."""
        from scripts.rendering.studio.studio import (_CONTENT_ALLOWED_PX,
                                                     _CONTENT_ALLOWED_WORDS, _CONTENT_CSS)
        from scripts.rendering.webkit.design_render_adapter import content_offtokens
        for atrule in ("@media (min-width: 8px) { .swap-opt { color: var(--ink); } }",
                       "@supports (background: #ff0000) { .swap-opt { color: var(--ink); } }"):
            self.assertTrue(
                content_offtokens(_CONTENT_CSS + "\n" + atrule,
                                  _CONTENT_ALLOWED_PX, _CONTENT_ALLOWED_WORDS),
                f"an at-rule ({atrule.split(' ')[0]}) in content CSS must be flagged")

    def test_content_allowlists_are_pinned_exactly(self):
        """codex A3b #2: the allowlist is the scan's ONLY escape, so it is DATA with a second key —
        widening it (e.g. adding a colour word like `blue`) reddens HERE until this pin is also edited,
        making every widening a visible, reviewed act. Neither set may ever name a colour."""
        from scripts.rendering.studio.studio import _CONTENT_ALLOWED_PX, _CONTENT_ALLOWED_WORDS
        self.assertEqual(_CONTENT_ALLOWED_PX, frozenset({"2px", "64px", "999px"}))
        self.assertEqual(_CONTENT_ALLOWED_WORDS,
                         frozenset({"ui-monospace", "monospace", "not-allowed"}))


if __name__ == "__main__":
    unittest.main()

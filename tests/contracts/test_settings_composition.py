"""P5-SETTINGS (authority: settings) — the governed control plane.

`compose(base, overrides)` + `is_admissible()` (scripts/quality/settings_admissibility.py) are the
ONE Python decision source. An INVALID combination — a partial property mix that is a valid instance
of NO active design language — is UNCONSTRUCTABLE (the design twin of the bootstrap-RED gate).
`render_settings()` -> `site/settings.html` only DISPLAYS the decision; it carries no second (JS)
verdict. candidate_only.
"""
from __future__ import annotations

import copy
import unittest
from pathlib import Path


def _repo_root() -> Path:
    for p in Path(__file__).resolve().parents:
        if (p / "scripts").is_dir() and (p / "site").is_dir():
            return p
    raise RuntimeError("repo root not found")


ROOT = _repo_root()
SETTINGS = ROOT / "site" / "settings.html"


class SettingsCompositionContract(unittest.TestCase):
    def test_invalid_combination_is_unconstructable(self):
        """A Frankenstein card — liquid-glass frosted material + Carbon's square 0-radius — conforms
        to NO active language (neither an Apple rounded grouped list nor a Carbon flat Tile), so the
        gate refuses it. Mutation-provable (widen the admissible logic and it would slip through)."""
        from scripts.quality.settings_admissibility import is_admissible
        self.assertFalse(
            is_admissible("liquid-glass", {"card": {"material": "liquid-glass", "radius_px": 0}}),
            "a frosted square-0 card is a valid instance of no design language -> unconstructable")

    def test_partial_override_on_an_uncovered_axis_is_rejected(self):
        """codex settings #5: an override on an axis NOT covered by an emitted invariant
        (liquid-glass declares no button-anatomy invariant) still cannot slip — admissibility checks
        the composed button's RENDERED facts against the full fingerprint of the language it claims
        to be. A glass capsule wearing Carbon's label-left-icon-right DOM is a valid instance of NO
        language -> unconstructable."""
        from scripts.quality.settings_admissibility import is_admissible
        self.assertFalse(
            is_admissible("liquid-glass", {"button": {"anatomy": "label-left-icon-right"}}),
            "a glass capsule with Carbon's anatomy is a Frankenstein on an uncovered axis")

    def test_public_flat_theme_bridge_does_not_grant_glass_capability(self):
        """Carbon is now a public web theme, so it has a `design_tokens.MATERIALS` bridge row.
        That row must NOT make Carbon glass-capable: a liquid-glass button/chip cannot be
        transplanted into a flat Carbon base and still count as valid liquid glass."""
        from scripts.quality.settings_admissibility import is_admissible
        from scripts.rendering.design import loader
        liquid = loader.load("liquid-glass")["components"]
        self.assertFalse(is_admissible("carbon", {"button": copy.deepcopy(liquid["button"])}))
        self.assertFalse(is_admissible("carbon", {"chip": copy.deepcopy(liquid["chip"])}))

    def test_admissible_wholesale_swap_composes_and_conforms(self):
        """Swapping Carbon's WHOLE card into a liquid-glass base is admissible — the composed card is
        a real Carbon instance (it satisfies Carbon's full card invariant set as rendered)."""
        from scripts.quality.settings_admissibility import is_admissible, matching_languages
        from scripts.rendering.design import loader
        carbon_card = copy.deepcopy(loader.load("carbon")["components"]["card"])
        self.assertTrue(is_admissible("liquid-glass", {"card": carbon_card}),
                        "Carbon's whole card in a liquid-glass base is admissible")
        self.assertIn("carbon", matching_languages("liquid-glass", {"card": carbon_card}, "card"))

    def test_admissible_space_is_computed_not_rubber_stamped(self):
        """The pre-baked space is COMPUTED from the real render (not asserted True): every cell
        marked admissible re-verifies as a full valid language instance. (Honest: a swap that cannot
        render validly is excluded, so the space is a genuine computation, not a rubber stamp.)"""
        from scripts.quality.settings_admissibility import admissible_space, is_admissible
        from scripts.rendering.design import loader
        space = admissible_space()
        self.assertTrue(space, "the admissible space is non-empty")
        for cell in space:
            if cell["admissible"]:
                spec = copy.deepcopy(loader.load(cell["source"])["components"][cell["component"]])
                self.assertTrue(is_admissible(cell["base"], {cell["component"]: spec}),
                                f"admissible cell must re-verify against the render: {cell}")

    def test_settings_page_is_generated_and_has_no_second_verdict_source(self):
        """codex must-fix #2 — ONE Python decider: site/settings.html DISPLAYS the admissibility that
        Python computes. Its only script is the shared verdict-free theme bootstrap."""
        import re
        from scripts.rendering.pageshell.pageshell import theme_continuity_script_tag
        from scripts.rendering.settings.settings import render_settings
        self.assertTrue(SETTINGS.is_file(), "site/settings.html must be generated + committed")
        self.assertEqual(SETTINGS.read_text(encoding="utf-8"), render_settings(),
                         "settings drift — regenerate via scripts.rendering.settings.settings.write_settings")
        scripts = re.findall(r"<script>.*?</script>", SETTINGS.read_text(encoding="utf-8"), re.S)
        self.assertEqual(scripts, [theme_continuity_script_tag()],
                         "theme continuity is the only settings script; Python remains the ONE decider")
        for verdict_token in ("admissible_space", "is_admissible", "matching_languages"):
            self.assertNotIn(verdict_token, scripts[0])


class SettingsChromeContract(unittest.TestCase):
    """P5-CHROME A4: the settings CHROME is the governed page-shell (apple-dark house), not hand CSS.
    The governed control plane is itself a rendered instance of a design language, and its verdict
    pills derive from that language's status tokens — so the control plane follows the same process
    it governs (the design twin of A3's showcase-frames-itself)."""

    HOUSE = "apple-dark"

    def test_settings_chrome_is_the_governed_page_shell(self):
        """The page frame is render_page_shell(apple-dark): the shell root class + its exact host-chrome
        CSS are present (so settings is drift-tied to the governed shell, not a hand copy)."""
        from scripts.rendering.pageshell.pageshell import shell_css
        from scripts.rendering.settings.settings import render_settings
        html = render_settings()
        self.assertIn(f'class="ps-{self.HOUSE}"', html, "settings must frame itself in the governed shell")
        self.assertIn(shell_css(self.HOUSE), html, "settings must embed the exact governed shell CSS")

    def test_settings_carries_no_hand_chrome_palette(self):
        """The old hand-written dark chrome + copied verdict palette are GONE — the frame + verdict pills
        derive from the shell's tokens (var(--surface)/var(--hairline)/var(--status-*)), no raw chrome hex."""
        from scripts.rendering.settings.settings import render_settings
        html = render_settings()
        for banned in ("#0a0a0f", "#9a9aa6", "#23232e", "#12121a", "#c9c9d6", "#f2d06b", "#101018",
                       "#1a1a24", "#0f3d2e", "#55e0a8", "#1c6b4f", "#451118", "#ff8a9b", "#7a1f2b"):
            self.assertNotIn(banned, html, f"the hand chrome literal {banned} must be gone")
        for tok in ("var(--status-success)", "var(--status-danger)"):
            self.assertIn(tok, html, f"the verdict pills must derive from {tok}")

    def test_settings_breadcrumb_orients_across_the_surfaces(self):
        """Explainability/IA: the shell breadcrumb links the sibling surfaces so a viewer can navigate —
        settings previously carried NO nav at all, so this is the orientation fix."""
        from scripts.rendering.settings.settings import render_settings
        html = render_settings()
        self.assertRegex(html, r'class="ps-crumbs"')
        for href in ("index.html", "showcase.html", "studio.html"):
            self.assertIn(href, html, f"the settings page must link {href}")

    def test_settings_content_css_is_token_only_beyond_the_explicit_allowlist(self):
        """codex A3 #1: `_CONTENT_CSS` is page CONTENT (not host chrome), so the A1 shell gate never
        sees it — without its own scan it is a laundering hole for chrome-like decisions. Every
        colour is a var(); the ONLY bare literals are the module's DECLARED structural allowlist
        (layout px + layout keywords, no colour of any form)."""
        from scripts.rendering.settings.settings import (_CONTENT_ALLOWED_PX,
                                                         _CONTENT_ALLOWED_WORDS, _CONTENT_CSS)
        from scripts.rendering.webkit.design_render_adapter import content_offtokens
        self.assertEqual(
            content_offtokens(_CONTENT_CSS, _CONTENT_ALLOWED_PX, _CONTENT_ALLOWED_WORDS), [],
            "settings content CSS must be token-only beyond its declared structural allowlist")

    def test_content_scanner_catches_a_smuggled_decision(self):
        """Non-vacuity: a colour in ANY form (hex / colour fn / named / system) or an off-allowlist
        px pushed into `_CONTENT_CSS` is flagged — the allowlist is the only escape, and it admits
        no colour."""
        from scripts.rendering.settings.settings import (_CONTENT_ALLOWED_PX,
                                                         _CONTENT_ALLOWED_WORDS, _CONTENT_CSS)
        from scripts.rendering.webkit.design_render_adapter import content_offtokens
        target = "color: var(--accent);"
        self.assertIn(target, _CONTENT_CSS, "the mutation target must exist")
        for smuggle in ("color: #ff0000", "background: rgb(1,2,3)", "color: rebeccapurple",
                        "padding: 8px", "border-color: CanvasText", "color: initial"):
            css = _CONTENT_CSS.replace(target, smuggle + ";")
            self.assertTrue(
                content_offtokens(css, _CONTENT_ALLOWED_PX, _CONTENT_ALLOWED_WORDS),
                f"a smuggled {smuggle!r} must be flagged")

    def test_content_cannot_mint_or_override_tokens(self):
        """codex A3b #1: token DECLARATION belongs to the shell (`root_block`, provenance-pinned) —
        content may only REFERENCE vars. A `:root` block in content (which would OVERRIDE shell
        tokens, since content CSS loads after the shell's) or a custom-property declaration in any
        content rule is flagged — even a non-colour one (minting a token is itself the violation)."""
        from scripts.rendering.settings.settings import (_CONTENT_ALLOWED_PX,
                                                         _CONTENT_ALLOWED_WORDS, _CONTENT_CSS)
        from scripts.rendering.webkit.design_render_adapter import content_offtokens
        for mint in (":root { --evil: #ff0000; }\n" + _CONTENT_CSS,
                     _CONTENT_CSS + "\n.verdict { --backdrop: #ff0000; }",
                     _CONTENT_CSS + "\n.verdict { --pad: 31px; }"):
            self.assertTrue(
                content_offtokens(mint, _CONTENT_ALLOWED_PX, _CONTENT_ALLOWED_WORDS),
                "content minting/overriding a token must be flagged")

    def test_content_css_is_atrule_free(self):
        """codex A3c: an at-rule PRELUDE is CSS the body-scan never reads — `@media (min-width: 8px)`
        or `@supports (background: #ff0000)` would smuggle literals past the allowlist. Content CSS
        is therefore @-rule-free entirely (the same closed-structure law as the shell)."""
        from scripts.rendering.settings.settings import (_CONTENT_ALLOWED_PX,
                                                         _CONTENT_ALLOWED_WORDS, _CONTENT_CSS)
        from scripts.rendering.webkit.design_render_adapter import content_offtokens
        for atrule in ("@media (min-width: 8px) { .verdict { color: var(--ink); } }",
                       "@supports (background: #ff0000) { .verdict { color: var(--ink); } }"):
            self.assertTrue(
                content_offtokens(_CONTENT_CSS + "\n" + atrule,
                                  _CONTENT_ALLOWED_PX, _CONTENT_ALLOWED_WORDS),
                f"an at-rule ({atrule.split(' ')[0]}) in content CSS must be flagged")

    def test_content_allowlists_are_pinned_exactly(self):
        """codex A3b #2: the allowlist is the scan's ONLY escape, so it is DATA with a second key —
        widening it (e.g. adding a colour word like `blue`) reddens HERE until this pin is also
        edited, making every widening a visible, reviewed act. Neither set may ever name a colour."""
        from scripts.rendering.settings.settings import _CONTENT_ALLOWED_PX, _CONTENT_ALLOWED_WORDS
        self.assertEqual(_CONTENT_ALLOWED_PX, frozenset({"2px", "999px"}))
        self.assertEqual(_CONTENT_ALLOWED_WORDS,
                         frozenset({"ui-monospace", "monospace", "inline-block"}))


if __name__ == "__main__":
    unittest.main()

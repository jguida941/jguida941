"""P5-CHROME WS-A (authority: page_chrome) — the switchable governed page-shell.

The site that shows off design languages must ITSELF be a rendered instance of a governed design
language — not hand-written dark CSS. `render_page_shell(profile, ...)` builds the page CHROME (bg,
header, breadcrumb, section panels) token-only from `loader.resolve_tokens(profile)` + a documented
shell IA scale (`SHELL_SCALE`), so the frame around every specimen is itself governed and switchable.

The honest gate is **provenance + mutation, not merely "no hex"** (codex): every host-chrome value is
a `var(--role)`; the `:root` token vars equal `resolve_tokens(profile)` EXACTLY (no arbitrary hex
smuggled behind a token name) and the IA-scale vars equal `SHELL_SCALE`; and a moved token moves the
rendered chrome (so a hardcoded copy of a token value fails). Deterministic claims are `emitted`
(conform's `page-shell` aspect: backdrop-is-token / host-chrome-token-only / has-orientation); visual
hierarchy / no-camouflage / responsive stay `candidate` with a visual receipt. candidate_only.
"""
from __future__ import annotations

import copy
import re
import unittest


def _active():
    from scripts.rendering.design import loader
    return loader.load("_index")["active_design_profiles"]


def _strip_root_blocks(css: str) -> str:
    """Host chrome AFTER the declared `:root { … }` token blocks are removed — what remains must carry
    no design literal (every colour/space/size is a var())."""
    return re.sub(r':root(?:\[data-theme="[\w-]+"\])?\s*\{[^}]*\}', "", css)


def _shell(name: str, **kw):
    from scripts.rendering.pageshell.pageshell import render_page_shell
    args = dict(title="Governed surface", intro="Every part follows the process.",
                breadcrumbs=[("home", "index.html")], sections=[])
    args.update(kw)
    return render_page_shell(name, **args)


class PageShellTokenOnlyContract(unittest.TestCase):
    def test_render_page_shell_host_chrome_is_token_only(self):
        """After stripping the declared `:root` token blocks + the legit `var(--…)` refs, the host-chrome
        CSS has NO colour literal of ANY form (hex / rgb() / hsl() / named / currentColor) and no bare
        design px (only a 1px hairline width) — every decision is a var()."""
        for name in _active():
            _, css = _shell(name)
            scan = re.sub(r"var\(--[\w-]+\)", "", _strip_root_blocks(css))
            self.assertNotRegex(scan, r"#[0-9a-fA-F]{3,8}\b", f"{name}: no raw hex in host chrome")
            self.assertNotRegex(scan, r"\b(?:rgba?|hsla?|hwb|lab|lch|oklab|oklch|color)\s*\(",
                                f"{name}: no colour-function literal in host chrome")
            self.assertNotRegex(scan, r"\bcurrentColor\b", f"{name}: no currentColor in host chrome")
            self.assertNotRegex(scan, r"\b(?:black|white|red|green|blue|gray|grey|purple|orange|yellow"
                                      r"|teal|navy|silver|gold)\b", f"{name}: no named colour in host chrome")
            stray = [px for px in re.findall(r"(?<![\w.-])(\d+)px", scan) if px != "1"]
            self.assertEqual(stray, [], f"{name}: host-chrome spacing/size must be var(), not bare px: {stray}")

    def test_root_values_have_provenance_exactly(self):
        """The anti-vibe-code core (codex A1 #3): the `:root` var map is EXACTLY the profile's resolved
        tokens + `SHELL_SCALE` — no missing var, and NO EXTRA arbitrary var. So `--accent: #7dcfff`
        cannot be smuggled in through a token name; every var traces to a declared source."""
        from scripts.rendering.pageshell.pageshell import SHELL_SCALE
        from scripts.rendering import design_tokens as dt
        for name in _active():
            _, css = _shell(name)
            root_block = re.search(r":root\s*\{([^}]*)\}", css).group(1)
            root = dict(re.findall(r"(color-scheme|--[\w-]+):\s*([^;]+);", root_block))
            expected = dt.css_declarations(name)
            expected.update(SHELL_SCALE)
            self.assertEqual(root, expected,
                             f"{name}: :root must be EXACTLY resolve_tokens + SHELL_SCALE (no missing/extra var)")

    def test_shell_spacing_scale_is_on_the_4px_grid(self):
        """docs/design/pageshell.md §3: the shell SPACING constants are 4px multiples (the type ramp is
        exempt). Pins the doctrine claim so it can't drift off-grid (codex A1 #5)."""
        from scripts.rendering import design_tokens as dt
        from scripts.rendering.pageshell.pageshell import SHELL_SCALE
        for var in ("--ps-pad-tight", "--ps-gap", "--ps-gap-tight", "--ps-gap-section"):
            px = int(SHELL_SCALE[var].removesuffix("px"))
            self.assertEqual(px % 4, 0, f"{var}={px}px must be a 4px multiple")
        # D-SHELL: --ps-pad moved out of SHELL_SCALE — it is the profile's density band, still 4px-grid
        for name in _active():
            self.assertEqual(dt.density(name)["panel_pad"] % 4, 0,
                             f"{name}: density panel_pad must be a 4px multiple")

    def test_page_shell_has_orientation(self):
        """A user can figure out what the page is: the title + breadcrumb are present (the glossary
        lands in A6). Explainability is structural, not vibes."""
        for name in _active():
            html, _ = _shell(name, title="Design-language studio")
            self.assertIn("Design-language studio", html, f"{name}: the page title is present")
            self.assertRegex(html, r'class="ps-crumbs"', f"{name}: a breadcrumb/orientation row is present")
            self.assertIn("index.html", html, f"{name}: the breadcrumb links back")

    def test_page_background_is_the_language_backdrop(self):
        """The page IS the language: the shell root paints `var(--backdrop)` (== the profile's backdrop
        token), so switching language switches the whole page's ground."""
        from scripts.rendering.design import loader
        for name in _active():
            _, css = _shell(name)
            self.assertRegex(css, r"\.ps-[\w-]+\s*\{[^}]*background:\s*var\(--backdrop\)",
                             f"{name}: the shell root must paint var(--backdrop)")
            base = re.search(r":root\s*\{([^}]*)\}", css).group(1)
            root = dict(re.findall(r"(--[\w-]+):\s*([^;]+);", base))
            self.assertEqual(root.get("--backdrop"), loader.resolve_tokens(name)["color"]["backdrop"])


_GATE_HTML = ('<div class="ps-x"><h1 class="ps-title">T</h1>'
              '<p class="ps-crumbs"><a href="index.html">home</a></p></div>')
_GATE_CLEAN = (":root { --backdrop: #000; --accent: #fff; }\n"
               ".ps-x { background: var(--backdrop); color: var(--accent); padding: var(--ps-pad); }\n"
               ".ps-x .ps-panel { background: var(--surface); border: 1px solid var(--hairline); }")


class PageShellGateContract(unittest.TestCase):
    """The anti-vibe-code gate, pinned on CRAFTED inputs (codex A1b/A1c) — so every off-token colour/px
    form AND every exotic-selector spoof is caught durably in the suite, not just by ephemeral mutation.
    Token-only is decided per declaration VALUE (prop-independent); the chrome must be a CLOSED structure."""

    def _facts(self, css, html=_GATE_HTML):
        from scripts.rendering.webkit.design_render_adapter import pageshell_facts
        return pageshell_facts(html, css)

    def test_a_clean_shell_is_closed_token_only_and_backdrop(self):
        from scripts.contracts.design_predicates import (backdrop_is_token, host_chrome_is_closed,
                                                         host_chrome_token_only)
        f = self._facts(_GATE_CLEAN)
        self.assertTrue(host_chrome_is_closed(f), "a simple .ps-x structure is closed")
        self.assertTrue(host_chrome_token_only(f), "a var()-only shell is token-only")
        self.assertTrue(backdrop_is_token(f), "the shell root paints var(--backdrop)")

    def test_paint_containment_is_a_structural_token_only_value(self):
        from scripts.contracts.design_predicates import host_chrome_token_only

        css = _GATE_CLEAN.replace(
            "background: var(--surface);",
            "contain: paint; background: var(--surface);",
        )
        self.assertTrue(
            host_chrome_token_only(self._facts(css)),
            "contain: paint is structural and must not be mistaken for a design literal",
        )

    def test_every_off_token_colour_and_px_form_is_caught(self):
        """Prop-INDEPENDENT: a colour in ANY property (incl. an obscure one like stop-color) or hidden
        after a comment is caught, no property list (codex A1c #2/#3)."""
        from scripts.contracts.design_predicates import host_chrome_token_only
        vectors = {
            "hex": "color: #abcdef",
            "rgb()": "color: rgb(1,2,3)",
            "hsl()": "color: hsl(200, 50%, 50%)",
            "named": "color: rebeccapurple",
            "named-in-fallback": "color: var(--x, aliceblue)",
            "currentColor": "color: currentColor",
            "color-mix()": "background: color-mix(in srgb, var(--a), var(--b))",
            "var-fallback-hex": "color: var(--x, #fff)",
            "decimal-px": "padding: 1.5px",
            "negative-px": "margin: -8px",
            "uppercase-PX": "padding: 8PX",
            "obscure-colour-prop": "stop-color: red",
            "colour-after-a-comment": "color: var(--accent); /* ok */ border-color: teal",
            "initial": "color: initial",       # escapes the token system → browser default (codex A1d)
            "inherit": "color: inherit",
            "unset": "color: unset",
            "system-colour": "color: CanvasText",
        }
        for label, decl in vectors.items():
            css = _GATE_CLEAN.replace("color: var(--accent);", decl + ";")
            self.assertFalse(host_chrome_token_only(self._facts(css)),
                             f"vibe-coded {label} must redden the token-only gate")

    def test_named_colour_word_in_a_SELECTOR_is_not_a_false_positive(self):
        """The scan reads declaration VALUES, never selector text: a class named `.ps-red-team` (contains
        'red') is token-only + closed (codex A1b #4)."""
        from scripts.contracts.design_predicates import host_chrome_is_closed, host_chrome_token_only
        html = _GATE_HTML.replace("ps-x", "ps-red-team")
        css = _GATE_CLEAN.replace("ps-x", "ps-red-team")
        f = self._facts(css, html)
        self.assertTrue(host_chrome_token_only(f), "a colour word in a SELECTOR must not false-positive")
        self.assertTrue(host_chrome_is_closed(f), "the renamed shell is still closed")

    def test_closure_makes_specificity_atrule_and_attribute_spoofs_unconstructable(self):
        """codex A1c: rather than out-parse adversarial CSS, exotic selectors are UNCONSTRUCTABLE — a
        @media block, an attribute+specificity override of the root, a pseudo-class, or a child combinator
        all redden host_chrome_is_closed, so the backdrop/token-only checks never reason over trick CSS."""
        from scripts.contracts.design_predicates import host_chrome_is_closed
        for label, extra in {
            "@media": "@media (min-width: 0px) { .ps-x { background: var(--surface); } }",
            "attribute+specificity": '[class~="ps-x"].ps-x { background: var(--surface); }',
            "pseudo-class": ".ps-x:hover { background: var(--surface); }",
            "child-combinator": ".ps-x > .ps-panel { background: var(--surface); }",
        }.items():
            self.assertFalse(host_chrome_is_closed(self._facts(_GATE_CLEAN + "\n" + extra)),
                             f"{label} must redden host_chrome_is_closed (unconstructable chrome)")


class PageShellInjectionContract(unittest.TestCase):
    """codex A3 #2: `body_html`/section bodies are RAW page content injected inside the shell root.
    A shell-reserved `ps-*` class in that content could spoof the global-regex shell facts (a fake
    `ps-title` flips has_title), so the GENERATOR refuses it — the spoof is unconstructable,
    fail-closed at the seam, not detected downstream."""

    def _shell(self, **kw):
        from scripts.rendering.pageshell.pageshell import render_page_shell
        return render_page_shell("apple-dark", title="T", intro="i",
                                 breadcrumbs=[("home", "index.html")], **kw)

    def test_reserved_class_in_body_html_is_unconstructable(self):
        for spoof in ('<h1 class="ps-title">fake</h1>',
                      '<p class="ps-crumbs"><a href="x.html">fake</a></p>',
                      "<div class='ps-apple-dark'>nested shell root</div>"):
            with self.assertRaises(ValueError, msg=f"injected {spoof!r} must be refused"):
                self._shell(body_html=spoof)

    def test_reserved_class_in_a_section_body_is_unconstructable(self):
        with self.assertRaises(ValueError):
            self._shell(sections=[("h", '<span class="ps-title">fake</span>')])

    def test_prefix_html_renders_first_inside_the_shell_root(self):
        """P5-CHROME A5 seam: `prefix_html` is content a page needs as the FIRST children INSIDE the
        shell root (before ps-title) — the studio's pure-CSS switcher radios, whose `:checked ~`
        sibling selectors must reach the stages that follow. Placement is structural: root div,
        then prefix, then title."""
        html, _ = self._shell(prefix_html='<input type="radio" id="lang-x" class="lang-radio">')
        self.assertRegex(
            html, r'<div class="ps-apple-dark"[^>]*><div class="ps-main"[^>]*>'
                  r'<input type="radio" id="lang-x"[^>]*><h1 class="ps-title"[^>]*>',
            "prefix_html must render as the content column's first children, before ps-title")

    def test_reserved_class_in_prefix_html_is_unconstructable(self):
        """The ps-* injection guard covers prefix_html like body_html/sections — a prefix is the
        FIRST thing pageshell_facts' global regexes would meet, so a spoof there is the most
        dangerous of all."""
        with self.assertRaises(ValueError):
            self._shell(prefix_html='<h1 class="ps-title">fake</h1>')

    def test_legit_content_classes_render(self):
        """The guard bans only the shell's own `ps-*` anatomy — ordinary content classes (incl. a
        word that merely CONTAINS "ps-", like `caps-lock`) pass untouched."""
        html, _ = self._shell(
            body_html='<section class="lang"><div class="stage caps-lock">x</div></section>')
        self.assertIn('class="lang"', html)


class PageLayoutContract(unittest.TestCase):
    """P5 D-SHELL (design-audit #1/#6/#7): LAYOUT is a governed aspect, not vibe. The shell must
    (a) constrain ALL content to ONE centered page column (max-width = the cited 980px measure,
    auto-centered, fluid gutters — the index .wrap precedent, DESIGN_SPEC Part 6), (b) carry a real
    heading tier between title and body (title > h2 > body — the audit found body-sized section
    headers), and (c) consume the LANGUAGE'S OWN cited density band (apple-dark is 'airy'
    panel_pad 32 — THEME_IA, grounded in HIG Layout) instead of one minted constant."""

    def test_shell_renders_one_centered_content_column(self):
        for name in _active():
            html, css = _shell(name)
            self.assertIn('class="ps-main"', html, f"{name}: content must sit in the .ps-main column")
            self.assertRegex(
                css, r"\.ps-" + name + r"\s+\.ps-main\s*\{[^}]*max-width:\s*var\(--ps-measure-page\)",
                f"{name}: the column must be bound to the measure token")
            self.assertRegex(css, r"\.ps-main\s*\{[^}]*margin:\s*0\s+auto", f"{name}: centered")

    def test_layout_facts_are_gathered_fail_closed(self):
        from scripts.quality.design_invariants import _pageshell_facts
        for name in _active():
            f = _pageshell_facts(name)
            self.assertTrue(f.get("has_content_column"), f"{name}: has_content_column fact")
            self.assertTrue(f.get("type_ramp_tiered"), f"{name}: title > h2 > body tiering fact")
            self.assertTrue(f.get("pad_matches_density_band"),
                            f"{name}: --ps-pad must equal the language's declared density panel_pad")

    def test_a_columnnless_shell_reddens_fail_closed(self):
        """Crafted vector: shell CSS WITHOUT a .ps-main column (yesterday's sprawl) must fail the
        page_has_content_column predicate — the audit's #1 becomes unconstructable."""
        from scripts.contracts.design_predicates import page_has_content_column
        from scripts.rendering.webkit.design_render_adapter import pageshell_facts
        f = pageshell_facts(_GATE_HTML, _GATE_CLEAN)   # the A1 gate fixture has no column
        self.assertFalse(page_has_content_column(f), "a shell without the column must redden")

    def test_conform_emits_passing_ratified_page_aspect_rows(self):
        from scripts.quality.design_invariants import conform
        for name in _active():
            rows = {r["aspect"]: r for r in conform(name)
                    if r["aspect"] in {"page-layout", "page-type-ramp", "page-spacing-rhythm"}}
            self.assertEqual(set(rows), {"page-layout", "page-type-ramp", "page-spacing-rhythm"},
                             f"{name}: D-SHELL-1 emits the three ratified page aspects")
            for aspect, row in rows.items():
                self.assertEqual(row["status"], "pass", f"{name}: {aspect}/{row['invariant_id']} must pass")


class PageShellConformanceContract(unittest.TestCase):
    def test_conform_governs_the_page_shell_aspect(self):
        """The page shell is governed by the SAME conform() runner as the specimens: every active
        profile emits `page-shell` rows and each PASSES (deterministic) — the chrome is proven, not
        asserted."""
        from scripts.quality.design_invariants import conform
        for name in _active():
            ps = [r for r in conform(name) if r["aspect"] == "page-shell"]
            self.assertTrue(ps, f"{name}: conform() must include page-shell rows")
            for r in ps:
                self.assertEqual(r["status"], "pass",
                                 f"{name}: page-shell invariant {r['invariant_id']} must pass, got {r['status']}")


if __name__ == "__main__":
    unittest.main()

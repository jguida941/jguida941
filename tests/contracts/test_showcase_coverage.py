"""P5-SHOWCASE 1c (authority: showcase) — the conformance run RENDERED.

`render_showcase(receipts)` turns the committed conformance receipts into
`site/showcase.html`: for every active profile it renders the REAL webkit button AND a
per-invariant verdict whose value comes ONLY from the receipt JSON. A `candidate`
(judgment/deferred) row is stamped "cannot certify" — never a green pass (codex H4: NO
coupling to the nonexistent Playwright/PNG probe). Closed cover: rendered cells ==
receipt invariants, BOTH directions. Drift-guarded (committed bytes == regenerated).
candidate_only.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


def _repo_root() -> Path:
    for p in Path(__file__).resolve().parents:
        if (p / "scripts").is_dir() and (p / "site").is_dir():
            return p
    raise RuntimeError("repo root not found")


ROOT = _repo_root()
SHOWCASE = ROOT / "site" / "showcase.html"


def _active() -> list[str]:
    idx = json.loads((ROOT / "contracts" / "design_profiles" / "_index.json").read_text(encoding="utf-8"))
    return idx["active_design_profiles"]


def _committed_receipts() -> dict:
    out = {}
    for name in _active():
        p = ROOT / "assets" / "receipts" / name / "conformance_receipt.json"
        out[name] = json.loads(p.read_text(encoding="utf-8"))
    return out


class ShowcaseCoverageContract(unittest.TestCase):
    def test_showcase_is_generated_not_handwritten(self):
        """Drift guard (mirrors index.html): the committed bytes are EXACTLY what
        render_showcase(committed receipts) produces — a hand edit reddens; the page can
        only change by changing the generator + regenerating."""
        from scripts.rendering.showcase.showcase import render_showcase
        self.assertTrue(SHOWCASE.is_file(), "site/showcase.html must exist (generated + committed)")
        self.assertEqual(
            SHOWCASE.read_text(encoding="utf-8"), render_showcase(_committed_receipts()),
            "showcase drift — regenerate via scripts.rendering.showcase.showcase.write_showcase")

    def _cells_by_profile(self, html: str) -> dict:
        """Parse the rendered cells PER `<section data-profile>` as a list of (invariant, status)
        — scoped so a duplicate, a wrong-profile row, or a `data-invariant` outside the verdict
        table cannot be laundered by a global set (codex 1c #2)."""
        out = {}
        for prof, body in re.findall(
                r'<section class="lang"[^>]*data-profile="([^"]+)"[^>]*>(.*?)</section>', html, re.S):
            out.setdefault(prof, []).extend(
                re.findall(r'<tr data-invariant="([^"]+)" data-status="([^"]+)">', body))
        return out

    def test_rendered_cells_equal_receipt_invariants_per_profile_both_directions(self):
        """Closed cover, per profile, as a MULTISET: the (invariant, status) rows rendered in
        each profile's section equal that profile's receipt rows exactly — no duplicate, no
        fabricated cell, no missing cell, no row under the wrong profile."""
        from collections import Counter
        from scripts.rendering.showcase.showcase import render_showcase
        receipts = _committed_receipts()
        by_profile = self._cells_by_profile(render_showcase(receipts))
        self.assertEqual(set(by_profile), set(receipts), "a section per active profile, no more/less")
        for name, rc in receipts.items():
            rendered = Counter(by_profile[name])
            declared = Counter((r["invariant_id"], r["status"]) for r in rc["results"])
            self.assertTrue(declared, f"{name}: receipt must carry invariants")
            self.assertEqual(rendered, declared,
                             f"{name}: rendered cells must equal the receipt rows (multiset)")

    def test_every_active_profile_renders_a_real_button_no_placeholder(self):
        """The showcase requires the REAL webkit component for every active profile — a
        `.no-render` placeholder (the graceful fallback) must never appear for a shipped
        profile (codex 1c nice-to-have)."""
        from scripts.rendering.showcase.showcase import render_showcase
        html = render_showcase(_committed_receipts())
        self.assertNotIn("[[component-not-rendered]]", html,
                         "every active profile must render its real button (no placeholder)")
        for name in _active():
            self.assertIn(f'btn-{name}-', html, f"{name}: its rendered button class must be present")

    def test_candidate_cells_are_stamped_cannot_certify_never_a_pass(self):
        """R5 + codex H4: a judgment/deferred (`candidate`) cell shows "cannot certify" and
        NEVER a pass badge — the honest "automation cannot decide this" state."""
        from scripts.rendering.showcase.showcase import render_showcase
        synthetic = {"carbon": {"profile": "carbon", "results": [
            {"invariant_id": "syn-cand", "status": "candidate", "law": "L", "doc_cite": "d",
             "aspect": "component-button", "determinism": "judgment", "receipt_status": "pending",
             "receipt_obligation": {"required": True, "kind": "token-derived-reconstruction",
                                    "artifact": "assets/receipts/carbon/syn-cand.png"}}]}}
        html = render_showcase(synthetic)
        row = re.search(r'data-invariant="syn-cand".*?</tr>', html, re.S)
        self.assertIsNotNone(row, "the candidate invariant must render a row")
        self.assertIn("cannot certify", row.group(0).lower())
        self.assertNotIn("badge-pass", row.group(0), "a candidate must never show a pass badge")
        self.assertIn("pending", row.group(0), "a candidate must surface receipt status")
        self.assertIn("assets/receipts/carbon/syn-cand.png", row.group(0),
                      "a candidate must surface its required receipt artifact")

    def test_a_failing_receipt_cannot_be_forged_into_a_pass(self):
        """Anti-tautology / forge: a `fail` receipt renders a FAIL cell, not a pass — the
        showcase may ship a visibly-failing cell (the honest state), never a fake-green."""
        from scripts.rendering.showcase.showcase import render_showcase
        synthetic = {"carbon": {"profile": "carbon", "results": [
            {"invariant_id": "syn-fail", "status": "fail", "law": "L", "doc_cite": "d",
             "aspect": "component-button", "determinism": "deterministic"}]}}
        html = render_showcase(synthetic)
        self.assertIn('data-invariant="syn-fail" data-status="fail"', html)
        row = re.search(r'data-invariant="syn-fail".*?</tr>', html, re.S).group(0)
        self.assertNotIn("badge-pass", row, "a fail row must not carry a pass badge")


class ShowcaseChromeContract(unittest.TestCase):
    """P5-CHROME A3: the showcase CHROME is the governed page-shell (apple-dark house), not hand CSS.
    Its own frame is a rendered instance of a design language, and its verdict palette derives from the
    language's status tokens — so the proof page follows the same process it displays."""

    HOUSE = "apple-dark"

    def test_showcase_chrome_is_the_governed_page_shell(self):
        """The page frame is render_page_shell(apple-dark): the shell root class + its exact host-chrome
        CSS are present (so the showcase is drift-tied to the governed shell, not a hand copy)."""
        from scripts.rendering.pageshell.pageshell import shell_css
        from scripts.rendering.showcase.showcase import render_showcase
        html = render_showcase(_committed_receipts())
        self.assertIn(f'class="ps-{self.HOUSE}"', html, "showcase must frame itself in the governed shell")
        self.assertIn(shell_css(self.HOUSE), html, "showcase must embed the exact governed shell CSS")

    def test_showcase_carries_no_hand_chrome_palette(self):
        """The old hand-written dark chrome + copied verdict palette are GONE — the frame + badges derive
        from the shell's tokens (var(--surface)/var(--hairline)/var(--status-*)), no raw chrome hex."""
        from scripts.rendering.showcase.showcase import render_showcase
        html = render_showcase(_committed_receipts())
        for banned in ("#0a0a0f", "#101018", "#12121a", "#0f3d2e", "#451118", "#3a3410", "#1a1a24"):
            self.assertNotIn(banned, html, f"the hand chrome literal {banned} must be gone")
        for tok in ("var(--status-success)", "var(--status-danger)", "var(--status-warning)"):
            self.assertIn(tok, html, f"the verdict palette must derive from {tok}")

    def test_showcase_breadcrumb_orients_across_the_surfaces(self):
        """Explainability/IA: the shell breadcrumb links the sibling surfaces so a viewer can navigate."""
        from scripts.rendering.showcase.showcase import render_showcase
        html = render_showcase(_committed_receipts())
        self.assertRegex(html, r'class="ps-crumbs"')
        for href in ("index.html", "studio.html", "settings.html"):
            self.assertIn(href, html, f"the showcase must link {href}")

    def test_content_css_is_token_only_beyond_the_explicit_allowlist(self):
        """codex A3 #1: `_CONTENT_CSS` is page CONTENT (not host chrome), so the A1 shell gate never
        sees it — without its own scan it is a laundering hole for chrome-like decisions. Every
        colour is a var(); the ONLY bare literals are the module's DECLARED structural allowlist
        (layout px + layout keywords, no colour of any form). The per-language specimen CSS
        (`button_css`) is deliberately NOT scanned — specimens render in their OWN languages."""
        from scripts.rendering.showcase.showcase import (_CONTENT_ALLOWED_PX,
                                                         _CONTENT_ALLOWED_WORDS, _CONTENT_CSS)
        from scripts.rendering.webkit.design_render_adapter import content_offtokens
        self.assertEqual(
            content_offtokens(_CONTENT_CSS, _CONTENT_ALLOWED_PX, _CONTENT_ALLOWED_WORDS), [],
            "showcase content CSS must be token-only beyond its declared structural allowlist")

    def test_content_scanner_catches_a_smuggled_decision(self):
        """Non-vacuity: a colour in ANY form (hex / colour fn / named / system) or an off-allowlist
        px pushed into `_CONTENT_CSS` is flagged — the allowlist is the only escape, and it admits
        no colour."""
        from scripts.rendering.showcase.showcase import (_CONTENT_ALLOWED_PX,
                                                         _CONTENT_ALLOWED_WORDS, _CONTENT_CSS)
        from scripts.rendering.webkit.design_render_adapter import content_offtokens
        target = "color: var(--ink-dim); font-style: italic;"
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
        from scripts.rendering.showcase.showcase import (_CONTENT_ALLOWED_PX,
                                                         _CONTENT_ALLOWED_WORDS, _CONTENT_CSS)
        from scripts.rendering.webkit.design_render_adapter import content_offtokens
        for mint in (":root { --evil: #ff0000; }\n" + _CONTENT_CSS,
                     _CONTENT_CSS + "\n.badge { --backdrop: #ff0000; }",
                     _CONTENT_CSS + "\n.badge { --pad: 31px; }"):
            self.assertTrue(
                content_offtokens(mint, _CONTENT_ALLOWED_PX, _CONTENT_ALLOWED_WORDS),
                "content minting/overriding a token must be flagged")

    def test_content_css_is_atrule_free(self):
        """codex A3c: an at-rule PRELUDE is CSS the body-scan never reads — `@media (min-width: 8px)`
        or `@supports (background: #ff0000)` would smuggle literals past the allowlist. Content CSS
        is therefore @-rule-free entirely (the same closed-structure law as the shell); a genuine
        future need (responsive content) is a deliberate, reviewed widening — not a prelude escape."""
        from scripts.rendering.showcase.showcase import (_CONTENT_ALLOWED_PX,
                                                         _CONTENT_ALLOWED_WORDS, _CONTENT_CSS)
        from scripts.rendering.webkit.design_render_adapter import content_offtokens
        for atrule in ("@media (min-width: 8px) { .badge { color: var(--ink); } }",
                       "@supports (background: #ff0000) { .badge { color: var(--ink); } }"):
            self.assertTrue(
                content_offtokens(_CONTENT_CSS + "\n" + atrule,
                                  _CONTENT_ALLOWED_PX, _CONTENT_ALLOWED_WORDS),
                f"an at-rule ({atrule.split(' ')[0]}) in content CSS must be flagged")

    def test_verdict_table_is_grouped_by_aspect_with_hoisted_cites(self):
        """D-SHELL-2 L-SHOW-1: rows group into one tbody per aspect (first-appearance order) with
        a subheader th[scope=colgroup] carrying the group's SINGLE hoisted doc cite — the per-row
        doc column dies. Fail-closed: a missing aspect is a KeyError; mixed cites in a group raise."""
        from scripts.rendering.showcase.showcase import _rows, render_showcase
        html = render_showcase(_committed_receipts())
        self.assertRegex(html, r'<tbody class="aspect-group"[^>]*data-aspect="page-shell"[^>]*>')
        self.assertRegex(html, r'<tr class="aspect-head"[^>]*><th colspan="4" scope="colgroup">')
        self.assertNotIn("<th>doc</th>", html, "the per-row doc column must be gone")
        self.assertNotIn('<td class="cite">', html)
        base = {"invariant_id": "a", "status": "pass", "law": "l", "aspect": "s"}
        with self.assertRaises(ValueError):
            _rows([{**base, "doc_cite": "x"}, {**base, "invariant_id": "b", "doc_cite": "y"}])
        with self.assertRaises(KeyError):
            _rows([{"invariant_id": "a", "status": "pass", "law": "l", "doc_cite": "x"}])

    def test_pass_is_quiet_and_exceptions_are_loud(self):
        """D-SHELL-2 L-SHOW-2 (exception-first scanning): the pass pill is QUIET (transparent fill,
        status ink, 1px status border) while fail/candidate stay SOLID — two-directional, so a wall
        of loud greens can never drown the two rows that matter."""
        from scripts.rendering.showcase.showcase import _CONTENT_CSS
        pass_rule = re.search(r"\.badge-pass \{([^}]*)\}", _CONTENT_CSS).group(1)
        self.assertIn("background: transparent", pass_rule, "pass must be quiet")
        self.assertIn("color: var(--status-success)", pass_rule)
        for cls, tok in (("badge-fail", "--status-danger"), ("badge-candidate", "--status-warning")):
            rule = re.search(rf"\.{cls} \{{([^}}]*)\}}", _CONTENT_CSS).group(1)
            self.assertIn(f"background: var({tok})", rule, f"{cls} must stay loud/solid")

    def test_empty_receipt_cells_render_empty_not_dash(self):
        """D-SHELL-2 L-SHOW-5: an absent receipt is an EMPTY cell — a placeholder dash fakes
        content and made 90% of the column noise."""
        from scripts.rendering.showcase.showcase import render_showcase
        self.assertNotIn(">—<", render_showcase(_committed_receipts()))

    def test_content_allowlists_are_pinned_exactly(self):
        """codex A3b #2: the allowlist is the scan's ONLY escape, so it is DATA with a second key —
        widening it (e.g. adding a colour word like `blue`) reddens HERE until this pin is also
        edited, making every widening a visible, reviewed act. Neither set may ever name a colour."""
        from scripts.rendering.showcase.showcase import _CONTENT_ALLOWED_PX, _CONTENT_ALLOWED_WORDS
        self.assertEqual(_CONTENT_ALLOWED_PX, frozenset({"96px", "260px", "2px", "999px"}))
        self.assertEqual(_CONTENT_ALLOWED_WORDS,
                         frozenset({"column", "space-between", "inline-block",
                                    "ui-monospace", "monospace", "inherit"}))


if __name__ == "__main__":
    unittest.main()

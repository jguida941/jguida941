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
                r'<section class="lang" data-profile="([^"]+)">(.*?)</section>', html, re.S):
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


if __name__ == "__main__":
    unittest.main()

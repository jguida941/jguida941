"""1b (authority: conformance) — the conform() runner proof.

`conform(profile)` walks a profile's `invariants[]`, gathers verdict-free facts from the rendered
component (the adapter), dispatches each EMITTED+DETERMINISTIC row's `predicate_class` into the
closed predicate library, and DECIDES pass/fail. A DEFERRED/judgment row (contrast over glass)
becomes `candidate` — never a fabricated pass. This is the genericity proof (a surface can't be
half-shipped) + the honest-verdict proof + the RECEIPT seam. candidate_only.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path


def _repo_root() -> Path:
    for p in Path(__file__).resolve().parents:
        if (p / "scripts").is_dir() and (p / "tests").is_dir():
            return p
    raise RuntimeError("repo root not found")


ROOT = _repo_root()


def _active() -> list[str]:
    idx = json.loads((ROOT / "contracts" / "design_profiles" / "_index.json").read_text(encoding="utf-8"))
    return idx["active_design_profiles"]


class DesignConformanceContract(unittest.TestCase):
    def test_conform_stamps_every_component_pass_for_every_active_profile(self):
        """Every active profile's emitted deterministic invariants for EVERY component (button AND
        chip — codex chip #1) PASS against its own rendered component. A broken _COMPONENT_FACTS
        dispatch or adapter that emitted a chip `fail` reddens here, not just at receipt regen.
        Mutation-proof: flip a cited value in the profile and the corresponding result flips to fail."""
        from scripts.quality.design_invariants import conform
        for name in _active():
            emitted = [r for r in conform(name)
                       if r["determinism"] == "deterministic" and str(r["aspect"]).startswith("component-")]
            aspects = {r["aspect"] for r in emitted}
            self.assertIn("component-button", aspects, f"{name}: must have emitted button invariants")
            self.assertIn("component-chip", aspects, f"{name}: must have emitted chip invariants")
            self.assertIn("component-card", aspects, f"{name}: must have emitted card invariants")
            for r in emitted:
                self.assertEqual(r["status"], "pass",
                                 f"{name}/{r['invariant_id']} FAILED — evidence={r['evidence']}")

    def test_every_emitted_invariant_resolves_to_a_predicate_and_cites_a_doc(self):
        """Genericity (scout's generic-runner-over-data pattern): every EMITTED deterministic
        invariant's `predicate_class` resolves to a real predicate AND traces to a `doc_cite` — so a
        surface cannot be half-shipped (a declared invariant with no predicate or no cite reddens)."""
        from scripts.contracts.design_predicates import PREDICATES
        from scripts.rendering.design import loader
        for name in _active():
            for inv in loader.load(name).get("invariants", []):
                if inv["emission_status"] == "emitted" and inv["determinism"] == "deterministic":
                    self.assertIn(inv["predicate"]["predicate_class"], PREDICATES,
                                  f"{name}/{inv['invariant_id']}: predicate_class not in the library")
                    self.assertTrue(inv.get("doc_cite"), f"{name}/{inv['invariant_id']}: must cite a doc")

    def test_deferred_invariants_are_candidate_never_a_fabricated_pass(self):
        """The honest split (ACT/axe lineage): a judgment/deferred row (contrast over glass) is
        `candidate` — a review anchor, never pass/fail. No fake-green."""
        from scripts.quality.design_invariants import conform
        for name in _active():
            for r in conform(name):
                if r["determinism"] == "judgment":
                    self.assertEqual(r["status"], "candidate",
                                     f"{name}/{r['invariant_id']}: a judgment row must be candidate, not {r['status']}")
                    self.assertTrue(r.get("refute_by"), f"{name}/{r['invariant_id']}: candidate must say how to refute it")
                    obligation = r.get("receipt_obligation") or {}
                    self.assertIs(obligation.get("required"), True,
                                  f"{name}/{r['invariant_id']}: candidate must carry a required receipt obligation")
                    self.assertIn(obligation.get("kind"), {"headless-contrast-probe", "viewport-visual-receipt"},
                                  f"{name}/{r['invariant_id']}: receipt obligation must name the probe kind")
                    self.assertTrue(str(obligation.get("artifact", "")).startswith(f"assets/receipts/{name}/"),
                                    f"{name}/{r['invariant_id']}: receipt artifact must live in that profile's receipt home")
                    self.assertIn(r.get("receipt_status"), {"pending", "present"},
                                  f"{name}/{r['invariant_id']}: receipt status must be explicit")

    def test_profile_candidate_rows_have_structured_receipt_obligations(self):
        """P5-RECEIPT-GATE: visual/runtime rows are allowed to remain candidate, but not as loose
        prose. The profile row must declare a `receipt_obligation` and `refute_by` before the
        conformance receipt can serialize it."""
        from scripts.rendering.design import loader
        for name in _active():
            for inv in loader.load(name).get("invariants", []):
                if inv.get("determinism") == "judgment" or inv.get("emission_status") == "deferred":
                    self.assertTrue(inv.get("defer_reason"), f"{name}/{inv['invariant_id']}: missing defer_reason")
                    self.assertTrue(inv.get("refute_by"), f"{name}/{inv['invariant_id']}: missing refute_by")
                    obligation = inv.get("receipt_obligation") or {}
                    self.assertIs(obligation.get("required"), True,
                                  f"{name}/{inv['invariant_id']}: receipt_obligation.required must be true")
                    self.assertTrue(obligation.get("reason"), f"{name}/{inv['invariant_id']}: missing obligation reason")
                    self.assertTrue(str(obligation.get("artifact", "")).startswith(f"assets/receipts/{name}/"),
                                    f"{name}/{inv['invariant_id']}: artifact must stay under assets/receipts/{name}/")

    def test_committed_receipts_are_current_and_write_receipt_targets_the_governed_tree(self):
        """The RECEIPT seam: as of 1c EVERY active profile's receipt is a COMMITTED artifact the
        showcase reads. Drift guard via the PURE `receipt_json` (no disk write, so a drift never
        mutates the committed fixture — codex 1c #1); `write_receipt` is then exercised leak-safely
        (restored in `finally`) to prove it targets `assets/receipts/<profile>/` (receipts_layout)."""
        from scripts.quality.design_invariants import receipt_json, write_receipt
        for name in _active():
            committed = ROOT / "assets" / "receipts" / name / "conformance_receipt.json"
            self.assertTrue(committed.is_file(), f"{name}: committed receipt must exist")
            before = committed.read_text(encoding="utf-8")   # committed baseline
            expected = receipt_json(name)                    # PURE — no disk write
            data = json.loads(expected)
            self.assertEqual(data["authority_status"], "candidate_only")
            self.assertTrue(any(r["status"] == "pass" for r in data["results"]),
                            f"{name}: a real pass is recorded")
            self.assertEqual(before, expected,
                             f"{name}: receipt drift — regenerate via showcase.write_showcase")
            try:  # the disk seam writes to the governed tree; restore regardless (no leaked state)
                out = write_receipt(name)
                self.assertEqual(out, committed, "write_receipt writes to assets/receipts/<profile>/")
            finally:
                committed.write_text(before, encoding="utf-8")


class AdapterFailsClosed(unittest.TestCase):
    """codex 1b-ii fold: the GATHER seam must never manufacture a pass from missing/ambiguous CSS.
    Each test feeds the adapter a degenerate CSS and asserts the corresponding predicate FAILS."""

    def test_material_and_elevation_predicates_fail_closed_on_unparsable_css(self):
        """#1: with no parseable base rule, material/shadow facts are None (not False), so
        button_material_opaque / _glass / _zero_elevation cannot pass on empty CSS."""
        from scripts.contracts.design_predicates import (
            button_material_glass, button_material_opaque, button_zero_elevation)
        from scripts.rendering.webkit.design_render_adapter import button_facts
        facts = button_facts("", "")
        self.assertIsNone(facts["has_backdrop_filter"])
        self.assertIsNone(facts["has_box_shadow"])
        self.assertFalse(button_material_opaque(facts), "opaque must not pass on empty CSS")
        self.assertFalse(button_material_glass(facts), "glass must not pass on empty CSS")
        self.assertFalse(button_zero_elevation(facts), "flat must not pass on empty CSS")

    def test_anatomy_fails_closed_on_empty_render(self):
        """The anatomy gatherer must require POSITIVE DOM evidence (a rendered <button> / chip pill),
        not default from ABSENCE — else a component that renders NOTHING silently passes its anatomy
        invariant. This is the precondition for an honest reject-gate (P5-SETTINGS): `conform` must
        never pass a law on an empty render."""
        from scripts.contracts.design_predicates import button_anatomy
        from scripts.rendering.webkit.design_render_adapter import button_facts, chip_facts
        self.assertIsNone(button_facts("", "")["anatomy"], "no <button> DOM -> anatomy None")
        self.assertIsNone(chip_facts("", "")["anatomy"], "no chip DOM -> anatomy None")
        # codex: an EMPTY element (no text content) is not positive anatomy evidence either
        self.assertIsNone(button_facts("<button></button>", "")["anatomy"], "empty <button> -> None")
        self.assertIsNone(chip_facts('<span class="chip-x"></span>', "")["anatomy"], "empty chip span -> None")
        # codex (2nd pass): an empty-LABEL structured DOM is not evidence either
        self.assertIsNone(button_facts('<button><span class="btn-label"></span><svg class="btn-icon"></svg></button>', "")["anatomy"],
                          "empty-label Carbon button DOM -> None")
        self.assertIsNone(chip_facts('<span class="chip-x"><span class="chip-label"></span><button class="chip-dismiss">x</button></span>', "")["anatomy"],
                          "empty-label dismiss chip DOM -> None")
        self.assertFalse(button_anatomy(button_facts("", ""), expected="centered-capsule"),
                         "button anatomy must NOT pass on an empty render")
        self.assertFalse(button_anatomy(chip_facts("", ""), expected="centered-label"),
                         "chip anatomy must NOT pass on an empty render")

    def test_backdrop_filter_none_is_not_glass(self):
        """codex: `backdrop-filter: none` is NOT frosted glass — a substring check would fake-green
        `button_material_glass`. The gatherer requires a non-`none` value."""
        from scripts.contracts.design_predicates import button_material_glass
        from scripts.rendering.webkit.design_render_adapter import button_facts, chip_facts
        for facts in (button_facts("<button>x</button>", ".b { backdrop-filter: none; }"),
                      chip_facts('<span class="chip-x">x</span>', ".c { backdrop-filter: none; }"),
                      # codex (2nd pass): `none !important` must not read as present either
                      button_facts("<button>x</button>", ".b { backdrop-filter: none !important; }")):
            self.assertFalse(facts["has_backdrop_filter"], "backdrop-filter: none is not glass")
            self.assertFalse(button_material_glass(facts), "material_glass must not pass on `none`")

    def test_state_mechanic_is_mutually_exclusive_ambiguous_is_none(self):
        """#2: two press signals in one .is-active is ambiguous -> None -> the mechanic predicate
        fails for EVERY expected value (no priority-picked pass)."""
        from scripts.contracts.design_predicates import button_state_mechanic
        from scripts.rendering.webkit.design_render_adapter import button_facts
        css = ".btn-x { border-radius: 4px; }\n.btn-x.is-active { opacity: 0.5; background-color: #123456; }"
        facts = button_facts("<button></button>", css)
        self.assertIsNone(facts["state_mechanic"], "ambiguous mechanic must be None")
        for expected in ("token-swap", "opacity-dim", "glass-brightness"):
            self.assertFalse(button_state_mechanic(facts, expected=expected),
                             f"ambiguous mechanic must not pass as {expected}")

    def test_chip_sentence_case_and_material_flat_fail_closed_on_unparsable_css(self):
        """codex chip #2/#4: `chip_sentence_case` and `material_flat` must not pass on empty CSS —
        typography_case is None (not 'sentence') and the material facts are None (not False)."""
        from scripts.contracts.design_predicates import chip_sentence_case, material_flat
        from scripts.rendering.webkit.design_render_adapter import chip_facts
        facts = chip_facts("", "")
        self.assertIsNone(facts["typography_case"])
        self.assertFalse(chip_sentence_case(facts), "sentence-case must not pass on empty CSS")
        self.assertFalse(material_flat(facts), "material_flat must not pass on empty CSS")

    def test_square_2px_ring_requires_the_2px_inset_geometry(self):
        """#3: `square-2px-ring` keys on the 2px inset ring, not merely 'has an inset' — a mutated
        `inset 0 0 0 999px` is no longer a 2px square ring."""
        from scripts.contracts.design_predicates import button_focus_recipe
        from scripts.rendering.webkit.design_render_adapter import button_facts
        css = ".btn-x { border-radius: 0px; }\n.btn-x.is-focus { box-shadow: inset 0 0 0 999px #000; }"
        facts = button_facts("<button></button>", css)
        self.assertNotEqual(facts["focus_recipe"], "square-2px-ring")
        self.assertFalse(button_focus_recipe(facts, expected="square-2px-ring"),
                         "an oversized inset must not pass the 2px-square-ring invariant")

    def test_button_focus_recipe_is_mutually_exclusive_ambiguous_is_none(self):
        """The button focus gatherer must match the chip's discipline: if one focus rule contains
        two ring recipes, it is ambiguous -> None -> every focus predicate fails. No priority-pick."""
        from scripts.contracts.design_predicates import button_focus_recipe
        from scripts.rendering.webkit.design_render_adapter import button_facts
        css = (".btn-x { border-radius: 0px; }\n"
               ".btn-x.is-focus { box-shadow: inset 0 0 0 2px #000, 0 0 0 5px #0af; }")
        facts = button_facts("<button>x</button>", css)
        self.assertIsNone(facts["focus_recipe"], "ambiguous focus recipe must be None")
        for expected in ("square-2px-ring", "capsule-halo", "rounded-system-ring"):
            self.assertFalse(button_focus_recipe(facts, expected=expected),
                             f"ambiguous focus must not pass as {expected}")


class ReceiptClaimIsHonest(unittest.TestCase):
    def test_candidate_and_fail_rows_do_not_read_satisfies(self):
        """codex 1b-ii #4: a `candidate` (judgment/deferred) row must not claim 'satisfies'; a
        `fail` row must read 'VIOLATES'. Only a `pass` may say 'satisfies'."""
        from scripts.quality.design_invariants import _CLAIM, conform
        self.assertIn("candidate", _CLAIM["candidate"])
        self.assertIn("VIOLATES", _CLAIM["fail"])
        self.assertTrue(_CLAIM["pass"].startswith("satisfies"))
        for name in _active():
            for r in conform(name):
                if r["status"] != "pass":
                    self.assertNotIn("satisfies", r["claim"],
                                     f"{name}/{r['invariant_id']} ({r['status']}) must not claim 'satisfies'")


if __name__ == "__main__":
    unittest.main()

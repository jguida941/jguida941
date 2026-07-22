"""R-W3-RATCHET-1 contract (w3c-0 §13.2): the correction failure-ratchet.

Hostile RED for ``scripts/organization/correction_ratchet.py``. Strengthened
across three Codex CODE+ADVERSARIAL rounds. This round closes the r2 findings:

  * TRUSTED RUNNER — ``run_and_verify`` RUNS the pinned command, validates the
    run is honest (``Ran N>0``, terminal status, return-code agreement, module
    DISCOVERY, fully-qualified identities), loads the PARENT via ``git show``, and
    invokes projection+subset+frozen INSEPARABLY. A ``Ran 0``/deleted-tests/
    unmask-to-zero run is REJECTED, not accepted as progress.
  * SEVEN-ID ATOMIC EXTRACTOR — the structural ids' fingerprints are the sorted
    set of atomic ``category|side|member`` violations recomputed from the live
    collections; a member add/remove flips exactly one atom.
  * FULLY-QUALIFIED loader keys — a ``_FailedTest`` for
    ``tests.contracts.definitely_missing`` keys as the dotted module.
  * TOTALS — ``unique_test_ids`` is ``rows + loader + setupclass`` (16 for the
    seed), exercised WITH a non-empty setUpClass mask.

Because the on-disk seed committed at slice 0 is a slice-0 SEED (bare loader
keys, ``seed-terminal-line`` fingerprints, the six-key seed totals vocabulary
carrying ``observed_identities`` rather than ``unique_test_ids``, and an extra
``ratchet_status`` annotation) that ``regenerate_canonical_seed`` turns into the
canonical shape at slice-1 landing — a one-way bootstrap, with a seed refused as
a ratchet parent until then — the behaviour tests bind a CANONICAL in-memory
ledger built to the §13.2 shape rather than the stale bytes; the seed file itself
gets a load/parse smoke plus the seed-shape and docstring-honesty checks.
"""

import copy
import io
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import scripts.organization.correction_ratchet as cr
from scripts.organization.correction_ratchet import (  # RED: module must satisfy this API
    STRUCTURAL_EXTRACTOR_IDS,
    ExtractorUnavailable,
    RatchetRunError,
    RatchetViolation,
    RunResult,
    failure_units,
    load_ledger,
    observe_from_unittest_output,
    run_and_verify,
    structural_atoms,
    symmetric_atoms,
    verify_frozen_structure,
    verify_observation_projection,
    verify_subset_of_parent,
)

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "contracts" / "correction_baseline.json"

LEDGER_KEYS = {"contract_id", "schema_version", "purpose", "observed_utc", "command",
               "measurement_context", "totals", "setupclass_masks", "loader_masks", "failing"}
FAILING_ROW_KEYS = {"id", "kind", "fingerprint_mode", "subtest_vectors", "fingerprints"}
LOADER_MASK_KEYS = {"module", "fingerprint", "unmask_rule"}

_SL = "tests.contracts.test_structural_layout.StructuralLayoutContract"
_TL = "tests.contracts.test_tests_layout_contract.TestsLayoutContract"

NINE_LOADER_MODULES = (
    "tests.contracts.test_page_archetype",
    "tests.contracts.test_design_source_provenance",
    "tests.contracts.test_official_source_parity",
    "tests.contracts.test_reference_pack",
    "tests.contracts.test_dashboard_visual_authority",
    "tests.contracts.test_rendered_facts",
    "tests.contracts.test_rendered_fact_adversarial",
    "tests.contracts.test_rendered_fact_density_adversarial",
    "tests.contracts.test_rendered_fact_paint_adversarial",
)
UNMASK_RULE = (
    "when this module becomes importable its loader mask MUST be removed in that "
    "same slice; discovery MUST yield at least the slice's bound RED test and every "
    "discovered test executes; any failure/error/setUpClass error/new fingerprint "
    "must already be in the ordinary ledger; importable-with-zero-tests, a stale "
    "mask, a changed loader fingerprint, or an unmasked red test all redden"
)

# The seven structural rows, each with a VALID atomic-member fingerprint (the
# exact value is immaterial — projection matches the ledger against itself).
_SEVEN_ROWS = (
    (f"{_SL}::test_declared_homes_have_no_phantom_members",
     ["source_layout|phantom|contracts/rendered/interaction.py"]),
    (f"{_SL}::test_every_src_module_has_a_declared_home",
     ["source_layout|missing|contracts/rendered/interaction.py"]),
    (f"{_SL}::test_every_test_file_has_a_declared_home",
     ["test_layout|missing|contracts/test_reference_pack.py"]),
    (f"{_SL}::test_guard_fires_on_a_forged_or_misplaced_file",
     ["source_layout|missing|contracts/rendered/interaction.py"]),
    (f"{_SL}::test_placement_enforced_groups_live_in_their_subdir",
     ["source_layout|misplaced|interaction.py"]),
    (f"{_TL}::test_declared_modules_exist",
     ["tests_module_home|missing|tests/contracts/test_reference_pack.py"]),
    (f"{_TL}::test_design_contracts_grouped_by_authority",
     ["authority_axis|stale|test_reference_pack.py"]),
)


def _canonical_ledger():
    """A §13.2-shaped ledger: 7 ordinary structural rows + 9 FQ loader masks +
    0 setUpClass masks, ``unique_test_ids = 16``, atomic-member fingerprints."""
    command = load_ledger(LEDGER)["command"]  # reuse the real pinned 17-module command
    failing = [
        {"id": tid, "kind": "failure", "fingerprint_mode": "atomic-members",
         "subtest_vectors": 0, "fingerprints": list(fps)}
        for tid, fps in _SEVEN_ROWS
    ]
    loader_masks = [
        {"module": m, "fingerprint": f"ModuleNotFoundError: No module named '{m}'",
         "unmask_rule": UNMASK_RULE}
        for m in NINE_LOADER_MODULES
    ]
    led = {
        "contract_id": "CorrectionFailureBaseline",
        "schema_version": 1,
        "purpose": "R-W3-RATCHET-1 canonical fixture (§13.2 shape).",
        "observed_utc": "2026-07-15",
        "command": command,
        "measurement_context": "clean worktree of the branch tip with ONLY the slice final patch applied",
        "totals": {"failures": 0, "errors": 0, "unique_test_ids": 0},
        "setupclass_masks": [],
        "loader_masks": loader_masks,
        "failing": failing,
    }
    led["totals"] = cr._derived_totals(led)  # {7, 9, 16}
    return led


def _obs(led):
    return {
        "ordinary": {(r["id"], fp) for r in led["failing"] for fp in r["fingerprints"]},
        "loader": {(m["module"], m["fingerprint"], m["unmask_rule"]) for m in led["loader_masks"]},
        "setupclass": {(m["class"], m["fingerprint"], m["unmask_rule"]) for m in led["setupclass_masks"]},
    }


def _real_unittest_output(cases=(), names=()):
    """REAL ``python -m unittest -v`` output (produced by unittest, not hand
    forged) for the given TestCase classes and loader names."""
    suite = unittest.TestSuite()
    loader = unittest.defaultTestLoader
    for case in cases:
        suite.addTests(loader.loadTestsFromTestCase(case))
    for name in names:
        suite.addTests(loader.loadTestsFromName(name))
    stream = io.StringIO()
    unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    return stream.getvalue()


def _synth_run(led, *, status="FAILED", ran=75, rc=1, failures=7, errors=9, drop_modules=()):
    """Synthesize a realistic ``-v`` run for ``led`` as a :class:`RunResult`:
    a green smoke line per executing module, a FAIL block per ordinary row, an
    ``_FailedTest`` ERROR block per loader mask, and the ``Ran/OK|FAILED`` tail."""
    named = cr._command_modules(led["command"])
    masked = {m["module"] for m in led["loader_masks"]}
    drop = set(drop_modules)
    executing = [m for m in named if m not in masked and m not in drop]

    verbose, details = [], []
    for mod in executing:
        verbose.append(f"test_smoke ({mod}.Smoke) ... ok")
    for row in led["failing"]:
        cp, method = row["id"].split("::")
        verbose.append(f"{method} ({cp}) ... FAIL")
        details += [
            "======================================================================",
            f"FAIL: {method} ({cp})",
            "----------------------------------------------------------------------",
            "Traceback (most recent call last):",
            f'  File "x.py", line 1, in {method}',
            f"AssertionError: aggregate terminal line for {method}",
            "",
        ]
    for mask in led["loader_masks"]:
        fq = mask["module"]
        base = fq.rsplit(".", 1)[-1]
        verbose.append(f"{base} (unittest.loader._FailedTest) ... ERROR")
        details += [
            "======================================================================",
            f"ERROR: {base} (unittest.loader._FailedTest)",
            "----------------------------------------------------------------------",
            f"ImportError: Failed to import test module: {fq}",
            "Traceback (most recent call last):",
            '  File "loader.py", line 154, in loadTestsFromName',
            "    module = __import__(module_name)",
            mask["fingerprint"],
            "",
        ]
    tail = [
        "----------------------------------------------------------------------",
        f"Ran {ran} tests in 0.010s",
        "",
        f"FAILED (failures={failures}, errors={errors})" if status == "FAILED" else "OK",
    ]
    output = "\n".join(verbose + [""] + details + tail) + "\n"
    return RunResult(output=output, returncode=rc)


# --------------------------------------------------------------------------- #
# Schema / loading
# --------------------------------------------------------------------------- #

class RatchetSchema(unittest.TestCase):
    def test_canonical_shape_is_closed(self):
        led = _canonical_ledger()
        self.assertEqual(led["contract_id"], "CorrectionFailureBaseline")
        self.assertEqual(set(led), LEDGER_KEYS)
        for row in led["failing"]:
            self.assertEqual(set(row), FAILING_ROW_KEYS)
        for mask in led["loader_masks"]:
            self.assertEqual(set(mask), LOADER_MASK_KEYS)

    def test_totals_unique_ids_count_rows_plus_masks(self):
        """§13.2: unique_test_ids = ordinary rows + loader masks + setUpClass masks
        (16 = 7 + 9 + 0), NOT len(failing)."""
        led = _canonical_ledger()
        self.assertEqual(led["totals"], {"failures": 7, "errors": 9, "unique_test_ids": 16})
        self.assertEqual(led["totals"]["unique_test_ids"],
                         len(led["failing"]) + len(led["loader_masks"]) + len(led["setupclass_masks"]))

    def test_totals_are_derived_incl_setupclass_nonempty(self):
        """The setUpClass mask MUST count toward errors AND unique_test_ids — with
        a NON-empty setUpClass list (the r2 vacuity finding)."""
        led = _canonical_ledger()
        led["setupclass_masks"] = [{
            "class": "tests.contracts.test_rendered_facts.RenderedFactsBehavior",
            "fingerprint": "RuntimeError: rendered facts input hashes are stale or mismatched",
            "unmask_rule": UNMASK_RULE,
        }]
        derived = cr._derived_totals(led)
        self.assertEqual(derived["errors"], 10)           # 0 error rows + 9 loader + 1 setupclass
        self.assertEqual(derived["unique_test_ids"], 17)  # 7 + 9 + 1
        # and frozen-structure recomputes it: a forged unique count reddens
        led["totals"] = derived
        parent = copy.deepcopy(led)
        self.assertEqual(verify_frozen_structure(led, parent), "frozen")
        bad = copy.deepcopy(led)
        bad["totals"]["unique_test_ids"] = 16
        with self.assertRaises(RatchetViolation):
            verify_frozen_structure(bad, parent)

    def test_load_ledger_rejects_duplicate_json_keys(self):
        with self.assertRaises(RatchetViolation):
            cr._loads_no_dupes('{"a": 1, "a": 2}')          # flat duplicate
        with self.assertRaises(RatchetViolation):
            cr._loads_no_dupes('{"x": {"b": 1, "b": 2}}')   # nested duplicate

    def test_seed_file_loads_and_carries_required_keys(self):
        """The on-disk slice-0 seed parses (dup-key-safe) and carries the required
        keys. It is deliberately NOT bound to the §13.2-corrected shape here — it
        is a known-stale seed the conductor regenerates at slice-1 using the parser
        + extractor in this module (see the module docstring)."""
        led = load_ledger(LEDGER)
        self.assertEqual(led["contract_id"], "CorrectionFailureBaseline")
        self.assertTrue(LEDGER_KEYS <= set(led))


# --------------------------------------------------------------------------- #
# Failure units
# --------------------------------------------------------------------------- #

class RatchetFailureUnits(unittest.TestCase):
    def test_mask_identity_includes_unmask_rule(self):
        led = _canonical_ledger()
        units = failure_units(led)
        for m in led["loader_masks"]:
            self.assertIn(("loader", m["module"], m["fingerprint"], m["unmask_rule"]), units)
        for r in led["failing"]:
            for fp in r["fingerprints"]:
                self.assertIn(("ordinary", r["id"], fp), units)


# --------------------------------------------------------------------------- #
# Atomic-member extractor (the closed seven-id map)
# --------------------------------------------------------------------------- #

class RatchetAtomicExtractor(unittest.TestCase):
    def test_map_covers_exactly_the_seven_seed_ids(self):
        seed_ids = {r["id"] for r in load_ledger(LEDGER)["failing"]}
        self.assertEqual(set(STRUCTURAL_EXTRACTOR_IDS), seed_ids)
        self.assertEqual(len(STRUCTURAL_EXTRACTOR_IDS), 7)

    def test_atoms_are_member_atoms_not_terminal_lines(self):
        for tid in STRUCTURAL_EXTRACTOR_IDS:
            atoms = structural_atoms(tid)          # live recompute
            self.assertIsInstance(atoms, set)
            for atom in atoms:
                self.assertGreaterEqual(atom.count("|"), 2)      # category|side|member
                self.assertNotIn("Traceback", atom)
                self.assertNotIn("AssertionError", atom)
                self.assertNotIn("Set self.maxDiff", atom)
        self.assertIsNone(structural_atoms("not.a.mapped.Case::test_x"))

    def test_member_add_removes_change_the_fingerprint_set(self):
        base = symmetric_atoms("source_layout", "missing", {"a.py", "b.py"}, "undeclared", set())
        added = symmetric_atoms("source_layout", "missing", {"a.py", "b.py", "c.py"}, "undeclared", set())
        removed = symmetric_atoms("source_layout", "missing", {"a.py"}, "undeclared", set())
        self.assertEqual(added - base, {"source_layout|missing|c.py"})
        self.assertEqual(base - removed, {"source_layout|missing|b.py"})
        self.assertNotEqual(added, base)
        self.assertNotEqual(removed, base)

    def test_both_drift_directions_are_atoms(self):
        atoms = symmetric_atoms("source_layout", "missing", {"declared.py"}, "undeclared", {"ondisk.py"})
        self.assertEqual(atoms, {"source_layout|missing|declared.py", "source_layout|undeclared|ondisk.py"})


# --------------------------------------------------------------------------- #
# Observation parsing (real unittest output, not hand-forged)
# --------------------------------------------------------------------------- #

class RatchetObservationParsing(unittest.TestCase):
    def test_ordinary_fail_and_error_and_setupclass_from_real_output(self):
        class F(unittest.TestCase):
            def test_fail(self):
                self.fail("ordinary fail")

        class E(unittest.TestCase):
            def test_error(self):
                raise ValueError("ordinary error")

        class S(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                raise RuntimeError("setup boom")

            def test_hidden(self):
                pass

        obs = observe_from_unittest_output(_real_unittest_output(cases=(F, E, S)))
        # locally-defined cases carry a <locals>-qualified class path; match the tail.
        ordinary = obs["ordinary"]
        self.assertTrue(any(i.endswith(".F::test_fail") and f == "AssertionError: ordinary fail"
                            for i, f in ordinary), ordinary)
        self.assertTrue(any(i.endswith(".E::test_error") and f == "ValueError: ordinary error"
                            for i, f in ordinary), ordinary)
        self.assertTrue(any(c.endswith(".S") and f == "RuntimeError: setup boom"
                            for c, f in obs["setupclass"]), obs["setupclass"])

    def test_failed_test_keys_fully_qualified_module(self):
        """A ``_FailedTest`` for tests.contracts.definitely_missing keys as the
        DOTTED module, not the bare basename (the r2 basename finding)."""
        out = _real_unittest_output(names=("tests.contracts.definitely_missing_module",))
        obs = observe_from_unittest_output(out)
        self.assertTrue(obs["loader"], "expected a loader observation")
        modules = {m for m, _fp in obs["loader"]}
        self.assertIn("tests.contracts.definitely_missing_module", modules)
        self.assertNotIn("definitely_missing_module", modules)  # bare basename rejected

    def test_py311_paren_method_form(self):
        obs = observe_from_unittest_output("FAIL: test_x (pkg.mod.Case.test_x)\nAssertionError: py311\n")
        self.assertIn(("pkg.mod.Case::test_x", "AssertionError: py311"), obs["ordinary"])


# --------------------------------------------------------------------------- #
# Observation projection (pure)
# --------------------------------------------------------------------------- #

class RatchetObservationProjection(unittest.TestCase):
    def test_matching_observation_passes(self):
        led = _canonical_ledger()
        verify_observation_projection(led, _obs(led))

    def test_new_pair_reddens(self):
        led = _canonical_ledger()
        o = _obs(led)
        o["ordinary"] = o["ordinary"] | {("t::x", "AssertionError: boom")}
        with self.assertRaises(RatchetViolation):
            verify_observation_projection(led, o)

    def test_missing_pair_reddens(self):
        led = _canonical_ledger()
        with self.assertRaises(RatchetViolation):
            verify_observation_projection(led, {"ordinary": set(), "loader": set(), "setupclass": set()})


# --------------------------------------------------------------------------- #
# Subset law (pure)
# --------------------------------------------------------------------------- #

class RatchetSubset(unittest.TestCase):
    def test_identical_unchanged(self):
        led = _canonical_ledger()
        self.assertEqual(verify_subset_of_parent(led, led), "unchanged")

    def test_strict_subset_shrunk(self):
        led = _canonical_ledger()
        child = copy.deepcopy(led)
        child["failing"] = child["failing"][:-1]
        child["totals"] = cr._derived_totals(child)
        self.assertEqual(verify_subset_of_parent(child, led), "shrunk")

    def test_added_unit_reddens(self):
        led = _canonical_ledger()
        child = copy.deepcopy(led)
        child["failing"].append({"id": "x::y", "kind": "failure", "fingerprint_mode": "atomic-members",
                                 "subtest_vectors": 0, "fingerprints": ["AssertionError: new"]})
        with self.assertRaises(RatchetViolation):
            verify_subset_of_parent(child, led)

    def test_unmask_rule_edit_reddens(self):
        led = _canonical_ledger()
        child = copy.deepcopy(led)
        child["loader_masks"][0]["unmask_rule"] = "weakened"
        with self.assertRaises(RatchetViolation):
            verify_subset_of_parent(child, led)


# --------------------------------------------------------------------------- #
# Frozen structure (pure)
# --------------------------------------------------------------------------- #

class RatchetFrozenStructure(unittest.TestCase):
    def setUp(self):
        self.parent = _canonical_ledger()

    def _child(self):
        return copy.deepcopy(self.parent)

    def test_clean_shrink_is_frozen(self):
        self.assertEqual(verify_frozen_structure(self.parent, self.parent), "frozen")

    def test_command_change_reddens(self):
        c = self._child(); c["command"] += " --x"
        with self.assertRaises(RatchetViolation):
            verify_frozen_structure(c, self.parent)

    def test_measurement_context_edit_reddens(self):
        c = self._child(); c["measurement_context"] += " tampered"
        with self.assertRaises(RatchetViolation):
            verify_frozen_structure(c, self.parent)

    def test_subtest_vectors_increase_reddens(self):
        c = self._child(); c["failing"][0]["subtest_vectors"] += 1
        with self.assertRaises(RatchetViolation):
            verify_frozen_structure(c, self.parent)

    def test_row_kind_change_reddens(self):
        c = self._child(); c["failing"][0]["kind"] = "error"
        with self.assertRaises(RatchetViolation):
            verify_frozen_structure(c, self.parent)

    def test_duplicate_failing_id_reddens(self):
        c = self._child(); c["failing"].append(copy.deepcopy(c["failing"][0]))
        with self.assertRaises(RatchetViolation):
            verify_frozen_structure(c, self.parent)

    def test_duplicate_mask_reddens(self):
        c = self._child(); c["loader_masks"].append(copy.deepcopy(c["loader_masks"][0]))
        with self.assertRaises(RatchetViolation):
            verify_frozen_structure(c, self.parent)

    def test_empty_row_reddens(self):
        c = self._child(); c["failing"][0]["fingerprints"] = []
        with self.assertRaises(RatchetViolation):
            verify_frozen_structure(c, self.parent)

    def test_row_level_extra_key_reddens(self):
        c = self._child(); c["failing"][0]["sneaky"] = True
        with self.assertRaises(RatchetViolation):
            verify_frozen_structure(c, self.parent)

    def test_top_level_added_key_reddens(self):
        c = self._child(); c["extra"] = 1
        with self.assertRaises(RatchetViolation):
            verify_frozen_structure(c, self.parent)

    def test_totals_unique_ids_forged_reddens(self):
        c = self._child(); c["totals"]["unique_test_ids"] += 99
        with self.assertRaises(RatchetViolation):
            verify_frozen_structure(c, self.parent)

    def test_added_failing_row_reddens(self):
        c = self._child()
        c["failing"].append({"id": "n::m", "kind": "failure", "fingerprint_mode": "atomic-members",
                             "subtest_vectors": 0, "fingerprints": ["source_layout|missing|z.py"]})
        c["totals"] = cr._derived_totals(c)
        with self.assertRaises(RatchetViolation):
            verify_frozen_structure(c, self.parent)


# --------------------------------------------------------------------------- #
# Trusted runner (hermetic — injected subprocess / git / extractor)
# --------------------------------------------------------------------------- #

class RatchetTrustedRunner(unittest.TestCase):
    def setUp(self):
        self.led = _canonical_ledger()
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        (self.dir / "contracts").mkdir()
        self.path = self.dir / "contracts" / "correction_baseline.json"
        self.path.write_text(json.dumps(self.led), encoding="utf-8")
        # inject an extractor that returns each structural row's own atoms, so the
        # observed set (post-rewrite) is the exact image of the canonical ledger.
        self.atoms = {r["id"]: set(r["fingerprints"]) for r in self.led["failing"]}
        self.extractor = lambda tid: self.atoms.get(tid)
        self.git_ok = lambda ref, rel: json.dumps(self.led)

    def _run(self, runresult, **kw):
        # Hermetic seams live on the module-private _run_and_verify_with; the public
        # run_and_verify exposes no injection parameters (finding #2).
        return cr._run_and_verify_with(
            self.path, base_ref="HEAD",
            subprocess_runner=lambda cmd: runresult,
            git_show=kw.pop("git_show", self.git_ok),
            atomic_extractor=kw.pop("atomic_extractor", self.extractor),
        )

    # -- happy paths --------------------------------------------------------- #

    def test_honest_unchanged_run_passes(self):
        result = self._run(_synth_run(self.led))
        self.assertEqual(result["ledger_change"], "unchanged")
        self.assertEqual(result["frozen"], "frozen")
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(len(result["modules"]), 17)

    def test_honest_strict_shrink_classifies_shrunk(self):
        parent = copy.deepcopy(self.led)
        parent["failing"].append({"id": "tests.contracts.test_extra.C::t", "kind": "failure",
                                  "fingerprint_mode": "atomic-members", "subtest_vectors": 0,
                                  "fingerprints": ["source_layout|missing|extra.py"]})
        parent["totals"] = cr._derived_totals(parent)
        result = self._run(_synth_run(self.led), git_show=lambda ref, rel: json.dumps(parent))
        self.assertEqual(result["ledger_change"], "shrunk")

    def test_trusted_path_classifies_shrink_via_subset_call(self):
        """FINDING #6 isolation RED (kills neutralising the runner's
        verify_subset_of_parent call). The subset call is load-bearing THROUGH its
        classification return value — which frozen structure does not provide:
        identical -> 'unchanged', a strict subset -> 'shrunk'. Neutralising the
        call flips one of these, so this RED reddens on that mutant."""
        self.assertEqual(self._run(_synth_run(self.led))["ledger_change"], "unchanged")
        parent = copy.deepcopy(self.led)
        parent["failing"].append({"id": "tests.contracts.test_extra.C::t", "kind": "failure",
                                  "fingerprint_mode": "atomic-members", "subtest_vectors": 0,
                                  "fingerprints": ["source_layout|missing|extra.py"]})
        parent["totals"] = cr._derived_totals(parent)
        result = self._run(_synth_run(self.led), git_show=lambda ref, rel: json.dumps(parent))
        self.assertEqual(result["ledger_change"], "shrunk")

    # -- dishonest RUN vectors ---------------------------------------------- #

    def test_check_run_isolates_zero_and_undiscovered(self):
        """Directly isolate the run-honesty guard from the downstream projection:
        Ran 0 and an undiscovered (neither-executed-nor-masked) module both raise
        inside _check_run itself."""
        empty = {"ordinary": set(), "loader": set(), "setupclass": set()}
        with self.assertRaises(RatchetRunError):
            cr._check_run("Ran 0 tests in 0.0s\n\nOK\n", 0, ["tests.contracts.test_a"], empty)
        with self.assertRaises(RatchetRunError):
            cr._check_run("test_x (tests.contracts.test_b.C) ... ok\n\nRan 1 test in 0.0s\n\nOK\n",
                          0, ["tests.contracts.test_a"], empty)

    def test_zero_test_run_rejected(self):
        zero = RunResult(output="\n----------------------------------------------------------------------\n"
                                "Ran 0 tests in 0.000s\n\nOK\n", returncode=0)
        with self.assertRaises(RatchetViolation):
            self._run(zero)

    def test_deleted_tests_undiscovered_module_rejected(self):
        # drop a green module's only evidence: it is neither executed nor masked
        run = _synth_run(self.led, drop_modules=("tests.contracts.test_bootstrap_red_ref",))
        with self.assertRaises(RatchetViolation):
            self._run(run)

    def test_missing_ran_summary_rejected(self):
        run = RunResult(output="test_x (a.b.C) ... ok\n\nOK\n", returncode=0)
        with self.assertRaises(RatchetViolation):
            self._run(run)

    def test_missing_terminal_status_rejected(self):
        run = RunResult(output="test_x (a.b.C) ... ok\nRan 5 tests in 0.001s\n", returncode=0)
        with self.assertRaises(RatchetViolation):
            self._run(run)

    def test_returncode_disagrees_with_failed_status_rejected(self):
        with self.assertRaises(RatchetViolation):
            self._run(_synth_run(self.led, rc=0))                 # FAILED but rc 0

    def test_returncode_disagrees_with_ok_status_rejected(self):
        with self.assertRaises(RatchetViolation):
            self._run(_synth_run(self.led, status="OK", rc=1))    # OK but rc nonzero

    # -- the three checks are actually invoked ------------------------------ #

    def test_projection_is_invoked(self):
        # extractor yields atoms that do NOT match the ledger -> projection reddens
        bogus = lambda tid: {"source_layout|missing|WRONG.py"}
        with self.assertRaises(RatchetViolation):
            self._run(_synth_run(self.led), atomic_extractor=bogus)

    def test_added_row_vs_git_parent_reddens(self):
        # git parent LACKS a row the candidate has -> the ratchet reddens against
        # the GIT-loaded parent (subset and/or frozen), never a caller-supplied one
        thin = copy.deepcopy(self.led)
        thin["failing"] = thin["failing"][:-1]
        thin["totals"] = cr._derived_totals(thin)
        with self.assertRaises(RatchetViolation):
            self._run(_synth_run(self.led), git_show=lambda ref, rel: json.dumps(thin))

    def test_frozen_is_invoked(self):
        # candidate on disk has forged totals -> frozen reddens (parent == candidate)
        forged = copy.deepcopy(self.led)
        forged["totals"]["unique_test_ids"] = 999
        self.path.write_text(json.dumps(forged), encoding="utf-8")
        with self.assertRaises(RatchetViolation):
            self._run(_synth_run(forged), git_show=lambda ref, rel: json.dumps(forged))

    def test_parent_provenance_is_git_not_caller(self):
        # There is no parent parameter: the parent ALWAYS comes from git_show(base_ref).
        # The candidate ADDS a loader mask, so the run OBSERVES it and projection
        # passes — yet the GIT parent (the original 9-mask ledger) lacks that unit,
        # so the subset/frozen ratchet reddens. A caller cannot launder an addition
        # by pretending the candidate is its own parent.
        added = copy.deepcopy(self.led)
        added["loader_masks"].append({
            "module": "tests.contracts.test_skill_structure",
            "fingerprint": "ModuleNotFoundError: No module named 'tests.contracts.test_skill_structure'",
            "unmask_rule": UNMASK_RULE})
        added["totals"] = cr._derived_totals(added)
        self.path.write_text(json.dumps(added), encoding="utf-8")
        with self.assertRaises(RatchetViolation):
            cr._run_and_verify_with(self.path, base_ref="HEAD",
                                    subprocess_runner=lambda cmd: _synth_run(added, errors=10),
                                    git_show=self.git_ok,          # returns the ORIGINAL 9-mask led
                                    atomic_extractor=self.extractor)

    def test_git_show_failure_is_rejected(self):
        def boom(ref, rel):
            raise RatchetRunError("git show failed")
        with self.assertRaises(RatchetViolation):
            self._run(_synth_run(self.led), git_show=boom)


# --------------------------------------------------------------------------- #
# Trusted runner (integration — REAL subprocess + REAL git show, tiny fixture)
# --------------------------------------------------------------------------- #

@unittest.skipUnless(shutil.which("git"), "git required for the integration arm")
class RatchetRunnerIntegration(unittest.TestCase):
    """Clearly-labeled integration arm: builds a tiny throwaway git repo with one
    real failing test, then drives run_and_verify with the REAL subprocess runner
    and REAL ``git show`` (no injection)."""

    def test_real_subprocess_and_git_show_end_to_end(self):
        repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, repo, ignore_errors=True)
        (repo / "contracts").mkdir()
        (repo / "tests").mkdir()
        (repo / "tests" / "__init__.py").write_text("", encoding="utf-8")
        (repo / "tests" / "contracts").mkdir()
        (repo / "tests" / "contracts" / "__init__.py").write_text("", encoding="utf-8")
        (repo / "tests" / "contracts" / "test_x.py").write_text(
            "import unittest\n"
            "class C(unittest.TestCase):\n"
            "    def test_boom(self):\n"
            "        self.assertEqual(1, 2)\n",
            encoding="utf-8",
        )
        ledger = {
            "contract_id": "CorrectionFailureBaseline",
            "schema_version": 1,
            "purpose": "integration fixture",
            "observed_utc": "2026-07-15",
            "command": "python3 -m unittest -v tests.contracts.test_x",
            "measurement_context": "throwaway fixture repo",
            "totals": {"failures": 1, "errors": 0, "unique_test_ids": 1},
            "setupclass_masks": [],
            "loader_masks": [],
            "failing": [{
                "id": "tests.contracts.test_x.C::test_boom",
                "kind": "failure",
                "fingerprint_mode": "exact",
                "subtest_vectors": 0,
                "fingerprints": ["AssertionError: 1 != 2"],
            }],
        }
        (repo / "contracts" / "correction_baseline.json").write_text(json.dumps(ledger), encoding="utf-8")

        env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        run = lambda *a: subprocess.run(a, cwd=str(repo), env={**dict(__import__("os").environ), **env},
                                        capture_output=True, text=True)
        self.assertEqual(run("git", "init", "-q").returncode, 0)
        run("git", "add", "-A")
        commit = run("git", "commit", "-q", "-m", "seed")
        self.assertEqual(commit.returncode, 0, commit.stderr)

        result = run_and_verify(repo / "contracts" / "correction_baseline.json", base_ref="HEAD")
        self.assertEqual(result["ledger_change"], "unchanged")
        self.assertEqual(result["frozen"], "frozen")
        self.assertEqual(result["status"], "FAILED")
        self.assertNotEqual(result["returncode"], 0)

    def test_real_run_with_deleted_test_is_rejected(self):
        """If the sole test is removed, the real run reports Ran 0 / no discovery
        and run_and_verify rejects the dishonest shrink."""
        repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, repo, ignore_errors=True)
        (repo / "contracts").mkdir()
        (repo / "tests").mkdir()
        (repo / "tests" / "__init__.py").write_text("", encoding="utf-8")
        (repo / "tests" / "contracts").mkdir()
        (repo / "tests" / "contracts" / "__init__.py").write_text("", encoding="utf-8")
        # a module that imports fine but defines ZERO tests
        (repo / "tests" / "contracts" / "test_x.py").write_text("x = 1\n", encoding="utf-8")
        ledger = {
            "contract_id": "CorrectionFailureBaseline", "schema_version": 1,
            "purpose": "integration fixture", "observed_utc": "2026-07-15",
            "command": "python3 -m unittest -v tests.contracts.test_x",
            "measurement_context": "throwaway fixture repo",
            "totals": {"failures": 0, "errors": 0, "unique_test_ids": 0},
            "setupclass_masks": [], "loader_masks": [], "failing": [],
        }
        (repo / "contracts" / "correction_baseline.json").write_text(json.dumps(ledger), encoding="utf-8")
        env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        run = lambda *a: subprocess.run(a, cwd=str(repo), env={**dict(__import__("os").environ), **env},
                                        capture_output=True, text=True)
        run("git", "init", "-q")
        run("git", "add", "-A")
        run("git", "commit", "-q", "-m", "seed")
        with self.assertRaises(RatchetViolation):
            run_and_verify(repo / "contracts" / "correction_baseline.json", base_ref="HEAD")


# --------------------------------------------------------------------------- #
# FINDING #1 (P0) — execution ordering: verification + parent load BEFORE any
# candidate-supplied command runs (real subprocess + real git, sentinel witness)
# --------------------------------------------------------------------------- #

@unittest.skipUnless(shutil.which("git"), "git required for the ordering arm")
class RatchetCommandExecutionOrdering(unittest.TestCase):
    """All verification that can be done pre-run — loading the git parent and
    confirming the candidate's frozen structure, including the ``command`` scalar
    — must happen BEFORE any command executes. Proven with the REAL subprocess
    runner and REAL ``git show`` (no injection) through a sentinel-file witness:
    a tampered candidate ``command`` carrying an appended side effect is rejected
    WITHOUT that side effect ever running."""

    def _git(self, repo):
        env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        return lambda *a: subprocess.run(
            a, cwd=str(repo), env={**dict(__import__("os").environ), **env},
            capture_output=True, text=True)

    def test_tampered_candidate_command_never_executes_before_verification(self):
        repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, repo, ignore_errors=True)
        (repo / "contracts").mkdir()
        (repo / "tests").mkdir()
        (repo / "tests" / "__init__.py").write_text("", encoding="utf-8")
        (repo / "tests" / "contracts").mkdir()
        (repo / "tests" / "contracts" / "__init__.py").write_text("", encoding="utf-8")
        (repo / "tests" / "contracts" / "test_x.py").write_text(
            "import unittest\n"
            "class C(unittest.TestCase):\n"
            "    def test_boom(self):\n"
            "        self.assertEqual(1, 2)\n",
            encoding="utf-8",
        )
        honest = "python3 -m unittest -v tests.contracts.test_x"
        ledger = {
            "contract_id": "CorrectionFailureBaseline", "schema_version": 1,
            "purpose": "ordering fixture", "observed_utc": "2026-07-15",
            "command": honest, "measurement_context": "throwaway fixture repo",
            "totals": {"failures": 1, "errors": 0, "unique_test_ids": 1},
            "setupclass_masks": [], "loader_masks": [],
            "failing": [{
                "id": "tests.contracts.test_x.C::test_boom", "kind": "failure",
                "fingerprint_mode": "exact", "subtest_vectors": 0,
                "fingerprints": ["AssertionError: 1 != 2"],
            }],
        }
        path = repo / "contracts" / "correction_baseline.json"
        path.write_text(json.dumps(ledger), encoding="utf-8")

        git = self._git(repo)
        self.assertEqual(git("git", "init", "-q").returncode, 0)
        git("git", "add", "-A")
        commit = git("git", "commit", "-q", "-m", "seed")
        self.assertEqual(commit.returncode, 0, commit.stderr)

        # Overwrite the WORKING-COPY ledger with a tampered candidate: the honest
        # command plus an appended sentinel side effect. The committed PARENT keeps
        # the honest command, so the frozen ``command`` scalar differs.
        tampered = copy.deepcopy(ledger)
        tampered["command"] = honest + " ; touch pwned_sentinel"
        path.write_text(json.dumps(tampered), encoding="utf-8")

        sentinel = repo / "pwned_sentinel"
        with self.assertRaises(RatchetViolation):
            run_and_verify(path, base_ref="HEAD")
        self.assertFalse(
            sentinel.exists(),
            "the tampered candidate command executed its side effect BEFORE verification",
        )


# --------------------------------------------------------------------------- #
# FINDING #2 (P1) — substitutable provenance: the PUBLIC entry point exposes no
# injection seams; the real subprocess / git / extractor are not opt-out
# --------------------------------------------------------------------------- #

class RatchetPublicSurface(unittest.TestCase):
    def test_public_run_and_verify_exposes_no_injection_seams(self):
        import inspect
        params = inspect.signature(run_and_verify).parameters
        self.assertEqual(set(params), {"baseline_path", "base_ref"})
        for banned in ("subprocess_runner", "git_show", "atomic_extractor"):
            self.assertNotIn(banned, params)
        for name, p in params.items():
            if p.default is not inspect.Parameter.empty:
                self.assertFalse(
                    callable(p.default),
                    f"public parameter {name!r} carries a callable default",
                )


# --------------------------------------------------------------------------- #
# FINDING #3 (P1) — completion/discovery input-handling: discovery evidence comes
# only from the top streaming region; the completion status must follow the
# summary (a status before the summary, or none after it, is not completion)
# --------------------------------------------------------------------------- #

class RatchetRunParsing(unittest.TestCase):
    def test_embedded_ok_line_is_not_counted_as_module_discovery(self):
        # test_real executes; test_ghost has ZERO real tests and is NOT a mask.
        # test_ghost's only evidence is a forged verbose line printed INSIDE a
        # failing test's detail block (after the ==== separator), not in the top
        # streaming region — it must not count as discovery.
        output = "\n".join([
            "test_a (tests.contracts.test_real.C) ... ok",
            "test_b (tests.contracts.test_real.C) ... FAIL",
            "======================================================================",
            "FAIL: test_b (tests.contracts.test_real.C)",
            "----------------------------------------------------------------------",
            "Traceback (most recent call last):",
            "smoke (tests.contracts.test_ghost.C) ... ok",     # forged, inside detail
            "AssertionError: boom",
            "----------------------------------------------------------------------",
            "Ran 2 tests in 0.010s",
            "",
            "FAILED (failures=1)",
        ]) + "\n"
        modules = ["tests.contracts.test_real", "tests.contracts.test_ghost"]
        observed_raw = {
            "ordinary": {("tests.contracts.test_real.C::test_b", "AssertionError: boom")},
            "loader": set(), "setupclass": set(),
        }
        with self.assertRaises(RatchetRunError):
            cr._check_run(output, 1, modules, observed_raw)

    def test_status_before_summary_is_not_a_valid_terminal_status(self):
        # An OK appears BEFORE the "Ran N" summary and there is NO status after
        # it (a truncated/forged tail). Ran N>0 and the named module executes, so
        # the ONLY thing wrong is the misplaced completion status.
        output = "\n".join([
            "test_a (tests.contracts.test_x.C) ... ok",
            "OK",                                               # early, pre-summary
            "----------------------------------------------------------------------",
            "Ran 1 test in 0.010s",
        ]) + "\n"
        empty = {"ordinary": set(), "loader": set(), "setupclass": set()}
        with self.assertRaises(RatchetRunError):
            cr._check_run(output, 0, ["tests.contracts.test_x"], empty)


# --------------------------------------------------------------------------- #
# FINDING #4 (P1) — seed-to-canonical transition: the one-way bootstrap that
# mints a canonical ledger from the slice-0 seed, and the refusal of a seed as
# a ratchet parent
# --------------------------------------------------------------------------- #

class RatchetSeedToCanonical(unittest.TestCase):
    def _seed(self):
        return load_ledger(LEDGER)

    def test_regenerate_canonical_seed_projects_onto_seed_identities(self):
        seed = self._seed()
        fixture = _canonical_ledger()
        atoms = {r["id"]: set(r["fingerprints"]) for r in fixture["failing"]}
        extractor = lambda tid: atoms.get(tid)

        out = cr.regenerate_canonical_seed(seed, _synth_run(fixture), extractor)

        # 1. canonical totals vocabulary (no seed six-key vocabulary)
        self.assertEqual(set(out["totals"]), {"failures", "errors", "unique_test_ids"})
        # 2. fully-qualified loader keys + atomic-members fingerprint mode
        self.assertTrue(out["loader_masks"])
        for m in out["loader_masks"]:
            self.assertTrue(m["module"].startswith("tests.contracts."), m["module"])
        for row in out["failing"]:
            self.assertEqual(row["fingerprint_mode"], "atomic-members")
            self.assertTrue(row["fingerprints"])
        # the minted ledger is a well-formed CANONICAL ledger (clean self-parent)
        self.assertEqual(cr.seed_shape(out), "canonical")
        self.assertEqual(verify_frozen_structure(out, out), "frozen")

        # 3. a NEW failure absent from the seed identity set may not be smuggled in
        extra = copy.deepcopy(fixture)
        extra["failing"].append({
            "id": "tests.contracts.test_dom_cover.DomCover::test_smuggled",
            "kind": "failure", "fingerprint_mode": "exact", "subtest_vectors": 0,
            "fingerprints": ["AssertionError: smuggled"]})
        with self.assertRaises(RatchetViolation):
            cr.regenerate_canonical_seed(seed, _synth_run(extra, failures=8), extractor)

    def test_slice0_seed_is_refused_as_ratchet_parent(self):
        seed = self._seed()
        self.assertEqual(cr.seed_shape(seed), "slice0-seed")
        self.assertEqual(cr.seed_shape(_canonical_ledger()), "canonical")
        child = _canonical_ledger()
        with self.assertRaisesRegex(RatchetViolation, "seed"):
            verify_subset_of_parent(child, seed)
        with self.assertRaisesRegex(RatchetViolation, "seed"):
            verify_frozen_structure(child, seed)


# --------------------------------------------------------------------------- #
# FINDING #6 (P1) — mutation-isolation REDs: each PASSES on HEAD and its
# right-reason failure is proven against a NAMED mutant (recorded in the build
# report's witness table). These make each defense load-bearing.
# --------------------------------------------------------------------------- #

class RatchetMutationIsolation(unittest.TestCase):
    def test_ran_zero_rejected_even_when_all_modules_masked(self):
        """Kills removing the ``if ran == 0`` guard. Every named module is a
        declared loader mask, so discovery passes with zero executed tests and the
        run reports ``Ran 0`` + a canonical ``OK``; only the Ran-0 guard rejects
        it."""
        output = "\n".join([
            "----------------------------------------------------------------------",
            "Ran 0 tests in 0.001s",
            "",
            "OK",
        ]) + "\n"
        observed_raw = {
            "ordinary": set(),
            "loader": {("tests.contracts.test_masked",
                        "ModuleNotFoundError: No module named 'tests.contracts.test_masked'")},
            "setupclass": set(),
        }
        with self.assertRaises(RatchetRunError):
            cr._check_run(output, 0, ["tests.contracts.test_masked"], observed_raw)

    def test_missing_status_rejected_when_all_modules_execute(self):
        """Kills removing the missing-terminal-status guard. Every named module
        emits a real verbose line (discovery passes) and ``Ran N>0`` is present,
        but there is NO terminal status; all names match so a module-name mismatch
        cannot be what rejects it."""
        output = "\n".join([
            "test_a (tests.contracts.test_m.C) ... ok",
            "----------------------------------------------------------------------",
            "Ran 1 test in 0.010s",
        ]) + "\n"
        empty = {"ordinary": set(), "loader": set(), "setupclass": set()}
        with self.assertRaises(RatchetRunError):
            cr._check_run(output, 0, ["tests.contracts.test_m"], empty)

    def test_non_fully_qualified_identity_rejected_directly(self):
        """Kills removing the fully-qualified-identity block. Summary, status and
        discovery all pass, but an observed ordinary identity is not under any
        named module; only the FQ-identity check rejects it."""
        output = "\n".join([
            "test_x (tests.contracts.test_real.C) ... ok",
            "----------------------------------------------------------------------",
            "Ran 1 test in 0.010s",
            "",
            "OK",
        ]) + "\n"
        observed_raw = {
            "ordinary": {("some.other.Module::test_x", "AssertionError: boom")},
            "loader": set(), "setupclass": set(),
        }
        with self.assertRaisesRegex(RatchetRunError, "fully qualified"):
            cr._check_run(output, 0, ["tests.contracts.test_real"], observed_raw)

    def test_each_structural_extractor_yields_nonempty_atoms_on_a_fixture(self):
        """Kills replacing any of the seven extractors with ``return set()``. Uses
        a CONSTRUCTED fixture tree (NEVER the live tree, where 4 of 7 extractors
        are legitimately empty) engineered so every extractor yields >=1 atom whose
        members match the ``category|side|member`` grammar."""
        fixture = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, fixture, ignore_errors=True)
        (fixture / "contracts").mkdir()
        layout = {
            "structural_layout": {
                "source_layout": {
                    "root": "scripts", "glob": "**/*.py", "placement_enforced": True,
                    "root_allowlist": ["phantom_root_src.py"],
                    "groups": [{"id": "organization", "target_dir": "organization",
                                "members": ["phantom_member_src.py"]}],
                },
                "test_layout": {
                    "root": "tests", "glob": "**/test_*.py", "placement_enforced": True,
                    "data_dirs": ["fixtures"], "root_allowlist": [],
                    "groups": [{"id": "contracts", "target_dir": "contracts",
                                "members": ["test_phantom_member.py"]}],
                },
            }
        }
        (fixture / "contracts" / "repo_layout.json").write_text(json.dumps(layout), encoding="utf-8")
        # No scripts/ or tests/ tree exists under the fixture root, so every declared
        # home is missing/phantom/misplaced and every live-declared test module /
        # authority file is absent -> all seven extractors are non-empty.
        for tid in STRUCTURAL_EXTRACTOR_IDS:
            atoms = structural_atoms(tid, repo_root=fixture)
            self.assertTrue(atoms, f"{tid} produced no atoms on the fixture")
            for atom in atoms:
                self.assertGreaterEqual(atom.count("|"), 2, atom)  # category|side|member


# --------------------------------------------------------------------------- #
# FINDING #5 (P2) — documentation honesty: the seed docstrings describe the
# ACTUAL on-disk seed (six-key totals vocabulary, seed-terminal-line
# fingerprints, ratchet_status annotation), bound to a declared constant
# --------------------------------------------------------------------------- #

class RatchetSeedDocstringHonesty(unittest.TestCase):
    def test_seed_docstring_facts_hold_on_disk(self):
        seed = load_ledger(LEDGER)
        # the declared seed vocabulary constant exists and matches the on-disk seed
        self.assertEqual(set(seed["totals"]), set(cr._SEED_TOTALS_KEYS))
        self.assertNotIn("unique_test_ids", set(seed["totals"]))
        # the on-disk seed's fingerprint mode is seed-terminal-line on every row
        self.assertTrue(all(r["fingerprint_mode"] == "seed-terminal-line" for r in seed["failing"]))
        self.assertIn("ratchet_status", seed)
        # the MODULE docstring documents the ACTUAL seed, not the retired
        # unique_test_ids = 7 story
        doc = cr.__doc__
        self.assertIn("seed-terminal-line", doc)
        self.assertIn("ratchet_status", doc)
        self.assertNotIn("(7) rather than 16", doc)
        # the TEST-module docstring is reconciled to the same facts
        test_doc = sys.modules[__name__].__doc__
        self.assertNotIn("unique_test_ids = 7", test_doc)
        self.assertIn("seed-terminal-line", test_doc)


# --------------------------------------------------------------------------- #
# R5 ITEM 1 (F8) — one summary block, one truth: the run's test COUNT and its
# completion STATUS must derive from the SAME final ``Ran N tests`` anchor, so
# an early captured ``Ran N`` line can never be mistaken for the terminal count.
# --------------------------------------------------------------------------- #

class RatchetSummaryAnchor(unittest.TestCase):
    def test_zero_tests_rejected_despite_earlier_nonzero_summary(self):
        """An early ``Ran 1 test`` line (e.g. captured from an inner run) precedes
        the REAL terminal ``Ran 0 tests`` / ``OK``. The count MUST come from the
        final summary the status uses, so the zero-tests guard fires. Reading the
        count from the FIRST ``Ran N`` match returns ``(1, 'OK')`` and slips past
        the zero-tests guard."""
        output = "\n".join([
            "Ran 1 test in 0.001s",          # early, captured — NOT the terminal summary
            "OK",
            "----------------------------------------------------------------------",
            "Ran 0 tests in 0.001s",         # the REAL terminal summary
            "",
            "OK",
        ]) + "\n"
        observed_raw = {
            "ordinary": set(),
            "loader": {("tests.contracts.test_masked",
                        "ModuleNotFoundError: No module named 'tests.contracts.test_masked'")},
            "setupclass": set(),
        }
        with self.assertRaises(RatchetRunError):
            cr._check_run(output, 0, ["tests.contracts.test_masked"], observed_raw)

    def test_summary_count_comes_from_final_anchor(self):
        """An early ``Ran 3 tests`` line precedes the terminal ``Ran 2 tests``. The
        returned count MUST be 2 (the final anchor), never 3 (the first match) —
        count and status can never disagree on which summary block they read."""
        output = "\n".join([
            "test_a (tests.contracts.test_real.C) ... ok",   # top-region discovery
            "Ran 3 tests in 0.001s",                          # early captured summary
            "OK",
            "----------------------------------------------------------------------",
            "Ran 2 tests in 0.002s",                          # the REAL terminal summary
            "",
            "OK",
        ]) + "\n"
        empty = {"ordinary": set(), "loader": set(), "setupclass": set()}
        ran, status = cr._check_run(output, 0, ["tests.contracts.test_real"], empty)
        self.assertEqual(ran, 2)
        self.assertEqual(status, "OK")


# --------------------------------------------------------------------------- #
# R5 ITEM 2 (F7) — no shell between the frozen command and execution: the
# default runner splits the parent-pinned string with shlex, lifts the leading
# VAR=value tokens into an environment overlay, and executes with shell=False,
# so a shell metacharacter in an argument reaches the child LITERALLY. Behaviour
# is defined ONLY for the frozen parent-pinned string (unchanged trust boundary).
# --------------------------------------------------------------------------- #

class RatchetRunnerNoShell(unittest.TestCase):
    def _helper(self):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        helper = d / "echo_args.py"
        helper.write_text(
            "import os, sys\n"
            "sys.stdout.write('ENV=' + os.environ.get('RATCHET_ENVVAR', '<unset>') + '\\n')\n"
            "sys.stdout.write('ARGV=' + repr(sys.argv[1:]) + '\\n')\n",
            encoding="utf-8",
        )
        return d, helper

    def test_shell_metacharacter_in_argument_is_literal(self):
        d, helper = self._helper()
        # An argument carrying a command-substitution metacharacter. A shell expands
        # $(whoami) to the username; shell=False delivers it LITERALLY. No spaces, so
        # shlex keeps it a single token.
        arg = "pre$(whoami)post"
        command = "{} {} {}".format(shlex.quote(sys.executable), shlex.quote(str(helper)), arg)
        run = cr._default_subprocess_runner(command, d)
        self.assertEqual(run.returncode, 0, run.output)
        self.assertIn("pre$(whoami)post", run.output)   # literal byte reached the child

    def test_env_prefix_becomes_child_environment(self):
        d, helper = self._helper()
        # A leading VAR=value prefix whose VALUE carries a command-substitution
        # metacharacter. A shell runs the substitution into the value; the split
        # runner applies the value LITERALLY as a child-environment overlay, so the
        # child both SEES the variable and sees its exact frozen bytes.
        command = "RATCHET_ENVVAR=pre$(whoami)post {} {}".format(
            shlex.quote(sys.executable), shlex.quote(str(helper)))
        run = cr._default_subprocess_runner(command, d)
        self.assertEqual(run.returncode, 0, run.output)
        self.assertIn("ENV=pre$(whoami)post", run.output)   # overlay applied, literally

    def test_runner_invokes_subprocess_without_a_shell(self):
        recorded = {}

        def fake_run(*args, **kwargs):
            recorded["args"] = args
            recorded["kwargs"] = kwargs
            return subprocess.CompletedProcess(
                args=(args[0] if args else kwargs.get("args")), returncode=0, stdout="", stderr="")

        with mock.patch.object(cr.subprocess, "run", side_effect=fake_run):
            cr._default_subprocess_runner(
                "{} -c pass".format(shlex.quote(sys.executable)), Path("."))
        self.assertFalse(recorded["kwargs"].get("shell", False),
                         "the runner executed through a shell")
        first = recorded["args"][0] if recorded["args"] else recorded["kwargs"].get("args")
        self.assertIsInstance(first, list)   # an argv vector, not a raw command string


# --------------------------------------------------------------------------- #
# R5 ITEM 3 (F6) — reproducible mutation matrix: driving the runner over named
# entries proves each neutralization is KILLED (a test reddens) and — via a
# deliberately vacuous entry — that the runner itself is non-vacuous (a no-op
# patch SURVIVES and flips the exit code). The class self-skips inside a matrix
# child run (RATCHET_MUTATION_MATRIX=1) so the matrix never recurses into itself.
# --------------------------------------------------------------------------- #

@unittest.skipIf(os.environ.get("RATCHET_MUTATION_MATRIX") == "1",
                 "matrix child run: matrix-invocation tests self-skip to avoid recursion")
class RatchetMutationMatrixRunner(unittest.TestCase):
    def test_matrix_kills_named_defenses(self):
        import scripts.organization.ratchet_mutation_matrix as rmm
        entries = ["zero_tests_guard", "missing_status_guard", "undiscovered_module_guard"]
        out = Path(tempfile.mkdtemp()) / "witness.json"
        self.addCleanup(shutil.rmtree, out.parent, ignore_errors=True)
        report = rmm.run_matrix(entries=entries, out_path=out)
        self.assertEqual(len(report["results"]), 3)
        for r in report["results"]:
            self.assertTrue(r["applied"], "{} patch spec failed to apply".format(r["id"]))
            self.assertFalse(r["survived"], "{} SURVIVED — not load-bearing".format(r["id"]))
            self.assertTrue(r["reddened"], "{} killed but recorded no reddened test".format(r["id"]))
            self.assertEqual(len(r["output_sha256"]), 64)
        self.assertEqual(report["survivors"], [])
        self.assertEqual(report["specs_failed"], [])
        self.assertTrue(out.exists())
        witness = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(len(witness["results"]), 3)

    def test_vacuous_entry_survives_and_flips_exit(self):
        import scripts.organization.ratchet_mutation_matrix as rmm
        out = Path(tempfile.mkdtemp()) / "witness.json"
        self.addCleanup(shutil.rmtree, out.parent, ignore_errors=True)
        exit_code = rmm.main(["--entries", "vacuous_comment_noop", "--out", str(out)])
        self.assertNotEqual(exit_code, 0)   # a surviving entry flips the exit code
        witness = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(len(witness["results"]), 1)
        self.assertTrue(witness["results"][0]["survived"])
        self.assertTrue(witness["results"][0]["applied"])


if __name__ == "__main__":
    unittest.main()
# --------------------------------------------------------------------------- #
# RATCHET R6 CONVERGENCE ARMS — tranche 1 (Fable-authored 2026-07-17; appends to
# the adopted r5 test file 162524e6…; Opus never edits this file).
#
# Assembly: final RED = adopted tests/contracts/test_correction_ratchet.py + this
# block appended verbatim (helpers _canonical_ledger/_synth_run/_obs, the `cr`
# alias, LEDGER, and the stdlib imports all come from the adopted file).
#
# Every arm below must be observed FAILING against the adopted r5 module
# (2140f086…) in the fresh 74fe3ecd room BEFORE the build, for its stated
# reason (recorded in red-observation-receipt-r6.md). Tranche 2 (R6-1 live
# transition, R6-2 public seed parent, R6-8 mask rows, R6-9 homing) binds to
# the room-baseline receipt's live identity delta.
# --------------------------------------------------------------------------- #

import inspect


def _r6_git_env():
    """A git-clean base env for FIXTURE CONSTRUCTION only (never the surface
    under test): ambient GIT_*/config vectors stripped so building the fixture
    repos is itself hermetic."""
    env = {k: v for k, v in os.environ.items()
           if not k.startswith("GIT_") and k not in ("HOME", "XDG_CONFIG_HOME")}
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    return env


def _r6_git(args, cwd, env):
    proc = subprocess.run(["git", *args], cwd=str(cwd), env=env,
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise AssertionError(f"fixture git {args} failed: {proc.stderr}")
    return proc.stdout


class R6HostileGitProvenance(unittest.TestCase):
    """r5 finding F2 (BLOCKING) — R6-3: the REAL ``git show`` parent lookup must
    run under an explicit sanitized environment. End-to-end through the PUBLIC
    ``run_and_verify`` against a real target repo while every repository-selection
    variable points at a forged alternate repo. A fake injected seam does not
    satisfy this arm (prompt :74-77)."""

    #: the full hostile matrix from the r6 prompt (:87-89)
    _POISON_KEYS = (
        "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_NAMESPACE",
    )

    def _ledger(self, failing):
        rows = [{"id": tid, "kind": "failure", "fingerprint_mode": "exact",
                 "subtest_vectors": 0, "fingerprints": list(fps)}
                for tid, fps in failing]
        led = {
            "contract_id": "CorrectionFailureBaseline",
            "schema_version": 1,
            "purpose": "r6 hostile-git fixture",
            "observed_utc": "2026-07-17",
            "command": "python3 -m unittest -v tests.contracts.test_r6tiny",
            "measurement_context": "r6 hostile-git fixture repo",
            "totals": {"failures": 0, "errors": 0, "unique_test_ids": 0},
            "setupclass_masks": [],
            "loader_masks": [],
            "failing": rows,
        }
        led["totals"] = cr._derived_totals(led)
        return led

    def _write_repo(self, root, parent_led, work_led):
        """A real git repo whose committed parent is ``parent_led`` and whose
        working candidate is ``work_led``, plus the tiny genuinely-failing test
        module the pinned command runs."""
        env = _r6_git_env()
        (root / "contracts").mkdir(parents=True)
        (root / "tests" / "contracts").mkdir(parents=True)
        (root / "tests" / "__init__.py").write_text("")
        (root / "tests" / "contracts" / "__init__.py").write_text("")
        (root / "tests" / "contracts" / "test_r6tiny.py").write_text(
            "import unittest\n\n\n"
            "class R6Tiny(unittest.TestCase):\n"
            "    def test_fails(self):\n"
            "        self.assertEqual(1, 2)\n"
        )
        base = root / "contracts" / "correction_baseline.json"
        base.write_text(json.dumps(parent_led, indent=1) + "\n")
        _r6_git(["init", "-q", "-b", "main", "."], root, env)
        _r6_git(["-c", "user.email=r6@test", "-c", "user.name=r6",
                 "add", "-A"], root, env)
        _r6_git(["-c", "user.email=r6@test", "-c", "user.name=r6",
                 "commit", "-q", "-m", "parent"], root, env)
        base.write_text(json.dumps(work_led, indent=1) + "\n")
        return base

    def test_forged_alternate_parent_refused_under_hostile_git_env(self):
        tid = "tests.contracts.test_r6tiny.R6Tiny::test_fails"
        fp = "AssertionError: 1 != 2"
        candidate = self._ledger([(tid, [fp])])   # carries the failing row
        true_parent = self._ledger([])            # does NOT: candidate is no subset

        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        target = tmp / "target"
        target.mkdir()
        baseline = self._write_repo(target, true_parent, candidate)

        # The forged repo: its committed parent IS the candidate, so if the
        # parent lookup can be redirected the check reports "unchanged".
        forged = tmp / "forged"
        forged.mkdir()
        self._write_repo(forged, candidate, candidate)

        poison = {k: "" for k in self._POISON_KEYS}
        poison.update({
            "GIT_DIR": str(forged / ".git"),
            "GIT_WORK_TREE": str(forged),
            "GIT_COMMON_DIR": str(forged / ".git"),
            "GIT_INDEX_FILE": str(forged / ".git" / "index"),
            "GIT_OBJECT_DIRECTORY": str(forged / ".git" / "objects"),
            "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(forged / ".git" / "objects"),
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "core.bare",
            "GIT_CONFIG_VALUE_0": "false",
        })
        with mock.patch.dict(os.environ, poison):
            # Honest behaviour: the parent is read from the TARGET repo (the
            # baseline's own repository), the candidate is not a subset of it,
            # and the check raises. Ambient-substitutable behaviour reads the
            # forged parent and returns "unchanged" — the r5 defect.
            with self.assertRaises(RatchetViolation):
                run_and_verify(baseline, "main")


class R6ClosedExecutionEnvironment(unittest.TestCase):
    """r6 prompt :84-89 — R6-7: the pinned command runs in a CLOSED constructed
    environment; the command's own pinned env prefix is the only overlay.
    ``{**os.environ, **overlay}`` inheritance is the defect under test."""

    def test_poisoned_pythonpath_does_not_reach_the_pinned_command(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        poisoned = tmp / "poisoned-site"
        poisoned.mkdir()
        cmd = ('python3 -c "import sys; print(\'R6-SITE:\' + chr(58).join(sys.path))"')
        with mock.patch.dict(os.environ, {"PYTHONPATH": str(poisoned)}):
            run = cr._default_subprocess_runner(cmd, tmp)
        self.assertNotIn(str(poisoned), run.output,
                         "poisoned PYTHONPATH leaked into the pinned command's "
                         "interpreter — the execution environment must be closed")

    def test_hijacked_path_cannot_substitute_the_interpreter(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        bindir = tmp / "hijack-bin"
        bindir.mkdir()
        fake = bindir / "python3"
        fake.write_text("#!/bin/sh\necho R6-HIJACKED-INTERPRETER\n")
        fake.chmod(0o755)
        cmd = 'python3 -c "print(\'R6-REAL-INTERPRETER\')"'
        with mock.patch.dict(os.environ, {"PATH": f"{bindir}:{os.environ.get('PATH', '')}"}):
            run = cr._default_subprocess_runner(cmd, tmp)
        self.assertNotIn("R6-HIJACKED-INTERPRETER", run.output,
                         "a PATH-hijacked interpreter executed the pinned command")
        self.assertIn("R6-REAL-INTERPRETER", run.output)


class R6TrustedBootstrap(unittest.TestCase):
    """r5 finding F3 (BLOCKING) — R6-4: canonical authority is minted ONLY by a
    path-only trusted bootstrap (loads committed seed bytes, executes the stored
    pinned command through the real runner, uses the live extractor). Synthetic
    injection survives only as a private unit seam that cannot mint authority."""

    def test_regeneration_requires_path_only_trusted_bootstrap(self):
        self.assertTrue(
            hasattr(cr, "bootstrap_canonical_from_seed"),
            "module must expose bootstrap_canonical_from_seed — the path-only "
            "trusted entry for the seed→canonical transition",
        )
        params = list(inspect.signature(cr.bootstrap_canonical_from_seed).parameters)
        self.assertEqual(params[:1], ["baseline_path"],
                         "the trusted bootstrap is path-only: no run_result, no "
                         "extractor, no injectable authority")
        for banned in ("run_result", "atomic_extractor", "output"):
            self.assertNotIn(banned, params,
                             f"injectable parameter {banned!r} on the trusted bootstrap")

    def test_synthetic_injection_cannot_mint_canonical_authority(self):
        seed = copy.deepcopy(load_ledger(LEDGER))
        seed["command"] = "forged-python -m unittest " + " ".join(
            cr._command_modules(load_ledger(LEDGER)["command"]))
        fixture = _canonical_ledger()
        fixture["command"] = seed["command"]
        atoms = {r["id"]: set(r["fingerprints"]) for r in fixture["failing"]}
        with self.assertRaises((RatchetViolation, RatchetRunError)):
            # A command that was never executed by the trusted runner (and is
            # not even python) must not be able to mint a canonical ledger from
            # synthetic output. On the r5 module this mints silently.
            cr.regenerate_canonical_seed(
                seed, _synth_run(fixture), lambda tid: atoms.get(tid))


class R6SeedSchemaClosure(unittest.TestCase):
    """r5 finding F3 (BLOCKING) — R6-5/R6-6: the seed classification is
    all-or-nothing and the seed schema is CLOSED with recomputed totals."""

    def test_partial_seed_signals_rejected(self):
        # one signal only: the annotation key
        led = _canonical_ledger()
        led["ratchet_status"] = "candidate"
        with self.assertRaises(RatchetViolation):
            cr.seed_shape(led)
        # one signal only: a seed-terminal-line row
        led2 = _canonical_ledger()
        led2["failing"][0]["fingerprint_mode"] = "seed-terminal-line"
        with self.assertRaises(RatchetViolation):
            cr.seed_shape(led2)

    def test_full_seed_and_canonical_still_classify(self):
        # guard against over-correction: the REAL committed seed keeps
        # classifying as a seed; a clean canonical ledger stays canonical.
        self.assertEqual(cr.seed_shape(load_ledger(LEDGER)), "slice0-seed")
        self.assertEqual(cr.seed_shape(_canonical_ledger()), "canonical")

    def test_seed_schema_closed_and_totals_recomputed(self):
        fixture = _canonical_ledger()
        atoms = {r["id"]: set(r["fingerprints"]) for r in fixture["failing"]}
        extractor = lambda tid: atoms.get(tid)

        # unknown top-level key on the seed must refuse regeneration
        seed_extra = copy.deepcopy(load_ledger(LEDGER))
        seed_extra["annotation_smuggled"] = {"x": 1}
        with self.assertRaises(RatchetViolation):
            cr.regenerate_canonical_seed(seed_extra, _synth_run(fixture), extractor)

        # corrupt totals (not derivable from the rows) must refuse regeneration
        seed_bad_totals = copy.deepcopy(load_ledger(LEDGER))
        seed_bad_totals["totals"]["failures"] = 999
        with self.assertRaises(RatchetViolation):
            cr.regenerate_canonical_seed(seed_bad_totals, _synth_run(fixture), extractor)


class R6DocumentationTruth(unittest.TestCase):
    """r5 finding F6 (MINOR) — R6-10: the execution comment must tell the truth:
    the pinned command is executed with shell=False; nothing 'reaches the shell'
    and nothing 'genuinely needs a shell'."""

    def test_runner_shell_documentation_truth(self):
        src = Path(cr.__file__).read_text()
        self.assertNotIn("genuinely needs a shell", src)
        self.assertNotIn("reaches the shell", src)
        self.assertIn("shell=False", src)
# --------------------------------------------------------------------------- #
# RATCHET R6 CONVERGENCE ARMS — tranche 2 (Fable-authored 2026-07-17; appends
# after tranche 1; reuses tranche 1's module-level _r6_git_env/_r6_git helpers).
# Bound to the room-baseline receipt (red/room-baseline-receipt-2026-07-17.md):
# live delta on the committed tip = 2 ADDED ordinary identities (both layout-
# contract failures caused by the un-homed ratchet surfaces), 0 missing,
# loader 9=9. The homing arms below are anchored to those two exact identities.
# --------------------------------------------------------------------------- #


class R6LiveSeedTransition(unittest.TestCase):
    """r5 finding F1 (BLOCKING) — R6-1: the seed→canonical transition must work
    on the REAL artifact. The trusted path-only bootstrap executes the committed
    seed's pinned command through the real runner + live extractor; legitimate
    MISSING identities SHRINK (accepted, row dropped, totals recomputed);
    ADDED identities keep rejecting (existing smuggle arm at
    test_regenerate_canonical_seed_projects_onto_seed_identities preserves that
    half — not duplicated here)."""

    def test_live_seed_transition_bootstraps_canonical_on_the_committed_tip(self):
        # The LIVE arm: no _synth_run, no lambda extractor — the bootstrap loads
        # the committed seed bytes, runs the stored pinned command for real, and
        # mints the canonical ledger. On the homed post-build tree the live run
        # projects onto the seed identity set (room receipt: 0 missing; the 2
        # added identities are exactly the un-homed-surface failures the same
        # patch removes by homing them).
        out = cr.bootstrap_canonical_from_seed(LEDGER)
        self.assertEqual(cr.seed_shape(out), "canonical")
        self.assertEqual(set(out["totals"]), {"failures", "errors", "unique_test_ids"})
        self.assertNotIn("ratchet_status", out)
        for m in out["loader_masks"]:
            self.assertTrue(m["module"].startswith("tests.contracts."), m["module"])

    def test_missing_seed_identities_shrink_not_reject(self):
        # Unit seam (lawful: the seam cannot MINT authority — it exercises the
        # projection semantics only). A run legitimately missing ONE seed
        # identity must SHRINK: the row is dropped and totals recompute; the r5
        # module instead raises on any inequality (:1208) — M1 restores that
        # exact equality and must flip this arm.
        seed = load_ledger(LEDGER)
        fixture = _canonical_ledger()
        dropped = fixture["failing"][0]["id"]
        fixture["failing"] = fixture["failing"][1:]
        atoms = {r["id"]: set(r["fingerprints"]) for r in fixture["failing"]}
        out = cr.regenerate_canonical_seed(
            seed, _synth_run(fixture, failures=6), lambda tid: atoms.get(tid))
        out_ids = {r["id"] for r in out["failing"]}
        self.assertNotIn(dropped, out_ids)
        self.assertEqual(out["totals"]["failures"], len(out["failing"]))
        self.assertEqual(
            out["totals"]["unique_test_ids"],
            len(out["failing"]) + len(out["loader_masks"]) + len(out["setupclass_masks"]))


class R6PublicSeedParent(unittest.TestCase):
    """r5 finding F1b — R6-2: the PUBLIC ``run_and_verify`` accepts the one-time
    valid seed parent and validates the canonical transition. Leaving
    ``_refuse_seed_parent`` on the public verifier fails this arm (a separate
    bootstrap helper alone does not close the law — prompt :70-72)."""

    def _mini_seed(self, tid, terminal, command):
        return {
            "contract_id": "CorrectionFailureBaseline",
            "schema_version": 1,
            "purpose": "r6 mini seed fixture",
            "observed_utc": "2026-07-17",
            "command": command,
            "measurement_context": "r6 mini seed fixture repo",
            "ratchet_status": "SEED — binds at slice 1 (r6 fixture).",
            "totals": {"failures": 1, "errors": 0, "ordinary_failing_rows": 1,
                       "loader_masks": 0, "setupclass_masks": 0,
                       "observed_identities": 1},
            "setupclass_masks": [],
            "loader_masks": [],
            "failing": [{"id": tid, "kind": "failure",
                         "fingerprint_mode": "seed-terminal-line",
                         "subtest_vectors": 0, "fingerprints": [terminal]}],
        }

    def _mini_canonical(self, tid, terminal, command):
        led = {
            "contract_id": "CorrectionFailureBaseline",
            "schema_version": 1,
            "purpose": "r6 mini seed fixture",
            "observed_utc": "2026-07-17",
            "command": command,
            "measurement_context": "r6 mini seed fixture repo",
            "totals": {"failures": 0, "errors": 0, "unique_test_ids": 0},
            "setupclass_masks": [],
            "loader_masks": [],
            "failing": [{"id": tid, "kind": "failure", "fingerprint_mode": "exact",
                         "subtest_vectors": 0, "fingerprints": [terminal]}],
        }
        led["totals"] = cr._derived_totals(led)
        return led

    def test_public_run_and_verify_accepts_one_time_seed_parent(self):
        tid = "tests.contracts.test_r6tiny.R6Tiny::test_fails"
        terminal = "AssertionError: 1 != 2"
        command = "python3 -m unittest -v tests.contracts.test_r6tiny"
        env = _r6_git_env()
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        (root / "contracts").mkdir()
        (root / "tests" / "contracts").mkdir(parents=True)
        (root / "tests" / "__init__.py").write_text("")
        (root / "tests" / "contracts" / "__init__.py").write_text("")
        (root / "tests" / "contracts" / "test_r6tiny.py").write_text(
            "import unittest\n\n\n"
            "class R6Tiny(unittest.TestCase):\n"
            "    def test_fails(self):\n"
            "        self.assertEqual(1, 2)\n"
        )
        baseline = root / "contracts" / "correction_baseline.json"
        baseline.write_text(json.dumps(
            self._mini_seed(tid, terminal, command), indent=1) + "\n")
        _r6_git(["init", "-q", "-b", "main", "."], root, env)
        _r6_git(["-c", "user.email=r6@test", "-c", "user.name=r6", "add", "-A"], root, env)
        _r6_git(["-c", "user.email=r6@test", "-c", "user.name=r6",
                 "commit", "-q", "-m", "seed parent"], root, env)
        baseline.write_text(json.dumps(
            self._mini_canonical(tid, terminal, command), indent=1) + "\n")

        # The committed parent IS the one-time seed; the working candidate is
        # its canonical projection. The public path must validate the
        # transition and return, not refuse the parent.
        result = run_and_verify(baseline, "main")
        self.assertIsInstance(result, dict)
        self.assertIn("ran", result)


class R6MaskCanonicalization(unittest.TestCase):
    """r5 finding F4 (MAJOR) — R6-8: regeneration must CANONICALIZE mask rules,
    not freeze the seed's nonconformant text (the committed seed's 9 rows carry
    0 instances of the discovery/zero-test/stale-mask obligations). One exact
    loader unmask rule is promoted to production authority; all NINE live rows
    are validated before regeneration."""

    def _fixture_and_extractor(self):
        fixture = _canonical_ledger()
        atoms = {r["id"]: set(r["fingerprints"]) for r in fixture["failing"]}
        return fixture, (lambda tid: atoms.get(tid))

    def test_production_authority_unmask_rule_exists(self):
        self.assertTrue(
            hasattr(cr, "CANONICAL_UNMASK_RULE"),
            "module must promote the exact loader unmask rule to production "
            "authority (the test-file copy is not an authority)")
        for needle in ("discovery", "zero", "stale"):
            self.assertIn(needle, cr.CANONICAL_UNMASK_RULE)

    def test_regenerated_mask_rules_canonicalized(self):
        seed = load_ledger(LEDGER)
        fixture, extractor = self._fixture_and_extractor()
        out = cr.regenerate_canonical_seed(seed, _synth_run(fixture), extractor)
        self.assertEqual(len(out["loader_masks"]), 9)
        for m in out["loader_masks"]:
            for needle in ("discovery", "zero", "stale"):
                self.assertIn(
                    needle, m["unmask_rule"],
                    f"regenerated rule for {m['module']} not canonicalized")

    def test_all_nine_live_seed_rows_validated_before_regeneration(self):
        seed = copy.deepcopy(load_ledger(LEDGER))
        seed["loader_masks"][3]["unmask_rule"] = ""
        fixture, extractor = self._fixture_and_extractor()
        with self.assertRaises(RatchetViolation):
            cr.regenerate_canonical_seed(seed, _synth_run(fixture), extractor)


class R6LayoutHoming(unittest.TestCase):
    """r5 finding F1 homing half / prompt :102-106 — R6-9: the ratchet surfaces
    are homed in the same slice. Anchored to the room receipt's two live added
    identities — the layout suite's own complaints about the un-homed files."""

    def test_ratchet_surfaces_declared_in_repo_layout(self):
        text = (ROOT / "contracts" / "repo_layout.json").read_text()
        for name in ("correction_ratchet.py", "ratchet_mutation_matrix.py",
                     "test_correction_ratchet.py", "correction_baseline.json"):
            self.assertIn(name, text, f"{name} is not declared in repo_layout.json")

    def _run_named(self, dotted):
        suite = unittest.defaultTestLoader.loadTestsFromName(dotted)
        stream = io.StringIO()
        result = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
        return result, stream.getvalue()

    def test_scripts_layout_contract_green_with_ratchet_homed(self):
        result, out = self._run_named(
            "tests.contracts.test_scripts_layout_contract.ScriptsLayoutContractTests"
            ".test_live_scripts_tree_matches_semantic_contract")
        self.assertTrue(result.wasSuccessful(),
                        f"scripts layout contract reddens on the un-homed ratchet "
                        f"surfaces:\n{out}")

    def test_tests_layout_contract_green_with_ratchet_homed(self):
        result, out = self._run_named(
            "tests.contracts.test_tests_layout_contract.TestsLayoutContract"
            ".test_every_test_file_in_declared_home")
        self.assertTrue(result.wasSuccessful(),
                        f"tests layout contract reddens on the un-homed ratchet "
                        f"test:\n{out}")

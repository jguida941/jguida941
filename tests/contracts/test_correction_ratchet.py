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

Because the on-disk seed committed at slice 0 is a known-stale best-effort seed
(bare loader keys, terminal-line fingerprints, ``unique_test_ids = 7``, extra
``ratchet_status`` key) that the conductor regenerates at slice-1 landing with
the parser + extractor provided here, the behaviour tests bind a CANONICAL
in-memory ledger built to the §13.2 shape rather than the stale bytes; the seed
file itself gets only a load/parse smoke.
"""

import copy
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

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
        return run_and_verify(
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
            run_and_verify(self.path, base_ref="HEAD",
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


if __name__ == "__main__":
    unittest.main()

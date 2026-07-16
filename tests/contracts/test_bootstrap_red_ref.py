"""P5-0c — the RED guarding the BOOTSTRAP-RED-REF gate (add-the-RED-before-the-file).

Proves the verdict-free gather/relay in scripts/organization/bootstrap_red_ref.py: a
mutation-capable task with no named RED is REJECTED; a cleanup/reorg/SHAPE task is rejected
unless its RED is an executable target-shape contract; a read-only task may proceed; unknown
intent fails CLOSED. Mutation-proven (the gate CAN reject). The gate decides no authority — the
sealed Rust MissingRedTestRef (preflight.rs) is the decider; this only relays the rule.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import unittest

from scripts.organization.bootstrap_red_ref import (
    build_observation,
    classify,
    gate,
)


ROOT = Path(__file__).resolve().parents[2]
RED = "tests/contracts/test_page_archetype.py"
SCOPE = {
    "routes": ["index", "showcase", "settings", "studio"],
    "profiles": ["apple-dark", "carbon", "liquid-glass"],
    "aspects": ["page-archetype"],
}


def _observed(*, exit_code: int = 1, output: str = "AssertionError: page archetype missing") -> dict:
    return build_observation(
        "implement source-backed page archetypes",
        RED,
        expected_failure_fingerprint="page archetype missing",
        scope=SCOPE,
        exit_code=exit_code,
        observed_output=output,
        root=ROOT,
    )


class BootstrapRedRefContract(unittest.TestCase):
    # --- classify: mutation / shape / read-only / fail-closed ---

    def test_mutation_verbs_are_mutation_capable(self):
        for task in ("add the foo module", "implement the chart runtime", "edit web_render"):
            self.assertTrue(classify(task)["mutation_capable"], task)

    def test_shape_verbs_require_a_shape_red(self):
        for task in ("reorganize the scripts package", "consolidate the layout", "clean up the docs"):
            cls = classify(task)
            self.assertTrue(cls["mutation_capable"], task)
            self.assertTrue(cls["requires_shape_red"], task)

    def test_file_op_reorg_with_a_path_requires_shape_red(self):
        cls = classify("move helpers into scripts/helpers")
        self.assertTrue(cls["requires_shape_red"], "a file move naming a path is a shape task")

    def test_code_refactor_naming_no_file_does_not_require_shape_red(self):
        # both-directions safe: a code refactor that names no file/path is NOT a shape task
        for task in ("rename the enum variant", "remove the unused parameter"):
            self.assertFalse(classify(task)["requires_shape_red"], task)

    def test_read_only_is_not_mutation_capable(self):
        cls = classify("analyze and inventory the codebase")
        self.assertFalse(cls["mutation_capable"])
        self.assertTrue(cls["read_only"])

    def test_unknown_intent_fails_closed_to_mutation(self):
        self.assertTrue(classify("something vague")["mutation_capable"])

    # --- gate: the relayed admission rule ---

    def test_mutation_without_red_is_rejected(self):
        v = gate("add the foo module", red_ref="")
        self.assertFalse(v["admit"])
        self.assertIn("no named RED", v["reason"])

    def test_nonexistent_red_is_rejected(self):
        v = gate("add the foo module", red_ref="tests/contracts/test_foo.py", root=ROOT)
        self.assertFalse(v["admit"])
        self.assertIn("does not exist", v["reason"])

    def test_existing_red_without_observed_failure_is_rejected(self):
        v = gate("implement source-backed page archetypes", red_ref=RED, root=ROOT)
        self.assertFalse(v["admit"])
        self.assertIn("observation", v["reason"])

    def test_nonzero_expected_failure_is_admitted_and_fully_bound(self):
        observation = _observed()
        v = gate(
            "implement source-backed page archetypes",
            red_ref=RED,
            observation=observation,
            root=ROOT,
        )
        self.assertTrue(v["admit"], v["reason"])
        for field in (
            "base_revision", "red_ref", "test_sha256", "command", "exit_code",
            "expected_failure_fingerprint", "observed_output_sha256", "observed_at_utc", "scope",
        ):
            self.assertIn(field, observation)
        self.assertEqual(
            hashlib.sha256((ROOT / RED).read_bytes()).hexdigest(),
            observation["test_sha256"],
        )

    def test_green_or_wrong_failure_is_rejected(self):
        green = _observed(exit_code=0, output="OK")
        self.assertFalse(gate(
            "implement source-backed page archetypes", RED, green, root=ROOT,
        )["admit"])
        wrong = _observed(output="AssertionError: unrelated failure")
        self.assertFalse(gate(
            "implement source-backed page archetypes", RED, wrong, root=ROOT,
        )["admit"])

    def test_stale_hash_revision_and_scope_mutations_reject(self):
        valid = _observed()
        mutations = []
        for field in ("base_revision", "test_sha256", "observed_output_sha256"):
            changed = deepcopy(valid)
            changed[field] = "0" * 64
            mutations.append((field, changed))
        for field in ("routes", "profiles", "aspects"):
            changed = deepcopy(valid)
            changed["scope"][field] = []
            mutations.append((f"scope.{field}", changed))
        changed = deepcopy(valid)
        changed["observed_at_utc"] = "2000-01-01T00:00:00Z"
        mutations.append(("observed_at_utc", changed))
        for label, observation in mutations:
            with self.subTest(label=label):
                verdict = gate(
                    "implement source-backed page archetypes", RED, observation, root=ROOT,
                )
                self.assertFalse(verdict["admit"], label)

    def test_shape_task_with_a_non_shape_red_is_rejected(self):
        v = gate("reorganize scripts/", red_ref="tests/contracts/test_foo.py")
        self.assertFalse(v["admit"], "a shape task needs a target-shape contract, not just any RED")

    def test_shape_task_with_the_target_shape_contract_is_admitted(self):
        red = "tests/contracts/test_structural_layout.py"
        observation = build_observation(
            "reorganize scripts/",
            red,
            expected_failure_fingerprint="structural layout mismatch",
            scope={"routes": ["repo"], "profiles": ["not-applicable"], "aspects": ["layout"]},
            exit_code=1,
            observed_output="AssertionError: structural layout mismatch",
            root=ROOT,
        )
        self.assertTrue(gate("reorganize scripts/", red, observation, root=ROOT)["admit"])

    def test_read_only_task_is_admitted(self):
        self.assertTrue(gate("analyze the layout", red_ref="")["admit"])

    def test_relay_is_verdict_free_candidate_only(self):
        v = gate("add x", red_ref="tests/test_x.py", root=ROOT)
        self.assertEqual("candidate_only", v["authority_status"])
        self.assertTrue(v["cannot_mark_done"])
        self.assertIn("BootstrapRedObservation", v["decider"])

    def test_observation_red_ref_must_match_the_requested_red(self):
        observation = _observed()
        v = gate(
            "implement source-backed page archetypes",
            "tests/contracts/test_bootstrap_red_ref.py",
            observation,
            root=ROOT,
        )
        self.assertFalse(v["admit"])


if __name__ == "__main__":
    unittest.main()

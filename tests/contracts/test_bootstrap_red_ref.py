"""P5-0c — the RED guarding the BOOTSTRAP-RED-REF gate (add-the-RED-before-the-file).

Proves the verdict-free gather/relay in scripts/organization/bootstrap_red_ref.py: a
mutation-capable task with no named RED is REJECTED; a cleanup/reorg/SHAPE task is rejected
unless its RED is an executable target-shape contract; a read-only task may proceed; unknown
intent fails CLOSED. Mutation-proven (the gate CAN reject). The gate decides no authority — the
sealed Rust MissingRedTestRef (preflight.rs) is the decider; this only relays the rule.
"""
from __future__ import annotations

import unittest

from scripts.organization.bootstrap_red_ref import classify, gate


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

    def test_mutation_with_red_is_admitted(self):
        self.assertTrue(gate("add the foo module", red_ref="tests/contracts/test_foo.py")["admit"])

    def test_shape_task_with_a_non_shape_red_is_rejected(self):
        v = gate("reorganize scripts/", red_ref="tests/contracts/test_foo.py")
        self.assertFalse(v["admit"], "a shape task needs a target-shape contract, not just any RED")

    def test_shape_task_with_the_target_shape_contract_is_admitted(self):
        self.assertTrue(gate("reorganize scripts/",
                             red_ref="tests/contracts/test_structural_layout.py")["admit"])

    def test_read_only_task_is_admitted(self):
        self.assertTrue(gate("analyze the layout", red_ref="")["admit"])

    def test_relay_is_verdict_free_candidate_only(self):
        v = gate("add x", red_ref="tests/test_x.py")
        self.assertEqual("candidate_only", v["authority_status"])
        self.assertTrue(v["cannot_mark_done"])
        self.assertIn("MissingRedTestRef", v["decider"])

    # --- dogfood: this very slice (adding the gate) satisfies its own gate ---

    def test_this_slice_satisfies_the_gate(self):
        v = gate("add the bootstrap-red-ref gate module",
                 red_ref="tests/contracts/test_bootstrap_red_ref.py")
        self.assertTrue(v["admit"], "adding this gate, with this RED named, must be admitted")


if __name__ == "__main__":
    unittest.main()

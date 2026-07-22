"""Finite execution + throughput law RED — the corpus amendment as executable law.

Authored by the fresh exact `claude-fable-5` DESIGN + RED author lane (charter
`fable-process-throughput-design-red-charter-r1`, sha256 `33b75c7f…6162b9`,
amended by the operator scope correction: the law folds into EVERY applicable
governed authority surface in this same slice). `/root` conducts; a DIFFERENT
fresh Opus lane builds GREEN; Codex performs the ONE bounded conformance check.

This module is written BEFORE `contracts/process_throughput_policy.toml` exists.
While that policy is absent, EVERY case fails in setUp with the exact bootstrap
fingerprint `PROCESS-THROUGHPUT-RED: policy absent`. Once the GREEN builder
lands the policy plus the design §8 folds (AGENTS.md finite-execution section,
ACTIVE/HANDOFF routing lines, skill lifecycle sentences, ledger append, layout
homing rows, and the lawful deterministic predecessor re-pin), each case runs
its real closed-rule body: parse the policy, refuse tampered blocker/mechanical/
budget tables fail-closed, prove the five-condition fast path is conjunctive,
prove only invalidating adjacent findings block, prove executable cutoff and
bounded RED repair, prove the whole-slice heartbeat, artifact consumer law, and
worktree retirement, verify the live authority surfaces carry the folded law,
and verify the predecessor currentness family survives byte-pinned and
unweakened. History stays byte-history: the ledger accepts appends only.
"""
from __future__ import annotations

import copy
import hashlib
import re
import unittest
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11 (local): pinned backport, repo law
    import tomli as tomllib


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "scripts").is_dir() and (parent / "tests").is_dir():
            return parent
    raise RuntimeError("repo root not found")


ROOT = _repo_root()
POLICY_PATH = ROOT / "contracts" / "process_throughput_policy.toml"
FINGERPRINT = "PROCESS-THROUGHPUT-RED: policy absent"

# --- anchored law (sealed 2026-07-22; the policy must agree with every anchor) ------

TOP_LEVEL_KEYS = {
    "meta", "predecessor", "blockers", "mechanical_correction", "design_gate",
    "family", "adjacent_findings", "executable_cutoff", "heartbeat", "artifacts",
    "worktree_closure", "budgets", "throughput_invariants", "fast_path", "record",
    "governed_docs", "transition_classes", "transitions",
}

CLASSES = [
    "PROBEABLE",
    "MECHANICAL_IDENTITY",
    "STRUCTURAL_PREREQUISITE",
    "ENVIRONMENT_CAPABILITY",
    "POLICY_AUTHORITY",
]

SEATS = {
    "conductor": "/root",
    "design_red_author": "fable",
    "green_builder": "opus",
    "reviewer": "codex",
}

FOUR_BLOCKERS = [
    "BEHAVIOR_AMBIGUITY",
    "WRITE_CUSTODY_UNSAFE",
    "AUTHORITY_UNRESOLVED",
    "RED_INVALID",
]

FIVE_CONDITIONS = [
    "AUTHORITY_DETERMINES_BYTES",
    "NO_NEW_BEHAVIOR_OR_AUTHORITY",
    "WRITE_PATH_AUTHORIZED_AND_UNCONFLICTED",
    "DETERMINISTIC_VALIDATOR_PROVES",
    "INDEPENDENCE_AND_RED_PRESERVED",
]

FORBIDDEN_ROUTES = [
    "NEW_DESIGN_FAMILY", "NEW_REVIEW_LIFECYCLE", "REVIEW_OF_REVIEW", "PACKET_OF_PACKET",
]

INVALIDATING_KINDS = ["SAFETY", "AUTHORITY", "SCOPE", "RED_PROOF", "GREEN_INTENT"]
NONBLOCKING_REQUIRES = ["stable_id", "transition_class", "disposition", "retrigger"]

EXECUTABLE_OWNERS = ["CARRIER_VALIDATOR", "BEHAVIOR_RED", "NAMED_MUTANT_KILL", "PROOF_COMMAND"]
PROSE_RETURN_REASONS = ["ENCODES_WRONG_BEHAVIOR", "ENCODES_WRONG_AUTHORITY"]

NON_INSTANTIATING = [
    "TYPO", "PACKET_CORRECTION", "VALIDATOR_COMPLAINT", "REVIEW_COMMENT",
    "MECHANICAL_CORRECTION",
]
PASS_OUTCOMES = [
    "SLICE_ADVANCED", "NEW_EXECUTABLE_CLAIM", "BLOCKER_CLOSED", "EXTERNAL_BLOCKER_REPORTED",
]

ARTIFACT_FIELDS = ["consumer", "blocker_removed", "enabled_transition"]

RECOVERY_REFS = ["BRANCH", "COMMIT", "PATCH_HASH", "FOLD_RECEIPT"]
VALID_RETENTION = ["AWAITING_SPECIFIC_EXTERNAL_GATE", "CI_BRANCH_POLICY"]

NEVER_BUDGETS = ["SILENCE", "ELAPSED_TIME", "TOKENS", "CONTEXT", "OUTPUT_VOLUME"]

FAST_GATES = [
    "ADMISSION", "RIGHT_REASON_RED", "RED_CONFORMANCE",
    "FINAL_CODE_ADVERSARIAL_REVIEW", "PROOF", "RECORD",
]

TI_PROPOSITIONS = {
    "TI-1": "Once the real blockers are cleared and RED conformance passes, the next state "
            "is builder execution, not another design or packet review.",
    "TI-2": "Every new governance artifact must name its immediate consumer, the blocker it "
            "removes, and the lifecycle transition it enables; if it enables none, do not "
            "create it.",
    "TI-3": "A slice has one design family and one RED family; corrections update those "
            "stable families in place and preserve lineage.",
    "TI-4": "Review does not recursively govern its own carrier; deterministic carrier "
            "defects are corrected and validated directly.",
    "TI-5": "Repeating the same semantic review without new counterevidence is not progress "
            "and cannot reset the review count.",
    "TI-6": "Each heartbeat pass must advance the slice, produce a newly executable claim, "
            "close a named blocker, or report a concrete external blocker and recovery "
            "condition.",
    "TI-7": "Audit completeness never authorizes indefinite delay after safety, authority, "
            "scope, and proof admission are satisfied.",
    "TI-8": "The conductor keeps the number of live write worktrees to the work that is "
            "actually executing or awaiting a specific external gate; parallel alternative "
            "answers do not remain open for convenience.",
}
TI_IDS = list(TI_PROPOSITIONS)

# Predecessor identities: at-authorship (frozen while this RED was written) and the
# deterministic post-fold identities the lawful same-slice re-pin must produce.
PRED_POLICY_PATH = "contracts/process_docs_currency_policy.toml"
PRED_RED_PATH = "tests/contracts/test_process_docs_currency.py"
PRED_PATCH_SHA = "13640c3c4b5d40cc149e8a7aefd218f85590d578f8bd9794396a3f63e3755e5b"
PRED_POLICY_SHA_AT_AUTHORSHIP = "b1845d77e86c4b713dc945336235da8cefcd250add918702daddde9102d76b80"
PRED_RED_SHA_AT_AUTHORSHIP = "2e58986f6e60ab8d948aadc39c58431152da5b288c2b495568a91496a5f3141a"
POST_FOLD = {
    "policy": "8c066cdb74b1e9472c00fa54faa936e6c747141b83f8b5cd28022c3d48b18196",
    "red": "c198fd6634f0cca9dce4b61450bb02d7cff743d244a6c00bd527c5fb35bfb2e7",
    "agents": "e66e8609f38db272756f6604f631907e28dfa7a7b8153610b65858efe65f9e06",
    "active": "cac57cd1812034a84d277bb7d44af0c9dd20ec7f7a8058a001db8e49e5d8d393",
}

PRED_CASE_NAMES = [
    "test_adoption_pins_match_sealed_authority_bytes",
    "test_authoritative_documents_enumerated_and_current",
    "test_conformance_requires_immediate_distinct_opus_successor",
    "test_each_finding_has_exactly_one_class",
    "test_historical_records_exempt_not_rewritten",
    "test_live_docs_forbid_stale_conductor_patterns",
    "test_plan_ledger_prefix_immutable_and_adoption_row_appended",
    "test_policy_schema_is_closed",
    "test_proc_findings_are_red_authored_immediate",
    "test_proc_transitions_bind_to_real_red_cases",
    "test_red_author_cannot_build_green",
    "test_rename_and_correction_preserve_terminal_lineage",
    "test_reviewer_cannot_author_red",
    "test_roles_and_seats_are_the_ratified_law",
    "test_skill_files_point_to_agents_authority",
    "test_skill_findings_are_red_required_after_lane_c",
    "test_skill_owns_no_competing_lifecycle",
    "test_third_prose_review_rejected",
    "test_transition_classes_are_the_agents_enum",
    "test_transition_totality_exact_twelve_findings",
]

LEDGER_PATH = "docs/history/PLAN-LEDGER.md"
LEDGER_HEADING = "## 2026-07-22 — finite execution + throughput amendment (process law)"
LEDGER_PREFIX_SHA = "83b351f84fcc4668088bae0e7adf2a103515e03c3afc478a2d9072b890359a44"
LEDGER_PREFIX_BYTES = 7988

AGENTS_SOP_ANCHOR = "The slice SOP — the full 13-step ritual"

AMENDMENT_CORPUS_SHA = "c36c41d8e7f341f9e8797a698de8c825a6a500e6a1606fb32fa98a495724c0f9"
CHARTER_PATH = "scratchpad/active/process/fable-process-throughput-design-red-charter-r1.txt"
CHARTER_SHA = "33b75c7f56019b59695392dfa6623b9b9b546577bcf59cc2a6eebc804e6162b9"
DESIGN_PATH = "scratchpad/active/process/process-throughput-amendment-design-r1.md"
AMENDMENT_SOURCE = (
    "SEMANTIC-TDD-PROCESS-CORPUS.md#proposed-finite-execution-and-throughput-amendment"
)
FOREIGN_TOKENS = ("semproof", "make prove", "12-row", "cargo")

GOVERNED_DOC_PROPS = {
    "AGENTS.md": [
        "### Finite execution and throughput law",
        "only four blockers stop pre-GREEN work",
        "all five mechanical conditions hold",
        "fixed in place and deterministically validated",
        "one bounded design gate, only for genuine semantic or authority ambiguity",
        "only an invalidating adjacent finding",
        "disagreement resolves against executable evidence",
        "The 13-step slice SOP governs the whole slice, never each correction inside it.",
        "release the lane and retire the source worktree",
        "never substantive-work budgets",
        "`contracts/process_throughput_policy.toml`",
    ],
    "docs/plans/ACTIVE.md": [
        "only the four real blockers stop pre-GREEN work",
        "mechanical corrections fix in place under `contracts/process_throughput_policy.toml`",
        "folded lanes retire their worktrees",
    ],
    "docs/plans/handoff/HANDOFF.md": [
        "mechanical corrections fix in place and never open a new review lifecycle",
        "only invalidating findings block the builder",
        "folded worktrees retire",
    ],
    "skills/design-language-tdd/SKILL.md": [
        "mechanical carrier fixes are corrected in place under the throughput law",
    ],
    "skills/design-language-tdd/references/prove-theme.md": [
        "mechanical carrier fixes are corrected in place under the throughput law",
    ],
    "skills/design-language-tdd/references/add-component.md": [
        "mechanical carrier fixes are corrected in place under the throughput law",
    ],
}

RED_CLASS_PREFIX = "tests.contracts.test_process_throughput_law.ProcessThroughputLawRed."

RED_AUTHORED_EVIDENCE = {
    "THRU-SCOPE-001": "test_policy_schema_is_closed",
    "THRU-PRED-001": "test_predecessor_binding_and_repin_rule",
    "THRU-BASE-001": "test_only_four_real_blockers_block_pre_green",
    "THRU-MECH-001": "test_mechanical_correction_is_conjunctive",
    "THRU-GATE-001": "test_single_bounded_design_gate",
    "THRU-ADJ-001": "test_only_invalidating_adjacent_findings_block",
    "THRU-CUTOFF-001": "test_executable_cutoff_resolves_against_evidence",
    "THRU-HEARTBEAT-001": "test_heartbeat_governs_whole_slice_not_events",
    "THRU-ARTIFACT-001": "test_artifact_requires_consumer_blocker_transition",
    "THRU-WORKTREE-001": "test_worktree_retired_after_verified_fold",
    "THRU-INVARIANT-001": "test_eight_throughput_invariants_closed_and_total",
    "THRU-FASTPATH-001": "test_fast_path_finite_without_gate_bypass",
    "THRU-RECORD-001": "test_ledger_records_throughput_adoption",
    "THRU-TOTALITY-001": "test_transition_totality_exact_throughput_findings",
    "THRU-DOCFOLD-001": "test_live_docs_carry_throughput_law",
}

DISPOSITIONED_OWNERS = {
    "THRU-OBS-001": "fable",
    "THRU-OBS-003": "fable",
    "THRU-OBS-004": "/root",
}

ALL_FINDING_IDS = sorted(list(RED_AUTHORED_EVIDENCE) + list(DISPOSITIONED_OWNERS))


# --- deterministic validators (pure; consumed only with policy data + explicit input) --


def blocking_findings(findings, policy: dict) -> list:
    """Only the closed four real blockers block pre-GREEN; tampered tables refuse."""
    table = policy["blockers"]
    if table["pre_green_blocking"] != FOUR_BLOCKERS:
        raise ValueError("blocker table tampered: the four real blockers are closed law")
    if table["closed"] is not True or table["anything_else_blocks"] is not False:
        raise ValueError("blocker table tampered: closure flags are closed law")
    return [f for f in findings if f["kind"] in table["pre_green_blocking"]]


def mechanical_route(assessment: dict, policy: dict) -> str:
    """The five-condition mechanical test is conjunctive; routes never spawn lifecycles."""
    table = policy["mechanical_correction"]
    if table["conditions"] != FIVE_CONDITIONS:
        raise ValueError("mechanical conditions tampered: the five conditions are closed law")
    if table["all_required"] is not True:
        raise ValueError("mechanical test tampered: all five conditions are required")
    if set(assessment) != set(table["conditions"]):
        raise ValueError("mechanical assessment must answer exactly the five conditions")
    for value in assessment.values():
        if not isinstance(value, bool):
            raise ValueError("mechanical assessment answers must be booleans")
    route = table["pass_route"] if all(assessment.values()) else table["fail_route"]
    if route in table["forbidden_routes"]:
        raise ValueError(f"mechanical route may never spawn a lifecycle: {route}")
    return route


def design_gate_check(requests, policy: dict) -> list:
    """At most one bounded design gate, only for genuine semantic/authority ambiguity."""
    table = policy["design_gate"]
    violations = []
    if len(requests) > table["max_design_gates"]:
        violations.append("more than the one bounded design gate")
    for request in requests:
        if request["reason"] not in table["allowed_reasons"]:
            violations.append(
                f"design gate reason not a genuine ambiguity: {request['reason']}"
            )
    return violations


def adjacent_finding_gate(finding: dict, policy: dict) -> dict:
    """Only invalidating adjacent findings block; nonblocking ones must stay typed."""
    table = policy["adjacent_findings"]
    if table["nonblocking_blocks_builder"] is not False:
        raise ValueError("adjacent-finding law tampered: nonblocking findings never block")
    invalidates = finding.get("invalidates")
    if invalidates is not None:
        if invalidates not in table["invalidating_kinds"]:
            raise ValueError(f"unknown invalidation kind: {invalidates}")
        return {"builder_blocked": True, "violations": []}
    violations = []
    for field in table["nonblocking_requires"]:
        if not finding.get(field):
            violations.append(f"nonblocking finding missing {field}")
    classes = policy["transition_classes"]["classes"]
    if finding.get("transition_class") and finding["transition_class"] not in classes:
        violations.append("nonblocking finding class outside the AGENTS enum")
    return {"builder_blocked": False, "violations": violations}


def cutoff_route(claim: dict, challenge: dict, policy: dict) -> str:
    """Executable claims resolve against executable evidence, not prose."""
    table = policy["executable_cutoff"]
    owner = claim.get("executable_owner")
    if owner is None:
        return "NOT_YET_EXECUTABLE"
    if owner not in table["executable_owners"]:
        raise ValueError(f"unknown executable owner kind: {owner}")
    if challenge.get("demonstrates") in table["prose_return_reasons"]:
        return "PROSE_RETURN_AUTHORIZED"
    return table["resolve_against"]


def red_repair_ledger(events, policy: dict) -> list:
    """A weak RED returns to its author at most once; no review-of-review, ever."""
    table = policy["executable_cutoff"]
    allowed = {
        "RED_RETURNED_TO_AUTHOR", "REVIEW_OF_REVIEW", "CARRIER_VALIDATOR_FAILED",
        "RED_ACCEPTED", "GREEN_DISPATCH",
    }
    violations = []
    returns = 0
    for kind, data in events:
        if kind not in allowed:
            raise ValueError(f"unknown repair event: {kind}")
        if kind == "RED_RETURNED_TO_AUTHOR":
            returns += 1
        elif kind == "REVIEW_OF_REVIEW":
            violations.append("review-of-review is never a lawful state")
        elif kind == "CARRIER_VALIDATOR_FAILED":
            if data.get("route") != table["validator_failure_route"]:
                violations.append(
                    "a carrier validator failure must route DIRECT_CORRECTION, got "
                    f"{data.get('route')}"
                )
    if returns > table["red_repair_returns_max"]:
        violations.append("the RED may return to its author at most once")
    return violations


def heartbeat_check(events, policy: dict) -> list:
    """One 13-step SOP instance governs the whole slice; carrier events never recurse."""
    table = policy["heartbeat"]
    allowed = {"SOP_INSTANTIATED", "HEARTBEAT_PASS"} | set(table["non_instantiating_events"])
    violations = []
    instances: dict = {}
    for kind, data in events:
        if kind not in allowed:
            raise ValueError(f"unknown heartbeat event: {kind}")
        if kind == "SOP_INSTANTIATED":
            slice_id = data["slice"]
            instances[slice_id] = instances.get(slice_id, 0) + 1
            if instances[slice_id] > 1:
                violations.append(
                    f"more than one SOP instance for slice {slice_id}: the SOP governs "
                    "the whole slice"
                )
            if data.get("caused_by") in table["non_instantiating_events"]:
                violations.append(
                    f"a {data['caused_by']} event may never instantiate a new SOP cycle"
                )
        elif kind == "HEARTBEAT_PASS":
            if data.get("outcome") not in table["required_pass_outcomes"]:
                violations.append(
                    f"a heartbeat pass must advance the slice, got {data.get('outcome')}"
                )
    return violations


def artifact_admissible(artifact: dict, policy: dict) -> list:
    """No consumer, no removed blocker, no enabled transition => no artifact."""
    table = policy["artifacts"]
    if table["create_without_all"] is not False:
        raise ValueError("artifact law tampered: all three fields are required")
    return [
        f"artifact missing {field}"
        for field in table["required_fields"]
        if not artifact.get(field)
    ]


def worktree_closure_check(record: dict, policy: dict) -> list:
    """After verified fold + recorded recovery, the lane releases and the worktree retires."""
    table = policy["worktree_closure"]
    if table["alternate_answer_retention"] is not False:
        raise ValueError("closure law tampered: alternate-answer retention is never lawful")
    if not (record.get("folded_verified") and record.get("recovery_recorded")):
        return []
    violations = []
    if not record.get("worktree_retired"):
        reason = record.get("retention_reason")
        if reason not in table["valid_retention_reasons"]:
            violations.append(f"worktree retained after verified fold: {reason}")
    if not record.get("lane_released"):
        violations.append("lane lease not released after verified fold")
    return violations


def lifecycle_authority_check(decision: dict, policy: dict) -> list:
    """Silence/time/tokens/context/output are never lifecycle authority or budgets."""
    table = policy["budgets"]
    if table["budget_is_lifecycle_authority"] is not False:
        raise ValueError("budget law tampered: budgets are never lifecycle authority")
    if decision.get("justified_by") in table["never_budgets"]:
        return [
            "lifecycle decision justified by a non-authority budget signal: "
            f"{decision['justified_by']}"
        ]
    return []


def fast_path_check(events, policy: dict) -> list:
    """The fast path is finite but bypasses no gate; only `/root` integrates."""
    table = policy["fast_path"]
    if table["bypassable"] is not False:
        raise ValueError("fast-path law tampered: gates are not bypassable")
    allowed = set(table["required_gates"]) | {"INTEGRATION", "DELAY_FOR_AUDIT_COMPLETENESS"}
    violations = []
    seen: list = []
    admission_seen = False
    integration_at = None
    for index, (kind, data) in enumerate(events):
        if kind not in allowed:
            raise ValueError(f"unknown fast-path event: {kind}")
        if kind == "ADMISSION":
            admission_seen = True
        if kind == "DELAY_FOR_AUDIT_COMPLETENESS" and admission_seen:
            violations.append(
                "audit completeness never authorizes delay after admission is satisfied"
            )
        if kind == "INTEGRATION":
            integration_at = index
            if data.get("actor") != table["integration_authority"]:
                violations.append(
                    f"integration/commit authority is /root only, got {data.get('actor')}"
                )
        seen.append(kind)
    if integration_at is None:
        violations.append("no integration event: the fast path did not complete")
    else:
        before = set(seen[:integration_at])
        for gate in table["required_gates"]:
            if gate not in before:
                violations.append(f"gate bypassed before integration: {gate}")
    return violations


def throughput_doc_scan(policy: dict, rel_path: str, text: str) -> list:
    """Every governed live surface must carry its folded throughput propositions."""
    rows = {d["path"]: d for d in policy["governed_docs"]}
    row = rows.get(rel_path)
    if row is None:
        return [f"undeclared governed doc: {rel_path}"]
    return [
        f"{rel_path}: required proposition absent: {proposition!r}"
        for proposition in row["required_propositions"]
        if proposition not in text
    ]


class ProcessThroughputLawRed(unittest.TestCase):
    """23 cases; each fails with the bootstrap fingerprint until GREEN lands the policy."""

    maxDiff = None

    def setUp(self) -> None:
        if not POLICY_PATH.is_file():
            self.fail(FINGERPRINT)
        self.policy = tomllib.loads(POLICY_PATH.read_text(encoding="utf-8"))

    # --- schema, scope, and predecessor binding -----------------------------------

    def test_policy_schema_is_closed(self) -> None:
        self.assertEqual(set(self.policy), TOP_LEVEL_KEYS)
        meta = self.policy["meta"]
        self.assertEqual(meta["contract_id"], "ProcessThroughputPolicy")
        self.assertEqual(meta["schema_version"], 1)
        self.assertEqual(meta["ratified"], "2026-07-22")
        self.assertEqual(meta["amendment_source"], AMENDMENT_SOURCE)
        self.assertEqual(meta["amendment_corpus_sha256"], AMENDMENT_CORPUS_SHA)
        self.assertEqual(meta["charter"], CHARTER_PATH)
        self.assertEqual(meta["charter_sha256"], CHARTER_SHA)
        self.assertEqual(meta["authority_doc"], "AGENTS.md")
        self.assertEqual(meta["design"], DESIGN_PATH)
        raw = POLICY_PATH.read_text(encoding="utf-8")
        low = raw.lower()
        for token in FOREIGN_TOKENS:
            self.assertNotIn(
                token, low,
                f"foreign (semantic-tdd-side) authority token imported: {token!r}",
            )
        self.assertIsNone(
            re.search(r"\bBOOT\b", raw),
            "the semantic-tdd BOOT ritual is not JGUIDA law",
        )
        self.assertNotIn(
            "CONSTELLATION-SPLIT-RECOVERY-PLAN", raw,
            "the recovery plan is cross-repo candidate evidence, never a law source",
        )

    def test_predecessor_binding_and_repin_rule(self) -> None:
        pred = self.policy["predecessor"]
        self.assertEqual(pred["policy_path"], PRED_POLICY_PATH)
        self.assertEqual(pred["contract_id"], "ProcessDocsCurrencyPolicy")
        self.assertEqual(pred["red_path"], PRED_RED_PATH)
        self.assertEqual(pred["canonical_patch_sha256"], PRED_PATCH_SHA)
        self.assertEqual(pred["policy_sha256_at_authorship"], PRED_POLICY_SHA_AT_AUTHORSHIP)
        self.assertEqual(pred["red_sha256_at_authorship"], PRED_RED_SHA_AT_AUTHORSHIP)
        repin = pred["repin"]
        self.assertIn("actual predecessor commit SHA", repin)
        self.assertIn("deterministic re-pin only", repin)
        self.assertIn("never a new design/review family", repin)
        self.assertTrue((ROOT / pred["policy_path"]).is_file())
        self.assertTrue((ROOT / pred["red_path"]).is_file())

    def test_predecessor_law_repinned_not_weakened(self) -> None:
        pred = self.policy["predecessor"]
        self.assertEqual(pred["policy_sha256_post_fold"], POST_FOLD["policy"])
        self.assertEqual(pred["red_sha256_post_fold"], POST_FOLD["red"])
        self.assertEqual(pred["agents_post_fold_sha256"], POST_FOLD["agents"])
        self.assertEqual(pred["active_post_fold_sha256"], POST_FOLD["active"])
        live = {
            "policy": hashlib.sha256((ROOT / PRED_POLICY_PATH).read_bytes()).hexdigest(),
            "red": hashlib.sha256((ROOT / PRED_RED_PATH).read_bytes()).hexdigest(),
            "agents": hashlib.sha256((ROOT / "AGENTS.md").read_bytes()).hexdigest(),
            "active": hashlib.sha256(
                (ROOT / "docs" / "plans" / "ACTIVE.md").read_bytes()
            ).hexdigest(),
        }
        self.assertEqual(
            live, POST_FOLD,
            "the lawful deterministic re-pin must produce exactly the precomputed "
            "post-fold bytes — anything else weakened or forked the predecessor law",
        )
        currency = tomllib.loads((ROOT / PRED_POLICY_PATH).read_text(encoding="utf-8"))
        rows = {d["path"]: d for d in currency["currency"]["documents"]}
        self.assertEqual(rows["AGENTS.md"]["adoption_sha256"], POST_FOLD["agents"])
        self.assertEqual(rows["docs/plans/ACTIVE.md"]["adoption_sha256"], POST_FOLD["active"])
        from tests.contracts import test_process_docs_currency as pred_mod

        names = sorted(
            name
            for name in dir(pred_mod.ProcessDocsCurrencyRed)
            if name.startswith("test_")
        )
        self.assertEqual(
            names, sorted(PRED_CASE_NAMES),
            "the predecessor's 20 currentness cases must survive byte-for-byte in "
            "name and count — the re-pin substitutes two hash literals, nothing else",
        )
        self.assertEqual(len(names), 20)

    # --- the practical base case: four real blockers ------------------------------

    def test_only_four_real_blockers_block_pre_green(self) -> None:
        table = self.policy["blockers"]
        self.assertEqual(table["pre_green_blocking"], FOUR_BLOCKERS)
        self.assertIs(table["closed"], True)
        self.assertIs(table["anything_else_blocks"], False)
        for kind in FOUR_BLOCKERS:
            blocking = blocking_findings([{"kind": kind}], self.policy)
            self.assertEqual(
                [{"kind": kind}], blocking, f"{kind} must block pre-GREEN on its own"
            )
        for kind in ("AUDIT_INCOMPLETE", "MORE_DESIGN_DESIRED", "ADJACENT_STYLE_FINDING"):
            self.assertEqual(
                [], blocking_findings([{"kind": kind}], self.policy),
                f"{kind} is not one of the four real blockers and must not block",
            )
        self.assertEqual([], blocking_findings([], self.policy))

    def test_four_blockers_not_weakened(self) -> None:
        dropped = copy.deepcopy(self.policy)
        dropped["blockers"]["pre_green_blocking"] = FOUR_BLOCKERS[:-1]
        with self.assertRaises(ValueError):
            blocking_findings([], dropped)
        opened = copy.deepcopy(self.policy)
        opened["blockers"]["closed"] = False
        with self.assertRaises(ValueError):
            blocking_findings([], opened)
        widened = copy.deepcopy(self.policy)
        widened["blockers"]["anything_else_blocks"] = True
        with self.assertRaises(ValueError):
            blocking_findings([], widened)

    # --- the five-condition mechanical-correction test ----------------------------

    def test_mechanical_correction_is_conjunctive(self) -> None:
        table = self.policy["mechanical_correction"]
        self.assertEqual(table["conditions"], FIVE_CONDITIONS)
        self.assertIs(table["all_required"], True)
        self.assertEqual(table["pass_route"], "FIX_IN_PLACE_VALIDATE_RESUME")
        self.assertEqual(table["fail_route"], "CLASSIFY_ACTUAL_BLOCKER")
        all_true = {condition: True for condition in FIVE_CONDITIONS}
        self.assertEqual(
            "FIX_IN_PLACE_VALIDATE_RESUME", mechanical_route(all_true, self.policy)
        )
        for condition in FIVE_CONDITIONS:
            assessment = dict(all_true, **{condition: False})
            self.assertEqual(
                "CLASSIFY_ACTUAL_BLOCKER", mechanical_route(assessment, self.policy),
                f"a single failed condition ({condition}) must break the mechanical route",
            )
        with self.assertRaises(ValueError):
            missing = dict(all_true)
            missing.pop(FIVE_CONDITIONS[0])
            mechanical_route(missing, self.policy)
        with self.assertRaises(ValueError):
            mechanical_route(dict(all_true, EXTRA_CONDITION=True), self.policy)
        weakened = copy.deepcopy(self.policy)
        weakened["mechanical_correction"]["all_required"] = False
        with self.assertRaises(ValueError):
            mechanical_route(all_true, weakened)

    def test_mechanical_route_never_spawns_lifecycle(self) -> None:
        table = self.policy["mechanical_correction"]
        self.assertEqual(table["forbidden_routes"], FORBIDDEN_ROUTES)
        all_true = {condition: True for condition in FIVE_CONDITIONS}
        one_false = dict(all_true, DETERMINISTIC_VALIDATOR_PROVES=False)
        for assessment in (all_true, one_false):
            self.assertNotIn(mechanical_route(assessment, self.policy), FORBIDDEN_ROUTES)
        hostile = copy.deepcopy(self.policy)
        hostile["mechanical_correction"]["pass_route"] = "NEW_DESIGN_FAMILY"
        with self.assertRaises(ValueError):
            mechanical_route(all_true, hostile)

    # --- one bounded design gate; successor law stays with the predecessor --------

    def test_single_bounded_design_gate(self) -> None:
        gate = self.policy["design_gate"]
        self.assertEqual(gate["max_design_gates"], 1)
        self.assertEqual(gate["allowed_reasons"], ["SEMANTIC_AMBIGUITY", "AUTHORITY_AMBIGUITY"])
        family = self.policy["family"]
        self.assertEqual(family["family_id"], "process-throughput-amendment")
        self.assertEqual(family["design_families_max"], 1)
        self.assertEqual(family["red_families_max"], 1)
        self.assertEqual(family["corrections"], "IN_PLACE_PRESERVE_LINEAGE")
        self.assertEqual([], design_gate_check([], self.policy))
        self.assertEqual(
            [], design_gate_check([{"reason": "SEMANTIC_AMBIGUITY"}], self.policy)
        )
        two_gates = design_gate_check(
            [{"reason": "SEMANTIC_AMBIGUITY"}, {"reason": "AUTHORITY_AMBIGUITY"}],
            self.policy,
        )
        self.assertTrue(any("more than the one bounded" in v for v in two_gates))
        carrier = design_gate_check([{"reason": "MECHANICAL_CARRIER_DEFECT"}], self.policy)
        self.assertTrue(any("not a genuine ambiguity" in v for v in carrier))

    def test_design_gate_successor_parity_with_predecessor(self) -> None:
        for key in ("roles", "separation", "successor", "lineage"):
            self.assertNotIn(
                key, self.policy,
                f"one-definition rule: {key!r} law lives in the predecessor policy only",
            )
        gate = self.policy["design_gate"]
        self.assertEqual(gate["successor_authority"], PRED_POLICY_PATH)
        self.assertEqual(
            gate["after_gate_sequence"],
            ["DISTINCT_RED_AUTHOR", "RED_CONFORMANCE_CHECK", "GREEN_DISPATCH"],
        )
        currency = tomllib.loads((ROOT / PRED_POLICY_PATH).read_text(encoding="utf-8"))
        self.assertEqual(currency["roles"], SEATS)
        successor = currency["successor"]
        self.assertEqual(successor["max_conformance_checks"], 1)
        self.assertEqual(successor["required_next_event"], "GREEN_DISPATCH")
        self.assertEqual(successor["green_builder"], "opus")
        self.assertEqual(
            successor["forbidden_after_red_accepted"], ["PROSE_REVIEW", "REVIEW_OF_REVIEW"]
        )
        lineage = currency["lineage"]
        self.assertEqual(lineage["prose_review_cap"], 2)
        self.assertEqual(lineage["reset_events"], [])

    # --- adjacent findings: conserved, typed, and only invalidating ones block ----

    def test_only_invalidating_adjacent_findings_block(self) -> None:
        table = self.policy["adjacent_findings"]
        self.assertEqual(table["invalidating_kinds"], INVALIDATING_KINDS)
        self.assertEqual(table["nonblocking_requires"], NONBLOCKING_REQUIRES)
        self.assertIs(table["nonblocking_blocks_builder"], False)
        for kind in INVALIDATING_KINDS:
            verdict = adjacent_finding_gate({"invalidates": kind}, self.policy)
            self.assertTrue(verdict["builder_blocked"], kind)
        styling = {
            "invalidates": None,
            "stable_id": "THRU-EX-001",
            "transition_class": "MECHANICAL_IDENTITY",
            "disposition": "recorded; scheduled",
            "retrigger": "next slice touching the surface",
        }
        verdict = adjacent_finding_gate(styling, self.policy)
        self.assertFalse(verdict["builder_blocked"])
        self.assertEqual([], verdict["violations"])
        hostile = copy.deepcopy(self.policy)
        hostile["adjacent_findings"]["nonblocking_blocks_builder"] = True
        with self.assertRaises(ValueError):
            adjacent_finding_gate(styling, hostile)

    def test_nonblocking_adjacent_finding_must_be_conserved_and_typed(self) -> None:
        complete = {
            "invalidates": None,
            "stable_id": "THRU-EX-002",
            "transition_class": "PROBEABLE",
            "disposition": "typed and scheduled",
            "retrigger": "when the adjacent surface is next opened",
        }
        self.assertEqual([], adjacent_finding_gate(complete, self.policy)["violations"])
        for field in NONBLOCKING_REQUIRES:
            partial = dict(complete)
            partial.pop(field)
            verdict = adjacent_finding_gate(partial, self.policy)
            self.assertFalse(
                verdict["builder_blocked"],
                "conservation violations still never block the builder",
            )
            self.assertTrue(
                any(field in violation for violation in verdict["violations"]),
                f"dropping {field} must be a conservation violation",
            )

    # --- executable cutoff and the bounded RED repair -----------------------------

    def test_executable_cutoff_resolves_against_evidence(self) -> None:
        table = self.policy["executable_cutoff"]
        self.assertEqual(table["executable_owners"], EXECUTABLE_OWNERS)
        self.assertEqual(table["resolve_against"], "EXECUTABLE_EVIDENCE")
        self.assertEqual(table["prose_return_reasons"], PROSE_RETURN_REASONS)
        for owner in EXECUTABLE_OWNERS:
            self.assertEqual(
                "EXECUTABLE_EVIDENCE",
                cutoff_route(
                    {"executable_owner": owner}, {"demonstrates": None}, self.policy
                ),
                f"a {owner}-owned claim resolves against its evidence, never prose",
            )
        self.assertEqual(
            "PROSE_RETURN_AUTHORIZED",
            cutoff_route(
                {"executable_owner": "BEHAVIOR_RED"},
                {"demonstrates": "ENCODES_WRONG_BEHAVIOR"},
                self.policy,
            ),
        )
        self.assertEqual(
            "PROSE_RETURN_AUTHORIZED",
            cutoff_route(
                {"executable_owner": "CARRIER_VALIDATOR"},
                {"demonstrates": "ENCODES_WRONG_AUTHORITY"},
                self.policy,
            ),
        )
        self.assertEqual(
            "EXECUTABLE_EVIDENCE",
            cutoff_route(
                {"executable_owner": "PROOF_COMMAND"},
                {"demonstrates": "STYLE_PREFERENCE"},
                self.policy,
            ),
            "a non-authority complaint never reopens prose",
        )
        self.assertEqual(
            "NOT_YET_EXECUTABLE",
            cutoff_route({"executable_owner": None}, {"demonstrates": None}, self.policy),
        )
        with self.assertRaises(ValueError):
            cutoff_route({"executable_owner": "VIBES"}, {"demonstrates": None}, self.policy)

    def test_red_repair_bounded_once_no_review_of_review(self) -> None:
        table = self.policy["executable_cutoff"]
        self.assertEqual(table["validator_failure_route"], "DIRECT_CORRECTION")
        self.assertEqual(table["red_repair_returns_max"], 1)
        one_return = (
            ("RED_RETURNED_TO_AUTHOR", {}),
            ("RED_ACCEPTED", {}),
            ("GREEN_DISPATCH", {}),
        )
        self.assertEqual([], red_repair_ledger(one_return, self.policy))
        two_returns = (
            ("RED_RETURNED_TO_AUTHOR", {}),
            ("RED_RETURNED_TO_AUTHOR", {}),
        )
        self.assertTrue(
            any("at most once" in v for v in red_repair_ledger(two_returns, self.policy))
        )
        meta_review = (("REVIEW_OF_REVIEW", {}),)
        self.assertTrue(
            any(
                "review-of-review" in v
                for v in red_repair_ledger(meta_review, self.policy)
            )
        )
        direct = (("CARRIER_VALIDATOR_FAILED", {"route": "DIRECT_CORRECTION"}),)
        self.assertEqual([], red_repair_ledger(direct, self.policy))
        detoured = (("CARRIER_VALIDATOR_FAILED", {"route": "NEW_REVIEW"}),)
        self.assertTrue(
            any(
                "DIRECT_CORRECTION" in v
                for v in red_repair_ledger(detoured, self.policy)
            )
        )

    # --- the heartbeat governs the whole slice ------------------------------------

    def test_heartbeat_governs_whole_slice_not_events(self) -> None:
        table = self.policy["heartbeat"]
        self.assertEqual(table["sop_source"], "AGENTS.md")
        self.assertEqual(table["sop_steps"], 13)
        self.assertEqual(table["scope"], "SLICE")
        self.assertEqual(table["non_instantiating_events"], NON_INSTANTIATING)
        self.assertEqual(table["required_pass_outcomes"], PASS_OUTCOMES)
        agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn(
            AGENTS_SOP_ANCHOR, agents_text,
            "the policy's SOP source must be the live 13-step ritual in AGENTS.md",
        )
        one_slice = [
            ("SOP_INSTANTIATED", {"slice": "s1"}),
            ("TYPO", {}),
            ("PACKET_CORRECTION", {}),
            ("VALIDATOR_COMPLAINT", {}),
            ("REVIEW_COMMENT", {}),
            ("MECHANICAL_CORRECTION", {}),
            ("HEARTBEAT_PASS", {"slice": "s1", "outcome": "SLICE_ADVANCED"}),
        ]
        self.assertEqual([], heartbeat_check(one_slice, self.policy))
        recursed = one_slice + [("SOP_INSTANTIATED", {"slice": "s1", "caused_by": "TYPO"})]
        violations = heartbeat_check(recursed, self.policy)
        self.assertTrue(any("whole slice" in v for v in violations), violations)
        self.assertTrue(
            any("never instantiate" in v for v in violations),
            "a typo may never instantiate a new SOP cycle",
        )
        prose_pass = [
            ("SOP_INSTANTIATED", {"slice": "s2"}),
            ("HEARTBEAT_PASS", {"slice": "s2", "outcome": "MORE_PROSE_PRODUCED"}),
        ]
        self.assertTrue(
            any("must advance" in v for v in heartbeat_check(prose_pass, self.policy))
        )

    # --- artifact consumer law ----------------------------------------------------

    def test_artifact_requires_consumer_blocker_transition(self) -> None:
        table = self.policy["artifacts"]
        self.assertEqual(table["required_fields"], ARTIFACT_FIELDS)
        self.assertIs(table["create_without_all"], False)
        lawful = {
            "consumer": "the Opus GREEN builder",
            "blocker_removed": "no executable law exists",
            "enabled_transition": "RED-conformance -> GREEN_DISPATCH",
        }
        self.assertEqual([], artifact_admissible(lawful, self.policy))
        for field in ARTIFACT_FIELDS:
            orphan = dict(lawful)
            orphan.pop(field)
            self.assertTrue(
                any(field in v for v in artifact_admissible(orphan, self.policy)),
                f"an artifact without {field} is forbidden to create",
            )
            empty = dict(lawful, **{field: ""})
            self.assertTrue(
                any(field in v for v in artifact_admissible(empty, self.policy))
            )

    # --- worktree retirement ------------------------------------------------------

    def test_worktree_retired_after_verified_fold(self) -> None:
        table = self.policy["worktree_closure"]
        self.assertEqual(table["after"], ["VERIFIED_FOLD", "RECOVERY_RECORDED"])
        self.assertIs(table["release_lane"], True)
        self.assertIs(table["retire_worktree"], True)
        self.assertEqual(table["recovery_refs"], RECOVERY_REFS)
        self.assertEqual(table["valid_retention_reasons"], VALID_RETENTION)
        self.assertIs(table["alternate_answer_retention"], False)
        retired = {
            "folded_verified": True, "recovery_recorded": True,
            "lane_released": True, "worktree_retired": True, "retention_reason": None,
        }
        self.assertEqual([], worktree_closure_check(retired, self.policy))
        for reason in ("ALTERNATE_ANSWER", "BACKUP_CONVENIENCE", "PATCH_HASH_EXISTS"):
            hoarded = dict(retired, worktree_retired=False, retention_reason=reason)
            self.assertTrue(
                any("retained after verified fold" in v
                    for v in worktree_closure_check(hoarded, self.policy)),
                f"{reason} is recovery-or-convenience, never retention authority",
            )
        gated = dict(
            retired, worktree_retired=False,
            retention_reason="AWAITING_SPECIFIC_EXTERNAL_GATE",
        )
        self.assertEqual([], worktree_closure_check(gated, self.policy))
        unreleased = dict(retired, lane_released=False)
        self.assertTrue(
            any("lease not released" in v
                for v in worktree_closure_check(unreleased, self.policy))
        )
        not_yet_folded = {
            "folded_verified": False, "recovery_recorded": False,
            "lane_released": False, "worktree_retired": False, "retention_reason": None,
        }
        self.assertEqual([], worktree_closure_check(not_yet_folded, self.policy))

    # --- the eight invariants and the no-budget law -------------------------------

    def test_eight_throughput_invariants_closed_and_total(self) -> None:
        rows = self.policy["throughput_invariants"]
        self.assertEqual([row["id"] for row in rows], TI_IDS)
        self.assertEqual(len(rows), 8)
        for row in rows:
            self.assertEqual(
                row["proposition"], TI_PROPOSITIONS[row["id"]],
                f"{row['id']}: the invariant proposition is closed law, byte-exact",
            )
        dropped = copy.deepcopy(self.policy)
        dropped["throughput_invariants"].pop()
        self.assertNotEqual(
            [row["id"] for row in dropped["throughput_invariants"]], TI_IDS,
            "a dropped invariant row must be detectable",
        )

    def test_no_inferred_work_budgets(self) -> None:
        table = self.policy["budgets"]
        self.assertEqual(table["never_budgets"], NEVER_BUDGETS)
        self.assertIs(table["budget_is_lifecycle_authority"], False)
        for signal in NEVER_BUDGETS:
            self.assertTrue(
                any(
                    signal in violation
                    for violation in lifecycle_authority_check(
                        {"justified_by": signal}, self.policy
                    )
                ),
                f"{signal} is never lifecycle authority or a substantive-work budget",
            )
        self.assertEqual(
            [],
            lifecycle_authority_check(
                {"justified_by": "EXPLICIT_TERMINAL_RESULT"}, self.policy
            ),
        )
        hostile = copy.deepcopy(self.policy)
        hostile["budgets"]["budget_is_lifecycle_authority"] = True
        with self.assertRaises(ValueError):
            lifecycle_authority_check({"justified_by": "SILENCE"}, hostile)

    # --- the fast path is finite but bypasses nothing -----------------------------

    def test_fast_path_finite_without_gate_bypass(self) -> None:
        table = self.policy["fast_path"]
        self.assertEqual(table["required_gates"], FAST_GATES)
        self.assertEqual(table["integration_authority"], "/root")
        self.assertIs(table["bypassable"], False)
        lawful = [(gate, {}) for gate in FAST_GATES] + [
            ("INTEGRATION", {"actor": "/root"})
        ]
        self.assertEqual([], fast_path_check(lawful, self.policy))
        for gate in FAST_GATES:
            bypassed = [(kind, {}) for kind in FAST_GATES if kind != gate] + [
                ("INTEGRATION", {"actor": "/root"})
            ]
            self.assertTrue(
                any(gate in v for v in fast_path_check(bypassed, self.policy)),
                f"the fast path may never skip {gate}",
            )
        for actor in ("fable", "opus"):
            usurped = [(gate, {}) for gate in FAST_GATES] + [
                ("INTEGRATION", {"actor": actor})
            ]
            self.assertTrue(
                any(
                    "/root only" in v
                    for v in fast_path_check(usurped, self.policy)
                ),
                f"{actor} may never integrate or commit",
            )
        delayed = [("ADMISSION", {}), ("DELAY_FOR_AUDIT_COMPLETENESS", {})] + [
            (gate, {}) for gate in FAST_GATES if gate != "ADMISSION"
        ] + [("INTEGRATION", {"actor": "/root"})]
        self.assertTrue(
            any(
                "never authorizes delay" in v
                for v in fast_path_check(delayed, self.policy)
            )
        )

    # --- typed transitions: closed, total, real -----------------------------------

    def test_transition_totality_exact_throughput_findings(self) -> None:
        self.assertEqual(self.policy["transition_classes"]["classes"], CLASSES)
        rows = self.policy["transitions"]
        ids = [row["finding_id"] for row in rows]
        self.assertEqual(sorted(ids), ALL_FINDING_IDS)
        self.assertEqual(len(ids), 18)
        self.assertEqual(len(set(ids)), 18, "each finding is classified exactly once")
        by_id = {row["finding_id"]: row for row in rows}
        for finding_id, row in by_id.items():
            self.assertIn(row["transition_class"], CLASSES, finding_id)
        for finding_id in RED_AUTHORED_EVIDENCE:
            row = by_id[finding_id]
            self.assertEqual(row["transition_class"], "PROBEABLE", finding_id)
            self.assertEqual(row["status"], "RED_AUTHORED", finding_id)
            self.assertEqual(row["dependency"], "IMMEDIATE", finding_id)
            self.assertEqual(row["owner_seat"], "fable", finding_id)
        for finding_id, owner in DISPOSITIONED_OWNERS.items():
            row = by_id[finding_id]
            self.assertEqual(row["transition_class"], "MECHANICAL_IDENTITY", finding_id)
            self.assertEqual(row["status"], "DISPOSITIONED", finding_id)
            self.assertEqual(row["dependency"], "ON_RETRIGGER", finding_id)
            self.assertEqual(row["owner_seat"], owner, finding_id)
            self.assertTrue(row.get("disposition"), f"{finding_id}: disposition required")
            self.assertTrue(row.get("retrigger"), f"{finding_id}: retrigger required")

    def test_transitions_bind_to_real_red_cases(self) -> None:
        by_id = {row["finding_id"]: row for row in self.policy["transitions"]}
        for finding_id, case_name in RED_AUTHORED_EVIDENCE.items():
            row = by_id.get(finding_id)
            self.assertIsNotNone(row, finding_id)
            self.assertEqual(row["evidence"], RED_CLASS_PREFIX + case_name, finding_id)
            self.assertTrue(
                callable(getattr(type(self), case_name, None)),
                f"{finding_id}: evidence case {case_name} must exist in this class",
            )
        red_authored = {
            row["finding_id"]
            for row in self.policy["transitions"]
            if row["status"] == "RED_AUTHORED"
        }
        self.assertEqual(red_authored, set(RED_AUTHORED_EVIDENCE))

    # --- durable record and the live-doc fold -------------------------------------

    def test_ledger_records_throughput_adoption(self) -> None:
        record = self.policy["record"]
        self.assertEqual(record["ledger_path"], LEDGER_PATH)
        self.assertEqual(record["required_heading"], LEDGER_HEADING)
        raw = (ROOT / LEDGER_PATH).read_bytes()
        self.assertGreaterEqual(len(raw), LEDGER_PREFIX_BYTES)
        self.assertEqual(
            hashlib.sha256(raw[:LEDGER_PREFIX_BYTES]).hexdigest(), LEDGER_PREFIX_SHA,
            "history was rewritten — the ledger accepts appends only",
        )
        self.assertIn(
            LEDGER_HEADING, raw.decode("utf-8"),
            "the throughput adoption row must be APPENDED to the ledger",
        )

    def test_live_docs_carry_throughput_law(self) -> None:
        rows = {d["path"]: d for d in self.policy["governed_docs"]}
        self.assertEqual(set(rows), set(GOVERNED_DOC_PROPS))
        for path, propositions in GOVERNED_DOC_PROPS.items():
            self.assertEqual(
                rows[path]["required_propositions"], propositions,
                f"{path}: the policy must require exactly the anchored propositions",
            )
            live = ROOT / path
            self.assertTrue(live.is_file(), f"governed doc missing from disk: {path}")
            text = live.read_text(encoding="utf-8")
            self.assertEqual(
                [], throughput_doc_scan(self.policy, path, text),
                f"{path}: the live surface must carry the folded throughput law",
            )
        undeclared = throughput_doc_scan(self.policy, "docs/UNDECLARED.md", "text")
        self.assertTrue(any("undeclared" in v for v in undeclared))
        canary = throughput_doc_scan(
            self.policy,
            "AGENTS.md",
            "Stale governing prose that never folded the finite-execution law.",
        )
        self.assertTrue(
            any("required proposition absent" in v for v in canary),
            "a governed surface without the folded law must redden",
        )


if __name__ == "__main__":
    unittest.main()

"""OrchestrationExchangePolicy adversarial RED bank (A13/A14 r9): review-to-RED fold, executable.

Fable-authored r9 fold of the controlling independent XHIGH Codex ADVERSARIAL review
(ADVERSARIAL-VERDICT: revise, 2026-07-19) into executable REDs: ADV-A13-001 (open-world
contradictory live role prose is accepted), ADV-A14-002 (dot/NUL/Windows/separator/ambiguous
exchange paths are accepted on artifact and receipt surfaces), ADV-A14-003 (duplicate edge and
receipt identities are accepted), ADV-CONV-004 (the convergence preflight is neither closed nor
exact and is bound to no sealed artifact), plus the typed executable obligation for the
disclosed tautological `or found` diagnostic debt (DEBT-A13A14-TAUT-005).

Seat law: this file is wholly Fable-frozen RED surface. GREEN may not edit THIS file; a diff
touching it is rejected whole. The predicates under test live in the r9 GREEN-writable zones of
tests/contracts/test_orchestration_exchange.py (the r7 bank), whose five Fable-frozen regions
FR-A..FR-E are hash-pinned by the r9 packet and probe bank. This module implements no predicate
fix: every test calls the live surface and states the law the fix must satisfy, with a required
diagnostic token per rejection class so a rejection can never pass for an unrelated reason.

The guard is record-internal and tracked-prose only: it never reads any path outside the
repository tree. Every test's FIRST assertion is the shared record-existence check, so a staged
run without the canonical record FAILs (never ERRORs) uniformly.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path


def _repo_root() -> Path:
    """Walk up to the dir holding both scripts/ and tests/ (depth-independent)."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "scripts").is_dir() and (parent / "tests").is_dir():
            return parent
    raise RuntimeError("repo root not found")


ROOT = _repo_root()
LIVE_MODULE_RELPATH = "tests/contracts/test_orchestration_exchange.py"
LIVE_MODULE_PATH = ROOT / "tests" / "contracts" / "test_orchestration_exchange.py"
RECORD_PATH = ROOT / "contracts" / "orchestration_exchange_policy.json"
MISSING_MSG = "record missing: contracts/orchestration_exchange_policy.json"

_spec = importlib.util.spec_from_file_location("a13a14_oxc_live", LIVE_MODULE_PATH)
oxc = importlib.util.module_from_spec(_spec)
sys.modules["a13a14_oxc_live"] = oxc
_spec.loader.exec_module(oxc)

# Required diagnostic tokens (the corrected GREEN predicates must name each rejection class):
TOKEN_ROLE = "live-role-contradiction"
TOKEN_PATH = "path-lexical-law"
TOKEN_DUP = "duplicate-identity"
TOKEN_CONV = "convergence-closure"

# --- ADV-A13-001: open-world contradictory live role prose --------------------------------------
# Every vector is a permissive seat/capability assertion whose (actor, capability) pair is
# unlawful under the typed seat law; none matches the frozen 15-phrase literal blacklist, and at
# r9 every one of them is ACCEPTED verbatim by all_doc_violations on all three routing docs.
ROLE_CONTRADICTION_VECTORS = [
    ("V-A13-FABLE-CONDUCT", "Fable is the sole conductor."),
    ("V-A13-OPUS-REVIEW", "Opus may review and approve CODE and ADVERSARIAL gates."),
    ("V-A13-CODEX-IMPLEMENT", "Codex implements GREEN changes."),
    ("V-A13-ROOT-AUTHOR-RED", "/root may author REDs."),
    ("V-A13-OPUS-CONDUCT", "Opus conducts every dispatch."),
    ("V-A13-CODEX-COMMIT", "Codex commits the reviewed patch."),
    ("V-A13-FABLE-IMPLEMENT", "Fable implements the GREEN tier."),
    ("V-A13-FABLE-SELF-APPROVE", "Fable may approve its own artifact."),
    ("V-A13-ROOT-IMPLEMENT", "/root implements corrections directly."),
    ("V-A13-ROOT-REVIEW-VERDICT", "/root reviews and issues the final verdict."),
    ("V-A13-ROOT-DESIGN", "/root designs the next slice."),
    ("V-A13-OPUS-DESIGN", "Opus designs the next slice."),
    ("V-A13-OPUS-AUTHOR-RED", "Opus authors the RED bank."),
    ("V-A13-OPUS-PUSH", "Opus pushes the landing commit to main."),
    ("V-A13-CODEX-CONDUCT", "Codex conducts the orchestration."),
    ("V-A13-CODEX-DESIGN", "Codex designs slice boundaries."),
    ("V-A13-CODEX-AUTHOR-RED", "Codex may author REDs."),
    ("V-A13-CODEX-MERGE", "Codex merges approved patches."),
    ("V-A13-FABLE-COMMIT", "Fable stages and commits its own artifact."),
    ("V-A13-ROOT-AUTHOR-RED-2", "/root authors the executable REDs."),
]
# Lawful/negated sentences that must STAY violation-free before and after GREEN (the
# false-positive fence: the fix must be a seat-capability law, not a word blacklist).
LAWFUL_ROLE_FENCES = [
    "`/root` conducts every dispatch.",
    "Fable authors the executable REDs.",
    "Fable designs the slice boundaries.",
    "Opus implements every GREEN tier.",
    "Codex reviews the exact final patch.",
    "`/root` integrates and commits after both final approvals.",
    "Opus never reviews.",
    "Codex may not implement.",
    "The conductor NEVER designs, authors REDs, implements, or issues review verdicts.",
]

# --- ADV-A14-002: lexical path law over artifact + proof + review receipt paths -----------------
PATH_VECTORS = [
    ("V-PATH-DOT", "."),
    ("V-PATH-DOT-PREFIX", "./candidate.json"),
    ("V-PATH-DOT-SEGMENT", "exports/./candidate.json"),
    ("V-PATH-NUL", "exports/\x00nul.json"),
    ("V-PATH-BACKSLASH-TRAVERSAL", "..\\escape.json"),
    ("V-PATH-WINDOWS-ABSOLUTE", "C:\\temp\\candidate.json"),
    ("V-PATH-DRIVE-FORWARD", "C:/temp/candidate.json"),
    ("V-PATH-BACKSLASH-SEPARATOR", "exports\\candidate.json"),
    ("V-PATH-EMPTY-SEGMENT", "exports//candidate.json"),
    ("V-PATH-TRAILING-SLASH", "exports/candidate.json/"),
    ("V-PATH-LEADING-SPACE", " exports/candidate.json"),
    ("V-PATH-INTERIOR-SPACE", "exports/candidate .json"),
]
PATH_SURFACES = ("artifact_path", "proof_receipts", "review_receipts")
# Lawful multi-segment paths that must STAY accepted (the fix may not over-close to one segment).
PATH_FENCES = [
    ("artifact_path", "exports/sub/dir/deep-artifact.json"),
    ("proof_receipts", "receipts/sub/proof-deep.json"),
    ("review_receipts", "receipts/sub/review-deep.md"),
]


def _edge_with(surface: str, path: str) -> dict:
    edge = copy.deepcopy(oxc.VALID_EDGE_FIXTURE)
    if surface == "artifact_path":
        edge["artifact_path"] = path
    elif surface == "proof_receipts":
        edge["proof_receipts"] = [{"path": path, "sha256": "d" * 64}]
    else:
        edge["review_receipts"] = [{"path": path, "sha256": "e" * 64}]
    return edge


# --- ADV-CONV-004: closed/exact convergence bound to the sealed artifact ------------------------
# The canonical convergence projection, frozen HERE as an independent deep literal (never
# imported), and hash-bound: the sealed r9 packet's design_gate must equal this object
# byte-for-byte under canonical JSON (probe P-CONV-PACKET), and the live module's
# CONVERGENCE_FIXTURE must equal it structurally (asserted below). Canonical form is
# json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) in UTF-8.
PROJECTION_CANONICAL_SHA256 = "94750a81c2ad497d69aebdc4c3f4a0ebfc5e39b096d9231e52c0633d62e75388"
_R1_REVIEW_SHA = "18e4a2fdb0d53230e4e8165fa1bbb16ebd1d9e6359d6de5d1be56eb010918f29"
_R1_ROLLOUT_SHA = "6a7e19bfd8cb6f3f641fa11138ee22cedee77376a4db0614470abe8858b8b5cf"
_R2_REVIEW_SHA = "006ae480be9fd274b344887e8903e1e630194b7a92e49868228e7bcc5d47153a"
_R2_ROLLOUT_SHA = "7f2bed0548c21318dcbedc86cc39dba741e1952325fd4b92804bb44c4eabf546"
FROZEN_CONVERGENCE_PROJECTION = {
    "binding_state": "lawful-two-revise-convergence",
    "convergence_law": (
        "after two REVISE rounds on the same artifact, remaining findings convert to executable "
        "REDs/probes and move to the build phase; Codex then reviews code and executable "
        "output, never another prose restatement"
    ),
    "revise_rounds": [
        {"round": 1,
         "review_path": "scratchpad/active/bootstrap/a13-a14-codex-design-review-r1.md",
         "review_sha256": _R1_REVIEW_SHA, "rollout_sha256": _R1_ROLLOUT_SHA,
         "verdict": "REVISE", "effort": "max-grandfathered"},
        {"round": 2,
         "review_path": "scratchpad/active/bootstrap/a13-a14-codex-design-delta-review-r2.md",
         "review_sha256": _R2_REVIEW_SHA, "rollout_sha256": _R2_ROLLOUT_SHA,
         "verdict": "REVISE", "effort": "xhigh"},
    ],
    "finding_map": {
        "R1-CURRENTNESS-001": {"disposition": "closed-covered",
                               "executable": ["test_w7_and_retirement_pinned",
                                              "M-GRANDFATHER-FORGED"]},
        "R1-EFFORT-002": {"disposition": "closed-partial-to-R2-LIVE-RULE-001",
                          "executable": ["test_no_stale_seat_text", "M-REVIEW-EFFORT-DRIFT",
                                         "M-REVIEW-LAW-DOWNGRADE"]},
        "R1-GUARD-EDGE-003A": {"disposition": "closed-partial-to-R2-EDGE-SHAPE-002",
                               "executable": ["test_edge_fixture_positive",
                                              "test_edge_hostile_vectors_all_fire"]},
        "R1-GUARD-EVIDENCE-003B": {"disposition": "closed-covered",
                                   "executable": ["test_evidence_rows_wellformed",
                                                  "M-EVIDENCE-ROW-DELETED",
                                                  "M-PRECEDENCE-WEAKENED",
                                                  "M-FRAGMENT-MISMATCH"]},
        "R1-GUARD-CODEX-003C": {"disposition": "closed-covered",
                                "executable": ["reviewer_never-exact-set", "M-CODEX-CONDUCTS",
                                               "M-CODEX-PUSHES"]},
        "R1-FOLD-SCOPE-004": {"disposition": "closed-partial-to-R2-FOLD-SCOPE-003",
                              "executable": ["test_fold_scope_preserved", "M-FOLD-SCOPE-EATEN"]},
        "R1-RED-STAGING-005": {"disposition": "closed-covered",
                               "executable": ["red-observation-r7-step1",
                                              "red-observation-r7-step2"]},
        "R1-MEASURED-FACTS-006": {"disposition": "closed-covered",
                                  "executable": ["M-FRAGMENT-MISMATCH",
                                                 "rb-sha256sums-row-counts"]},
        "R1-PROBE-GIT-007": {"disposition": "closed-reverified",
                             "executable": ["packet-V-steps", "r7-session-verification"]},
        "R1-PROBE-JSONL-008": {"disposition": "closed-reverified",
                               "executable": ["evidence-rows-pinned"]},
        "R1-PROBE-BANK-009": {"disposition": "closed-reverified",
                              "executable": ["evidence-rows-pinned", "M-EVIDENCE-ROW-DELETED"]},
        "R1-PROBE-PROJECTION-010": {"disposition": "closed-partial-to-R2-LIVE-RULE-001",
                                    "executable": ["PROBE-R2-LIVE-RULE-001"]},
        "R1-PROBE-WRITABLE-011": {"disposition": "closed-as-precondition",
                                  "executable": ["packet-V0-V1-stop-rule"]},
        "R1-PROBE-SCOPE-012": {"disposition": "closed-reverified",
                               "executable": ["packet-closed-paths"]},
        "ERR-R2-ABBR-01": {"disposition": "non-actionable-presentation-erratum",
                           "executable": ["packet-full-value-pins"]},
        "ERR-R2-ABBR-02": {"disposition": "non-actionable-presentation-erratum",
                           "executable": ["packet-full-value-pins"]},
        "ERR-R2-ABBR-03": {"disposition": "non-actionable-presentation-erratum",
                           "executable": ["packet-full-value-pins"]},
        "R2-LIVE-RULE-001": {"disposition": "open-red-required",
                             "executable": ["test_no_live_rule_contradiction",
                                            "PROBE-R2-LIVE-RULE-001", "M-A4-UNCHANGED-LAW-1",
                                            "M-A4-UNCHANGED-LAW-2", "M-A4-UNCHANGED-LAW-3"]},
        "R2-EDGE-SHAPE-002": {"disposition": "open-red-required",
                              "executable": ["test_edges_container_fail_closed",
                                             "PROBE-R2-EDGE-SHAPE-002", "M-EDGES-NOT-LIST",
                                             "V-EDGE-NONOBJECT"]},
        "R2-FOLD-SCOPE-003": {"disposition": "open-red-required",
                              "executable": ["test_later_fold_clauses_exact",
                                             "PROBE-R2-FOLD-SCOPE-003",
                                             "M-FOLD-CLAUSE-DROPPED-1",
                                             "M-FOLD-CLAUSE-DROPPED-2",
                                             "M-FOLD-CLAUSE-DROPPED-3",
                                             "M-FOLD-CLAUSE-DROPPED-4"]},
        "R2-CONVERGENCE-PACKET-004": {"disposition": "open-probe-required",
                                      "executable": ["test_convergence_packet_fixture",
                                                     "PROBE-R2-CONVERGENCE-PACKET-004",
                                                     "M-CONVERGENCE-REQUIRES-APPROVE"]},
        "R2-OPUS-REVIEW-AUTHORITY-005": {"disposition": "open-red-required",
                                         "executable": ["test_no_opus_review_standin_mapping",
                                                        "PROBE-R2-OPUS-REVIEW-AUTHORITY-005",
                                                        "M-OPUS-REVIEW-STANDIN"]},
    },
    "approving_design_verdict": None,
    "third_prose_design_review_permitted": False,
}


def _canonical_sha256(obj: object) -> str:
    payload = json.dumps(obj, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _set_law(gate: dict) -> None:
    gate["convergence_law"] = gate["convergence_law"] + " (as amended)"


CONVERGENCE_CLOSURE_ARMS = [
    ("V-CONV-EXTRA-TOP-KEY", lambda g: g.update(audit_note="reviewed")),
    ("V-CONV-NESTED-APPROVAL-OBJ", lambda g: g.update(audit={"verdict": "APPROVE"})),
    ("V-CONV-NESTED-APPROVAL-LIST", lambda g: g.update(history=[{"verdict": "APPROVE"}])),
    ("V-CONV-VERDICT-FIELD-REMOVED", lambda g: g.pop("approving_design_verdict")),
    ("V-CONV-LAW-REMOVED", lambda g: g.pop("convergence_law")),
    ("V-CONV-LAW-APPROVE", lambda g: g.update(convergence_law="APPROVE")),
    ("V-CONV-LAW-REWORDED", _set_law),
    ("V-CONV-ROUND1-PATH-REMOVED", lambda g: g["revise_rounds"][0].pop("review_path")),
    ("V-CONV-ROUND1-PATH-FORGED",
     lambda g: g["revise_rounds"][0].update(
         review_path="scratchpad/active/bootstrap/forged-review.md")),
    ("V-CONV-ROUND2-EFFORT-REMOVED", lambda g: g["revise_rounds"][1].pop("effort")),
    ("V-CONV-ROUND2-EFFORT-DOWNGRADED", lambda g: g["revise_rounds"][1].update(effort="high")),
    ("V-CONV-ROUND2-EXTRA-APPROVAL-FIELD",
     lambda g: g["revise_rounds"][1].update(supplemental_verdict="APPROVE")),
    ("V-CONV-EXTRA-FINDING-ID",
     lambda g: g["finding_map"].update({"ADV-FAKE-999": {
         "disposition": "closed-covered",
         "executable": ["test_record_exists_and_shape_closed"]}})),
    ("V-CONV-FINDING-EXTRA-APPROVAL-FIELD",
     lambda g: g["finding_map"]["R2-LIVE-RULE-001"].update(approval="granted")),
    ("V-CONV-DISPOSITION-APPROVE",
     lambda g: g["finding_map"]["R2-LIVE-RULE-001"].update(disposition="APPROVE")),
    ("V-CONV-EXECUTABLE-REFS-ARBITRARY",
     lambda g: g["finding_map"]["R2-LIVE-RULE-001"].update(
         executable=["design-verdict-approve-record"])),
]

# --- import contract over the GREEN-writable live surface ---------------------------------------
IMPORT_CONTRACT_CALLABLES = (
    "record_violations", "edge_violations", "evidence_violations", "doc_violations",
    "live_rule_conflict_violations", "opus_review_authority_violations", "all_doc_violations",
    "convergence_packet_violations", "_load_record", "_doc_texts",
)
SINGLE_BINDING_CONSTANTS = (
    "VALID_EDGE_FIXTURE", "MANDATORY_FINDING_IDS", "CONVERGENCE_FIXTURE", "RECORD_MUTANTS",
    "DOC_MUTANTS", "HOSTILE_EDGE_VECTORS",
)
SINGLE_DEF_FUNCTIONS = (
    "edge_violations", "evidence_violations", "record_violations", "doc_violations",
    "live_rule_conflict_violations", "opus_review_authority_violations", "all_doc_violations",
    "convergence_packet_violations", "_load_record", "_doc_texts",
)
FILE_TERMINAL = 'if __name__ == "__main__":\n    unittest.main()\n'


class AdversarialFoldRedBank(unittest.TestCase):
    maxDiff = None

    def _require_record(self) -> dict:
        self.assertTrue(RECORD_PATH.is_file(), MISSING_MSG)
        return oxc._load_record()

    # R9-1 (ADV-A13-001)
    def test_adv_a13_001_contradictory_role_prose_rejected(self) -> None:
        record = self._require_record()
        texts = oxc._doc_texts()
        self.assertEqual(oxc.all_doc_violations(record, texts), [],
                         "baseline: the REAL live docs must stay violation-free")
        for fence in LAWFUL_ROLE_FENCES:
            for doc in texts:
                with self.subTest(fence=fence, doc=doc):
                    mutated = dict(texts)
                    mutated[doc] = texts[doc] + "\n" + fence + "\n"
                    self.assertEqual(
                        oxc.all_doc_violations(record, mutated), [],
                        f"fence: lawful sentence must never be flagged in {doc}: {fence!r}")
        for vid, sentence in ROLE_CONTRADICTION_VECTORS:
            for doc in texts:
                with self.subTest(vector=vid, doc=doc):
                    mutated = dict(texts)
                    mutated[doc] = texts[doc] + "\n" + sentence + "\n"
                    found = oxc.all_doc_violations(record, mutated)
                    self.assertNotEqual(
                        found, [],
                        f"{vid}: contradictory role prose ACCEPTED in {doc}: {sentence!r} "
                        "(ADV-A13-001: the live-role boundary must be a seat-capability law, "
                        "not a literal blacklist)")
                    self.assertTrue(
                        any(TOKEN_ROLE in viol for viol in found),
                        f"{vid}: no violation names {TOKEN_ROLE!r}: {found}")
                    self.assertTrue(
                        any(doc in viol for viol in found),
                        f"{vid}: no violation names the offending doc {doc}: {found}")

    # R9-2 (ADV-A14-002)
    def test_adv_a14_002_path_lexical_law(self) -> None:
        record = self._require_record()
        exch = record["exchange_law"]
        self.assertEqual(oxc.edge_violations(copy.deepcopy(oxc.VALID_EDGE_FIXTURE), exch), [],
                         "baseline: the valid fixture must stay violation-free")
        for surface, fence_path in PATH_FENCES:
            with self.subTest(fence=surface, path=fence_path):
                self.assertEqual(
                    oxc.edge_violations(_edge_with(surface, fence_path), exch), [],
                    f"fence: lawful nested {surface} path must stay accepted: {fence_path!r}")
        for pid, bad in PATH_VECTORS:
            for surface in PATH_SURFACES:
                with self.subTest(vector=pid, surface=surface):
                    found = oxc.edge_violations(_edge_with(surface, bad), exch)
                    self.assertNotEqual(
                        found, [],
                        f"{pid}: hostile path ACCEPTED on {surface}: {bad!r} (ADV-A14-002: "
                        "dot/NUL/Windows/separator/ambiguous forms must be lexically rejected "
                        "on artifact, proof-receipt, and review-receipt surfaces)")
                    self.assertTrue(
                        any(TOKEN_PATH in viol for viol in found),
                        f"{pid}/{surface}: no violation names {TOKEN_PATH!r}: {found}")

    # R9-3 (ADV-A14-003)
    def test_adv_a14_003_duplicate_identity_law(self) -> None:
        record = self._require_record()
        exch = record["exchange_law"]
        fx = oxc.VALID_EDGE_FIXTURE

        def _second_edge() -> dict:
            e = copy.deepcopy(fx)
            e["edge_id"] = "fixture-edge-2"
            e["artifact_path"] = "exports/candidate-artifact-2.json"
            e["artifact_sha256"] = "f" * 64
            e["proof_receipts"] = [{"path": "receipts/proof-2.json", "sha256": "d" * 64}]
            e["review_receipts"] = [{"path": "receipts/review-2.md", "sha256": "e" * 64}]
            return e

        fence_record = copy.deepcopy(record)
        fence_record["exchange_law"]["edges"] = [copy.deepcopy(fx), _second_edge()]
        self.assertEqual(oxc.record_violations(fence_record), [],
                         "fence: two DISTINCT valid edges must stay accepted")
        fence_edge = copy.deepcopy(fx)
        fence_edge["proof_receipts"] = [
            {"path": "receipts/proof.json", "sha256": "d" * 64},
            {"path": "receipts/proof-b.json", "sha256": "d" * 64},
        ]
        self.assertEqual(oxc.edge_violations(fence_edge, exch), [],
                         "fence: two DISTINCT-path receipt rows must stay accepted")

        def _rec(mutate) -> list:
            mutant = copy.deepcopy(record)
            mutate(mutant)
            return oxc.record_violations(mutant)

        def _edg(mutate) -> list:
            edge = copy.deepcopy(fx)
            mutate(edge)
            return oxc.edge_violations(edge, exch)

        conflict = _second_edge()
        conflict["edge_id"] = fx["edge_id"]
        dup_arms = [
            ("V-DUP-EDGE-ID-IDENTICAL", _rec(lambda r: r["exchange_law"].update(
                edges=[copy.deepcopy(fx), copy.deepcopy(fx)]))),
            ("V-DUP-EDGE-ID-CONFLICT", _rec(lambda r: r["exchange_law"].update(
                edges=[copy.deepcopy(fx), conflict]))),
            ("V-DUP-PROOF-ROW", _edg(lambda e: e.update(proof_receipts=[
                {"path": "receipts/proof.json", "sha256": "d" * 64},
                {"path": "receipts/proof.json", "sha256": "d" * 64}]))),
            ("V-DUP-REVIEW-ROW", _edg(lambda e: e.update(review_receipts=[
                {"path": "receipts/review.md", "sha256": "e" * 64},
                {"path": "receipts/review.md", "sha256": "e" * 64}]))),
            ("V-DUP-PROOF-PATH-DIGEST-CONFLICT", _edg(lambda e: e.update(proof_receipts=[
                {"path": "receipts/proof.json", "sha256": "d" * 64},
                {"path": "receipts/proof.json", "sha256": "a" * 64}]))),
            ("V-DUP-REVIEW-PATH-DIGEST-CONFLICT", _edg(lambda e: e.update(review_receipts=[
                {"path": "receipts/review.md", "sha256": "e" * 64},
                {"path": "receipts/review.md", "sha256": "a" * 64}]))),
            ("V-DUP-CROSS-KIND-PATH", _edg(lambda e: e.update(review_receipts=[
                {"path": "receipts/proof.json", "sha256": "e" * 64}]))),
        ]
        for label, found in dup_arms:
            with self.subTest(arm=label):
                self.assertNotEqual(
                    found, [],
                    f"{label}: duplicate identity ACCEPTED (ADV-A14-003: edge_id values must "
                    "be unique and a receipt path may appear at most once across the union of "
                    "an edge's proof and review receipt rows)")
                self.assertTrue(
                    any(TOKEN_DUP in viol for viol in found),
                    f"{label}: no violation names {TOKEN_DUP!r}: {found}")

    # R9-4 (ADV-CONV-004)
    def test_adv_conv_004_convergence_closure(self) -> None:
        self._require_record()
        cpv = oxc.convergence_packet_violations
        self.assertEqual(_canonical_sha256(FROZEN_CONVERGENCE_PROJECTION),
                         PROJECTION_CANONICAL_SHA256,
                         "projection self-integrity: the frozen canonical projection drifted")
        self.assertEqual(oxc.CONVERGENCE_FIXTURE, FROZEN_CONVERGENCE_PROJECTION,
                         "the live CONVERGENCE_FIXTURE must equal the hash-bound canonical "
                         "projection exactly (ADV-CONV-004 binding half)")
        self.assertEqual(cpv(copy.deepcopy(FROZEN_CONVERGENCE_PROJECTION)), [],
                         "the lawful two-REVISE canonical projection must stay accepted")
        for label, mutate in CONVERGENCE_CLOSURE_ARMS:
            with self.subTest(arm=label):
                gate = copy.deepcopy(FROZEN_CONVERGENCE_PROJECTION)
                mutate(gate)
                found = cpv(gate)
                self.assertNotEqual(
                    found, [],
                    f"{label}: non-canonical convergence gate ACCEPTED (ADV-CONV-004: the "
                    "preflight must be closed and exact — top-level, round, finding-map, "
                    "disposition, evidence-reference, path, effort, and convergence-law "
                    "closure, with approval-bearing fields rejected everywhere)")
                self.assertTrue(
                    any(TOKEN_CONV in viol for viol in found),
                    f"{label}: no violation names {TOKEN_CONV!r}: {found}")

    # R9-5 (DEBT-A13A14-TAUT-005)
    def test_mutant_aspect_tokens_strict(self) -> None:
        record = self._require_record()
        self.assertEqual(oxc.record_violations(record), [],
                         "baseline: the REAL record must be violation-free")
        self.assertEqual(len(oxc.RECORD_MUTANTS), 52)
        self.assertEqual(sum(len(arms) for _, _, arms in oxc.RECORD_MUTANTS), 62)
        for name, token, arms in oxc.RECORD_MUTANTS:
            for i, arm in enumerate(arms):
                with self.subTest(mutant=name, arm=i):
                    mutant = copy.deepcopy(record)
                    arm(mutant)
                    found = oxc.record_violations(mutant)
                    self.assertNotEqual(found, [], f"{name} arm {i} did not fire")
                    self.assertTrue(
                        any(token in viol for viol in found),
                        f"{name} arm {i}: no violation names its exact table token {token!r} "
                        "(strict aspect law, DEBT-A13A14-TAUT-005: the r7 'or found' escape "
                        f"does not apply in this bank): {found}")

    # R9-6 (frozen-surface import contract; guard, green today and forever)
    def test_green_surface_import_contract(self) -> None:
        self._require_record()
        for name in IMPORT_CONTRACT_CALLABLES:
            self.assertTrue(callable(getattr(oxc, name, None)),
                            f"live surface must export callable {name}")
        self.assertIsInstance(oxc.VALID_EDGE_FIXTURE, dict)
        self.assertIsInstance(oxc.CONVERGENCE_FIXTURE, dict)
        self.assertEqual(len(oxc.MANDATORY_FINDING_IDS), 22)
        self.assertEqual(len(oxc.RECORD_MUTANTS), 52)
        self.assertEqual(sum(len(arms) for _, _, arms in oxc.RECORD_MUTANTS), 62)
        self.assertEqual(len(oxc.DOC_MUTANTS), 6)
        self.assertEqual(len(oxc.HOSTILE_EDGE_VECTORS), 15)
        src = LIVE_MODULE_PATH.read_text(encoding="utf-8")
        for cname in SINGLE_BINDING_CONSTANTS:
            self.assertEqual(
                len(re.findall(rf"^{cname} = ", src, flags=re.M)), 1,
                f"{cname} must be bound exactly once in the live module (no rebinding after "
                "a frozen region)")
        for fname in SINGLE_DEF_FUNCTIONS:
            self.assertEqual(
                len(re.findall(rf"^def {fname}\(", src, flags=re.M)), 1,
                f"{fname} must be defined exactly once in the live module")
        for fname in SINGLE_DEF_FUNCTIONS:
            self.assertEqual(
                len(re.findall(rf"^{fname} = ", src, flags=re.M)), 0,
                f"{fname} must never be rebound by a top-level assignment (frozen-surface "
                "law: GREEN edits each definition in place and never shadows it)")
        self.assertEqual(
            len(re.findall(r"^class OrchestrationExchangeContract\(", src, flags=re.M)), 1)
        self.assertTrue(src.endswith(FILE_TERMINAL),
                        "frozen region FR-E must terminate the live module (nothing may be "
                        "appended after the r7 test class)")


if __name__ == "__main__":
    unittest.main()

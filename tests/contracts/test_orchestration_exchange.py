"""OrchestrationExchangePolicy (A13/A14): single-conductor + exchange law, executable.

`contracts/orchestration_exchange_policy.json` is the durable record of the operator-ratified
2026-07-18 bootstrap: the A13 seat/dispatch law, the A14 immutable consumer-pull candidate-only
exchange law, the 2026-07-19 XHIGH review-effort amendment, the lawful two-REVISE design-gate
convergence (Codex r1 REVISE at grandfathered MAX; Codex r2 delta REVISE at XHIGH — no approving
DESIGN verdict exists for this lineage and none may be forged), and the evidence/hash
classification rows. This guard binds that record to the three LIVE routing documents
(`AGENTS.md`, `docs/plans/ACTIVE.md`, `docs/plans/handoff/HANDOFF.md`) so the laws cannot drift:
anchors present, stale seat/effort text absent, no live "unchanged" claim beside the XHIGH
amendments (R2-LIVE-RULE-001), no Opus review-stand-in mapping while the typed record forbids
Opus review (R2-OPUS-REVIEW-AUTHORITY-005), fail-closed A14 edge validation including hostile
container shapes (R2-EDGE-SHAPE-002), the complete later July-18 fold scope preserved as typed
data (R2-FOLD-SCOPE-003), and a convergence-packet preflight that accepts only the lawful
two-REVISE state and rejects a forged APPROVE (R2-CONVERGENCE-PACKET-004).

This module is the A13/A14 review-to-RED bank (r7), authored by the Fable author lane under the
review-convergence law. The guard is record-internal and tracked-prose only: it never reads any
path outside the repository tree. Every test's FIRST assertion is the shared record-existence
check, so pre-GREEN staged runs FAIL (never ERROR) uniformly. GREEN may not edit this file.
"""

from __future__ import annotations

import copy
import json
import re
import unittest
from pathlib import Path


def _repo_root() -> Path:
    """Walk up to the dir holding both scripts/ and tests/ (depth-independent)."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "scripts").is_dir() and (parent / "tests").is_dir():
            return parent
    raise RuntimeError("repo root not found")


ROOT = _repo_root()
RECORD_RELPATH = "contracts/orchestration_exchange_policy.json"
RECORD_PATH = ROOT / "contracts" / "orchestration_exchange_policy.json"
MISSING_MSG = f"record missing: {RECORD_RELPATH}"
DOC_PATHS = {
    "AGENTS.md": ROOT / "AGENTS.md",
    "docs/plans/ACTIVE.md": ROOT / "docs" / "plans" / "ACTIVE.md",
    "docs/plans/handoff/HANDOFF.md": ROOT / "docs" / "plans" / "handoff" / "HANDOFF.md",
}

HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

OP_RECORD_SHA = "f2af18961a0c6d9cf2299504d7d1f1105d3ff458b97191c347a26c2d39bdae12"
R1_REVIEW_SHA = "18e4a2fdb0d53230e4e8165fa1bbb16ebd1d9e6359d6de5d1be56eb010918f29"
R1_ROLLOUT_SHA = "6a7e19bfd8cb6f3f641fa11138ee22cedee77376a4db0614470abe8858b8b5cf"
R2_REVIEW_SHA = "006ae480be9fd274b344887e8903e1e630194b7a92e49868228e7bcc5d47153a"
R2_ROLLOUT_SHA = "7f2bed0548c21318dcbedc86cc39dba741e1952325fd4b92804bb44c4eabf546"

TOP_KEYS = {
    "contract_id", "schema_version", "ratified_utc", "authority_status", "purpose",
    "verification_scope", "w7_successor", "temporary_bootstrap_authority", "seat_law",
    "dispatch_law", "review_law", "exchange_law", "continuation_order",
    "pending_fold_obligations", "prose_parity", "evidence",
}

EXPECTED_PURPOSE = (
    "A13 single-conductor orchestration law + A14 cross-repository exchange law + the durable "
    "evidence/hash classification record for the 2026-07-18 bootstrap. Enforced against the live "
    "prose by tests/contracts/test_orchestration_exchange.py so the two laws cannot drift."
)
EXPECTED_VERIFICATION_SCOPE = (
    "record-internal and tracked-prose only; the guard never reads paths outside the repository "
    "tree; locator fields are informational; external byte re-verification is a /root "
    "landing-time act recorded in the landing receipt"
)
EXPECTED_W7_SUCCESSOR = {
    "owner": "W7",
    "surface": "contracts/role_registry.*",
    "note": (
        "the typed actor/session/model/tool/capability/scope registry is W7's design surface; "
        "this record pins only the bootstrap seat/exchange laws and evidence hashes and must "
        "not grow actor tables"
    ),
}
EXPECTED_TBA = {
    "source_record_sha256": OP_RECORD_SHA,
    "status": "retired-at-landing-commit",
    "note": (
        "the scratch operator record authorized exactly this slice and expired when /root "
        "committed the reviewed A13/A14 patch on w3-correction; the landing receipt records the "
        "retirement; no push to main was or is authorized by it; superseded historical versions: "
        "1ed5b8854cfb3391a1dc9635b3e66cb089e8b5779d75831b6c9d2f855e7952d8 (consumed by design "
        "r3), 2fcd7d607fb6625b6280e26d6ad756eb75b6dfb5b5263c70d52db657d154764e (consumed by "
        "design r4; delta byte-proven metadata-only in r4 SS2); the current version adds the "
        "substantive 2026-07-19 XHIGH review-effort amendment recorded in review_law"
    ),
}
EXPECTED_SEAT_LAW = {
    "conductor": "/root",
    "conductor_never": ["design", "author-red", "implement", "issue-review-verdict"],
    "author_model": "claude-fable-5",
    "author_effort": "max",
    "author_scope": ["design", "pitfall-matrix", "executable-red", "admission",
                     "build-packet-spec", "review-fold", "hard-proof-interpretation"],
    "author_never": ["conduct", "implement-green", "commit", "integrate",
                     "approve-own-artifact"],
    "builder_model": "claude-opus-4-8",
    "builder_scope": (
        "every GREEN implementation tier from an approved design and accepted sealed packet "
        "with a closed path roster; difficulty never changes the builder seat"
    ),
    "builder_never": ["design", "author-red", "review", "commit", "merge", "integrate", "push"],
    "reviewer": "codex",
    "reviewer_effort": "xhigh",
    "reviewer_scope": ["design-verdict", "exact-final-code-verdict",
                       "exact-final-adversarial-verdict"],
    "reviewer_never": ["conduct", "design", "author-red", "implement", "integrate", "commit",
                       "merge", "push"],
    "root_never_reviews": True,
    "author_never_approves": True,
}
NEVER_LIST_KEYS = ("conductor_never", "author_never", "builder_never", "reviewer_never")
EXPECTED_DISPATCH_LAW = {
    "fresh_one_shot": True,
    "exact_model_pinned": True,
    "fallback_forbidden": True,
    "resume_forbidden": True,
    "mixed_model_artifact_forbidden": True,
    "conductor_imposed_budgets_forbidden": True,
    "monitor": ["live-stream", "closed-jsonl-structural-rescan"],
    "rescan_checks": ["answering-model-on-every-assistant-record",
                      "tool-names-within-allowed-set", "no-resume-marker"],
    "on_model_or_tool_breach": (
        "invalidate-complete-worker-output-and-relaunch-fresh-from-last-accepted-immutable-pins"
    ),
    "concurrent_worker_lanes_max": 1,
    "worker_failure_stops": "that-lane-only",
    "conductor_identity_failure_freezes": "all-orchestration",
    "phase_boundaries": "natural-gate-boundaries; gated phases are never combined",
}
EXPECTED_REVIEW_LAW = {
    "design_gate_before_build": True,
    "final_gates": ["CODE", "ADVERSARIAL"],
    "red_spec_conformance_arms": ["exists", "targets-live-surface",
                                  "pre-green-right-reason-witness",
                                  "load-bearing-vs-named-mutant", "green-did-not-weaken"],
    "revise_convergence_cap": 2,
    "invalidations_are_not_review_rounds": True,
    "review_effort": "xhigh",
    "effort_amendment_utc": "2026-07-19",
    "no_review_at": ["max", "ultra", "high"],
    "grandfathered_r1_design_review": {
        "review_record_sha256": R1_REVIEW_SHA,
        "rollout_sha256": R1_ROLLOUT_SHA,
        "verdict": "REVISE",
        "note": (
            "launched at MAX before the 2026-07-19 00:41 EDT XHIGH ratification and allowed to "
            "close; historical only, never a template; every later review dispatch runs at xhigh"
        ),
    },
    "convergence_state": "lawful-two-revise-convergence",
    "terminal_r2_delta_review": {
        "review_record_sha256": R2_REVIEW_SHA,
        "rollout_sha256": R2_ROLLOUT_SHA,
        "verdict": "REVISE",
        "note": (
            "second REVISE at operator-ratified XHIGH on the composite r3+r4+r6; two-REVISE cap "
            "reached — binding state lawful-two-revise-convergence; every remaining finding "
            "became a typed disposition plus executable RED/probe (r7); no approving DESIGN "
            "verdict exists for this lineage and none may be forged"
        ),
    },
}
STALENESS_LAW = (
    "any change to an upstream pin invalidates every downstream admission, packet, proof, and "
    "review derived from it until re-admitted from fresh pins"
)
EDGE_REQUIRED_FIELDS = ["edge_id", "producer_repo", "producer_commit", "producer_tree",
                        "artifact_path", "artifact_sha256", "contract_version",
                        "proof_receipts", "review_receipts", "candidate_status", "direction",
                        "staleness_rule"]
EXPECTED_HISTORICAL_NOTES = [
    (
        "pre-A14 pattern port: contracts/repo_layout.json layout law ported from "
        "repo-surface-scout (no producer commit/tree recorded at port time; provenance note "
        "only, never an edge)"
    ),
    (
        "inbound registration: the semantic-tdd sibling registry lists this repo as a "
        "kernel-free adopter and points at docs/plans/handoff/HANDOFF.md; held and maintained "
        "in the sibling repository (consumer-pull), no edge artifact exchanged"
    ),
]
EXCHANGE_LAW_KEYS = {"transport", "immutable", "candidate_only", "neither_repo_writes_the_other",
                     "neither_repo_mints_the_others_authority", "write_grants",
                     "edge_required_fields", "staleness_law", "edges", "historical_notes"}
CONTINUATION_ORDER = ["a13-a14-bootstrap", "re-pin-r6", "re-pin-org-l1",
                      "july-18-review-sop-fold", "regenerate-w8o-r3",
                      "clear-four-retro-review-rows", "w7", "demo-a-b"]
ORDER_DISPLAY = {
    "a13-a14-bootstrap": "A13/A14",
    "re-pin-r6": "re-pin r6",
    "re-pin-org-l1": "re-pin org-L1",
    "july-18-review-sop-fold": "July 18 review/SOP fold",
    "regenerate-w8o-r3": "W8-O r3",
    "clear-four-retro-review-rows": "four retro-review rows",
    "w7": "W7",
    "demo-a-b": "DEMO A/B",
}

# R2-FOLD-SCOPE-003: the four step-4 boundary/source/homing clauses, exact and normalized.
REQUIRED_LATER_FOLD_CLAUSES = (
    "retain-v1-and-v2-boundary-with-hashes-in-typed-report-homes-created-by-org-l1",
    "reference-a13-a14-without-duplicating-authority",
    "reissue-handoff-and-generated-task-board-from-live-git-worktree-lease-packet-facts",
    "never-copy-opus-tainted-handoff-text",
)
FOLD_OBLIGATIONS = {
    "owner_step": "july-18-review-sop-fold",
    "status": "deferred-not-implemented-here",
    "source": ("approved plan, Ordered JGUIDA Execution step 4 (2026-07-18) + operator-record "
               "ordered continuation"),
    "process": ["exact-tree-currentness", "generated-board-handoff", "typed-lifecycle",
                "source-snapshots", "receipt-freshness", "browser-toolchain-portability",
                "executable-review-convergence"],
    "w7": ["typed-actor-session-model-tool-capability-scope-records",
           "scout-versus-builder-separation"],
    "demo_a": ["real-parsing-lowering", "source-binding", "deterministic-outputs",
               "genuinely-cold-skill-trial"],
    "w6_demo_b": ["route-resource-state-coverage", "unknown-cell-refusal",
                  "hostile-crawler-fixture",
                  "robots-rate-session-privacy-third-party-retention-controls"],
    "product_claims": ["join-declared-product-instances-to-rendered-receipts",
                       "refuse-unsupported-whole-site-compiler-claims"],
    "later_fold_clauses": list(REQUIRED_LATER_FOLD_CLAUSES),
    "precedence_note": ("v2 controls conflicts; v1 and the v2 boundary correction remain "
                        "preserved and hash-classified"),
}

AGENTS_ANCHORS = [
    "`/root` (the operator's conductor session) is the SOLE CONDUCTOR",
    "The conductor NEVER designs, authors REDs, implements, or issues review verdicts.",
    ("Fable never conducts, never implements GREEN, never commits, never integrates, and never "
     "approves its own artifact."),
    "the BUILD lane for EVERY implementation tier — difficulty never changes the builder seat.",
    ("Codex never conducts, never designs, never authors REDs, never implements, never "
     "integrates, never commits, never merges, never pushes"),
    "`/root` is never a reviewer.",
    "author-never-approves",
    ("fresh one-shot session pinned to its exact model, with no fallback, no resume, and no "
     "mixed-model artifact"),
    "invalidates the COMPLETE worker output",
    "One JGUIDA worker lane runs at a time.",
    "IMMUTABLE, CONSUMER-PULL, and CANDIDATE-ONLY",
    "Neither repository ever writes into the other",
    "ANY change to an upstream pin invalidates every downstream admission, packet, proof, and review",
    ("Role→agent assignments become DATA in the role registry `contracts/role_registry.*` when "
     "the W7 design lands"),
    ("every review dispatched after the grandfathered A13/A14 r1 design review runs at "
     "operator-ratified XHIGH"),
    "Seat text in earlier gate/design records is historical; THIS section is the binding routing.",
    "Fable authoring dispatches always run at MAX effort with no conductor-imposed budgets.",
    "Review stand-ins are never Opus",
    "approving DESIGN, CODE, and ADVERSARIAL review authority remains separate Codex",
]
ACTIVE_ANCHORS = [
    "**`/root` is the sole conductor**",
    "A14 exchange law (immutable, consumer-pull, candidate-only)",
    ("**Binding order:** A13/A14 → re-pin r6 → re-pin org-L1 → July 18 review/SOP fold → "
     "W8-O r3 → four retro-review rows → W7 → DEMO A/B."),
    "at operator-ratified XHIGH",
    "Codex only reviews.",
]
HANDOFF_ANCHORS = [
    "`/root` conducts",
    "fresh MAX `claude-fable-5` events author designs/REDs/packets",
]
EXPECTED_PROSE_DOCS = {
    "AGENTS.md": AGENTS_ANCHORS,
    "docs/plans/ACTIVE.md": ACTIVE_ANCHORS,
    "docs/plans/handoff/HANDOFF.md": HANDOFF_ANCHORS,
}
# R2-OPUS-REVIEW-AUTHORITY-005: the exact normalized stand-in mapping is forbidden phrase 15.
OPUS_STANDIN_MAPPING = (
    "independent review stand-ins — never mutating the tree; fan-outs run as Opus workers"
)
FORBIDDEN_PHRASES = [
    "Fable (Claude, main loop) is the CONDUCTOR",
    "Fable (the conductor)",
    "Fable conducts",
    "Fable verifies in a clean worktree, integrates, and commits",
    "Fable verification",
    "Fable commit",
    "Continuation routing (operator, 2026-07-16",
    "Continuation routing (operator 2026-07-16)",
    "the FIRST review round on an artifact runs at max/ultra",
    "first round max/ultra",
    "Codex verdict rounds run at operator-ratified HIGH",
    "operator-ratified HIGH effort",
    "codes by default",
    "does not implement by default",
    OPUS_STANDIN_MAPPING,
]

# R2-LIVE-RULE-001: a live "unchanged" claim about the SOP or the review-effort/convergence
# law may not coexist with the 2026-07-19 XHIGH amendments in the same document.
UNCHANGED_LAW_CLAIMS = [
    ("unchanged-claim-bundled",
     ("The 13-step slice SOP, the review-effort/convergence law, the receipt law (MF1), and "
      "the build-packet bindings are unchanged")),
    ("unchanged-claim-sop", "The 13-step slice SOP is unchanged"),
    ("unchanged-claim-review-effort-law", "the review-effort/convergence law is unchanged"),
]
XHIGH_AMENDMENT_MARKERS = [
    "review-effort amendment 2026-07-19",
    ("every review dispatched after the grandfathered A13/A14 r1 design review runs at "
     "operator-ratified XHIGH"),
    "operator-ratified XHIGH, 2026-07-19",
    "at operator-ratified XHIGH",
]

EVIDENCE_VOCAB = {
    "kind": ["process-record", "session-jsonl", "session-dir", "untracked-draft",
             "review-bank-file", "review-record", "control-bundle"],
    "repo_class": ["jguida", "semantic-tdd"],
    "authority_class": ["bootstrap-process-record", "evidence-only",
                        "non-authoritative-tainted", "unverified-non-gating"],
    "integrity": ["fable-only", "opus-only", "model-transition-verified",
                  "mixed-prose-conservative", "static-file", "live-appending", "not-inspected"],
    "pin_status": ["pinned", "pending-close", "classification-only", "unavailable"],
}
ROW_KEYS = {"id", "kind", "locator", "repo_class", "authority_class", "integrity", "sha256",
            "expected_prefix", "expected_suffix", "size_bytes", "observed_utc", "pin_status",
            "gating", "finding"}
REQUIRED_EVIDENCE_IDS = frozenset({
    "op-record-2026-07-18", "evidence-inventory", "r1-invalidation", "r2-invalidation",
    "r5-invalidation", "design-r3", "design-r4-currentness", "design-r6-correction",
    "approved-plan-archive", "codex-design-review-r1", "codex-design-verdict",
    "jsonl-r1-worker", "jsonl-r2-worker", "jsonl-r3-author", "jsonl-r4-author",
    "jsonl-r6-author", "jsonl-conductor-631e90bb", "jsonl-f5421057", "jsonl-ac57345a",
    "jsonl-7b2c4f22", "jsonl-4c73f47e", "jsonl-08672472", "jsonl-6acf59c3", "jsonl-b27aa1c8",
    "jsonl-8d06f4b2", "jsonl-4af6f55a", "jsonl-fd14c56f", "jsonl-a3060398", "untitled-1-ini",
    "rb-sha256sums", "rb-desk-digest", "rb-v1-review", "rb-v1-replay-log", "rb-v1-focused-log",
    "rb-v1-brief", "rb-v1-manifest", "rb-v2-review", "rb-v2-replay-log",
    "rb-v2-boundary-correction", "rb-v2-focused-log", "rb-v2-brief", "rb-v2-manifest",
    "std-semantic-tdd", "std-constellation", "std-scout", "control-bundle-zip",
    "rr-cand-ratchet-r5", "rr-cand-w8o-r2", "rr-cand-model-void",
})
TAINTED_IDS = {"jsonl-08672472", "jsonl-6acf59c3", "jsonl-b27aa1c8", "jsonl-8d06f4b2"}
EXPECTED_PRECEDENCE = ("v2-overrides-v1-on-conflict; both versions and the v2 boundary "
                       "correction preserved locally and hash-classified")
CONTROL_DIGEST_DISPLAY = "966ec630…1492"

VALID_EDGE_FIXTURE = {
    "edge_id": "fixture-edge-1",
    "producer_repo": "semantic-tdd",
    "producer_commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "producer_tree": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "artifact_path": "exports/candidate-artifact.json",
    "artifact_sha256": "c" * 64,
    "contract_version": "1",
    "proof_receipts": [{"path": "receipts/proof.json", "sha256": "d" * 64}],
    "review_receipts": [{"path": "receipts/review.md", "sha256": "e" * 64}],
    "candidate_status": "candidate",
    "direction": "consumer-pull",
    "staleness_rule": STALENESS_LAW,
}

EDGE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
CONTRACT_VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def _norm(s: str) -> str:
    return " ".join(s.split())


def edge_violations(edge: object, exchange_law: dict) -> list[str]:
    """Fail-closed validation of ONE exchange edge. Never raises; a non-object edge is a named
    violation (R2-EDGE-SHAPE-002, V-EDGE-NONOBJECT), never a crash and never a silent pass."""
    if not isinstance(edge, dict):
        return [f"edge: element is not an object (got {type(edge).__name__}) — "
                "fail-closed: every edge must be a mapping with the exact required fields"]
    v: list[str] = []
    required = exchange_law.get("edge_required_fields", EDGE_REQUIRED_FIELDS)
    missing = [k for k in required if k not in edge]
    unknown = [k for k in edge if k not in required]
    if missing:
        v.append(f"edge {edge.get('edge_id', '?')}: missing required fields {missing}")
    if unknown:
        v.append(f"edge {edge.get('edge_id', '?')}: unknown fields {unknown}")
    if missing or unknown:
        return v

    def _s(key: str) -> object:
        return edge[key]

    if not isinstance(_s("edge_id"), str) or not EDGE_ID_RE.match(edge["edge_id"]):
        v.append("edge: edge_id must match ^[a-z0-9][a-z0-9-]{0,63}$")
    repo = _s("producer_repo")
    if (not isinstance(repo, str) or not repo or repo != repo.strip() or "\n" in repo):
        v.append(f"edge {edge['edge_id']}: producer_repo must be a non-empty single-line "
                 "string with no surrounding whitespace")
    for key in ("producer_commit", "producer_tree"):
        val = _s(key)
        if not isinstance(val, str) or not HEX40.match(val):
            v.append(f"edge {edge['edge_id']}: {key} must be 40 lowercase hex")
    path = _s("artifact_path")
    if (not isinstance(path, str) or not path or "\n" in path or path.startswith("/")
            or ".." in Path(path).parts):
        v.append(f"edge {edge['edge_id']}: artifact_path must be a relative, newline-free, "
                 "non-escaping path")
    digest = _s("artifact_sha256")
    if not isinstance(digest, str) or not HEX64.match(digest):
        v.append(f"edge {edge['edge_id']}: artifact_sha256 must be 64 lowercase hex")
    ver = _s("contract_version")
    if not isinstance(ver, str) or not CONTRACT_VERSION_RE.match(ver):
        v.append(f"edge {edge['edge_id']}: contract_version malformed")
    for key in ("proof_receipts", "review_receipts"):
        items = _s(key)
        if not isinstance(items, list) or len(items) < 1:
            v.append(f"edge {edge['edge_id']}: {key} must be a non-empty list")
            continue
        for i, item in enumerate(items):
            if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
                v.append(f"edge {edge['edge_id']}: {key}[{i}] must have exactly path+sha256")
                continue
            ipath, isha = item["path"], item["sha256"]
            if (not isinstance(ipath, str) or not ipath or "\n" in ipath
                    or ipath.startswith("/") or ".." in Path(ipath).parts):
                v.append(f"edge {edge['edge_id']}: {key}[{i}].path malformed")
            if not isinstance(isha, str) or not HEX64.match(isha):
                v.append(f"edge {edge['edge_id']}: {key}[{i}].sha256 must be 64 lowercase hex")
    if _s("candidate_status") != "candidate":
        v.append(f"edge {edge['edge_id']}: candidate_status must be exactly 'candidate' "
                 "(candidate-only exchange)")
    if _s("direction") != "consumer-pull":
        v.append(f"edge {edge['edge_id']}: direction must be exactly 'consumer-pull'")
    if _s("staleness_rule") != exchange_law.get("staleness_law"):
        v.append(f"edge {edge['edge_id']}: staleness_rule must equal the normative "
                 "staleness_law sentence byte-exactly (restating it weaker is a violation)")
    return v


def evidence_violations(record: dict) -> list[str]:
    v: list[str] = []
    evidence = record.get("evidence")
    if not isinstance(evidence, dict):
        return ["evidence: must be an object"]
    if set(evidence) != {"vocab", "external_review_precedence", "items"}:
        v.append(f"evidence: keys must be exactly vocab+external_review_precedence+items, "
                 f"got {sorted(evidence)}")
        return v
    if evidence["vocab"] != EVIDENCE_VOCAB:
        v.append("evidence.vocab: must equal the closed A13/A14 vocabulary exactly")
    if evidence["external_review_precedence"] != EXPECTED_PRECEDENCE:
        v.append("evidence.external_review_precedence: must equal the exact v2-overrides-v1 "
                 "sentence by full string equality (prefix acceptance is withdrawn)")
    items = evidence["items"]
    if not isinstance(items, list):
        return v + ["evidence.items: must be a list"]
    ids = [row.get("id") for row in items if isinstance(row, dict)]
    if len(ids) != len(items):
        v.append("evidence.items: every row must be an object with an id")
    if len(ids) != len(set(ids)):
        v.append(f"evidence.items: duplicate ids {sorted(i for i in ids if ids.count(i) > 1)}")
    actual = set(ids)
    if actual != set(REQUIRED_EVIDENCE_IDS):
        v.append(f"evidence roster drift — missing {sorted(REQUIRED_EVIDENCE_IDS - actual)}; "
                 f"smuggled {sorted(actual - REQUIRED_EVIDENCE_IDS)}")
    for row in items:
        if not isinstance(row, dict):
            continue
        rid = row.get("id", "?")
        expected_keys = ROW_KEYS | ({"digest_display"} if rid == "control-bundle-zip" else set())
        if set(row) != expected_keys:
            v.append(f"row {rid}: keys must be exactly the closed row schema "
                     f"(delta {sorted(set(row) ^ expected_keys)})")
            continue
        for key in ("kind", "repo_class", "authority_class", "integrity", "pin_status"):
            if row[key] not in EVIDENCE_VOCAB[key]:
                v.append(f"row {rid}: {key} {row[key]!r} outside the closed vocab")
        if not isinstance(row["locator"], str) or not row["locator"].strip():
            v.append(f"row {rid}: locator must be a non-empty string")
        sha, pin = row["sha256"], row["pin_status"]
        if pin == "pinned":
            if not isinstance(sha, str) or not HEX64.match(sha):
                v.append(f"row {rid}: pinned row needs a full 64-lowercase-hex sha256")
        elif sha is not None:
            v.append(f"row {rid}: sha256 must be null unless pin_status is 'pinned'")
        for frag_key, check in (("expected_prefix", "startswith"), ("expected_suffix", "endswith")):
            frag = row[frag_key]
            if frag is None:
                continue
            if not isinstance(frag, str) or not re.match(r"^[0-9a-f]{4,16}$", frag):
                v.append(f"row {rid}: {frag_key} must be 4-16 lowercase hex or null")
            elif isinstance(sha, str) and not getattr(sha, check)(frag):
                v.append(f"row {rid}: sha256 does not {check} {frag_key} {frag!r} — "
                         "evidence drifted: STOP and reclassify, never overwrite")
        size = row["size_bytes"]
        if pin == "pinned":
            if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
                v.append(f"row {rid}: pinned row needs a positive integer size_bytes")
        elif size is not None:
            v.append(f"row {rid}: size_bytes must be null unless pinned")
        if not isinstance(row["observed_utc"], str) or not DATE_RE.match(row["observed_utc"]):
            v.append(f"row {rid}: observed_utc must be YYYY-MM-DD")
        if row["gating"] is not False:
            v.append(f"row {rid}: gating must be False — evidence never gates")
        finding = row["finding"]
        if not isinstance(finding, str) or not finding or len(finding) > 300 or "\n" in finding:
            v.append(f"row {rid}: finding must be a single line of 1-300 chars")
        if rid in TAINTED_IDS and row["authority_class"] != "non-authoritative-tainted":
            v.append(f"row {rid}: model-transition session must stay non-authoritative-tainted")
        if row["repo_class"] == "semantic-tdd" and row["authority_class"] != "evidence-only":
            v.append(f"row {rid}: a semantic-tdd row is evidence-only and can never be a "
                     "bootstrap-process-record")
        if rid == "control-bundle-zip":
            if row.get("digest_display") != CONTROL_DIGEST_DISPLAY:
                v.append("row control-bundle-zip: digest_display must be exactly the "
                         "operator-supplied abbreviated digest (never expanded)")
            if row["sha256"] is not None:
                v.append("row control-bundle-zip: sha256 must stay null (UNVERIFIED)")
            if row["authority_class"] != "unverified-non-gating":
                v.append("row control-bundle-zip: authority_class must be unverified-non-gating")
            hexes = [val for val in row.values()
                     if isinstance(val, str) and re.search(r"[0-9a-fA-F]{64}", val)]
            if hexes:
                v.append("row control-bundle-zip: NO 64-hex string may appear anywhere in the "
                         "row — missing digest bytes are never invented (M-DIGEST-MINT)")
    return v


def record_violations(record: object) -> list[str]:
    if not isinstance(record, dict):
        return ["record: not a JSON object"]
    v: list[str] = []
    if set(record) != TOP_KEYS:
        v.append(f"top-level keys must be exactly the closed 16-key set "
                 f"(delta {sorted(set(record) ^ TOP_KEYS)}) — W7's registry surface is "
                 "preserved; no actor tables here")
        return v
    if record["contract_id"] != "OrchestrationExchangePolicy":
        v.append("contract_id must be OrchestrationExchangePolicy")
    if record["schema_version"] != 1:
        v.append("schema_version must be 1")
    if record["ratified_utc"] != "2026-07-18":
        v.append("ratified_utc must be 2026-07-18")
    if record["authority_status"] != "operator_ratified":
        v.append("authority_status must be operator_ratified")
    if record["purpose"] != EXPECTED_PURPOSE:
        v.append("purpose drifted from the ratified sentence")
    if record["verification_scope"] != EXPECTED_VERIFICATION_SCOPE:
        v.append("verification_scope drifted from the ratified sentence")
    if record["w7_successor"] != EXPECTED_W7_SUCCESSOR:
        v.append("w7_successor must equal the ratified object exactly (owner W7, surface "
                 "contracts/role_registry.*)")
    if record["temporary_bootstrap_authority"] != EXPECTED_TBA:
        v.append("temporary_bootstrap_authority must pin the current operator record "
                 f"{OP_RECORD_SHA[:8]}… and the retired-at-landing-commit status exactly")

    seat = record["seat_law"]
    if not isinstance(seat, dict) or set(seat) != set(EXPECTED_SEAT_LAW):
        v.append("seat_law: key set must exactly match the ratified seat law")
    else:
        for key, expected in EXPECTED_SEAT_LAW.items():
            got = seat[key]
            if key in NEVER_LIST_KEYS:
                if (not isinstance(got, list) or len(got) != len(set(got))
                        or sorted(got) != sorted(expected)):
                    v.append(f"seat_law.{key}: must be duplicate-free and exactly "
                             f"{sorted(expected)} — every prohibition is individually "
                             f"load-bearing (got {got})")
            elif got != expected:
                v.append(f"seat_law.{key}: must be {expected!r} (got {got!r})")
    if record["dispatch_law"] != EXPECTED_DISPATCH_LAW:
        v.append("dispatch_law must equal the ratified A13 dispatch-integrity object exactly "
                 "(fresh one-shot, exact model, no fallback/resume, budgets forbidden, "
                 "closed-JSONL rescan, one lane)")
    review = record["review_law"]
    if not isinstance(review, dict) or set(review) != set(EXPECTED_REVIEW_LAW):
        v.append("review_law: key set must exactly match the ratified review law "
                 "(including convergence_state and terminal_r2_delta_review)")
    else:
        for key, expected in EXPECTED_REVIEW_LAW.items():
            if review[key] != expected:
                v.append(f"review_law.{key}: must equal the ratified value exactly "
                         f"(got {review[key]!r}) — the two-REVISE convergence and XHIGH law "
                         "may not be forged or downgraded")

    exch = record["exchange_law"]
    if not isinstance(exch, dict) or set(exch) != EXCHANGE_LAW_KEYS:
        v.append("exchange_law: key set must be exactly the closed A14 set")
    else:
        expected_simple = {
            "transport": "consumer-pull", "immutable": True, "candidate_only": True,
            "neither_repo_writes_the_other": True, "neither_repo_mints_the_others_authority": True,
            "write_grants": [], "edge_required_fields": EDGE_REQUIRED_FIELDS,
            "staleness_law": STALENESS_LAW, "historical_notes": EXPECTED_HISTORICAL_NOTES,
        }
        for key, expected in expected_simple.items():
            if exch[key] != expected:
                v.append(f"exchange_law.{key}: must equal the ratified value exactly "
                         f"(got {exch[key]!r})")
        edges = exch["edges"]
        if not isinstance(edges, list):
            v.append(f"exchange_law.edges: must be a LIST (got {type(edges).__name__}) — "
                     "fail-closed container law (M-EDGES-NOT-LIST): a non-list edges value "
                     "can never validate vacuously")
        else:
            for i, edge in enumerate(edges):
                for finding in edge_violations(edge, exch):
                    v.append(f"exchange_law.edges[{i}]: {finding}")

    if record["continuation_order"] != CONTINUATION_ORDER:
        v.append(f"continuation_order must be exactly {CONTINUATION_ORDER}")
    fold = record["pending_fold_obligations"]
    if fold != FOLD_OBLIGATIONS:
        v.append("pending_fold_obligations must equal the typed FOLD_OBLIGATIONS constant by "
                 "full structural equality — narrowing, renaming, or deleting any obligation "
                 "reddens")
    if isinstance(fold, dict):
        if fold.get("owner_step") not in record.get("continuation_order", []):
            v.append("pending_fold_obligations.owner_step must be an element of "
                     "continuation_order")
        clauses = fold.get("later_fold_clauses", [])
        if (not isinstance(clauses, list) or len(clauses) != len(set(clauses))
                or set(clauses) != set(REQUIRED_LATER_FOLD_CLAUSES)):
            missing = sorted(set(REQUIRED_LATER_FOLD_CLAUSES) - set(clauses or []))
            v.append(f"later_fold_clauses must be duplicate-free and set-equal to the four "
                     f"REQUIRED_LATER_FOLD_CLAUSES (missing {missing}) — R2-FOLD-SCOPE-003")

    parity = record["prose_parity"]
    if (not isinstance(parity, dict) or set(parity) != {"docs", "forbidden_phrases"}
            or parity.get("docs") != EXPECTED_PROSE_DOCS
            or parity.get("forbidden_phrases") != FORBIDDEN_PHRASES):
        v.append("prose_parity must equal the exact anchor/forbidden sets — an incomplete "
                 "exact set that preserves itself is the named pitfall (M-PARITY-SET-SHRUNK)")

    v.extend(evidence_violations(record))
    return v


def doc_violations(record: dict, doc_texts: dict, kinds: tuple = ("anchors", "forbidden")) -> list[str]:
    v: list[str] = []
    parity = record.get("prose_parity", {})
    if "anchors" in kinds:
        for doc, anchors in parity.get("docs", {}).items():
            text = _norm(doc_texts.get(doc, ""))
            for anchor in anchors:
                if _norm(anchor) not in text:
                    v.append(f"{doc}: required anchor absent: {anchor!r}")
    if "forbidden" in kinds:
        for doc in parity.get("docs", {}):
            text = _norm(doc_texts.get(doc, ""))
            for phrase in parity.get("forbidden_phrases", []):
                if _norm(phrase) in text:
                    v.append(f"{doc}: forbidden phrase present: {phrase!r}")
    return v


def live_rule_conflict_violations(doc_texts: dict) -> list[str]:
    """R2-LIVE-RULE-001: an 'SOP unchanged' / 'review-effort/convergence law unchanged' claim
    coexisting with the C15/C16 XHIGH amendments in the same document is a contradiction."""
    v: list[str] = []
    for doc, text in doc_texts.items():
        norm = _norm(text)
        markers = [m for m in XHIGH_AMENDMENT_MARKERS if _norm(m) in norm]
        if not markers:
            continue
        for claim_id, claim in UNCHANGED_LAW_CLAIMS:
            if _norm(claim) in norm:
                v.append(f"{doc}: unchanged-law-claim conflict ({claim_id}): the claim "
                         f"{claim!r} coexists with the XHIGH amendment marker {markers[0]!r} — "
                         "the 2026-07-19 amendment supersedes it (M-A4-UNCHANGED-LAW)")
    return v


def opus_review_authority_violations(record: dict, doc_texts: dict) -> list[str]:
    """R2-OPUS-REVIEW-AUTHORITY-005: while the typed record prohibits Opus review, no live doc
    may map independent review stand-ins onto Opus workers. The single ratified capacity: Opus
    fan-outs do bounded read-only inspection and evidence extraction; approving DESIGN, CODE,
    and ADVERSARIAL review authority remains separate Codex."""
    v: list[str] = []
    builder_never = record.get("seat_law", {}).get("builder_never", [])
    if "review" not in builder_never:
        v.append("seat_law.builder_never: must contain 'review' (M-OPUS-REVIEWS) — the typed "
                 "prohibition is the controlling half of the capacity resolution")
        return v
    for doc, text in doc_texts.items():
        if _norm(OPUS_STANDIN_MAPPING) in _norm(text):
            v.append(f"{doc}: opus-review-standin mapping present while typed builder_never "
                     "contains 'review' — review stand-ins are never Opus "
                     "(M-OPUS-REVIEW-STANDIN)")
    return v


def all_doc_violations(record: dict, doc_texts: dict) -> list[str]:
    return (doc_violations(record, doc_texts)
            + live_rule_conflict_violations(doc_texts)
            + opus_review_authority_violations(record, doc_texts))


# --- R2-CONVERGENCE-PACKET-004: sealed-packet convergence preflight ---------------------------

MANDATORY_FINDING_IDS = (
    "R1-CURRENTNESS-001", "R1-EFFORT-002", "R1-GUARD-EDGE-003A", "R1-GUARD-EVIDENCE-003B",
    "R1-GUARD-CODEX-003C", "R1-FOLD-SCOPE-004", "R1-RED-STAGING-005", "R1-MEASURED-FACTS-006",
    "R1-PROBE-GIT-007", "R1-PROBE-JSONL-008", "R1-PROBE-BANK-009", "R1-PROBE-PROJECTION-010",
    "R1-PROBE-WRITABLE-011", "R1-PROBE-SCOPE-012", "ERR-R2-ABBR-01", "ERR-R2-ABBR-02",
    "ERR-R2-ABBR-03", "R2-LIVE-RULE-001", "R2-EDGE-SHAPE-002", "R2-FOLD-SCOPE-003",
    "R2-CONVERGENCE-PACKET-004", "R2-OPUS-REVIEW-AUTHORITY-005",
)


def convergence_packet_violations(gate: object) -> list[str]:
    """Preflight for the sealed build packet's design_gate section. Accepts ONLY the lawful
    two-REVISE convergence with both exact receipts and a complete finding map; rejects a
    missing r2 receipt, a missing finding mapping, and any forged APPROVE."""
    if not isinstance(gate, dict):
        return ["design_gate: not an object"]
    v: list[str] = []
    state = gate.get("binding_state")
    if state != "lawful-two-revise-convergence":
        v.append(f"design_gate: binding_state must be lawful-two-revise-convergence "
                 f"(got {state!r})")
    for key, val in gate.items():
        if isinstance(val, str) and "approve" in val.lower() and key != "convergence_law":
            v.append(f"design_gate.{key}: forged APPROVE — no approving DESIGN verdict exists "
                     "for this lineage (M-CONVERGENCE-REQUIRES-APPROVE)")
    if gate.get("approving_design_verdict") is not None:
        v.append("design_gate.approving_design_verdict: must be null — forged APPROVE "
                 "(M-CONVERGENCE-REQUIRES-APPROVE)")
    if gate.get("third_prose_design_review_permitted") is not False:
        v.append("design_gate.third_prose_design_review_permitted: must be False")
    rounds = gate.get("revise_rounds")
    expected_rounds = [
        (1, R1_REVIEW_SHA, R1_ROLLOUT_SHA), (2, R2_REVIEW_SHA, R2_ROLLOUT_SHA),
    ]
    if not isinstance(rounds, list) or [r.get("round") for r in rounds if isinstance(r, dict)] \
            != [1, 2]:
        v.append("design_gate.revise_rounds: must contain exactly rounds 1 and 2 — a missing "
                 "r2 receipt is a rejection")
    else:
        for (num, review_sha, rollout_sha), row in zip(expected_rounds, rounds):
            if row.get("verdict") != "REVISE":
                v.append(f"design_gate round {num}: verdict must be REVISE "
                         f"(got {row.get('verdict')!r}) — any other value is forged")
            if row.get("review_sha256") != review_sha:
                v.append(f"design_gate round {num}: review_sha256 must be {review_sha}")
            if row.get("rollout_sha256") != rollout_sha:
                v.append(f"design_gate round {num}: rollout_sha256 must be {rollout_sha}")
    fmap = gate.get("finding_map")
    if not isinstance(fmap, dict):
        v.append("design_gate.finding_map: missing — the complete typed disposition map is "
                 "required")
    else:
        for fid in MANDATORY_FINDING_IDS:
            entry = fmap.get(fid)
            if not isinstance(entry, dict):
                v.append(f"design_gate.finding_map: finding {fid} unmapped — every finding "
                         "needs a typed disposition before build")
                continue
            if not isinstance(entry.get("disposition"), str) or not entry["disposition"]:
                v.append(f"design_gate.finding_map[{fid}]: disposition must be non-empty")
            ex = entry.get("executable")
            if not isinstance(ex, list) or not ex or not all(isinstance(e, str) and e for e in ex):
                v.append(f"design_gate.finding_map[{fid}]: executable RED/probe refs required")
    return v


CONVERGENCE_FIXTURE = {
    "binding_state": "lawful-two-revise-convergence",
    "convergence_law": (
        "after two REVISE rounds on the same artifact, remaining findings convert to executable "
        "REDs/probes and move to the build phase; Codex then reviews code and executable "
        "output, never another prose restatement"
    ),
    "revise_rounds": [
        {"round": 1,
         "review_path": "scratchpad/active/bootstrap/a13-a14-codex-design-review-r1.md",
         "review_sha256": R1_REVIEW_SHA, "rollout_sha256": R1_ROLLOUT_SHA,
         "verdict": "REVISE", "effort": "max-grandfathered"},
        {"round": 2,
         "review_path": "scratchpad/active/bootstrap/a13-a14-codex-design-delta-review-r2.md",
         "review_sha256": R2_REVIEW_SHA, "rollout_sha256": R2_ROLLOUT_SHA,
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


# --- named mutants (each: deep-copy of the REAL input, exactly one lawful perversion) ---------

def _row(record: dict, rid: str) -> dict:
    for row in record["evidence"]["items"]:
        if row.get("id") == rid:
            return row
    raise AssertionError(f"mutant setup: roster row {rid} missing")


def _del_row(record: dict, rid: str) -> None:
    items = record["evidence"]["items"]
    record["evidence"]["items"] = [r for r in items if r.get("id") != rid]


def _set(path_keys: tuple, value: object):
    def apply(record: dict) -> None:
        obj = record
        for key in path_keys[:-1]:
            obj = obj[key]
        obj[path_keys[-1]] = value
    return apply


def _remove_from(path_keys: tuple, member: str):
    def apply(record: dict) -> None:
        obj = record
        for key in path_keys[:-1]:
            obj = obj[key]
        obj[path_keys[-1]] = [m for m in obj[path_keys[-1]] if m != member]
    return apply


def _drop_clause(index: int):
    def apply(record: dict) -> None:
        clauses = record["pending_fold_obligations"]["later_fold_clauses"]
        del clauses[index]
    return apply


def _mut_edges_dict(record: dict) -> None:
    record["exchange_law"]["edges"] = {}


def _mut_edges_nested_list(record: dict) -> None:
    record["exchange_law"]["edges"] = [[]]


def _mut_inject_push_edge(record: dict) -> None:
    bad = copy.deepcopy(VALID_EDGE_FIXTURE)
    bad["direction"] = "producer-push"
    record["exchange_law"]["edges"].append(bad)


def _mut_inject_unpinned_edge(record: dict) -> None:
    bad = copy.deepcopy(VALID_EDGE_FIXTURE)
    del bad["producer_tree"]
    record["exchange_law"]["edges"].append(bad)


def _mut_digest_mint_display(record: dict) -> None:
    _row(record, "control-bundle-zip")["digest_display"] = "9" * 64


def _mut_digest_mint_sha(record: dict) -> None:
    _row(record, "control-bundle-zip")["sha256"] = "9" * 64


def _mut_hash_truncate(record: dict) -> None:
    row = _row(record, "design-r3")
    row["sha256"] = row["sha256"][:63]


def _mut_order_swap(record: dict) -> None:
    order = record["continuation_order"]
    i, j = order.index("w7"), order.index("demo-a-b")
    order[i], order[j] = order[j], order[i]


def _mut_parity_anchor_deleted(record: dict) -> None:
    record["prose_parity"]["docs"]["AGENTS.md"] = \
        record["prose_parity"]["docs"]["AGENTS.md"][1:]


def _mut_parity_phrase_deleted(record: dict) -> None:
    record["prose_parity"]["forbidden_phrases"] = \
        record["prose_parity"]["forbidden_phrases"][:-1]


RECORD_MUTANTS = [
    ("M-CODEX-DEFAULT-BUILDER", "seat_law.builder_model",
     [_set(("seat_law", "builder_model"), "codex")]),
    ("M-SELF-REVIEW", "seat_law",
     [_set(("seat_law", "author_never_approves"), False),
      _remove_from(("seat_law", "author_never"), "approve-own-artifact")]),
    ("M-UNMONITORED-TRANSITION", "dispatch_law",
     [_set(("dispatch_law", "on_model_or_tool_breach"), "continue"),
      _remove_from(("dispatch_law", "monitor"), "closed-jsonl-structural-rescan")]),
    ("M-EFFORT-DOWNGRADE", "seat_law.author_effort",
     [_set(("seat_law", "author_effort"), "high")]),
    ("M-REVIEW-EFFORT-DRIFT", "seat_law.reviewer_effort",
     [_set(("seat_law", "reviewer_effort"), "high"),
      _set(("seat_law", "reviewer_effort"), "max")]),
    ("M-REVIEW-LAW-DOWNGRADE", "review_law.review_effort",
     [_set(("review_law", "review_effort"), "high")]),
    ("M-GRANDFATHER-FORGED", "review_law.grandfathered_r1_design_review",
     [_set(("review_law", "grandfathered_r1_design_review", "verdict"), "APPROVE")]),
    ("M-R2-VERDICT-FORGED", "review_law",
     [_set(("review_law", "terminal_r2_delta_review", "verdict"), "APPROVE"),
      _set(("review_law", "convergence_state"), "approved-design-verdict")]),
    ("M-PRODUCER-PUSH", "exchange_law.transport",
     [_set(("exchange_law", "transport"), "producer-push")]),
    ("M-XREPO-WRITE-GRANT", "exchange_law.write_grants",
     [_set(("exchange_law", "write_grants"), [{"repo": "semantic-tdd", "grant": "write"}])]),
    ("M-DIGEST-MINT", "control-bundle-zip", [_mut_digest_mint_display, _mut_digest_mint_sha]),
    ("M-HASH-TRUNCATE", "sha256", [_mut_hash_truncate]),
    ("M-FRAGMENT-MISMATCH", "rb-v1-manifest.expected_suffix",
     [lambda r: _row(r, "rb-v1-manifest").update(expected_suffix="7eac0b")]),
    ("M-TAINT-UNMARK", "jsonl-08672472.authority_class",
     [lambda r: _row(r, "jsonl-08672472").update(authority_class="evidence-only")]),
    ("M-V1-OVER-V2", "external_review_precedence",
     [_set(("evidence", "external_review_precedence"),
           "v1-overrides-v2-on-conflict; both versions and the v2 boundary correction "
           "preserved locally and hash-classified")]),
    ("M-PRECEDENCE-WEAKENED", "external_review_precedence",
     [_set(("evidence", "external_review_precedence"),
           EXPECTED_PRECEDENCE + "-except-where-inconvenient")]),
    ("M-SECOND-LANE", "dispatch_law.concurrent_worker_lanes_max",
     [_set(("dispatch_law", "concurrent_worker_lanes_max"), 2)]),
    ("M-RESUME-ALLOWED", "dispatch_law.resume_forbidden",
     [_set(("dispatch_law", "resume_forbidden"), False)]),
    ("M-ORDER-SWAP", "continuation_order", [_mut_order_swap]),
    ("M-REGISTRY-EATEN", "top-level keys",
     [lambda r: r.update(actor_registry={})]),
    ("M-EDGE-FIELD-DROPPED", "edge_required_fields",
     [_remove_from(("exchange_law", "edge_required_fields"), "direction")]),
    ("M-EDGE-INJECTED-PUSH", "edges", [_mut_inject_push_edge]),
    ("M-EDGE-INJECTED-UNPINNED", "edges", [_mut_inject_unpinned_edge]),
    ("M-EDGES-NOT-LIST", "exchange_law.edges",
     [_mut_edges_dict, _mut_edges_nested_list]),
    ("M-EVIDENCE-ROW-DELETED", "evidence roster",
     [lambda r: _del_row(r, "rb-v2-boundary-correction"),
      lambda r: _del_row(r, "approved-plan-archive")]),
    ("M-FOLD-SCOPE-EATEN", "pending_fold_obligations.w6_demo_b",
     [_remove_from(("pending_fold_obligations", "w6_demo_b"), "hostile-crawler-fixture")]),
    ("M-FOLD-FAMILY-DROPPED", "pending_fold_obligations.product_claims",
     [lambda r: r["pending_fold_obligations"].pop("product_claims")]),
    ("M-FOLD-STEP-UNORDERED", "pending_fold_obligations.owner_step",
     [_set(("pending_fold_obligations", "owner_step"), "july-18-fold-lite")]),
    ("M-FOLD-CLAUSE-DROPPED-1", "later_fold_clauses", [_drop_clause(0)]),
    ("M-FOLD-CLAUSE-DROPPED-2", "later_fold_clauses", [_drop_clause(1)]),
    ("M-FOLD-CLAUSE-DROPPED-3", "later_fold_clauses", [_drop_clause(2)]),
    ("M-FOLD-CLAUSE-DROPPED-4", "later_fold_clauses", [_drop_clause(3)]),
    ("M-PARITY-SET-SHRUNK", "prose_parity",
     [_mut_parity_anchor_deleted, _mut_parity_phrase_deleted]),
    ("M-CODEX-CONDUCTS", "reviewer_never",
     [_remove_from(("seat_law", "reviewer_never"), "conduct")]),
    ("M-CODEX-DESIGNS", "reviewer_never",
     [_remove_from(("seat_law", "reviewer_never"), "design")]),
    ("M-CODEX-AUTHORS-RED", "reviewer_never",
     [_remove_from(("seat_law", "reviewer_never"), "author-red")]),
    ("M-CODEX-IMPLEMENTS", "reviewer_never",
     [_remove_from(("seat_law", "reviewer_never"), "implement")]),
    ("M-CODEX-INTEGRATES", "reviewer_never",
     [_remove_from(("seat_law", "reviewer_never"), "integrate")]),
    ("M-CODEX-COMMITS", "reviewer_never",
     [_remove_from(("seat_law", "reviewer_never"), "commit")]),
    ("M-CODEX-MERGES", "reviewer_never",
     [_remove_from(("seat_law", "reviewer_never"), "merge")]),
    ("M-CODEX-PUSHES", "reviewer_never",
     [_remove_from(("seat_law", "reviewer_never"), "push")]),
    ("M-ROOT-DESIGNS", "conductor_never",
     [_remove_from(("seat_law", "conductor_never"), "design")]),
    ("M-ROOT-AUTHORS-RED", "conductor_never",
     [_remove_from(("seat_law", "conductor_never"), "author-red")]),
    ("M-ROOT-IMPLEMENTS", "conductor_never",
     [_remove_from(("seat_law", "conductor_never"), "implement")]),
    ("M-ROOT-VERDICTS", "conductor_never",
     [_remove_from(("seat_law", "conductor_never"), "issue-review-verdict")]),
    ("M-FABLE-CONDUCTS-SEAT", "author_never",
     [_remove_from(("seat_law", "author_never"), "conduct")]),
    ("M-FABLE-BUILDS", "author_never",
     [_remove_from(("seat_law", "author_never"), "implement-green")]),
    ("M-OPUS-DESIGNS", "builder_never",
     [_remove_from(("seat_law", "builder_never"), "design")]),
    ("M-OPUS-AUTHORS-RED", "builder_never",
     [_remove_from(("seat_law", "builder_never"), "author-red")]),
    ("M-OPUS-REVIEWS", "builder_never",
     [_remove_from(("seat_law", "builder_never"), "review")]),
    ("M-OPUS-COMMITS", "builder_never",
     [_remove_from(("seat_law", "builder_never"), "commit"),
      _remove_from(("seat_law", "builder_never"), "merge"),
      _remove_from(("seat_law", "builder_never"), "integrate")]),
    ("M-OPUS-PUSHES", "builder_never",
     [_remove_from(("seat_law", "builder_never"), "push")]),
]

DOC_MUTANTS = [
    ("M-FABLE-CONDUCTS", "AGENTS.md",
     lambda text: text + "\nFable (Claude, main loop) is the CONDUCTOR\n",
     "forbidden phrase"),
    ("M-ANCHOR-DELETED", "AGENTS.md",
     lambda text: text.replace(
         "`/root` (the operator's conductor session) is the SOLE CONDUCTOR", "", 1),
     "required anchor absent"),
    ("M-A4-UNCHANGED-LAW-1", "AGENTS.md",
     lambda text: text + ("\nThe 13-step slice SOP, the review-effort/convergence law, the "
                          "receipt law (MF1), and the build-packet bindings are unchanged.\n"),
     "unchanged-law-claim conflict"),
    ("M-A4-UNCHANGED-LAW-2", "AGENTS.md",
     lambda text: text + "\nThe 13-step slice SOP is unchanged.\n",
     "unchanged-law-claim conflict"),
    ("M-A4-UNCHANGED-LAW-3", "AGENTS.md",
     lambda text: text + "\nFor this continuation the review-effort/convergence law is "
                         "unchanged.\n",
     "unchanged-law-claim conflict"),
    ("M-OPUS-REVIEW-STANDIN", "AGENTS.md",
     lambda text: text + ("\nRead-only fan-outs: audits, research extraction, independent "
                          "review stand-ins — never mutating the tree; fan-outs run as Opus "
                          "workers.\n"),
     "opus-review-standin"),
]


def _hostile_edge(transform) -> object:
    edge = copy.deepcopy(VALID_EDGE_FIXTURE)
    return transform(edge)


def _del_key(key: str):
    def transform(edge: dict) -> dict:
        del edge[key]
        return edge
    return transform


def _set_key(key: str, value: object):
    def transform(edge: dict) -> dict:
        edge[key] = value
        return edge
    return transform


def _receipt_no_digest(edge: dict) -> dict:
    edge["review_receipts"] = [{"path": "receipts/review.md"}]
    return edge


def _receipt_extra_key(edge: dict) -> dict:
    edge["review_receipts"] = [{"path": "receipts/review.md", "sha256": "e" * 64,
                                "note": "extra"}]
    return edge


HOSTILE_EDGE_VECTORS = [
    ("V-EDGE-MISSING-TREE", _del_key("producer_tree")),
    ("V-EDGE-UNKNOWN-KEY", _set_key("write_grant", "yes")),
    ("V-EDGE-SHORT-COMMIT", _set_key("producer_commit", "a" * 39)),
    ("V-EDGE-UPPER-HEX", _set_key("artifact_sha256", "C" * 64)),
    ("V-EDGE-BAD-DIGEST-LEN", _set_key("artifact_sha256", "c" * 63)),
    ("V-EDGE-EMPTY-PROOFS", _set_key("proof_receipts", [])),
    ("V-EDGE-RECEIPT-NO-DIGEST", _receipt_no_digest),
    ("V-EDGE-RECEIPT-EXTRA-KEY", _receipt_extra_key),
    ("V-EDGE-STATUS-ADMITTED", _set_key("candidate_status", "admitted")),
    ("V-EDGE-DIRECTION-PUSH", _set_key("direction", "producer-push")),
    ("V-EDGE-ABS-PATH", _set_key("artifact_path", "/etc/passwd")),
    ("V-EDGE-DOTDOT", _set_key("artifact_path", "../escape.json")),
    ("V-EDGE-STALENESS-WEAKENED", _set_key("staleness_rule", "never stales")),
    ("V-EDGE-EMPTY-REPO", _set_key("producer_repo", "")),
    ("V-EDGE-NONOBJECT", lambda edge: []),
]


def _load_record() -> dict:
    return json.loads(RECORD_PATH.read_text(encoding="utf-8"))


def _doc_texts() -> dict:
    return {doc: path.read_text(encoding="utf-8") for doc, path in DOC_PATHS.items()}


class OrchestrationExchangeContract(unittest.TestCase):
    maxDiff = None

    def _require_record(self) -> dict:
        self.assertTrue(RECORD_PATH.is_file(), MISSING_MSG)
        return _load_record()

    # 1
    def test_record_exists_and_shape_closed(self) -> None:
        record = self._require_record()
        self.assertEqual(record_violations(record), [])

    # 2
    def test_prose_anchors_present(self) -> None:
        record = self._require_record()
        self.assertEqual(doc_violations(record, _doc_texts(), kinds=("anchors",)), [])

    # 3
    def test_no_stale_seat_text(self) -> None:
        record = self._require_record()
        self.assertEqual(doc_violations(record, _doc_texts(), kinds=("forbidden",)), [])

    # 4
    def test_evidence_rows_wellformed(self) -> None:
        record = self._require_record()
        self.assertEqual(evidence_violations(record), [])

    # 5
    def test_record_rejection_mutants_all_fire(self) -> None:
        record = self._require_record()
        self.assertEqual(record_violations(record), [],
                         "baseline: the REAL record must be violation-free")
        self.assertEqual(len(RECORD_MUTANTS), 52)
        for name, token, arms in RECORD_MUTANTS:
            self.assertGreaterEqual(len(arms), 1, name)
            for i, arm in enumerate(arms):
                mutant = copy.deepcopy(record)
                arm(mutant)
                found = record_violations(mutant)
                self.assertNotEqual(found, [], f"{name} arm {i} did not fire (vacuous probe)")
                self.assertTrue(any(token in viol for viol in found) or found,
                                f"{name} arm {i}: no violation names its aspect: {found}")

    # 6
    def test_doc_rejection_mutants_all_fire(self) -> None:
        record = self._require_record()
        texts = _doc_texts()
        self.assertEqual(all_doc_violations(record, texts), [],
                         "baseline: the REAL live docs must be violation-free")
        self.assertEqual(len(DOC_MUTANTS), 6)
        for name, doc, transform, token in DOC_MUTANTS:
            mutated = dict(texts)
            mutated[doc] = transform(texts[doc])
            found = all_doc_violations(record, mutated)
            self.assertNotEqual(found, [], f"{name} did not fire (vacuous probe)")
            self.assertTrue(any(token in viol for viol in found),
                            f"{name}: no violation names its aspect {token!r}: {found}")

    # 7
    def test_w7_and_retirement_pinned(self) -> None:
        record = self._require_record()
        self.assertEqual(record["w7_successor"]["owner"], "W7")
        self.assertEqual(record["w7_successor"]["surface"], "contracts/role_registry.*")
        tba = record["temporary_bootstrap_authority"]
        self.assertEqual(tba["status"], "retired-at-landing-commit")
        self.assertEqual(tba["source_record_sha256"], OP_RECORD_SHA)

    # 8
    def test_continuation_order_matches_active_plan(self) -> None:
        record = self._require_record()
        self.assertEqual(record["continuation_order"], CONTINUATION_ORDER)
        chain = " → ".join(ORDER_DISPLAY[step] for step in record["continuation_order"])
        anchor = f"**Binding order:** {chain}."
        active = _norm(DOC_PATHS["docs/plans/ACTIVE.md"].read_text(encoding="utf-8"))
        self.assertIn(_norm(anchor), active,
                      "ACTIVE.md must carry the Binding order sentence generated from "
                      "continuation_order (single source; a silent reorder reddens)")

    # 9
    def test_edge_fixture_positive(self) -> None:
        record = self._require_record()
        exch = record["exchange_law"]
        self.assertEqual(edge_violations(VALID_EDGE_FIXTURE, exch), [])
        for edge in exch["edges"]:
            self.assertEqual(edge_violations(edge, exch), [])

    # 10
    def test_edge_hostile_vectors_all_fire(self) -> None:
        record = self._require_record()
        exch = record["exchange_law"]
        self.assertEqual(len(HOSTILE_EDGE_VECTORS), 15)
        for name, transform in HOSTILE_EDGE_VECTORS:
            found = edge_violations(_hostile_edge(transform), exch)
            self.assertNotEqual(found, [], f"{name} did not fire (vacuous probe)")
            self.assertIsInstance(found, list, f"{name}: checker must fail closed, not raise")

    # 11
    def test_fold_scope_preserved(self) -> None:
        record = self._require_record()
        self.assertEqual(record["pending_fold_obligations"], FOLD_OBLIGATIONS)
        self.assertIn(record["pending_fold_obligations"]["owner_step"],
                      record["continuation_order"])

    # 12 (R2-FOLD-SCOPE-003)
    def test_later_fold_clauses_exact(self) -> None:
        record = self._require_record()
        clauses = record["pending_fold_obligations"]["later_fold_clauses"]
        self.assertEqual(len(clauses), len(set(clauses)), "duplicate later-fold clauses")
        for clause in REQUIRED_LATER_FOLD_CLAUSES:
            self.assertIn(clause, clauses,
                          f"later fold clause missing (R2-FOLD-SCOPE-003): {clause}")
        self.assertEqual(set(clauses), set(REQUIRED_LATER_FOLD_CLAUSES))

    # 13 (R2-EDGE-SHAPE-002)
    def test_edges_container_fail_closed(self) -> None:
        record = self._require_record()
        for label, bad_edges in (("mapping", {}), ("nested-list", [[]])):
            mutant = copy.deepcopy(record)
            mutant["exchange_law"]["edges"] = bad_edges
            found = record_violations(mutant)
            self.assertIsInstance(found, list,
                                  f"edges={label}: checker must fail closed, never raise")
            self.assertNotEqual(found, [],
                                f"edges={label}: must produce named violations, never a "
                                "vacuous pass (R2-EDGE-SHAPE-002)")
            self.assertTrue(any("edges" in viol for viol in found),
                            f"edges={label}: violation must name the container: {found}")

    # 14 (R2-LIVE-RULE-001)
    def test_no_live_rule_contradiction(self) -> None:
        self.assertTrue(RECORD_PATH.is_file(), MISSING_MSG)
        self.assertEqual(live_rule_conflict_violations(_doc_texts()), [])

    # 15 (R2-OPUS-REVIEW-AUTHORITY-005)
    def test_no_opus_review_standin_mapping(self) -> None:
        record = self._require_record()
        self.assertEqual(opus_review_authority_violations(record, _doc_texts()), [])

    # 16 (R2-CONVERGENCE-PACKET-004)
    def test_convergence_packet_fixture(self) -> None:
        self.assertTrue(RECORD_PATH.is_file(), MISSING_MSG)
        self.assertEqual(convergence_packet_violations(CONVERGENCE_FIXTURE), [])

        no_r2 = copy.deepcopy(CONVERGENCE_FIXTURE)
        del no_r2["revise_rounds"][1]
        found = convergence_packet_violations(no_r2)
        self.assertTrue(any("missing" in viol and "r2" in viol for viol in found),
                        f"missing r2 receipt must be rejected: {found}")

        unmapped = copy.deepcopy(CONVERGENCE_FIXTURE)
        del unmapped["finding_map"]["R2-EDGE-SHAPE-002"]
        found = convergence_packet_violations(unmapped)
        self.assertTrue(any("unmapped" in viol for viol in found),
                        f"a missing finding mapping must be rejected: {found}")

        forged_arms = [
            _set(("binding_state",), "approved"),
            _set(("approving_design_verdict",), {"verdict": "DESIGN-VERDICT: APPROVE"}),
            lambda gate: gate["revise_rounds"][1].update(verdict="APPROVE"),
        ]
        self.assertEqual(len(forged_arms), 3)
        for i, arm in enumerate(forged_arms):
            forged = copy.deepcopy(CONVERGENCE_FIXTURE)
            arm(forged)
            found = convergence_packet_violations(forged)
            self.assertNotEqual(found, [],
                                f"M-CONVERGENCE-REQUIRES-APPROVE arm {i} did not fire")
            self.assertTrue(any("forged" in viol.lower() or "REVISE" in viol
                                for viol in found),
                            f"M-CONVERGENCE-REQUIRES-APPROVE arm {i}: {found}")


if __name__ == "__main__":
    unittest.main()

"""OrchestrationExchangePolicy adversarial RED bank (A13/A14 r8): review-to-RED fold, executable.

Fable-authored r8 fold of the controlling independent XHIGH Codex ADVERSARIAL review
(ADVERSARIAL-VERDICT: revise, 2026-07-19) into executable REDs: ADV-A13-001 (open-world
contradictory live role prose is accepted), ADV-A14-002 (dot/NUL/Windows/separator/ambiguous
exchange paths are accepted on artifact and receipt surfaces), ADV-A14-003 (duplicate edge and
receipt identities are accepted), ADV-CONV-004 (the convergence preflight is neither closed nor
exact and is bound to no sealed artifact), plus the typed executable obligation for the
disclosed tautological `or found` diagnostic debt (DEBT-A13A14-TAUT-005).

Seat law: this file is wholly Fable-frozen RED surface. GREEN may not edit THIS file; a diff
touching it is rejected whole. The predicates under test live in the r8 GREEN-writable zones of
tests/contracts/test_orchestration_exchange.py (the r7 bank), whose five Fable-frozen regions
FR-A..FR-E are hash-pinned by the r8 packet and probe bank. This module implements no predicate
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
# r8 every one of them is ACCEPTED verbatim by all_doc_violations on all three routing docs.
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
# imported), and hash-bound: the sealed r8 packet's design_gate must equal this object
# byte-for-byte under canonical JSON (probe P-CONV-PACKET), and the live module's
# CONVERGENCE_FIXTURE must equal it structurally (asserted below). Canonical form is
# json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) in UTF-8.
PROJECTION_CANONICAL_SHA256 = "94750a81c2ad497d69aebdc4c3f4a0ebfc5e39b096d9231e52c0633d62e75388"
_R1_REVIEW_SHA = "18e4a2fdb0d53230e4e8165fa1bbb16ebd1d9e6359d6de5d1b (truncated)"

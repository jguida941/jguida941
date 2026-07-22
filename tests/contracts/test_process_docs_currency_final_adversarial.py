"""Final-adversarial executable RED — the four terminal ADVERSARIAL findings become law.

Authored by the fresh exact `claude-fable-5` delegated DESIGN + executable-RED author
lane (charter `process-doc-currentness-final-adversarial-fable-red-charter-r1.txt`).
`/root` conducts; a DIFFERENT fresh Opus lane builds GREEN; the author never approves.
Pinned base `74fe3ecda8a7bbaba62677df8786937dc88e6265`; reviewed composite patch sha256
`ede602a16fc3e4c2d90e5d5c3f8ab99733ac20ff6d305008d788851fe3544192`.

This module compiles the four stable PROBEABLE findings of
`scratchpad/active/process/process-doc-currentness-final-adversarial-review-r1.md`
(sha256 `566ca277082dbfab38fd2371ed4ff7b30ed2d97a8fddeae8d569593cf706e012`) into
executable evidence: PDC-FINAL-ADV-001 (live w3c-0 conductor-duty sentences plus the
uncaught `Fable integrates and commits` / `Fable, the conductor` / `Fable serves as
conductor` variants), PDC-FINAL-ADV-002 (whitespace-spoofable session identity and the
open successor log that accepts zero conformance, `PROSE_REVIEW_V2` smuggling, and a
`prose_review_waiver` dispatch field), PDC-FINAL-ADV-003 (historical-row `waived=true`
key and system-family `APPROVE` token surviving, and `historical_exempt=true` on the
live w3c document bypassing every check), and PDC-FINAL-ADV-004 (the AGENTS pointer
coexisting with skill lifecycle-ownership claims).

Every failure message begins with the stable fingerprint
`PROCESS-DOC-CURRENTNESS-FINAL-ADVERSARIAL-RED:` and names the exact missing law. Both
frozen predecessors (`test_process_docs_currency.py`,
`test_process_docs_currency_postreview.py`) are imported for pure helpers/anchors only,
stay byte-frozen and GREEN, and their weak surfaces are probed only as stable gap
witnesses — never as assertions GREEN must change them to satisfy. GREEN's closed seam:
add the Fable-duty and skill-ownership forbidden patterns to the policy rows, correct
the three live w3c-0 cadence sentences (`/root` holds verify/integrate/commit; the §15
revision narrative is conserved byte-for-byte, never rewritten), and land the governed
deterministic validator `scripts/organization/process_governance_validator.py`
transcribed exactly from this module's reference section, homed in the same slice.
No test in this module writes to the repository.
"""
from __future__ import annotations

import copy
import importlib.util
import re
import unicodedata
import unittest
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11 (local): pinned backport, same law as predecessors
    import tomli as tomllib

from tests.contracts.test_process_docs_currency import (
    AGENTS_POINTER,
    CLASSES,
    HISTORICAL_RECORD_IDS,
    LEDGER_PATH,
    OPERATOR_LAW,
    R2_REVIEW,
    ROOT,
    SEATS,
    SKILL_FINDING_IDS,
    SKILL_LIFECYCLE_PATTERNS,
    STALE_CONDUCTOR_PATTERNS,
    check_separation,
    check_successor,
)
from tests.contracts.test_process_docs_currency_postreview import (
    AUTHORITY_POLICY_PATH,
    CURRENCY_POLICY_PATH,
    DEMANDED_DISPATCH_SCHEMA,
    DEMANDED_RECORD_SCHEMA,
    PAREN_CONDUCTOR_PATTERN,
    PERSLICE_SOP_PATTERN,
    SKILL_DIR,
    all_currency_rows,
    census_violations,
    closed_dispatch_check,
    closed_separation_check,
    demanded_census,
    history_exemption_violations,
    nested_schema_violations,
    pattern_coverage_violations,
    postreview_scan,
)

FINGERPRINT = "PROCESS-DOC-CURRENTNESS-FINAL-ADVERSARIAL-RED:"

W3C0_PATH = "docs/plans/handoff/w3c-0-design-closure.md"

# --- PDC-FINAL-ADV-001: demanded Fable conductor-duty variant patterns ---------------
# The sealed set + the parenthesized form provably miss every string below (gap
# witnesses asserted in the case). Duty verbs are matched only IMMEDIATELY after the
# Fable subject and `verification` only as the noun near the subject, so the §15
# revision-history narration (`... routing in-session (Fable verifies, integrates, and
# commits; ...)`, `the operator restored Fable-conducts in-session ...`) and lawful
# DESIGN+RED-author prose (`Fable authors every bounded design and executable RED`)
# are never flagged — history is append-only and is conserved, not rewritten.

FABLE_DUTY_PATTERNS = (
    r"(?i)\bfable(?:\s+5)?\s*,\s*(?:the\s+)?conductor\b",
    r"(?i)\bfable(?:\s+5)?\s+(?:serves?|acts?|acting|serving)\s+as\s+(?:the\s+)?conductor\b",
    r"(?i)\bfable(?:\s+5)?\s+integrates?\b",
    r"(?i)\bfable(?:\s+5)?\s+commits?\b",
    r"(?i)\bfable(?:\s+5)?\s+[^.\n]{0,100}\bverification\b",
)

# Exact live stale sentences (single lines of the live file; attack-replay canaries
# conserved even after GREEN corrects the live bytes).
W3C0_STALE_INTEGRATE = (
    "Fable integrate the approved patch in the primary checkout, repeat the preflight, staging,"
)
W3C0_STALE_VERIFICATION = (
    "the FINAL patch → Fable clean-worktree suite + ratchet + named-mutant verification (§6.4) →"
)
W3C0_STALE_COMMITS = (
    "packet-bound patch is rebuilt/reverified/re-reviewed at xhigh → Fable commits the exact approved"
)
REVIEW_NAMED_VARIANTS = (
    "Fable integrates and commits",
    "Fable, the conductor",
    "Fable serves as conductor",
)

# The demanded corrected live lines (the conductor holds these duties).
W3C0_CORRECTED_LINES = (
    "`/root` integrate the approved patch in the primary checkout, repeat the preflight, staging,",
    "the FINAL patch → `/root` clean-worktree suite + ratchet + named-mutant verification (§6.4) →",
    "packet-bound patch is rebuilt/reverified/re-reviewed at xhigh → `/root` commits the exact approved",
)

# §15 revision-history narration: conserved byte-exact in the live file AND provably
# outside every pattern (explicit narrative-history controls; append-only history law).
W3C0_NARRATIVE_CONSERVED = (
    "the operator restored Fable-conducts in-session on 2026-07-16",
    "operator restored the Fable-conducts routing in-session (Fable verifies, integrates, and\n"
    "commits; Codex reviews only)",
    "one finding (Fable-conducts propagation through surviving rev15 blocks)",
)

LAWFUL_AUTHORSHIP_CONTROLS = (
    "Fable 5 is the delegated DESIGN + RED author",
    "Fable authors every bounded design and executable RED",
    "Fable is the delegated design and executable-RED author",
    "Fable-authored scratch design (bounded section referencing THIS document's laws)",
    "Fable-authored homed RED",
    "authored by FABLE (design author) while an emergency seat draft (Codex to "
    "orchestrate/integrate/commit) was under consideration",
    "Fable does not implement GREEN, review or approve its own artifacts, integrate, "
    "commit, merge, or push",
    "(Fable verifies, integrates, and commits; Codex reviews only)",
    "the conductor seat (formerly Fable's) is `/root`",
)

# --- PDC-FINAL-ADV-004: demanded skill lifecycle-OWNERSHIP patterns ------------------
# A skill file may carry the AGENTS pointer; it may never also CLAIM the lifecycle.

SKILL_OWNERSHIP_PATTERNS = (
    r"(?i)\b(?:this|the)\s+(?:skill|reference|lane)\s+(?:dispatches|approves|integrates|commits|merges|reviews)\b",
    r"(?i)\b(?:this|the)\s+(?:skill|reference|lane)\s+owns\s+(?:the\s+)?(?:dispatch|approval|review|integration|commit|lifecycle)\b",
)

OWNERSHIP_ATTACKS = (
    "This skill owns dispatch, approval, integration, and commits.",
    "This skill dispatches the GREEN builder itself.",
    "The skill approves its own patches.",
    "this reference integrates and commits when green.",
    "This lane reviews and merges the final patch.",
    "the skill owns the lifecycle end to end.",
)

DOMAIN_METHOD_CONTROLS = (
    "this skill owns no lifecycle and mints no verdict",
    "this lane carries only the proving method",
    "the independent codex review and the commit run under `AGENTS.md`'s slice SOP and "
    "role seats; fold review disagreements RED-first",
    "lifecycle, seats, gates, and commits are governed by `AGENTS.md` (operator process "
    "correction 2026-07-22)",
    "Slice lifecycle, role seats, review gates, and commit authority are governed by `AGENTS.md`",
)

# --- PDC-FINAL-ADV-002/003: the demanded governed deterministic validator ------------
# The closed laws below are executable here as the REFERENCE; GREEN transcribes this
# reference section exactly into the governed artifact and homes it in the same slice.

VALIDATOR_REL_PATH = "scripts/organization/process_governance_validator.py"
VALIDATOR_PATH = ROOT / "scripts" / "organization" / "process_governance_validator.py"
VALIDATOR_CALLABLES = (
    "canonicalize_session",
    "closed_identity_check",
    "dispatch_payload_check",
    "closed_successor_log_check",
    "closed_policy_rows_check",
    "exemption_closure_check",
    "exemption_aware_scan",
)

LAWFUL_EXEMPT_PREFIXES = ("docs/history/",)
LIFECYCLE_KINDS = ("RED_ACCEPTED", "CONFORMANCE_PASSED", "GREEN_DISPATCH")

EXPECTED_META = {
    "contract_id": "ProcessDocsCurrencyPolicy",
    "schema_version": 1,
    "ratified": "2026-07-22",
    "law_source": OPERATOR_LAW,
    "authority_doc": "AGENTS.md",
}
EXPECTED_SEPARATION_FLAGS = {
    "reviewer_may_author_red": False,
    "red_author_may_build_green": False,
    "author_approves_own_artifact": False,
}
EXPECTED_SUCCESSOR_SCALARS = {
    "max_conformance_checks": 1,
    "required_next_event": "GREEN_DISPATCH",
    "green_builder": "opus",
    "forbidden_after_red_accepted": ["PROSE_REVIEW", "REVIEW_OF_REVIEW"],
}
EXPECTED_LINEAGE = {
    "prose_review_cap": 2,
    "terminal_verdicts": ["REVISE", "APPROVE"],
    "identity_preserving_events": ["CORRECTION", "RENAME", "VERSION_BUMP", "SUCCESSOR_PACKET"],
    "reset_events": [],
}
EXPECTED_FAMILY_ROWS = (
    {
        "family_id": "semantic-tdd-conductor-skill",
        "prose_reviews_used": 1,
        "terminal_verdict_token": "SKILL-DESIGN-VERDICT: REVISE",
        "another_prose_review_authorized": False,
        "findings": list(SKILL_FINDING_IDS),
        "terminal_review_doc": R2_REVIEW,
    },
    {
        "family_id": "build-lane-contract-system",
        "prose_reviews_used": 2,
        "terminal_verdict_token": "CONTRACT-DESIGN-VERDICT: REVISE",
        "another_prose_review_authorized": False,
    },
)
HISTORICAL_ROW_KEYS = {"path", "sha256", "enforcement"}
EXPECTED_HISTORICAL_ROWS = tuple(
    {"path": path, "sha256": sha, "enforcement": "identity"}
    for path, sha in HISTORICAL_RECORD_IDS.items()
)


# === reference implementation (GREEN transcribes this section into the artifact) =====


def canonicalize_session(value):
    """Canonical identity form for seats and session ids: NFKC-normalize, drop
    Unicode format (Cf) characters, strip edge whitespace, casefold. Two ids are
    the SAME logical session iff their canonical forms are equal; a field whose
    bytes differ from its own canonical form is a spoof and fails closed."""
    if not isinstance(value, str):
        return None
    text = unicodedata.normalize("NFKC", value)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Cf")
    return text.strip().casefold()


def closed_identity_check(record: dict, schema: dict, roles: dict) -> list[str]:
    """PDC-FINAL-ADV-002: the closed six-field identity payload with CANONICAL
    session law — trailing whitespace, case aliasing, zero-width and width tricks
    can never make the same logical session count as distinct."""
    violations = []
    required = list(schema["required_keys"])
    for key in required:
        value = record.get(key)
        if not isinstance(value, str) or not value.strip():
            violations.append(f"missing or empty identity field: {key}")
    if schema.get("allow_unknown_keys", True) is False:
        for key in sorted(set(record) - set(required)):
            violations.append(f"unknown identity field: {key}")
    if violations:
        return violations
    for key in required:
        if record[key] != canonicalize_session(record[key]):
            violations.append(f"non-canonical identity field: {key}")
    if violations:
        return violations
    if record["reviewer_seat"] != roles["reviewer"]:
        violations.append("reviewer_seat must equal the policy reviewer seat")
    if record["reviewer_seat"] == roles["design_red_author"]:
        violations.append("the RED author seat may not approve, even across different sessions")
    if record["reviewer_seat"] == roles["green_builder"]:
        violations.append("the GREEN builder seat may not approve, even across different sessions")
    if record["red_author_seat"] != roles["design_red_author"]:
        violations.append("the governing RED author seat must be the delegated DESIGN + RED author")
    if record["green_builder_seat"] != roles["green_builder"]:
        violations.append("GREEN must be built by the delegated Opus builder seat")
    distinct_pairs = (
        ("reviewer_session", "red_author_session",
         "the reviewer session must be canonically distinct from the RED author session"),
        ("reviewer_session", "green_builder_session",
         "the reviewer session must be canonically distinct from the GREEN builder session"),
        ("green_builder_session", "red_author_session",
         "the GREEN builder session must be canonically distinct from the RED author "
         "session — the RED author may not build GREEN"),
    )
    for left, right, message in distinct_pairs:
        if canonicalize_session(record[left]) == canonicalize_session(record[right]):
            violations.append(message)
    return violations


def dispatch_payload_check(payload: dict, schema: dict, successor: dict) -> list[str]:
    """The GREEN_DISPATCH payload under the policy's closed dispatch schema with
    the canonical session law applied (the schema is APPLIED, not merely declared)."""
    violations = []
    required = list(schema["required_keys"])
    allowed = set(schema["allowed_keys"])
    for key in required:
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            violations.append(f"missing or empty dispatch field: {key}")
    for key in sorted(set(payload) - allowed):
        violations.append(f"unknown dispatch field: {key}")
    if violations:
        return violations
    for key in required:
        if payload[key] != canonicalize_session(payload[key]):
            violations.append(f"non-canonical dispatch field: {key}")
    if violations:
        return violations
    if payload["builder_seat"] != successor["green_builder"]:
        violations.append("the GREEN successor must be the Opus builder seat")
    if canonicalize_session(payload["builder_session"]) == canonicalize_session(
        payload["red_author_session"]
    ):
        violations.append(
            "the GREEN successor session must be canonically distinct from the RED author session"
        )
    return violations


def closed_successor_log_check(events, policy: dict) -> list[str]:
    """PDC-FINAL-ADV-002: the successor lifecycle log is CLOSED — known event kinds
    only, exactly one accepted RED, the one bounded conformance check must OCCUR
    after acceptance, GREEN_DISPATCH immediately follows it and is final, and the
    dispatch payload is validated against successor.dispatch_schema."""
    successor = policy["successor"]
    schema = successor["dispatch_schema"]
    allowed_kinds = set(LIFECYCLE_KINDS) | set(successor["forbidden_after_red_accepted"])
    violations = []
    kinds = [kind for kind, _ in events]
    for kind in kinds:
        if kind not in allowed_kinds:
            violations.append(f"unknown lifecycle event: {kind}")
    if kinds.count("RED_ACCEPTED") != 1:
        violations.append("the lifecycle log must contain exactly one RED_ACCEPTED")
    conformance_count = kinds.count("CONFORMANCE_PASSED")
    if conformance_count > successor["max_conformance_checks"]:
        violations.append("more than the one bounded RED-SPEC-CONFORMANCE check")
    if conformance_count < successor["max_conformance_checks"]:
        violations.append("the one bounded RED-SPEC-CONFORMANCE check never ran")
    if "RED_ACCEPTED" in kinds:
        accepted = kinds.index("RED_ACCEPTED")
        if "CONFORMANCE_PASSED" in kinds and kinds.index("CONFORMANCE_PASSED") < accepted:
            violations.append("the conformance check must follow the accepted RED")
        for kind in kinds[accepted + 1 :]:
            if kind in successor["forbidden_after_red_accepted"]:
                violations.append(f"forbidden review event after accepted RED: {kind}")
    if kinds.count("GREEN_DISPATCH") != 1:
        violations.append("the lifecycle log must contain exactly one GREEN_DISPATCH")
    else:
        dispatch_index = kinds.index("GREEN_DISPATCH")
        if dispatch_index != len(kinds) - 1:
            violations.append("GREEN_DISPATCH must be the final lifecycle event")
        if conformance_count == 1 and kinds.index("CONFORMANCE_PASSED") + 1 != dispatch_index:
            violations.append("GREEN_DISPATCH must immediately follow the bounded conformance check")
        violations.extend(dispatch_payload_check(events[dispatch_index][1], schema, successor))
    return violations


def closed_policy_rows_check(policy: dict) -> list[str]:
    """PDC-FINAL-ADV-003: every nested row is key-closed and every terminal value is
    pinned — a smuggled historical-row key (waived=true) and a rewritten system-family
    terminal token (APPROVE) both fail closed."""
    violations = []
    if policy.get("meta") != EXPECTED_META:
        violations.append("meta must equal the five conserved terminal values exactly")
    if policy.get("roles") != SEATS:
        violations.append("roles must equal the four ratified seats exactly")
    separation = policy.get("separation", {})
    if {key: separation.get(key) for key in EXPECTED_SEPARATION_FLAGS} != EXPECTED_SEPARATION_FLAGS:
        violations.append("separation flags must stay the three conserved false values")
    if separation.get("record_schema") != DEMANDED_RECORD_SCHEMA:
        violations.append("separation.record_schema must equal the closed six-field payload exactly")
    successor = policy.get("successor", {})
    if {key: successor.get(key) for key in EXPECTED_SUCCESSOR_SCALARS} != EXPECTED_SUCCESSOR_SCALARS:
        violations.append(
            "successor scalars must equal the conserved terminal values "
            "(one bounded conformance check, GREEN_DISPATCH next, opus builder, closed forbidden list)"
        )
    if successor.get("dispatch_schema") != DEMANDED_DISPATCH_SCHEMA:
        violations.append("successor.dispatch_schema must equal the closed three-field payload exactly")
    if policy.get("lineage") != EXPECTED_LINEAGE:
        violations.append("lineage must equal the conserved terminal values exactly")
    if policy.get("transition_classes", {}).get("classes") != CLASSES:
        violations.append("transition_classes must equal the closed five-class enum exactly")
    families = policy.get("review_families", [])
    if len(families) != len(EXPECTED_FAMILY_ROWS):
        violations.append("review_families must be exactly the two terminal families, in order")
    else:
        for family, expected in zip(families, EXPECTED_FAMILY_ROWS):
            family_id = expected["family_id"]
            unknown = sorted(set(family) - set(expected))
            if unknown:
                violations.append(f"{family_id}: unknown review-family keys {unknown}")
            missing = sorted(set(expected) - set(family))
            if missing:
                violations.append(f"{family_id}: missing review-family keys {missing}")
            for key in sorted(set(expected) & set(family)):
                if family[key] != expected[key]:
                    violations.append(f"{family_id}: field {key!r} must equal the conserved terminal value")
    records = policy.get("currency", {}).get("historical_records", [])
    if len(records) != len(EXPECTED_HISTORICAL_ROWS):
        violations.append("currency.historical_records must be exactly the five conserved rows, in order")
    else:
        for record, expected in zip(records, EXPECTED_HISTORICAL_ROWS):
            path = expected["path"]
            unknown = sorted(set(record) - HISTORICAL_ROW_KEYS)
            if unknown:
                violations.append(f"{path}: unknown historical-record row keys {unknown}")
            missing = sorted(HISTORICAL_ROW_KEYS - set(record))
            if missing:
                violations.append(f"{path}: missing historical-record row keys {missing}")
            for key in sorted(HISTORICAL_ROW_KEYS & set(record)):
                if record[key] != expected[key]:
                    violations.append(f"{path}: field {key!r} must equal the conserved terminal value")
    return violations


def exemption_closure_check(policy: dict) -> list[str]:
    """PDC-FINAL-ADV-003: `historical_exempt` is lawful ONLY on declared history
    paths — marking a live document historical is a scan bypass and fails closed."""
    violations = []
    prefixes = policy.get("currency", {}).get("historical_exempt_prefixes")
    if prefixes != list(LAWFUL_EXEMPT_PREFIXES):
        violations.append(
            "historical_exempt_prefixes must equal exactly ['docs/history/'] — "
            "widening the exemption surface is a bypass"
        )
    for row in all_currency_rows(policy):
        path = row.get("path", "<missing path>")
        flag = row.get("historical_exempt")
        if flag is None or flag is False:
            continue
        if flag is not True:
            violations.append(f"{path}: historical_exempt must be a boolean, got {flag!r}")
            continue
        if not path.startswith(LAWFUL_EXEMPT_PREFIXES):
            violations.append(
                f"{path}: historical_exempt on a non-declared-history path — "
                "live documents may never be exempted from scanning"
            )
    return violations


def exemption_aware_scan(policy: dict, rel_path: str, text: str) -> list[str]:
    """Currency scan over the sealed + postreview roster union that honors the
    history exemption ONLY for declared history paths: an unlawfully exempted live
    row is scanned anyway (fail closed), so exemption flags cannot bypass the
    pattern, proposition, or malicious-text checks."""
    rows: dict[str, dict] = {}
    for row in all_currency_rows(policy):
        rows.setdefault(row.get("path", ""), row)
    row = rows.get(rel_path)
    if row is None:
        return [f"undeclared document: {rel_path}"]
    if rel_path.startswith(LAWFUL_EXEMPT_PREFIXES):
        return []
    violations = []
    for pattern in row.get("forbidden_patterns", []):
        if re.search(pattern, text):
            violations.append(f"{rel_path}: forbidden pattern matched: {pattern}")
    for proposition in row.get("required_propositions", []):
        if proposition not in text:
            violations.append(f"{rel_path}: required proposition absent: {proposition!r}")
    return violations


# === end of the reference section GREEN transcribes ==================================


def duty_pattern_coverage_violations(policy: dict) -> list[str]:
    """PDC-FINAL-ADV-001/004 coverage demand: every nonhistorical governed row must
    forbid the Fable conductor-duty variants; skill-role rows must also forbid the
    lifecycle-ownership claims."""
    violations = []
    for row in all_currency_rows(policy):
        path = row.get("path", "")
        if row.get("historical_exempt", False) or path.startswith(LAWFUL_EXEMPT_PREFIXES):
            continue
        declared = row.get("forbidden_patterns", [])
        for pattern in FABLE_DUTY_PATTERNS:
            if pattern not in declared:
                violations.append(f"{path}: missing conductor-duty pattern {pattern}")
        if row.get("role", "") in ("skill", "skill_reference"):
            for pattern in SKILL_OWNERSHIP_PATTERNS:
                if pattern not in declared:
                    violations.append(f"{path}: missing lifecycle-ownership pattern {pattern}")
    return violations


def demanded_final_policy(policy: dict) -> dict:
    """The exact demanded GREEN policy state: the live policy plus the duty patterns
    on every nonhistorical row and the ownership patterns on every skill-role row."""
    lawful = copy.deepcopy(policy)
    for row in all_currency_rows(lawful):
        path = row.get("path", "")
        if row.get("historical_exempt", False) or path.startswith(LAWFUL_EXEMPT_PREFIXES):
            continue
        declared = row.setdefault("forbidden_patterns", [])
        for pattern in FABLE_DUTY_PATTERNS:
            if pattern not in declared:
                declared.append(pattern)
        if row.get("role", "") in ("skill", "skill_reference"):
            for pattern in SKILL_OWNERSHIP_PATTERNS:
                if pattern not in declared:
                    declared.append(pattern)
    return lawful


def load_governed_validator():
    """Load the demanded governed validator artifact; None while it is absent.
    Loaded via its file path so a missing artifact is a fingerprinted failure,
    never an import/collection error."""
    if not VALIDATOR_PATH.is_file():
        return None, "absent"
    spec = importlib.util.spec_from_file_location("process_governance_validator", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        return None, "unloadable"
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # a broken artifact is a red failure, not a harness error
        return None, f"failed to execute: {exc!r}"
    return module, "loaded"


class ProcessDocsCurrencyFinalAdversarialRed(unittest.TestCase):
    """6 cases; every failure begins with the stable final-adversarial fingerprint."""

    maxDiff = None

    def setUp(self) -> None:
        for path in (CURRENCY_POLICY_PATH, AUTHORITY_POLICY_PATH):
            if not path.is_file():
                self.fail(
                    f"{FINGERPRINT} finished-state overlay incomplete: "
                    f"{path.relative_to(ROOT).as_posix()} absent"
                )
        self.policy = tomllib.loads(CURRENCY_POLICY_PATH.read_text(encoding="utf-8"))
        self.authority = tomllib.loads(AUTHORITY_POLICY_PATH.read_text(encoding="utf-8"))
        self.skill_census = tuple(
            sorted(
                p.relative_to(ROOT).as_posix()
                for p in (ROOT / SKILL_DIR).rglob("*.md")
                if p.is_file()
            )
        )
        self.lawful_final = demanded_final_policy(self.policy)

    # --- fingerprinted assertion helpers ----------------------------------------

    def _red(self, condition: bool, detail: str) -> None:
        if not condition:
            self.fail(f"{FINGERPRINT} {detail}")

    def _red_empty(self, violations: list[str], detail: str) -> None:
        if violations:
            self.fail(f"{FINGERPRINT} {detail}: " + " | ".join(violations))

    def _demand_validator(self, law: str, callables) -> object:
        module, state = load_governed_validator()
        self._red(
            module is not None,
            f"{law} is not yet an executable governed artifact: {VALIDATOR_REL_PATH} "
            f"{state} — GREEN must land it transcribed exactly from this module's "
            f"reference section (demanded callables: {', '.join(callables)}) and home "
            "it in the same slice",
        )
        for name in callables:
            self._red(
                callable(getattr(module, name, None)),
                f"governed validator lacks the demanded callable {name}",
            )
        return module

    # --- PDC-FINAL-ADV-001: live docs forbid the Fable conductor-duty variants ---

    def test_live_docs_forbid_fable_conductor_duty_variants(self) -> None:
        sealed_union = list(STALE_CONDUCTOR_PATTERNS) + [PAREN_CONDUCTOR_PATTERN]
        demanded_union = sealed_union + list(FABLE_DUTY_PATTERNS)
        # Witnesses: the three live stale sentences and the three review-named
        # variants are killed by the demanded set and provably escape the sealed set.
        for witness in (
            W3C0_STALE_INTEGRATE,
            W3C0_STALE_VERIFICATION,
            W3C0_STALE_COMMITS,
        ) + REVIEW_NAMED_VARIANTS:
            self._red(
                any(re.search(pattern, witness) for pattern in FABLE_DUTY_PATTERNS),
                f"MUT-FABLE-DUTY-VARIANT-MISSED survived: the demanded duty set must "
                f"kill {witness!r}",
            )
            self._red(
                all(re.search(pattern, witness) is None for pattern in sealed_union),
                f"gap witness drifted: the sealed stale set unexpectedly catches "
                f"{witness!r} — re-derive the final-adversarial pattern law",
            )
        # Punctuation/verb variants each die on its named pattern.
        for variant, pattern in (
            ("Fable 5, the conductor, resolves every dispute.", FABLE_DUTY_PATTERNS[0]),
            ("fable  ,  the  Conductor", FABLE_DUTY_PATTERNS[0]),
            ("Fable acts as the conductor", FABLE_DUTY_PATTERNS[1]),
            ("fable serving as conductor", FABLE_DUTY_PATTERNS[1]),
            ("FABLE 5 INTEGRATES the final patch.", FABLE_DUTY_PATTERNS[2]),
            ("fable commit the exact approved diff", FABLE_DUTY_PATTERNS[3]),
            ("Fable re-runs the suite + ratchet verification in the clean worktree",
             FABLE_DUTY_PATTERNS[4]),
        ):
            self._red(
                re.search(pattern, variant) is not None,
                f"MUT-FABLE-DUTY-VARIANT-MISSED survived on variant: {variant!r}",
            )
        # Lawful DESIGN+RED-author controls and the §15 narrative recall must
        # escape the entire demanded union (append-only history is never flagged).
        for control in LAWFUL_AUTHORSHIP_CONTROLS + W3C0_NARRATIVE_CONSERVED:
            self._red(
                all(re.search(pattern, control) is None for pattern in demanded_union),
                f"MUT-NARRATIVE-OR-AUTHORSHIP-FLAGGED: lawful or historical prose "
                f"must survive: {control!r}",
            )
        # Narrative history is conserved byte-exact in the live file.
        live_w3c0 = (ROOT / W3C0_PATH).read_text(encoding="utf-8")
        for conserved in W3C0_NARRATIVE_CONSERVED:
            self._red(
                conserved in live_w3c0,
                "MUT-NARRATIVE-HISTORY-REWRITTEN survived: the §15 revision narration "
                f"must stay byte-present (append-only history): {conserved[:60]!r}…",
            )
        # The demanded lawful policy state validates clean (satisfiability).
        self._red_empty(
            duty_pattern_coverage_violations(self.lawful_final),
            "the demanded lawful duty-pattern state must itself validate clean",
        )
        # MUT-DUTY-PATTERN-ROW-DROPPED: removing the duty set from one row reddens.
        dropped = copy.deepcopy(self.lawful_final)
        for row in all_currency_rows(dropped):
            if row.get("path") == W3C0_PATH:
                row["forbidden_patterns"] = [
                    pattern for pattern in row["forbidden_patterns"]
                    if pattern not in FABLE_DUTY_PATTERNS
                ]
        self._red(
            any(
                W3C0_PATH in violation and "missing conductor-duty pattern" in violation
                for violation in duty_pattern_coverage_violations(dropped)
            ),
            "MUT-DUTY-PATTERN-ROW-DROPPED survived: a row without the duty set must redden",
        )
        # The live demand: rows carry the duty set; every census doc scans clean of
        # conductor-duty text; the three corrected `/root` lines are live.
        violations = [
            violation
            for violation in duty_pattern_coverage_violations(self.policy)
            if "missing conductor-duty pattern" in violation
        ]
        for path in sorted(demanded_census(self.authority, self.policy, self.skill_census)):
            live = ROOT / path
            if not live.is_file():
                violations.append(f"{path}: live doc missing from tree")
                continue
            text = live.read_text(encoding="utf-8")
            for pattern in demanded_union:
                if re.search(pattern, text):
                    violations.append(f"{path}: stale conductor-duty authority matched: {pattern}")
        for corrected in W3C0_CORRECTED_LINES:
            if corrected not in live_w3c0:
                violations.append(
                    f"{W3C0_PATH}: corrected conductor line absent: {corrected[:60]!r}…"
                )
        self._red_empty(
            violations,
            "live documents still assign Fable the conductor's verify/integrate/commit "
            "duties and the policy does not forbid the variants",
        )

    # --- PDC-FINAL-ADV-002: canonical session identity ---------------------------

    def test_identity_sessions_are_canonical_and_distinct(self) -> None:
        roles = self.policy["roles"]
        schema = self.policy["separation"]["record_schema"]
        lawful = {
            "red_author_seat": "fable", "red_author_session": "fable-s1",
            "reviewer_seat": "codex", "reviewer_session": "codex-s1",
            "green_builder_seat": "opus", "green_builder_session": "opus-s2",
        }
        # Canonicalization vectors (the reference law).
        for raw, canonical in (
            ("fable-s1 ", "fable-s1"),
            (" fable-s1", "fable-s1"),
            ("FABLE-S1", "fable-s1"),
            ("fable-s1​", "fable-s1"),
            ("ｆａｂｌｅ－ｓ１", "fable-s1"),
            ("opus-s2", "opus-s2"),
        ):
            self._red(
                canonicalize_session(raw) == canonical,
                f"canonicalize_session({raw!r}) must be {canonical!r}",
            )
        # Stable gap witnesses: BOTH frozen validators accept the whitespace-spoofed
        # builder session as distinct (the exact adversarial replay).
        whitespace_spoof = dict(lawful, green_builder_session="fable-s1 ")
        self._red(
            check_separation(whitespace_spoof, self.policy) == []
            and closed_separation_check(whitespace_spoof, DEMANDED_RECORD_SCHEMA, roles) == [],
            "gap witness drifted: the frozen validators now reject the whitespace-"
            "spoofed session — re-derive this case against them",
        )
        self._red_empty(
            closed_identity_check(lawful, schema, roles),
            "the lawful canonical record must validate clean",
        )
        # MUT-SESSION-TRAILING-WHITESPACE: the same logical session with trailing
        # whitespace must fail closed, never count as distinct.
        found = closed_identity_check(whitespace_spoof, schema, roles)
        self._red(
            any("non-canonical identity field: green_builder_session" in v for v in found),
            f"MUT-SESSION-TRAILING-WHITESPACE survived: got {found}",
        )
        # MUT-SESSION-CASE-ALIAS: case aliasing cannot make sessions distinct.
        case_alias = dict(lawful, green_builder_session="FABLE-S1")
        self._red(
            any("non-canonical identity field: green_builder_session" in v
                for v in closed_identity_check(case_alias, schema, roles)),
            "MUT-SESSION-CASE-ALIAS survived: a case-aliased session must fail closed",
        )
        # MUT-SESSION-ZERO-WIDTH-SMUGGLE and MUT-SESSION-WIDTH-ALIAS.
        for spoof, mutant in (
            ("fable-s1​", "MUT-SESSION-ZERO-WIDTH-SMUGGLE"),
            ("ｆａｂｌｅ－ｓ１", "MUT-SESSION-WIDTH-ALIAS"),
        ):
            smuggled = dict(lawful, green_builder_session=spoof)
            self._red(
                any("non-canonical identity field: green_builder_session" in v
                    for v in closed_identity_check(smuggled, schema, roles)),
                f"{mutant} survived on {spoof!r}",
            )
        # Canonical distinctness: literal equality after canonicalization dies.
        shared = dict(lawful, green_builder_session="fable-s1")
        self._red(
            any("the RED author may not build GREEN" in v
                for v in closed_identity_check(shared, schema, roles)),
            "canonical-collision law missing: a shared canonical session must be rejected",
        )
        # Controls: distinct-but-similar ids stay lawful; the closed payload holds.
        near_miss = dict(lawful, green_builder_session="fable-s10")
        near_violations = [
            v for v in closed_identity_check(near_miss, schema, roles)
            if "session" in v and "canonically" in v
        ]
        self._red(
            near_violations == [],
            f"false positive: fable-s10 is a DISTINCT session, got {near_violations}",
        )
        self._red(
            any("unknown identity field: conductor_seat" in v
                for v in closed_identity_check(dict(lawful, conductor_seat="/root"), schema, roles)),
            "closed identity payload drifted: unknown fields must still fail closed",
        )
        # The law must be a governed executable artifact; then it must agree with
        # the reference on every vector.
        module = self._demand_validator(
            "canonical session-identity law", ("canonicalize_session", "closed_identity_check")
        )
        for raw in ("fable-s1 ", " fable-s1", "FABLE-S1", "fable-s1​", "opus-s2", 7, None):
            self._red(
                module.canonicalize_session(raw) == canonicalize_session(raw),
                f"landed canonicalize_session diverges from the reference on {raw!r}",
            )
        for record in (lawful, whitespace_spoof, case_alias, shared, near_miss,
                       dict(lawful, conductor_seat="/root"),
                       dict(lawful, reviewer_seat="fable", reviewer_session="fable-s7"),
                       {key: value for key, value in lawful.items() if key != "reviewer_session"}):
            self._red(
                module.closed_identity_check(dict(record), dict(schema), dict(roles))
                == closed_identity_check(dict(record), dict(schema), dict(roles)),
                f"landed closed_identity_check diverges from the reference on {record!r}",
            )

    # --- PDC-FINAL-ADV-002: the closed successor log ------------------------------

    def test_successor_log_is_closed_requires_one_conformance_and_validates_dispatch(self) -> None:
        lawful_dispatch = {
            "builder_seat": "opus", "builder_session": "opus-s2",
            "red_author_session": "fable-s1",
        }
        lawful_log = (
            ("RED_ACCEPTED", {}),
            ("CONFORMANCE_PASSED", {}),
            ("GREEN_DISPATCH", dict(lawful_dispatch)),
        )
        zero_conformance = (("RED_ACCEPTED", {}),)
        smuggled_kind = (
            ("RED_ACCEPTED", {}),
            ("PROSE_REVIEW_V2", {"verdict": "REVISE"}),
            ("CONFORMANCE_PASSED", {}),
            ("GREEN_DISPATCH", dict(lawful_dispatch)),
        )
        waiver_log = (
            ("RED_ACCEPTED", {}),
            ("CONFORMANCE_PASSED", {}),
            ("GREEN_DISPATCH", dict(lawful_dispatch, prose_review_waiver="granted")),
        )
        whitespace_successor = (
            ("RED_ACCEPTED", {}),
            ("CONFORMANCE_PASSED", {}),
            ("GREEN_DISPATCH", dict(lawful_dispatch, builder_session="fable-s1 ")),
        )
        # Stable gap witnesses: the frozen check_successor accepts all four attacks;
        # the frozen closed_dispatch_check accepts the whitespace successor.
        self._red(
            check_successor(zero_conformance, self.policy) == []
            and check_successor(smuggled_kind, self.policy) == []
            and check_successor(waiver_log, self.policy) == []
            and check_successor(whitespace_successor, self.policy) == [],
            "gap witness drifted: the frozen check_successor now rejects the "
            "zero-conformance/smuggled/waiver/whitespace attacks — re-derive this case",
        )
        self._red(
            closed_dispatch_check(
                dict(lawful_dispatch, builder_session="fable-s1 "),
                DEMANDED_DISPATCH_SCHEMA,
                self.policy["successor"],
            ) == [],
            "gap witness drifted: the frozen closed_dispatch_check now rejects the "
            "whitespace successor — re-derive this case",
        )
        # The closed law: lawful log clean; each attack dies for its named reason.
        self._red_empty(
            closed_successor_log_check(lawful_log, self.policy),
            "the lawful successor lifecycle log must validate clean",
        )
        self._red(
            any("the one bounded RED-SPEC-CONFORMANCE check never ran" in v
                for v in closed_successor_log_check(zero_conformance, self.policy))
            and any("exactly one GREEN_DISPATCH" in v
                    for v in closed_successor_log_check(zero_conformance, self.policy)),
            "MUT-ZERO-CONFORMANCE-DISPATCHLESS-LOG survived: a log with no conformance "
            "check and no dispatch must fail closed",
        )
        self._red(
            any("unknown lifecycle event: PROSE_REVIEW_V2" in v
                for v in closed_successor_log_check(smuggled_kind, self.policy)),
            "MUT-EVENT-NAME-SMUGGLED survived: an unknown event kind must fail closed",
        )
        self._red(
            any("unknown dispatch field: prose_review_waiver" in v
                for v in closed_successor_log_check(waiver_log, self.policy)),
            "MUT-DISPATCH-WAIVER-RIDES-LOG survived: the closed dispatch schema must "
            "be APPLIED to the log's GREEN_DISPATCH payload",
        )
        self._red(
            any("non-canonical dispatch field: builder_session" in v
                for v in closed_successor_log_check(whitespace_successor, self.policy)),
            "MUT-WHITESPACE-SUCCESSOR-SPOOF survived: a whitespace-aliased successor "
            "session must fail closed",
        )
        canonical_collision = (
            ("RED_ACCEPTED", {}),
            ("CONFORMANCE_PASSED", {}),
            ("GREEN_DISPATCH", dict(lawful_dispatch, builder_session="fable-s1")),
        )
        self._red(
            any("canonically distinct from the RED author session" in v
                for v in closed_successor_log_check(canonical_collision, self.policy)),
            "the RED author session building GREEN must be rejected canonically",
        )
        not_final = lawful_log + (("CONFORMANCE_PASSED", {}),)
        found = closed_successor_log_check(not_final, self.policy)
        self._red(
            any("GREEN_DISPATCH must be the final lifecycle event" in v for v in found)
            and any("more than the one bounded" in v for v in found),
            f"MUT-DISPATCH-NOT-FINAL survived: got {found}",
        )
        conformance_first = (
            ("CONFORMANCE_PASSED", {}),
            ("RED_ACCEPTED", {}),
            ("GREEN_DISPATCH", dict(lawful_dispatch)),
        )
        found = closed_successor_log_check(conformance_first, self.policy)
        self._red(
            any("must follow the accepted RED" in v for v in found)
            and any("immediately follow the bounded conformance check" in v for v in found),
            f"MUT-CONFORMANCE-BEFORE-ACCEPTANCE survived: got {found}",
        )
        prose_after = (
            ("RED_ACCEPTED", {}),
            ("PROSE_REVIEW", {"verdict": "REVISE"}),
            ("CONFORMANCE_PASSED", {}),
            ("GREEN_DISPATCH", dict(lawful_dispatch)),
        )
        self._red(
            any("forbidden review event after accepted RED: PROSE_REVIEW" in v
                for v in closed_successor_log_check(prose_after, self.policy)),
            "a prose review after the accepted RED must stay forbidden in the closed log",
        )
        # The law must be a governed executable artifact agreeing on every vector.
        module = self._demand_validator(
            "the closed successor-log law",
            ("closed_successor_log_check", "dispatch_payload_check"),
        )
        for log in (lawful_log, zero_conformance, smuggled_kind, waiver_log,
                    whitespace_successor, canonical_collision, not_final,
                    conformance_first, prose_after):
            self._red(
                module.closed_successor_log_check(tuple(log), copy.deepcopy(self.policy))
                == closed_successor_log_check(tuple(log), copy.deepcopy(self.policy)),
                f"landed closed_successor_log_check diverges from the reference on {log!r}",
            )

    # --- PDC-FINAL-ADV-003: exact nested-row and terminal-value closure -----------

    def test_nested_rows_and_terminal_values_are_exactly_closed(self) -> None:
        waived = copy.deepcopy(self.policy)
        waived["currency"]["historical_records"][0]["waived"] = True
        approved = copy.deepcopy(self.policy)
        approved["review_families"][1]["terminal_verdict_token"] = "CONTRACT-DESIGN-VERDICT: APPROVE"
        # Stable gap witnesses: both exact adversarial replays survive the frozen
        # nested-closure validator.
        self._red(
            nested_schema_violations(waived) == [] and nested_schema_violations(approved) == [],
            "gap witness drifted: the frozen nested_schema_violations now rejects the "
            "waived-key/APPROVE replays — re-derive this case against it",
        )
        # The conserved live policy passes the closed law (guard: value drift reddens).
        self._red_empty(
            closed_policy_rows_check(self.policy),
            "the live policy drifted from the conserved terminal values",
        )
        # MUT-HISTORICAL-ROW-KEY-SMUGGLED: the exact waived=true replay dies.
        found = closed_policy_rows_check(waived)
        self._red(
            any("unknown historical-record row keys ['waived']" in v for v in found),
            f"MUT-HISTORICAL-ROW-KEY-SMUGGLED survived: got {found}",
        )
        # MUT-SYSTEM-TERMINAL-TOKEN-APPROVED: the exact APPROVE replay dies.
        found = closed_policy_rows_check(approved)
        self._red(
            any("build-lane-contract-system" in v
                and "'terminal_verdict_token'" in v for v in found),
            f"MUT-SYSTEM-TERMINAL-TOKEN-APPROVED survived: got {found}",
        )
        # MUT-SKILL-FINDINGS-ROSTER-DRIFT: dropping a conserved finding id dies.
        drifted = copy.deepcopy(self.policy)
        drifted["review_families"][0]["findings"] = list(SKILL_FINDING_IDS[:-1])
        self._red(
            any("semantic-tdd-conductor-skill" in v and "'findings'" in v
                for v in closed_policy_rows_check(drifted)),
            "MUT-SKILL-FINDINGS-ROSTER-DRIFT survived: a drifted findings roster must redden",
        )
        # MUT-META-LAW-SOURCE-REWRITTEN: repointing the law source dies.
        repointed = copy.deepcopy(self.policy)
        repointed["meta"]["law_source"] = "scratchpad/active/process/forged-law.md"
        self._red(
            any("meta must equal the five conserved terminal values" in v
                for v in closed_policy_rows_check(repointed)),
            "MUT-META-LAW-SOURCE-REWRITTEN survived: a repointed law_source must redden",
        )
        # MUT-CONFORMANCE-BUDGET-WIDENED: a second conformance check dies.
        widened = copy.deepcopy(self.policy)
        widened["successor"]["max_conformance_checks"] = 2
        self._red(
            any("successor scalars must equal the conserved terminal values" in v
                for v in closed_policy_rows_check(widened)),
            "MUT-CONFORMANCE-BUDGET-WIDENED survived: widening the conformance budget must redden",
        )
        # A smuggled review-family key dies (row closure, both directions).
        smuggled = copy.deepcopy(self.policy)
        smuggled["review_families"][1]["review_amnesty"] = True
        self._red(
            any("build-lane-contract-system: unknown review-family keys ['review_amnesty']" in v
                for v in closed_policy_rows_check(smuggled)),
            "a smuggled review-family key must redden",
        )
        # The law must be a governed executable artifact agreeing on every vector.
        module = self._demand_validator(
            "the nested-row/terminal-value closure law", ("closed_policy_rows_check",)
        )
        for vector in (self.policy, waived, approved, drifted, repointed, widened, smuggled):
            self._red(
                module.closed_policy_rows_check(copy.deepcopy(vector))
                == closed_policy_rows_check(copy.deepcopy(vector)),
                "landed closed_policy_rows_check diverges from the reference",
            )

    # --- PDC-FINAL-ADV-003: exemption is closed to declared history paths ---------

    def test_only_declared_history_paths_may_be_exempt(self) -> None:
        malicious = (
            "Fable (the conductor) verifies, integrates, and commits everything; "
            "Fable conducts."
        )
        exempted = copy.deepcopy(self.policy)
        for row in exempted["currency"]["postreview_documents"]:
            if row.get("path") == W3C0_PATH:
                row["historical_exempt"] = True
        present = {
            row.get("path") for row in all_currency_rows(self.policy)
            if (ROOT / row.get("path", "")).is_file()
        }
        # Stable gap witnesses: the unlawful exemption bypasses the frozen scan,
        # pattern-coverage, history, census, and nested checks (the exact replay).
        self._red(
            postreview_scan(exempted, W3C0_PATH, malicious) == []
            and pattern_coverage_violations(exempted) == []
            and history_exemption_violations(exempted) == []
            and census_violations(self.authority, exempted, self.skill_census, present) == []
            and nested_schema_violations(exempted) == [],
            "gap witness drifted: the frozen checks now reject the exempted live "
            "document — re-derive this case against them",
        )
        # The closed law: only declared history paths may be exempt.
        self._red_empty(
            exemption_closure_check(self.policy),
            "the live exemption state must validate clean (ledger-only)",
        )
        found = exemption_closure_check(exempted)
        self._red(
            any(W3C0_PATH in v and "non-declared-history path" in v for v in found),
            f"MUT-LIVE-DOC-MARKED-HISTORICAL survived: got {found}",
        )
        # MUT-EXEMPT-PREFIX-WIDENED: widening the prefix roster dies.
        widened = copy.deepcopy(self.policy)
        widened["currency"]["historical_exempt_prefixes"] = ["docs/history/", "docs/plans/"]
        self._red(
            any("widening the exemption surface is a bypass" in v
                for v in exemption_closure_check(widened)),
            "MUT-EXEMPT-PREFIX-WIDENED survived: a widened exemption prefix must redden",
        )
        # MUT-EXEMPTION-SCAN-BYPASS: the fail-closed scan ignores the unlawful flag —
        # malicious text in the exempted live document is still flagged.
        flagged = exemption_aware_scan(exempted, W3C0_PATH, malicious)
        self._red(
            any("forbidden pattern matched" in v for v in flagged),
            f"MUT-EXEMPTION-SCAN-BYPASS survived: got {flagged}",
        )
        # Controls: the ledger stays lawfully exempt and unscanned; clean text passes.
        self._red(
            exemption_aware_scan(self.policy, LEDGER_PATH, malicious) == [],
            "declared history must stay unscanned (append-only, never rewritten)",
        )
        self._red(
            exemption_aware_scan(
                self.lawful_final, W3C0_PATH,
                "`/root` conducts; Fable authors every bounded design and executable RED.",
            ) == [],
            "false positive: lawful conductor prose must scan clean in the live document",
        )
        # The law must be a governed executable artifact agreeing on every vector.
        module = self._demand_validator(
            "the declared-history-only exemption law",
            ("exemption_closure_check", "exemption_aware_scan"),
        )
        for vector in (self.policy, exempted, widened):
            self._red(
                module.exemption_closure_check(copy.deepcopy(vector))
                == exemption_closure_check(copy.deepcopy(vector)),
                "landed exemption_closure_check diverges from the reference",
            )
        for policy_vector, path, text in (
            (exempted, W3C0_PATH, malicious),
            (self.policy, LEDGER_PATH, malicious),
            (self.policy, "docs/plans/handoff/ghost.md", malicious),
            (self.lawful_final, W3C0_PATH, "`/root` conducts; clean."),
        ):
            self._red(
                module.exemption_aware_scan(copy.deepcopy(policy_vector), path, text)
                == exemption_aware_scan(copy.deepcopy(policy_vector), path, text),
                f"landed exemption_aware_scan diverges from the reference on {path}",
            )

    # --- PDC-FINAL-ADV-004: pointer + lifecycle ownership cannot coexist ----------

    def test_agents_pointer_cannot_coexist_with_skill_lifecycle_ownership(self) -> None:
        pointer_sentence = (
            "Slice lifecycle, role seats, review gates, and commit authority "
            "are governed by `AGENTS.md`."
        )
        coexistence_attack = OWNERSHIP_ATTACKS[0] + "\n" + pointer_sentence + "\n"
        skill_md = f"{SKILL_DIR}/SKILL.md"
        # Stable gap witness: under the exact SEALED reviewed pattern sets (an
        # in-memory snapshot, so the witness survives GREEN's row extensions), the
        # frozen scan accepts the pointer+ownership text.
        sealed_snapshot = copy.deepcopy(self.policy)
        for row in all_currency_rows(sealed_snapshot):
            if row.get("path") == skill_md:
                row["forbidden_patterns"] = (
                    list(STALE_CONDUCTOR_PATTERNS)
                    + [PAREN_CONDUCTOR_PATTERN]
                    + list(SKILL_LIFECYCLE_PATTERNS)
                    + [PERSLICE_SOP_PATTERN]
                )
        self._red(
            postreview_scan(sealed_snapshot, skill_md, coexistence_attack) == [],
            "gap witness drifted: the frozen scan under the sealed pattern sets now "
            "rejects the pointer+ownership coexistence — re-derive this case against it",
        )
        # Each ownership claim dies on the demanded set; the sealed lifecycle set
        # provably misses every one of them (gap witness).
        sealed_lifecycle = list(SKILL_LIFECYCLE_PATTERNS) + [PERSLICE_SOP_PATTERN]
        for attack in OWNERSHIP_ATTACKS:
            self._red(
                any(re.search(pattern, attack) for pattern in SKILL_OWNERSHIP_PATTERNS),
                f"MUT-SKILL-LIFECYCLE-CLAIM-MISSED survived: must catch {attack!r}",
            )
            self._red(
                all(re.search(pattern, attack) is None for pattern in sealed_lifecycle),
                f"gap witness drifted: the sealed lifecycle set unexpectedly catches "
                f"{attack!r} — re-derive the ownership pattern law",
            )
        # MUT-DOMAIN-METHOD-FLAGGED: domain-method prose and the AGENTS pointer
        # survive the ownership set.
        for control in DOMAIN_METHOD_CONTROLS + (pointer_sentence, AGENTS_POINTER):
            self._red(
                all(re.search(pattern, control) is None for pattern in SKILL_OWNERSHIP_PATTERNS),
                f"MUT-DOMAIN-METHOD-FLAGGED: lawful skill prose must survive: {control!r}",
            )
        # Under the demanded law the coexistence attack dies WITH the pointer present:
        # the forbidden claim reddens while no required proposition is missing.
        found = exemption_aware_scan(self.lawful_final, skill_md, coexistence_attack)
        self._red(
            any("forbidden pattern matched" in v for v in found)
            and all("required proposition absent" not in v for v in found),
            "MUT-POINTER-PLUS-OWNERSHIP-COEXISTS survived: the AGENTS pointer must "
            f"never launder a lifecycle-ownership claim, got {found}",
        )
        # The live skill tree already scans clean of ownership claims (control), and
        # must stay clean under the demanded union.
        live_violations = []
        for path in self.skill_census:
            text = (ROOT / path).read_text(encoding="utf-8")
            for pattern in sealed_lifecycle + list(SKILL_OWNERSHIP_PATTERNS):
                if re.search(pattern, text):
                    live_violations.append(f"{path}: lifecycle ownership matched: {pattern}")
        self._red_empty(
            live_violations,
            "a live skill file claims lifecycle ownership",
        )
        # MUT-OWNERSHIP-PATTERN-ROW-DROPPED: a skill row without the ownership set
        # reddens against the demanded coverage law.
        dropped = copy.deepcopy(self.lawful_final)
        for row in all_currency_rows(dropped):
            if row.get("path") == skill_md:
                row["forbidden_patterns"] = [
                    pattern for pattern in row["forbidden_patterns"]
                    if pattern not in SKILL_OWNERSHIP_PATTERNS
                ]
        self._red(
            any(
                skill_md in violation and "missing lifecycle-ownership pattern" in violation
                for violation in duty_pattern_coverage_violations(dropped)
            ),
            "MUT-OWNERSHIP-PATTERN-ROW-DROPPED survived: a skill row without the "
            "ownership set must redden",
        )
        self._red_empty(
            [
                violation
                for violation in duty_pattern_coverage_violations(self.policy)
                if "missing lifecycle-ownership pattern" in violation
            ],
            "skill rows do not forbid lifecycle-ownership claims — the AGENTS pointer "
            "can coexist with a skill claiming dispatch/approval/integration/commit",
        )


if __name__ == "__main__":
    unittest.main()

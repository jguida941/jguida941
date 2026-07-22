"""Governed deterministic process-governance validator (pure; no I/O).

Landed by the process-doc-currentness final-adversarial GREEN slice as the executable
governed artifact demanded by design section 4 of
`scratchpad/active/process/process-doc-currentness-final-adversarial-design-r1.md`.
It compiles the terminal ADVERSARIAL findings PDC-FINAL-ADV-002 (canonical session
identity + the closed successor log) and PDC-FINAL-ADV-003 (exact nested-row/terminal-
value closure + the declared-history-only exemption) into deterministic law.

The function bodies below are transcribed EXACTLY from the marked reference section of
the governing RED `tests/contracts/test_process_docs_currency_final_adversarial.py`
(sha256 `612d3555e917b57b4a9a4efbc968627bf5dd2ad140cbb23f4068e5c421c67d6e`), which binds
this artifact by differential OUTPUT EQUALITY over its full vector battery. The anchors
that reference section imports are materialized here as literal constants with values
byte-identical to the frozen predecessor modules, so this module is self-contained: it
imports exactly `hashlib`, `re`, and `unicodedata` and imports no test module. It
performs no file, network, clock, or random access (`hashlib` is used only to hash an
in-memory string for the R3 contextual history law below).

The `--- R2 successor law ---` section at the bottom compiles the seven terminal R2
findings (`PDC-CODE-R2-ROLE-CURRENTNESS-001`, `PDC-CODE-R2-POSTREVIEW-FINITENESS-001`,
`PDC-CODE-R2-VALIDATOR-COMPOSITION-001`, `PDC-R2-ADV-001..004`) governed by
`tests/contracts/test_process_docs_currency_final_r2.py` (sha256
`7dde1748279853eeba404c8b899208b3fd953b70cd74c1f35094230588e9a49f`) into the seven
demanded callables. The predecessor laws above are NOT relaxed: the only pre-existing
callable the successor touches is `closed_successor_log_check`, which gains a
shape/payload pre-pass that is silent on every predecessor vector (see the amendment
note there), so its differential output equality with the frozen predecessor reference
is conserved exactly.

The `--- R3 successor law ---` section at the bottom compiles the eleven terminal R2
CODE/ADVERSARIAL findings (`PDC-R2-CODE-FINAL-001..004`, `PDC-R2-FINAL-ADV-001..007`)
governed by `tests/contracts/test_process_docs_currency_final_r3.py` (sha256
`b27f7f2682ccd7e2d8b2191c10672fcc2ab2b0af9f3e231ace9e38577b7b93c3`): finiteness over
re-round/re-review grammar, total (never-raising) value laws, an IMMUTABLE identity
schema, confusable/duty-synonym authority coverage, an exact path/section/hash
contextual history law, control-character rejection in canonical paths, and one atomic
composer over every predecessor and successor law. As above, no predecessor law is
relaxed: each amendment is silent on every vector the frozen predecessor batteries
replay, so their differential output equalities are conserved exactly.
"""

import hashlib
import re
import unicodedata

# --- materialized anchors (values byte-identical to the frozen predecessor REDs) -----

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

R2_REVIEW = (
    "scratchpad/active/process/"
    "build-lane-contract-system-codex-design-admission-review-r2.md"
)
OPERATOR_LAW = (
    "scratchpad/active/process/OPERATOR-POST-REVIEW-EXECUTION-LAW-2026-07-22.md"
)

SKILL_FINDING_IDS = (
    "SKILL-R1-001",
    "SKILL-R1-002",
    "SKILL-R1-003",
    "SKILL-R1-004",
    "SKILL-R1-005",
    "SKILL-R1-006",
)

HISTORICAL_RECORD_IDS = {
    OPERATOR_LAW: "90a9b7e231fecf88339afbac6ab6e5cb13825a3f48b84cbdfe69131da1b63e66",
    R2_REVIEW: "102f72c0024ea7f9f6d1dc665e805646ae63d97b05dab76732bbb35b098b5711",
    "scratchpad/active/process/semantic-tdd-conductor-skill-design-r1.md":
        "865c6479e58e9404d70d5340e33474ddd9b76286843bef0c51d19a1ec2dad5e1",
    "scratchpad/active/process/semantic-tdd-conductor-skill-red-spec-r1.json":
        "d73e32afd79bb6763fa7b38c3d4cb7d8a955b888c613df31624a8f08beacdb5a",
    "scratchpad/active/process/"
    "JGUIDA-CONSOLIDATED-RECOVERY-ANTI-STALL-UI-AUTHORITY-PLAN-2026-07-22.md":
        "11e0e19ef38801e92e2b4c5729d370a5808a0f6e873728c309795dd94b9e3ceb",
}

DEMANDED_RECORD_SCHEMA = {
    "required_keys": [
        "red_author_seat",
        "red_author_session",
        "reviewer_seat",
        "reviewer_session",
        "green_builder_seat",
        "green_builder_session",
    ],
    "allow_unknown_keys": False,
}

DEMANDED_DISPATCH_SCHEMA = {
    "required_keys": ["builder_seat", "builder_session", "red_author_session"],
    "allowed_keys": ["builder_seat", "builder_session", "red_author_session"],
}

# --- reference constants (transcribed from the RED's reference section) -------------

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


# --- total accessors (PDC-R2-CODE-FINAL-003) -----------------------------------------
# A governed section that is not the shape it declares is a POLICY DEFECT to report, not
# an exception to propagate. These two coercions let every closure law below read a
# hostile policy without a type check at each use site; the law then reports the
# terminal-value or closure mismatch that the malformed section actually causes.


def _mapping(value) -> dict:
    """The value as a mapping, or the empty mapping when it is not one."""
    return value if isinstance(value, dict) else {}


def _sequence(value) -> list:
    """The value as a list, or the empty list when it is not a sequence.

    Strings and bytes are deliberately NOT sequences here: a roster spelled as a bare
    string is a malformed roster, never a roster of its characters."""
    if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
        return []
    return list(value)


# --- local roster helper (documents + postreview_documents, in declared order) -------


def all_currency_rows(policy: dict) -> list[dict]:
    """The declared roster union, in declared order.

    PDC-R2-CODE-FINAL-003 amendment: TOTAL over malformed containers. A missing or
    non-mapping `currency`, and a non-sequence roster, yield an empty union instead of
    raising, so the shape laws (not an exception) report the defect. On every
    well-formed policy the frozen predecessor batteries replay this returns exactly the
    same rows as before.
    """
    currency = policy.get("currency") if isinstance(policy, dict) else None
    if not isinstance(currency, dict):
        return []
    rows: list[dict] = []
    for section in ("documents", "postreview_documents"):
        declared = currency.get(section, [])
        if isinstance(declared, (list, tuple)):
            rows.extend(declared)
    return rows


# --- the reference law, transcribed exactly from the governing RED ------------------


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
    can never make the same logical session count as distinct.

    PDC-R2-CODE-FINAL-003 amendment: the three shape guards below make the per-record
    law TOTAL, matching the chain law above. They fire only where the transcribed
    reference would have raised (a non-mapping record/roles, a non-mapping schema, a
    missing or non-sequence `required_keys`), so differential output equality with the
    frozen reference holds on every vector it compares."""
    if not isinstance(record, dict):
        return ["identity record must be a mapping"]
    if not isinstance(schema, dict):
        return ["identity record schema must be a mapping"]
    if not isinstance(schema.get("required_keys"), (list, tuple)):
        return ["identity schema required_keys must be a sequence"]
    if not isinstance(roles, dict):
        return ["policy roles must be a mapping"]
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
    the canonical session law applied (the schema is APPLIED, not merely declared).

    PDC-R2-CODE-FINAL-003 amendment: the roster pre-pass below makes the law TOTAL —
    an unhashable roster entry (`allowed_keys = [["builder_seat"]]`) becomes a
    deterministic violation instead of `TypeError: unhashable type`. It is silent on
    every well-formed schema the frozen predecessor battery replays."""
    if not isinstance(payload, dict):
        return ["dispatch payload must be a mapping"]
    if not isinstance(schema, dict):
        return ["dispatch schema must be a mapping"]
    rosters = (schema.get("required_keys"), schema.get("allowed_keys"))
    if not all(
        isinstance(roster, (list, tuple)) and all(isinstance(key, str) for key in roster)
        for roster in rosters
    ):
        return ["dispatch schema rosters must be sequences of strings"]
    if not isinstance(successor, dict):
        return ["policy.successor must be a mapping"]
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


# --- PDC-R2-ADV-003 amendment: closed event payloads + malformed-input totality ------
# Every lifecycle event kind carries an EXACT payload schema, so reset/waiver keys can
# never ride an event, and a malformed container/row/payload returns a deterministic
# violation instead of raising. GREEN_DISPATCH is deliberately absent from this table:
# its payload schema is policy DATA (`successor.dispatch_schema`) and is applied by
# `dispatch_payload_check` below, which already closes it in both directions.
#
# Predecessor conservation: this pre-pass is SILENT on every vector the frozen
# `test_process_docs_currency_final_adversarial.py` battery replays (all of them are
# 2-tuples of an ASCII kind and a mapping, and the only payload-bearing known kinds they
# use are PROSE_REVIEW `{"verdict": ...}` and GREEN_DISPATCH), so the differential output
# equality that binds `closed_successor_log_check` to its frozen reference is preserved.
EVENT_PAYLOAD_SCHEMAS = {
    "RED_ACCEPTED": (frozenset(), frozenset()),
    "CONFORMANCE_PASSED": (frozenset(), frozenset()),
    "PROSE_REVIEW": (frozenset({"verdict"}), frozenset({"verdict"})),
    "REVIEW_OF_REVIEW": (frozenset(), frozenset()),
}

EVENT_KIND_GRAMMAR = r"[A-Z][A-Z0-9_]*"


def successor_log_shape_violations(events) -> list[str]:
    """The shape/payload pre-pass: malformed containers, rows, kinds, and payloads
    become deterministic violations, and each known kind's payload is key-closed."""
    if not isinstance(events, (list, tuple)):
        return ["lifecycle events must be a sequence of (kind, payload) rows"]
    violations = []
    for index, event in enumerate(events):
        if not isinstance(event, (list, tuple)) or len(event) != 2:
            violations.append(f"event {index} must be a two-item (kind, payload) sequence")
            continue
        kind, payload = event
        if not isinstance(kind, str) or re.fullmatch(EVENT_KIND_GRAMMAR, kind) is None:
            violations.append(f"event {index} kind must use the ASCII lifecycle-event grammar")
            continue
        if not isinstance(payload, dict):
            violations.append(f"event {index}.{kind}: payload must be a mapping")
            continue
        schema = EVENT_PAYLOAD_SCHEMAS.get(kind)
        if schema is None:
            # Unknown kinds and GREEN_DISPATCH are judged by the closed lifecycle law.
            continue
        required, allowed = schema
        missing = sorted(required - set(payload))
        unknown = sorted(set(payload) - allowed)
        if missing:
            violations.append(f"event {index}.{kind}: missing payload keys {missing}")
        if unknown:
            violations.append(f"event {index}.{kind}: unknown payload keys {unknown}")
    return violations


def closed_successor_log_check(events, policy: dict) -> list[str]:
    """PDC-FINAL-ADV-002: the successor lifecycle log is CLOSED — known event kinds
    only, exactly one accepted RED, the one bounded conformance check must OCCUR
    after acceptance, GREEN_DISPATCH immediately follows it and is final, and the
    dispatch payload is validated against successor.dispatch_schema.

    PDC-R2-ADV-003 amendment: the shape/payload pre-pass runs first and returns
    early, so no malformed input can reach (and raise inside) the closed law below."""
    shape = successor_log_shape_violations(events)
    if shape:
        return shape
    if not isinstance(policy, dict) or not isinstance(policy.get("successor"), dict):
        return ["policy.successor must be a mapping"]
    successor = policy["successor"]
    if not isinstance(successor.get("dispatch_schema"), dict):
        return ["policy.successor.dispatch_schema must be a mapping"]
    schema = successor["dispatch_schema"]
    missing_policy = sorted(
        f"policy.successor.{key}"
        for key in ("max_conformance_checks", "forbidden_after_red_accepted", "green_builder")
        if key not in successor
    ) + sorted(
        f"policy.successor.dispatch_schema.{key}"
        for key in ("required_keys", "allowed_keys")
        if key not in schema
    )
    if missing_policy:
        return [f"successor law cannot run: missing policy keys {missing_policy}"]
    if not isinstance(successor["forbidden_after_red_accepted"], (list, tuple)):
        return ["policy.successor.forbidden_after_red_accepted must be a sequence"]
    if not isinstance(schema["required_keys"], (list, tuple)) or not isinstance(
        schema["allowed_keys"], (list, tuple)
    ):
        return ["policy.successor.dispatch_schema rosters must be sequences"]
    # PDC-R2-CODE-FINAL-003 amendment: the two value pre-passes below keep the closed
    # law TOTAL — a non-integer bound and an unhashable roster entry become
    # deterministic violations instead of `TypeError`. Both are silent on every vector
    # the frozen predecessor battery replays (bound `1`, rosters of plain strings).
    if not all(
        isinstance(key, str)
        for roster in (schema["required_keys"], schema["allowed_keys"])
        for key in roster
    ):
        return ["policy.successor.dispatch_schema rosters must contain strings only"]
    if not isinstance(successor["max_conformance_checks"], int) or isinstance(
        successor["max_conformance_checks"], bool
    ):
        return ["policy.successor.max_conformance_checks must be an integer"]
    forbidden = successor["forbidden_after_red_accepted"]
    if not all(isinstance(kind, str) for kind in forbidden):
        return ["policy.successor.forbidden_after_red_accepted must contain strings only"]
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
    terminal token (APPROVE) both fail closed.

    PDC-R2-CODE-FINAL-003 amendment: a non-mapping policy returns a deterministic
    violation instead of raising `AttributeError`. Every vector the frozen predecessor
    battery replays is a mapping, so its outputs are unchanged."""
    if not isinstance(policy, dict):
        return ["policy must be a mapping"]
    violations = []
    if policy.get("meta") != EXPECTED_META:
        violations.append("meta must equal the five conserved terminal values exactly")
    if policy.get("roles") != SEATS:
        violations.append("roles must equal the four ratified seats exactly")
    # PDC-R2-CODE-FINAL-003 amendment: `_mapping()`/`_sequence()` below coerce a
    # non-mapping / non-sequence nested section to its empty form, so a hostile scalar
    # in `separation`, `successor`, `transition_classes`, `review_families`, or
    # `currency` reports the terminal-value mismatch it IS instead of raising
    # `AttributeError`/`TypeError` mid-law. Every section the frozen predecessor
    # battery replays is already well-formed, so its verdicts are unchanged.
    separation = _mapping(policy.get("separation"))
    if {key: separation.get(key) for key in EXPECTED_SEPARATION_FLAGS} != EXPECTED_SEPARATION_FLAGS:
        violations.append("separation flags must stay the three conserved false values")
    if separation.get("record_schema") != DEMANDED_RECORD_SCHEMA:
        violations.append("separation.record_schema must equal the closed six-field payload exactly")
    successor = _mapping(policy.get("successor"))
    if {key: successor.get(key) for key in EXPECTED_SUCCESSOR_SCALARS} != EXPECTED_SUCCESSOR_SCALARS:
        violations.append(
            "successor scalars must equal the conserved terminal values "
            "(one bounded conformance check, GREEN_DISPATCH next, opus builder, closed forbidden list)"
        )
    if successor.get("dispatch_schema") != DEMANDED_DISPATCH_SCHEMA:
        violations.append("successor.dispatch_schema must equal the closed three-field payload exactly")
    if policy.get("lineage") != EXPECTED_LINEAGE:
        violations.append("lineage must equal the conserved terminal values exactly")
    if _mapping(policy.get("transition_classes")).get("classes") != CLASSES:
        violations.append("transition_classes must equal the closed five-class enum exactly")
    families = _sequence(policy.get("review_families"))
    if len(families) != len(EXPECTED_FAMILY_ROWS):
        violations.append("review_families must be exactly the two terminal families, in order")
    else:
        for family, expected in zip(families, EXPECTED_FAMILY_ROWS):
            family_id = expected["family_id"]
            if not isinstance(family, dict):
                violations.append(f"{family_id}: review-family row must be a mapping")
                continue
            unknown = sorted(set(family) - set(expected))
            if unknown:
                violations.append(f"{family_id}: unknown review-family keys {unknown}")
            missing = sorted(set(expected) - set(family))
            if missing:
                violations.append(f"{family_id}: missing review-family keys {missing}")
            for key in sorted(set(expected) & set(family)):
                if family[key] != expected[key]:
                    violations.append(f"{family_id}: field {key!r} must equal the conserved terminal value")
    records = _sequence(_mapping(policy.get("currency")).get("historical_records"))
    if len(records) != len(EXPECTED_HISTORICAL_ROWS):
        violations.append("currency.historical_records must be exactly the five conserved rows, in order")
    else:
        for record, expected in zip(records, EXPECTED_HISTORICAL_ROWS):
            path = expected["path"]
            if not isinstance(record, dict):
                violations.append(f"{path}: historical-record row must be a mapping")
                continue
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
    paths — marking a live document historical is a scan bypass and fails closed.

    PDC-R2-CODE-FINAL-003 amendment: a non-mapping policy or row, and a non-string
    path, become deterministic violations instead of raising. Silent on every vector
    the frozen predecessor battery replays."""
    if not isinstance(policy, dict):
        return ["policy must be a mapping"]
    violations = []
    currency = policy.get("currency")
    prefixes = currency.get("historical_exempt_prefixes") if isinstance(currency, dict) else None
    if prefixes != list(LAWFUL_EXEMPT_PREFIXES):
        violations.append(
            "historical_exempt_prefixes must equal exactly ['docs/history/'] — "
            "widening the exemption surface is a bypass"
        )
    for row in all_currency_rows(policy):
        if not isinstance(row, dict):
            violations.append("currency document rows must be mappings")
            continue
        path = row.get("path", "<missing path>")
        flag = row.get("historical_exempt")
        if flag is None or flag is False:
            continue
        if flag is not True:
            violations.append(f"{path}: historical_exempt must be a boolean, got {flag!r}")
            continue
        if not isinstance(path, str):
            violations.append(f"{path!r}: exempted document path must be a string")
            continue
        if not path.startswith(LAWFUL_EXEMPT_PREFIXES):
            violations.append(
                f"{path}: historical_exempt on a non-declared-history path — "
                "live documents may never be exempted from scanning"
            )
    return violations


def declared_currency_row(policy: dict, rel_path) -> dict | None:
    """The first declared roster row for `rel_path`, or None when undeclared."""
    rows: dict = {}
    for row in all_currency_rows(policy):
        if isinstance(row, dict):
            rows.setdefault(row.get("path", ""), row)
    if not isinstance(rel_path, str):
        return None
    return rows.get(rel_path)


def _forbidden_pattern_violations(row: dict, rel_path: str, text) -> list[str]:
    """The row's declared forbidden-pattern arm (total over malformed rows/text)."""
    declared = row.get("forbidden_patterns", [])
    if not isinstance(declared, (list, tuple)):
        return [f"{rel_path}: forbidden_patterns must be a sequence"]
    if not isinstance(text, str):
        return [f"{rel_path}: document text must be a string"]
    violations = []
    for pattern in declared:
        if not isinstance(pattern, str):
            violations.append(f"{rel_path}: forbidden pattern must be a string")
            continue
        if re.search(pattern, text):
            violations.append(f"{rel_path}: forbidden pattern matched: {pattern}")
    return violations


def _required_proposition_violations(row: dict, rel_path: str, text) -> list[str]:
    """The row's declared required-proposition arm (total over malformed rows/text)."""
    declared = row.get("required_propositions", [])
    if not isinstance(declared, (list, tuple)):
        return [f"{rel_path}: required_propositions must be a sequence"]
    if not isinstance(text, str):
        return [f"{rel_path}: document text must be a string"]
    violations = []
    for proposition in declared:
        if not isinstance(proposition, str):
            violations.append(f"{rel_path}: required proposition must be a string")
            continue
        if proposition not in text:
            violations.append(f"{rel_path}: required proposition absent: {proposition!r}")
    return violations


def exemption_aware_scan(policy: dict, rel_path: str, text: str) -> list[str]:
    """Currency scan over the sealed + postreview roster union that honors the
    history exemption ONLY for declared history paths: an unlawfully exempted live
    row is scanned anyway (fail closed), so exemption flags cannot bypass the
    pattern, proposition, or malicious-text checks.

    The body is now expressed through the three helpers above so the R3 aggregate can
    reuse the SAME roster/exemption decision; the emitted list — forbidden-pattern
    verdicts first, then required-proposition verdicts, in declared order — is
    byte-identical to the transcribed reference on every well-formed vector."""
    row = declared_currency_row(policy, rel_path)
    if row is None:
        return [f"undeclared document: {rel_path}"]
    if rel_path.startswith(LAWFUL_EXEMPT_PREFIXES):
        return []
    return _forbidden_pattern_violations(row, rel_path, text) + (
        _required_proposition_violations(row, rel_path, text)
    )


# =====================================================================================
# --- R2 successor law ----------------------------------------------------------------
# Governed by tests/contracts/test_process_docs_currency_final_r2.py. Seven findings,
# seven callables, one atomic composer. Nothing above this line is relaxed.
# =====================================================================================


# --- PDC-R2-ADV-001: normalization before any authority matching ---------------------


def normalize_governance_text(value):
    """NFKC normalization + removal of Unicode format (Cf) controls; non-strings fail
    closed as ``None``.

    Every authority law below matches against THIS form only, so fullwidth (`Ｆａｂｌｅ`)
    and zero-width (`Fa<ZWSP>ble`) spellings collapse onto the ASCII subject before any
    pattern runs. The transform is idempotent: NFKC is idempotent and the second pass
    has no Cf characters left to drop. `canonicalize_session` above is the identity-field
    specialization of this same normal form (it additionally strips and casefolds)."""
    if not isinstance(value, str):
        return None
    text = unicodedata.normalize("NFKC", value)
    return "".join(ch for ch in text if unicodedata.category(ch) != "Cf")


# --- PDC-CODE-R2-ROLE-CURRENTNESS-001 / PDC-R2-ADV-001: role + skill authority --------
# The direct-duty arm requires a lifecycle DUTY VERB next to the Fable subject, so lawful
# authorship prose ("Fable authors the bounded design", "Fable 5 is the delegated DESIGN
# + RED author") is never flagged. The passive arm catches "<duty> ... by Fable", and the
# conductor-noun arm catches the seat claim itself.

ROLE_AUTHORITY_PATTERNS = (
    r"(?i)\bfable(?:\s+5)?(?:\s*,\s*(?:the\s+)?conductor\s*,?)?\s+"
    r"(?:(?:shall|must|will|may|can|should|would)\s+|is\s+(?:to|responsible\s+for)\s+|"
    r"continues?\s+to\s+)?(?:appl(?:y|ies|ied|ying)|integrat(?:e|es|ed|ing)|"
    r"commit(?:s|ted|ting)?|verif(?:y|ies|ied|ying)|conducts?)\b",
    r"(?i)\b(?:appl(?:y|ied)|integrat(?:e|ed|ion)|commit(?:ted|ment)?|"
    r"verif(?:y|ied|ication)|conducted)"
    r"\b[^.\n]{0,80}\bby\s+fable(?:\s+5)?\b",
    r"(?i)\bfable(?:\s+5)?\s*(?:,|\(|-)?\s*(?:the\s+)?conductor\b",
)

# --- PDC-R2-FINAL-ADV-005: confusable folding + the lifecycle DUTY SYNONYMS -----------
# The R2 duty union above covers apply/integrate/commit/verify/conduct. The terminal
# ADVERSARIAL round showed the same seat claim survives in two other spellings:
#   * a Cyrillic-confusable subject (`Fаble`, U+0430) — NFKC does not fold script
#     confusables, so the ASCII patterns never see the subject at all; and
#   * the approve/review/merge/own duty family, which the R2 union never named.
# `CONFUSABLE_SKELETON` is a strict 1:1 character map, so match offsets are preserved
# and the conserved-history spans below stay valid on the folded text.

CONFUSABLE_SKELETON = str.maketrans({
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x",
    "А": "A", "Е": "E", "О": "O", "Р": "P", "С": "C", "Х": "X",
})


def confusable_skeleton(normalized: str) -> str:
    """Fold the Cyrillic lookalikes onto their Latin skeleton (offset-preserving)."""
    if not isinstance(normalized, str):
        return ""
    return normalized.translate(CONFUSABLE_SKELETON)


# Direct-duty and passive arms for the approve/review/merge/own family. Both keep the
# R2 adjacency discipline — the duty verb sits immediately after the Fable subject (or
# after one modal) — so lawful authorship prose survives untouched:
#   "Fable authors the bounded scratch design."      (no duty verb after the subject)
#   "Fable does not implement GREEN, review or approve its own artifacts, integrate,
#    commit, merge, or push"                          ("does" is not a modal here)
#   "Fable 5 is the delegated DESIGN + RED author"    (no duty verb)
ROLE_DUTY_SYNONYM_PATTERNS = (
    r"(?i)\bfable(?:\s+5)?(?:\s*,\s*(?:the\s+)?conductor\s*,?)?\s+"
    r"(?:(?:shall|must|will|may|can|should|would)\s+|is\s+(?:to|responsible\s+for)\s+|"
    r"continues?\s+to\s+)?(?:approv(?:e|es|ed|ing)|review(?:s|ed|ing)?|"
    r"merg(?:e|es|ed|ing)|own(?:s|ed|ing)?)\b",
    r"(?i)\b(?:approval|review|merge|integration|lifecycle|ownership)\b"
    r"[^.\n]{0,80}\b(?:owned|approved|reviewed|merged|controlled)\s+by\s+"
    r"fable(?:\s+5)?\b",
)

SKILL_REOWNERSHIP_PATTERNS = (
    r"(?i)\b(?:dispatch|approval|review|integration|commit|merge|lifecycle)\b"
    r"[^.\n]{0,80}\b(?:is|are)\s+(?:performed|owned|controlled|approved|handled)\s+by\s+"
    r"(?:this|the)\s+(?:skill|reference|lane)\b",
    r"(?i)\b(?:this|the)\s+(?:skill|reference|lane)\s+"
    r"(?:shall|must|will|may|can|should|is\s+responsible\s+for)\s+"
    r"(?:dispatch|approv(?:e|al)|review|integrat(?:e|ion)|commit|merge|own)\w*\b",
    r"(?i)\b(?:dispatch|approval|review|integration|commit|merge|lifecycle)\b"
    r"[^.\n]{0,80}\bbelongs\s+to\s+(?:this|the)\s+(?:skill|reference|lane)\b",
)

# --- the closed conserved-history register -------------------------------------------
# The role law governs PRESCRIPTIONS IN FORCE; it does not rewrite the append-only record
# of superseded routings. That distinction is not a convenience here — it is already
# FROZEN LAW: `tests/contracts/test_process_docs_currency_final_adversarial.py` (sha256
# `612d3555e917b57b4a9a4efbc968627bf5dd2ad140cbb23f4068e5c421c67d6e`) both
#   (a) lists "(Fable verifies, integrates, and commits; Codex reviews only)" in
#       LAWFUL_AUTHORSHIP_CONTROLS, which lawful prose MUST survive the duty union, and
#   (b) asserts via MUT-NARRATIVE-HISTORY-REWRITTEN that the whole clause below stays
#       BYTE-PRESENT in the live `docs/plans/handoff/w3c-0-design-closure.md`.
# So the sentence cannot be deleted, and it must not be read as an active prescription.
#
# The register is deliberately the weakest possible carve-out:
#   * CLOSED — a fixed roster of complete historical clauses; nothing is inferred from
#     tense, dates, or parentheses, so no author can talk their way into an exemption;
#   * SPAN-SCOPED — only a match lying ENTIRELY inside an occurrence of a declared clause
#     is narration; text appended before or after it is judged normally;
#   * WHITESPACE-TOLERANT, byte-exact otherwise — the clause is matched with runs of
#     whitespace collapsed (it is line-wrapped in the governed document), and every other
#     byte, including the routing framing that makes it a historical record, must match.
# Adding an entry is a governed code change to this module, reviewable on its own.
#
# PDC-R2-CODE-FINAL-001 amendment: the register gained its SECOND (and only other)
# entry, the rev-16 cadence clause that `docs/plans/handoff/w3c-0-design-closure.md`
# now quotes as a superseded record. The same frozen adversarial module pins that exact
# clause byte-present (W3C0_CORRECTED_LINES), so it cannot be deleted either; §13.3's
# ACTIVE cadence no longer prescribes a re-review round, and the retained bytes are a
# conserved record of the routing the 2026-07-22 operator law replaced.
CONSERVED_HISTORICAL_NARRATIONS = (
    "the operator restored the Fable-conducts routing in-session "
    "(Fable verifies, integrates, and commits; Codex reviews only)",
    "packet-bound patch is rebuilt/reverified/re-reviewed at xhigh "
    "→ `/root` commits the exact approved",
)

CONSERVED_HISTORICAL_PATTERNS = tuple(
    re.compile(r"\s+".join(re.escape(word) for word in narration.split()))
    for narration in CONSERVED_HISTORICAL_NARRATIONS
)


def conserved_history_spans(normalized: str) -> list:
    """Half-open [start, end) spans of the declared historical clauses in the text.

    A non-string carries no conserved span (its caller's normalizer has already failed
    it closed), so the register is TOTAL and never raises on hostile input."""
    if not isinstance(normalized, str):
        return []
    return [
        (match.start(), match.end())
        for pattern in CONSERVED_HISTORICAL_PATTERNS
        for match in pattern.finditer(normalized)
    ]


def _prescriptive_match(pattern: str, normalized: str, conserved: list) -> bool:
    """True iff `pattern` matches at least once OUTSIDE every conserved history span."""
    for match in re.finditer(pattern, normalized):
        if not any(start <= match.start() and match.end() <= end for start, end in conserved):
            return True
    return False


def _authority_violations(skeleton: str, skill: bool, conserved: list) -> list[str]:
    """The whole duty union over an already-normalized, confusable-folded text.

    `conserved` is the span roster the caller decided on: the live-document law passes
    the conserved-history spans; the strict/contextual law below passes none."""
    violations = [
        f"forbidden Fable conductor/build duty: {pattern}"
        for pattern in ROLE_AUTHORITY_PATTERNS + ROLE_DUTY_SYNONYM_PATTERNS
        if _prescriptive_match(pattern, skeleton, conserved)
    ]
    if skill:
        violations.extend(
            f"skill reclaims lifecycle authority: {pattern}"
            for pattern in SKILL_REOWNERSHIP_PATTERNS
            if _prescriptive_match(pattern, skeleton, conserved)
        )
    return violations


def role_authority_text_check(text, skill=False) -> list[str]:
    """PDC-CODE-R2-ROLE-CURRENTNESS-001 + PDC-R2-ADV-001 + PDC-R2-FINAL-ADV-005: no live
    governed document may assign Fable the conductor's apply/integrate/commit/verify/
    conduct duties or the approve/review/merge/own duties — in ASCII, fullwidth,
    zero-width, or Cyrillic-confusable spelling — and a skill document may never reclaim
    the lifecycle it is governed by."""
    normalized = normalize_governance_text(text)
    if normalized is None:
        return ["authority text must be a string"]
    skeleton = confusable_skeleton(normalized)
    return _authority_violations(skeleton, skill, conserved_history_spans(skeleton))


def strict_role_authority_text_check(text, skill=False) -> list[str]:
    """The same duty union with NO conserved-narration carve-out.

    PDC-R2-FINAL-ADV-006: conserved bytes are exempt only in their authorized CONTEXT
    (see `contextual_role_authority_text_check`), never because of what they say. This
    is the law that judges a relocated, re-sectioned, or edited copy of them."""
    normalized = normalize_governance_text(text)
    if normalized is None:
        return ["authority text must be a string"]
    return _authority_violations(confusable_skeleton(normalized), skill, [])


# --- PDC-R2-CODE-FINAL-004 + PDC-R2-FINAL-ADV-006: the contextual history exemption ---
# The portable text carve-out above is a property of BYTES; this law is a property of a
# PLACE. Exactly one section of one document is exempt, identified by the triple
# (path, section id, section sha256). Copy those bytes anywhere else, file them under a
# different section id, or edit one character of them, and they are active law again.

AUTHORIZED_HISTORY_PATH = "docs/plans/handoff/w3c-0-design-closure.md"
AUTHORIZED_HISTORY_SECTION = "rev-16-routing-narrative"
AUTHORIZED_HISTORY_SECTION_SHA256 = (
    "89ee8beb4127f157305eb1fc54af40906c3056ce2ad4f59dddeb286257e4b9a4"
)


def contextual_role_authority_text_check(path, section, text, skill=False) -> list[str]:
    """The authority law bound to an exact path/section/hash context.

    Returns no violation ONLY for the one authorized conserved-history tuple; every
    other context — including the identical bytes under another path or section id, and
    the authorized context holding drifted bytes — is judged by the strict law."""
    if (
        path == AUTHORIZED_HISTORY_PATH
        and section == AUTHORIZED_HISTORY_SECTION
        and isinstance(text, str)
        and hashlib.sha256(text.encode("utf-8")).hexdigest()
        == AUTHORIZED_HISTORY_SECTION_SHA256
    ):
        return []
    return strict_role_authority_text_check(text, skill)


# --- PDC-CODE-R2-POSTREVIEW-FINITENESS-001: review finiteness -------------------------
# Live process law may NARRATE how many rounds a family used; it may not PRESCRIBE
# another one. Finite-law controls ("No review-of-review is authorized", "one bounded
# RED-conformance check runs, then Opus builds") carry no re-round grammar and survive.

REVIEW_LOOP_PATTERNS = (
    r"(?i)\b(?:codex|reviewer|review\s+authority)\b[^.\n]{0,100}\breviews?\b"
    r"[^.\n]{0,100}\bre[- ]?rounds?\b",
    r"(?i)\bre[- ]?rounds?\b[^.\n]{0,100}\b(?:design\s+)?review\b",
    r"(?i)\b(?:must|shall|should|will|may)\s+(?:repeat|rerun|re-run|request|launch|"
    r"dispatch|perform)\b[^.\n]{0,100}\b(?:another|fresh|new|independent|subsequent)?"
    r"\s*(?:design\s+)?review\b",
    r"(?i)\bif\s+[^.\n]{0,60}\brevise\b[^.\n]{0,100}\b(?:review\s+again|another\s+"
    r"review|next\s+review|new\s+round)\b",
    # PDC-R2-CODE-FINAL-001 + PDC-R2-FINAL-ADV-001: the R2 union only caught a re-round
    # that names a "review" or a modal that launches one. The terminal round showed the
    # EFFORT-BUDGET spelling escapes it entirely — "re-rounds xhigh", "re-reviewed at
    # xhigh", and the "rebuilt/reverified/re-reviewed" compound each prescribe another
    # round while never using the launching grammar above.
    r"(?i)\bre[- ]?rounds?\b[^.\n]{0,120}\b(?:xhigh|max|ultra)\b",
    r"(?i)\bre[- ]?review(?:ed|s|ing)?\b[^.\n]{0,80}\b(?:xhigh|max|ultra)\b",
    r"(?i)\brebuilt\s*/\s*reverified\s*/\s*re[- ]?reviewed\b",
)


def review_finiteness_text_check(text) -> list[str]:
    """PDC-CODE-R2-POSTREVIEW-FINITENESS-001 + PDC-R2-CODE-FINAL-001: live process law
    contains no prescription to re-round, re-review, repeat, or launch another prose/
    design review — including the effort-budget spellings ("re-rounds xhigh")."""
    normalized = normalize_governance_text(text)
    if normalized is None:
        return ["review text must be a string"]
    conserved = conserved_history_spans(normalized)
    return [
        f"repeated prose-review prescription: {pattern}"
        for pattern in REVIEW_LOOP_PATTERNS
        if _prescriptive_match(pattern, normalized, conserved)
    ]


# --- PDC-R2-ADV-002: cross-record identity binding + ASCII identifier grammar ---------
# The R2 slice's RED author seat is `codex-max` under the routing the operator ratified
# in `scratchpad/active/process/finding-to-evidence-transition-process-currentness-r2.json`
# (`routing.red_author`). That is the SEAT THAT AUTHORED THIS SLICE'S RED; the policy's
# `roles.design_red_author` remains the design-lineage seat and is unchanged.
R2_RED_AUTHOR_SEAT = "codex-max"

SEAT_IDENTIFIER_GRAMMAR = r"(?:/[a-z0-9][a-z0-9._/-]*|[a-z0-9][a-z0-9._:-]*)"
SESSION_IDENTIFIER_GRAMMAR = r"[a-z0-9][a-z0-9._:-]*"
IDENTIFIER_MAX_BYTES = 128


def _identifier_violations(value, label: str, seat: bool = False) -> list[str]:
    """Canonical ASCII-safe identifier grammar. A Unicode confusable (Cyrillic `о`) is
    its own canonical form, so the ASCII gate — not the canonicality gate — kills it."""
    if not isinstance(value, str) or not value:
        return [f"{label}: identifier must be a non-empty string"]
    if value != canonicalize_session(value):
        return [f"{label}: identifier must already be canonical ASCII"]
    grammar = SEAT_IDENTIFIER_GRAMMAR if seat else SESSION_IDENTIFIER_GRAMMAR
    if not value.isascii() or re.fullmatch(grammar, value) is None:
        return [f"{label}: identifier violates the ASCII-safe grammar"]
    if len(value) > IDENTIFIER_MAX_BYTES:
        return [f"{label}: identifier exceeds {IDENTIFIER_MAX_BYTES} bytes"]
    return []


def closed_identity_chain_check(records, schema, roles) -> list[str]:
    """PDC-R2-ADV-002 + PDC-R2-FINAL-ADV-003: the closed six-field identity payload,
    held IMMUTABLE across every record in the chain — exact seats, pairwise-distinct
    sessions, canonical ASCII-safe identifiers, and no unknown field.

    PDC-R2-FINAL-ADV-003 amendment: the authority schema is the MODULE CONSTANT
    `DEMANDED_RECORD_SCHEMA`, not the caller's argument. The argument is still accepted
    (callers pass policy data) but it is now VALIDATED against the constant and never
    obeyed: mutable policy can neither drop a required identity field nor flip
    `allow_unknown_keys` to admit an extra one. The live policy's `record_schema`
    equals the constant, so every vector the frozen R2 battery replays is unchanged."""
    violations: list[str] = []
    if schema != DEMANDED_RECORD_SCHEMA:
        violations.append(
            "identity schema must equal the immutable six-field authority schema"
        )
    schema = DEMANDED_RECORD_SCHEMA
    required = list(schema["required_keys"])
    if not isinstance(records, (list, tuple)) or not records:
        return violations + ["identity records must be a non-empty sequence"]
    seats = roles if isinstance(roles, dict) else {}
    binding = None
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            violations.append(f"identity record {index} must be a mapping")
            continue
        missing = sorted(set(required) - set(record))
        unknown = sorted(set(record) - set(required))
        if missing:
            violations.append(f"identity record {index}: missing keys {missing}")
        if schema.get("allow_unknown_keys") is False and unknown:
            violations.append(f"identity record {index}: unknown keys {unknown}")
        if missing or unknown:
            continue
        for key in required:
            violations.extend(_identifier_violations(
                record[key], f"identity record {index}.{key}", seat=key.endswith("_seat")
            ))
        if any(not isinstance(record[key], str) for key in required):
            continue
        if record.get("red_author_seat") != R2_RED_AUTHOR_SEAT:
            violations.append(f"identity record {index}: wrong RED-author seat")
        if record.get("reviewer_seat") != seats.get("reviewer"):
            violations.append(f"identity record {index}: wrong reviewer seat")
        if record.get("green_builder_seat") != seats.get("green_builder"):
            violations.append(f"identity record {index}: wrong GREEN-builder seat")
        sessions = [
            record.get("red_author_session"),
            record.get("reviewer_session"),
            record.get("green_builder_session"),
        ]
        if len({canonicalize_session(session) for session in sessions}) != 3:
            violations.append(f"identity record {index}: sessions must be pairwise distinct")
        current = tuple(record[key] for key in required)
        if binding is None:
            binding = current
        elif current != binding:
            violations.append(
                f"identity record {index}: immutable identity binding changed across records"
            )
    return violations


# --- PDC-R2-ADV-004: policy closure in both directions -------------------------------
# Required == allowed for every map and row, so a smuggled key and a deleted key both
# fail closed. The schema-key rosters are derived from the terminal payloads already
# pinned above, so the two closures can never drift apart.

TOP_LEVEL_KEYS = frozenset({
    "meta", "roles", "separation", "successor", "lineage", "review_families",
    "transition_classes", "transitions", "currency",
})
NESTED_KEYS = {
    "meta": frozenset(EXPECTED_META),
    "roles": frozenset(SEATS),
    "separation": frozenset(EXPECTED_SEPARATION_FLAGS) | {"record_schema"},
    "successor": frozenset(EXPECTED_SUCCESSOR_SCALARS) | {"dispatch_schema"},
    "lineage": frozenset(EXPECTED_LINEAGE),
    "transition_classes": frozenset({"classes"}),
    "currency": frozenset({
        "historical_exempt_prefixes", "documents", "postreview_documents",
        "historical_records",
    }),
}
RECORD_SCHEMA_KEYS = frozenset(DEMANDED_RECORD_SCHEMA)
DISPATCH_SCHEMA_KEYS = frozenset(DEMANDED_DISPATCH_SCHEMA)
TRANSITION_KEYS = frozenset({
    "finding_id", "transition_class", "status", "dependency", "source_review",
    "owner_seat", "evidence",
})
LIVE_ROW_KEYS = frozenset({"path", "role", "forbidden_patterns", "required_propositions"})
SEALED_ROW_EXTRA_KEYS = frozenset({"adoption_sha256"})
HISTORY_DOC_KEYS = LIVE_ROW_KEYS | {
    "historical_exempt", "immutable_prefix_sha256", "immutable_prefix_bytes",
}
HISTORICAL_RECORD_KEYS = frozenset(HISTORICAL_ROW_KEYS)
SKILL_FAMILY_ID = "semantic-tdd-conductor-skill"
FAMILY_BASE_KEYS = frozenset({
    "family_id", "prose_reviews_used", "terminal_verdict_token",
    "another_prose_review_authorized",
})
FAMILY_SKILL_EXTRA_KEYS = frozenset({"findings", "terminal_review_doc"})


def _identifier_kind_violations(value, label: str) -> list[str]:
    """PDC-R2-CODE-FINAL-003: a governed IDENTITY value is a string.

    Every roster below deduplicates its identifiers, and `set()` over an unhashable
    value (`family_id = ["semantic-tdd-conductor-skill"]`, `finding_id = {...}`,
    `path = ["AGENTS.md"]`) raised `TypeError` from inside the closure law. The kind
    law runs first and turns each of those into a deterministic violation; only
    string identifiers reach the duplicate census."""
    if not isinstance(value, str):
        return [f"{label} must be a string, got {type(value).__name__}"]
    return []


def _duplicate_violations(values, label: str) -> list[str]:
    """Duplicate census over the string identifiers only (total by construction)."""
    strings = [value for value in values if isinstance(value, str)]
    if len(strings) != len(set(strings)):
        return [label]
    return []


def _closed_keys(mapping, required, allowed, label: str) -> list[str]:
    if not isinstance(mapping, dict):
        return [f"{label} must be a mapping"]
    violations = []
    missing = sorted(set(required) - set(mapping))
    unknown = sorted(set(mapping) - set(allowed))
    if missing:
        violations.append(f"{label}: missing keys {missing}")
    if unknown:
        violations.append(f"{label}: unknown keys {unknown}")
    return violations


def _path_violations(path, label: str) -> list[str]:
    """Canonical relative POSIX paths only. Implemented on raw string segments so this
    module keeps its narrow-import purity; the verdicts match a PurePosixPath round-trip:
    an empty, `.`, or `..` segment and a `//` run are all normalization escapes.

    PDC-R2-FINAL-ADV-007: the Unicode Cc gate runs FIRST and covers the whole class —
    NUL..US, DEL, and the C1 block. The ASCII gate below only reached the C1 half, so
    every ASCII control (a NUL truncating a C consumer, a newline forging a second
    roster line, a DEL hiding a segment in a terminal) rode through the canonical
    path fields untouched."""
    if not isinstance(path, str) or not path:
        return [f"{label}: path must be a non-empty string"]
    if any(unicodedata.category(character) == "Cc" for character in path):
        return [f"{label}: path contains a control character"]
    if not path.isascii() or "\\" in path or path.startswith("/"):
        return [f"{label}: path must be relative canonical ASCII POSIX"]
    if any(part in ("", ".", "..") for part in path.split("/")):
        return [f"{label}: path contains a normalization escape"]
    return []


def closed_process_policy_check(policy) -> list[str]:
    """PDC-R2-ADV-004: the whole policy is CLOSED — top-level, nested, family, document,
    history, and transition rows; identifiers unique; exemption paths canonical."""
    if not isinstance(policy, dict):
        return ["policy must be a mapping"]
    violations = _closed_keys(policy, TOP_LEVEL_KEYS, TOP_LEVEL_KEYS, "policy")
    for name, allowed in NESTED_KEYS.items():
        if name in policy:
            violations.extend(_closed_keys(policy[name], allowed, allowed, f"policy.{name}"))
    separation = policy.get("separation")
    if isinstance(separation, dict) and "record_schema" in separation:
        violations.extend(_closed_keys(
            separation["record_schema"], RECORD_SCHEMA_KEYS, RECORD_SCHEMA_KEYS,
            "policy.separation.record_schema",
        ))
    successor = policy.get("successor")
    if isinstance(successor, dict) and "dispatch_schema" in successor:
        violations.extend(_closed_keys(
            successor["dispatch_schema"], DISPATCH_SCHEMA_KEYS, DISPATCH_SCHEMA_KEYS,
            "policy.successor.dispatch_schema",
        ))

    families = policy.get("review_families", [])
    if not isinstance(families, list):
        violations.append("policy.review_families must be a list")
    else:
        family_ids = []
        for index, row in enumerate(families):
            allowed = FAMILY_BASE_KEYS | (
                FAMILY_SKILL_EXTRA_KEYS
                if isinstance(row, dict) and row.get("family_id") == SKILL_FAMILY_ID
                else frozenset()
            )
            violations.extend(_closed_keys(row, allowed, allowed, f"review_families[{index}]"))
            if isinstance(row, dict):
                violations.extend(_identifier_kind_violations(
                    row.get("family_id"), f"review_families[{index}].family_id"
                ))
                family_ids.append(row.get("family_id"))
        violations.extend(_duplicate_violations(
            family_ids, "review_families contain duplicate family_id values"
        ))

    transitions = policy.get("transitions", [])
    if not isinstance(transitions, list):
        violations.append("policy.transitions must be a list")
    else:
        finding_ids = []
        for index, row in enumerate(transitions):
            violations.extend(_closed_keys(
                row, TRANSITION_KEYS, TRANSITION_KEYS, f"transitions[{index}]"
            ))
            if isinstance(row, dict):
                violations.extend(_identifier_kind_violations(
                    row.get("finding_id"), f"transitions[{index}].finding_id"
                ))
                finding_ids.append(row.get("finding_id"))
        violations.extend(_duplicate_violations(
            finding_ids, "transitions contain duplicate finding_id values"
        ))

    currency = policy.get("currency")
    if isinstance(currency, dict):
        violations.extend(_closed_currency_check(currency))
    return violations


def _closed_currency_check(currency: dict) -> list[str]:
    violations: list[str] = []
    all_paths = []
    for section in ("documents", "postreview_documents"):
        rows = currency.get(section, [])
        if not isinstance(rows, list):
            violations.append(f"currency.{section} must be a list")
            continue
        for index, row in enumerate(rows):
            label = f"currency.{section}[{index}]"
            if not isinstance(row, dict):
                violations.append(f"{label} must be a mapping")
                continue
            if row.get("historical_exempt") is True:
                required = allowed = HISTORY_DOC_KEYS
            else:
                required = LIVE_ROW_KEYS
                allowed = LIVE_ROW_KEYS | (
                    SEALED_ROW_EXTRA_KEYS if section == "documents" else frozenset()
                )
            violations.extend(_closed_keys(row, required, allowed, label))
            violations.extend(_path_violations(row.get("path"), f"{label}.path"))
            all_paths.append(row.get("path"))
    violations.extend(_duplicate_violations(
        all_paths, "currency document rosters contain duplicate path values"
    ))

    records = currency.get("historical_records", [])
    if not isinstance(records, list):
        violations.append("currency.historical_records must be a list")
    else:
        record_paths = []
        for index, row in enumerate(records):
            label = f"currency.historical_records[{index}]"
            violations.extend(_closed_keys(
                row, HISTORICAL_RECORD_KEYS, HISTORICAL_RECORD_KEYS, label
            ))
            if isinstance(row, dict):
                violations.extend(_path_violations(row.get("path"), f"{label}.path"))
                record_paths.append(row.get("path"))
        violations.extend(_duplicate_violations(
            record_paths, "historical_records contain duplicate path values"
        ))

    prefixes = currency.get("historical_exempt_prefixes", [])
    if not isinstance(prefixes, list):
        violations.append("historical_exempt_prefixes must be a list")
    else:
        for index, prefix in enumerate(prefixes):
            label = f"historical_exempt_prefixes[{index}]"
            candidate = prefix[:-1] if isinstance(prefix, str) and prefix.endswith("/") else prefix
            violations.extend(_path_violations(candidate, label))
            if not isinstance(prefix, str) or not prefix.endswith("/"):
                violations.append(f"{label} must end in '/'")
    return violations


# =====================================================================================
# --- R3 successor law ----------------------------------------------------------------
# Governed by tests/contracts/test_process_docs_currency_final_r3.py. The value-kind
# law, the immutable seat binding, the aggregate document scan, and the one atomic
# composer. Nothing above this line is relaxed.
# =====================================================================================


# --- PDC-R2-CODE-FINAL-003 + PDC-R2-FINAL-ADV-004: the total value-kind law -----------
# Totality is not "wrap it in try/except": each governed value carries a declared KIND,
# and a value of the wrong kind is reported as that — a deterministic, category-bearing
# violation naming the field — instead of surfacing as a `TypeError` from whichever
# closure law happened to touch it first.


def policy_value_shape_check(policy) -> list[str]:
    """Every governed scalar, roster, identifier, and path has its declared kind."""
    if not isinstance(policy, dict):
        return ["policy must be a mapping"]
    violations: list[str] = []

    successor = policy.get("successor")
    if not isinstance(successor, dict):
        violations.append("policy.successor must be a mapping")
    else:
        bound = successor.get("max_conformance_checks")
        if not isinstance(bound, int) or isinstance(bound, bool):
            violations.append(
                "policy.successor.max_conformance_checks must be an integer"
            )
        dispatch = successor.get("dispatch_schema")
        if not isinstance(dispatch, dict):
            violations.append("policy.successor.dispatch_schema must be a mapping")
        else:
            for key in ("required_keys", "allowed_keys"):
                roster = dispatch.get(key)
                if not isinstance(roster, (list, tuple)) or not all(
                    isinstance(item, str) for item in roster
                ):
                    violations.append(
                        f"policy.successor.dispatch_schema.{key} must be a roster of strings"
                    )

    for label, rows, key in (
        ("review_families", policy.get("review_families"), "family_id"),
        ("transitions", policy.get("transitions"), "finding_id"),
    ):
        if not isinstance(rows, (list, tuple)):
            violations.append(f"policy.{label} must be a sequence")
            continue
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                violations.append(f"{label}[{index}] must be a mapping")
                continue
            violations.extend(_identifier_kind_violations(
                row.get(key), f"{label}[{index}].{key}"
            ))

    currency = policy.get("currency")
    if not isinstance(currency, dict):
        violations.append("policy.currency must be a mapping")
        return violations
    for section in ("documents", "postreview_documents", "historical_records"):
        rows = currency.get(section)
        if not isinstance(rows, (list, tuple)):
            violations.append(f"policy.currency.{section} must be a sequence")
            continue
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                violations.append(f"currency.{section}[{index}] must be a mapping")
                continue
            violations.extend(_identifier_kind_violations(
                row.get("path"), f"currency.{section}[{index}].path"
            ))
    return violations


def _total(label: str, law, *args) -> list[str]:
    """Run a sub-law and guarantee a list verdict.

    Every sub-law composed below is total BY CONSTRUCTION (the kind law above plus the
    per-law guards), so this net is the fail-closed floor and never the working path:
    an escape still becomes a violation — the aggregate can be wrong, but it can never
    raise and it can never fall silent."""
    try:
        verdicts = law(*args)
    except Exception as exc:  # noqa: BLE001 - totality floor; the escape becomes data
        return [f"{label}: law raised {type(exc).__name__}"]
    if not isinstance(verdicts, list):
        return [f"{label}: law returned a non-list verdict"]
    return verdicts


# --- PDC-R2-FINAL-ADV-002: the immutable seat binding --------------------------------


def immutable_seat_binding_check(policy, events) -> list[str]:
    """The ratified seats are a MODULE CONSTANT, not policy data.

    `closed_policy_rows_check` pins the terminal seat values inside the policy; this
    law pins the seat that the lifecycle log actually dispatches to. Re-pointing
    `successor.green_builder` at the RED-author seat AND matching the GREEN_DISPATCH
    payload to it keeps the log internally consistent — and still fails here."""
    violations: list[str] = []
    builder = SEATS["green_builder"]
    successor = policy.get("successor") if isinstance(policy, dict) else None
    if isinstance(successor, dict) and successor.get("green_builder") != builder:
        violations.append(
            f"policy.successor.green_builder must be the ratified {builder!r} seat"
        )
    if not isinstance(events, (list, tuple)):
        return violations
    for index, event in enumerate(events):
        if not isinstance(event, (list, tuple)) or len(event) != 2:
            continue
        kind, payload = event
        if kind != "GREEN_DISPATCH" or not isinstance(payload, dict):
            continue
        if payload.get("builder_seat") != builder:
            violations.append(
                f"event {index}.GREEN_DISPATCH: builder_seat must be the ratified "
                f"{builder!r} seat"
            )
    return violations


# --- PDC-R2-CODE-FINAL-002: the declared-document arm of the aggregate ---------------


def declared_document_scan(policy, rel_path, text) -> list[str]:
    """The roster-bound arm the aggregate applies to a supplied document body.

    It reuses the SAME roster/exemption decision as `exemption_aware_scan` — an
    undeclared path fails closed, a declared-history path is exempt — and applies the
    row's declared forbidden patterns plus the CURRENCY proposition that gives this
    policy its name: a governed process document that never names the ratified
    conductor seat is by definition not current.

    The row's full `required_propositions` roster is deliberately NOT applied here.
    That roster is asserted against the LIVE document bytes by the currency REDs; the
    aggregate receives arbitrary supplied text, which is not required to be a whole
    governed document."""
    row = declared_currency_row(policy, rel_path)
    if row is None:
        return [f"undeclared document: {rel_path}"]
    if isinstance(rel_path, str) and rel_path.startswith(LAWFUL_EXEMPT_PREFIXES):
        return []
    violations = _forbidden_pattern_violations(row, rel_path, text)
    roles = policy.get("roles") if isinstance(policy, dict) else None
    seat = roles.get("conductor") if isinstance(roles, dict) else None
    if not isinstance(seat, str) or not seat:
        return violations + [f"{rel_path}: policy.roles.conductor must name a seat"]
    normalized = normalize_governance_text(text)
    if normalized is None:
        return violations + [f"{rel_path}: document text must be a string"]
    if seat not in normalized:
        violations.append(
            f"{rel_path}: required proposition absent: the governed document never "
            f"names the ratified conductor seat {seat!r}"
        )
    return violations


# --- PDC-CODE-R2-VALIDATOR-COMPOSITION-001 + PDC-R2-CODE-FINAL-002 --------------------
# The one atomic entry point.


def validate_process_governance(policy, identity_records, events, documents) -> list[str]:
    """The single production entry point.

    It evaluates EVERY predecessor and successor law on every call — value kinds,
    policy closure in both directions, the nested-row/terminal-value closure, the
    declared-history exemption closure, the immutable seat binding, the identity chain,
    the successor log, and the governed-document scan (authority + finiteness +
    declared-roster arms) — and returns one deterministic, category-prefixed violation
    list. Omitting any sub-law lets a named mutant live; malformed input becomes
    violations, never an exception."""
    violations = [
        f"policy: {item}" for item in _total("shape", policy_value_shape_check, policy)
    ]
    violations.extend(
        f"policy: {item}"
        for item in _total("closure", closed_process_policy_check, policy)
    )
    violations.extend(
        f"policy: {item}" for item in _total("rows", closed_policy_rows_check, policy)
    )
    violations.extend(
        f"exemption: {item}"
        for item in _total("exemption", exemption_closure_check, policy)
    )
    violations.extend(
        f"seat: {item}"
        for item in _total("seat", immutable_seat_binding_check, policy, events)
    )
    if isinstance(policy, dict):
        separation = policy.get("separation")
        schema = separation.get("record_schema") if isinstance(separation, dict) else None
        violations.extend(
            f"identity: {item}" for item in _total(
                "identity", closed_identity_chain_check,
                identity_records, schema, policy.get("roles"),
            )
        )
        violations.extend(
            f"successor: {item}"
            for item in _total("successor", closed_successor_log_check, events, policy)
        )
    else:
        violations.append("identity: policy unavailable")
        violations.append("successor: policy unavailable")
    if not isinstance(documents, dict):
        violations.append("scan: documents must be a path-to-text mapping")
        return violations
    for doc_path in sorted(documents, key=lambda key: (not isinstance(key, str), str(key))):
        if not isinstance(doc_path, str):
            violations.append(f"scan: document path must be a string, got {doc_path!r}")
            continue
        text = documents[doc_path]
        skill = doc_path.startswith("skills/")
        violations.extend(
            f"scan: {doc_path}: {item}"
            for item in _total("role", role_authority_text_check, text, skill)
        )
        violations.extend(
            f"scan: {doc_path}: {item}"
            for item in _total("finiteness", review_finiteness_text_check, text)
        )
        violations.extend(
            f"scan: {doc_path}: {item}"
            for item in _total("declared", declared_document_scan, policy, doc_path, text)
        )
    return violations

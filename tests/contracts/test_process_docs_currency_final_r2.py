"""Executable successor RED for the seven process-currentness R2 findings.

This is a RED-author artifact, not a design or review verdict.  It preserves the
already-green 38 predecessor cases and names only successor gaps found against the
finished currentness patch: live role/re-review prose, atomic validator composition,
Unicode-safe authority scanning, immutable cross-record identities, closed event
payloads, and complete policy/row/transition closure.

Every failing assertion starts with ``PROCESS-DOC-CURRENTNESS-R2-RED:``.  The
reference helpers are pure, deterministic, and intentionally local to the RED; GREEN
must expose the demanded production callables from
``scripts/organization/process_governance_validator.py`` without importing this test.
"""
from __future__ import annotations

import copy
import importlib.util
import re
import unicodedata
import unittest
from pathlib import Path, PurePosixPath

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11 in the governed environment
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "contracts" / "process_docs_currency_policy.toml"
VALIDATOR_PATH = ROOT / "scripts" / "organization" / "process_governance_validator.py"
FINGERPRINT = "PROCESS-DOC-CURRENTNESS-R2-RED:"

FINDING_TO_TEST = {
    "PDC-CODE-R2-ROLE-CURRENTNESS-001":
        "test_live_role_currentness_has_no_fable_conductor_or_apply_authority",
    "PDC-CODE-R2-POSTREVIEW-FINITENESS-001":
        "test_live_process_docs_do_not_prescribe_re_rounding_reviews",
    "PDC-CODE-R2-VALIDATOR-COMPOSITION-001":
        "test_one_production_entry_point_atomically_composes_all_laws",
    "PDC-R2-ADV-001":
        "test_normalized_role_and_skill_authority_kills_modal_passive_and_unicode_attacks",
    "PDC-R2-ADV-002":
        "test_cross_record_identity_binding_and_ascii_identifier_grammar",
    "PDC-R2-ADV-003":
        "test_event_payloads_are_closed_and_malformed_inputs_return_violations",
    "PDC-R2-ADV-004":
        "test_policy_is_closed_unique_path_normalized_and_composed_end_to_end",
}

MUTANTS = {
    "PDC-CODE-R2-ROLE-CURRENTNESS-001": (
        "MUT-LIVE-FABLE-APPLIES",
        "MUT-LIVE-FABLE-COMMITS",
        "MUT-LIVE-FABLE-CONDUCTOR-NARRATION",
        "MUT-ROLE-PATTERN-REMOVED",
    ),
    "PDC-CODE-R2-POSTREVIEW-FINITENESS-001": (
        "MUT-RE-ROUNDS-AT-XHIGH",
        "MUT-IF-REVISE-REVIEW-AGAIN",
        "MUT-FRESH-REVIEW-PRESCRIPTION",
    ),
    "PDC-CODE-R2-VALIDATOR-COMPOSITION-001": (
        "MUT-COMPOSITE-OMITS-POLICY",
        "MUT-COMPOSITE-OMITS-IDENTITY",
        "MUT-COMPOSITE-OMITS-SUCCESSOR",
        "MUT-COMPOSITE-OMITS-SCAN",
    ),
    "PDC-R2-ADV-001": (
        "MUT-MODAL-FABLE-WILL-APPLY",
        "MUT-PASSIVE-COMMIT-BY-FABLE",
        "MUT-SKILL-LIFECYCLE-PASSIVE",
        "MUT-SKILL-RESPONSIBLE-FOR-APPROVAL",
        "MUT-FULLWIDTH-FABLE",
        "MUT-ZERO-WIDTH-FABLE",
        "MUT-LAWFUL-DESIGN-AUTHOR-FALSE-POSITIVE",
    ),
    "PDC-R2-ADV-002": (
        "MUT-CROSS-RECORD-REVIEWER-SWAP",
        "MUT-CROSS-RECORD-BUILDER-SWAP",
        "MUT-CONFUSABLE-SESSION-ID",
        "MUT-NONCANONICAL-SESSION-ID",
        "MUT-UNKNOWN-IDENTITY-FIELD",
    ),
    "PDC-R2-ADV-003": (
        "MUT-RED-RESET-PAYLOAD",
        "MUT-CONFORMANCE-WAIVER-PAYLOAD",
        "MUT-DISPATCH-WAIVER-PAYLOAD",
        "MUT-MALFORMED-EVENTS-CONTAINER",
        "MUT-MALFORMED-EVENT-ROW",
        "MUT-MALFORMED-EVENT-PAYLOAD",
    ),
    "PDC-R2-ADV-004": (
        "MUT-TOP-LEVEL-KEY-SMUGGLED",
        "MUT-NESTED-KEY-SMUGGLED",
        "MUT-DOCUMENT-ROW-KEY-SMUGGLED",
        "MUT-TRANSITION-ROW-KEY-SMUGGLED",
        "MUT-DUPLICATE-DOCUMENT-PATH",
        "MUT-DUPLICATE-TRANSITION-ID",
        "MUT-DOTDOT-HISTORY-EXEMPTION",
        "MUT-COMPOSITE-NONATOMIC",
        "MUT-REQUIRED-KEY-DELETION-MATRIX",
    ),
}

R2_RED_AUTHOR_SEAT = "codex-max"


# These patterns are applied only after NFKC normalization and removal of Unicode
# format controls.  The direct-duty grammar deliberately requires a duty verb next
# to the Fable subject; it does not reject lawful "Fable authors the design" prose.
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

REVIEW_LOOP_PATTERNS = (
    r"(?i)\b(?:codex|reviewer|review\s+authority)\b[^.\n]{0,100}\breviews?\b"
    r"[^.\n]{0,100}\bre[- ]?rounds?\b",
    r"(?i)\bre[- ]?rounds?\b[^.\n]{0,100}\b(?:design\s+)?review\b",
    r"(?i)\b(?:must|shall|should|will|may)\s+(?:repeat|rerun|re-run|request|launch|"
    r"dispatch|perform)\b[^.\n]{0,100}\b(?:another|fresh|new|independent|subsequent)?"
    r"\s*(?:design\s+)?review\b",
    r"(?i)\bif\s+[^.\n]{0,60}\brevise\b[^.\n]{0,100}\b(?:review\s+again|another\s+"
    r"review|next\s+review|new\s+round)\b",
)

ROLE_ATTACKS = (
    "Fable will apply the final patch.",
    "Fable 5 must integrate and commit the accepted bytes.",
    "The exact patch is committed by Fable.",
    "Verification is performed by Fable 5.",
    "Ｆａｂｌｅ will apply the final patch.",
    "Fa\u200bble commits the approved bytes.",
)
SKILL_ATTACKS = (
    "GREEN dispatch is performed by this skill.",
    "Approval belongs to the reference.",
    "This lane will review and merge the patch.",
    "The skill is responsible for integration and commit.",
)
AUTHORITY_CONTROLS = (
    "Fable authors the bounded design only.",
    "Fable does not implement GREEN, integrate, commit, or approve.",
    "A different Opus builder applies the patch.",
    "`/root` verifies, integrates, and commits.",
    "This skill owns no lifecycle and mints no verdict.",
    "The skill explains domain proving methods.",
)
REVIEW_ATTACKS = (
    "Codex reviews the landing diff and re-rounds at xhigh.",
    "If the verdict is REVISE, request another review.",
    "The conductor must launch a fresh design review.",
)
REVIEW_CONTROLS = (
    "No review-of-review is authorized.",
    "One bounded RED-conformance check runs, then Opus builds.",
    "The historical record says its repeat independent DESIGN review ran in 2026.",
    "New findings become executable evidence slices.",
)

TOP_LEVEL_KEYS = {
    "meta", "roles", "separation", "successor", "lineage", "review_families",
    "transition_classes", "transitions", "currency",
}
NESTED_KEYS = {
    "meta": {"contract_id", "schema_version", "ratified", "law_source", "authority_doc"},
    "roles": {"conductor", "design_red_author", "green_builder", "reviewer"},
    "separation": {
        "reviewer_may_author_red", "red_author_may_build_green",
        "author_approves_own_artifact", "record_schema",
    },
    "successor": {
        "max_conformance_checks", "required_next_event", "green_builder",
        "forbidden_after_red_accepted", "dispatch_schema",
    },
    "lineage": {
        "prose_review_cap", "terminal_verdicts", "identity_preserving_events",
        "reset_events",
    },
    "transition_classes": {"classes"},
    "currency": {
        "historical_exempt_prefixes", "documents", "postreview_documents",
        "historical_records",
    },
}
RECORD_SCHEMA_KEYS = {"required_keys", "allow_unknown_keys"}
DISPATCH_SCHEMA_KEYS = {"required_keys", "allowed_keys"}
TRANSITION_KEYS = {
    "finding_id", "transition_class", "status", "dependency", "source_review",
    "owner_seat", "evidence",
}
LIVE_ROW_KEYS = {"path", "role", "forbidden_patterns", "required_propositions"}
SEALED_ROW_EXTRA_KEYS = {"adoption_sha256"}
HISTORY_DOC_KEYS = {
    "path", "role", "historical_exempt", "immutable_prefix_sha256",
    "immutable_prefix_bytes", "forbidden_patterns", "required_propositions",
}
HISTORICAL_RECORD_KEYS = {"path", "sha256", "enforcement"}
FAMILY_BASE_KEYS = {
    "family_id", "prose_reviews_used", "terminal_verdict_token",
    "another_prose_review_authorized",
}
FAMILY_SKILL_EXTRA_KEYS = {"findings", "terminal_review_doc"}

EVENT_SCHEMAS = {
    "RED_ACCEPTED": (set(), set()),
    "CONFORMANCE_PASSED": (set(), set()),
    "GREEN_DISPATCH": (
        {"builder_seat", "builder_session", "red_author_session"},
        {"builder_seat", "builder_session", "red_author_session"},
    ),
    "PROSE_REVIEW": ({"verdict"}, {"verdict"}),
    "REVIEW_OF_REVIEW": (set(), set()),
}


def normalize_governance_text(value) -> str | None:
    """NFKC + format-control removal; non-strings fail closed."""
    if not isinstance(value, str):
        return None
    text = unicodedata.normalize("NFKC", value)
    return "".join(ch for ch in text if unicodedata.category(ch) != "Cf")


def reference_role_text_check(text: str, *, skill: bool = False) -> list[str]:
    normalized = normalize_governance_text(text)
    if normalized is None:
        return ["authority text must be a string"]
    violations = [
        f"forbidden Fable conductor/build duty: {pattern}"
        for pattern in ROLE_AUTHORITY_PATTERNS if re.search(pattern, normalized)
    ]
    if skill:
        violations.extend(
            f"skill reclaims lifecycle authority: {pattern}"
            for pattern in SKILL_REOWNERSHIP_PATTERNS if re.search(pattern, normalized)
        )
    return violations


def reference_review_finiteness_check(text: str) -> list[str]:
    normalized = normalize_governance_text(text)
    if normalized is None:
        return ["review text must be a string"]
    return [
        f"repeated prose-review prescription: {pattern}"
        for pattern in REVIEW_LOOP_PATTERNS if re.search(pattern, normalized)
    ]


def _canonical_identifier(value) -> str | None:
    normalized = normalize_governance_text(value)
    if normalized is None:
        return None
    return normalized.strip().casefold()


def _identifier_violations(value, label: str, *, seat: bool = False) -> list[str]:
    if not isinstance(value, str) or not value:
        return [f"{label}: identifier must be a non-empty string"]
    canonical = _canonical_identifier(value)
    if value != canonical:
        return [f"{label}: identifier must already be canonical ASCII"]
    grammar = r"(?:/[a-z0-9][a-z0-9._/-]*|[a-z0-9][a-z0-9._:-]*)" if seat else (
        r"[a-z0-9][a-z0-9._:-]*"
    )
    if not value.isascii() or re.fullmatch(grammar, value) is None:
        return [f"{label}: identifier violates the ASCII-safe grammar"]
    if len(value) > 128:
        return [f"{label}: identifier exceeds 128 bytes"]
    return []


def reference_identity_chain_check(records, schema: dict, roles: dict) -> list[str]:
    if not isinstance(records, (list, tuple)) or not records:
        return ["identity records must be a non-empty sequence"]
    required = schema.get("required_keys", []) if isinstance(schema, dict) else []
    if not isinstance(required, list) or not all(isinstance(key, str) for key in required):
        return ["identity schema required_keys must be a string list"]
    violations: list[str] = []
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
        if record["red_author_seat"] != R2_RED_AUTHOR_SEAT:
            violations.append(f"identity record {index}: wrong RED-author seat")
        if record["reviewer_seat"] != roles.get("reviewer"):
            violations.append(f"identity record {index}: wrong reviewer seat")
        if record["green_builder_seat"] != roles.get("green_builder"):
            violations.append(f"identity record {index}: wrong GREEN-builder seat")
        sessions = [
            record["red_author_session"], record["reviewer_session"],
            record["green_builder_session"],
        ]
        if len(set(sessions)) != 3:
            violations.append(f"identity record {index}: sessions must be pairwise distinct")
        current = tuple(record[key] for key in required)
        if binding is None:
            binding = current
        elif current != binding:
            violations.append(
                f"identity record {index}: immutable identity binding changed across records"
            )
    return violations


def reference_event_log_check(events, policy: dict) -> list[str]:
    if not isinstance(events, (list, tuple)):
        return ["lifecycle events must be a sequence"]
    violations: list[str] = []
    parsed: list[tuple[str, dict]] = []
    for index, event in enumerate(events):
        if not isinstance(event, (list, tuple)) or len(event) != 2:
            violations.append(f"event {index} must be a two-item sequence")
            continue
        kind, payload = event
        if not isinstance(kind, str) or re.fullmatch(r"[A-Z][A-Z0-9_]*", kind) is None:
            violations.append(f"event {index} kind must use the ASCII event grammar")
            continue
        if kind not in EVENT_SCHEMAS:
            violations.append(f"event {index}: unknown lifecycle event {kind}")
            continue
        if not isinstance(payload, dict):
            violations.append(f"event {index}.{kind}: payload must be a mapping")
            continue
        required, allowed = EVENT_SCHEMAS[kind]
        missing = sorted(required - set(payload))
        unknown = sorted(set(payload) - allowed)
        if missing:
            violations.append(f"event {index}.{kind}: missing payload keys {missing}")
        if unknown:
            violations.append(f"event {index}.{kind}: unknown payload keys {unknown}")
        parsed.append((kind, payload))
    if violations:
        return violations

    kinds = [kind for kind, _ in parsed]
    if kinds != ["RED_ACCEPTED", "CONFORMANCE_PASSED", "GREEN_DISPATCH"]:
        violations.append(
            "lifecycle must be exactly RED_ACCEPTED, CONFORMANCE_PASSED, GREEN_DISPATCH"
        )
        return violations
    successor = policy.get("successor") if isinstance(policy, dict) else None
    if not isinstance(successor, dict):
        return ["policy.successor must be a mapping"]
    dispatch = parsed[-1][1]
    for key in ("builder_seat", "builder_session", "red_author_session"):
        violations.extend(_identifier_violations(
            dispatch.get(key), f"GREEN_DISPATCH.{key}", seat=key == "builder_seat"
        ))
    if dispatch.get("builder_seat") != successor.get("green_builder"):
        violations.append("GREEN_DISPATCH builder seat must equal policy successor")
    if dispatch.get("builder_session") == dispatch.get("red_author_session"):
        violations.append("GREEN builder and RED author sessions must be distinct")
    return violations


def _path_violations(path, label: str) -> list[str]:
    if not isinstance(path, str) or not path:
        return [f"{label}: path must be a non-empty string"]
    if not path.isascii() or "\\" in path or path.startswith("/"):
        return [f"{label}: path must be relative canonical ASCII POSIX"]
    parts = PurePosixPath(path).parts
    if any(part in ("", ".", "..") for part in parts) or "//" in path:
        return [f"{label}: path contains a normalization escape"]
    if PurePosixPath(path).as_posix() != path:
        return [f"{label}: path is not canonical POSIX"]
    return []


def _closed_keys(mapping, required: set[str], allowed: set[str], label: str) -> list[str]:
    if not isinstance(mapping, dict):
        return [f"{label} must be a mapping"]
    missing = sorted(required - set(mapping))
    unknown = sorted(set(mapping) - allowed)
    violations = []
    if missing:
        violations.append(f"{label}: missing keys {missing}")
    if unknown:
        violations.append(f"{label}: unknown keys {unknown}")
    return violations


def reference_policy_structure_check(policy) -> list[str]:
    if not isinstance(policy, dict):
        return ["policy must be a mapping"]
    violations = _closed_keys(policy, TOP_LEVEL_KEYS, TOP_LEVEL_KEYS, "policy")
    for name, allowed in NESTED_KEYS.items():
        if name in policy:
            violations.extend(_closed_keys(policy[name], allowed, allowed, f"policy.{name}"))
    separation = policy.get("separation", {})
    if isinstance(separation, dict) and "record_schema" in separation:
        violations.extend(_closed_keys(
            separation["record_schema"], RECORD_SCHEMA_KEYS, RECORD_SCHEMA_KEYS,
            "policy.separation.record_schema",
        ))
    successor = policy.get("successor", {})
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
                if isinstance(row, dict) and row.get("family_id") == "semantic-tdd-conductor-skill"
                else set()
            )
            violations.extend(_closed_keys(row, allowed, allowed, f"review_families[{index}]"))
            if isinstance(row, dict):
                family_ids.append(row.get("family_id"))
        if len(family_ids) != len(set(family_ids)):
            violations.append("review_families contain duplicate family_id values")

    transitions = policy.get("transitions", [])
    if not isinstance(transitions, list):
        violations.append("policy.transitions must be a list")
    else:
        ids = []
        for index, row in enumerate(transitions):
            violations.extend(_closed_keys(
                row, TRANSITION_KEYS, TRANSITION_KEYS, f"transitions[{index}]"
            ))
            if isinstance(row, dict):
                ids.append(row.get("finding_id"))
        if len(ids) != len(set(ids)):
            violations.append("transitions contain duplicate finding_id values")

    currency = policy.get("currency", {})
    if isinstance(currency, dict):
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
                    allowed = HISTORY_DOC_KEYS
                    required = HISTORY_DOC_KEYS
                else:
                    allowed = LIVE_ROW_KEYS | (SEALED_ROW_EXTRA_KEYS if section == "documents" else set())
                    required = LIVE_ROW_KEYS
                violations.extend(_closed_keys(row, required, allowed, label))
                violations.extend(_path_violations(row.get("path"), f"{label}.path"))
                all_paths.append(row.get("path"))
        if len(all_paths) != len(set(all_paths)):
            violations.append("currency document rosters contain duplicate path values")
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
            if len(record_paths) != len(set(record_paths)):
                violations.append("historical_records contain duplicate path values")
        prefixes = currency.get("historical_exempt_prefixes", [])
        if not isinstance(prefixes, list):
            violations.append("historical_exempt_prefixes must be a list")
        else:
            for index, prefix in enumerate(prefixes):
                candidate = prefix[:-1] if isinstance(prefix, str) and prefix.endswith("/") else prefix
                violations.extend(_path_violations(candidate, f"historical_exempt_prefixes[{index}]"))
                if not isinstance(prefix, str) or not prefix.endswith("/"):
                    violations.append(f"historical_exempt_prefixes[{index}] must end in '/'")
    return violations


def _live_document_map(policy: dict) -> dict[str, str]:
    documents = {}
    currency = policy.get("currency", {})
    for section in ("documents", "postreview_documents"):
        for row in currency.get(section, []):
            path = row.get("path")
            if not isinstance(path, str) or row.get("historical_exempt") is True:
                continue
            file_path = ROOT / path
            if file_path.is_file():
                documents[path] = file_path.read_text(encoding="utf-8")
    return documents


def _lawful_identity_records() -> list[dict]:
    row = {
        "red_author_seat": R2_RED_AUTHOR_SEAT,
        "red_author_session": "codex-max-red-r2",
        "reviewer_seat": "codex",
        "reviewer_session": "codex-review-r2",
        "green_builder_seat": "opus",
        "green_builder_session": "opus-green-r2",
    }
    return [dict(row), dict(row), dict(row)]


def _lawful_events() -> list[tuple[str, dict]]:
    return [
        ("RED_ACCEPTED", {}),
        ("CONFORMANCE_PASSED", {}),
        ("GREEN_DISPATCH", {
            "builder_seat": "opus",
            "builder_session": "opus-green-r2",
            "red_author_session": "codex-max-red-r2",
        }),
    ]


def reference_validate_process_governance(
    policy, identity_records, events, documents
) -> list[str]:
    """Atomic reference composer: no sub-law can be omitted without a named mutant living."""
    violations = [
        f"policy: {item}" for item in reference_policy_structure_check(policy)
    ]
    if isinstance(policy, dict):
        separation = policy.get("separation", {})
        roles = policy.get("roles", {})
        schema = separation.get("record_schema", {}) if isinstance(separation, dict) else {}
        violations.extend(
            f"identity: {item}"
            for item in reference_identity_chain_check(identity_records, schema, roles)
        )
        violations.extend(
            f"successor: {item}" for item in reference_event_log_check(events, policy)
        )
    else:
        violations.extend(("identity: policy unavailable", "successor: policy unavailable"))
    if not isinstance(documents, dict):
        violations.append("scan: documents must be a path-to-text mapping")
    else:
        for doc_path, text in sorted(documents.items()):
            if not isinstance(doc_path, str):
                violations.append("scan: document path must be a string")
                continue
            skill = doc_path.startswith("skills/")
            violations.extend(
                f"scan: {doc_path}: {item}"
                for item in reference_role_text_check(text, skill=skill)
            )
            violations.extend(
                f"scan: {doc_path}: {item}"
                for item in reference_review_finiteness_check(text)
            )
    return violations


def _safe_call(callable_, *args):
    try:
        return callable_(*args)
    except Exception as exc:  # exceptions become deterministic RED failures, never test errors
        return [f"production validator raised {type(exc).__name__}: {exc}"]


def load_validator():
    if not VALIDATOR_PATH.is_file():
        return None
    spec = importlib.util.spec_from_file_location("process_governance_validator_r2", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return None
    return module


class ProcessDocsCurrencyFinalR2Red(unittest.TestCase):
    """Seven independent executable findings; no test mutates repository files."""

    maxDiff = None

    def setUp(self) -> None:
        if not POLICY_PATH.is_file():
            self.fail(f"{FINGERPRINT} policy artifact absent: {POLICY_PATH.relative_to(ROOT)}")
        self.policy = tomllib.loads(POLICY_PATH.read_text(encoding="utf-8"))
        self.validator = load_validator()
        self._executed_mutants: set[str] = set()

    def _red(self, condition: bool, detail: str) -> None:
        if not condition:
            self.fail(f"{FINGERPRINT} {detail}")

    def _kill(self, mutant_id: str, condition: bool, detail: str) -> None:
        declared = {item for values in MUTANTS.values() for item in values}
        self._red(mutant_id in declared, f"undeclared mutant exercised: {mutant_id}")
        self._executed_mutants.add(mutant_id)
        self._red(condition, f"{mutant_id} survived: {detail}")

    def _assert_mutants_exercised(self, finding_id: str) -> None:
        missing = sorted(set(MUTANTS[finding_id]) - self._executed_mutants)
        self._red(not missing, f"declared mutants were not exercised: {missing}")

    def _demand(self, name: str):
        self._red(self.validator is not None, "governed production validator is not loadable")
        callable_ = getattr(self.validator, name, None)
        self._red(callable(callable_), f"production validator lacks callable {name}")
        return callable_

    def test_live_role_currentness_has_no_fable_conductor_or_apply_authority(self) -> None:
        """PDC-CODE-R2-ROLE-CURRENTNESS-001."""
        witnesses = {
            "MUT-LIVE-FABLE-APPLIES": "Fable applies the draft to a clean worktree.",
            "MUT-LIVE-FABLE-COMMITS": "Fable commits the exact approved patch.",
            "MUT-LIVE-FABLE-CONDUCTOR-NARRATION": "Fable, the conductor, integrates.",
        }
        for mutant_id, witness in witnesses.items():
            self._kill(
                mutant_id, bool(reference_role_text_check(witness)),
                f"sealed role-authority witness escaped: {witness!r}",
            )
        direct = normalize_governance_text(witnesses["MUT-LIVE-FABLE-APPLIES"])
        self._kill(
            "MUT-ROLE-PATTERN-REMOVED",
            bool(reference_role_text_check(direct))
            and all(re.search(pattern, direct) is None for pattern in ROLE_AUTHORITY_PATTERNS[1:]),
            "removing the direct-duty arm must let its sealed witness escape",
        )
        self._assert_mutants_exercised("PDC-CODE-R2-ROLE-CURRENTNESS-001")
        live = _live_document_map(self.policy)
        production = self._demand("role_authority_text_check")
        violations = []
        for path, text in live.items():
            violations.extend(
                f"{path}: {item}" for item in _safe_call(
                    production, text, path.startswith("skills/")
                )
            )
        self._red(
            not violations,
            "live governed documents retain Fable conductor/apply/integrate/commit authority: "
            + " | ".join(violations),
        )

    def test_live_process_docs_do_not_prescribe_re_rounding_reviews(self) -> None:
        """PDC-CODE-R2-POSTREVIEW-FINITENESS-001."""
        for mutant_id, witness in zip(MUTANTS["PDC-CODE-R2-POSTREVIEW-FINITENESS-001"], REVIEW_ATTACKS):
            self._kill(
                mutant_id, bool(reference_review_finiteness_check(witness)),
                f"sealed repeated-review witness escaped: {witness!r}",
            )
        self._assert_mutants_exercised("PDC-CODE-R2-POSTREVIEW-FINITENESS-001")
        live = _live_document_map(self.policy)
        production = self._demand("review_finiteness_text_check")
        violations = []
        for path, text in live.items():
            violations.extend(f"{path}: {item}" for item in _safe_call(production, text))
        self._red(
            not violations,
            "live governed documents still prescribe repeated prose review: "
            + " | ".join(violations),
        )

    def test_one_production_entry_point_atomically_composes_all_laws(self) -> None:
        """PDC-CODE-R2-VALIDATOR-COMPOSITION-001."""
        documents = {
            "AGENTS.md": "`/root` conducts. Fable authors the bounded design. Opus builds."
        }
        reference_lawful = reference_validate_process_governance(
            copy.deepcopy(self.policy), _lawful_identity_records(), _lawful_events(), documents
        )
        self._red(not reference_lawful, f"reference lawful composite must pass: {reference_lawful}")

        attacks = []
        policy_attack = copy.deepcopy(self.policy)
        policy_attack["review_reset"] = True
        attacks.append(("MUT-COMPOSITE-OMITS-POLICY", "policy", policy_attack, _lawful_identity_records(), _lawful_events(), documents))
        identity_attack = _lawful_identity_records()
        identity_attack[1]["reviewer_session"] = "codex-swapped-r2"
        attacks.append(("MUT-COMPOSITE-OMITS-IDENTITY", "identity", self.policy, identity_attack, _lawful_events(), documents))
        event_attack = _lawful_events()
        event_attack[0] = ("RED_ACCEPTED", {"waiver": True})
        attacks.append(("MUT-COMPOSITE-OMITS-SUCCESSOR", "successor", self.policy, _lawful_identity_records(), event_attack, documents))
        scan_attack = dict(documents)
        first_path = sorted(scan_attack)[0]
        scan_attack[first_path] += "\nFable will apply the final patch.\n"
        attacks.append(("MUT-COMPOSITE-OMITS-SCAN", "scan", self.policy, _lawful_identity_records(), _lawful_events(), scan_attack))
        for mutant_id, expected, policy, identities, events, docs in attacks:
            found = reference_validate_process_governance(
                copy.deepcopy(policy), copy.deepcopy(identities), copy.deepcopy(events),
                copy.deepcopy(docs),
            )
            self._kill(
                mutant_id, any(expected in str(item).casefold() for item in found),
                f"reference atomic composer omitted {expected}: {found}",
            )
        self._assert_mutants_exercised("PDC-CODE-R2-VALIDATOR-COMPOSITION-001")

        composite = self._demand("validate_process_governance")
        lawful = _safe_call(
            composite, copy.deepcopy(self.policy), _lawful_identity_records(),
            _lawful_events(), documents,
        )
        self._red(not lawful, f"lawful composite input must pass, got {lawful}")
        for mutant_id, expected, policy, identities, events, docs in attacks:
            found = _safe_call(
                composite, copy.deepcopy(policy), copy.deepcopy(identities),
                copy.deepcopy(events), copy.deepcopy(docs),
            )
            self._red(
                any(expected in str(item).casefold() for item in found),
                f"{mutant_id} survived production atomic validation: {found}",
            )

    def test_normalized_role_and_skill_authority_kills_modal_passive_and_unicode_attacks(self) -> None:
        """PDC-R2-ADV-001."""
        load_bearing = (
            ("MUT-MODAL-FABLE-WILL-APPLY", ROLE_ATTACKS[0], False),
            ("MUT-PASSIVE-COMMIT-BY-FABLE", ROLE_ATTACKS[2], False),
            ("MUT-SKILL-LIFECYCLE-PASSIVE", SKILL_ATTACKS[0], True),
            ("MUT-SKILL-RESPONSIBLE-FOR-APPROVAL", SKILL_ATTACKS[3], True),
            ("MUT-FULLWIDTH-FABLE", ROLE_ATTACKS[4], False),
            ("MUT-ZERO-WIDTH-FABLE", ROLE_ATTACKS[5], False),
        )
        for mutant_id, attack, skill in load_bearing:
            self._kill(
                mutant_id, bool(reference_role_text_check(attack, skill=skill)),
                f"normalized authority attack escaped: {attack!r}",
            )
        for attack in ROLE_ATTACKS:
            self._red(
                bool(reference_role_text_check(attack)),
                f"reference role grammar failed to kill attack {attack!r}",
            )
        for attack in SKILL_ATTACKS:
            self._red(
                bool(reference_role_text_check(attack, skill=True)),
                f"reference skill grammar failed to kill attack {attack!r}",
            )
        for control in AUTHORITY_CONTROLS:
            self._red(
                reference_role_text_check(control, skill=True) == [],
                f"reference role grammar false-positive on lawful control {control!r}",
            )
        self._kill(
            "MUT-LAWFUL-DESIGN-AUTHOR-FALSE-POSITIVE",
            all(reference_role_text_check(control, skill=True) == []
                for control in AUTHORITY_CONTROLS),
            "a lawful design-only/control sentence was rejected",
        )
        self._assert_mutants_exercised("PDC-R2-ADV-001")

        production_normalize = self._demand("normalize_governance_text")
        production_check = self._demand("role_authority_text_check")
        for attack in ROLE_ATTACKS:
            normalized = _safe_call(production_normalize, attack)
            self._red(
                isinstance(normalized, str),
                f"production normalization failed deterministically on {attack!r}: {normalized}",
            )
            self._red(
                bool(_safe_call(production_check, attack, False)),
                f"normalized role attack survived: {attack!r}",
            )
        for attack in SKILL_ATTACKS:
            self._red(
                bool(_safe_call(production_check, attack, True)),
                f"skill lifecycle reownership survived: {attack!r}",
            )
        for control in AUTHORITY_CONTROLS:
            self._red(
                _safe_call(production_check, control, True) == [],
                f"lawful authority control was rejected: {control!r}",
            )

    def test_cross_record_identity_binding_and_ascii_identifier_grammar(self) -> None:
        """PDC-R2-ADV-002."""
        schema = self.policy["separation"]["record_schema"]
        roles = self.policy["roles"]
        lawful = _lawful_identity_records()
        self._red(
            reference_identity_chain_check(lawful, schema, roles) == [],
            "reference identity chain rejects its lawful control",
        )
        attacks = []
        swapped_reviewer = copy.deepcopy(lawful)
        swapped_reviewer[1]["reviewer_session"] = "codex-other-r2"
        attacks.append(swapped_reviewer)
        swapped_builder = copy.deepcopy(lawful)
        swapped_builder[2]["green_builder_session"] = "opus-other-r2"
        attacks.append(swapped_builder)
        confusable = copy.deepcopy(lawful)
        confusable[0]["reviewer_session"] = "c\u043edex-review-r2"  # Cyrillic small o
        attacks.append(confusable)
        noncanonical = copy.deepcopy(lawful)
        noncanonical[0]["reviewer_session"] = "Codex-Review-R2 "
        attacks.append(noncanonical)
        unknown = copy.deepcopy(lawful)
        unknown[0]["identity_waiver"] = True
        attacks.append(unknown)
        for mutant_id, attack in zip(MUTANTS["PDC-R2-ADV-002"], attacks):
            self._kill(
                mutant_id, bool(reference_identity_chain_check(attack, schema, roles)),
                f"reference identity chain accepted attack {attack!r}",
            )
        self._assert_mutants_exercised("PDC-R2-ADV-002")
        production = self._demand("closed_identity_chain_check")
        self._red(
            _safe_call(production, lawful, schema, roles) == [],
            "production identity chain rejects its lawful control",
        )
        for attack in attacks:
            self._red(
                bool(_safe_call(production, attack, schema, roles)),
                f"cross-record or identifier attack survived: {attack!r}",
            )

    def test_event_payloads_are_closed_and_malformed_inputs_return_violations(self) -> None:
        """PDC-R2-ADV-003."""
        lawful = _lawful_events()
        attacks = [
            [("RED_ACCEPTED", {"reset": True})] + lawful[1:],
            [lawful[0], ("CONFORMANCE_PASSED", {"waiver": True}), lawful[2]],
            lawful[:-1] + [("GREEN_DISPATCH", dict(lawful[-1][1], review_waiver=True))],
            None,
            ["RED_ACCEPTED", lawful[1], lawful[2]],
            [lawful[0], ("CONFORMANCE_PASSED", []), lawful[2]],
        ]
        self._red(
            reference_event_log_check(lawful, self.policy) == [],
            "reference event law rejects the lawful lifecycle",
        )
        for mutant_id, attack in zip(MUTANTS["PDC-R2-ADV-003"], attacks):
            self._kill(
                mutant_id, bool(reference_event_log_check(attack, self.policy)),
                f"reference event law accepted attack {attack!r}",
            )
        self._assert_mutants_exercised("PDC-R2-ADV-003")

        production = self._demand("closed_successor_log_check")
        self._red(
            _safe_call(production, lawful, self.policy) == [],
            "production successor law rejects the lawful lifecycle",
        )
        for attack in attacks:
            found = _safe_call(production, attack, self.policy)
            self._red(
                bool(found) and not any(str(item).startswith("production validator raised") for item in found),
                f"malformed/reset/waiver event must return violations without raising: {found}",
            )

    def test_policy_is_closed_unique_path_normalized_and_composed_end_to_end(self) -> None:
        """PDC-R2-ADV-004."""
        self._red(
            reference_policy_structure_check(self.policy) == [],
            "reference policy closure rejects the lawful live policy: "
            + " | ".join(reference_policy_structure_check(self.policy)),
        )
        attacks = []
        top = copy.deepcopy(self.policy)
        top["review_amnesty"] = True
        attacks.append(top)
        nested = copy.deepcopy(self.policy)
        nested["successor"]["reset_budget"] = 1
        attacks.append(nested)
        row = copy.deepcopy(self.policy)
        row["currency"]["documents"][0]["waived"] = True
        attacks.append(row)
        transition = copy.deepcopy(self.policy)
        transition["transitions"][0]["closed_by_prose"] = True
        attacks.append(transition)
        duplicate_path = copy.deepcopy(self.policy)
        duplicate_path["currency"]["postreview_documents"].append(
            copy.deepcopy(duplicate_path["currency"]["postreview_documents"][0])
        )
        attacks.append(duplicate_path)
        duplicate_transition = copy.deepcopy(self.policy)
        duplicate_transition["transitions"].append(copy.deepcopy(duplicate_transition["transitions"][0]))
        attacks.append(duplicate_transition)
        escaped = copy.deepcopy(self.policy)
        escaped["currency"]["postreview_documents"][0]["path"] = "docs/history/../plans/escape.md"
        escaped["currency"]["postreview_documents"][0]["historical_exempt"] = True
        attacks.append(escaped)
        for mutant_id, attack in zip(MUTANTS["PDC-R2-ADV-004"][:7], attacks):
            self._kill(
                mutant_id, bool(reference_policy_structure_check(attack)),
                f"reference policy closure accepted attack {attack!r}",
            )

        deletion_vectors = []
        for key in TOP_LEVEL_KEYS:
            vector = copy.deepcopy(self.policy)
            del vector[key]
            deletion_vectors.append((f"policy.{key}", vector))
        for section, required in NESTED_KEYS.items():
            for key in required:
                vector = copy.deepcopy(self.policy)
                del vector[section][key]
                deletion_vectors.append((f"policy.{section}.{key}", vector))
        for parent, child, required in (
            ("separation", "record_schema", RECORD_SCHEMA_KEYS),
            ("successor", "dispatch_schema", DISPATCH_SCHEMA_KEYS),
        ):
            for key in required:
                vector = copy.deepcopy(self.policy)
                del vector[parent][child][key]
                deletion_vectors.append((f"policy.{parent}.{child}.{key}", vector))
        for index, family in enumerate(self.policy["review_families"]):
            required = FAMILY_BASE_KEYS | (
                FAMILY_SKILL_EXTRA_KEYS
                if family.get("family_id") == "semantic-tdd-conductor-skill" else set()
            )
            for key in required:
                vector = copy.deepcopy(self.policy)
                del vector["review_families"][index][key]
                deletion_vectors.append((f"review_families[{index}].{key}", vector))
        for index in range(len(self.policy["transitions"])):
            for key in TRANSITION_KEYS:
                vector = copy.deepcopy(self.policy)
                del vector["transitions"][index][key]
                deletion_vectors.append((f"transitions[{index}].{key}", vector))
        for section in ("documents", "postreview_documents"):
            for index, document in enumerate(self.policy["currency"][section]):
                required = HISTORY_DOC_KEYS if document.get("historical_exempt") is True else LIVE_ROW_KEYS
                for key in required:
                    vector = copy.deepcopy(self.policy)
                    del vector["currency"][section][index][key]
                    deletion_vectors.append((f"currency.{section}[{index}].{key}", vector))
        for index in range(len(self.policy["currency"]["historical_records"])):
            for key in HISTORICAL_RECORD_KEYS:
                vector = copy.deepcopy(self.policy)
                del vector["currency"]["historical_records"][index][key]
                deletion_vectors.append((f"currency.historical_records[{index}].{key}", vector))
        missed_deletions = [
            label for label, vector in deletion_vectors
            if not reference_policy_structure_check(vector)
        ]
        self._kill(
            "MUT-REQUIRED-KEY-DELETION-MATRIX", not missed_deletions,
            f"required-key deletions escaped closure: {missed_deletions}",
        )

        malicious_control = {"skills/example/SKILL.md": "Approval belongs to this skill."}
        reference_end_to_end = reference_validate_process_governance(
            copy.deepcopy(self.policy), _lawful_identity_records(), _lawful_events(),
            malicious_control,
        )
        self._kill(
            "MUT-COMPOSITE-NONATOMIC",
            any("scan" in str(item).casefold() for item in reference_end_to_end),
            f"reference composite omitted skill reownership scan: {reference_end_to_end}",
        )
        self._assert_mutants_exercised("PDC-R2-ADV-004")

        structure = self._demand("closed_process_policy_check")
        self._red(
            _safe_call(structure, self.policy) == [],
            "production policy closure rejects the lawful live policy",
        )
        for attack in attacks:
            self._red(
                bool(_safe_call(structure, attack)),
                "top/nested/row/transition/duplicate/path-normalization attack survived",
            )

        composite = self._demand("validate_process_governance")
        found = _safe_call(
            composite, copy.deepcopy(self.policy), _lawful_identity_records(),
            _lawful_events(), malicious_control,
        )
        self._red(
            any("scan" in str(item).casefold() for item in found),
            f"MUT-COMPOSITE-NONATOMIC survived end-to-end skill reownership: {found}",
        )


if __name__ == "__main__":
    unittest.main()

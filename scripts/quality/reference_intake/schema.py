"""Closed, fail-closed validators for the reference-capture lane (w3c-0 §8).

Pure stdlib. Every validator enforces an EXACT closed key set (an unknown key
rejects), rejects duplicate JSON keys at parse time, and raises
``ReferenceContractError`` on the first law it can prove violated. The laws are the
slice-0 W5f-lane invariants R1-R8:

  R1  producer != approver principals; the approver principal is an operator
  R2  one hashed vocabulary — aspect ids are members of the closed 31-id set
  R3  source != target: the full closed 12-field occurrence key, vocabulary-bound
  R4  four rights dimensions present (publication / custody / redistribution / retention)
  R5  per-aspect lifecycle — approval binds the candidate hash BEFORE measurement;
      an evidence-only candidate can never carry a measurement
  R6  content-addressed immutable pack graph — replaces/replaces_manifest_sha256
      pairing + the single closed dashboard-pre-w3 legacy-adapter allowance
  R7  file-driven promotion — a promoted clause whose aspect isn't approved reddens
  R8  dynamic homes with inverse/phantom checks — every promoted clause has exactly
      one binding row and vice versa

The vocabulary itself is ``contracts/reference_aspects.json``
(``contract_id: "ReferenceAspectVocabulary"``, ``vocabulary_version: 1``).
"""

from __future__ import annotations

import hashlib
import json
import string
from pathlib import Path
from typing import Any


class ReferenceContractError(ValueError):
    """Raised when a reference-lane record violates its closed contract."""


# --------------------------------------------------------------------------- closed vocabularies
ASPECT_KINDS: frozenset[str] = frozenset({"page", "visual", "component"})
APPLIES_TO: frozenset[str] = frozenset({"page", "archetype-region", "component-occurrence"})

PAGE_ASPECTS: tuple[str, ...] = (
    "page.navigation", "page.hero-orientation", "page.hierarchy", "page.grouping",
    "page.data-presentation", "page.density", "page.alignment", "page.material-placement",
    "page.scan-path", "page.responsive-composition",
)
VISUAL_ASPECTS: tuple[str, ...] = (
    "visual.palette", "visual.typography", "visual.spacing-density", "visual.size-geometry",
    "visual.shape-radius", "visual.border-divider", "visual.elevation-shadow",
    "visual.material-blur", "visual.iconography", "visual.motion",
)
# Per-component CLOSED subaspect subsets, EXACTLY per w3c-0 §3.1 (order-significant).
COMPONENT_SUBASPECTS: dict[str, tuple[str, ...]] = {
    "component.button": ("anatomy", "geometry", "typography", "paint", "state-mechanic", "focus", "label-honesty", "icon"),
    "component.chip": ("anatomy", "geometry", "typography", "paint", "state-mechanic", "focus", "label-honesty"),
    "component.card": ("anatomy", "geometry", "paint", "divider"),
    "component.nav": ("anatomy", "geometry", "paint", "state-mechanic", "focus"),
    "component.kpi": ("anatomy", "geometry", "typography"),
    "component.input": ("anatomy", "geometry", "paint", "focus", "state-mechanic"),
    "component.table": ("anatomy", "geometry", "typography", "paint", "state-mechanic"),
    "component.chart": ("anatomy", "paint", "typography"),
    "component.hero": ("anatomy", "typography", "geometry"),
    "component.selector": ("anatomy", "geometry", "paint", "focus", "state-mechanic", "independence"),
    "component.status-row": ("anatomy", "geometry", "typography", "paint"),
}
CANONICAL_STATES: tuple[str, ...] = ("rest", "hover", "focus-visible", "active", "selected", "disabled")
PROFILE_STATE_MAP: dict[str, str] = {
    "default": "rest", "hover": "hover", "focus-visible": "focus-visible",
    "active": "active", "selected": "selected", "disabled": "disabled",
}
VISIBILITY_PHASES: tuple[str, ...] = ("initial", "hydrated")
TABLE_ANATOMY_VARIANTS: tuple[str, ...] = ("data-table", "structured-list")

# Rights (R4): four independent dimensions, each a closed enum.
PUBLICATION: frozenset[str] = frozenset({"none", "derived", "crops", "full"})
REDISTRIBUTION: frozenset[str] = frozenset({"forbidden", "quotation", "licensed", "owned"})
RETENTION_POLICIES: frozenset[str] = frozenset({"until-replaced", "dated-expiry"})

# Per-aspect lifecycle (R5), closed.
LIFECYCLE_STATES: frozenset[str] = frozenset({
    "proposed", "presented", "approved", "rejected", "pending", "expired",
    "frozen", "fidelity-confirmed", "measured", "promoted",
    "withdrawn", "revoked", "custody-lost",
})
APPROVAL_DECISIONS: frozenset[str] = frozenset({"approved", "rejected", "pending"})

# The full occurrence key (R3), closed 12 fields.
OCCURRENCE_KEY_FIELDS: frozenset[str] = frozenset({
    "target_repo_or_url", "target_revision", "route", "profile_or_context", "viewport",
    "state", "region", "subject_selector", "occurrence_index", "aspect_id",
    "vocabulary_version", "vocabulary_sha256",
})

# Promoted reference clauses keep EXACTLY the 7-key catalog shape with authority pinned.
PROMOTED_AUTHORITY = "approved-reference"
PROMOTED_AUTHORITY_TUPLE = ("measured-reference", "measurement-exact")  # (source_mode, exactness)
PROMOTED_SOURCE_KIND = "approved-reference"
PROMOTED_SOURCE_REF_PREFIX = "contracts/reference_packs/"

# The one closed legacy pack + its pinned manifest digest (w3c-0 §8).
LEGACY_PACK_ID = "dashboard-pre-w3"
LEGACY_PACK_MANIFEST_SHA256 = "34ed2ae295e8f350bd406b30e6891488c7fe6407e0d04dbed6bb93ad16544fac"

# A pack in this authority state is structurally excluded from authority (w3c-0 §5.9/§8).
REJECTED_EVIDENCE = "rejected-evidence"

# Fields that would smuggle a MEASUREMENT into an evidence-only candidate (R5).
_MEASUREMENT_FIELDS: frozenset[str] = frozenset({
    "measured_aspects", "run_sha256", "session_id", "chrome_version",
    "measurement", "measurement_run", "measured_at",
})

_HEXDIGITS = set(string.hexdigits.lower())


# --------------------------------------------------------------------------- parse + primitives
def loads_no_duplicate_keys(text: str) -> Any:
    """json.loads that rejects a duplicated key at ANY object depth (fail-closed)."""

    def _hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        seen: set[str] = set()
        for key, _ in pairs:
            if key in seen:
                raise ReferenceContractError(f"duplicate JSON key: {key!r}")
            seen.add(key)
        return dict(pairs)

    try:
        return json.loads(text, object_pairs_hook=_hook)
    except json.JSONDecodeError as exc:  # pragma: no cover - malformed bytes
        raise ReferenceContractError(f"invalid JSON: {exc}") from exc


def load_json_file(path: str | Path) -> Any:
    return loads_no_duplicate_keys(Path(path).read_text(encoding="utf-8"))


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def vocabulary_sha256(path: str | Path) -> str:
    """Content digest of the vocabulary file bytes (the value pinned in records)."""
    return sha256_hex(Path(path).read_bytes())


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(ch in _HEXDIGITS for ch in value)


def _mapping(value: Any, label: str) -> dict:
    if not isinstance(value, dict):
        raise ReferenceContractError(f"{label} must be an object")
    return value


def _closed(value: Any, keys: set[str], *, label: str) -> dict:
    mapping = _mapping(value, label)
    if set(mapping) != keys:
        missing = sorted(keys - set(mapping))
        extra = sorted(set(mapping) - keys)
        raise ReferenceContractError(f"{label} keys are not the closed set (missing={missing}, unknown={extra})")
    return mapping


def _closed_optional(value: Any, required: set[str], optional: set[str], *, label: str) -> dict:
    mapping = _mapping(value, label)
    keys = set(mapping)
    if not required <= keys:
        raise ReferenceContractError(f"{label} missing required keys {sorted(required - keys)}")
    unknown = keys - required - optional
    if unknown:
        raise ReferenceContractError(f"{label} has unknown keys {sorted(unknown)}")
    return mapping


def _nonempty_str(mapping: dict, key: str, *, label: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ReferenceContractError(f"{label}.{key} must be a nonempty string")
    return value


def _sha(mapping: dict, key: str, *, label: str) -> str:
    value = mapping.get(key)
    if not _is_sha256(value):
        raise ReferenceContractError(f"{label}.{key} must be a 64-char lowercase sha256 hex")
    return value


def _list(mapping: dict, key: str, *, label: str, allow_empty: bool = True) -> list:
    value = mapping.get(key)
    if not isinstance(value, list) or (not allow_empty and not value):
        raise ReferenceContractError(f"{label}.{key} must be a{'' if allow_empty else ' nonempty'} list")
    return value


def _bool(mapping: dict, key: str, *, label: str) -> bool:
    value = mapping.get(key)
    if not isinstance(value, bool):
        raise ReferenceContractError(f"{label}.{key} must be a boolean")
    return value


def _unique_nonempty_str_list(value: Any, *, label: str) -> list[str]:
    if not isinstance(value, list) or not value \
            or len(value) != len(set(value)) \
            or not all(isinstance(item, str) and item for item in value):
        raise ReferenceContractError(f"{label} must be a unique nonempty string list")
    return value


# --------------------------------------------------------------------------- vocabulary (R2 anchor)
def validate_reference_aspect_vocabulary(doc: Any) -> dict:
    """Validate contracts/reference_aspects.json — the closed 31-id vocabulary."""
    top = _closed(doc, {"contract_id", "schema_version", "vocabulary_version", "aspects",
                        "subaspect_variants", "states"}, label="ReferenceAspectVocabulary")
    if top["contract_id"] != "ReferenceAspectVocabulary":
        raise ReferenceContractError("contract_id must be ReferenceAspectVocabulary")
    if top["schema_version"] != 1 or top["vocabulary_version"] != 1:
        raise ReferenceContractError("vocabulary schema_version/vocabulary_version must be 1")

    aspects = _list(top, "aspects", label="vocabulary", allow_empty=False)
    ids: list[str] = []
    kinds: dict[str, str] = {}
    for index, aspect in enumerate(aspects):
        row = _closed(aspect, {"id", "kind", "subaspects", "applies_to"}, label=f"aspect[{index}]")
        aid = row["id"]
        if not isinstance(aid, str) or not aid or aid in kinds:
            raise ReferenceContractError(f"aspect id duplicate/empty: {aid!r}")
        kind = row["kind"]
        if kind not in ASPECT_KINDS:
            raise ReferenceContractError(f"{aid}: kind must be one of {sorted(ASPECT_KINDS)}")
        if row["applies_to"] not in APPLIES_TO:
            raise ReferenceContractError(f"{aid}: applies_to must be one of {sorted(APPLIES_TO)}")
        sub = row["subaspects"]
        if not isinstance(sub, list):
            raise ReferenceContractError(f"{aid}: subaspects must be a list")
        if kind == "component":
            expected = COMPONENT_SUBASPECTS.get(aid)
            if expected is None or tuple(sub) != expected:
                raise ReferenceContractError(f"{aid}: component subaspects must be exactly {expected}")
        elif sub:
            raise ReferenceContractError(f"{aid}: non-component aspects carry no subaspects")
        ids.append(aid)
        kinds[aid] = kind

    if tuple(a for a in ids if kinds[a] == "page") != PAGE_ASPECTS:
        raise ReferenceContractError("page.* aspects are not the closed set of 10")
    if tuple(a for a in ids if kinds[a] == "visual") != VISUAL_ASPECTS:
        raise ReferenceContractError("visual.* aspects are not the closed set of 10")
    if frozenset(a for a in ids if kinds[a] == "component") != frozenset(COMPONENT_SUBASPECTS):
        raise ReferenceContractError("component.* aspects are not the closed set of 11")
    if len(ids) != 31:
        raise ReferenceContractError(f"vocabulary must carry exactly 31 aspect ids, got {len(ids)}")

    variants = _mapping(top["subaspect_variants"], "subaspect_variants")
    if set(variants) != {"component.table"}:
        raise ReferenceContractError("subaspect_variants must cover exactly component.table")
    if variants["component.table"] != {"anatomy": list(TABLE_ANATOMY_VARIANTS)}:
        raise ReferenceContractError("component.table anatomy variants must be data-table|structured-list")

    states = _closed(top["states"], {"ids", "profile_state_map", "visibility_phases"}, label="states")
    if list(states["ids"]) != list(CANONICAL_STATES):
        raise ReferenceContractError(f"states.ids must be exactly {list(CANONICAL_STATES)}")
    if states["profile_state_map"] != PROFILE_STATE_MAP:
        raise ReferenceContractError("states.profile_state_map drift")
    if list(states["visibility_phases"]) != list(VISIBILITY_PHASES):
        raise ReferenceContractError(f"states.visibility_phases must be {list(VISIBILITY_PHASES)}")
    return top


def vocabulary_aspect_ids(doc: Any) -> frozenset[str]:
    validate_reference_aspect_vocabulary(doc)
    return frozenset(aspect["id"] for aspect in doc["aspects"])


def _allowed_state_tokens(vocabulary: dict) -> frozenset[str]:
    states = vocabulary["states"]
    return frozenset(states["ids"]) | frozenset(states["profile_state_map"])


def _require_aspect(aspect_id: Any, ids: frozenset[str], *, label: str) -> str:
    if not isinstance(aspect_id, str) or aspect_id not in ids:
        raise ReferenceContractError(f"{label}: aspect id {aspect_id!r} is not in the closed vocabulary")
    return aspect_id


def _pack_not_rejected(pack_id: str, pack_states: dict | None, *, label: str) -> None:
    if pack_states and pack_states.get(pack_id) == REJECTED_EVIDENCE:
        raise ReferenceContractError(f"{label}: cites rejected-evidence pack {pack_id!r}")


# --------------------------------------------------------------------------- rights (R4)
def _validate_rights_row(row: Any, *, label: str) -> None:
    r = _closed(row, {"resource", "publication", "custody_id", "redistribution", "retention"}, label=label)
    _nonempty_str(r, "resource", label=label)
    if r["publication"] not in PUBLICATION:
        raise ReferenceContractError(f"{label}.publication must be one of {sorted(PUBLICATION)}")
    _nonempty_str(r, "custody_id", label=label)
    if r["redistribution"] not in REDISTRIBUTION:
        raise ReferenceContractError(f"{label}.redistribution must be one of {sorted(REDISTRIBUTION)}")
    _validate_retention(r["retention"], label=f"{label}.retention")


def _validate_retention(value: Any, *, label: str) -> None:
    retention = _closed_optional(value, {"policy"}, {"expires_utc"}, label=label)
    if retention["policy"] not in RETENTION_POLICIES:
        raise ReferenceContractError(f"{label}.policy must be one of {sorted(RETENTION_POLICIES)}")
    if retention["policy"] == "dated-expiry":
        _nonempty_str(retention, "expires_utc", label=label)
    elif "expires_utc" in retention:
        raise ReferenceContractError(f"{label}: expires_utc only valid with dated-expiry")


# --------------------------------------------------------------------------- occurrence key (R3)
def _validate_occurrence_key(value: Any, *, vocabulary: dict, ids: frozenset[str],
                             vocabulary_sha256: str | None, label: str) -> None:
    key = _closed(value, set(OCCURRENCE_KEY_FIELDS), label=label)
    _require_aspect(key["aspect_id"], ids, label=label)
    if key["vocabulary_version"] != vocabulary["vocabulary_version"]:
        raise ReferenceContractError(f"{label}: vocabulary_version mismatch")
    if not _is_sha256(key["vocabulary_sha256"]):
        raise ReferenceContractError(f"{label}: vocabulary_sha256 must be a sha256 hex")
    if vocabulary_sha256 is not None and key["vocabulary_sha256"] != vocabulary_sha256:
        raise ReferenceContractError(f"{label}: vocabulary_sha256 does not pin this vocabulary")
    if key["state"] not in _allowed_state_tokens(vocabulary):
        raise ReferenceContractError(f"{label}: state {key['state']!r} outside the closed state set")
    if not isinstance(key["occurrence_index"], int) or isinstance(key["occurrence_index"], bool) \
            or key["occurrence_index"] < 0:
        raise ReferenceContractError(f"{label}: occurrence_index must be a non-negative int")
    for field in ("target_repo_or_url", "target_revision", "route", "profile_or_context",
                  "region", "subject_selector"):
        _nonempty_str(key, field, label=label)
    if not (isinstance(key["viewport"], int) and not isinstance(key["viewport"], bool)) \
            and not (isinstance(key["viewport"], str) and key["viewport"]):
        raise ReferenceContractError(f"{label}: viewport must be an int or nonempty string")


# --------------------------------------------------------------------------- candidate (R4, R5 evidence-only)
def validate_reference_candidate_record(record: Any, *, vocabulary: dict) -> dict:
    ids = vocabulary_aspect_ids(vocabulary)
    rec = _closed(record, {
        "contract_id", "schema_version", "candidate_id", "origin", "producer", "source",
        "rights", "capture", "observable_anatomy", "uncovered_aspects_claimed", "status",
        "record_sha256",
    }, label="ReferenceCandidateRecord")
    if rec["contract_id"] != "ReferenceCandidateRecord":
        raise ReferenceContractError("contract_id must be ReferenceCandidateRecord")
    if rec["schema_version"] != 1:
        raise ReferenceContractError("candidate schema_version must be 1")
    _nonempty_str(rec, "candidate_id", label="candidate")
    _nonempty_str(rec, "origin", label="candidate")
    if rec["status"] not in LIFECYCLE_STATES:
        raise ReferenceContractError(f"candidate.status must be a lifecycle state, got {rec['status']!r}")
    _sha(rec, "record_sha256", label="candidate")

    producer = _closed(rec["producer"], {"principal_id", "tool", "version", "command", "run_id"}, label="candidate.producer")
    for field in ("principal_id", "tool", "version", "command", "run_id"):
        _nonempty_str(producer, field, label="candidate.producer")

    source = _closed(rec["source"], {"url_or_path", "fetched_utc", "robots"}, label="candidate.source")
    _nonempty_str(source, "url_or_path", label="candidate.source")
    _nonempty_str(source, "fetched_utc", label="candidate.source")
    robots = _closed_optional(source["robots"], {"checked", "allowed"}, {"override_reason"}, label="candidate.source.robots")
    _bool(robots, "checked", label="candidate.source.robots")
    _bool(robots, "allowed", label="candidate.source.robots")
    if "override_reason" in robots:
        _nonempty_str(robots, "override_reason", label="candidate.source.robots")

    rights = _list(rec, "rights", label="candidate", allow_empty=False)
    for index, row in enumerate(rights):
        _validate_rights_row(row, label=f"candidate.rights[{index}]")

    capture = _closed(rec["capture"], {"live_evidence", "staging_tree_sha256", "gaps"}, label="candidate.capture")
    _list(capture, "live_evidence", label="candidate.capture")
    _sha(capture, "staging_tree_sha256", label="candidate.capture")
    _list(capture, "gaps", label="candidate.capture")

    anatomy = _mapping(rec["observable_anatomy"], "candidate.observable_anatomy")
    if anatomy.get("authority_status") != "evidence-only":
        raise ReferenceContractError("candidate.observable_anatomy must be authority_status=evidence-only")
    smuggled = _MEASUREMENT_FIELDS & set(anatomy)
    if smuggled:
        raise ReferenceContractError(
            f"evidence-only candidate cannot carry a measurement (fields {sorted(smuggled)})")

    claimed = _list(rec, "uncovered_aspects_claimed", label="candidate")
    for aspect_id in claimed:
        _require_aspect(aspect_id, ids, label="candidate.uncovered_aspects_claimed")
    return rec


# --------------------------------------------------------------------------- approval (R1, R2, R3, R5)
def assert_producer_approver_independent(candidate: dict, approval: dict, *, principals: dict | None = None) -> None:
    """R1: the approving principal differs from the producing principal (and is an operator)."""
    producer_id = _mapping(candidate.get("producer"), "candidate.producer").get("principal_id")
    approver_id = approval.get("approver_principal_id")
    if not isinstance(approver_id, str) or not approver_id:
        raise ReferenceContractError("approval.approver_principal_id must be a nonempty string")
    if producer_id == approver_id:
        raise ReferenceContractError("producer principal must differ from approver principal (R1)")
    if principals is not None:
        row = principals.get(approver_id)
        if not isinstance(row, dict) or row.get("kind") != "operator":
            raise ReferenceContractError("approver principal must have kind=operator (R1)")


def validate_reference_aspect_approval(record: Any, *, vocabulary: dict, candidate: dict | None = None,
                                       principals: dict | None = None,
                                       vocabulary_sha256: str | None = None) -> dict:
    ids = vocabulary_aspect_ids(vocabulary)
    rec = _closed(record, {
        "contract_id", "schema_version", "pack_id", "candidate_id", "candidate_sha256",
        "rows", "approver_principal_id", "approved_utc", "transitions",
    }, label="ReferenceAspectApproval")
    if rec["contract_id"] != "ReferenceAspectApproval":
        raise ReferenceContractError("contract_id must be ReferenceAspectApproval")
    if rec["schema_version"] != 1:
        raise ReferenceContractError("approval schema_version must be 1")
    _nonempty_str(rec, "pack_id", label="approval")
    _nonempty_str(rec, "candidate_id", label="approval")
    _nonempty_str(rec, "approved_utc", label="approval")
    approver_id = _nonempty_str(rec, "approver_principal_id", label="approval")
    # R5: approval binds the candidate staged-byte hash BEFORE measurement.
    _sha(rec, "candidate_sha256", label="approval")

    # R1: operator approver + independence when the peer records are supplied.
    if principals is not None:
        row = principals.get(approver_id)
        if not isinstance(row, dict) or row.get("kind") != "operator":
            raise ReferenceContractError("approver principal must have kind=operator (R1)")
    if candidate is not None:
        assert_producer_approver_independent(candidate, rec, principals=principals)
        if rec["candidate_id"] != candidate.get("candidate_id"):
            raise ReferenceContractError("approval.candidate_id does not match the candidate")
        if rec["candidate_sha256"] != candidate.get("record_sha256"):
            raise ReferenceContractError("approval.candidate_sha256 does not bind the candidate hash (R5)")

    rows = _list(rec, "rows", label="approval", allow_empty=False)
    for index, row in enumerate(rows):
        label = f"approval.rows[{index}]"
        r = _closed(row, {"aspect_id", "decision", "subjects", "states", "viewports",
                          "target_scope", "rights_ack"}, label=label)
        _require_aspect(r["aspect_id"], ids, label=label)
        if r["decision"] not in APPROVAL_DECISIONS:
            raise ReferenceContractError(f"{label}.decision must be one of {sorted(APPROVAL_DECISIONS)}")
        subjects = _list(r, "subjects", label=label, allow_empty=False)
        for sindex, subject in enumerate(subjects):
            s = _closed(subject, {"subject_id", "selector"}, label=f"{label}.subjects[{sindex}]")
            _nonempty_str(s, "subject_id", label=f"{label}.subjects[{sindex}]")
            _nonempty_str(s, "selector", label=f"{label}.subjects[{sindex}]")
        for state in _list(r, "states", label=label, allow_empty=False):
            if state not in _allowed_state_tokens(vocabulary):
                raise ReferenceContractError(f"{label}.states: {state!r} outside the closed state set")
        _list(r, "viewports", label=label, allow_empty=False)
        _nonempty_str(r, "rights_ack", label=label)
        _validate_occurrence_key(r["target_scope"], vocabulary=vocabulary, ids=ids,
                                 vocabulary_sha256=vocabulary_sha256, label=f"{label}.target_scope")
        if r["target_scope"]["aspect_id"] != r["aspect_id"]:
            raise ReferenceContractError(f"{label}: target_scope aspect_id must match the row aspect_id")

    for index, transition in enumerate(_list(rec, "transitions", label="approval")):
        t = _closed(transition, {"aspect_id", "from", "to", "principal_id", "date", "reason"},
                    label=f"approval.transitions[{index}]")
        _require_aspect(t["aspect_id"], ids, label=f"approval.transitions[{index}]")
        for state in (t["from"], t["to"]):
            if state not in LIFECYCLE_STATES:
                raise ReferenceContractError(f"approval.transitions[{index}]: {state!r} is not a lifecycle state")
        for field in ("principal_id", "date", "reason"):
            _nonempty_str(t, field, label=f"approval.transitions[{index}]")
    return rec


# --------------------------------------------------------------------------- external pack (R6)
def validate_external_reference_pack(record: Any, *, vocabulary: dict, pack_states: dict | None = None) -> dict:
    ids = vocabulary_aspect_ids(vocabulary)
    required = {
        "contract_id", "schema_version", "pack_id", "pack_version", "frozen_source", "matrix",
        "aspect_ownership", "official_precedence_exclusions", "capture_gaps", "captures",
        "retention", "custody_id", "revalidation",
    }
    optional = {"replaces", "replaces_manifest_sha256", "legacy_adapter"}
    rec = _closed_optional(record, required, optional, label="ExternalReferencePack")
    if rec["contract_id"] != "ExternalReferencePack":
        raise ReferenceContractError("contract_id must be ExternalReferencePack")
    if rec["schema_version"] != 1:
        raise ReferenceContractError("pack schema_version must be 1")
    _nonempty_str(rec, "pack_id", label="pack")
    _nonempty_str(rec, "custody_id", label="pack")
    if not isinstance(rec["pack_version"], int) or isinstance(rec["pack_version"], bool) or rec["pack_version"] < 1:
        raise ReferenceContractError("pack_version must be a positive integer (R6)")

    # R6: replaces + replaces_manifest_sha256 appear TOGETHER or not at all.
    has_replaces = "replaces" in rec
    has_pin = "replaces_manifest_sha256" in rec
    if has_replaces != has_pin:
        raise ReferenceContractError("replaces and replaces_manifest_sha256 must appear together (R6)")
    if has_replaces:
        replaced = _nonempty_str(rec, "replaces", label="pack")
        _sha(rec, "replaces_manifest_sha256", label="pack")
        _pack_not_rejected(replaced, pack_states, label="pack.replaces")

    # R6: legacy_adapter permitted ONLY for the one closed legacy id.
    if "legacy_adapter" in rec:
        if rec.get("replaces") != LEGACY_PACK_ID:
            raise ReferenceContractError(f"legacy_adapter only permitted when replaces == {LEGACY_PACK_ID!r} (R6)")
        adapter = _closed(rec["legacy_adapter"],
                          {"legacy_predecessor", "legacy_predecessor_manifest_sha256", "treated_as"},
                          label="pack.legacy_adapter")
        if adapter["legacy_predecessor"] != LEGACY_PACK_ID:
            raise ReferenceContractError("legacy_adapter.legacy_predecessor must be dashboard-pre-w3")
        if adapter["legacy_predecessor_manifest_sha256"] != LEGACY_PACK_MANIFEST_SHA256:
            raise ReferenceContractError("legacy_adapter predecessor digest does not match the pinned legacy manifest")
        treated = _closed(adapter["treated_as"], {"pack_version", "state"}, label="pack.legacy_adapter.treated_as")
        if treated["pack_version"] != 1 or treated["state"] != "promoted":
            raise ReferenceContractError("legacy_adapter.treated_as must be {pack_version:1, state:'promoted'}")

    frozen = _closed(rec["frozen_source"],
                     {"artifact", "tree_sha256", "script_policy", "dom_excisions", "entry", "entry_sha256"},
                     label="pack.frozen_source")
    _nonempty_str(frozen, "artifact", label="pack.frozen_source")
    _nonempty_str(frozen, "script_policy", label="pack.frozen_source")
    _nonempty_str(frozen, "entry", label="pack.frozen_source")
    _sha(frozen, "tree_sha256", label="pack.frozen_source")
    _sha(frozen, "entry_sha256", label="pack.frozen_source")
    _list(frozen, "dom_excisions", label="pack.frozen_source")

    matrix = _closed(rec["matrix"], {"viewports", "states"}, label="pack.matrix")
    _list(matrix, "viewports", label="pack.matrix", allow_empty=False)
    _list(matrix, "states", label="pack.matrix", allow_empty=False)

    ownership = _mapping(rec["aspect_ownership"], "pack.aspect_ownership")
    if not ownership:
        raise ReferenceContractError("pack.aspect_ownership must be non-empty")
    for aspect_id, scope in ownership.items():
        _require_aspect(aspect_id, ids, label="pack.aspect_ownership")
        if not scope:
            raise ReferenceContractError(f"pack.aspect_ownership[{aspect_id}] occurrence_scope is empty")

    _list(rec, "official_precedence_exclusions", label="pack")
    _list(rec, "capture_gaps", label="pack")
    captures = _list(rec, "captures", label="pack", allow_empty=False)
    for index, capture in enumerate(captures):
        label = f"pack.captures[{index}]"
        cap = _closed(capture, {"viewport", "state", "screenshot", "facts", "provenance"}, label=label)
        if cap["state"] not in _allowed_state_tokens(vocabulary):
            raise ReferenceContractError(f"{label}.state {cap['state']!r} outside the closed state set")
        for artifact in ("screenshot", "facts", "provenance"):
            art = _closed(cap[artifact], {"path", "sha256"}, label=f"{label}.{artifact}")
            _nonempty_str(art, "path", label=f"{label}.{artifact}")
            _sha(art, "sha256", label=f"{label}.{artifact}")

    _validate_retention(rec["retention"], label="pack.retention")

    reval = _closed(rec["revalidation"],
                    {"pack_manifest_sha256", "catalog_file_sha256s", "baseline_clause_digests", "vocabulary_sha256"},
                    label="pack.revalidation")
    _sha(reval, "pack_manifest_sha256", label="pack.revalidation")
    _sha(reval, "vocabulary_sha256", label="pack.revalidation")
    _list(reval, "catalog_file_sha256s", label="pack.revalidation")
    _list(reval, "baseline_clause_digests", label="pack.revalidation")
    return rec


# --------------------------------------------------------------------------- measurement run
def validate_measurement_run(record: Any, *, vocabulary: dict, pack_states: dict | None = None) -> dict:
    ids = vocabulary_aspect_ids(vocabulary)
    rec = _closed(record, {
        "contract_id", "schema_version", "pack_id", "session_id", "measured_aspects",
        "producer_principal_id", "chrome_version", "command", "run_sha256",
    }, label="MeasurementRun")
    if rec["contract_id"] != "MeasurementRun":
        raise ReferenceContractError("contract_id must be MeasurementRun")
    if rec["schema_version"] != 1:
        raise ReferenceContractError("measurement schema_version must be 1")
    pack_id = _nonempty_str(rec, "pack_id", label="measurement")
    for field in ("session_id", "producer_principal_id", "chrome_version", "command"):
        _nonempty_str(rec, field, label="measurement")
    _sha(rec, "run_sha256", label="measurement")
    measured = _list(rec, "measured_aspects", label="measurement", allow_empty=False)
    for aspect_id in measured:
        _require_aspect(aspect_id, ids, label="measurement.measured_aspects")
    _pack_not_rejected(pack_id, pack_states, label="measurement.pack_id")
    return rec


# --------------------------------------------------------------------------- promoted clauses (R7)
def validate_promoted_reference_clauses(clauses: Any, *, approved_aspects: set[str] | None = None) -> list[dict]:
    """Promoted references.json clause rows keep EXACTLY the 7-key catalog shape with
    authority pinned to approved-reference. R7: file-driven promotion — every clause's
    aspect must be in the approved set when one is supplied."""
    if not isinstance(clauses, list) or not clauses:
        raise ReferenceContractError("promoted reference clauses must be a nonempty list")
    seen: set[str] = set()
    for clause in clauses:
        row = _closed(clause, {"clause_id", "claim", "authority", "source_mode", "exactness", "sources", "scope"},
                      label="promoted-clause")
        clause_id = row["clause_id"]
        if not isinstance(clause_id, str) or not clause_id or clause_id in seen:
            raise ReferenceContractError(f"duplicate or empty promoted clause_id: {clause_id!r}")
        seen.add(clause_id)
        if row["authority"] != PROMOTED_AUTHORITY:
            raise ReferenceContractError(f"{clause_id}: promoted clause authority must be {PROMOTED_AUTHORITY!r}")
        if (row["source_mode"], row["exactness"]) != PROMOTED_AUTHORITY_TUPLE:
            raise ReferenceContractError(f"{clause_id}: incoherent authority tuple for approved-reference")
        _nonempty_str(row, "claim", label=clause_id)
        sources = _list(row, "sources", label=clause_id, allow_empty=False)
        for source in sources:
            s = _closed(source, {"source_kind", "ref"}, label=f"{clause_id}/source")
            if s["source_kind"] != PROMOTED_SOURCE_KIND:
                raise ReferenceContractError(f"{clause_id}: promoted source_kind must be {PROMOTED_SOURCE_KIND!r}")
            ref = s["ref"]
            if not isinstance(ref, str) or not ref.startswith(PROMOTED_SOURCE_REF_PREFIX):
                raise ReferenceContractError(f"{clause_id}: source ref must cite a reference pack manifest")
        scope = _closed(row["scope"], {"profiles", "aspects", "invariant_ids"}, label=f"{clause_id}/scope")
        for key in ("profiles", "aspects", "invariant_ids"):
            _unique_nonempty_str_list(scope[key], label=f"{clause_id}/scope/{key}")
        if approved_aspects is not None:
            unapproved = [a for a in scope["aspects"] if a not in approved_aspects]
            if unapproved:
                raise ReferenceContractError(
                    f"{clause_id}: promotes unapproved aspect(s) {unapproved} (R7 file-driven promotion)")
    return list(clauses)


# --------------------------------------------------------------------------- bindings (R8 inverse/phantom)
def validate_reference_bindings(doc: Any, *, promoted_clause_ids: set[str] | None = None,
                                pack_states: dict | None = None) -> dict:
    rec = _closed(doc, {"contract_id", "schema_version", "bindings"}, label="ReferenceClauseBindings")
    if rec["contract_id"] != "ReferenceClauseBindings":
        raise ReferenceContractError("contract_id must be ReferenceClauseBindings")
    if rec["schema_version"] != 1:
        raise ReferenceContractError("bindings schema_version must be 1")
    bindings = _list(rec, "bindings", label="bindings", allow_empty=False)
    clause_ids: list[str] = []
    for index, binding in enumerate(bindings):
        label = f"bindings[{index}]"
        b = _closed(binding, {"clause_id", "pack_id", "pack_manifest_sha256", "occurrence_scope", "fact_bindings"},
                    label=label)
        clause_id = _nonempty_str(b, "clause_id", label=label)
        pack_id = _nonempty_str(b, "pack_id", label=label)
        _sha(b, "pack_manifest_sha256", label=label)
        if not b["occurrence_scope"]:
            raise ReferenceContractError(f"{label}.occurrence_scope is empty")
        for findex, fact in enumerate(_list(b, "fact_bindings", label=label, allow_empty=False)):
            f = _closed(fact, {"fact_id", "field", "expected"}, label=f"{label}.fact_bindings[{findex}]")
            _nonempty_str(f, "fact_id", label=f"{label}.fact_bindings[{findex}]")
            _nonempty_str(f, "field", label=f"{label}.fact_bindings[{findex}]")
        _pack_not_rejected(pack_id, pack_states, label=f"{label}.pack_id")
        clause_ids.append(clause_id)

    if len(clause_ids) != len(set(clause_ids)):
        raise ReferenceContractError("bindings: duplicate clause_id (each promoted clause binds exactly once)")
    # R8: inverse + phantom parity against the promoted clause set.
    if promoted_clause_ids is not None:
        bound = set(clause_ids)
        phantom = bound - promoted_clause_ids
        unbound = promoted_clause_ids - bound
        if phantom:
            raise ReferenceContractError(f"bindings: phantom binding for non-promoted clause(s) {sorted(phantom)} (R8)")
        if unbound:
            raise ReferenceContractError(f"bindings: promoted clause(s) with no binding {sorted(unbound)} (R8)")
    return rec


# --------------------------------------------------------------------------- consumer override
def validate_reference_override_record(record: Any, *, vocabulary: dict) -> dict:
    ids = vocabulary_aspect_ids(vocabulary)
    rec = _closed(record, {"contract_id", "schema_version", "pack_id", "overrides"},
                  label="ReferenceOverrideRecord")
    if rec["contract_id"] != "ReferenceOverrideRecord":
        raise ReferenceContractError("contract_id must be ReferenceOverrideRecord")
    if rec["schema_version"] != 1:
        raise ReferenceContractError("override schema_version must be 1")
    _nonempty_str(rec, "pack_id", label="override")
    overrides = _list(rec, "overrides", label="override", allow_empty=False)
    for index, row in enumerate(overrides):
        label = f"override.overrides[{index}]"
        o = _closed(row, {"aspect_id", "measured_value", "owner_value", "mode_d_clause_id", "forked_from_measured"},
                    label=label)
        _require_aspect(o["aspect_id"], ids, label=label)
        _nonempty_str(o, "mode_d_clause_id", label=label)
        if "measured_value" not in o or "owner_value" not in o:
            raise ReferenceContractError(f"{label} must name both measured_value and owner_value")
        if o["forked_from_measured"] is not True:
            raise ReferenceContractError(f"{label}.forked_from_measured must be exactly true")
    return rec

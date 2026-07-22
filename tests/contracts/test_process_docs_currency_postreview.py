"""Post-review executable RED — terminal CODE + ADVERSARIAL findings become law.

Authored by the fresh exact `claude-fable-5` delegated executable-RED author lane
(`fable-process-currentness-postreview-r1`). `/root` conducts; a DIFFERENT fresh
Opus lane builds GREEN; the author never approves. Pinned base
`74fe3ecda8a7bbaba62677df8786937dc88e6265`; overlaid predecessor patch sha256
`13640c3c4b5d40cc149e8a7aefd218f85590d578f8bd9794396a3f63e3755e5b`.

This module compiles the ten stable findings of
`scratchpad/active/process/process-doc-currentness-code-review-r1.md` and
`scratchpad/active/process/process-doc-currentness-adversarial-review-r1.md`
into executable evidence: PDC-ADV-001..004, PROC-CODE-CURRENCY-COVER-001,
PROC-CODE-REVIEWER-IDENTITY-001, PROC-CODE-SUCCESSOR-IDENTITY-001,
PROC-CODE-TRANSITION-PAYLOAD-001, PROC-CODE-CONTRACT-HOMING-001,
PROC-CODE-SKILL-CURRENTNESS-001.

Every failure message begins with the stable fingerprint
`PROCESS-DOC-CURRENTNESS-POSTREVIEW-RED:` and names the exact missing
enforcement. The frozen predecessor `tests/contracts/test_process_docs_currency.py`
is imported for pure helpers/anchors only and stays GREEN and unedited; this
module never weakens it. GREEN's seam is policy-as-DATA plus live-document
correction: extend `contracts/process_docs_currency_policy.toml` with the
authority-derived census rows (`[[currency.postreview_documents]]`), the
parenthesized-conductor and per-slice-SOP-delegation patterns, the closed
`[separation.record_schema]` and `[successor.dispatch_schema]` payload schemas,
declare `toml_allowlist` in `contracts/repo_layout.json:structural_layout.
contracts_layout`, and correct the live stale sentences — never by editing or
loosening the sealed predecessor surfaces, which this module re-pins.
"""
from __future__ import annotations

import copy
import json
import re
import unittest
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11 (local): pinned backport, same law as predecessor
    import tomli as tomllib

from tests.contracts.test_process_docs_currency import (
    AGENTS_POINTER,
    CLASSES,
    GOVERNED_DOCS,
    HISTORICAL_RECORD_IDS,
    LEDGER_PATH,
    OPERATOR_LAW,
    PROC_EVIDENCE_CASES,
    R2_REVIEW,
    RED_CLASS_PREFIX,
    REQUIRED_TRANSITIONS,
    ROOT,
    SEATS,
    SKILL_DOCS,
    SKILL_LIFECYCLE_PATTERNS,
    STALE_CONDUCTOR_PATTERNS,
    check_separation,
    check_successor,
    scan_document,
)

FINGERPRINT = "PROCESS-DOC-CURRENTNESS-POSTREVIEW-RED:"

CURRENCY_POLICY_PATH = ROOT / "contracts" / "process_docs_currency_policy.toml"
AUTHORITY_POLICY_PATH = ROOT / "contracts" / "doc_authority_policy.toml"
REPO_LAYOUT_PATH = ROOT / "contracts" / "repo_layout.json"
SKILL_DIR = "skills/design-language-tdd"

# --- demanded enforcement DATA (the exact GREEN target; zero builder choices) --------

# PDC-ADV-001: the stale-pattern matcher must also kill the parenthesized form.
PAREN_CONDUCTOR_PATTERN = r"(?i)\bfable(?:\s+5)?\s*\(\s*the\s+conductor\s*\)"

# PDC-ADV-004 / PROC-CODE-SKILL-CURRENTNESS-001: lifecycle delegation to SKILL.md
# (any case/spacing/parenthesized variant) dies; domain-method prose and the
# `AGENTS.md` pointer survive.
PERSLICE_SOP_PATTERN = r"(?i)\bper[\s-]*slice\s+sop\b[^\n]{0,120}\bskill\.md\b"

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

EXPECTED_CONTRACT_TOMLS = [
    "doc_authority_policy.toml",
    "process_docs_currency_policy.toml",
]

# Sealed unrelated layout rules that GREEN may not loosen while homing the TOMLs.
SEALED_CONTRACTS_JSON_GLOB = "**/*.json"
SEALED_CONTRACTS_ROOT_ALLOWLIST = [
    "repo_layout.json", "page_manifest.json", "dom_cover.json",
    "dashboard_surface.json", "rendered_fact_policy.json",
    "correction_baseline.json", "reference_aspects.json",
]
SEALED_CONTRACTS_GROUP_DIRS = ["design_profiles", "official_sources", "reference_packs"]

# The two live handoffs the seven-document roster excluded (PDC-ADV-001 /
# PROC-CODE-CURRENCY-COVER-001), with their doc-authority classes as currency roles.
HANDOFF_ROLE = {
    "docs/plans/handoff/w3-visual-regression-correction.md": "gate_record",
    "docs/plans/handoff/w3c-0-design-closure.md": "design_record",
}

# Exact live stale sentences (attack-replay canaries; conserved even after GREEN
# corrects the live files).
STALE_W3V_49 = (
    "(landing with slice 0): Fable (the conductor) orchestrates, "
    "authors the slice designs and REDs,"
)
STALE_W3C0_111 = (
    "never previously committed): Fable (the conductor) orchestrates, "
    "authors designs and REDs,"
)

# Exact SKILL-R1 evidence obligations (verbatim from the terminal transition
# registry, mirrored by the policy rows; the predecessor never bound these —
# PDC-ADV-002 / PROC-CODE-TRANSITION-PAYLOAD-001).
SKILL_EVIDENCE = {
    "SKILL-R1-001": (
        "deterministic framework/lockfile evidence: closed detect_stack framework "
        "signals + exact conflict/precedence law; identical rosters with pytest "
        "config vs unittest imports resolve differently; two package-manager locks "
        "resolve as unresolved/ambiguous, never by preference"
    ),
    "SKILL-R1-002": (
        "right-reason RED identity/fingerprint: red_witness requires expected test "
        "identity + expected failure fingerprint, distinguishes runner/infrastructure "
        "errors; an unrelated ImportError never emits RED-WITNESS; only the intended "
        "assertion does"
    ),
    "SKILL-R1-003": (
        "authorized fixtures + structured forward-test grading: authorized AGENTS "
        "fixture variants (or a specified authority grant) and a structured "
        "event/grader schema for state order, reads, tools, refusals, and mutation "
        "boundaries; unauthorized fixtures emit exactly one role-block event and "
        "zero later tool events"
    ),
    "SKILL-R1-004": (
        "recursive target-shape validator: deterministic shape-contract validator "
        "(or fail-closed absence), git ls-files root census, per-directory "
        "misplacement RED; an undeclared root entry and a misplaced governed file "
        "fail while the exact recursively declared tree passes"
    ),
    "SKILL-R1-005": (
        "generic packet validator or exact pre-BUILD refusal: on a repository "
        "without packet tooling, either a bundled generic validated packet rejects "
        "altered base/design/RED/path hashes, or the skill stops before BUILD with "
        "an exact blocked token"
    ),
    "SKILL-R1-006": (
        "tracked-to-installed sync + generated/validated agents/openai.yaml: "
        "deterministic install-sync (exact hash manifest, no extra files) over temp "
        "roots incl. stale/locally-modified installed copies; quick_validate passes; "
        "agents/openai.yaml generated via the prescribed scripts after reading "
        "references/openai_yaml.md and matching the designed interface values"
    ),
}

ALLOWED_TRANSITION_KEYS = (
    "finding_id", "transition_class", "status", "dependency",
    "source_review", "owner_seat", "evidence",
)

# PDC-ADV-003: the nested tables are closed exactly, both directions. The rosters
# include the two payload schemas and the census extension GREEN must land.
DEMANDED_TABLE_KEYS = {
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
        "prose_review_cap", "terminal_verdicts",
        "identity_preserving_events", "reset_events",
    },
    "transition_classes": {"classes"},
    "currency": {
        "historical_exempt_prefixes", "documents",
        "postreview_documents", "historical_records",
    },
}
TERMINAL_VERDICTS = ["REVISE", "APPROVE"]
FORBIDDEN_AFTER_RED = ["PROSE_REVIEW", "REVIEW_OF_REVIEW"]
IDENTITY_EVENTS = ["CORRECTION", "RENAME", "VERSION_BUMP", "SUCCESSOR_PACKET"]
EXPECTED_FAMILY_IDS = ["semantic-tdd-conductor-skill", "build-lane-contract-system"]
EXPECTED_FAMILY_KEYS = {
    "semantic-tdd-conductor-skill": {
        "family_id", "prose_reviews_used", "terminal_verdict_token",
        "another_prose_review_authorized", "findings", "terminal_review_doc",
    },
    "build-lane-contract-system": {
        "family_id", "prose_reviews_used", "terminal_verdict_token",
        "another_prose_review_authorized",
    },
}

DOC_ROW_BASE_KEYS = {"path", "role", "forbidden_patterns", "required_propositions"}
DOC_ROW_OPTIONAL_KEYS = {
    "adoption_sha256", "historical_exempt",
    "immutable_prefix_sha256", "immutable_prefix_bytes",
}


# --- pure derivations and validators (policy-as-DATA; memory-mutant friendly) --------


def derive_live_process_docs(authority: dict) -> set[str]:
    """Census source: the document-authority policy, never a hard-coded roster."""
    live = {authority["plan_of_record"]["path"]}
    live.update(authority["completeness"]["required_docs"])
    for row in authority.get("doc", []):
        if row.get("status") == "live":
            live.add(row["path"])
    return live


def split_historical(paths: set[str], prefixes: tuple[str, ...]) -> tuple[set[str], set[str]]:
    historical = {p for p in paths if prefixes and p.startswith(prefixes)}
    return paths - historical, historical


def all_currency_rows(policy: dict) -> list[dict]:
    currency = policy["currency"]
    return list(currency.get("documents", [])) + list(
        currency.get("postreview_documents", [])
    )


def demanded_census(authority: dict, policy: dict, skill_docs) -> set[str]:
    prefixes = tuple(policy["currency"].get("historical_exempt_prefixes", []))
    nonhistorical, _ = split_historical(derive_live_process_docs(authority), prefixes)
    return nonhistorical | {"AGENTS.md"} | set(skill_docs)


def census_violations(authority: dict, policy: dict, skill_docs, present: set[str]) -> list[str]:
    """Every tracked nonhistorical live process document is currency-governed;
    duplicates, rogue rows, and vanished declared docs fail closed."""
    prefixes = tuple(policy["currency"].get("historical_exempt_prefixes", []))
    live = derive_live_process_docs(authority)
    _, historical = split_historical(live, prefixes)
    demanded = demanded_census(authority, policy, skill_docs)
    declared = [row.get("path") for row in all_currency_rows(policy)]
    violations = []
    for path in sorted({p for p in declared if declared.count(p) > 1}):
        violations.append(f"duplicate currency declaration: {path}")
    declared_set = set(declared)
    for path in sorted(demanded - declared_set):
        violations.append(f"live process document not currency-governed: {path}")
    for path in sorted(declared_set - demanded - historical):
        violations.append(f"rogue currency document (not a tracked live process doc): {path}")
    for path in sorted(declared_set - present):
        violations.append(f"currency-declared document absent from the tree: {path}")
    return violations


def history_exemption_violations(policy: dict) -> list[str]:
    currency = policy["currency"]
    violations = []
    if "docs/history/" not in currency.get("historical_exempt_prefixes", []):
        violations.append("docs/history/ must stay a historical-exempt prefix")
    for row in all_currency_rows(policy):
        path = row.get("path", "")
        if path.startswith("docs/history/") and row.get("historical_exempt") is not True:
            violations.append(f"{path}: history row must be historical_exempt (never scanned)")
    return violations


def demanded_row_patterns(role: str) -> list[str]:
    patterns = list(STALE_CONDUCTOR_PATTERNS) + [PAREN_CONDUCTOR_PATTERN]
    if role in ("skill", "skill_reference"):
        patterns += list(SKILL_LIFECYCLE_PATTERNS) + [PERSLICE_SOP_PATTERN]
    return patterns


def pattern_coverage_violations(policy: dict) -> list[str]:
    """Every nonhistorical governed row carries the full stale-conductor set
    (incl. the parenthesized form); skill rows also carry the lifecycle-
    delegation set (incl. per-slice-SOP-in-SKILL.md)."""
    prefixes = tuple(policy["currency"].get("historical_exempt_prefixes", []))
    violations = []
    for row in all_currency_rows(policy):
        path = row.get("path", "")
        if row.get("historical_exempt", False) or (prefixes and path.startswith(prefixes)):
            continue
        declared = row.get("forbidden_patterns", [])
        for pattern in demanded_row_patterns(row.get("role", "")):
            if pattern not in declared:
                violations.append(f"{path}: missing forbidden pattern {pattern}")
    return violations


def doc_row_shape_violations(policy: dict) -> list[str]:
    violations = []
    for row in all_currency_rows(policy):
        path = row.get("path", "<missing path>")
        unknown = sorted(set(row) - DOC_ROW_BASE_KEYS - DOC_ROW_OPTIONAL_KEYS)
        if unknown:
            violations.append(f"{path}: unknown document-row keys {unknown}")
        missing = sorted(DOC_ROW_BASE_KEYS - set(row))
        if missing:
            violations.append(f"{path}: missing document-row keys {missing}")
    return violations


def skill_governance_violations(census, policy: dict) -> list[str]:
    """PROC-CODE-SKILL-CURRENTNESS-001: every reachable skill file carries a
    skill-role currency row that requires the AGENTS.md authority pointer."""
    rows = {row.get("path"): row for row in all_currency_rows(policy)}
    violations = []
    for path in census:
        row = rows.get(path)
        if row is None:
            violations.append(f"{path}: reachable skill file not currency-governed")
            continue
        if row.get("role") not in ("skill", "skill_reference"):
            violations.append(f"{path}: skill file must carry a skill role")
        if AGENTS_POINTER not in row.get("required_propositions", []):
            violations.append(f"{path}: row must require the AGENTS.md authority pointer")
    return violations


def demanded_postreview_rows(reference_docs) -> list[dict]:
    rows = [
        {
            "path": path,
            "role": role,
            "forbidden_patterns": demanded_row_patterns(role),
            "required_propositions": [],
        }
        for path, role in HANDOFF_ROLE.items()
    ]
    rows += [
        {
            "path": path,
            "role": "skill_reference",
            "forbidden_patterns": demanded_row_patterns("skill_reference"),
            "required_propositions": [AGENTS_POINTER],
        }
        for path in sorted(reference_docs)
    ]
    return rows


def synthetic_lawful_policy(policy: dict, reference_docs) -> dict:
    """The exact demanded GREEN policy state, built from the real policy — used
    to prove the RED is satisfiable and to host memory mutants."""
    lawful = copy.deepcopy(policy)
    for row in lawful["currency"]["documents"]:
        if row.get("historical_exempt", False):
            continue
        declared = row.setdefault("forbidden_patterns", [])
        for pattern in demanded_row_patterns(row.get("role", "")):
            if pattern not in declared:
                declared.append(pattern)
    lawful["currency"]["postreview_documents"] = demanded_postreview_rows(reference_docs)
    lawful["separation"]["record_schema"] = copy.deepcopy(DEMANDED_RECORD_SCHEMA)
    lawful["successor"]["dispatch_schema"] = copy.deepcopy(DEMANDED_DISPATCH_SCHEMA)
    return lawful


def postreview_scan(policy: dict, rel_path: str, text: str) -> list[str]:
    """scan_document semantics over the sealed + postreview roster union."""
    currency = policy["currency"]
    rows: dict[str, dict] = {}
    for row in all_currency_rows(policy):
        rows.setdefault(row.get("path", ""), row)
    row = rows.get(rel_path)
    if row is None:
        return [f"undeclared document: {rel_path}"]
    prefixes = tuple(currency.get("historical_exempt_prefixes", []))
    if row.get("historical_exempt", False) or (prefixes and rel_path.startswith(prefixes)):
        return []
    violations = []
    for pattern in row.get("forbidden_patterns", []):
        if re.search(pattern, text):
            violations.append(f"{rel_path}: forbidden pattern matched: {pattern}")
    for proposition in row.get("required_propositions", []):
        if proposition not in text:
            violations.append(f"{rel_path}: required proposition absent: {proposition!r}")
    return violations


def closed_separation_check(record: dict, schema: dict, roles: dict) -> list[str]:
    """PROC-CODE-REVIEWER-IDENTITY-001: closed identity payload; the reviewer
    seat is bound; author/builder seats never approve, across any sessions."""
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
    if record["reviewer_session"] == record["red_author_session"]:
        violations.append("the reviewer session must be distinct from the RED author session")
    if record["reviewer_session"] == record["green_builder_session"]:
        violations.append("the reviewer session must be distinct from the GREEN builder session")
    if record["green_builder_session"] == record["red_author_session"]:
        violations.append("the RED author may not build GREEN")
    return violations


def closed_dispatch_check(payload: dict, schema: dict, successor: dict) -> list[str]:
    """PROC-CODE-SUCCESSOR-IDENTITY-001: the GREEN_DISPATCH payload is a closed
    schema; missing/empty/unknown fields fail closed before seat semantics."""
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
    if payload["builder_seat"] != successor["green_builder"]:
        violations.append("the GREEN successor must be the Opus builder seat")
    if payload["builder_session"] == payload["red_author_session"]:
        violations.append("the GREEN successor session must be distinct from the RED author session")
    return violations


def expected_transition_rows() -> dict[str, dict]:
    rows = {}
    for finding_id, (cls, status, dependency) in REQUIRED_TRANSITIONS.items():
        skill = finding_id.startswith("SKILL-R1-")
        rows[finding_id] = {
            "finding_id": finding_id,
            "transition_class": cls,
            "status": status,
            "dependency": dependency,
            "source_review": R2_REVIEW if skill else OPERATOR_LAW,
            "owner_seat": SEATS["design_red_author"],
            "evidence": SKILL_EVIDENCE[finding_id] if skill
            else RED_CLASS_PREFIX + PROC_EVIDENCE_CASES[finding_id],
        }
    return rows


def transition_rows_violations(rows: list[dict]) -> list[str]:
    """PROC-CODE-TRANSITION-PAYLOAD-001 / PDC-ADV-002: all twelve rows bound
    field-by-field, exact allowed keys, no duplicates/omissions/closure keys."""
    expected = expected_transition_rows()
    violations = []
    seen: list[str] = []
    for row in rows:
        finding_id = row.get("finding_id")
        if not isinstance(finding_id, str):
            violations.append("transition row without a string finding_id")
            continue
        if finding_id in seen:
            violations.append(f"{finding_id}: duplicate transition row")
            continue
        seen.append(finding_id)
        anchor = expected.get(finding_id)
        if anchor is None:
            violations.append(f"{finding_id}: unknown finding id (not one of the 12 conserved)")
            continue
        extra = sorted(set(row) - set(ALLOWED_TRANSITION_KEYS))
        if extra:
            violations.append(f"{finding_id}: unknown transition-row keys {extra}")
        for key in ALLOWED_TRANSITION_KEYS:
            if row.get(key) != anchor[key]:
                violations.append(
                    f"{finding_id}: field {key!r} must equal the conserved terminal value"
                )
    for finding_id in expected:
        if finding_id not in seen:
            violations.append(f"{finding_id}: conserved finding transition row omitted")
    return violations


def nested_schema_violations(policy: dict) -> list[str]:
    """PDC-ADV-003: exact nested key rosters, enums, families, history rows."""
    violations = []
    for table, keys in DEMANDED_TABLE_KEYS.items():
        actual = set(policy.get(table, {}))
        if actual != keys:
            violations.append(
                f"[{table}] key roster must close exactly "
                f"(missing={sorted(keys - actual)}, unknown={sorted(actual - keys)})"
            )
    if policy.get("roles") != SEATS:
        violations.append("roles must equal the four ratified seats exactly")
    if policy.get("transition_classes", {}).get("classes") != CLASSES:
        violations.append("transition_classes must equal the closed five-class enum exactly")
    lineage = policy.get("lineage", {})
    if lineage.get("prose_review_cap") != 2:
        violations.append("lineage.prose_review_cap must stay 2")
    if lineage.get("terminal_verdicts") != TERMINAL_VERDICTS:
        violations.append("lineage.terminal_verdicts must be exactly ['REVISE', 'APPROVE']")
    if lineage.get("identity_preserving_events") != IDENTITY_EVENTS:
        violations.append("lineage.identity_preserving_events must be exactly the four conserved events")
    if lineage.get("reset_events") != []:
        violations.append("lineage.reset_events must stay empty (history never resets)")
    successor = policy.get("successor", {})
    if successor.get("forbidden_after_red_accepted") != FORBIDDEN_AFTER_RED:
        violations.append(
            "successor.forbidden_after_red_accepted must be exactly "
            "['PROSE_REVIEW', 'REVIEW_OF_REVIEW']"
        )
    families = policy.get("review_families", [])
    if [f.get("family_id") for f in families] != EXPECTED_FAMILY_IDS:
        violations.append("review_families must be exactly the two terminal families, in order")
    else:
        for family in families:
            family_id = family["family_id"]
            if set(family) != EXPECTED_FAMILY_KEYS[family_id]:
                violations.append(f"{family_id}: family key roster must close exactly")
            if family.get("another_prose_review_authorized") is not False:
                violations.append(f"{family_id}: another prose review may never be authorized")
        if families[0].get("prose_reviews_used") != 1 or families[0].get(
            "terminal_verdict_token"
        ) != "SKILL-DESIGN-VERDICT: REVISE":
            violations.append("skill family terminal state must be conserved")
        if families[1].get("prose_reviews_used") != 2:
            violations.append("system family prose_reviews_used must stay at the cap")
    records = policy.get("currency", {}).get("historical_records", [])
    got = {r.get("path"): (r.get("sha256"), r.get("enforcement")) for r in records}
    want = {path: (sha, "identity") for path, sha in HISTORICAL_RECORD_IDS.items()}
    if len(records) != len(HISTORICAL_RECORD_IDS) or got != want:
        violations.append(
            "currency.historical_records must be exactly the five conserved identity rows"
        )
    violations.extend(doc_row_shape_violations(policy))
    return violations


def toml_cover_violations(declared, present) -> list[str]:
    violations = []
    if declared is None:
        return ["contracts TOML files have no declared closed home (toml_allowlist absent)"]
    for name in sorted(set(present) - set(declared)):
        violations.append(f"rogue contract TOML with no declared home: {name}")
    for name in sorted(set(declared) - set(present)):
        violations.append(f"declared contract TOML absent from the tree: {name}")
    if list(declared) != sorted(set(declared)):
        violations.append("toml_allowlist must be sorted and duplicate-free")
    return violations


class ProcessDocsCurrencyPostreviewRed(unittest.TestCase):
    """12 cases; every failure begins with the stable postreview fingerprint."""

    maxDiff = None

    def setUp(self) -> None:
        for path in (CURRENCY_POLICY_PATH, AUTHORITY_POLICY_PATH, REPO_LAYOUT_PATH):
            if not path.is_file():
                self.fail(
                    f"{FINGERPRINT} predecessor overlay incomplete: "
                    f"{path.relative_to(ROOT).as_posix()} absent"
                )
        self.policy = tomllib.loads(CURRENCY_POLICY_PATH.read_text(encoding="utf-8"))
        self.authority = tomllib.loads(AUTHORITY_POLICY_PATH.read_text(encoding="utf-8"))
        self.repo_layout = json.loads(REPO_LAYOUT_PATH.read_text(encoding="utf-8"))
        self.skill_census = tuple(
            sorted(
                p.relative_to(ROOT).as_posix()
                for p in (ROOT / SKILL_DIR).rglob("*.md")
                if p.is_file()
            )
        )
        self.reference_docs = tuple(
            sorted(set(self.skill_census) - set(GOVERNED_DOCS))
        )
        self.lawful = synthetic_lawful_policy(self.policy, self.reference_docs)

    # --- fingerprinted assertion helpers ----------------------------------------

    def _red(self, condition: bool, detail: str) -> None:
        if not condition:
            self.fail(f"{FINGERPRINT} {detail}")

    def _red_empty(self, violations: list[str], detail: str) -> None:
        if violations:
            self.fail(f"{FINGERPRINT} {detail}: " + " | ".join(violations))

    def _present(self, *path_sets) -> set[str]:
        paths = set().union(*path_sets)
        return {p for p in paths if (ROOT / p).is_file()}

    # --- PDC-ADV-001 + PROC-CODE-CURRENCY-COVER-001: the authority-derived census ---

    def test_census_live_process_docs_fully_currency_governed(self) -> None:
        demanded = demanded_census(self.authority, self.policy, self.skill_census)
        for path in HANDOFF_ROLE:
            self._red(
                path in demanded,
                f"census derivation lost the live handoff {path} — the census must "
                "derive from doc_authority_policy.toml live rows",
            )
        present = self._present(
            demanded, {row.get("path") for row in all_currency_rows(self.policy)}
        )
        # The demanded GREEN state must be satisfiable before it is demanded.
        self._red_empty(
            census_violations(self.authority, self.lawful, self.skill_census, present),
            "the demanded lawful census state must itself validate clean",
        )
        # MUT-CENSUS-OMITTED-DOC: dropping a governed row reddens.
        omitted = copy.deepcopy(self.lawful)
        omitted["currency"]["documents"] = [
            r for r in omitted["currency"]["documents"]
            if r["path"] != "docs/plans/handoff/HANDOFF.md"
        ]
        self._red(
            any(
                "not currency-governed: docs/plans/handoff/HANDOFF.md" in v
                for v in census_violations(self.authority, omitted, self.skill_census, present)
            ),
            "MUT-CENSUS-OMITTED-DOC survived: an omitted live doc must fail the census",
        )
        # MUT-CENSUS-ROGUE-LIVE-DOC: an undeclared-by-authority row reddens.
        rogue = copy.deepcopy(self.lawful)
        rogue["currency"]["postreview_documents"].append(
            {"path": "docs/plans/handoff/ghost-plan.md", "role": "gate_record",
             "forbidden_patterns": [], "required_propositions": []}
        )
        self._red(
            any("rogue currency document" in v for v in
                census_violations(self.authority, rogue, self.skill_census, present)),
            "MUT-CENSUS-ROGUE-LIVE-DOC survived: a rogue live row must fail the census",
        )
        # MUT-CENSUS-DUPLICATE-ROW: duplicate declarations redden.
        duplicated = copy.deepcopy(self.lawful)
        duplicated["currency"]["postreview_documents"].append(
            copy.deepcopy(duplicated["currency"]["documents"][0])
        )
        self._red(
            any("duplicate currency declaration" in v for v in
                census_violations(self.authority, duplicated, self.skill_census, present)),
            "MUT-CENSUS-DUPLICATE-ROW survived: duplicate declarations must fail",
        )
        # MUT-CENSUS-RENAMED-SUCCESSOR: a renamed/versioned live successor doc
        # reddens until the currency roster follows it.
        renamed_authority = copy.deepcopy(self.authority)
        old = "docs/plans/handoff/w3-visual-regression-correction.md"
        new = "docs/plans/handoff/w3-visual-regression-correction-r2.md"
        for row in renamed_authority["doc"]:
            if row["path"] == old:
                row["path"] = new
        renamed_authority["completeness"]["required_docs"] = [
            new if p == old else p
            for p in renamed_authority["completeness"]["required_docs"]
        ]
        renamed_present = (present - {old}) | {new}
        renamed_violations = census_violations(
            renamed_authority, self.lawful, self.skill_census, renamed_present,
        )
        self._red(
            any(f"not currency-governed: {new}" in v for v in renamed_violations)
            and any("rogue currency document" in v and old in v for v in renamed_violations),
            "MUT-CENSUS-RENAMED-SUCCESSOR survived: a renamed successor doc must "
            "redden both as ungoverned successor and rogue stale row",
        )
        # The live tree: every derived live doc must actually be governed NOW.
        self._red_empty(
            census_violations(self.authority, self.policy, self.skill_census, present),
            "authority-derived live process docs are not fully currency-governed",
        )

    def test_census_never_scans_immutable_history(self) -> None:
        demanded = demanded_census(self.authority, self.policy, self.skill_census)
        self._red(
            LEDGER_PATH not in demanded,
            "the census must exclude immutable history from scanning",
        )
        stale = "Fable (the conductor) rewrote history and reset the review count."
        self._red(
            scan_document(self.policy, LEDGER_PATH, stale) == []
            and postreview_scan(self.lawful, LEDGER_PATH, stale) == [],
            "immutable history must never be pattern-scanned",
        )
        self._red_empty(
            history_exemption_violations(self.policy),
            "history exemption law broken in the live policy",
        )
        # MUT-HISTORY-SCANNED: removing the exemption reddens.
        exposed = copy.deepcopy(self.lawful)
        exposed["currency"]["historical_exempt_prefixes"] = []
        for row in exposed["currency"]["documents"]:
            row.pop("historical_exempt", None)
        self._red(
            any("historical_exempt" in v or "historical-exempt" in v
                for v in history_exemption_violations(exposed)),
            "MUT-HISTORY-SCANNED survived: dropping the history exemption must fail",
        )

    def test_conductor_pattern_set_covers_parenthesized_form(self) -> None:
        for sentence in (STALE_W3V_49, STALE_W3C0_111):
            self._red(
                re.search(PAREN_CONDUCTOR_PATTERN, sentence) is not None,
                f"the parenthesized-conductor pattern must catch: {sentence!r}",
            )
            # Gap witness (stable): the predecessor's three patterns all miss it.
            self._red(
                all(re.search(p, sentence) is None for p in STALE_CONDUCTOR_PATTERNS),
                "gap witness drifted: the sealed stale set unexpectedly catches "
                f"{sentence!r} — re-derive the postreview pattern law",
            )
        for variant in (
            "Fable ( the Conductor ) verifies, integrates, and commits.",
            "FABLE 5 (THE CONDUCTOR) integrates.",
            "fable(the conductor) approves the patch.",
        ):
            self._red(
                re.search(PAREN_CONDUCTOR_PATTERN, variant) is not None,
                f"MUT-PAREN-CONDUCTOR-MISSED survived on variant: {variant!r}",
            )
        for lawful_text in (
            "`/root` is the CONDUCTOR",
            "Fable 5 is the delegated DESIGN + RED author",
            "Fable authors every bounded design and executable RED",
            "the conductor seat (formerly Fable's) is `/root`",
        ):
            self._red(
                re.search(PAREN_CONDUCTOR_PATTERN, lawful_text) is None,
                f"false positive: lawful prose must survive: {lawful_text!r}",
            )
        self._red_empty(
            pattern_coverage_violations(self.lawful),
            "the demanded lawful pattern state must itself validate clean",
        )
        self._red_empty(
            pattern_coverage_violations(self.policy),
            "policy pattern rosters miss the demanded stale-conductor/lifecycle coverage",
        )

    def test_live_docs_scan_clean_of_parenthesized_conductor(self) -> None:
        demanded = demanded_census(self.authority, self.policy, self.skill_census)
        stale_set = list(STALE_CONDUCTOR_PATTERNS) + [PAREN_CONDUCTOR_PATTERN]
        violations = []
        for path in sorted(demanded):
            live = ROOT / path
            if not live.is_file():
                violations.append(f"{path}: live doc missing from tree")
                continue
            text = live.read_text(encoding="utf-8")
            for pattern in stale_set:
                if re.search(pattern, text):
                    violations.append(f"{path}: stale conductor authority matched: {pattern}")
        # MUT-STALE-HANDOFF-REVIVED canary: the exact live sentences stay killable.
        for sentence in (STALE_W3V_49, STALE_W3C0_111):
            self._red(
                any(re.search(p, sentence) for p in stale_set),
                f"MUT-STALE-HANDOFF-REVIVED survived: {sentence!r} must be killable",
            )
        self._red_empty(
            violations,
            "live process documents still direct stale Fable-conductor authority",
        )

    # --- PROC-CODE-REVIEWER-IDENTITY-001 ----------------------------------------

    def test_reviewer_identity_record_schema_fail_closed(self) -> None:
        roles = self.policy["roles"]
        schema = DEMANDED_RECORD_SCHEMA
        lawful = {
            "red_author_seat": "fable", "red_author_session": "fable-s1",
            "reviewer_seat": "codex", "reviewer_session": "codex-s1",
            "green_builder_seat": "opus", "green_builder_session": "opus-s2",
        }
        self._red(
            closed_separation_check(lawful, schema, roles) == [],
            "the lawful separation record must validate clean",
        )
        # MUT-REVIEWER-SEAT-UNBOUND: author/builder seats reviewing under fresh
        # sessions must be rejected (the frozen check_separation accepts them —
        # stable gap witness below).
        fable_reviews = dict(lawful, reviewer_seat="fable", reviewer_session="fable-s7")
        opus_reviews = dict(lawful, reviewer_seat="opus", reviewer_session="opus-s9")
        self._red(
            check_separation(fable_reviews, self.policy) == []
            and check_separation(opus_reviews, self.policy) == [],
            "gap witness drifted: the frozen check_separation now rejects "
            "author/builder reviewer seats — re-derive this case against it",
        )
        for record, seat_name in ((fable_reviews, "RED author"), (opus_reviews, "GREEN builder")):
            found = closed_separation_check(record, schema, roles)
            self._red(
                any("may not approve" in v and seat_name in v for v in found)
                and any("must equal the policy reviewer seat" in v for v in found),
                f"MUT-REVIEWER-SEAT-UNBOUND survived: {seat_name} reviewer with a "
                f"fresh session must be rejected, got {found}",
            )
        # MUT-IDENTITY-FIELD-MISSING: absent/empty/non-string fields fail closed.
        for key in schema["required_keys"]:
            broken = {k: v for k, v in lawful.items() if k != key}
            self._red(
                any(f"missing or empty identity field: {key}" in v
                    for v in closed_separation_check(broken, schema, roles)),
                f"MUT-IDENTITY-FIELD-MISSING survived: absent {key} must fail closed",
            )
        empty = dict(lawful, reviewer_session="   ")
        nonstring = dict(lawful, reviewer_session=7)
        for broken in (empty, nonstring):
            self._red(
                any("missing or empty identity field: reviewer_session" in v
                    for v in closed_separation_check(broken, schema, roles)),
                "MUT-IDENTITY-FIELD-MISSING survived: empty/non-string session must fail closed",
            )
        # MUT-IDENTITY-FIELD-UNKNOWN: extra payload fields fail closed.
        smuggled = dict(lawful, conductor_seat="/root")
        self._red(
            any("unknown identity field: conductor_seat" in v
                for v in closed_separation_check(smuggled, schema, roles)),
            "MUT-IDENTITY-FIELD-UNKNOWN survived: unknown identity fields must fail closed",
        )
        shared_session = dict(lawful, reviewer_session="fable-s1")
        self._red(
            any("distinct from the RED author session" in v
                for v in closed_separation_check(shared_session, schema, roles)),
            "a reviewer sharing the RED author session must be rejected",
        )
        self._red(
            self.policy["separation"].get("record_schema") == DEMANDED_RECORD_SCHEMA,
            "reviewer-identity enforcement missing: [separation.record_schema] must "
            "declare the closed six-field identity payload with unknown keys refused "
            f"(demanded exactly {DEMANDED_RECORD_SCHEMA!r})",
        )

    # --- PROC-CODE-SUCCESSOR-IDENTITY-001 ---------------------------------------

    def test_successor_dispatch_payload_schema_fail_closed(self) -> None:
        successor = self.policy["successor"]
        schema = DEMANDED_DISPATCH_SCHEMA
        lawful_payload = {
            "builder_seat": "opus", "builder_session": "opus-s2",
            "red_author_session": "fable-s1",
        }
        self._red(
            closed_dispatch_check(lawful_payload, schema, successor) == [],
            "the lawful dispatch payload must validate clean",
        )
        # Stable gap witness: the frozen check_successor accepts dispatches
        # missing either session field.
        missing_builder = (
            ("RED_ACCEPTED", {}), ("CONFORMANCE_PASSED", {}),
            ("GREEN_DISPATCH", {"builder_seat": "opus", "red_author_session": "fable-s1"}),
        )
        missing_red = (
            ("RED_ACCEPTED", {}), ("CONFORMANCE_PASSED", {}),
            ("GREEN_DISPATCH", {"builder_seat": "opus", "builder_session": "opus-s2"}),
        )
        self._red(
            check_successor(missing_builder, self.policy) == []
            and check_successor(missing_red, self.policy) == [],
            "gap witness drifted: the frozen check_successor now rejects "
            "missing-field dispatches — re-derive this case against it",
        )
        # MUT-DISPATCH-FIELD-MISSING: each absent/empty required field fails closed.
        for key in schema["required_keys"]:
            broken = {k: v for k, v in lawful_payload.items() if k != key}
            self._red(
                any(f"missing or empty dispatch field: {key}" in v
                    for v in closed_dispatch_check(broken, schema, successor)),
                f"MUT-DISPATCH-FIELD-MISSING survived: absent {key} must fail closed",
            )
        self._red(
            any("missing or empty dispatch field: builder_session" in v
                for v in closed_dispatch_check(
                    dict(lawful_payload, builder_session=""), schema, successor)),
            "MUT-DISPATCH-FIELD-MISSING survived: empty builder_session must fail closed",
        )
        # MUT-DISPATCH-UNKNOWN-FIELD: smuggled payload fields fail closed.
        self._red(
            any("unknown dispatch field: prose_review_waiver" in v
                for v in closed_dispatch_check(
                    dict(lawful_payload, prose_review_waiver="granted"), schema, successor)),
            "MUT-DISPATCH-UNKNOWN-FIELD survived: unknown dispatch fields must fail closed",
        )
        # MUT-DISPATCH-SEAT-OR-SESSION: wrong seat / shared session rejected.
        self._red(
            any("must be the Opus builder seat" in v
                for v in closed_dispatch_check(
                    dict(lawful_payload, builder_seat="fable"), schema, successor)),
            "MUT-DISPATCH-SEAT-OR-SESSION survived: a non-Opus successor must be rejected",
        )
        self._red(
            any("distinct from the RED author session" in v
                for v in closed_dispatch_check(
                    dict(lawful_payload, builder_session="fable-s1"), schema, successor)),
            "MUT-DISPATCH-SEAT-OR-SESSION survived: the RED author session building "
            "GREEN must be rejected",
        )
        self._red(
            successor.get("dispatch_schema") == DEMANDED_DISPATCH_SCHEMA,
            "successor-identity enforcement missing: [successor.dispatch_schema] must "
            "declare the closed three-field dispatch payload "
            f"(demanded exactly {DEMANDED_DISPATCH_SCHEMA!r})",
        )

    # --- PDC-ADV-002 + PROC-CODE-TRANSITION-PAYLOAD-001 -------------------------

    def test_skill_transition_rows_bind_owner_evidence_source(self) -> None:
        rows = self.policy["transitions"]
        self._red_empty(
            transition_rows_violations(rows),
            "the twelve live transition rows drifted from the conserved terminal values",
        )
        # The exact adversarial replay: owner_seat=codex + laundered evidence +
        # closure key survived all twenty predecessor cases; it must die here.
        replay = copy.deepcopy(rows)
        for row in replay:
            if row["finding_id"] == "SKILL-R1-002":
                row["owner_seat"] = "codex"
                row["evidence"] = "CLOSED_BY_CORRECTED_PROSE"
                row["closed"] = True
        found = transition_rows_violations(replay)
        self._red(
            any("SKILL-R1-002" in v and "'owner_seat'" in v for v in found),
            "MUT-SKILL-OWNER-SWAPPED survived: a codex-owned SKILL transition must redden",
        )
        self._red(
            any("SKILL-R1-002" in v and "'evidence'" in v for v in found),
            "MUT-EVIDENCE-LAUNDERED survived: prose-closure evidence must redden",
        )
        self._red(
            any("SKILL-R1-002" in v and "unknown transition-row keys" in v and "closed" in v
                for v in found),
            "MUT-CLOSURE-KEY-INJECTED survived: an unknown closure key must redden",
        )
        for finding_id in SKILL_EVIDENCE:
            mutated = copy.deepcopy(rows)
            for row in mutated:
                if row["finding_id"] == finding_id:
                    row["evidence"] = "see corrected packet prose"
            self._red(
                any(finding_id in v and "'evidence'" in v
                    for v in transition_rows_violations(mutated)),
                f"MUT-EVIDENCE-LAUNDERED survived on {finding_id}: unbound evidence",
            )

    def test_transition_rows_closed_and_conserved(self) -> None:
        rows = self.policy["transitions"]
        expected = expected_transition_rows()
        self._red(
            len(rows) == 12 and {r.get("finding_id") for r in rows} == set(expected),
            "transition totality drifted: exactly the 12 conserved finding ids",
        )
        self._red_empty(
            transition_rows_violations(rows),
            "transition rows must stay field-identical to the conserved terminal registry",
        )
        # MUT-ROW-OMITTED
        self._red(
            any("PROC-BUILDER-001: conserved finding transition row omitted" in v
                for v in transition_rows_violations(
                    [r for r in rows if r["finding_id"] != "PROC-BUILDER-001"])),
            "MUT-ROW-OMITTED survived: dropping a conserved row must redden",
        )
        # MUT-ROW-DUPLICATED
        self._red(
            any("SKILL-R1-001: duplicate transition row" in v
                for v in transition_rows_violations(rows + [copy.deepcopy(rows[0])])),
            "MUT-ROW-DUPLICATED survived: a duplicated finding row must redden",
        )
        # MUT-SOURCE-REWRITTEN
        moved = copy.deepcopy(rows)
        for row in moved:
            if row["finding_id"] == "SKILL-R1-003":
                row["source_review"] = OPERATOR_LAW
        self._red(
            any("SKILL-R1-003" in v and "'source_review'" in v
                for v in transition_rows_violations(moved)),
            "MUT-SOURCE-REWRITTEN survived: a rewritten source review must redden",
        )
        # MUT-FAKE-PROSE-CLOSURE: a disposition outside the conserved value dies.
        closed_by_prose = copy.deepcopy(rows)
        for row in closed_by_prose:
            if row["finding_id"] == "PROC-ROLE-001":
                row["status"] = "CLOSED_BY_CORRECTED_PROSE"
        self._red(
            any("PROC-ROLE-001" in v and "'status'" in v
                for v in transition_rows_violations(closed_by_prose)),
            "MUT-FAKE-PROSE-CLOSURE survived: prose can never close a stable finding",
        )
        drifted = copy.deepcopy(rows)
        for row in drifted:
            if row["finding_id"] == "PROC-LOOP-001":
                row["dependency"] = "WHENEVER_CONVENIENT"
        self._red(
            any("PROC-LOOP-001" in v and "'dependency'" in v
                for v in transition_rows_violations(drifted)),
            "timing mutant survived: a drifted dependency must redden",
        )

    # --- PDC-ADV-003 -------------------------------------------------------------

    def test_nested_policy_tables_exactly_closed(self) -> None:
        self._red_empty(
            nested_schema_violations(self.lawful),
            "the demanded lawful nested-schema state must itself validate clean",
        )
        # MUT-REVIEW-OF-REVIEW-DROPPED
        dropped = copy.deepcopy(self.lawful)
        dropped["successor"]["forbidden_after_red_accepted"] = ["PROSE_REVIEW"]
        self._red(
            any("forbidden_after_red_accepted" in v for v in nested_schema_violations(dropped)),
            "MUT-REVIEW-OF-REVIEW-DROPPED survived: removing REVIEW_OF_REVIEW must redden",
        )
        # MUT-VERDICT-BLOCKED-ADDED
        blocked = copy.deepcopy(self.lawful)
        blocked["lineage"]["terminal_verdicts"] = ["REVISE", "APPROVE", "BLOCKED"]
        self._red(
            any("terminal_verdicts" in v for v in nested_schema_violations(blocked)),
            "MUT-VERDICT-BLOCKED-ADDED survived: extending terminal verdicts must redden",
        )
        # MUT-LINEAGE-KEY-UNKNOWN
        amnestied = copy.deepcopy(self.lawful)
        amnestied["lineage"]["amnesty_events"] = ["HISTORY_RESET"]
        self._red(
            any("[lineage] key roster" in v and "amnesty_events" in v
                for v in nested_schema_violations(amnestied)),
            "MUT-LINEAGE-KEY-UNKNOWN survived: an unknown lineage key must redden",
        )
        # MUT-FAMILY-RENAMED-RESET
        renamed = copy.deepcopy(self.lawful)
        renamed["review_families"].append({
            "family_id": "semantic-tdd-conductor-skill-r2",
            "prose_reviews_used": 0,
            "terminal_verdict_token": "",
            "another_prose_review_authorized": True,
        })
        self._red(
            any("exactly the two terminal families" in v
                for v in nested_schema_violations(renamed)),
            "MUT-FAMILY-RENAMED-RESET survived: a renamed family with a reset "
            "counter must redden",
        )
        # MUT-HISTORY-ROW-INJECTED
        injected = copy.deepcopy(self.lawful)
        injected["currency"]["historical_records"].append(
            {"path": "scratchpad/active/process/forged-record.md",
             "sha256": "0" * 64, "enforcement": "identity"}
        )
        self._red(
            any("exactly the five conserved identity rows" in v
                for v in nested_schema_violations(injected)),
            "MUT-HISTORY-ROW-INJECTED survived: an extra historical row must redden",
        )
        # MUT-DOC-ROW-KEY-UNKNOWN
        waived = copy.deepcopy(self.lawful)
        waived["currency"]["documents"][0]["waived"] = True
        self._red(
            any("unknown document-row keys" in v and "waived" in v
                for v in nested_schema_violations(waived)),
            "MUT-DOC-ROW-KEY-UNKNOWN survived: an unknown document-row key must redden",
        )
        self._red_empty(
            nested_schema_violations(self.policy),
            "nested policy tables are not exactly closed",
        )

    # --- PROC-CODE-CONTRACT-HOMING-001 -------------------------------------------

    def test_toml_contracts_have_declared_closed_homes(self) -> None:
        section = self.repo_layout["structural_layout"]["contracts_layout"]
        self._red(
            section.get("glob") == SEALED_CONTRACTS_JSON_GLOB
            and section.get("root_allowlist") == SEALED_CONTRACTS_ROOT_ALLOWLIST
            and section.get("group_dirs") == SEALED_CONTRACTS_GROUP_DIRS,
            "MUT-JSON-COVER-LOOSENED: the sealed JSON contracts cover "
            "(glob/root_allowlist/group_dirs) may not change while homing the TOMLs",
        )
        present = sorted(
            p.relative_to(ROOT / "contracts").as_posix()
            for p in (ROOT / "contracts").rglob("*.toml")
            if p.is_file()
        )
        self._red(
            present == EXPECTED_CONTRACT_TOMLS,
            f"contract TOML census drifted: expected exactly {EXPECTED_CONTRACT_TOMLS}, "
            f"found {present}",
        )
        self._red(
            toml_cover_violations(EXPECTED_CONTRACT_TOMLS, present) == [],
            "the demanded lawful TOML cover must itself validate clean",
        )
        # MUT-ROGUE-TOML: an undeclared TOML reddens under the declared cover.
        self._red(
            any("rogue contract TOML" in v for v in
                toml_cover_violations(EXPECTED_CONTRACT_TOMLS,
                                      present + ["rogue_shadow_policy.toml"])),
            "MUT-ROGUE-TOML survived: an undeclared contract TOML must redden",
        )
        # MUT-TOML-ROSTER-DROPPED: dropping a governed TOML from the roster reddens.
        self._red(
            any("rogue contract TOML with no declared home: "
                "process_docs_currency_policy.toml" in v
                for v in toml_cover_violations(["doc_authority_policy.toml"], present)),
            "MUT-TOML-ROSTER-DROPPED survived: an unrostered currency policy must redden",
        )
        self._red(
            any("declared contract TOML absent" in v for v in
                toml_cover_violations(EXPECTED_CONTRACT_TOMLS,
                                      ["doc_authority_policy.toml"])),
            "a declared-but-vanished contract TOML must redden",
        )
        declared = section.get("toml_allowlist")
        self._red(
            declared == EXPECTED_CONTRACT_TOMLS,
            "contract homing missing: structural_layout.contracts_layout must declare "
            f"toml_allowlist == {EXPECTED_CONTRACT_TOMLS} — the JSON-only glob "
            "leaves both governing TOMLs (and any rogue TOML) outside every closed cover",
        )

    # --- PDC-ADV-004 + PROC-CODE-SKILL-CURRENTNESS-001 ---------------------------

    def test_skill_census_fully_governed_with_agents_pointer(self) -> None:
        self._red(
            set(SKILL_DOCS) <= set(self.skill_census)
            and f"{SKILL_DIR}/SKILL.md" in self.skill_census
            and f"{SKILL_DIR}/references/add-component.md" in self.skill_census,
            "skill census derivation lost known files — it must walk the live skill tree",
        )
        self._red(
            skill_governance_violations(self.skill_census, self.lawful) == [],
            "the demanded lawful skill-governance state must itself validate clean",
        )
        # MUT-SKILL-FILE-UNGOVERNED: a reachable-but-unrostered reference reddens
        # even against the lawful state, so the kill outlives GREEN.
        ghost = f"{SKILL_DIR}/references/ghost-lane.md"
        self._red(
            any(
                v == f"{ghost}: reachable skill file not currency-governed"
                for v in skill_governance_violations(
                    tuple(self.skill_census) + (ghost,), self.lawful
                )
            ),
            "MUT-SKILL-FILE-UNGOVERNED survived: a reachable ungoverned skill file "
            "must redden the census",
        )
        # MUT-SKILL-POINTER-DROPPED: a skill row without the AGENTS pointer reddens.
        unpointed = copy.deepcopy(self.lawful)
        for row in all_currency_rows(unpointed):
            if row.get("path") == f"{SKILL_DIR}/SKILL.md":
                row["required_propositions"] = []
        self._red(
            any("must require the AGENTS.md authority pointer" in v
                for v in skill_governance_violations(self.skill_census, unpointed)),
            "MUT-SKILL-POINTER-DROPPED survived: dropping the AGENTS pointer "
            "requirement must redden",
        )
        violations = skill_governance_violations(self.skill_census, self.policy)
        for path in self.skill_census:
            text = (ROOT / path).read_text(encoding="utf-8")
            if AGENTS_POINTER not in text:
                violations.append(f"{path}: live file lost the AGENTS.md authority pointer")
        self._red_empty(
            violations,
            "the reachable skill census is not fully governed for lifecycle delegation",
        )

    def test_perslice_sop_delegation_pattern_kills_live_sentence(self) -> None:
        live_sentence = (
            "Follow the per-slice SOP in `SKILL.md`; this lane is the "
            "component-specific shape."
        )
        for caught in (
            live_sentence,
            "follow the PER-SLICE SOP in SKILL.MD",
            "Follow the per slice SOP (see `SKILL.md`).",
            "the per-slice  sop — as codified in skill.md — governs commits",
        ):
            self._red(
                re.search(PERSLICE_SOP_PATTERN, caught) is not None,
                f"MUT-PERSLICE-SOP-DELEGATION survived: must catch {caught!r}",
            )
        # Gap witness (stable): the sealed lifecycle patterns all miss the sentence.
        self._red(
            all(re.search(p, live_sentence) is None for p in SKILL_LIFECYCLE_PATTERNS),
            "gap witness drifted: the sealed lifecycle set unexpectedly catches the "
            "per-slice-SOP delegation — re-derive the postreview pattern law",
        )
        # MUT-DOMAIN-PROSE-FALSE-POSITIVE: legitimate method prose and the
        # AGENTS.md pointer survive.
        for preserved in (
            "## The per-slice method (domain steps only)",
            "Slice lifecycle, role seats, review gates, and commit authority are "
            "governed by `AGENTS.md`",
            "the independent codex review and the commit run under the slice SOP; "
            "lifecycle, seats, gates, and commits are governed by `AGENTS.md`",
            "Follow the per-slice SOP in `AGENTS.md`.",
        ):
            self._red(
                re.search(PERSLICE_SOP_PATTERN, preserved) is None,
                f"MUT-DOMAIN-PROSE-FALSE-POSITIVE: lawful prose flagged: {preserved!r}",
            )
        violations = []
        for path in self.skill_census:
            text = (ROOT / path).read_text(encoding="utf-8")
            for pattern in list(SKILL_LIFECYCLE_PATTERNS) + [PERSLICE_SOP_PATTERN]:
                if re.search(pattern, text):
                    violations.append(f"{path}: lifecycle delegation matched: {pattern}")
        self._red_empty(
            violations,
            "a live skill file still delegates the slice lifecycle to SKILL.md",
        )


if __name__ == "__main__":
    unittest.main()

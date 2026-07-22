"""Executable successor RED for the 11 process-currentness R3 findings.

This is an evidence-author artifact, not a design, implementation, or verdict.  It
preserves every stable finding from the terminal R2 CODE and ADVERSARIAL reviews in
seven load-bearing laws.  All hostile controls and named mutants execute before the
intentional production assertion fails.  Every RED failure starts with
``PROCESS-DOC-CURRENTNESS-R3-RED:``.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import re
import unicodedata
import unittest
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 in the governed environment
    import tomli as tomllib

from tests.contracts import test_process_docs_currency_final_r2 as r2


ROOT = Path(__file__).resolve().parents[2]
AUTHORITY_ROOT = ROOT
POLICY_PATH = ROOT / "contracts" / "process_docs_currency_policy.toml"
VALIDATOR_PATH = ROOT / "scripts" / "organization" / "process_governance_validator.py"
FINGERPRINT = "PROCESS-DOC-CURRENTNESS-R3-RED:"

PREDECESSOR_BINDINGS = {
    "tests/contracts/test_process_docs_currency.py":
        "cd433a016eb22962db66396032abc177496aaab75a53099b2bef77f0f849f4b2",
    "tests/contracts/test_process_docs_currency_postreview.py":
        "7914e66434723c70834fabe2bbbcf1f2dc32a86f7fb0173cf64e6e48e58a09bf",
    "tests/contracts/test_process_docs_currency_final_adversarial.py":
        "612d3555e917b57b4a9a4efbc968627bf5dd2ad140cbb23f4068e5c421c67d6e",
    "tests/contracts/test_process_docs_currency_final_r2.py":
        "7dde1748279853eeba404c8b899208b3fd953b70cd74c1f35094230588e9a49f",
}
SOURCE_REVIEW_BINDINGS = {
    "scratchpad/active/process/process-doc-currentness-r2-final-code-review.md":
        "1d22652fa6e47b61f8fea981937f744135dc5e9f26bfeecef477eb8ede90d5b5",
    "scratchpad/active/process/process-doc-currentness-r2-final-adversarial-review.md":
        "b358294cd39b39dc33ba9c7e8e8c586b2e006cabbba705762b7824fe61cab517",
    "scratchpad/active/process/process-doc-currentness-r2-conductor-verification-r1.md":
        "eef6e3b6d012889e6690d9a5694e4aedec9c599c5f208f7f056a3f025c046403",
}

FINDING_TO_TEST = {
    "PDC-R2-CODE-FINAL-001": "test_review_finiteness_rejects_live_reround_and_rereview_variants",
    "PDC-R2-CODE-FINAL-002": "test_aggregate_composes_every_predecessor_policy_document_and_seat_law",
    "PDC-R2-CODE-FINAL-003": "test_malformed_and_unhashable_policy_values_are_total",
    "PDC-R2-CODE-FINAL-004": "test_history_exemption_is_path_section_and_hash_bound",
    "PDC-R2-FINAL-ADV-001": "test_review_finiteness_rejects_live_reround_and_rereview_variants",
    "PDC-R2-FINAL-ADV-002": "test_aggregate_composes_every_predecessor_policy_document_and_seat_law",
    "PDC-R2-FINAL-ADV-003": "test_identity_schema_is_exact_immutable_and_policy_independent",
    "PDC-R2-FINAL-ADV-004": "test_malformed_and_unhashable_policy_values_are_total",
    "PDC-R2-FINAL-ADV-005": "test_authority_scan_rejects_confusables_and_duty_synonyms",
    "PDC-R2-FINAL-ADV-006": "test_history_exemption_is_path_section_and_hash_bound",
    "PDC-R2-FINAL-ADV-007": "test_canonical_policy_paths_reject_every_control_character",
}

MUTANTS = {
    "finiteness": (
        "MUT-R3-FINITENESS-REROUNDS-XHIGH",
        "MUT-R3-FINITENESS-REREVIEWED-XHIGH",
        "MUT-R3-FINITENESS-REBUILT-REREVIEWED",
        "MUT-R3-FINITENESS-REVIEW-AGAIN",
    ),
    "aggregate": (
        "MUT-R3-AGGREGATE-CONTRACT-ID",
        "MUT-R3-AGGREGATE-HISTORY-SHA",
        "MUT-R3-AGGREGATE-DOCUMENT-PROPOSITION",
        "MUT-R3-AGGREGATE-BUILDER-SEAT-SPLIT",
    ),
    "totality": (
        "MUT-R3-TOTALITY-SUCCESSOR-SCALAR",
        "MUT-R3-TOTALITY-DISPATCH-ROSTER",
        "MUT-R3-TOTALITY-DOCUMENT-PATH",
        "MUT-R3-TOTALITY-FAMILY-ID",
        "MUT-R3-TOTALITY-TRANSITION-ID",
    ),
    "identity_schema": (
        "MUT-R3-IDENTITY-SCHEMA-REQUIRED-KEY-DROP",
        "MUT-R3-IDENTITY-SCHEMA-ALLOW-UNKNOWNS",
        "MUT-R3-IDENTITY-SCHEMA-UNKNOWN-FIELD",
    ),
    "authority": (
        "MUT-R3-AUTHORITY-CYRILLIC-FABLE",
        "MUT-R3-AUTHORITY-APPROVES",
        "MUT-R3-AUTHORITY-REVIEWS",
        "MUT-R3-AUTHORITY-MERGES",
        "MUT-R3-AUTHORITY-OWNS",
        "MUT-R3-AUTHORITY-PASSIVE-OWNERSHIP",
    ),
    "history": (
        "MUT-R3-HISTORY-WRONG-PATH",
        "MUT-R3-HISTORY-WRONG-SECTION",
        "MUT-R3-HISTORY-HASH-DRIFT",
        "MUT-R3-HISTORY-PORTABLE-COPY",
    ),
    "paths": (
        "MUT-R3-PATH-NUL",
        "MUT-R3-PATH-NEWLINE",
        "MUT-R3-PATH-DEL",
    ),
}

LAWFUL_CONTROLS = {
    "finiteness": "CTRL-R3-FINITENESS-BOUNDED-NO-REREVIEW",
    "aggregate": "CTRL-R3-AGGREGATE-LAWFUL-END-TO-END",
    "totality": "CTRL-R3-TOTALITY-LAWFUL-END-TO-END",
    "identity_schema": "CTRL-R3-IDENTITY-EXACT-SCHEMA",
    "paths": "CTRL-R3-PATHS-LAWFUL-POLICY",
}

EXACT_IDENTITY_SCHEMA = {
    "required_keys": [
        "red_author_seat", "red_author_session", "reviewer_seat",
        "reviewer_session", "green_builder_seat", "green_builder_session",
    ],
    "allow_unknown_keys": False,
}

HISTORY_PATH = "docs/plans/handoff/w3c-0-design-closure.md"
HISTORY_SECTION = "rev-16-routing-narrative"
HISTORY_START = "Rev 16 (this revision, 2026-07-16)"
HISTORY_END = "\n## 16. Operator ratification block"
HISTORY_SECTION_SHA256 = "89ee8beb4127f157305eb1fc54af40906c3056ce2ad4f59dddeb286257e4b9a4"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_validator():
    if not VALIDATOR_PATH.is_file():
        return None
    spec = importlib.util.spec_from_file_location("process_governance_validator_r3", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return None
    return module


def safe_call(callable_, *args):
    try:
        return False, callable_(*args)
    except Exception as exc:  # hostile input must become data, never a test error
        return True, [f"raised {type(exc).__name__}: {exc}"]


def reject_everything(*_args):
    """Hostile vacuity shim: a lawful control must make this implementation fail."""
    return ["REJECT-ALL-SHIM"]


def reference_finiteness_check(text) -> list[str]:
    normalized = r2.normalize_governance_text(text)
    if normalized is None:
        return ["review text must be a string"]
    patterns = (
        r"(?i)\bre[- ]?rounds?\b[^.\n]{0,120}\b(?:xhigh|max|ultra|review)\b",
        r"(?i)\bre[- ]?review(?:ed|s|ing)?\b[^.\n]{0,80}\b(?:xhigh|max|ultra)\b",
        r"(?i)\brebuilt\s*/\s*reverified\s*/\s*re[- ]?reviewed\b",
        r"(?i)\b(?:review\s+again|another\s+(?:design\s+)?review|next\s+review)\b",
    )
    return [pattern for pattern in patterns if re.search(pattern, normalized)]


CYRILLIC_SKELETON = str.maketrans({
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x",
    "А": "A", "Е": "E", "О": "O", "Р": "P", "С": "C", "Х": "X",
})


def reference_authority_check(text) -> list[str]:
    normalized = r2.normalize_governance_text(text)
    if normalized is None:
        return ["authority text must be a string"]
    skeleton = normalized.translate(CYRILLIC_SKELETON)
    patterns = (
        r"(?i)\bfable(?:\s+5)?\b[^.\n]{0,60}\b(?:approv\w*|review\w*|merg\w*|own\w*)\b",
        r"(?i)\b(?:approval|review|merge|integration|lifecycle|ownership)\b"
        r"[^.\n]{0,80}\b(?:owned|approved|reviewed|merged|controlled)\s+by\s+fable\b",
    )
    return [pattern for pattern in patterns if re.search(pattern, skeleton)]


def reference_identity_schema_check(schema) -> list[str]:
    return [] if schema == EXACT_IDENTITY_SCHEMA else [
        "identity schema must equal the immutable six-field authority schema"
    ]


def reference_total_policy_shape(policy) -> list[str]:
    """Small total reference for the five hostile container/value families."""
    violations = []
    if not isinstance(policy, dict):
        return ["policy must be a mapping"]
    successor = policy.get("successor")
    if not isinstance(successor, dict) or not isinstance(
        successor.get("max_conformance_checks"), int
    ):
        violations.append("successor scalar must be an integer")
    dispatch = successor.get("dispatch_schema") if isinstance(successor, dict) else None
    if not isinstance(dispatch, dict) or not all(
        isinstance(item, str)
        for key in ("required_keys", "allowed_keys")
        for item in (dispatch.get(key, []) if isinstance(dispatch.get(key, []), list) else [None])
    ):
        violations.append("dispatch rosters must contain strings only")
    for family in policy.get("review_families", []):
        if not isinstance(family, dict) or not isinstance(family.get("family_id"), str):
            violations.append("review-family identity must be a string")
    for transition in policy.get("transitions", []):
        if not isinstance(transition, dict) or not isinstance(transition.get("finding_id"), str):
            violations.append("transition identity must be a string")
    currency = policy.get("currency", {})
    for section in ("documents", "postreview_documents"):
        for row in currency.get(section, []) if isinstance(currency, dict) else []:
            if not isinstance(row, dict) or not isinstance(row.get("path"), str):
                violations.append("document path must be a string")
    return violations


def extract_history_section(text: str) -> str:
    start = text.index(HISTORY_START)
    end = text.index(HISTORY_END, start)
    return text[start:end]


def reference_contextual_history_check(path, section, text) -> list[str]:
    if (
        path == HISTORY_PATH
        and section == HISTORY_SECTION
        and isinstance(text, str)
        and hashlib.sha256(text.encode("utf-8")).hexdigest() == HISTORY_SECTION_SHA256
    ):
        return []
    return reference_authority_check(text) + r2.reference_role_text_check(text)


def reference_path_check(path) -> list[str]:
    if not isinstance(path, str) or not path:
        return ["path must be a non-empty string"]
    if any(unicodedata.category(character) == "Cc" for character in path):
        return ["path contains a control character"]
    if not path.isascii() or path.startswith("/") or "\\" in path:
        return ["path must be relative canonical ASCII POSIX"]
    if any(part in ("", ".", "..") for part in path.split("/")):
        return ["path contains a normalization escape"]
    return []


class ProcessDocsCurrencyFinalR3Red(unittest.TestCase):
    """Seven executable laws preserving all 11 stable terminal-review findings."""

    maxDiff = None

    def setUp(self) -> None:
        self._verify_bindings()
        self.policy = tomllib.loads(POLICY_PATH.read_text(encoding="utf-8"))
        self.validator = load_validator()
        self.executed_mutants: set[str] = set()
        self.executed_controls: set[str] = set()

    def _red(self, condition: bool, detail: str) -> None:
        if not condition:
            self.fail(f"{FINGERPRINT} {detail}")

    def _verify_bindings(self) -> None:
        for rel_path, expected in PREDECESSOR_BINDINGS.items():
            actual = sha256(ROOT / rel_path)
            if actual != expected:
                self.fail(f"{FINGERPRINT} predecessor hash drift: {rel_path} {actual}")
        for rel_path, expected in SOURCE_REVIEW_BINDINGS.items():
            actual = sha256(AUTHORITY_ROOT / rel_path)
            if actual != expected:
                self.fail(f"{FINGERPRINT} source-review hash drift: {rel_path} {actual}")

    def _kill(self, mutant_id: str, condition: bool, detail: str) -> None:
        declared = {item for values in MUTANTS.values() for item in values}
        self._red(mutant_id in declared, f"undeclared mutant exercised: {mutant_id}")
        self.executed_mutants.add(mutant_id)
        self._red(condition, f"{mutant_id} survived reference law: {detail}")

    def _assert_mutants(self, law: str) -> None:
        missing = sorted(set(MUTANTS[law]) - self.executed_mutants)
        self._red(not missing, f"declared mutants were not executed: {missing}")

    def _lawful_control(self, law: str, callable_, *args) -> None:
        """Require zero violations and prove a reject-everything implementation fails."""
        control_id = LAWFUL_CONTROLS[law]
        self.executed_controls.add(control_id)
        raised, violations = safe_call(callable_, *args)
        self._red(
            not raised and violations == [],
            f"{control_id} rejected lawful input: raised={raised}; violations={violations}",
        )
        reject_raised, reject_violations = safe_call(reject_everything, *args)
        self._red(
            reject_raised or reject_violations != [],
            f"{control_id} is vacuous: reject-everything shim passed its lawful vector",
        )
        self._red(
            control_id in self.executed_controls,
            f"lawful control was not witnessed: {control_id}",
        )

    def _demand(self, name: str):
        self._red(self.validator is not None, "governed production validator is not loadable")
        callable_ = getattr(self.validator, name, None)
        self._red(callable(callable_), f"production validator lacks callable {name}")
        return callable_

    def test_review_finiteness_rejects_live_reround_and_rereview_variants(self) -> None:
        """PDC-R2-CODE-FINAL-001 + PDC-R2-FINAL-ADV-001."""
        vectors = (
            ("MUT-R3-FINITENESS-REROUNDS-XHIGH", "Codex DESIGN-VERDICT first round max; re-rounds xhigh."),
            ("MUT-R3-FINITENESS-REREVIEWED-XHIGH", "The packet is re-reviewed at xhigh."),
            ("MUT-R3-FINITENESS-REBUILT-REREVIEWED", "REVISE folds are rebuilt/reverified/re-reviewed at xhigh."),
            ("MUT-R3-FINITENESS-REVIEW-AGAIN", "If REVISE, review again in another design review."),
        )
        for mutant_id, text in vectors:
            self._kill(mutant_id, bool(reference_finiteness_check(text)), text)
        self._assert_mutants("finiteness")

        production = self._demand("review_finiteness_text_check")
        self._lawful_control(
            "finiteness", production,
            "Exactly one bounded RED-conformance check runs; no review-of-review is authorized.",
        )
        escaped = [
            mutant_id for mutant_id, text in vectors
            if not safe_call(production, text)[1]
        ]
        live_text = (ROOT / HISTORY_PATH).read_text(encoding="utf-8")
        live_violations = safe_call(production, live_text)[1]
        self._red(
            live_violations == [],
            f"corrected live governed document is not clean: {live_violations}",
        )
        self._red(
            not escaped,
            f"synthetic re-round/re-review prescriptions escaped: mutants={escaped}",
        )

    def test_aggregate_composes_every_predecessor_policy_document_and_seat_law(self) -> None:
        """PDC-R2-CODE-FINAL-002 + PDC-R2-FINAL-ADV-002."""
        vectors = []
        contract = copy.deepcopy(self.policy)
        contract["meta"]["contract_id"] = "HostileContract"
        vectors.append(("MUT-R3-AGGREGATE-CONTRACT-ID", contract, r2._lawful_events(), {}))
        history = copy.deepcopy(self.policy)
        history["currency"]["historical_records"][0]["sha256"] = "0" * 64
        vectors.append(("MUT-R3-AGGREGATE-HISTORY-SHA", history, r2._lawful_events(), {}))
        vectors.append((
            "MUT-R3-AGGREGATE-DOCUMENT-PROPOSITION", copy.deepcopy(self.policy),
            r2._lawful_events(), {"AGENTS.md": "Fable authors the bounded design."},
        ))
        split = copy.deepcopy(self.policy)
        split["successor"]["green_builder"] = "fable"
        split_events = r2._lawful_events()
        split_events[-1][1]["builder_seat"] = "fable"
        vectors.append(("MUT-R3-AGGREGATE-BUILDER-SEAT-SPLIT", split, split_events, {}))

        predecessor = self._demand("closed_policy_rows_check")
        document_scan = self._demand("exemption_aware_scan")
        for mutant_id, policy, _events, documents in vectors:
            if mutant_id == "MUT-R3-AGGREGATE-DOCUMENT-PROPOSITION":
                killed = bool(document_scan(policy, "AGENTS.md", documents["AGENTS.md"]))
            else:
                killed = bool(predecessor(policy))
            self._kill(mutant_id, killed, f"predecessor law accepted {mutant_id}")
        self._assert_mutants("aggregate")

        aggregate = self._demand("validate_process_governance")
        self._lawful_control(
            "aggregate", aggregate, copy.deepcopy(self.policy),
            r2._lawful_identity_records(), r2._lawful_events(), {},
        )
        escaped = []
        for mutant_id, policy, events, documents in vectors:
            raised, violations = safe_call(
                aggregate, policy, r2._lawful_identity_records(), events, documents,
            )
            if raised or not violations:
                escaped.append((mutant_id, raised, violations))
        self._red(
            not escaped,
            f"aggregate omitted predecessor policy/document/seat laws: {escaped}",
        )

    def test_malformed_and_unhashable_policy_values_are_total(self) -> None:
        """PDC-R2-CODE-FINAL-003 + PDC-R2-FINAL-ADV-004."""
        vectors = []
        successor = copy.deepcopy(self.policy)
        successor["successor"]["max_conformance_checks"] = "one"
        vectors.append(("MUT-R3-TOTALITY-SUCCESSOR-SCALAR", successor))
        dispatch = copy.deepcopy(self.policy)
        dispatch["successor"]["dispatch_schema"]["allowed_keys"] = [["builder_seat"]]
        vectors.append(("MUT-R3-TOTALITY-DISPATCH-ROSTER", dispatch))
        document = copy.deepcopy(self.policy)
        document["currency"]["documents"][0]["path"] = ["AGENTS.md"]
        vectors.append(("MUT-R3-TOTALITY-DOCUMENT-PATH", document))
        family = copy.deepcopy(self.policy)
        family["review_families"][0]["family_id"] = ["semantic-tdd-conductor-skill"]
        vectors.append(("MUT-R3-TOTALITY-FAMILY-ID", family))
        transition = copy.deepcopy(self.policy)
        transition["transitions"][0]["finding_id"] = {"id": "SKILL-R1-001"}
        vectors.append(("MUT-R3-TOTALITY-TRANSITION-ID", transition))

        for mutant_id, policy in vectors:
            self._kill(
                mutant_id, bool(reference_total_policy_shape(policy)),
                f"total reference accepted malformed vector {mutant_id}",
            )
        self._assert_mutants("totality")

        aggregate = self._demand("validate_process_governance")
        self._lawful_control(
            "totality", aggregate, copy.deepcopy(self.policy),
            r2._lawful_identity_records(), r2._lawful_events(), {},
        )
        failures = []
        for mutant_id, policy in vectors:
            raised, violations = safe_call(
                aggregate, policy, r2._lawful_identity_records(), r2._lawful_events(), {},
            )
            if raised or not violations:
                failures.append((mutant_id, raised, violations))
        self._red(
            not failures,
            f"malformed/unhashable policy values did not return deterministic violations: {failures}",
        )

    def test_identity_schema_is_exact_immutable_and_policy_independent(self) -> None:
        """PDC-R2-FINAL-ADV-003."""
        vectors = []
        dropped = copy.deepcopy(EXACT_IDENTITY_SCHEMA)
        dropped["required_keys"].remove("green_builder_session")
        vectors.append(("MUT-R3-IDENTITY-SCHEMA-REQUIRED-KEY-DROP", dropped, False))
        permissive = copy.deepcopy(EXACT_IDENTITY_SCHEMA)
        permissive["allow_unknown_keys"] = True
        vectors.append(("MUT-R3-IDENTITY-SCHEMA-ALLOW-UNKNOWNS", permissive, False))
        with_unknown = copy.deepcopy(permissive)
        vectors.append(("MUT-R3-IDENTITY-SCHEMA-UNKNOWN-FIELD", with_unknown, True))

        for mutant_id, schema, _add_unknown in vectors:
            self._kill(
                mutant_id, bool(reference_identity_schema_check(schema)),
                f"mutable schema accepted: {schema}",
            )
        self._assert_mutants("identity_schema")

        identity = self._demand("closed_identity_chain_check")
        self._lawful_control(
            "identity_schema", identity, r2._lawful_identity_records(),
            copy.deepcopy(EXACT_IDENTITY_SCHEMA), self.policy["roles"],
        )
        escaped = []
        for mutant_id, schema, add_unknown in vectors:
            records = r2._lawful_identity_records()
            if add_unknown:
                for record in records:
                    record["approval_session"] = "codex-approval-r3"
            raised, violations = safe_call(identity, records, schema, self.policy["roles"])
            if raised or not violations:
                escaped.append((mutant_id, raised, violations))
        self._red(
            not escaped,
            f"identity authority trusted a mutable policy schema: {escaped}",
        )

    def test_authority_scan_rejects_confusables_and_duty_synonyms(self) -> None:
        """PDC-R2-FINAL-ADV-005."""
        vectors = (
            ("MUT-R3-AUTHORITY-CYRILLIC-FABLE", "Fаble approves the patch."),
            ("MUT-R3-AUTHORITY-APPROVES", "Fable approves the patch."),
            ("MUT-R3-AUTHORITY-REVIEWS", "Fable reviews the finished patch."),
            ("MUT-R3-AUTHORITY-MERGES", "Fable merges the branch."),
            ("MUT-R3-AUTHORITY-OWNS", "Fable owns integration and lifecycle authority."),
            ("MUT-R3-AUTHORITY-PASSIVE-OWNERSHIP", "Approval is owned by Fable."),
        )
        for mutant_id, text in vectors:
            self._kill(mutant_id, bool(reference_authority_check(text)), text)
        self._assert_mutants("authority")
        self._red(
            not reference_authority_check("Fable authors the bounded scratch design."),
            "lawful Fable design authorship was rejected by the reference law",
        )

        production = self._demand("role_authority_text_check")
        escaped = [
            mutant_id for mutant_id, text in vectors
            if not safe_call(production, text, False)[1]
        ]
        lawful = safe_call(production, "Fable authors the bounded scratch design.", False)[1]
        self._red(
            not escaped and not lawful,
            f"confusable/duty-synonym scan mismatch: escaped={escaped}; lawful={lawful}",
        )

    def test_history_exemption_is_path_section_and_hash_bound(self) -> None:
        """PDC-R2-CODE-FINAL-004 + PDC-R2-FINAL-ADV-006."""
        document = (ROOT / HISTORY_PATH).read_text(encoding="utf-8")
        section_text = extract_history_section(document)
        self._red(
            hashlib.sha256(section_text.encode("utf-8")).hexdigest() == HISTORY_SECTION_SHA256,
            "authorized historical section hash drifted",
        )
        self._red(
            reference_contextual_history_check(HISTORY_PATH, HISTORY_SECTION, section_text) == [],
            "exact authorized historical section was not exempted",
        )
        vectors = (
            ("MUT-R3-HISTORY-WRONG-PATH", "skills/example/SKILL.md", HISTORY_SECTION, section_text),
            ("MUT-R3-HISTORY-WRONG-SECTION", HISTORY_PATH, "active-law", section_text),
            ("MUT-R3-HISTORY-HASH-DRIFT", HISTORY_PATH, HISTORY_SECTION, section_text + " "),
            ("MUT-R3-HISTORY-PORTABLE-COPY", "docs/plans/ACTIVE.md", "rev-16-routing-narrative", section_text),
        )
        for mutant_id, path, section, text in vectors:
            self._kill(
                mutant_id, bool(reference_contextual_history_check(path, section, text)),
                f"history exemption escaped tuple {(path, section)!r}",
            )
        self._assert_mutants("history")

        contextual = self._demand("contextual_role_authority_text_check")
        exact = safe_call(contextual, HISTORY_PATH, HISTORY_SECTION, section_text, False)[1]
        escaped = [
            mutant_id for mutant_id, path, section, text in vectors
            if not safe_call(contextual, path, section, text, path.startswith("skills/"))[1]
        ]
        self._red(
            not exact and not escaped,
            f"history exemption is not exact path/section/hash bound: exact={exact}; escaped={escaped}",
        )

    def test_canonical_policy_paths_reject_every_control_character(self) -> None:
        """PDC-R2-FINAL-ADV-007."""
        controls = [chr(codepoint) for codepoint in range(0x20)] + [chr(0x7F)] + [
            chr(codepoint) for codepoint in range(0x80, 0xA0)
        ]
        self._red(
            all(reference_path_check(f"docs/plans/a{control}b.md") for control in controls),
            "reference path law did not reject every Unicode Cc control",
        )
        for mutant_id, control in (
            ("MUT-R3-PATH-NUL", "\x00"),
            ("MUT-R3-PATH-NEWLINE", "\n"),
            ("MUT-R3-PATH-DEL", "\x7f"),
        ):
            self._kill(
                mutant_id, bool(reference_path_check(f"docs/plans/a{control}b.md")),
                f"control U+{ord(control):04X} survived",
            )
        self._assert_mutants("paths")

        policy_check = self._demand("closed_process_policy_check")
        self._lawful_control("paths", policy_check, copy.deepcopy(self.policy))
        escaped = []
        for control in controls:
            attack = copy.deepcopy(self.policy)
            attack["currency"]["postreview_documents"][0]["path"] = (
                f"docs/plans/a{control}b.md"
            )
            raised, violations = safe_call(policy_check, attack)
            if raised or not violations:
                escaped.append(f"U+{ord(control):04X}")
        self._red(
            not escaped,
            f"canonical policy paths accepted control characters: {escaped}",
        )


if __name__ == "__main__":
    unittest.main()

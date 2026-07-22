"""Process-doc currency + adoption RED — the 2026-07-22 operator law as executable law.

Authored by the fresh exact `claude-fable-5` DESIGN + RED author lane (charter
`fable-process-currentness-design-red-charter-r1`, sha256 `a58858d1…f21d6cf`).
`/root` conducts; a DIFFERENT fresh Opus lane builds GREEN; Codex reviews.

This module is written BEFORE `contracts/process_docs_currency_policy.toml`
exists. While that policy is absent, EVERY case fails in setUp with the exact
bootstrap fingerprint `PROCESS-DOC-CURRENCY-RED: policy absent`. Once the GREEN
builder lands the policy plus the adoption edits (design:
`scratchpad/active/process/process-doc-currentness-adoption-design-r1.md` §8),
each case runs its real closed-rule body: parse the policy, evaluate the live
governed documents and skill references, simulate renamed/versioned review
lineages, validate transition totality and exact classes, reject reviewer/
builder RED ownership, and reject conformance runs without an immediate
distinct Opus GREEN successor. History stays byte-history: exempted, never
rewritten.
"""
from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11 (local): pinned backport, same law as test_doc_authority
    import tomli as tomllib


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "scripts").is_dir() and (parent / "tests").is_dir():
            return parent
    raise RuntimeError("repo root not found")


ROOT = _repo_root()
POLICY_PATH = ROOT / "contracts" / "process_docs_currency_policy.toml"
FINGERPRINT = "PROCESS-DOC-CURRENCY-RED: policy absent"

# --- anchored law (sealed 2026-07-22; the policy must agree with every anchor) ------

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

REQUIRED_TRANSITIONS = {
    "SKILL-R1-001": ("PROBEABLE", "RED_REQUIRED", "AFTER_LANE_C"),
    "SKILL-R1-002": ("PROBEABLE", "RED_REQUIRED", "AFTER_LANE_C"),
    "SKILL-R1-003": ("PROBEABLE", "RED_REQUIRED", "AFTER_LANE_C"),
    "SKILL-R1-004": ("PROBEABLE", "RED_REQUIRED", "AFTER_LANE_C"),
    "SKILL-R1-005": ("PROBEABLE", "RED_REQUIRED", "AFTER_LANE_C"),
    "SKILL-R1-006": ("PROBEABLE", "RED_REQUIRED", "AFTER_LANE_C"),
    "PROC-ROLE-001": ("PROBEABLE", "RED_AUTHORED", "IMMEDIATE"),
    "PROC-LINEAGE-001": ("PROBEABLE", "RED_AUTHORED", "IMMEDIATE"),
    "PROC-LOOP-001": ("PROBEABLE", "RED_AUTHORED", "IMMEDIATE"),
    "PROC-TRANSITION-001": ("PROBEABLE", "RED_AUTHORED", "IMMEDIATE"),
    "PROC-RED-OWNER-001": ("PROBEABLE", "RED_AUTHORED", "IMMEDIATE"),
    "PROC-BUILDER-001": ("PROBEABLE", "RED_AUTHORED", "IMMEDIATE"),
}

SKILL_FINDING_IDS = tuple(f for f in REQUIRED_TRANSITIONS if f.startswith("SKILL-R1-"))
PROC_FINDING_IDS = tuple(f for f in REQUIRED_TRANSITIONS if f.startswith("PROC-"))

RED_CLASS_PREFIX = "tests.contracts.test_process_docs_currency.ProcessDocsCurrencyRed."

PROC_EVIDENCE_CASES = {
    "PROC-ROLE-001": "test_live_docs_forbid_stale_conductor_patterns",
    "PROC-LINEAGE-001": "test_rename_and_correction_preserve_terminal_lineage",
    "PROC-LOOP-001": "test_third_prose_review_rejected",
    "PROC-TRANSITION-001": "test_transition_totality_exact_twelve_findings",
    "PROC-RED-OWNER-001": "test_reviewer_cannot_author_red",
    "PROC-BUILDER-001": "test_conformance_requires_immediate_distinct_opus_successor",
}

GOVERNED_DOCS = (
    "AGENTS.md",
    "docs/plans/ACTIVE.md",
    "docs/plans/handoff/HANDOFF.md",
    "docs/history/PLAN-LEDGER.md",
    "skills/design-language-tdd/SKILL.md",
    "skills/design-language-tdd/references/prove-theme.md",
    "skills/design-language-tdd/references/add-component.md",
)
SKILL_DOCS = GOVERNED_DOCS[4:]
LEDGER_PATH = "docs/history/PLAN-LEDGER.md"

ADOPTION_SHA256 = {
    "AGENTS.md": "38a823c52d8fae295980deea08bacf00f4883d336b0bb014d15cfb4a4934845e",
    "docs/plans/ACTIVE.md": "199cd651da3915696a924479acd0f4ecb6a43b52f20dfae05cf98aef60b1db4f",
}

LEDGER_PREFIX_SHA = "83b351f84fcc4668088bae0e7adf2a103515e03c3afc478a2d9072b890359a44"
LEDGER_PREFIX_BYTES = 7988
LEDGER_HEADING = (
    "## 2026-07-22 — operator post-review execution law + `/root`-conductor adoption"
)

AGENTS_POINTER = "are governed by `AGENTS.md`"

REQUIRED_PROPOSITIONS = {
    "AGENTS.md": (
        "`/root` is the CONDUCTOR",
        "Fable 5 is the delegated DESIGN + RED author",
        "Opus is the delegated GREEN builder",
        "Codex is the independent review authority",
        "A document correction never resets the design family's review count",
        "`FindingToEvidenceTransition`",
        "the reviewer may not become the RED author",
        "No review-of-review",
        "dispatches a different Opus builder for GREEN",
    ),
    "docs/plans/ACTIVE.md": (
        "`/root` conducts, dispatches, verifies, integrates, commits",
        "typed `FindingToEvidenceTransition` rows",
        "No review-of-review",
        "one bounded RED-conformance check is followed immediately by a different "
        "Opus GREEN builder",
    ),
    "docs/plans/handoff/HANDOFF.md": ("`/root` conducts", AGENTS_POINTER),
    "docs/history/PLAN-LEDGER.md": (LEDGER_HEADING,),
    "skills/design-language-tdd/SKILL.md": (AGENTS_POINTER,),
    "skills/design-language-tdd/references/prove-theme.md": (AGENTS_POINTER,),
    "skills/design-language-tdd/references/add-component.md": (AGENTS_POINTER,),
}

STALE_CONDUCTOR_PATTERNS = (
    r"(?i)\bfable(?:\s+5)?\s+conducts\b",
    r"(?i)\bfable(?:\s+5)?\s+is\s+the\s+conductor\b",
    r"(?i)\bfable-as-conductor\b",
)

SKILL_LIFECYCLE_PATTERNS = (
    r"(?i)commit\s+(?:only\s+)?when\s+green\s*\+\s*codex\s+agrees",
    r"(?im)^##\s+commit\s+discipline\b",
    r"(?im)^##\s+the\s+per-slice\s+sop\b",
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

SKILL_FAMILY_FINDINGS = list(SKILL_FINDING_IDS)


# --- deterministic validators (pure; consumed only with policy data + explicit input) --


def scan_document(policy: dict, rel_path: str, text: str) -> list[str]:
    """Apply the policy's closed currency rules to one document's text.

    Historical records are EXEMPT (never pattern-scanned — history is never
    rewritten); every other governed document must match no forbidden pattern
    and carry every required proposition. An undeclared path is a violation.
    """
    currency = policy["currency"]
    rows = {d["path"]: d for d in currency["documents"]}
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


def lineage_state(events, lineage: dict) -> dict:
    """Fold a design-family event log under the policy lineage rules.

    PROSE_REVIEW advances the count and records terminal verdicts; every
    identity-preserving event (correction/rename/version/successor packet)
    changes NOTHING; an unknown event kind fails closed.
    """
    identity = set(lineage["identity_preserving_events"])
    used = 0
    terminal = None
    for kind, data in events:
        if kind == "PROSE_REVIEW":
            used += 1
            if data.get("verdict") in lineage["terminal_verdicts"]:
                terminal = data["verdict"]
        elif kind in identity:
            continue
        else:
            raise ValueError(f"unknown lineage event: {kind}")
    return {"prose_reviews_used": used, "terminal_verdict": terminal}


def may_schedule_prose_review(state: dict, lineage: dict) -> bool:
    """After ANY terminal verdict findings move to typed executable evidence —
    never another prose round; the cap is an absolute stop, not an entitlement."""
    if state["terminal_verdict"] is not None:
        return False
    return state["prose_reviews_used"] < lineage["prose_review_cap"]


def check_separation(record: dict, policy: dict) -> list[str]:
    """Author/reviewer/builder separation over one run record (seats + sessions)."""
    roles = policy["roles"]
    violations = []
    if record["red_author_seat"] != roles["design_red_author"]:
        violations.append(
            "the governing RED author seat must be the delegated DESIGN + RED author"
        )
    if (
        record["red_author_seat"] == roles["reviewer"]
        or record["red_author_session"] == record["reviewer_session"]
    ):
        violations.append("the reviewer may not author the RED that closes its own finding")
    if record["green_builder_seat"] != roles["green_builder"]:
        violations.append("GREEN must be built by the delegated Opus builder seat")
    if record["green_builder_session"] == record["red_author_session"]:
        violations.append("the RED author may not build GREEN")
    return violations


def check_successor(events, policy: dict) -> list[str]:
    """The conformance-to-builder successor rule over an ordered lifecycle event log."""
    successor = policy["successor"]
    violations = []
    kinds = [kind for kind, _ in events]
    conformance_idx = [i for i, kind in enumerate(kinds) if kind == "CONFORMANCE_PASSED"]
    if len(conformance_idx) > successor["max_conformance_checks"]:
        violations.append("more than the one bounded RED-conformance check")
    if "RED_ACCEPTED" in kinds:
        accepted = kinds.index("RED_ACCEPTED")
        for kind in kinds[accepted + 1 :]:
            if kind in successor["forbidden_after_red_accepted"]:
                violations.append(f"forbidden review event after accepted RED: {kind}")
    if conformance_idx:
        last = conformance_idx[-1]
        if last + 1 >= len(events):
            violations.append("no GREEN successor after the bounded conformance check")
        else:
            kind, data = events[last + 1]
            if kind != successor["required_next_event"]:
                violations.append(
                    "the event after the conformance check must be "
                    f"{successor['required_next_event']}, got {kind}"
                )
            else:
                if data.get("builder_seat") != successor["green_builder"]:
                    violations.append("the GREEN successor must be the Opus builder seat")
                if data.get("builder_session") == data.get("red_author_session"):
                    violations.append(
                        "the GREEN successor must be a session distinct from the RED author"
                    )
    return violations


class ProcessDocsCurrencyRed(unittest.TestCase):
    """20 cases; each fails with the bootstrap fingerprint until GREEN lands the policy."""

    maxDiff = None

    def setUp(self) -> None:
        if not POLICY_PATH.is_file():
            self.fail(FINGERPRINT)
        self.policy = tomllib.loads(POLICY_PATH.read_text(encoding="utf-8"))

    # --- policy schema -----------------------------------------------------------

    def test_policy_schema_is_closed(self) -> None:
        self.assertEqual(
            set(self.policy),
            {
                "meta", "roles", "separation", "successor", "lineage",
                "review_families", "transition_classes", "transitions", "currency",
            },
        )
        meta = self.policy["meta"]
        self.assertEqual(meta["contract_id"], "ProcessDocsCurrencyPolicy")
        self.assertEqual(meta["schema_version"], 1)
        self.assertEqual(meta["ratified"], "2026-07-22")

    def test_transition_classes_are_the_agents_enum(self) -> None:
        self.assertEqual(self.policy["transition_classes"]["classes"], CLASSES)

    def test_roles_and_seats_are_the_ratified_law(self) -> None:
        self.assertEqual(self.policy["roles"], SEATS)
        separation = self.policy["separation"]
        self.assertIs(separation["reviewer_may_author_red"], False)
        self.assertIs(separation["red_author_may_build_green"], False)
        self.assertIs(separation["author_approves_own_artifact"], False)
        self.assertEqual(self.policy["lineage"]["prose_review_cap"], 2)

    # --- typed transitions -------------------------------------------------------

    def test_transition_totality_exact_twelve_findings(self) -> None:
        ids = [row["finding_id"] for row in self.policy["transitions"]]
        self.assertEqual(sorted(ids), sorted(REQUIRED_TRANSITIONS))
        self.assertEqual(len(ids), 12)

    def test_each_finding_has_exactly_one_class(self) -> None:
        seen: dict[str, str] = {}
        for row in self.policy["transitions"]:
            finding_id = row["finding_id"]
            transition_class = row["transition_class"]
            self.assertIsInstance(
                transition_class, str, f"{finding_id}: class must be ONE string"
            )
            self.assertIn(transition_class, CLASSES, finding_id)
            self.assertNotIn(
                finding_id, seen, f"{finding_id}: appears twice (a finding with two classes)"
            )
            seen[finding_id] = transition_class
        for finding_id, (expected_class, _, _) in REQUIRED_TRANSITIONS.items():
            self.assertEqual(seen.get(finding_id), expected_class, finding_id)

    def test_skill_findings_are_red_required_after_lane_c(self) -> None:
        rows = {row["finding_id"]: row for row in self.policy["transitions"]}
        for finding_id in SKILL_FINDING_IDS:
            row = rows.get(finding_id)
            self.assertIsNotNone(row, finding_id)
            self.assertEqual(row["status"], "RED_REQUIRED", finding_id)
            self.assertEqual(row["dependency"], "AFTER_LANE_C", finding_id)
            self.assertEqual(row["source_review"], R2_REVIEW, finding_id)

    def test_proc_findings_are_red_authored_immediate(self) -> None:
        rows = {row["finding_id"]: row for row in self.policy["transitions"]}
        for finding_id in PROC_FINDING_IDS:
            row = rows.get(finding_id)
            self.assertIsNotNone(row, finding_id)
            self.assertEqual(row["status"], "RED_AUTHORED", finding_id)
            self.assertEqual(row["dependency"], "IMMEDIATE", finding_id)
            self.assertEqual(row["owner_seat"], SEATS["design_red_author"], finding_id)

    def test_proc_transitions_bind_to_real_red_cases(self) -> None:
        rows = {row["finding_id"]: row for row in self.policy["transitions"]}
        for finding_id, case_name in PROC_EVIDENCE_CASES.items():
            row = rows.get(finding_id)
            self.assertIsNotNone(row, finding_id)
            self.assertEqual(row["evidence"], RED_CLASS_PREFIX + case_name, finding_id)
            self.assertTrue(
                callable(getattr(type(self), case_name, None)),
                f"{finding_id}: evidence case {case_name} must exist in this class",
            )

    # --- RED ownership + successor law -------------------------------------------

    def test_reviewer_cannot_author_red(self) -> None:
        lawful = {
            "red_author_seat": "fable", "red_author_session": "fable-s1",
            "reviewer_seat": "codex", "reviewer_session": "codex-s1",
            "green_builder_seat": "opus", "green_builder_session": "opus-s2",
        }
        self.assertEqual([], check_separation(lawful, self.policy))
        reviewer_owned = dict(
            lawful, red_author_seat="codex", red_author_session="codex-s1"
        )
        violations = check_separation(reviewer_owned, self.policy)
        self.assertTrue(
            any("reviewer may not author the RED" in v for v in violations), violations
        )
        self.assertTrue(
            any("DESIGN + RED author" in v for v in violations), violations
        )

    def test_red_author_cannot_build_green(self) -> None:
        opus_authors_then_builds = {
            "red_author_seat": "opus", "red_author_session": "opus-s1",
            "reviewer_seat": "codex", "reviewer_session": "codex-s1",
            "green_builder_seat": "opus", "green_builder_session": "opus-s1",
        }
        violations = check_separation(opus_authors_then_builds, self.policy)
        self.assertTrue(
            any("RED author may not build GREEN" in v for v in violations), violations
        )
        self.assertTrue(
            any("DESIGN + RED author" in v for v in violations), violations
        )
        same_session_only = {
            "red_author_seat": "fable", "red_author_session": "shared-session",
            "reviewer_seat": "codex", "reviewer_session": "codex-s1",
            "green_builder_seat": "opus", "green_builder_session": "shared-session",
        }
        self.assertTrue(
            any(
                "RED author may not build GREEN" in v
                for v in check_separation(same_session_only, self.policy)
            )
        )

    def test_conformance_requires_immediate_distinct_opus_successor(self) -> None:
        dispatch = (
            "GREEN_DISPATCH",
            {
                "builder_seat": "opus",
                "builder_session": "opus-s2",
                "red_author_session": "fable-s1",
            },
        )
        lawful = (("RED_ACCEPTED", {}), ("CONFORMANCE_PASSED", {}), dispatch)
        self.assertEqual([], check_successor(lawful, self.policy))

        no_successor = (("RED_ACCEPTED", {}), ("CONFORMANCE_PASSED", {}))
        self.assertTrue(
            any("no GREEN successor" in v for v in check_successor(no_successor, self.policy))
        )

        delayed = (
            ("RED_ACCEPTED", {}),
            ("CONFORMANCE_PASSED", {}),
            ("PROSE_REVIEW", {"verdict": "REVISE"}),
            dispatch,
        )
        delayed_violations = check_successor(delayed, self.policy)
        self.assertTrue(
            any("forbidden review event after accepted RED" in v for v in delayed_violations)
        )
        self.assertTrue(
            any("must be GREEN_DISPATCH" in v for v in delayed_violations), delayed_violations
        )

        double_conformance = (
            ("RED_ACCEPTED", {}),
            ("CONFORMANCE_PASSED", {}),
            ("CONFORMANCE_PASSED", {}),
            dispatch,
        )
        self.assertTrue(
            any(
                "more than the one bounded" in v
                for v in check_successor(double_conformance, self.policy)
            )
        )

        wrong_seat = (
            ("RED_ACCEPTED", {}),
            ("CONFORMANCE_PASSED", {}),
            (
                "GREEN_DISPATCH",
                {
                    "builder_seat": "fable",
                    "builder_session": "fable-s9",
                    "red_author_session": "fable-s1",
                },
            ),
        )
        self.assertTrue(
            any(
                "must be the Opus builder seat" in v
                for v in check_successor(wrong_seat, self.policy)
            )
        )

        same_session = (
            ("RED_ACCEPTED", {}),
            ("CONFORMANCE_PASSED", {}),
            (
                "GREEN_DISPATCH",
                {
                    "builder_seat": "opus",
                    "builder_session": "fable-s1",
                    "red_author_session": "fable-s1",
                },
            ),
        )
        self.assertTrue(
            any(
                "distinct from the RED author" in v
                for v in check_successor(same_session, self.policy)
            )
        )

    # --- review lineage ----------------------------------------------------------

    def test_rename_and_correction_preserve_terminal_lineage(self) -> None:
        lineage = self.policy["lineage"]
        self.assertEqual(
            lineage["identity_preserving_events"],
            ["CORRECTION", "RENAME", "VERSION_BUMP", "SUCCESSOR_PACKET"],
        )
        self.assertEqual(lineage["reset_events"], [])
        renamed_family = (
            ("PROSE_REVIEW", {"verdict": "REVISE"}),
            ("CORRECTION", {"note": "corrected bytes"}),
            ("RENAME", {"from": "design-r1.md", "to": "design-r1-corrected.md"}),
            ("VERSION_BUMP", {"to": "r2"}),
            ("SUCCESSOR_PACKET", {}),
        )
        state = lineage_state(renamed_family, lineage)
        self.assertEqual(
            state, {"prose_reviews_used": 1, "terminal_verdict": "REVISE"},
            "a corrected/renamed/versioned family keeps its terminal count",
        )
        self.assertFalse(
            may_schedule_prose_review(state, lineage),
            "a rename or correction never reopens prose review after a terminal verdict",
        )
        with self.assertRaises(ValueError):
            lineage_state((("HISTORY_RESET", {}),), lineage)

    def test_third_prose_review_rejected(self) -> None:
        families = {f["family_id"]: f for f in self.policy["review_families"]}
        skill = families.get("semantic-tdd-conductor-skill")
        self.assertIsNotNone(skill)
        self.assertEqual(skill["prose_reviews_used"], 1)
        self.assertEqual(skill["terminal_verdict_token"], "SKILL-DESIGN-VERDICT: REVISE")
        self.assertEqual(skill["findings"], SKILL_FAMILY_FINDINGS)
        self.assertEqual(skill["terminal_review_doc"], R2_REVIEW)
        self.assertIs(skill["another_prose_review_authorized"], False)
        system = families.get("build-lane-contract-system")
        self.assertIsNotNone(system)
        self.assertEqual(system["prose_reviews_used"], 2)
        self.assertIs(system["another_prose_review_authorized"], False)
        lineage = self.policy["lineage"]
        self.assertEqual(system["prose_reviews_used"], lineage["prose_review_cap"])
        two_revise = (
            ("PROSE_REVIEW", {"verdict": "REVISE"}),
            ("CORRECTION", {}),
            ("PROSE_REVIEW", {"verdict": "REVISE"}),
        )
        state = lineage_state(two_revise, lineage)
        self.assertEqual(state["prose_reviews_used"], 2)
        self.assertFalse(
            may_schedule_prose_review(state, lineage),
            "a third prose review may never be scheduled",
        )

    # --- live document currency --------------------------------------------------

    def _document_rows(self) -> dict:
        return {d["path"]: d for d in self.policy["currency"]["documents"]}

    def test_live_docs_forbid_stale_conductor_patterns(self) -> None:
        rows = self._document_rows()
        for path in GOVERNED_DOCS:
            row = rows.get(path)
            self.assertIsNotNone(row, path)
            if row.get("historical_exempt", False):
                continue
            for pattern in STALE_CONDUCTOR_PATTERNS:
                self.assertIn(
                    pattern, row.get("forbidden_patterns", []),
                    f"{path}: the policy must forbid {pattern}",
                )
            text = (ROOT / path).read_text(encoding="utf-8")
            self.assertEqual([], scan_document(self.policy, path, text), path)
        canary = scan_document(
            self.policy,
            "docs/plans/handoff/HANDOFF.md",
            "Continuation routing: Fable conducts — authors designs and commits.",
        )
        self.assertTrue(
            any("forbidden pattern" in v for v in canary),
            "the archetypal stale-conductor sentence must be caught",
        )

    def test_authoritative_documents_enumerated_and_current(self) -> None:
        rows = self._document_rows()
        self.assertEqual(set(rows), set(GOVERNED_DOCS))
        for path, row in rows.items():
            live = ROOT / path
            self.assertTrue(live.is_file(), f"governed doc missing from disk: {path}")
            declared = row.get("required_propositions", [])
            for proposition in REQUIRED_PROPOSITIONS[path]:
                self.assertIn(
                    proposition, declared,
                    f"{path}: the policy must require {proposition!r}",
                )
            text = live.read_text(encoding="utf-8")
            for proposition in declared:
                self.assertIn(
                    proposition, text,
                    f"{path}: live doc lost required proposition {proposition!r}",
                )

    def test_adoption_pins_match_sealed_authority_bytes(self) -> None:
        rows = self._document_rows()
        for path, pin in ADOPTION_SHA256.items():
            row = rows.get(path)
            self.assertIsNotNone(row, path)
            self.assertEqual(row.get("adoption_sha256"), pin, path)
            live_sha = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            self.assertEqual(
                live_sha, pin,
                f"{path}: live bytes must equal the operator-amended landing authority",
            )

    # --- history: exempt, never rewritten ----------------------------------------

    def test_plan_ledger_prefix_immutable_and_adoption_row_appended(self) -> None:
        row = self._document_rows().get(LEDGER_PATH)
        self.assertIsNotNone(row, LEDGER_PATH)
        self.assertIs(row.get("historical_exempt"), True)
        self.assertEqual(row.get("immutable_prefix_sha256"), LEDGER_PREFIX_SHA)
        self.assertEqual(row.get("immutable_prefix_bytes"), LEDGER_PREFIX_BYTES)
        raw = (ROOT / LEDGER_PATH).read_bytes()
        self.assertGreaterEqual(len(raw), LEDGER_PREFIX_BYTES)
        self.assertEqual(
            hashlib.sha256(raw[:LEDGER_PREFIX_BYTES]).hexdigest(), LEDGER_PREFIX_SHA,
            "history was rewritten — the ledger accepts appends only",
        )
        self.assertIn(
            LEDGER_HEADING, raw.decode("utf-8"),
            "the 2026-07-22 adoption row must be APPENDED to the ledger",
        )

    def test_historical_records_exempt_not_rewritten(self) -> None:
        currency = self.policy["currency"]
        self.assertEqual(currency["historical_exempt_prefixes"], ["docs/history/"])
        stale = "Fable conducts everything and resets review history."
        self.assertEqual(
            [], scan_document(self.policy, LEDGER_PATH, stale),
            "historical records are EXEMPT from rewriting, never scanned",
        )
        flagged = scan_document(self.policy, "docs/plans/handoff/HANDOFF.md", stale)
        self.assertTrue(
            any("forbidden pattern" in v for v in flagged),
            "the same stale text in a LIVE doc must be flagged",
        )
        records = {r["path"]: r for r in currency["historical_records"]}
        for path, sha in HISTORICAL_RECORD_IDS.items():
            row = records.get(path)
            self.assertIsNotNone(row, path)
            self.assertEqual(row.get("sha256"), sha, path)
            self.assertEqual(row.get("enforcement"), "identity", path)
        for record in currency["historical_records"]:
            self.assertTrue(record.get("path"), "historical record row needs a path")
            self.assertRegex(record.get("sha256", ""), r"^[0-9a-f]{64}$", record["path"])
            self.assertIn(record.get("enforcement"), ("identity", "prefix"), record["path"])

    # --- the design-language skill owns no competing lifecycle --------------------

    def test_skill_owns_no_competing_lifecycle(self) -> None:
        rows = self._document_rows()
        for path in SKILL_DOCS:
            row = rows.get(path)
            self.assertIsNotNone(row, path)
            for pattern in SKILL_LIFECYCLE_PATTERNS:
                self.assertIn(
                    pattern, row.get("forbidden_patterns", []),
                    f"{path}: the policy must forbid {pattern}",
                )
            text = (ROOT / path).read_text(encoding="utf-8")
            self.assertEqual([], scan_document(self.policy, path, text), path)
        canary_text = (
            "## The per-slice SOP (every slice, in order)\n"
            "6. commit only when green + codex agrees.\n"
            "## Commit discipline (this repo)\n"
        )
        hits = scan_document(self.policy, SKILL_DOCS[0], canary_text)
        matched = [v for v in hits if "forbidden pattern" in v]
        self.assertGreaterEqual(
            len(matched), 3,
            f"all three competing-lifecycle canaries must be caught, got: {matched}",
        )

    def test_skill_files_point_to_agents_authority(self) -> None:
        for path in SKILL_DOCS:
            text = (ROOT / path).read_text(encoding="utf-8")
            self.assertIn(
                AGENTS_POINTER, text,
                f"{path}: must point lifecycle authority at AGENTS.md",
            )
        skill_md = (ROOT / SKILL_DOCS[0]).read_text(encoding="utf-8").lower()
        self.assertIn(
            "codex", skill_md,
            "SKILL.md keeps its codex review token (test_skill_structure compatibility)",
        )


if __name__ == "__main__":
    unittest.main()

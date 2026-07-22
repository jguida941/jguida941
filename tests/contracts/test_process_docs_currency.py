"""Process-docs currency guard (operator-directed): SKILL.md + AGENTS.md must teach the LIVE
process, or an AI agent cannot drive the system. Mirrors the kernel docs-currency law.

RED r3 (convergence round). Producing model: Fable 5 (claude-fable-5) — execution metadata only.
This revision closes r2 review findings 3 and 8 (`scratchpad/work/codex-org-red-r2-review-
2026-07-16.md`): every required concept id is bound to its CANONICAL kind and exact
projection-owner rule, and SOP-BLOCK markers must wrap the canonical NAMED section (a marker
before an unrelated "Cooking" heading now reddens). The seed class below is the landed
admission witness and is unchanged (never weakened).

Conductor-authored RED: the seed fails today because `skills/design-language-tdd/` is stale.
CR-10..CR-13 stay RED until the L4 docs-currency slice lands (SEQUENCED AFTER the W7 role
registry). Hostile probes are their own discoverable tests (green today).
"""

import re
import unittest
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11 (local): pinned backport in requirements.txt
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / "skills" / "design-language-tdd"
AGENTS = ROOT / "AGENTS.md"
HANDOFF = ROOT / "docs" / "plans" / "handoff" / "HANDOFF.md"
POLICY = ROOT / "contracts" / "process_docs_currency_policy.toml"

# Stale claims that must NOT survive anywhere in the skill (each is superseded by the live SOP).
STALE_TOKENS = [
    "self-demonstrating design system",   # the product is the universal compiler, not this
    "headless proof is deferred",         # MF1 Chrome-headless is binding now
    "deferred R4 aspect",                 # same
]
# The two-arg bootstrap form is non-functional (gate() returns admit=False without --expect).
BOOTSTRAP_TWO_ARG = re.compile(r'bootstrap_red_ref\s+"[^"]+"\s+"[^"]+"\s*(?:`|$|\n)')

# Live-process concepts the skill MUST teach (name, or a SOP-POINTER to AGENTS.md).
REQUIRED_CONCEPTS = [
    "13-step",                 # the full slice ritual
    "DESIGN-VERDICT",          # the three-gate cadence
    "ADVERSARIAL-VERDICT",
    "build lane",              # Opus-builds / Codex-reviews routing
    "Mode C",                  # the reference-capture lane
    "convergence",             # the review convergence law
    "MF1",                     # binding Chrome-headless receipts
]


def _skill_text() -> str:
    parts = []
    for md in sorted(SKILL_DIR.rglob("*.md")):
        parts.append(md.read_text(encoding="utf-8"))
    return "\n".join(parts)


class ProcessDocsCurrency(unittest.TestCase):
    def test_skill_dir_exists(self):
        self.assertTrue(SKILL_DIR.is_dir(), "the design-language-tdd skill must exist")

    def test_no_stale_tokens_in_skill(self):
        text = _skill_text().lower()
        found = [t for t in STALE_TOKENS if t.lower() in text]
        self.assertEqual(found, [], f"skill still teaches superseded claims: {found}")

    def test_no_nonfunctional_two_arg_bootstrap_example(self):
        text = _skill_text()
        hits = BOOTSTRAP_TWO_ARG.findall(text)
        # a two-arg bootstrap example with no --expect nearby is the non-functional form
        offenders = [h for h in hits if "--expect" not in text[text.find(h):text.find(h) + 200]]
        self.assertEqual(offenders, [], "skill prints the non-functional two-arg bootstrap command")

    def test_skill_teaches_live_process(self):
        text = _skill_text()
        missing = [c for c in REQUIRED_CONCEPTS if c.lower() not in text.lower()]
        self.assertEqual(missing, [], f"skill omits live-process concepts (or SOP-POINTERs): {missing}")

    def test_skill_routes_to_plan_of_record_and_sop(self):
        text = _skill_text()
        self.assertIn("docs/plans/ACTIVE.md", text, "skill must route to the plan-of-record")
        self.assertIn("AGENTS.md", text, "skill must route to the SOP (AGENTS.md)")


# --- CR-10..CR-13 : docs-currency convergence upgrades (packet-bound, RED-first) ---------
# Authored under the org packets against `w3c-org-rootwide-design.md` rev 2 + the r3 design
# delta. These four upgrade the seed guard above to the block-projection / governed-routing /
# policy-owner forms. They stay RED until the L4 docs-currency slice lands (after the W7 role
# registry): the conductor adds the SOP-BLOCK markers to AGENTS.md, the SOP-POINTER lines to
# HANDOFF.md, retargets the step-13 routing to `dev/reports/`, and writes
# `contracts/process_docs_currency_policy.toml`.

# Stable block-IDs for each canonical AGENTS.md-owned section (the marker vocabulary the L4
# edit stamps; HANDOFF pointers and these must agree).
REQUIRED_SOP_BLOCKS = (
    "thirteen-step-ritual",
    "three-verdicts",
    "review-convergence-law",
    "mf1-receipts",
    "org-shape-law",
    "failure-ratchet-exception",
    "mode-c-reference-lane",
    "backup-before-transform",
)
# The reentry-critical blocks HANDOFF.md must point to (a subset; the conductor may add more).
REQUIRED_HANDOFF_POINTERS = ("thirteen-step-ritual", "three-verdicts", "review-convergence-law")

BLOCK_RE = re.compile(r"<!--\s*SOP-BLOCK:\s*([a-z0-9-]+)\s*-->")
POINTER_RE = re.compile(r"SOP-POINTER:\s*([a-z0-9-]+)")

# --- r3 strengthening (r2 finding 8): a marker must bind the canonical NAMED section --------
# Keyword witnesses for each canonical block: the attached heading+body must carry at least one
# (case-insensitive). A marker wrapping unrelated prose (the "Cooking" case) reddens.
CANONICAL_BLOCK_KEYWORDS = {
    "thirteen-step-ritual": ("13-step", "13 step", "thirteen"),
    "three-verdicts": ("verdict",),
    "review-convergence-law": ("convergence",),
    "mf1-receipts": ("mf1", "chrome-headless"),
    "org-shape-law": ("shape", "organization"),
    "failure-ratchet-exception": ("ratchet",),
    "mode-c-reference-lane": ("mode c", "reference"),
    "backup-before-transform": ("backup",),
}

# --- r3 strengthening (r2 finding 3): closed concept vocabulary + CANONICAL bindings --------
CLOSED_CONCEPT_KINDS = {"demo", "mode_ladder", "role", "sop_process"}
REQUIRED_CONCEPT_IDS = {
    "thirteen-step-ritual", "three-verdicts", "review-convergence-law", "mf1-receipts",
    "org-shape-law", "failure-ratchet-exception", "mode-c-reference-lane",
    "demo-a-b", "mode-ladder", "backup-before-transform", "roles",
}
# Every required concept id is bound to its canonical KIND. A policy stamping every id
# kind="sop_process" now reddens on demo-a-b / mode-ladder / roles (r2 finding 3).
REQUIRED_CONCEPT_KINDS = {
    "thirteen-step-ritual": "sop_process",
    "three-verdicts": "sop_process",
    "review-convergence-law": "sop_process",
    "mf1-receipts": "sop_process",
    "org-shape-law": "sop_process",
    "failure-ratchet-exception": "sop_process",
    "mode-c-reference-lane": "sop_process",
    "backup-before-transform": "sop_process",
    "demo-a-b": "demo",
    "mode-ladder": "mode_ladder",
    "roles": "role",
}
# Role owners match EXACTLY (no substring laundering: "NOT contracts/role_registry.toml" reddens).
VALID_ROLE_OWNERS = {"contracts/role_registry.toml", "contracts/role_registry.*"}
# SOP-process concepts project from AGENTS.md block IDs: owner form AGENTS.md#<block-id>,
# and for a required id the fragment must equal the id itself (exact projection-owner rule).
_SOP_OWNER_RE = re.compile(r"^AGENTS\.md#([a-z0-9-]+)$")
# Interim-source timing is BEHAVIORAL (conductor decision, F5): if the registry file is ABSENT,
# every role row must carry interim_source; if it EXISTS, the field must be ABSENT (stale reddens).
REGISTRY = ROOT / "contracts" / "role_registry.toml"


def _block_sections(text: str) -> dict:
    """SOP-BLOCK id -> the REAL section text it binds: either a marker PAIR enclosing >=1
    non-marker content line, or a marker immediately preceding a heading with a body. Ids
    binding no real section are absent from the map."""
    lines = text.splitlines()
    marker_at: dict = {}
    for i, ln in enumerate(lines):
        m = BLOCK_RE.search(ln)
        if m:
            marker_at.setdefault(m.group(1), []).append(i)

    sections = {}
    for bid, locs in marker_at.items():
        if len(locs) >= 2:  # (a) pair enclosing content
            body = [lines[j] for j in range(locs[0] + 1, locs[-1])
                    if lines[j].strip() and not BLOCK_RE.search(lines[j])]
            if body:
                sections[bid] = "\n".join(body)
                continue
        j = locs[0] + 1     # (b) marker -> heading -> body
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j < len(lines) and lines[j].lstrip().startswith("#"):
            heading = lines[j]
            k = j + 1
            body = []
            while k < len(lines):
                s = lines[k]
                if BLOCK_RE.search(s) or s.lstrip().startswith("#"):
                    break
                if s.strip():
                    body.append(s)
                k += 1
            if body:
                sections[bid] = heading + "\n" + "\n".join(body)
    return sections


def _real_block_ids(text: str) -> set:
    return set(_block_sections(text))


def _marker_section_violations(text: str, required_ids) -> list:
    """missing: no marker at all; empty_marker: a marker binding no real section;
    wrong_section: the bound section carries none of the block's canonical keywords
    (r2 finding 8: a `three-verdicts` marker before a "Cooking" section reddens)."""
    sections = _block_sections(text)
    present = set(BLOCK_RE.findall(text))
    v = []
    for rid in required_ids:
        if rid not in present:
            v.append(f"missing:{rid}")
            continue
        if rid not in sections:
            v.append(f"empty_marker:{rid}")
            continue
        keywords = CANONICAL_BLOCK_KEYWORDS.get(rid)
        if keywords and not any(k in sections[rid].lower() for k in keywords):
            v.append(f"wrong_section:{rid}")
    return v


def _concept_row_violations(row, registry_exists: bool) -> list:
    """Every concept row must be FULLY bound: closed kind, canonical kind for required ids,
    and the exact per-kind projection-owner rule -- no conditional may be silently skipped."""
    v = []
    rid = str(row.get("id", "")).strip()
    if not rid:
        v.append("missing_id")
    kind = row.get("kind", "")
    if kind not in CLOSED_CONCEPT_KINDS:
        v.append(f"bad_kind:{kind!r}")
    if rid in REQUIRED_CONCEPT_KINDS and kind != REQUIRED_CONCEPT_KINDS[rid]:
        v.append(f"required_kind_mismatch:{rid}")
    owner = str(row.get("projection_owner", "")).strip()
    if not owner:
        v.append("missing_owner")
    if kind == "sop_process":
        m = _SOP_OWNER_RE.match(owner)
        if not m:
            v.append("sop_owner_not_block_bound")
        elif rid in REQUIRED_CONCEPT_KINDS and m.group(1) != rid:
            v.append(f"sop_owner_block_id_mismatch:{rid}")
    if kind in ("demo", "mode_ladder"):
        if not (owner.startswith("docs/plans/ACTIVE.md") or owner.startswith("docs/plans/handoff/")):
            v.append("plan_concept_bad_owner")
    if kind == "role":
        if owner not in VALID_ROLE_OWNERS:                 # exact match, never substring
            v.append("role_concept_bad_owner")
        if not registry_exists and "interim_source" not in row:
            v.append("missing_interim_source")   # registry ABSENT -> interim REQUIRED
        if registry_exists and "interim_source" in row:
            v.append("stale_interim_source")      # registry PRESENT -> interim FORBIDDEN
    return v


def _concept_coverage_violations(rows) -> list:
    ids = {str(r.get("id", "")).strip() for r in rows}
    return [f"uncovered:{m}" for m in sorted(REQUIRED_CONCEPT_IDS - ids)]


# ====================================================================================
# HOSTILE / VACUITY PROBES — green today; each is the named kill for a review finding.
# ====================================================================================
class DocsCurrencyHostileProbes(unittest.TestCase):
    # ---- finding 8: markers must bind the canonical NAMED section ----
    def test_hostile_f8_marker_before_unrelated_section_is_rejected(self) -> None:
        cooking = ("<!-- SOP-BLOCK: three-verdicts -->\n## Cooking\n"
                   "Preheat the oven to 200C and stir slowly.\n")
        self.assertIn(
            "wrong_section:three-verdicts",
            _marker_section_violations(cooking, ("three-verdicts",)),
            "the r2 hollow case: a three-verdicts marker before a Cooking section must redden",
        )
        real_heading = ("<!-- SOP-BLOCK: three-verdicts -->\n## The three verdicts\n"
                        "DESIGN / CODE / ADVERSARIAL each gate a slice.\n")
        self.assertEqual(
            _marker_section_violations(real_heading, ("three-verdicts",)), [],
            "positive control: the canonical named section passes",
        )
        paired = ("<!-- SOP-BLOCK: mf1-receipts -->\nChrome-headless receipts are binding.\n"
                  "<!-- SOP-BLOCK: mf1-receipts -->\n")
        self.assertEqual(
            _marker_section_violations(paired, ("mf1-receipts",)), [],
            "positive control: a marker PAIR enclosing canonical content passes",
        )
        hollow = "<!-- SOP-BLOCK: three-verdicts -->\n<!-- SOP-BLOCK: mf1-receipts -->\n"
        self.assertIn(
            "empty_marker:three-verdicts", _marker_section_violations(hollow, ("three-verdicts",)),
            "a bare marker wrapping no real section still reddens",
        )
        self.assertNotIn(
            "three-verdicts", _real_block_ids(hollow),
            "a pointer resolving to an EMPTY marker must not count as resolved (CR-12)",
        )
        self.assertIn(
            "three-verdicts",
            _real_block_ids("<!-- SOP-BLOCK: three-verdicts -->\n## Verdicts\nbody line\n"),
        )

    # ---- finding 3: canonical kind + exact owner bindings ----
    def test_hostile_f3_all_sop_process_policy_is_rejected(self) -> None:
        rows = [{"id": rid, "kind": "sop_process", "projection_owner": "anything"}
                for rid in sorted(REQUIRED_CONCEPT_IDS)]
        flat = []
        for r in rows:
            flat.extend(_concept_row_violations(r, registry_exists=False))
        self.assertIn("required_kind_mismatch:demo-a-b", flat,
                      "the r2 hollow case: stamping every id sop_process must redden on demo-a-b")
        self.assertIn("required_kind_mismatch:mode-ladder", flat)
        self.assertIn("required_kind_mismatch:roles", flat)
        self.assertIn("sop_owner_not_block_bound", flat,
                      "owner='anything' must redden (exact projection-owner rule)")

    def test_hostile_f3_substring_role_owner_is_rejected(self) -> None:
        neg = {"id": "roles", "kind": "role",
               "projection_owner": "NOT contracts/role_registry.toml",
               "interim_source": "AGENTS.md SOP prose"}
        self.assertIn("role_concept_bad_owner", _concept_row_violations(neg, registry_exists=False),
                      "the r2 hollow case: a negated owner containing the registry name reddens")
        good_role = {"id": "roles", "kind": "role",
                     "projection_owner": "contracts/role_registry.toml",
                     "interim_source": "AGENTS.md SOP prose"}
        self.assertEqual(_concept_row_violations(good_role, registry_exists=False), [],
                         "positive control: exact registry owner + interim (registry absent)")
        self.assertIn("stale_interim_source",
                      _concept_row_violations(good_role, registry_exists=True),
                      "registry PRESENT -> a role row still carrying interim_source reddens")
        bare = {"id": "roles", "kind": "role", "projection_owner": "contracts/role_registry.toml"}
        self.assertIn("missing_interim_source", _concept_row_violations(bare, registry_exists=False),
                      "registry ABSENT -> a role row without interim_source reddens")

    def test_hostile_f3_sop_owner_must_name_its_own_block(self) -> None:
        good = {"id": "three-verdicts", "kind": "sop_process",
                "projection_owner": "AGENTS.md#three-verdicts"}
        self.assertEqual(_concept_row_violations(good, registry_exists=False), [],
                         "positive control: a sop row bound to its own AGENTS block id")
        crossed = {"id": "three-verdicts", "kind": "sop_process",
                   "projection_owner": "AGENTS.md#mf1-receipts"}
        self.assertIn("sop_owner_block_id_mismatch:three-verdicts",
                      _concept_row_violations(crossed, registry_exists=False),
                      "a sop row pointing at a DIFFERENT block id must redden")
        plan_owner = {"id": "demo-a-b", "kind": "demo",
                      "projection_owner": "docs/plans/ACTIVE.md#demo-a-b"}
        self.assertEqual(_concept_row_violations(plan_owner, registry_exists=False), [],
                         "positive control: demo rows project from the plan authority")
        agents_demo = {"id": "demo-a-b", "kind": "demo", "projection_owner": "AGENTS.md#demo"}
        self.assertIn("plan_concept_bad_owner",
                      _concept_row_violations(agents_demo, registry_exists=False),
                      "demo/mode-ladder rows never project from AGENTS.md blocks")

    def test_hostile_f3_untyped_rows_and_coverage_floor(self) -> None:
        self.assertIn("missing_id",
                      _concept_row_violations({"kind": "role", "projection_owner": "x"}, False))
        self.assertIn("missing_owner",
                      _concept_row_violations({"id": "x", "kind": "sop_process"}, False))
        self.assertTrue(
            any(x.startswith("bad_kind") for x in
                _concept_row_violations({"id": "x", "projection_owner": "y"}, False)),
            "an empty/unknown kind reddens instead of skipping all conditionals",
        )
        one_row = [{"id": "roles", "kind": "role",
                    "projection_owner": "contracts/role_registry.toml",
                    "interim_source": "AGENTS.md SOP prose"}]
        self.assertTrue(_concept_coverage_violations(one_row),
                        "a policy missing required concept rows reddens (coverage floor)")


# ====================================================================================
# REAL CONTRACT ARMS — CR-10..CR-13. RED today; flip at L4 (after the W7 registry).
# ====================================================================================
class ProcessDocsCurrencyConvergence(unittest.TestCase):
    # -- CR-10 (r2-g4 / F5 / r2-finding-8) --------------------------------------------
    def test_agents_md_carries_stable_block_ids(self) -> None:
        """RED today: AGENTS.md has zero block markers. At L4 every canonical block id wraps
        its REAL, canonically NAMED section (keyword-witnessed), never unrelated prose."""
        violations = _marker_section_violations(AGENTS.read_text(encoding="utf-8"), REQUIRED_SOP_BLOCKS)
        self.assertEqual(
            violations, [],
            f"AGENTS.md must carry a <!-- SOP-BLOCK: <id> --> marker wrapping the canonical "
            f"named section per block; violations: {violations}",
        )

    # -- CR-11 (r2-g4) ------------------------------------------------------------------
    def test_agents_routes_evidence_to_governed_homes(self) -> None:
        """RED today: step-13 routes transcripts to the scratch review-queue. At L4 evidence
        routing names dev/reports/. A concrete scratch FILE path is banned; the bare tree name
        may survive only inside the scratch-grammar teaching (CR-20 dispositions own that)."""
        text = AGENTS.read_text(encoding="utf-8")
        self.assertNotIn(
            "scratch review-queue", text,
            "AGENTS.md step-13 RECORD still routes review transcripts to the scratch review-queue",
        )
        concrete = re.findall(r"scratchpad/work/[^\s`'\"()\[\]]+", text)
        self.assertEqual(
            concrete, [],
            f"AGENTS.md must not cite concrete scratch work files as evidence: {concrete}",
        )
        record_lines = [ln for ln in text.splitlines() if "review transcripts" in ln.lower()]
        self.assertTrue(record_lines, "AGENTS.md must retain a RECORD routing line for review transcripts")
        self.assertTrue(
            all("dev/reports/" in ln for ln in record_lines),
            "the RECORD routing for review transcripts must name dev/reports/, not the scratch queue",
        )

    # -- CR-12 (r2-g4 / F5 / r2-finding-8) ----------------------------------------------
    def test_handoff_carries_sop_pointer_ids(self) -> None:
        """RED today: HANDOFF.md has no SOP-POINTER lines. At L4 every cited id resolves to a
        REAL canonical AGENTS section (empty markers and wrong sections both dangle)."""
        cited = POINTER_RE.findall(HANDOFF.read_text(encoding="utf-8"))
        self.assertTrue(cited, "HANDOFF.md must carry SOP-POINTER: <block-id> lines; it has none today")
        missing = [p for p in REQUIRED_HANDOFF_POINTERS if p not in cited]
        self.assertEqual(missing, [], f"HANDOFF.md must point to the reentry-critical SOP blocks; missing: {missing}")
        agents_text = AGENTS.read_text(encoding="utf-8")
        dangling = _marker_section_violations(agents_text, sorted(set(cited)))
        self.assertEqual(
            dangling, [],
            f"HANDOFF SOP-POINTER ids must resolve to REAL canonical AGENTS SOP-BLOCK "
            f"sections; dangling: {dangling}",
        )

    # -- CR-13 (r2-g4 / F5 / r2-finding-3) ----------------------------------------------
    def test_policy_concept_rows_name_projection_owners(self) -> None:
        """RED today: the policy file is absent. At L4 every concept row is bound to its
        canonical kind and exact projection owner (role rows exactly the registry; sop rows
        their own AGENTS block; demo/mode-ladder rows the plan authority)."""
        registry_exists = REGISTRY.is_file()
        self.assertTrue(
            POLICY.is_file(),
            "contracts/process_docs_currency_policy.toml must exist (L4); it is absent today",
        )
        policy = tomllib.loads(POLICY.read_text(encoding="utf-8"))
        self.assertEqual(policy.get("contract_id"), "ProcessDocsCurrencyPolicy")
        concepts = policy.get("concept", [])
        self.assertTrue(concepts, "policy must declare [[concept]] rows")
        self.assertEqual(
            _concept_coverage_violations(concepts), [],
            "policy must cover the full required-concept list",
        )
        for row in concepts:
            cid = row.get("id", "<unnamed>")
            self.assertEqual(
                _concept_row_violations(row, registry_exists), [],
                f"concept {cid} is not fully bound: {_concept_row_violations(row, registry_exists)}",
            )


if __name__ == "__main__":
    unittest.main()

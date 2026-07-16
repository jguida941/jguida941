"""W6-K — hostile contracts for the reference-capture lane (w3c-0 §8, R1-R8).

RED-first. Every law from the slice-0 W5f-lane closure (`docs/plans/handoff/
w3c-0-design-closure.md` §8) and the 31-id aspect vocabulary (§3.1) is proved by a
hostile record that must be REJECTED and a well-formed record that must PASS:

  R1 producer != approver principals (kind==operator approver)
  R2 one hashed vocabulary — every aspect id is a member of the closed 31-id set
  R3 source != target: the full closed 12-field occurrence key, vocabulary-bound
  R4 four rights dimensions present (publication / custody / redistribution / retention)
  R5 per-aspect lifecycle — approval binds the candidate hash BEFORE measurement;
     an evidence-only candidate can never carry a measurement
  R6 content-addressed immutable pack graph — replaces/replaces_manifest_sha256
     pairing + the one closed dashboard-pre-w3 legacy adapter allowance
  R7 file-driven promotion — a promoted clause whose aspect isn't approved reddens
  R8 dynamic homes with inverse/phantom checks — every promoted clause has exactly
     one binding and vice versa

Plus the structural fail-closed laws every validator carries: exact closed key set
(unknown key rejects) and duplicate-JSON-key rejection.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "scripts").is_dir() and (parent / "contracts").is_dir():
            return parent
    raise RuntimeError("repo root not found")


ROOT = _repo_root()
VOCAB_PATH = ROOT / "contracts" / "reference_aspects.json"

from scripts.quality.reference_intake.schema import (  # noqa: E402  (import after ROOT resolves)
    ReferenceContractError,
    assert_producer_approver_independent,
    load_json_file,
    loads_no_duplicate_keys,
    validate_external_reference_pack,
    validate_measurement_run,
    validate_promoted_reference_clauses,
    validate_reference_aspect_approval,
    validate_reference_aspect_vocabulary,
    validate_reference_bindings,
    validate_reference_candidate_record,
    validate_reference_override_record,
    vocabulary_aspect_ids,
    vocabulary_sha256,
)

VOCAB = load_json_file(VOCAB_PATH)
IDS = vocabulary_aspect_ids(VOCAB)
VSHA = vocabulary_sha256(VOCAB_PATH)

SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_LEGACY = "34ed2ae295e8f350bd406b30e6891488c7fe6407e0d04dbed6bb93ad16544fac"

PRINCIPALS = {
    "op-1": {"principal_id": "op-1", "kind": "operator", "display": "Operator One"},
    "op-2": {"principal_id": "op-2", "kind": "operator", "display": "Operator Two"},
    "tool-cap": {"principal_id": "tool-cap", "kind": "tool", "display": "Capture Bot"},
}


# --------------------------------------------------------------------------- builders
def _occurrence_key(**over):
    key = {
        "target_repo_or_url": "https://github.com/owner/target-site",
        "target_revision": "deadbeef",
        "route": "index",
        "profile_or_context": "apple-dark",
        "viewport": 1280,
        "state": "default",
        "region": "editorial-masthead",
        "subject_selector": "[data-arch-region='editorial-masthead'] .cta",
        "occurrence_index": 0,
        "aspect_id": "component.button",
        "vocabulary_version": 1,
        "vocabulary_sha256": VSHA,
    }
    key.update(over)
    return key


def _candidate(**over):
    rec = {
        "contract_id": "ReferenceCandidateRecord",
        "schema_version": 1,
        "candidate_id": "cand-1",
        "origin": "operator-directed-capture",
        "producer": {
            "principal_id": "tool-cap",
            "tool": "reference_lane",
            "version": "0.1.0",
            "command": "reference candidate --id cand-1",
            "run_id": "run-777",
        },
        "source": {
            "url_or_path": "https://example.com/reference",
            "fetched_utc": "2026-07-15T00:00:00Z",
            "robots": {"checked": True, "allowed": True},
        },
        "rights": [
            {
                "resource": "https://example.com/reference",
                "publication": "derived",
                "custody_id": "store-private-1",
                "redistribution": "forbidden",
                "retention": {"policy": "until-replaced"},
            }
        ],
        "capture": {"live_evidence": ["screenshot-1280.png"], "staging_tree_sha256": SHA_A, "gaps": []},
        "observable_anatomy": {"authority_status": "evidence-only", "subjects": []},
        "uncovered_aspects_claimed": ["component.button", "page.navigation"],
        "status": "proposed",
        "record_sha256": SHA_B,
    }
    rec.update(over)
    return rec


def _approval(**over):
    rec = {
        "contract_id": "ReferenceAspectApproval",
        "schema_version": 1,
        "pack_id": "example-com-v1",
        "candidate_id": "cand-1",
        "candidate_sha256": SHA_B,  # binds the candidate's record_sha256 BEFORE measurement
        "rows": [
            {
                "aspect_id": "component.button",
                "decision": "approved",
                "subjects": [{"subject_id": "cta-0", "selector": ".cta"}],
                "states": ["default", "hover"],
                "viewports": [1280, 390],
                "target_scope": _occurrence_key(),
                "rights_ack": "derived/forbidden/until-replaced",
            }
        ],
        "approver_principal_id": "op-1",
        "approved_utc": "2026-07-15T01:00:00Z",
        "transitions": [
            {"aspect_id": "component.button", "from": "presented", "to": "approved",
             "principal_id": "op-1", "date": "2026-07-15", "reason": "operator approved"},
        ],
    }
    rec.update(over)
    return rec


def _pack(**over):
    rec = {
        "contract_id": "ExternalReferencePack",
        "schema_version": 1,
        "pack_id": "example-com-v1",
        "pack_version": 1,
        "frozen_source": {
            "artifact": "assets/receipts/reference-packs/example-com-v1/source.tar.gz",
            "tree_sha256": SHA_A,
            "script_policy": "stripped",
            "dom_excisions": ["script", "iframe"],
            "entry": "index.html",
            "entry_sha256": SHA_B,
        },
        "matrix": {"viewports": [1280, 390], "states": ["default", "hover"]},
        "aspect_ownership": {"component.button": "index/editorial-masthead/cta[0]"},
        "official_precedence_exclusions": [],
        "capture_gaps": [],
        "captures": [
            {
                "viewport": 1280,
                "state": "default",
                "screenshot": {"path": "assets/x/shot-1280.png", "sha256": SHA_A},
                "facts": {"path": "assets/x/facts-1280.json", "sha256": SHA_B},
                "provenance": {"path": "assets/x/prov-1280.json", "sha256": SHA_C},
            }
        ],
        "retention": {"policy": "until-replaced"},
        "custody_id": "store-private-1",
        "revalidation": {
            "pack_manifest_sha256": SHA_A,
            "catalog_file_sha256s": [SHA_B],
            "baseline_clause_digests": [SHA_C],
            "vocabulary_sha256": VSHA,
        },
    }
    rec.update(over)
    return rec


def _legacy_adapter():
    return {
        "legacy_predecessor": "dashboard-pre-w3",
        "legacy_predecessor_manifest_sha256": SHA_LEGACY,
        "treated_as": {"pack_version": 1, "state": "promoted"},
    }


def _measurement(**over):
    rec = {
        "contract_id": "MeasurementRun",
        "schema_version": 1,
        "pack_id": "example-com-v1",
        "session_id": "sess-9",
        "measured_aspects": ["component.button"],
        "producer_principal_id": "tool-cap",
        "chrome_version": "141.0.0.0",
        "command": "reference measure --id example-com-v1",
        "run_sha256": SHA_A,
    }
    rec.update(over)
    return rec


def _promoted_clause(**over):
    clause = {
        "clause_id": "R-REF-EX-BTN",
        "claim": "the example.com CTA button geometry equals the approved measured reference",
        "authority": "approved-reference",
        "source_mode": "measured-reference",
        "exactness": "measurement-exact",
        "sources": [{"source_kind": "approved-reference",
                     "ref": "contracts/reference_packs/example-com-v1/manifest.json"}],
        "scope": {"profiles": ["apple-dark"], "aspects": ["component.button"],
                  "invariant_ids": ["ex-btn-geometry"]},
    }
    clause.update(over)
    return clause


def _bindings(**over):
    doc = {
        "contract_id": "ReferenceClauseBindings",
        "schema_version": 1,
        "bindings": [
            {
                "clause_id": "R-REF-EX-BTN",
                "pack_id": "example-com-v1",
                "pack_manifest_sha256": SHA_A,
                "occurrence_scope": "index/editorial-masthead/cta[0]",
                "fact_bindings": [{"fact_id": "fact.button_boxes", "field": "radius_px", "expected": 8}],
            }
        ],
    }
    doc.update(over)
    return doc


def _override(**over):
    rec = {
        "contract_id": "ReferenceOverrideRecord",
        "schema_version": 1,
        "pack_id": "example-com-v1",
        "overrides": [
            {
                "aspect_id": "component.button",
                "measured_value": {"radius_px": 8},
                "owner_value": {"radius_px": 6},
                "mode_d_clause_id": "R-OWNER-BTN-1",
                "forked_from_measured": True,
            }
        ],
    }
    rec.update(over)
    return rec


# --------------------------------------------------------------------------- vocabulary (R2 anchor)
class VocabularyContract(unittest.TestCase):
    def test_valid_vocabulary_passes_and_has_31_ids(self):
        validate_reference_aspect_vocabulary(VOCAB)
        self.assertEqual(31, len(IDS))
        self.assertEqual(10, sum(1 for a in VOCAB["aspects"] if a["kind"] == "page"))
        self.assertEqual(10, sum(1 for a in VOCAB["aspects"] if a["kind"] == "visual"))
        self.assertEqual(11, sum(1 for a in VOCAB["aspects"] if a["kind"] == "component"))
        self.assertIn("component.button", IDS)
        self.assertIn("page.navigation", IDS)
        self.assertIn("visual.material-blur", IDS)

    def test_closed_states_set(self):
        states = VOCAB["states"]
        self.assertEqual(["rest", "hover", "focus-visible", "active", "selected", "disabled"], states["ids"])
        self.assertEqual("rest", states["profile_state_map"]["default"])
        self.assertEqual(["initial", "hydrated"], states["visibility_phases"])

    def test_component_subaspect_subsets_are_exact(self):
        by_id = {a["id"]: a for a in VOCAB["aspects"]}
        self.assertEqual(
            ["anatomy", "geometry", "typography", "paint", "state-mechanic", "focus", "label-honesty", "icon"],
            by_id["component.button"]["subaspects"],
        )
        self.assertEqual(["anatomy", "geometry", "paint", "divider"], by_id["component.card"]["subaspects"])
        self.assertEqual(
            {"anatomy": ["data-table", "structured-list"]},
            VOCAB["subaspect_variants"]["component.table"],
        )

    def test_vocabulary_unknown_top_level_key_rejects(self):
        bad = dict(VOCAB)
        bad["surprise"] = 1
        with self.assertRaises(ReferenceContractError):
            validate_reference_aspect_vocabulary(bad)

    def test_vocabulary_dropped_aspect_rejects(self):
        bad = json.loads(json.dumps(VOCAB))
        bad["aspects"] = bad["aspects"][:-1]  # 30 ids
        with self.assertRaises(ReferenceContractError):
            validate_reference_aspect_vocabulary(bad)

    def test_vocabulary_wrong_component_subaspects_rejects(self):
        bad = json.loads(json.dumps(VOCAB))
        for aspect in bad["aspects"]:
            if aspect["id"] == "component.card":
                aspect["subaspects"] = ["anatomy", "geometry", "paint"]  # dropped divider
        with self.assertRaises(ReferenceContractError):
            validate_reference_aspect_vocabulary(bad)


# --------------------------------------------------------------------------- structural (closed key + dup key)
class StructuralFailClosed(unittest.TestCase):
    def test_duplicate_json_key_rejected(self):
        with self.assertRaises(ReferenceContractError):
            loads_no_duplicate_keys('{"a": 1, "a": 2}')

    def test_duplicate_json_key_nested_rejected(self):
        with self.assertRaises(ReferenceContractError):
            loads_no_duplicate_keys('{"outer": {"k": 1, "k": 2}}')

    def test_unique_keys_ok(self):
        self.assertEqual({"a": 1, "b": {"c": 2}}, loads_no_duplicate_keys('{"a":1,"b":{"c":2}}'))

    def test_candidate_unknown_key_rejects(self):
        with self.assertRaises(ReferenceContractError):
            validate_reference_candidate_record(_candidate(surprise=1), vocabulary=VOCAB)

    def test_pack_unknown_key_rejects(self):
        with self.assertRaises(ReferenceContractError):
            validate_external_reference_pack(_pack(surprise=1), vocabulary=VOCAB)

    def test_measurement_unknown_key_rejects(self):
        with self.assertRaises(ReferenceContractError):
            validate_measurement_run(_measurement(surprise=1), vocabulary=VOCAB)


# --------------------------------------------------------------------------- candidate (R4 rights, evidence-only)
class CandidateContract(unittest.TestCase):
    def test_valid_candidate_passes(self):
        self.assertEqual("cand-1", validate_reference_candidate_record(_candidate(), vocabulary=VOCAB)["candidate_id"])

    def test_missing_rights_dimension_rejects(self):
        # R4: drop the retention dimension from the per-resource rights row.
        row = {"resource": "r", "publication": "derived", "custody_id": "store-1", "redistribution": "forbidden"}
        with self.assertRaises(ReferenceContractError):
            validate_reference_candidate_record(_candidate(rights=[row]), vocabulary=VOCAB)

    def test_bad_publication_value_rejects(self):
        row = dict(_candidate()["rights"][0])
        row["publication"] = "everything"
        with self.assertRaises(ReferenceContractError):
            validate_reference_candidate_record(_candidate(rights=[row]), vocabulary=VOCAB)

    def test_dated_expiry_without_expires_utc_rejects(self):
        row = dict(_candidate()["rights"][0])
        row["retention"] = {"policy": "dated-expiry"}  # missing expires_utc
        with self.assertRaises(ReferenceContractError):
            validate_reference_candidate_record(_candidate(rights=[row]), vocabulary=VOCAB)

    def test_unknown_claimed_aspect_rejects(self):
        # R2: uncovered_aspects_claimed must be members of the vocabulary.
        with self.assertRaises(ReferenceContractError):
            validate_reference_candidate_record(
                _candidate(uncovered_aspects_claimed=["component.button", "component.hologram"]),
                vocabulary=VOCAB,
            )

    def test_evidence_only_candidate_cannot_carry_measurement(self):
        # R5: an evidence-only observable_anatomy that smuggles measurement facts reddens.
        poisoned = {"authority_status": "evidence-only", "measured_aspects": ["component.button"], "run_sha256": SHA_A}
        with self.assertRaises(ReferenceContractError):
            validate_reference_candidate_record(_candidate(observable_anatomy=poisoned), vocabulary=VOCAB)

    def test_observable_anatomy_not_evidence_only_rejects(self):
        with self.assertRaises(ReferenceContractError):
            validate_reference_candidate_record(
                _candidate(observable_anatomy={"authority_status": "measured"}), vocabulary=VOCAB)


# --------------------------------------------------------------------------- approval (R1, R2, R3, R5)
class ApprovalContract(unittest.TestCase):
    def test_valid_approval_passes(self):
        validate_reference_aspect_approval(_approval(), vocabulary=VOCAB, principals=PRINCIPALS)

    def test_producer_equals_approver_rejects(self):
        # R1: independence. Candidate produced by tool-cap; approval by tool-cap == reject.
        cand = _candidate()  # producer principal tool-cap
        appr = _approval(approver_principal_id="tool-cap")
        with self.assertRaises(ReferenceContractError):
            assert_producer_approver_independent(cand, appr, principals=PRINCIPALS)
        with self.assertRaises(ReferenceContractError):
            validate_reference_aspect_approval(appr, vocabulary=VOCAB, candidate=cand, principals=PRINCIPALS)

    def test_operator_cannot_approve_own_capture(self):
        # R1 independence, ISOLATED: the same operator on both sides reddens even
        # though the approver IS an operator (so only the producer!=approver law can fire).
        cand = _candidate(producer={"principal_id": "op-1", "tool": "reference_lane",
                                    "version": "0.1.0", "command": "c", "run_id": "r"})
        appr = _approval(approver_principal_id="op-1")
        with self.assertRaises(ReferenceContractError):
            assert_producer_approver_independent(cand, appr, principals=PRINCIPALS)
        with self.assertRaises(ReferenceContractError):
            validate_reference_aspect_approval(appr, vocabulary=VOCAB, candidate=cand, principals=PRINCIPALS)

    def test_non_operator_approver_rejects(self):
        # R1: approver kind must be operator.
        with self.assertRaises(ReferenceContractError):
            validate_reference_aspect_approval(
                _approval(approver_principal_id="tool-cap"), vocabulary=VOCAB, principals=PRINCIPALS)

    def test_independent_operator_approves(self):
        cand = _candidate()  # tool-cap produced
        appr = _approval(approver_principal_id="op-1")
        assert_producer_approver_independent(cand, appr, principals=PRINCIPALS)  # no raise

    def test_unknown_row_aspect_id_rejects(self):
        # R2: an approval row naming an aspect outside the closed vocabulary reddens.
        rows = json.loads(json.dumps(_approval()["rows"]))
        rows[0]["aspect_id"] = "component.wormhole"
        rows[0]["target_scope"]["aspect_id"] = "component.wormhole"
        with self.assertRaises(ReferenceContractError):
            validate_reference_aspect_approval(_approval(rows=rows), vocabulary=VOCAB, principals=PRINCIPALS)

    def test_approval_omits_candidate_hash_rejects(self):
        # R5: approval binds the candidate staged-byte hash BEFORE measurement.
        with self.assertRaises(ReferenceContractError):
            validate_reference_aspect_approval(_approval(candidate_sha256=""), vocabulary=VOCAB, principals=PRINCIPALS)

    def test_approval_precedes_candidate_hash_rejects(self):
        # R5: a stale/placeholder hash that does not bind the real candidate reddens.
        cand = _candidate(record_sha256=SHA_B)
        appr = _approval(candidate_sha256="0" * 64, approver_principal_id="op-1")
        with self.assertRaises(ReferenceContractError):
            validate_reference_aspect_approval(appr, vocabulary=VOCAB, candidate=cand, principals=PRINCIPALS)

    def test_malformed_occurrence_key_rejects(self):
        # R3: the target occurrence key is the full closed 12-field key.
        rows = json.loads(json.dumps(_approval()["rows"]))
        rows[0]["target_scope"]["surprise"] = 1
        with self.assertRaises(ReferenceContractError):
            validate_reference_aspect_approval(_approval(rows=rows), vocabulary=VOCAB, principals=PRINCIPALS)

    def test_occurrence_key_vocabulary_sha_binding(self):
        # R3/R2: the occurrence key must pin THIS vocabulary's digest.
        rows = json.loads(json.dumps(_approval()["rows"]))
        rows[0]["target_scope"]["vocabulary_sha256"] = "f" * 64
        with self.assertRaises(ReferenceContractError):
            validate_reference_aspect_approval(
                _approval(rows=rows), vocabulary=VOCAB, principals=PRINCIPALS, vocabulary_sha256=VSHA)


# --------------------------------------------------------------------------- external pack (R6)
class ExternalPackContract(unittest.TestCase):
    def test_valid_pack_passes(self):
        validate_external_reference_pack(_pack(), vocabulary=VOCAB)

    def test_replaces_without_manifest_sha_rejects(self):
        # R6: replaces + replaces_manifest_sha256 must appear TOGETHER.
        with self.assertRaises(ReferenceContractError):
            validate_external_reference_pack(_pack(pack_version=2, replaces="example-com-v1"), vocabulary=VOCAB)

    def test_valid_replacement_pair_passes(self):
        validate_external_reference_pack(
            _pack(pack_version=2, replaces="example-com-v1", replaces_manifest_sha256=SHA_C), vocabulary=VOCAB)

    def test_legacy_adapter_only_for_dashboard_pre_w3(self):
        # R6: legacy_adapter permitted ONLY when replaces == the one closed legacy id.
        bad = _pack(pack_version=2, replaces="example-com-v1", replaces_manifest_sha256=SHA_C,
                    legacy_adapter=_legacy_adapter())
        with self.assertRaises(ReferenceContractError):
            validate_external_reference_pack(bad, vocabulary=VOCAB)

    def test_valid_legacy_adapter_passes(self):
        ok = _pack(pack_version=2, replaces="dashboard-pre-w3", replaces_manifest_sha256=SHA_LEGACY,
                   legacy_adapter=_legacy_adapter())
        validate_external_reference_pack(ok, vocabulary=VOCAB)

    def test_legacy_adapter_wrong_predecessor_digest_rejects(self):
        adapter = _legacy_adapter()
        adapter["legacy_predecessor_manifest_sha256"] = "e" * 64  # not the pinned legacy digest
        bad = _pack(pack_version=2, replaces="dashboard-pre-w3", replaces_manifest_sha256=SHA_LEGACY,
                    legacy_adapter=adapter)
        with self.assertRaises(ReferenceContractError):
            validate_external_reference_pack(bad, vocabulary=VOCAB)

    def test_unknown_ownership_aspect_rejects(self):
        with self.assertRaises(ReferenceContractError):
            validate_external_reference_pack(
                _pack(aspect_ownership={"component.button": "x", "component.portal": "y"}), vocabulary=VOCAB)

    def test_non_positive_pack_version_rejects(self):
        with self.assertRaises(ReferenceContractError):
            validate_external_reference_pack(_pack(pack_version=0), vocabulary=VOCAB)

    def test_pack_citing_rejected_evidence_pack_rejects(self):
        # rejected-evidence isolation: a pack whose predecessor is a rejected-evidence pack reddens.
        states = {"tainted-pack": "rejected-evidence"}
        bad = _pack(pack_version=2, replaces="tainted-pack", replaces_manifest_sha256=SHA_C)
        with self.assertRaises(ReferenceContractError):
            validate_external_reference_pack(bad, vocabulary=VOCAB, pack_states=states)


# --------------------------------------------------------------------------- measurement run
class MeasurementContract(unittest.TestCase):
    def test_valid_measurement_passes(self):
        validate_measurement_run(_measurement(), vocabulary=VOCAB)

    def test_measured_aspect_outside_vocabulary_rejects(self):
        with self.assertRaises(ReferenceContractError):
            validate_measurement_run(_measurement(measured_aspects=["component.button", "not.an.aspect"]),
                                     vocabulary=VOCAB)

    def test_measurement_citing_rejected_evidence_pack_rejects(self):
        with self.assertRaises(ReferenceContractError):
            validate_measurement_run(_measurement(pack_id="tainted"), vocabulary=VOCAB,
                                     pack_states={"tainted": "rejected-evidence"})


# --------------------------------------------------------------------------- promoted clauses (R7)
class PromotedClauseContract(unittest.TestCase):
    def test_valid_promoted_clause_passes(self):
        validate_promoted_reference_clauses([_promoted_clause()], approved_aspects={"component.button"})

    def test_promoted_clause_with_unapproved_aspect_rejects(self):
        # R7: file-driven promotion — the clause's aspect must have been approved.
        with self.assertRaises(ReferenceContractError):
            validate_promoted_reference_clauses([_promoted_clause()], approved_aspects={"component.card"})

    def test_wrong_authority_rejects(self):
        with self.assertRaises(ReferenceContractError):
            validate_promoted_reference_clauses([_promoted_clause(authority="owner-ratified")])

    def test_incoherent_authority_tuple_rejects(self):
        with self.assertRaises(ReferenceContractError):
            validate_promoted_reference_clauses([_promoted_clause(exactness="perceptual")])

    def test_source_not_a_reference_pack_rejects(self):
        with self.assertRaises(ReferenceContractError):
            validate_promoted_reference_clauses(
                [_promoted_clause(sources=[{"source_kind": "approved-reference", "ref": "contracts/design_sources/x.json"}])])

    def test_duplicate_clause_id_rejects(self):
        with self.assertRaises(ReferenceContractError):
            validate_promoted_reference_clauses([_promoted_clause(), _promoted_clause()])


# --------------------------------------------------------------------------- bindings (R8 inverse/phantom)
class BindingsContract(unittest.TestCase):
    def test_valid_bindings_pass(self):
        validate_reference_bindings(_bindings(), promoted_clause_ids={"R-REF-EX-BTN"})

    def test_phantom_binding_rejects(self):
        # R8: a binding for a clause that is not a promoted clause reddens.
        with self.assertRaises(ReferenceContractError):
            validate_reference_bindings(_bindings(), promoted_clause_ids={"R-REF-EX-OTHER"})

    def test_promoted_clause_without_binding_rejects(self):
        # R8 inverse: a promoted clause with no binding row reddens.
        with self.assertRaises(ReferenceContractError):
            validate_reference_bindings(_bindings(), promoted_clause_ids={"R-REF-EX-BTN", "R-REF-EX-EXTRA"})

    def test_duplicate_binding_clause_rejects(self):
        doc = _bindings()
        doc["bindings"] = doc["bindings"] + doc["bindings"]
        with self.assertRaises(ReferenceContractError):
            validate_reference_bindings(doc, promoted_clause_ids={"R-REF-EX-BTN"})

    def test_binding_to_rejected_evidence_pack_rejects(self):
        doc = _bindings()
        doc["bindings"][0]["pack_id"] = "tainted"
        with self.assertRaises(ReferenceContractError):
            validate_reference_bindings(doc, promoted_clause_ids={"R-REF-EX-BTN"},
                                        pack_states={"tainted": "rejected-evidence"})


# --------------------------------------------------------------------------- consumer override
class OverrideContract(unittest.TestCase):
    def test_valid_override_passes(self):
        validate_reference_override_record(_override(), vocabulary=VOCAB)

    def test_forked_from_measured_must_be_true(self):
        row = dict(_override()["overrides"][0])
        row["forked_from_measured"] = False
        with self.assertRaises(ReferenceContractError):
            validate_reference_override_record(_override(overrides=[row]), vocabulary=VOCAB)

    def test_override_unknown_aspect_rejects(self):
        row = dict(_override()["overrides"][0])
        row["aspect_id"] = "component.singularity"
        with self.assertRaises(ReferenceContractError):
            validate_reference_override_record(_override(overrides=[row]), vocabulary=VOCAB)


if __name__ == "__main__":
    unittest.main()

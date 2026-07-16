"""Fail-closed authority gate for design-language invariant claims."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
PROFILES = ROOT / "contracts" / "design_profiles"


class DesignSourceProvenanceContract(unittest.TestCase):
    def test_catalog_is_closed_and_every_invariant_resolves_or_declares_a_gap(self):
        from scripts.quality.design_sources.catalog import load_catalog
        from scripts.quality.design_sources.resolver import resolve_invariant

        catalog = load_catalog()
        active = json.loads((PROFILES / "_index.json").read_text(encoding="utf-8"))[
            "active_design_profiles"
        ]
        for profile in active:
            data = json.loads((PROFILES / f"{profile}.json").read_text(encoding="utf-8"))
            for invariant in data["invariants"]:
                self.assertEqual(
                    1,
                    int("clause_id" in invariant) + int("provenance_gap" in invariant),
                    f"{profile}/{invariant['invariant_id']}",
                )
                resolution = resolve_invariant(profile, invariant, catalog=catalog)
                self.assertIn(resolution["status"], {"resolved", "gap"})

    def test_clause_tuple_and_scope_mutations_red(self):
        from scripts.quality.design_sources.catalog import load_documents
        from scripts.quality.design_sources.schema import validate_documents

        documents = load_documents(validate=False)
        validate_documents(documents)
        forged = deepcopy(documents)
        clause = next(row for doc in forged for row in doc.get("clauses", []))
        clause["exactness"] = "source-exact"
        with self.assertRaises(ValueError):
            validate_documents(forged)

        forged = deepcopy(documents)
        clause = next(row for doc in forged for row in doc.get("clauses", []))
        clause["scope"]["invariant_ids"] = []
        with self.assertRaises(ValueError):
            validate_documents(forged)

    def test_gap_or_perceptual_evidence_cannot_be_pass_eligible(self):
        from scripts.quality.design_sources.resolver import resolve_invariant

        gap = resolve_invariant("apple-dark", {
            "invariant_id": "synthetic",
            "aspect": "component-button",
            "provenance_gap": {
                "reason": "no approved reference",
                "required_resolution": "approved-reference-or-owner-ratification",
            },
        })
        self.assertEqual("gap", gap["status"])
        self.assertFalse(gap["pass_eligible"])

    def test_showcase_rejects_a_forged_bare_pass(self):
        from scripts.rendering.showcase.showcase import _row

        with self.assertRaises(ValueError):
            _row({
                "invariant_id": "forged",
                "aspect": "page-shell",
                "status": "pass",
                "law": "unsupported",
                "doc_cite": "docs/design/pageshell.md",
            })


if __name__ == "__main__":
    unittest.main()

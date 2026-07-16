"""Closed proof for the operator-approved pre-W3 dashboard reference pack."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from scripts.quality.reference_pack.codec import sha256_path
from scripts.quality.reference_pack.schema import load_manifest, validate_manifest


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "contracts/reference_packs/dashboard-pre-w3/manifest.json"


class DashboardReferencePackContract(unittest.TestCase):
    def test_manifest_is_closed_and_operator_approved(self):
        manifest = load_manifest(MANIFEST)
        self.assertEqual([], validate_manifest(manifest))
        self.assertEqual("R-W3-VIS-REF-1", manifest["approval"]["clause_id"])
        self.assertNotIn("http", json.dumps(manifest["frozen_source"]))
        self.assertNotIn(".git", json.dumps(manifest["frozen_source"]))

    def test_pack_is_frozen_complete_and_hash_bound(self):
        manifest = load_manifest(MANIFEST)
        self.assertEqual("frozen", manifest["capture_status"])
        self.assertFalse(manifest["cannot_mark_done"])
        expected = {
            (theme, width)
            for theme in ("liquid-glass", "carbon", "apple-dark")
            for width in (1280, 390)
        }
        captures = manifest["captures"]
        self.assertEqual(expected, {(row["theme"], row["viewport"]["width"]) for row in captures})
        self.assertEqual(6, len(captures))
        fixture = ROOT / manifest["frozen_source"]["fixture"]
        self.assertTrue(fixture.is_file())
        for row in captures:
            for key in ("screenshot", "facts", "provenance"):
                artifact = ROOT / row[key]["path"]
                self.assertTrue(artifact.is_file(), f"missing {artifact}")
                self.assertEqual(row[key]["sha256"], sha256_path(artifact))

    def test_authority_is_per_aspect_and_official_precedence_is_explicit(self):
        manifest = load_manifest(MANIFEST)
        ownership = manifest["aspect_ownership"]
        self.assertEqual(
            {"orientation", "page-gutter", "liquid-content-edge", "apple-content-edge",
             "selector-edge", "group-edge", "row-divider"},
            set(ownership),
        )
        self.assertTrue(all(row["source_mode"] == "measured-reference" for row in ownership.values()))
        excluded = {row["aspect"] for row in manifest["official_precedence_exclusions"]}
        self.assertEqual({"liquid-content-material", "carbon-content-layering"}, excluded)


if __name__ == "__main__":
    unittest.main()

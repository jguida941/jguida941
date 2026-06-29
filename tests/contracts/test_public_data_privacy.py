"""Red-first PUBLIC DATA PRIVACY contract — authority: owner privacy rule.

site/data/profile_snapshot.json is served on GitHub Pages and fetched by the web
dashboard, so it IS the public profile — one curl away. The static index.html being
clean is NOT enough (the sensitive data arrives client-side from this JSON). The owner
rule: the internal token mode (whether the bot ran authenticated) and any credential
must never appear on the public profile; private-repo COUNTS/metadata are allowed,
contents and tokens are not.

Guards the committed public JSON + the scrubber that keeps it clean each pipeline run.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "scripts").is_dir() and (parent / "tests").is_dir():
            return parent
    raise RuntimeError("repo root not found")


ROOT = _repo_root()
PUBLIC_JSON = ROOT / "site" / "data" / "profile_snapshot.json"
# Credential / internal-posture markers that must never reach the public artifact.
BANNED = ("token_mode", "ghp_", "github_pat_", "gho_", "ghs_", "Bearer ", "Authorization")


class PublicDataPrivacyContract(unittest.TestCase):
    def setUp(self):
        self.text = PUBLIC_JSON.read_text(encoding="utf-8")
        self.data = json.loads(self.text)

    def test_no_credential_markers_anywhere(self):
        hits = [b for b in BANNED if b in self.text]
        self.assertEqual([], hits, f"public snapshot JSON must not contain credential markers: {hits}")

    def test_data_quality_carries_no_token_field(self):
        dq = self.data.get("data_quality", {})
        token_keys = [k for k in dq if "token" in k.lower()]
        self.assertEqual([], token_keys, f"data_quality must not expose token fields: {token_keys}")

    def test_scrubber_strips_token_fields_but_keeps_health(self):
        """Unit-guard the scrubber the pipeline runs every publish."""
        from scripts.pipeline.render_outputs import _public_dashboard_data
        out = _public_dashboard_data(
            {"data_quality": {"token_mode": "authenticated", "ci_status": "ok", "ci_note": "x"},
             "username": "u"}
        )
        self.assertNotIn("token_mode", out["data_quality"])
        self.assertEqual("ok", out["data_quality"]["ci_status"], "public source health must be preserved")
        self.assertEqual("u", out["username"], "non-sensitive fields must pass through")


if __name__ == "__main__":
    unittest.main()

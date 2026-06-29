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

    def test_activity_aggregations_are_counts_only(self):
        """LOCK the invariants that make the web calendar/heatmap data safe — against
        ADVERSARIAL input. Events/calendar must reduce to numbers + clean dates +
        whitelisted event labels; no repo name, URL, commit message, payload, hostile
        type, or hostile date string may survive into the public JSON."""
        from scripts.pipeline.compute_metrics import (
            _WEB_EVENT_LABELS, _activity_rhythm, _public_contribution_calendar,
        )
        hostile_events = [
            {"type": "PushEvent", "created_at": "2026-06-01T13:00:00Z",
             "repo": {"name": "jguida941/secret-private-repo", "url": "https://x/secret"},
             "payload": {"commits": [{"message": "CONFIDENTIAL refactor", "sha": "deadbeef"}]},
             "actor": {"login": "someone"}},
            {"type": "EvilEvent<script>", "created_at": "2026-06-01T14:00:00Z",
             "repo": {"name": "another-private"}},  # unmapped type must be dropped
            "not-a-dict", None, {"type": "PushEvent"},  # missing created_at
        ]
        rhythm = _activity_rhythm(hostile_events)
        cal = _public_contribution_calendar({"totalContributions": 5, "weeks": [{"contributionDays": [
            {"date": "2026-06-01", "contributionCount": 3},
            {"date": "<img onerror=alert(1)>", "contributionCount": 9},  # hostile date dropped
            {"date": "2026-06-02", "contributionCount": -4},  # negative coerced to 0
        ]}]})
        blob = json.dumps({"rhythm": rhythm, "calendar": cal})
        for leak in ("secret-private-repo", "CONFIDENTIAL", "deadbeef", "payload", "commits",
                     "message", "actor", "login", "EvilEvent", "<script>", "onerror", "<img"):
            self.assertNotIn(leak, blob, f"aggregation leaked {leak!r} into the public JSON")
        # structural invariants
        self.assertEqual({"matrix", "event_mix", "total", "timezone"}, set(rhythm))
        self.assertEqual(7, len(rhythm["matrix"]))
        self.assertTrue(all(len(row) == 24 and all(isinstance(c, int) for c in row) for row in rhythm["matrix"]))
        self.assertTrue(set(rhythm["event_mix"]).issubset(set(_WEB_EVENT_LABELS.values())),
                        "event_mix keys must come only from the fixed label whitelist")
        self.assertIsInstance(rhythm["total"], int)
        for week in cal["weeks"]:
            for day in week:
                self.assertEqual({"date", "count"}, set(day), "calendar day must be date+count only")
                self.assertRegex(day["date"], r"^\d{4}-\d{2}-\d{2}$", "date must be clean ISO")
                self.assertIsInstance(day["count"], int)
                self.assertGreaterEqual(day["count"], 0)

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

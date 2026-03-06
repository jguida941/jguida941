import json
from pathlib import Path
import unittest
from unittest.mock import patch

from scripts.collect_data import CollectedProfileData
from scripts.compute_metrics import compute_profile_model


class ComputeMetricsIntegrationTests(unittest.TestCase):
    def test_compute_profile_model_from_fixture_payload(self):
        fixture_path = Path("tests/fixtures/sample_collected_data.json")
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        collected = CollectedProfileData(**payload)

        with patch(
            "scripts.compute_metrics.gh.get_repo_commits_last_n_weeks",
            return_value=[1] * 12,
        ), patch(
            "scripts.compute_metrics.gh.get_releases_last_n_days",
            return_value=1,
        ):
            model = compute_profile_model(collected, logger=lambda *_args, **_kwargs: None)

        self.assertIn("snapshot", model)
        self.assertIn("scorecard", model)
        self.assertIn("dashboard_data", model)
        self.assertEqual(model["snapshot"]["total_stars"], 7)
        self.assertEqual(model["snapshot"]["public_scope_commits"], 123)
        self.assertEqual(model["scorecard"]["last_year_contributions"], 321)
        self.assertEqual(model["data_quality"]["commits_status"], "ok")
        self.assertEqual(model["dashboard_data"]["username"], "jguida941")


if __name__ == "__main__":
    unittest.main()

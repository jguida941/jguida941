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
        ), patch(
            "scripts.compute_metrics.gh.get_merged_prs_last_n_days",
            return_value=9,
        ):
            model = compute_profile_model(collected, logger=lambda *_args, **_kwargs: None)

        self.assertIn("snapshot", model)
        self.assertIn("scorecard", model)
        self.assertIn("dashboard_data", model)
        self.assertEqual(model["snapshot"]["total_stars"], 7)
        self.assertEqual(model["snapshot"]["public_scope_commits"], 123)
        self.assertEqual(model["snapshot"]["prs_merged"], 9)
        self.assertEqual(model["scorecard"]["last_year_contributions"], 321)
        self.assertEqual(model["data_quality"]["commits_status"], "ok")
        self.assertEqual(model["dashboard_data"]["username"], "jguida941")

    def test_current_streak_ignores_future_zero_days(self):
        fixture_path = Path("tests/fixtures/sample_collected_data.json")
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        payload["calendar"] = {
            "totalContributions": 12,
            "weeks": [
                {
                    "contributionDays": [
                        {"date": "2026-03-03", "contributionCount": 4, "weekday": 2},
                        {"date": "2026-03-04", "contributionCount": 3, "weekday": 3},
                        {"date": "2026-03-05", "contributionCount": 5, "weekday": 4},
                        {"date": "2099-01-01", "contributionCount": 0, "weekday": 5},
                    ]
                }
            ],
        }
        collected = CollectedProfileData(**payload)

        model = compute_profile_model(
            collected,
            logger=lambda *_args, **_kwargs: None,
            allow_network_calls=False,
        )

        self.assertEqual(model["snapshot"]["streak_days"], 3)


if __name__ == "__main__":
    unittest.main()

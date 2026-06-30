"""P5-DATA — semantic-TDD on the ACTUAL DATA (authority: data honesty).

Design + structure are under contract; the COMPUTED METRICS were not — so a misleading
figure shipped live: the scorecard showed "median ~204 days · since last push" while the
same snapshot recorded pushes TODAY. The number was a real median across all ~68 public
repos (half archived coursework), but the LABEL lied about its meaning. Nothing tested it.

These contracts make the DATA honest, the same way the design contracts make the look
honest: a metric's presented value + label must match its TRUE meaning and must not
contradict another signal in the same snapshot.
"""
from __future__ import annotations

import types
import unittest
from datetime import datetime, timedelta, timezone


class DataSemanticsContract(unittest.TestCase):
    def test_engineering_exposes_the_true_last_push_not_only_a_median(self):
        """`_build_engineering_metrics` must expose `days_since_last_push` = the FRESHEST repo's
        age (the user's real last push), so a stale-looking median across all repos can stop
        being presented as "since last push". Freshest <= median, and is non-negative."""
        from scripts.pipeline.compute_metrics import _build_engineering_metrics
        now = datetime(2026, 6, 29, tzinfo=timezone.utc)

        def _iso(days_ago: int) -> str:
            return (now - timedelta(days=days_ago)).isoformat().replace("+00:00", "Z")

        repos = [
            {"name": "fresh-today", "pushed_at": _iso(0)},
            {"name": "stale-300d", "pushed_at": _iso(300)},
            {"name": "stale-100d", "pushed_at": _iso(100)},
        ]
        collected = types.SimpleNamespace(calendar={}, repo_counts={}, private_repos=[])
        m = _build_engineering_metrics(collected, repos, [], now)
        self.assertIn("days_since_last_push", m,
                      "engineering metrics must expose days_since_last_push (the true last push)")
        self.assertEqual(m["days_since_last_push"], 0,
                         "days_since_last_push must be the FRESHEST repo's age (pushed today => 0)")
        self.assertLessEqual(m["days_since_last_push"], m["median_days_since_push"],
                             "the freshest push cannot be staler than the median across all repos")

    def test_no_presented_metric_shows_a_median_as_your_last_push(self):
        """The exact dishonesty the owner caught: a MEDIAN-across-all-repos value presented under a
        'last push' / 'last commit' label, which reads as 'you haven't pushed in N days'. No
        presented scorecard metric may pair a last-push label with the median key, and the honest
        days_since_last_push must be the one presented."""
        from scripts.contracts.profile_contract import SCORECARD_METRICS
        for metric in SCORECARD_METRICS:
            text = f"{metric.get('label', '')} {metric.get('detail', '')}".lower()
            if "last push" in text or "last commit" in text:
                self.assertNotEqual(
                    metric.get("key"), "median_days_since_push",
                    "a 'last push' metric must NOT bind the median across all repos (reads as inactivity)")
        keys = {metric.get("key") for metric in SCORECARD_METRICS}
        self.assertIn("days_since_last_push", keys,
                      "the scorecard must present the honest last-push metric (days_since_last_push)")

    def test_dashboard_binds_the_honest_last_push_metric(self):
        """The generated dashboard must bind the honest freshest-push metric, never the median
        under a last-push caption."""
        from scripts.pipeline.web_render import render_dashboard
        html = render_dashboard()
        self.assertIn("scorecard.days_since_last_push", html,
                      "the dashboard must bind the honest last-push metric (days_since_last_push)")


if __name__ == "__main__":
    unittest.main()

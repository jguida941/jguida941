import unittest

from scripts.generate_contribution_panel import _compute_streaks


class ContributionPanelTests(unittest.TestCase):
    def test_compute_streaks_ignores_future_days(self):
        days = [
            {"date": "2026-03-03", "contributionCount": 1},
            {"date": "2026-03-04", "contributionCount": 2},
            {"date": "2026-03-05", "contributionCount": 3},
            {"date": "2099-01-01", "contributionCount": 0},
        ]

        current, longest = _compute_streaks(days)

        self.assertEqual(current, 3)
        self.assertEqual(longest, 3)


if __name__ == "__main__":
    unittest.main()


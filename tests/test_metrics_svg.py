import unittest

from scripts.metrics_svg import parse_metrics_svg_text, check_metrics


class MetricsSvgTests(unittest.TestCase):
    def test_parse_supports_repository_and_repositories_labels(self):
        text = """
        <svg>
          <text>1 Repository</text>
          <text>0 Stargazers</text>
          <text>0 Releases</text>
        </svg>
        """
        parsed = parse_metrics_svg_text(text)
        self.assertEqual(parsed.repositories, 1)
        self.assertEqual(parsed.stargazers, 0)
        self.assertEqual(parsed.releases, 0)

    def test_parse_supports_plural_repositories_label(self):
        text = """
        <svg>
          <text>66 Repositories</text>
          <text>60 Stargazers</text>
          <text>11 Releases</text>
        </svg>
        """
        parsed = parse_metrics_svg_text(text)
        self.assertEqual(parsed.repositories, 66)
        self.assertEqual(parsed.stargazers, 60)
        self.assertEqual(parsed.releases, 11)

    def test_sanity_check_only_requires_repository_by_default(self):
        text = "<svg><text>1 Repository</text></svg>"
        parsed = parse_metrics_svg_text(text)
        result = check_metrics(parsed)
        self.assertTrue(result.ok)
        self.assertEqual(len(result.warnings), 2)

    def test_sanity_check_can_enforce_thresholds(self):
        text = """
        <svg>
          <text>66 Repositories</text>
          <text>60 Stargazers</text>
          <text>11 Releases</text>
        </svg>
        """
        parsed = parse_metrics_svg_text(text)
        result = check_metrics(parsed, stargazers_min=70, releases_min=12)
        self.assertFalse(result.ok)
        self.assertIn("Stargazers below threshold: 60 < 70", result.failures)
        self.assertIn("Releases below threshold: 11 < 12", result.failures)


if __name__ == "__main__":
    unittest.main()

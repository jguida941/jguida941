import unittest
from unittest.mock import patch

from scripts.triage import build_triage_report, has_severity_at_or_above, ranked_open_findings
from scripts.validate_generated_profile import ValidationResult


class TriageTests(unittest.TestCase):
    def test_build_triage_report_includes_critical_for_validation_errors(self):
        with patch(
            "scripts.triage.validate_profile",
            return_value=ValidationResult(
                errors=("missing required section",),
                warnings=(),
            ),
        ), patch("scripts.triage._load_snapshot", return_value={}), patch(
            "scripts.triage.actions_audit.fetch_runs",
            return_value=[],
        ):
            report = build_triage_report(workflow="Generate Metrics", run_limit=5)

        ids = {finding["finding_id"]: finding for finding in report["findings"]}
        self.assertEqual(report["schema"]["name"], "profile_triage_report")
        self.assertEqual(report["schema"]["version"], "1.0.0")
        self.assertIn("validation-errors", ids)
        self.assertEqual(ids["validation-errors"]["severity"], "critical")

    def test_has_severity_at_or_above(self):
        report = {
            "findings": [
                {"severity": "low"},
                {"severity": "high"},
            ]
        }
        self.assertTrue(has_severity_at_or_above(report, "medium"))
        self.assertFalse(has_severity_at_or_above(report, "critical"))

    def test_ranked_open_findings_orders_by_severity_then_confidence(self):
        report = {
            "findings": [
                {"finding_id": "a", "severity": "medium", "status": "open", "confidence": 0.9},
                {"finding_id": "b", "severity": "high", "status": "open", "confidence": 0.2},
                {"finding_id": "c", "severity": "high", "status": "open", "confidence": 0.8},
                {"finding_id": "d", "severity": "low", "status": "closed", "confidence": 1.0},
            ]
        }
        ranked = ranked_open_findings(report, min_severity="low", limit=3)
        self.assertEqual([item["finding_id"] for item in ranked], ["c", "b", "a"])


if __name__ == "__main__":
    unittest.main()

import tempfile
import json
from pathlib import Path
from contextlib import redirect_stdout
import io
import unittest
from unittest.mock import patch

from scripts.branch_protection import BranchProtectionAudit
from scripts.profile_cli import main
from scripts.validate_generated_profile import ValidationResult


class ProfileCliTests(unittest.TestCase):
    def test_cli_sanity_check_metrics_passes_with_repository_value(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            svg = Path(tmp_dir) / "metrics.general.svg"
            svg.write_text("<svg><text>1 Repository</text></svg>", encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                rc = main(["check-metrics", "--path", str(svg)])
            self.assertEqual(rc, 0)

    def test_cli_sanity_check_metrics_fails_when_file_missing(self):
        with redirect_stdout(io.StringIO()):
            rc = main(["check-metrics", "--path", "does-not-exist.svg"])
        self.assertEqual(rc, 1)

    def test_cli_doctor_runs(self):
        with redirect_stdout(io.StringIO()):
            rc = main(["doctor"])
        self.assertEqual(rc, 0)

    def test_cli_triage_runs_with_mocked_inputs(self):
        with patch(
            "scripts.triage.validate_profile",
            return_value=ValidationResult(errors=(), warnings=()),
        ), patch("scripts.triage._load_snapshot", return_value={}), patch(
            "scripts.triage.actions_audit.fetch_runs",
            return_value=[],
        ):
            with redirect_stdout(io.StringIO()):
                rc = main(["triage", "--limit", "2", "--fail-on", "none"])
        self.assertEqual(rc, 0)

    def test_cli_generate_profile_fixture_runs(self):
        with patch(
            "scripts.profile_pipeline.run_profile_pipeline_from_fixture",
        ) as mock_fixture_run, patch(
            "scripts.validate_generated_profile.validate_profile",
            return_value=ValidationResult(errors=(), warnings=()),
        ):
            with redirect_stdout(io.StringIO()):
                rc = main(
                    [
                        "generate-profile",
                        "--validate",
                        "--fixture",
                        "tests/fixtures/sample_collected_data.json",
                    ]
                )
        self.assertEqual(rc, 0)
        mock_fixture_run.assert_called_once()

    def test_cli_triage_summary_reads_report(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "triage_report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "findings": [
                            {
                                "finding_id": "token-missing",
                                "severity": "high",
                                "status": "open",
                                "confidence": 0.95,
                                "fix_hint": "set a token",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                rc = main(["triage-summary", "--input", str(report_path), "--min-severity", "low"])
        self.assertEqual(rc, 0)

    def test_cli_branch_protection_audit_and_fail_on_missing(self):
        audit = BranchProtectionAudit(
            repo="jguida941/stats",
            branch="main",
            required_checks=["Test Profile Pipeline"],
            configured_checks=[],
            missing_checks=["Test Profile Pipeline"],
            extra_checks=[],
        )
        with patch(
            "scripts.branch_protection.audit_required_checks",
            return_value=audit,
        ):
            with redirect_stdout(io.StringIO()):
                rc = main(
                    [
                        "branch-protection",
                        "--repo",
                        "jguida941/stats",
                        "--fail-on-missing",
                    ]
                )
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()

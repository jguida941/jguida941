import unittest
from unittest.mock import Mock, patch
import subprocess

from scripts.branch_protection import apply_required_checks, audit_required_checks


class BranchProtectionTests(unittest.TestCase):
    def test_audit_required_checks_detects_missing(self):
        with patch(
            "scripts.gh_cli.subprocess.run",
            return_value=Mock(stdout='{"required_status_checks":{"contexts":["Test Profile Pipeline"]}}'),
        ):
            audit = audit_required_checks(
                repo="jguida941/stats",
                branch="main",
                required_checks=["Test Profile Pipeline", "Build Analytics & README"],
            )
        self.assertEqual(audit.missing_checks, ["Build Analytics & README"])

    def test_apply_required_checks_sends_patch_call(self):
        with patch(
            "scripts.gh_cli.subprocess.run",
            return_value=Mock(stdout="{}"),
        ) as mocked_run:
            apply_required_checks(
                repo="jguida941/stats",
                branch="main",
                required_checks=["Test Profile Pipeline"],
            )

        cmd = mocked_run.call_args[0][0]
        self.assertIn("PATCH", cmd)
        self.assertIn("contexts[]=Test Profile Pipeline", cmd)

    def test_apply_required_checks_creates_protection_when_unprotected(self):
        patch_error = subprocess.CalledProcessError(
            returncode=1,
            cmd=["gh"],
            stderr="gh: Branch not protected (HTTP 404)",
        )
        with patch(
            "scripts.gh_cli.subprocess.run",
            side_effect=[patch_error, Mock(stdout="{}")],
        ) as mocked_run:
            apply_required_checks(
                repo="jguida941/stats",
                branch="main",
                required_checks=["Test Profile Pipeline"],
            )

        first_cmd = mocked_run.call_args_list[0][0][0]
        second_cmd = mocked_run.call_args_list[1][0][0]
        self.assertIn("PATCH", first_cmd)
        self.assertIn("PUT", second_cmd)


if __name__ == "__main__":
    unittest.main()

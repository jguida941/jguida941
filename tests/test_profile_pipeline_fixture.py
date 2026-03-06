import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from scripts.profile_pipeline import run_profile_pipeline_from_fixture


class ProfilePipelineFixtureTests(unittest.TestCase):
    def test_fixture_pipeline_runs_without_network_calls(self):
        fixture_path = Path("tests/fixtures/sample_collected_data.json").resolve()
        template_path = Path("templates/README.md.tpl").resolve()

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            (tmp_root / "templates").mkdir(parents=True, exist_ok=True)
            shutil.copy(template_path, tmp_root / "templates" / "README.md.tpl")

            original_cwd = Path.cwd()
            os.chdir(tmp_root)
            try:
                with patch(
                    "scripts.compute_metrics.gh.get_repo_commits_last_n_weeks",
                    side_effect=AssertionError("network lookup should not run"),
                ), patch(
                    "scripts.compute_metrics.gh.paginated_get",
                    side_effect=AssertionError("network lookup should not run"),
                ), patch(
                    "scripts.profile_helpers.gh.get_repo_ci_state",
                    side_effect=AssertionError("network lookup should not run"),
                ):
                    run_profile_pipeline_from_fixture(str(fixture_path), logger=lambda *_args, **_kwargs: None)
            finally:
                os.chdir(original_cwd)

            self.assertTrue((tmp_root / "README.md").exists())
            self.assertTrue((tmp_root / "site/data/profile_snapshot.json").exists())
            self.assertTrue((tmp_root / "assets/raw_snapshot.svg").exists())


if __name__ == "__main__":
    unittest.main()

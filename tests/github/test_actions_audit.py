import unittest
from unittest.mock import Mock, patch

from scripts.github.actions_audit import WorkflowRun, fetch_runs, summarize_runs


class ActionsAuditTests(unittest.TestCase):
    def test_fetch_runs_handles_missing_gh_cli(self):
        with patch("scripts.github.gh_cli.subprocess.run", side_effect=FileNotFoundError()):
            with self.assertRaisesRegex(RuntimeError, "GitHub CLI not found"):
                fetch_runs("Generate Metrics")

    def test_fetch_runs_parses_items_and_tolerates_bad_database_id(self):
        payload = '[{"databaseId":"bad-id","workflowName":"Generate Metrics","displayTitle":"run","status":"completed","conclusion":"success","createdAt":"2026-03-06T00:00:00Z","url":"https://example.com"}]'
        with patch(
            "scripts.github.gh_cli.subprocess.run",
            return_value=Mock(stdout=payload),
        ):
            runs = fetch_runs("Generate Metrics")
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0].database_id, 0)

    def test_summarize_runs_counts_states_and_limits_failures(self):
        runs = [
            WorkflowRun(
                database_id=1,
                workflow_name="Generate Metrics",
                display_title="run 1",
                status="completed",
                conclusion="failure",
                created_at="2026-03-06T01:00:00Z",
                url="https://example.com/1",
            ),
            WorkflowRun(
                database_id=2,
                workflow_name="Generate Metrics",
                display_title="run 2",
                status="completed",
                conclusion="success",
                created_at="2026-03-06T02:00:00Z",
                url="https://example.com/2",
            ),
            WorkflowRun(
                database_id=3,
                workflow_name="Generate Metrics",
                display_title="run 3",
                status="completed",
                conclusion="failure",
                created_at="2026-03-06T03:00:00Z",
                url="https://example.com/3",
            ),
        ]

        summary = summarize_runs(runs, failure_limit=1)
        self.assertEqual(summary.total, 3)
        self.assertEqual(summary.by_state["failure"], 2)
        self.assertEqual(summary.by_state["success"], 1)
        self.assertEqual(len(summary.recent_failures), 1)
        self.assertEqual(summary.recent_failures[0].database_id, 3)


class ProfileCIExecutionTests(unittest.TestCase):
    """Profile-repository Actions history is distinct from configured workflows."""

    def test_completed_failed_and_running_are_distinct_in_dated_sample(self):
        from scripts.github.actions_audit import normalize_profile_ci_runs

        rows = [
            {"databaseId": 103, "workflowName": "Deploy Profile Site",
             "status": "in_progress", "conclusion": "",
             "createdAt": "2026-10-15T12:02:00Z", "event": "workflow_run", "headBranch": "main"},
            {"databaseId": 102, "workflowName": "Generate Metrics",
             "status": "completed", "conclusion": "failure",
             "createdAt": "2026-10-15T12:01:00Z", "event": "schedule", "headBranch": "main"},
            {"databaseId": 101, "workflowName": "Generate Metrics",
             "status": "completed", "conclusion": "success",
             "createdAt": "2026-10-15T12:00:00Z", "event": "workflow_dispatch", "headBranch": "main"},
        ]
        sample = normalize_profile_ci_runs(
            rows, "jguida941/jguida941", "2026-10-15T12:03:00Z", limit=12)
        self.assertEqual("profile-ci-execution/v1", sample["schema"])
        self.assertEqual("available", sample["status"])
        self.assertEqual("jguida941/jguida941", sample["repository"])
        self.assertEqual(3, sample["observed_runs"])
        self.assertEqual([103, 102, 101], [item["run_id"] for item in sample["runs"]])
        self.assertEqual(["in_progress", "failure", "success"],
                         [item["outcome"] for item in sample["runs"]])
        self.assertEqual("2026-10-15T12:03:00Z", sample["observed_at"])

    def test_invalid_and_unavailable_runs_never_look_like_success_or_zero(self):
        from scripts.github.actions_audit import normalize_profile_ci_runs

        absent = normalize_profile_ci_runs(
            None, "jguida941/jguida941", "2026-10-15T12:03:00Z")
        self.assertEqual("unavailable", absent["status"])
        self.assertIsNone(absent["observed_runs"])
        self.assertEqual([], absent["runs"])
        empty = normalize_profile_ci_runs(
            [], "jguida941/jguida941", "2026-10-15T12:03:00Z")
        self.assertEqual("empty", empty["status"])
        self.assertEqual(0, empty["observed_runs"])
        invalid = normalize_profile_ci_runs(
            [{"databaseId": True, "workflowName": "wrong", "status": "completed",
              "conclusion": "success", "createdAt": "2026-10-15T12:00:00Z"},
             {"databaseId": 301, "workflowName": "<script>bad</script>",
              "status": "completed", "conclusion": "failure",
              "createdAt": "2026-10-15T12:01:00Z"}],
            "jguida941/jguida941", "2026-10-15T12:03:00Z")
        self.assertEqual("partial", invalid["status"])
        self.assertEqual(1, invalid["observed_runs"])
        self.assertEqual("failure", invalid["runs"][0]["outcome"])
        self.assertNotIn("url", invalid["runs"][0])

    def test_cli_failure_is_unavailable_not_empty(self):
        from scripts.github.actions_audit import collect_profile_ci_runs

        with patch("scripts.github.actions_audit.run_json", side_effect=RuntimeError("unavailable")):
            sample = collect_profile_ci_runs("jguida941/jguida941")
        self.assertEqual("unavailable", sample["status"])
        self.assertIsNone(sample["observed_runs"])
        self.assertEqual([], sample["runs"])


if __name__ == "__main__":
    unittest.main()

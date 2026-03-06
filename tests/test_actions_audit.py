import unittest
from unittest.mock import Mock, patch

from scripts.actions_audit import WorkflowRun, fetch_runs, summarize_runs


class ActionsAuditTests(unittest.TestCase):
    def test_fetch_runs_handles_missing_gh_cli(self):
        with patch("scripts.actions_audit.subprocess.run", side_effect=FileNotFoundError()):
            with self.assertRaisesRegex(RuntimeError, "GitHub CLI not found"):
                fetch_runs("Generate Metrics")

    def test_fetch_runs_parses_items_and_tolerates_bad_database_id(self):
        payload = '[{"databaseId":"bad-id","workflowName":"Generate Metrics","displayTitle":"run","status":"completed","conclusion":"success","createdAt":"2026-03-06T00:00:00Z","url":"https://example.com"}]'
        with patch(
            "scripts.actions_audit.subprocess.run",
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


if __name__ == "__main__":
    unittest.main()

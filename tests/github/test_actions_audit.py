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

    def test_execution_flows_to_public_snapshot_without_changing_adoption(self):
        """Real run outcomes and configured workflow counts are separate meanings."""
        from dataclasses import replace
        from scripts.github.actions_audit import normalize_profile_ci_runs
        from scripts.pipeline.compute_metrics import compute_profile_model
        from scripts.pipeline.render_outputs import _public_dashboard_data
        from tests.pipeline.test_compute_metrics_accuracy import AccuracyTests

        observed = normalize_profile_ci_runs([{
            "databaseId": 422, "workflowName": "Generate Metrics",
            "status": "completed", "conclusion": "failure",
            "createdAt": "2026-10-15T12:01:00Z",
            "event": "schedule", "headBranch": "main",
        }], "jguida941/jguida941", "2026-10-15T12:03:00Z")
        collected = AccuracyTests()._collected()
        before = compute_profile_model(collected, logger=lambda *_: None,
                                       allow_network_calls=False)
        candidate = replace(collected, ci_execution_observation=observed)
        after = compute_profile_model(candidate, logger=lambda *_: None,
                                      allow_network_calls=False)
        self.assertEqual(before["automation"], after["automation"],
                         "adding execution evidence cannot change configuration adoption")
        self.assertEqual(before["scorecard"]["ci_coverage_pct"],
                         after["scorecard"]["ci_coverage_pct"])
        self.assertEqual(observed, after["dashboard_data"]["ci_execution"])
        self.assertEqual(observed, _public_dashboard_data(after["dashboard_data"])["ci_execution"])

    def test_unhashable_provider_fields_are_partial_not_exceptions(self):
        from scripts.github.actions_audit import normalize_profile_ci_runs

        rows = [{"databaseId": 321, "workflowName": "Workflow", "status": [],
                 "conclusion": {"unexpected": True}, "createdAt": "2026-10-15T12:00:00Z"}]
        sample = normalize_profile_ci_runs(rows, "jguida941/jguida941", "2026-10-15T12:01:00Z")
        self.assertEqual("partial", sample["status"])
        self.assertEqual("unknown", sample["runs"][0]["outcome"])

    def test_cli_failure_is_unavailable_not_empty(self):
        from scripts.github.actions_audit import collect_profile_ci_runs

        with patch("scripts.github.actions_audit.run_json", side_effect=RuntimeError("unavailable")):
            sample = collect_profile_ci_runs("jguida941/jguida941")
        self.assertEqual("unavailable", sample["status"])
        self.assertIsNone(sample["observed_runs"])
        self.assertEqual([], sample["runs"])


class PublicMultiRepositoryCITimelineTests(unittest.TestCase):
    """Public Actions run history is a sampled cohort, not workflow adoption."""

    def test_public_selection_excludes_private_forks_foreign_owner_and_missing_config(self):
        from scripts.github.actions_audit import select_public_ci_repositories
        def repo(name, *, private=False, fork=False, owner="jguida941", workflow=True,
                 pushed="2026-10-10T00:00:00Z"):
            return {"name": name, "owner": {"login": owner}, "private": private,
                    "fork": fork, "has_ci_workflows": workflow, "pushed_at": pushed}
        rows = [repo("ci-cd-hub"), repo("recent", pushed="2026-10-14T00:00:00Z"),
                repo("hidden", private=True), repo("fork", fork=True),
                repo("foreign", owner="other"), repo("no-ci", workflow=False),
                repo("bad/name"), repo("jguida941")]
        self.assertEqual(
            ["jguida941/jguida941", "jguida941/recent", "jguida941/ci-cd-hub"],
            select_public_ci_repositories(rows, "jguida941"))

    def test_duplicate_repository_envelope_cannot_multiply_run_totals(self):
        """Replayed repo observations must not mint another run or repository."""
        from scripts.github.actions_audit import normalize_public_ci_timeline
        one = {"repository": "jguida941/ci-cd-hub", "runs": [{
            "databaseId": 321, "workflowName": "CI", "status": "completed",
            "conclusion": "failure", "createdAt": "2026-10-14T12:00:00Z",
        }]}
        sample = normalize_public_ci_timeline(
            [one, dict(one)], "jguida941", "2026-10-15T12:00:00Z")
        self.assertEqual(1, sample["observed_runs"])
        self.assertEqual(["jguida941/ci-cd-hub"],
                         [item["repository"] for item in sample["repositories"]])
        self.assertEqual("partial", sample["status"])

    def test_unverified_visibility_is_not_public_permission(self):
        """An absent privacy bit cannot qualify a repository as public."""
        from scripts.github.actions_audit import select_public_ci_repositories
        repo = {"name": "unknown-visibility", "owner": {"login": "jguida941"},
                "fork": False, "has_ci_workflows": True,
                "pushed_at": "2026-10-14T12:00:00Z"}
        self.assertEqual(["jguida941/jguida941"],
                         select_public_ci_repositories([repo], "jguida941"))

    def test_dated_run_identity_is_real_and_unavailable_is_not_zero(self):
        from scripts.github.actions_audit import normalize_public_ci_timeline
        rows = [{"repository": "jguida941/jguida941", "runs": [
            {"databaseId": 1, "workflowName": "CI", "status": "completed",
             "conclusion": "failure", "createdAt": "2026-10-12T00:00:00Z"},
            {"databaseId": 2, "workflowName": "CI", "status": "in_progress",
             "conclusion": None, "createdAt": "2026-10-13T00:00:00Z"},
            {"databaseId": 3, "workflowName": "old", "status": "completed",
             "conclusion": "success", "createdAt": "2026-06-01T00:00:00Z"}]},
            {"repository": "jguida941/ci-cd-hub", "runs": None}]
        sample = normalize_public_ci_timeline(rows, "jguida941", "2026-10-15T00:00:00Z")
        self.assertEqual("partial", sample["status"])
        self.assertEqual(2, sample["observed_runs"])
        self.assertEqual(["in_progress", "failure"],
                         [row["outcome"] for row in sample["repositories"][0]["runs"]])
        self.assertEqual("unavailable", sample["repositories"][1]["status"])
        self.assertIsNone(sample["repositories"][1]["observed_runs"])
        self.assertFalse(sample["repositories"][1]["runs"])


    def test_out_of_window_runs_cannot_mean_zero_in_window(self):
        """A nonempty provider history outside the chart window is not an empty-run proof."""
        from scripts.github.actions_audit import normalize_public_ci_timeline
        sample = normalize_public_ci_timeline([{"repository": "jguida941/jguida941",
            "runs": [{"databaseId": 91, "workflowName": "Old workflow", "status": "completed",
                      "conclusion": "success", "createdAt": "2026-01-01T00:00:00Z"}]}],
            "jguida941", "2026-10-15T12:00:00Z", window_days=84)
        row = sample["repositories"][0]
        self.assertEqual(0, sample["observed_runs"])
        self.assertEqual("partial", sample["status"],
                         "hidden prior runs cannot become a complete zero-run timeline")
        self.assertEqual("partial", row["status"])
        self.assertTrue(row["outside_window"],
                        "mark clipped history separately from actually empty API response")
        self.assertEqual([], row["runs"])

    def test_future_and_healthy_runs_keep_independent_timeline_meaning(self):
        from scripts.github.actions_audit import normalize_public_ci_timeline
        rows = [{"databaseId": 92, "workflowName": "Future", "status": "completed",
                 "conclusion": "failure", "createdAt": "2026-10-16T12:00:00Z"},
                {"databaseId": 93, "workflowName": "Current", "status": "completed",
                 "conclusion": "success", "createdAt": "2026-10-14T12:00:00Z"}]
        s = normalize_public_ci_timeline(
            [{"repository": "jguida941/jguida941", "runs": rows}],
            "jguida941", "2026-10-15T12:00:00Z")
        self.assertEqual(1, s["observed_runs"])
        self.assertEqual("partial", s["status"])
        self.assertEqual([93], [r["run_id"] for r in s["repositories"][0]["runs"]])
        self.assertTrue(s["repositories"][0]["outside_window"])

    def test_real_empty_sample_remains_distinct_from_clipped_history(self):
        from scripts.github.actions_audit import normalize_public_ci_timeline
        s = normalize_public_ci_timeline(
            [{"repository": "jguida941/jguida941", "runs": []}],
            "jguida941", "2026-10-15T12:00:00Z")
        self.assertEqual("empty", s["repositories"][0]["status"])
        self.assertFalse(s["repositories"][0]["outside_window"])

    def test_source_cap_prevents_exact_history_claim(self):
        from scripts.github.actions_audit import normalize_public_ci_timeline
        runs = [{"databaseId": i+1, "workflowName": "CI",
                 "status": "completed", "conclusion": "success",
                 "createdAt": "2026-10-15T00:00:00Z"} for i in range(20)]
        sample = normalize_public_ci_timeline(
            [{"repository": "jguida941/jguida941", "runs": runs}],
            "jguida941", "2026-10-15T12:00:00Z")
        self.assertEqual("partial", sample["status"])
        self.assertTrue(sample["repositories"][0]["truncated"])

    def test_one_provider_failure_does_not_erase_other_real_runs(self):
        from scripts.github.actions_audit import collect_public_ci_timeline
        rows = [{"name": "ci-cd-hub", "owner": {"login": "jguida941"},
                 "private": False, "fork": False,
                 "has_ci_workflows": True, "pushed_at": "2026-10-14T00:00:00Z"}]
        def fetch(command, **kwargs):
            if "ci-cd-hub" in command[command.index("--repo")+1]:
                raise RuntimeError("unavailable")
            return [{"databaseId": 12, "workflowName": "Profile",
                     "status": "completed", "conclusion": "failure",
                     "createdAt": "2026-10-15T11:00:00Z"}]
        with patch("scripts.github.actions_audit.run_json", side_effect=fetch):
            sample = collect_public_ci_timeline(rows, "jguida941")
        self.assertEqual("partial", sample["status"])
        self.assertEqual("failure", sample["repositories"][0]["runs"][0]["outcome"])
        self.assertEqual("unavailable", sample["repositories"][1]["status"])


# Owner-authorized minimal public/private execution metadata shares one carrier.
import json
from scripts.github.actions_audit import (
    collect_public_ci_timeline, normalize_public_ci_timeline, select_public_ci_repositories,
)
from scripts.pipeline.render_outputs import _public_dashboard_data


class RepositoryCITimelineTests(unittest.TestCase):
    owner = "jguida941"
    observed = "2026-11-19T20:00:00Z"

    @classmethod
    def inventory(cls, *, complete=True):
        def row(identity, name, pushed, *, private=False, owner=cls.owner, fork=False):
            return {"id": identity, "name": name, "owner": {"login": owner},
                    "full_name": f"{owner}/{name}", "private": private, "fork": fork,
                    "pushed_at": pushed, "aliases": [f"{owner}/{name}"],
                    "has_ci_workflows": False}
        return {"schema": "profile-repository-inventory/v1",
                "owners": [cls.owner, "semverity-labs"], "complete": complete,
                "rows": [
                    row(101, cls.owner, "2026-11-19T10:00:00Z"),
                    row(102, "profile-private-continuation", "2026-11-19T19:55:00Z", private=True),
                    row(103, "dijkstra-dashboard", "2026-11-19T17:38:34Z"),
                    row(104, "engine", "2026-11-19T19:45:00Z", private=True, owner="semverity-labs"),
                    row(105, "ordinary", "2026-11-19T19:40:00Z"),
                    row(106, "sixth", "2026-11-19T18:00:00Z"),
                    row(107, "older", "2026-11-18T18:00:00Z"),
                    row(108, "fork", "2026-11-19T19:59:00Z", fork=True),
                ]}

    @staticmethod
    def provider_run(identity=301, *, workflow="CI checks", created="2026-11-19T19:49:00Z",
            status="completed", conclusion="success"):
        return {"databaseId": identity, "workflowName": workflow, "status": status,
                "conclusion": conclusion, "createdAt": created,
                "event": "push", "headBranch": "private-feature",
                "displayTitle": "Internal commit title", "logs": "private log body",
                "source": "private source body", "token": "never publish"}

    def normalize(self, observations, **kwargs):
        return normalize_public_ci_timeline(
            observations, self.owner, self.observed,
            repository_inventory=self.inventory(), **kwargs)

    def test_authorized_private_run_metadata_reaches_public_carrier(self):
        sample = self.normalize([{
            "repository": "jguida941/profile-private-continuation", "repository_id": 102,
            "runs": [self.provider_run()],
        }])
        public = _public_dashboard_data({"ci_timeline": sample})["ci_timeline"]
        row = public["repositories"][0]
        self.assertEqual(1, row["observed_runs"])
        self.assertEqual([{"run_id": 301, "workflow": "CI checks", "outcome": "success",
                           "created_at": "2026-11-19T19:49:00Z"}], row["runs"])
        self.assertEqual("jguida941/profile-private-continuation", row["repository"])
        self.assertEqual(102, row["repository_id"])
        self.assertEqual("github:102", row["repository_key"])
        self.assertTrue(row["is_private"])
        self.assertEqual([row["repository"]], row["aliases"])
        self.assertEqual(sample, public)
        for private_body in ("private-feature", "Internal commit title", "private log body",
                             "private source body", "never publish"):
            self.assertNotIn(private_body, json.dumps(public))

    def test_recent_cohort_keeps_private_org_and_retained_workflow_history(self):
        selected = select_public_ci_repositories([], self.owner,
                                                 repository_inventory=self.inventory())
        self.assertEqual([
            "jguida941/jguida941", "jguida941/profile-private-continuation",
            "semverity-labs/engine", "jguida941/ordinary", "jguida941/sixth",
            "jguida941/dijkstra-dashboard",
        ], selected)

    def test_collector_requests_only_minimal_run_metadata_for_the_same_cohort(self):
        with patch("scripts.github.actions_audit.run_json", return_value=[]) as provider:
            sample = collect_public_ci_timeline([], self.owner,
                                                repository_inventory=self.inventory())
        selected = select_public_ci_repositories([], self.owner,
                                                 repository_inventory=self.inventory())
        self.assertEqual(selected, [row["repository"] for row in sample["repositories"]])
        self.assertEqual(selected, [call.args[0][call.args[0].index("--repo") + 1]
                                    for call in provider.call_args_list])
        for call in provider.call_args_list:
            command = call.args[0]
            self.assertEqual("20", command[command.index("--limit") + 1])
            self.assertEqual("databaseId,workflowName,status,conclusion,createdAt",
                             command[command.index("--json") + 1])

    def test_unknown_provider_is_distinct_from_observed_empty_and_clipped_history(self):
        sample = self.normalize([
            {"repository": "jguida941/jguida941", "runs": []},
            {"repository": "jguida941/profile-private-continuation", "runs": None},
            {"repository": "semverity-labs/engine", "runs": {}},
            {"repository": "jguida941/dijkstra-dashboard",
             "runs": [self.provider_run(created="2026-01-01T00:00:00Z")]},
        ])
        self.assertEqual("partial", sample["status"])
        self.assertEqual(0, sample["observed_runs"])
        self.assertEqual([("empty", 0, False), ("unavailable", None, False),
                          ("unavailable", None, False), ("partial", 0, True)],
                         [(row["status"], row["observed_runs"], row["outside_window"])
                          for row in sample["repositories"]])
        for raw in (None, {}):
            unknown = self.normalize([{"repository": "jguida941/jguida941", "runs": raw}])
            self.assertEqual("unavailable", unknown["status"])
            self.assertIsNone(unknown["observed_runs"])
            self.assertIsNone(unknown["repositories"][0]["observed_runs"])

    def test_recent_dijkstra_runs_survive_older_clipped_history(self):
        sample = self.normalize([{"repository": "jguida941/dijkstra-dashboard", "runs": [
            self.provider_run(44579379689, created="2026-11-19T17:38:37Z"),
            self.provider_run(44578962915, created="2026-11-19T17:36:16Z"),
            self.provider_run(1, created="2026-07-22T12:00:00Z"),
        ]}])
        row = sample["repositories"][0]
        self.assertEqual("partial", row["status"])
        self.assertTrue(row["outside_window"])
        self.assertEqual(2, row["observed_runs"])
        self.assertEqual([44579379689, 44578962915], [run["run_id"] for run in row["runs"]])

    def test_alias_identity_admission_rejects_forks_foreign_and_id_conflicts(self):
        inventory = self.inventory()
        inventory["rows"][3]["aliases"] = ["jguida941/legacy-engine", "semverity-labs/engine"]
        sample = normalize_public_ci_timeline([
            {"repository": "semverity-labs/engine", "repository_id": 104, "runs": [self.provider_run()]},
            {"repository": "jguida941/fork", "runs": [self.provider_run(302)]},
            {"repository": "outsider/engine", "runs": [self.provider_run(303)]},
            {"repository": "jguida941/ordinary", "repository_id": 999, "runs": [self.provider_run(304)]},
        ], self.owner, self.observed, repository_inventory=inventory)
        self.assertEqual(["semverity-labs/engine"], [row["repository"] for row in sample["repositories"]])
        self.assertEqual(1, sample["observed_runs"])
        self.assertEqual("partial", sample["status"])
        self.assertEqual("github:104", sample["repositories"][0]["repository_key"])
        self.assertEqual(["jguida941/legacy-engine", "semverity-labs/engine"],
                         sample["repositories"][0]["aliases"])

    def test_provider_run_ids_dates_caps_and_duplicate_envelopes_stay_qualified(self):
        runs = [self.provider_run(True), self.provider_run(301), self.provider_run(301),
                self.provider_run(302, created="2026-11-20T00:00:00Z"),
                self.provider_run(303, status="mystery", conclusion=None)]
        observation = {"repository": "jguida941/profile-private-continuation", "runs": runs}
        sample = self.normalize([observation, dict(observation)])
        self.assertEqual(2, sample["observed_runs"])
        self.assertEqual("partial", sample["status"])
        self.assertEqual([303, 301], [run["run_id"] for run in sample["repositories"][0]["runs"]])
        self.assertEqual(["unknown", "success"],
                         [run["outcome"] for run in sample["repositories"][0]["runs"]])
        self.assertTrue(sample["repositories"][0]["outside_window"])
        capped = self.normalize([{"repository": "jguida941/jguida941",
                                  "runs": [self.provider_run(i + 1) for i in range(21)]}], limit_per_repo=60)
        self.assertEqual(20, capped["sample_limit_per_repo"])
        self.assertEqual(20, capped["observed_runs"])
        self.assertTrue(capped["repositories"][0]["truncated"])
        self.assertEqual("partial", capped["status"])

    def test_credential_shaped_workflow_names_are_omitted_before_public_projection(self):
        credential = "ghp_" + "A" * 36
        sample = self.normalize([{"repository": "jguida941/profile-private-continuation",
                                  "runs": [self.provider_run(workflow=credential), self.provider_run(302)]}])
        self.assertNotIn(credential, json.dumps(sample))
        self.assertEqual([302], [run["run_id"] for run in sample["repositories"][0]["runs"]])
        self.assertEqual(1, sample["observed_runs"])
        self.assertEqual("partial", sample["status"])


if __name__ == "__main__":
    unittest.main()

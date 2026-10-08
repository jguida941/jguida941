import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib

from scripts.pipeline.profile_pipeline import run_profile_pipeline_from_fixture


ROOT = Path(__file__).resolve().parents[2]
METRICS_COMMIT_CONDITION = "success() && steps.gate.outputs.publish == 'true'"
ANALYTICS_COMMIT_CONDITION = METRICS_COMMIT_CONDITION
DEPLOY_JOB_CONDITION = (
    "github.event_name != 'workflow_run' || "
    "(github.event.workflow_run.conclusion == 'success' && "
    "github.event.workflow_run.head_branch == 'main')"
)
MANUAL_VALIDATION_CONDITION = "github.event_name == 'workflow_dispatch'"
PROFILE_PRODUCT_TEST_MODULES = (
    "tests.github.test_github_client",
    "tests.github.test_token_fallback",
    "tests.pipeline.test_compute_metrics_accuracy",
    "tests.pipeline.test_profile_pipeline_fixture",
    "tests.contracts.test_data_semantics",
    "tests.contracts.test_public_data_privacy",
    "tests.contracts.test_design_contract",
    "tests.contracts.test_dashboard_summary",
    "tests.contracts.test_dashboard_destinations",
    "tests.contracts.test_readme_projection",
    "tests.contracts.test_label_legibility",
)
PROFILE_PRODUCT_TEST_ENV = (
    ("PERSONAL_GITHUB_TOKEN", ""),
    ("GITHUB_TOKEN", ""),
    ("GH_TOKEN", ""),
    ("PROFILE_TOKEN_MODE", "none"),
    ("CACHE_DIR", "${{ runner.temp }}/profile-product-tests"),
    ("BYPASS_GITHUB_CACHE", "true"),
)
PROFILE_PAYLOAD_PATHS = (
    "README.md",
    "metrics.general.svg",
    "site/data/profile_snapshot.json",
    "assets/activity_heatmap.svg",
            "assets/dashboard_summary.svg",
            "assets/dashboard_summary_mobile.svg",
    "assets/badges.svg",
    "assets/builder_scorecard.svg",
    "assets/contribution_calendar.svg",
    "assets/currently_working.svg",
    "assets/engineering_cadence.svg",
    "assets/lang_breakdown.svg",
    "assets/now_next_shipped.svg",
    "assets/raw_snapshot.svg",
    "assets/repo_spotlight.svg",
    "assets/streak_summary.svg",
)
PROFILE_ARTIFACT_PATHS = PROFILE_PAYLOAD_PATHS + (
    "site/data/profile_artifact_manifest.json",
)


def _requirement_map(entries):
    dependencies = {}
    for entry in entries:
        requirement = entry.split("#", 1)[0].strip()
        if not requirement:
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)(.*)", requirement)
        if match is None:
            continue
        name = re.sub(r"[-_.]+", "-", match.group(1)).lower()
        suffix = re.sub(r"\s+", "", match.group(2)).lower()
        dependencies[name] = f"{name}{suffix}"
    return dependencies


def _workflow_steps(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    steps = []
    steps_indent = None
    current = []

    for line in lines:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if steps_indent is None:
            if stripped == "steps:":
                steps_indent = indent
            continue
        if stripped and indent <= steps_indent:
            break
        if re.match(rf"^\s{{{steps_indent + 2}}}-\s", line):
            if current:
                steps.append(current)
            current = [line]
        elif current:
            current.append(line)

    if current:
        steps.append(current)
    return steps


def _step_field(step, field):
    key = re.escape(field)
    spellings = "|".join((key, f"'{key}'", f'"{key}"'))
    pattern = re.compile(rf"^\s+(?:-\s+)?(?:{spellings})\s*:\s*(.*?)\s*$")
    for line in step:
        match = pattern.match(line)
        if match:
            return match.group(1)
    return None


def _key_spellings(field):
    key = re.escape(field)
    return "|".join((key, f"'{key}'", f'"{key}"'))


def _mapping_key_occurrences(text, field):
    pattern = re.compile(
        rf"(?:^[ \t]*(?:-[ \t]+)*|[{{,][ \t]*)(?:{_key_spellings(field)})[ \t]*:",
        re.MULTILINE,
    )
    return [match.group(0).strip() for match in pattern.finditer(text)]


def _env_scalar(raw):
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "'\"":
        return raw[1:-1]
    return raw


def _step_env_entries(step):
    entries = []
    env_indent = None
    for line in step:
        if not line.strip():
            continue
        if env_indent is None:
            opener = re.match(
                rf"^(\s*(?:-\s+)?)(?:{_key_spellings('env')})\s*:\s*$", line
            )
            if opener is not None:
                env_indent = len(opener.group(1))
            continue
        indent = len(line) - len(line.lstrip())
        if indent <= env_indent:
            break
        entry = re.match(
            r"^\s*([A-Za-z0-9_.-]+|'[^']*'|\"[^\"]*\")\s*:\s*(.*?)\s*$", line
        )
        if entry is not None:
            entries.append((_env_scalar(entry.group(1)), entry.group(2)))
    return entries


def _step_run_lines(step):
    for index, line in enumerate(step):
        match = re.match(r"^(\s+)run:\s*(.*?)\s*$", line)
        if match is None:
            continue
        run_indent = len(match.group(1))
        inline = match.group(2)
        if inline not in {"|", ">", "|-", ">-"}:
            return [inline]
        commands = []
        for command_line in step[index + 1 :]:
            if command_line.strip() and len(command_line) - len(command_line.lstrip()) <= run_indent:
                break
            commands.append(command_line.strip())
        return commands
    return []


def _step_runs(step, command_prefix):
    return any(
        line == command_prefix or line.startswith(f"{command_prefix} ")
        for line in _step_run_lines(step)
    )


def _step_index(steps, predicate):
    for index, step in enumerate(steps):
        if predicate(step):
            return index
    return None


def _job_condition(path, job_name):
    lines = path.read_text(encoding="utf-8").splitlines()
    in_job = False
    for line in lines:
        if re.fullmatch(rf"  {re.escape(job_name)}:\s*", line):
            in_job = True
            continue
        if in_job and re.match(r"^  [A-Za-z0-9_-]+:\s*$", line):
            break
        if in_job:
            match = re.match(r"^    if:\s*(.*?)\s*$", line)
            if match:
                return match.group(1)
    return None


def _normalize_workflow_condition(value):
    condition = value.strip()
    if condition.startswith("${{") and condition.endswith("}}"):
        condition = condition[3:-2]
    return re.sub(r"\s+", "", condition).replace('"', "'")


def _condition_matches(value, expected):
    return _normalize_workflow_condition(value) == _normalize_workflow_condition(expected)


def _decision_state(decision):
    state = getattr(decision, "state", decision)
    return str(getattr(state, "value", getattr(state, "name", state)))


def _canonical_json_digest(value):
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class _PublicationDecisionValue:
    def __init__(self, name, *, allows_effects):
        self.name = name
        self.value = name
        self.ready = allows_effects
        self.publish = allows_effects
        self.allowed = allows_effects
        self.allows_effects = allows_effects
        self.allows_canonical_writes = allows_effects
        self.reasons = (
            ()
            if allows_effects
            else ("NONCURRENT_CONTRIBUTIONS",)
        )

    @property
    def state(self):
        return self

    def __bool__(self):
        return self.ready

    def __eq__(self, other):
        comparable = getattr(other, "value", getattr(other, "name", other))
        return comparable == self.value

    def __str__(self):
        return self.value


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
                    "scripts.pipeline.compute_metrics.gh.get_repo_commits_last_n_weeks",
                    side_effect=AssertionError("network lookup should not run"),
                ), patch(
                    "scripts.pipeline.compute_metrics.gh.paginated_get",
                    side_effect=AssertionError("network lookup should not run"),
                ), patch(
                    "scripts.pipeline.profile_helpers.gh.get_repo_ci_state",
                    side_effect=AssertionError("network lookup should not run"),
                ):
                    run_profile_pipeline_from_fixture(str(fixture_path), logger=lambda *_args, **_kwargs: None)
            finally:
                os.chdir(original_cwd)

            self.assertTrue((tmp_root / "README.md").exists())
            self.assertTrue((tmp_root / "site/data/profile_snapshot.json").exists())
            self.assertTrue((tmp_root / "assets/raw_snapshot.svg").exists())
            self.assertTrue((tmp_root / "assets/streak_summary.svg").exists())
            metrics_svg = tmp_root / "metrics.general.svg"
            self.assertTrue(metrics_svg.exists())
            metrics_text = metrics_svg.read_text(encoding="utf-8")
            self.assertIn("Repositories", metrics_text)
            self.assertIn("Stargazers", metrics_text)
            self.assertIn("Releases", metrics_text)
            readme_text = (tmp_root / "README.md").read_text(encoding="utf-8")
            self.assertIn("assets/streak_summary.svg", readme_text)

    def test_fixture_declares_explicit_provider_observations(self):
        payload = json.loads(
            Path("tests/fixtures/sample_collected_data.json").read_text(encoding="utf-8")
        )
        observations = payload.get("metric_observations", {})
        self.assertEqual(
            {
                "public_scope_commits",
                "last_year_contributions",
                "releases_30d",
                "prs_merged",
                "recent_public_events",
            },
            set(observations),
        )
        for metric_id, observation in observations.items():
            with self.subTest(metric=metric_id):
                self.assertEqual("profile-provider-observation/v1", observation.get("schema"))
                self.assertEqual(metric_id, observation.get("metric_id"))
                self.assertEqual("ok", observation.get("status"))
                self.assertIs(observation.get("complete"), True)

    def test_previous_snapshot_reader_retains_source_time_and_metric_identity(self):
        from scripts.pipeline.collect_data import _read_previous_snapshot

        previous_payload = {
            "generated_at": "2026-08-25T09:30:00Z",
            "snapshot": {"last_year_contributions": 777},
            "data_quality": {
                "metric_provenance": {
                    "last_year_contributions": {
                        "schema": "profile-provider-observation/v1",
                        "metric_id": "last_year_contributions",
                        "source_metric_id": "github_contribution_calendar_total_and_days",
                        "status": "ok",
                        "complete": True,
                        "population_id": "github-contribution-calendar-visible-to-provider",
                        "population_signature": None,
                        "window_start": "2025-08-26T00:00:00Z",
                        "window_end": "2026-08-25T09:30:00Z",
                        "observed_at": "2026-08-25T09:30:00Z",
                        "source_id": "github_graphql_contribution_calendar",
                        "source_mode": "live",
                        "completion_reason": "all_components_observed",
                    }
                }
            },
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            snapshot_path = tmp_root / "site/data/profile_snapshot.json"
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            snapshot_path.write_text(json.dumps(previous_payload), encoding="utf-8")
            original_cwd = Path.cwd()
            os.chdir(tmp_root)
            try:
                with patch(
                    "scripts.pipeline.collect_data.subprocess.run",
                    side_effect=FileNotFoundError("git snapshot unavailable"),
                ):
                    restored = _read_previous_snapshot()
            finally:
                os.chdir(original_cwd)

        self.assertEqual("2026-08-25T09:30:00Z", restored.get("generated_at"))
        self.assertEqual(777, restored.get("snapshot", {}).get("last_year_contributions"))
        provenance = (
            restored.get("data_quality", {})
            .get("metric_provenance", {})
            .get("last_year_contributions", {})
        )
        self.assertEqual("2026-08-25T09:30:00Z", provenance.get("observed_at"))
        self.assertEqual(
            "github_contribution_calendar_total_and_days",
            provenance.get("source_metric_id"),
        )

    def test_noncurrent_contributions_use_one_decision_before_canonical_writes(self):
        from dataclasses import replace

        from scripts.pipeline import profile_pipeline
        from tests.pipeline.test_compute_metrics_accuracy import AccuracyTests

        collected = replace(
            AccuracyTests()._collected(),
            calendar=None,
            total_contributions=777,
        )
        object.__setattr__(
            collected,
            "metric_observations",
            {
                "last_year_contributions": {
                    "schema": "profile-provider-observation/v1",
                    "metric_id": "last_year_contributions",
                    "source_metric_id": "previous_profile_snapshot_contributions",
                    "value": 777,
                    "status": "fallback",
                    "complete": True,
                    "population_id": "github-contribution-calendar-visible-to-provider",
                    "population_signature": None,
                    "window_start": None,
                    "window_end": None,
                    "observed_at": "2026-08-25T09:30:00Z",
                    "source_id": "previous_profile_snapshot",
                    "source_mode": "previous_snapshot",
                    "completion_reason": "previous_snapshot",
                }
            },
        )
        held = _PublicationDecisionValue(
            "HOLD_NONCURRENT_CONTRIBUTIONS",
            allows_effects=False,
        )

        with patch.object(profile_pipeline, "ensure_output_dirs"), patch.object(
            profile_pipeline, "evaluate_profile_publication", return_value=held, create=True
        ) as evaluator, patch.object(
            profile_pipeline, "generate_assets"
        ) as generate_assets, patch.object(
            profile_pipeline, "write_dashboard_json"
        ) as write_dashboard_json, patch.object(
            profile_pipeline, "render_readme"
        ) as render_readme:
            result = profile_pipeline.run_profile_pipeline_with_collected(
                collected,
                logger=lambda *_args, **_kwargs: None,
                allow_network_calls=False,
                source_kind="fixture",
            )

        with self.subTest(assertion="one shared decision"):
            self.assertEqual(1, evaluator.call_count)
            call_text = repr(evaluator.call_args)
            self.assertIn("NONCURRENT_CONTRIBUTIONS", call_text)
        with self.subTest(assertion="all local canonical writers held"):
            self.assertEqual(
                {"assets": 0, "dashboard": 0, "readme": 0},
                {
                    "assets": generate_assets.call_count,
                    "dashboard": write_dashboard_json.call_count,
                    "readme": render_readme.call_count,
                },
            )
        with self.subTest(assertion="decision returned to caller"):
            returned = result.get("publication_decision") or result.get("decision")
            self.assertEqual(held, returned)

    def test_current_contributions_keep_each_local_writer_enabled(self):
        from scripts.pipeline import profile_pipeline
        from tests.pipeline.test_compute_metrics_accuracy import AccuracyTests

        current = AccuracyTests()._collected()
        ready = _PublicationDecisionValue("READY", allows_effects=True)
        with patch.object(profile_pipeline, "ensure_output_dirs"), patch.object(
            profile_pipeline, "evaluate_profile_publication", return_value=ready, create=True
        ), patch.object(
            profile_pipeline, "generate_assets"
        ) as generate_assets, patch.object(
            profile_pipeline, "write_dashboard_json"
        ) as write_dashboard_json, patch.object(
            profile_pipeline, "render_readme"
        ) as render_readme:
            profile_pipeline.run_profile_pipeline_with_collected(
                current,
                logger=lambda *_args, **_kwargs: None,
                allow_network_calls=False,
                source_kind="fixture",
            )

        generate_assets.assert_called_once()
        write_dashboard_json.assert_called_once()
        render_readme.assert_called_once()

    def _model_with_old_public_and_private_repositories(self):
        from copy import deepcopy
        from dataclasses import replace
        from datetime import datetime, timedelta, timezone

        from scripts.pipeline.compute_metrics import compute_profile_model
        from tests.pipeline.test_compute_metrics_accuracy import AccuracyTests

        collected = AccuracyTests()._collected()
        pushed_at = (
            datetime.now(timezone.utc) - timedelta(days=45)
        ).isoformat().replace("+00:00", "Z")
        public_repository = deepcopy(collected.repos[1])
        public_repository.update(
            {
                "name": "public-archive-tools",
                "html_url": "https://github.com/jguida941/public-archive-tools",
                "pushed_at": pushed_at,
                "latest_commit_message": "Document the public release summary",
                "private": False,
                "visibility": "public",
            }
        )
        private_repository = deepcopy(collected.private_repos[0])
        private_repository.update(
            {
                "name": "private-archive-tools",
                "html_url": "https://github.com/jguida941/private-archive-tools",
                "pushed_at": pushed_at,
                "latest_commit_message": "Document the private release summary",
                "private": True,
                "visibility": "private",
            }
        )
        collected = replace(
            collected,
            repo_counts={
                "public_owned_total": 1,
                "public_owned_forks": 0,
                "public_owned_nonfork": 1,
                "private_owned": 1,
                "private_owned_nonfork": 1,
            },
            repos=[public_repository],
            all_repos=[public_repository],
            events=[],
            latest_push_message_by_repo={},
            private_repos=[private_repository],
        )
        model = compute_profile_model(
            collected,
            logger=lambda *_args, **_kwargs: None,
            allow_network_calls=False,
        )
        return model, public_repository, private_repository

    def _assert_repository_metadata(self, observed, expected, *, private):
        self.assertEqual(expected["name"], observed.get("name"))
        self.assertEqual(expected["html_url"], observed.get("url"))
        self.assertEqual(expected["language"], observed.get("language"))
        self.assertEqual(expected["pushed_at"], observed.get("pushed_at_raw"))
        self.assertEqual(
            expected["latest_commit_message"],
            observed.get("last_commit_msg"),
        )
        if private:
            self.assertIs(
                True,
                observed.get("is_private"),
                "the row must retain its private visibility marker",
            )

    def test_repository_overview_keeps_old_public_and_private_metadata(self):
        model, public_repository, private_repository = (
            self._model_with_old_public_and_private_repositories()
        )
        rows = {
            row.get("name"): row
            for row in model["repo_overview_rows"]
            if isinstance(row, dict)
        }

        self.assertIn(
            public_repository["name"],
            rows,
            "the old public repository is the overview control",
        )
        self._assert_repository_metadata(
            rows[public_repository["name"]],
            public_repository,
            private=False,
        )
        self.assertIn(
            private_repository["name"],
            rows,
            "an overview is not a recent-only surface and must keep private metadata",
        )
        self._assert_repository_metadata(
            rows[private_repository["name"]],
            private_repository,
            private=True,
        )

    def test_dashboard_repository_matrix_keeps_old_public_and_private_metadata(self):
        from scripts.pipeline.render_outputs import _public_dashboard_data

        model, public_repository, private_repository = (
            self._model_with_old_public_and_private_repositories()
        )
        published = _public_dashboard_data(model["dashboard_data"])
        rows = {
            row.get("name"): row
            for row in published["repo_language_matrix"]
            if isinstance(row, dict)
        }

        self.assertIn(
            public_repository["name"],
            rows,
            "the old public repository is the dashboard control",
        )
        self._assert_repository_metadata(
            rows[public_repository["name"]],
            public_repository,
            private=False,
        )
        self.assertIn(
            private_repository["name"],
            rows,
            "published dashboard metadata must retain the private overview row",
        )
        self._assert_repository_metadata(
            rows[private_repository["name"]],
            private_repository,
            private=True,
        )

    def test_recent_repository_surface_keeps_its_time_window(self):
        model, public_repository, private_repository = (
            self._model_with_old_public_and_private_repositories()
        )
        recent_names = {
            row.get("name")
            for row in model["recent_repos"]
            if isinstance(row, dict)
        }
        self.assertNotIn(public_repository["name"], recent_names)
        self.assertNotIn(private_repository["name"], recent_names)

    def _dependency_authorities(self):
        requirements = _requirement_map(
            (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        )
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        project_dependencies = _requirement_map(project["project"]["dependencies"])
        return requirements, project_dependencies

    def test_core_dependencies_are_declared_consistently(self):
        requirements, project_dependencies = self._dependency_authorities()
        for existing_dependency in ("requests", "jinja2"):
            self.assertIn(existing_dependency, requirements)
            self.assertEqual(
                requirements[existing_dependency],
                project_dependencies.get(existing_dependency),
            )

    def test_image_dependency_is_declared_consistently(self):
        requirements, project_dependencies = self._dependency_authorities()
        self.assertIn("pillow", requirements)
        self.assertEqual(requirements["pillow"], project_dependencies.get("pillow"))
        required = "Pillow>=10.0"
        requirement_entries = [
            line.split("#", 1)[0].strip()
            for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
            if line.split("#", 1)[0].strip()
        ]
        project_entries = tomllib.loads(
            (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )["project"]["dependencies"]
        self.assertEqual(
            [required],
            [entry for entry in requirement_entries if entry.lower().startswith("pillow")],
        )
        self.assertEqual(
            [required],
            [entry for entry in project_entries if entry.lower().startswith("pillow")],
        )

    def _generation_workflows(self):
        return (
            ROOT / ".github/workflows/metrics.yml",
            ROOT / ".github/workflows/analytics.yml",
        )

    def _assert_bounded_product_test_step(self, step):
        self.assertIsNone(
            _step_field(step, "if"),
            "the product test step must run unconditionally",
        )
        self.assertIsNone(
            _step_field(step, "continue-on-error"),
            "the product test step must not be allowed to fail",
        )
        self.assertIsNone(
            _step_field(step, "shell"),
            "the product test step must use the runner's default shell",
        )
        command = " ".join(
            line.rstrip("\\").strip() for line in _step_run_lines(step)
        ).split()
        self.assertEqual(
            ["python", "-m", "unittest", *PROFILE_PRODUCT_TEST_MODULES],
            command,
            "the product test step must run exactly the approved product modules",
        )

    def _assert_hermetic_product_test_env(self, step):
        step_text = "\n".join(step)
        declared = {}
        for key, raw in _step_env_entries(step):
            declared.setdefault(key, []).append(raw)
        expected = dict(PROFILE_PRODUCT_TEST_ENV)
        extra_keys = [key for key in declared if key not in expected]
        observed = {}
        for key in list(expected) + extra_keys:
            declarations = _mapping_key_occurrences(step_text, key)
            values = declared.get(key, [])
            if len(declarations) == 1 and len(values) == 1 and values[0]:
                observed[key] = _env_scalar(values[0])
            else:
                observed[key] = {
                    "declarations": len(declarations),
                    "env_values": values,
                }
        self.assertEqual(
            expected,
            observed,
            "the product test step's env block must declare exactly the hermetic"
            " keys, each once with its exact value, so ordinary product tests can"
            " neither inherit nor restore the live generator credentials or cache",
        )

    def test_generation_workflows_generate_before_tests_that_gate_publication(self):
        for workflow in self._generation_workflows():
            with self.subTest(workflow=workflow.name):
                text = workflow.read_text(encoding="utf-8")
                self.assertIn("  workflow_dispatch:", text)
                if workflow.name == "metrics.yml":
                    self.assertIn("  schedule:", text)
                self.assertEqual(
                    [],
                    _mapping_key_occurrences(text, "shell"),
                    "generation workflows must not configure a custom shell in any"
                    " block or flow mapping, including workflow or job defaults",
                )
                self.assertEqual(
                    [],
                    [line for line in text.splitlines() if "BASH_ENV" in line],
                    "generation workflows must not name BASH_ENV anywhere, so no"
                    " bash startup file can restore live credentials or cache",
                )

                steps = _workflow_steps(workflow)
                test_index = _step_index(
                    steps,
                    lambda step: _step_runs(step, "python -m unittest"),
                )
                generation_occurrences = [
                    (index, line)
                    for index, step in enumerate(steps)
                    for line in _step_run_lines(step)
                    if "python scripts/profile_cli.py generate-profile" in line
                ]
                generation_invocations = sum(
                    line.count("python scripts/profile_cli.py generate-profile")
                    for _index, line in generation_occurrences
                )
                decision_index = _step_index(
                    steps,
                    lambda step: any(
                        "python scripts/profile_cli.py" in line
                        and "publication" in line
                        and "status" in line
                        for line in _step_run_lines(step)
                    ),
                )
                upload_index = _step_index(
                    steps,
                    lambda step: _step_field(step, "uses") == "actions/upload-artifact@v4"
                    and "README.md" in "\n".join(step),
                )
                commit_index = _step_index(
                    steps,
                    lambda step: _step_field(step, "uses")
                    == "stefanzweifel/git-auto-commit-action@v5",
                )
                self.assertIsNotNone(test_index, "ordinary product tests must run")
                self.assertEqual(
                    1,
                    generation_invocations,
                    "the workflow must invoke candidate generation exactly once",
                )
                generate_index, generation_command = generation_occurrences[0]
                self.assertEqual(
                    "python scripts/profile_cli.py generate-profile",
                    generation_command,
                    "the sole generation invocation must be the exact canonical command",
                )
                self.assertIsNotNone(decision_index, "the publication decision must run")
                self.assertIsNotNone(upload_index, "the canonical artifact upload must run")
                self.assertIsNotNone(commit_index, "verified outputs must be published")
                self.assertLess(
                    generate_index,
                    test_index,
                    "candidate generation must run before the fatal product tests so a"
                    " stale committed artifact is regenerated instead of failing every"
                    " scheduled run",
                )
                for boundary_name, boundary_index in (
                    ("publication decision", decision_index),
                    ("canonical artifact upload", upload_index),
                    ("auto-commit", commit_index),
                ):
                    self.assertLess(
                        test_index,
                        boundary_index,
                        f"the fatal product tests must complete before the {boundary_name}",
                    )
                test_step = steps[test_index]
                self._assert_bounded_product_test_step(test_step)
                self._assert_hermetic_product_test_env(test_step)
                self.assertNotIn("|| true", "\n".join(_step_run_lines(test_step)))

    def test_generation_workflows_keep_generation_and_publish_steps(self):
        for workflow in self._generation_workflows():
            with self.subTest(workflow=workflow.name):
                steps = _workflow_steps(workflow)
                generate_index = _step_index(
                    steps,
                    lambda step: _step_runs(
                        step, "python scripts/profile_cli.py generate-profile"
                    ),
                )
                commit_index = _step_index(
                    steps,
                    lambda step: _step_field(step, "uses")
                    == "stefanzweifel/git-auto-commit-action@v5",
                )
                self.assertIsNotNone(generate_index)
                self.assertIsNotNone(commit_index)
                self.assertLess(generate_index, commit_index)

    def test_generation_workflows_validate_before_auto_commit(self):
        for workflow in self._generation_workflows():
            with self.subTest(workflow=workflow.name):
                steps = _workflow_steps(workflow)
                generate_index = _step_index(
                    steps,
                    lambda step: _step_runs(
                        step, "python scripts/profile_cli.py generate-profile"
                    ),
                )
                validate_index = _step_index(
                    steps,
                    lambda step: _step_runs(step, "python scripts/profile_cli.py validate"),
                )
                commit_index = _step_index(
                    steps,
                    lambda step: _step_field(step, "uses")
                    == "stefanzweifel/git-auto-commit-action@v5",
                )

                self.assertIsNotNone(generate_index, "profile generation must run")
                self.assertIsNotNone(validate_index, "generated outputs must be validated")
                self.assertIsNotNone(commit_index, "verified outputs must be published")
                self.assertLess(generate_index, validate_index)
                self.assertLess(validate_index, commit_index)
                for index in (generate_index, validate_index):
                    step = steps[index]
                    self.assertNotEqual(_step_field(step, "continue-on-error"), "true")
                    self.assertNotIn("|| true", "\n".join(_step_run_lines(step)))

    def test_generation_auto_commit_requires_success(self):
        expected_conditions = {
            "metrics.yml": METRICS_COMMIT_CONDITION,
            "analytics.yml": ANALYTICS_COMMIT_CONDITION,
        }
        for workflow in self._generation_workflows():
            with self.subTest(workflow=workflow.name):
                steps = _workflow_steps(workflow)
                commit_index = _step_index(
                    steps,
                    lambda step: _step_field(step, "uses")
                    == "stefanzweifel/git-auto-commit-action@v5",
                )
                self.assertIsNotNone(commit_index, "verified outputs must be published")
                commit_condition = _step_field(steps[commit_index], "if") or ""
                self.assertTrue(
                    _condition_matches(commit_condition, expected_conditions[workflow.name]),
                    f"unexpected auto-commit condition in {workflow.name}: {commit_condition}",
                )

    def test_metrics_validation_gates_rendered_artifact_upload_and_commit(self):
        workflow = ROOT / ".github/workflows/metrics.yml"
        steps = _workflow_steps(workflow)
        validate_index = _step_index(
            steps,
            lambda step: _step_runs(step, "python scripts/profile_cli.py validate"),
        )
        upload_index = _step_index(
            steps,
            lambda step: _step_field(step, "uses") == "actions/upload-artifact@v4",
        )
        commit_index = _step_index(
            steps,
            lambda step: _step_field(step, "uses")
            == "stefanzweifel/git-auto-commit-action@v5",
        )

        self.assertIsNotNone(validate_index, "generated outputs must be validated")
        self.assertIsNotNone(upload_index, "validated outputs should remain downloadable")
        self.assertIsNotNone(commit_index, "validated outputs should still reach auto-commit")
        self.assertLess(validate_index, upload_index)
        self.assertLess(upload_index, commit_index)

        upload_step = steps[upload_index]
        upload_condition = _step_field(upload_step, "if") or ""
        self.assertTrue(
            _condition_matches(upload_condition, METRICS_COMMIT_CONDITION),
            "a failed validation must not upload rejected README/SVG/JSON artifacts",
        )
        upload_text = "\n".join(upload_step)
        for rendered_path in PROFILE_ARTIFACT_PATHS:
            with self.subTest(rendered_path=rendered_path):
                self.assertIn(rendered_path, upload_text)

        commit_condition = _step_field(steps[commit_index], "if") or ""
        self.assertTrue(
            _condition_matches(commit_condition, METRICS_COMMIT_CONDITION),
            "successful validation and the publish gate must still reach auto-commit",
        )

    def test_pages_deploy_accepts_only_successful_main_workflow_runs(self):
        workflow = ROOT / ".github/workflows/deploy-site.yml"
        condition = _job_condition(workflow, "deploy") or ""
        self.assertTrue(
            _condition_matches(condition, DEPLOY_JOB_CONDITION),
            f"unexpected deploy condition: {condition}",
        )

    def test_pages_deploy_verifies_before_upload(self):
        workflow = ROOT / ".github/workflows/deploy-site.yml"
        self.assertIn("  workflow_dispatch:", workflow.read_text(encoding="utf-8"))
        steps = _workflow_steps(workflow)
        validate_index = _step_index(
            steps,
            lambda step: _step_runs(step, "python scripts/profile_cli.py validate"),
        )
        test_index = _step_index(
            steps,
            lambda step: _step_runs(step, "python -m unittest"),
        )
        upload_index = _step_index(
            steps,
            lambda step: _step_field(step, "uses") == "actions/upload-pages-artifact@v3",
        )
        deploy_index = _step_index(
            steps,
            lambda step: _step_field(step, "uses") == "actions/deploy-pages@v4",
        )

        if test_index is None:
            self.fail("the bounded profile product tests must run before site upload")
        self._assert_bounded_product_test_step(steps[test_index])
        self.assertIsNotNone(validate_index, "site outputs must be verified before upload")
        self.assertIsNotNone(upload_index)
        self.assertIsNotNone(deploy_index)
        self.assertLess(test_index, validate_index)
        self.assertLess(validate_index, upload_index)
        self.assertLess(upload_index, deploy_index)
        validation_step = steps[validate_index]
        self.assertNotEqual(_step_field(validation_step, "continue-on-error"), "true")
        self.assertNotIn("|| true", "\n".join(_step_run_lines(validation_step)))
        validation_condition = _step_field(validation_step, "if") or ""
        self.assertTrue(
            not validation_condition
            or _condition_matches(validation_condition, MANUAL_VALIDATION_CONDITION),
            f"unexpected validation condition: {validation_condition}",
        )

    def test_workflow_conditions_reject_broadened_expressions(self):
        self.assertTrue(
            _condition_matches(
                '${{ success() && steps.gate.outputs.publish == "true" }}',
                METRICS_COMMIT_CONDITION,
            )
        )
        self.assertFalse(
            _condition_matches(
                "success() || steps.gate.outputs.publish == 'true'",
                METRICS_COMMIT_CONDITION,
            )
        )
        self.assertFalse(
            _condition_matches("success() && true", ANALYTICS_COMMIT_CONDITION)
        )
        self.assertFalse(
            _condition_matches(
                "github.event_name != 'workflow_run' || "
                "github.event.workflow_run.conclusion == 'success' || "
                "github.event.workflow_run.head_branch == 'main'",
                DEPLOY_JOB_CONDITION,
            )
        )
        self.assertFalse(
            _condition_matches(
                "github.event_name == 'workflow_dispatch' && false",
                MANUAL_VALIDATION_CONDITION,
            )
        )

    def test_pages_workflow_keeps_upload_then_deploy(self):
        workflow = ROOT / ".github/workflows/deploy-site.yml"
        self.assertIn("  workflow_dispatch:", workflow.read_text(encoding="utf-8"))
        steps = _workflow_steps(workflow)
        checkout_index = _step_index(
            steps,
            lambda step: _step_field(step, "uses") == "actions/checkout@v4",
        )
        upload_index = _step_index(
            steps,
            lambda step: _step_field(step, "uses") == "actions/upload-pages-artifact@v3",
        )
        deploy_index = _step_index(
            steps,
            lambda step: _step_field(step, "uses") == "actions/deploy-pages@v4",
        )
        self.assertIsNotNone(checkout_index)
        self.assertIsNotNone(upload_index)
        self.assertIsNotNone(deploy_index)
        self.assertLess(checkout_index, upload_index)
        self.assertLess(upload_index, deploy_index)


class ProfilePublicationAcceptanceTests(unittest.TestCase):
    def _generate_fixture(self, output_root):
        fixture_path = ROOT / "tests/fixtures/sample_collected_data.json"
        template_path = ROOT / "templates/README.md.tpl"
        (output_root / "templates").mkdir(parents=True, exist_ok=True)
        shutil.copy2(template_path, output_root / "templates/README.md.tpl")

        original_cwd = Path.cwd()
        os.chdir(output_root)
        try:
            return run_profile_pipeline_from_fixture(
                str(fixture_path),
                logger=lambda *_args, **_kwargs: None,
            )
        finally:
            os.chdir(original_cwd)

    def _validate_output(self, output_root):
        from scripts.quality.validate_generated_profile import validate_profile

        original_cwd = Path.cwd()
        os.chdir(output_root)
        try:
            return validate_profile()
        finally:
            os.chdir(original_cwd)

    @staticmethod
    def _write_json(path, payload):
        path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    @staticmethod
    def _active_repo_partial_disclosure(svg):
        visible_text = " ".join(re.sub(r"<[^>]+>", " ", svg).split())
        field_specific = bool(
            re.search(
                r"(?:active repos(?:itories)?|repository activity)"
                r".{0,80}\bpartial\b"
                r".{0,80}\b(?:known minimum|minimum known)\b"
                r".{0,80}\b(?:unknown|unobserved|missing)\s+push(?:es)?\b",
                visible_text,
                re.IGNORECASE,
            )
        )
        return visible_text, field_specific

    def _generate_collected(self, output_root, collected, *, source_kind):
        from scripts.pipeline import profile_pipeline

        template_path = ROOT / "templates/README.md.tpl"
        (output_root / "templates").mkdir(parents=True, exist_ok=True)
        shutil.copy2(template_path, output_root / "templates/README.md.tpl")

        original_cwd = Path.cwd()
        os.chdir(output_root)
        try:
            with patch.object(
                profile_pipeline,
                "refuse_dirty_generator_source",
                return_value=None,
            ), patch.object(
                profile_pipeline,
                "dirty_generator_source_paths",
                return_value=(),
            ):
                result = profile_pipeline.run_profile_pipeline_with_collected(
                    collected,
                    logger=lambda *_args, **_kwargs: None,
                    allow_network_calls=False,
                    source_kind=source_kind,
                )
                profile_pipeline._seal_artifact_set(
                    result,
                    logger=lambda *_args, **_kwargs: None,
                )
                return result
        finally:
            os.chdir(original_cwd)

    def test_direct_live_generation_refuses_dirty_source_before_model_or_writes(self):
        from scripts.pipeline import profile_pipeline
        from tests.pipeline.test_compute_metrics_accuracy import AccuracyTests

        ready_model = {
            "dashboard_data": {"generated_at": "2026-08-27T00:00:00Z"},
            "data_quality": {
                "private_aggregate_status": "exact",
                "metric_statuses": {},
            },
            "data_scope": {"metric_scopes": {}},
            "publication_hold_reasons": (),
        }
        collected = AccuracyTests()._collected()
        with patch.object(
            profile_pipeline,
            "dirty_generator_source_paths",
            return_value=("scripts/pipeline/profile_pipeline.py",),
        ) as dirty_census, patch.object(
            profile_pipeline,
            "admit_repository_population",
        ), patch.object(
            profile_pipeline,
            "compute_profile_model",
            return_value=ready_model,
        ) as compute_model, patch.object(
            profile_pipeline,
            "build_generation_identity",
            return_value={"source_kind": "github-api", "render_key": "a" * 64},
        ) as build_identity, patch.object(
            profile_pipeline,
            "ensure_output_dirs",
        ) as ensure_dirs, patch.object(
            profile_pipeline,
            "generate_assets",
        ) as generate_assets, patch.object(
            profile_pipeline,
            "write_dashboard_json",
        ) as write_dashboard_json, patch.object(
            profile_pipeline,
            "render_readme",
        ) as render_readme:
            error = None
            try:
                profile_pipeline.run_profile_pipeline_with_collected(
                    collected,
                    logger=lambda *_args, **_kwargs: None,
                    allow_network_calls=False,
                    source_kind="github-api",
                )
            except Exception as exc:  # the assertion below verifies the exact product error
                error = exc

        self.assertEqual(
            {
                "error_type": "ProfileGenerationIdentityError",
                "dirty_source_named": True,
                "dirty_census_calls": 1,
                "model_calls": 0,
                "identity_calls": 0,
                "writer_calls": (0, 0, 0, 0),
            },
            {
                "error_type": type(error).__name__ if error is not None else None,
                "dirty_source_named": bool(
                    error
                    and "clean generator inputs" in str(error)
                    and "scripts/pipeline/profile_pipeline.py" in str(error)
                ),
                "dirty_census_calls": dirty_census.call_count,
                "model_calls": compute_model.call_count,
                "identity_calls": build_identity.call_count,
                "writer_calls": (
                    ensure_dirs.call_count,
                    generate_assets.call_count,
                    write_dashboard_json.call_count,
                    render_readme.call_count,
                ),
            },
        )

    def test_undeclared_generation_origin_refuses_before_admission_or_writes(self):
        from scripts.pipeline import profile_pipeline
        from tests.pipeline.test_compute_metrics_accuracy import AccuracyTests

        ready_model = {
            "dashboard_data": {"generated_at": "2026-08-27T00:00:00Z"},
            "data_quality": {
                "private_aggregate_status": "exact",
                "metric_statuses": {},
            },
            "data_scope": {"metric_scopes": {}},
            "publication_hold_reasons": (),
        }
        collected = AccuracyTests()._collected()
        observed = {}
        for label, origin_kwargs in (
            ("omitted", {}),
            ("explicit_none", {"source_kind": None}),
        ):
            with patch.object(
                profile_pipeline,
                "dirty_generator_source_paths",
                return_value=("scripts/pipeline/profile_pipeline.py",),
            ) as dirty_census, patch.object(
                profile_pipeline,
                "admit_repository_population",
            ) as admit_population, patch.object(
                profile_pipeline,
                "compute_profile_model",
                return_value=ready_model,
            ) as compute_model, patch.object(
                profile_pipeline,
                "build_generation_identity",
                return_value={"source_kind": "github-api", "render_key": "a" * 64},
            ) as build_identity, patch.object(
                profile_pipeline,
                "ensure_output_dirs",
            ) as ensure_dirs, patch.object(
                profile_pipeline,
                "generate_assets",
            ) as generate_assets, patch.object(
                profile_pipeline,
                "write_dashboard_json",
            ) as write_dashboard_json, patch.object(
                profile_pipeline,
                "render_readme",
            ) as render_readme:
                error = None
                result = None
                try:
                    result = profile_pipeline.run_profile_pipeline_with_collected(
                        collected,
                        logger=lambda *_args, **_kwargs: None,
                        allow_network_calls=False,
                        **origin_kwargs,
                    )
                except Exception as exc:  # the assertion below verifies the exact product error
                    error = exc

            observed[label] = {
                "error_type": type(error).__name__ if error is not None else None,
                "dirty_source_named": bool(
                    error
                    and "clean generator inputs" in str(error)
                    and "scripts/pipeline/profile_pipeline.py" in str(error)
                ),
                "decision": (
                    _decision_state(result["publication_decision"])
                    if result is not None
                    else None
                ),
                "dirty_census_calls": dirty_census.call_count,
                "admission_calls": admit_population.call_count,
                "model_calls": compute_model.call_count,
                "identity_calls": build_identity.call_count,
                "writer_calls": (
                    ensure_dirs.call_count,
                    generate_assets.call_count,
                    write_dashboard_json.call_count,
                    render_readme.call_count,
                ),
            }

        expected = {
            "error_type": "ProfileGenerationIdentityError",
            "dirty_source_named": True,
            "decision": None,
            "dirty_census_calls": 1,
            "admission_calls": 0,
            "model_calls": 0,
            "identity_calls": 0,
            "writer_calls": (0, 0, 0, 0),
        }
        self.assertEqual(
            {"omitted": expected, "explicit_none": expected},
            observed,
        )

    def test_fixture_generation_and_generated_output_changes_remain_allowed(self):
        from scripts import contracts
        from scripts.pipeline import profile_pipeline
        from tests.pipeline.test_compute_metrics_accuracy import AccuracyTests

        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            source = repo / "scripts/pipeline/generator.py"
            template = repo / "templates/README.md.tpl"
            source.parent.mkdir(parents=True)
            template.parent.mkdir(parents=True)
            source.write_text("VALUE = 1\n", encoding="utf-8")
            template.write_text("template\n", encoding="utf-8")
            for command in (
                ("git", "init", "-q"),
                ("git", "config", "user.email", "profile-tests@example.invalid"),
                ("git", "config", "user.name", "Profile Tests"),
                ("git", "add", "scripts/pipeline/generator.py", "templates/README.md.tpl"),
                ("git", "commit", "-qm", "baseline"),
            ):
                subprocess.run(command, cwd=repo, check=True, capture_output=True, text=True)
            generated_output = repo / "assets/generated.svg"
            generated_output.parent.mkdir()
            generated_output.write_text("<svg/>\n", encoding="utf-8")
            with patch.object(contracts, "SOURCE_ROOT", repo), patch.object(
                contracts,
                "GENERATOR_SOURCE_ROOTS",
                ("scripts/pipeline",),
            ), patch.object(
                contracts,
                "GENERATOR_SOURCE_FILES",
                (),
            ), patch.object(
                contracts,
                "GENERATOR_TEMPLATE_PATH",
                "templates/README.md.tpl",
            ):
                output_only_dirty_paths = contracts.dirty_generator_source_paths()

        ready_model = {
            "dashboard_data": {"generated_at": "2026-08-27T00:00:00Z"},
            "data_quality": {
                "private_aggregate_status": "exact",
                "metric_statuses": {},
            },
            "data_scope": {"metric_scopes": {}},
            "publication_hold_reasons": (),
        }
        collected = AccuracyTests()._collected()
        with patch.object(
            profile_pipeline,
            "dirty_generator_source_paths",
            return_value=("scripts/pipeline/profile_pipeline.py",),
        ), patch.object(
            profile_pipeline,
            "admit_repository_population",
        ), patch.object(
            profile_pipeline,
            "compute_profile_model",
            return_value=ready_model,
        ), patch.object(
            profile_pipeline,
            "build_generation_identity",
            return_value={"source_kind": "fixture", "render_key": "a" * 64},
        ), patch.object(
            profile_pipeline,
            "ensure_output_dirs",
        ) as ensure_dirs, patch.object(
            profile_pipeline,
            "generate_assets",
        ) as generate_assets, patch.object(
            profile_pipeline,
            "write_dashboard_json",
        ) as write_dashboard_json, patch.object(
            profile_pipeline,
            "render_readme",
        ) as render_readme:
            fixture_result = profile_pipeline.run_profile_pipeline_with_collected(
                collected,
                logger=lambda *_args, **_kwargs: None,
                allow_network_calls=False,
                source_kind="fixture",
            )

        self.assertEqual((), output_only_dirty_paths)
        self.assertEqual(
            {
                "decision": "HOLD_NONLIVE_SOURCE",
                "writer_calls": (1, 1, 1, 1),
            },
            {
                "decision": _decision_state(fixture_result["publication_decision"]),
                "writer_calls": (
                    ensure_dirs.call_count,
                    generate_assets.call_count,
                    write_dashboard_json.call_count,
                    render_readme.call_count,
                ),
            },
        )

    def test_partial_push_value_is_qualified_before_ready_publication(self):
        from dataclasses import replace

        from scripts.pipeline import profile_pipeline
        from tests.pipeline.test_compute_metrics_accuracy import AccuracyTests

        collected = AccuracyTests()._collected()
        public_repositories = copy.deepcopy(collected.repos)
        next(
            repository
            for repository in public_repositories
            if repository.get("name") == "pub1"
        )["pushed_at"] = ""
        partial_push = replace(
            collected,
            repos=public_repositories,
            all_repos=copy.deepcopy(public_repositories),
        )

        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            result = self._generate_collected(
                output_root,
                partial_push,
                source_kind="github-api",
            )
            model = result["model"]
            decision = _decision_state(result["publication_decision"])
            value = model["scorecard"]["active_repos_7d"]
            status = model["data_quality"]["metric_statuses"]["active_repos_7d"]
            scope = model["data_scope"]["metric_scopes"]["active_repos_7d"]
            subject = profile_pipeline.candidate_publication_subject(
                model,
                source_kind="github-api",
            )
            validation = None
            visible_text = ""
            visibly_qualified = False
            if decision == "READY":
                validation = self._validate_output(output_root)
                builder = (output_root / "assets/builder_scorecard.svg").read_text(
                    encoding="utf-8"
                )
                visible_text, visibly_qualified = (
                    self._active_repo_partial_disclosure(builder)
                )

        self.assertEqual("exact", model["data_quality"]["private_aggregate_status"])
        self.assertEqual("partial", status)
        self.assertIn("partial", scope.casefold())
        self.assertIsNotNone(value)
        self.assertTrue(
            decision != "READY"
            or bool(validation and validation.ok and visibly_qualified),
            {
                "decision": decision,
                "validation_errors": list(validation.errors) if validation else None,
                "unqualified_consumers": list(subject.unqualified_partial_consumers),
                "active_repos_7d": value,
                "visible_text": visible_text,
            },
        )

    def test_generic_partial_line_cannot_qualify_active_repository_value(self):
        from dataclasses import replace

        from scripts.contracts import profile_contract
        from tests.pipeline.test_compute_metrics_accuracy import AccuracyTests

        collected = AccuracyTests()._collected()
        public_repositories = copy.deepcopy(collected.repos)
        next(
            repository
            for repository in public_repositories
            if repository.get("name") == "pub1"
        )["pushed_at"] = ""
        partial_push = replace(
            collected,
            repos=public_repositories,
            all_repos=copy.deepcopy(public_repositories),
        )

        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            with patch.dict(
                profile_contract.PARTIAL_QUALIFICATION_CONSUMERS[
                    "active_repos_7d"
                ],
                {"line": "Partial"},
            ):
                result = self._generate_collected(
                    output_root,
                    partial_push,
                    source_kind="github-api",
                )
                validation = self._validate_output(output_root)
                builder = (output_root / "assets/builder_scorecard.svg").read_text(
                    encoding="utf-8"
                )

        model = result["model"]
        visible_text, field_specific = self._active_repo_partial_disclosure(builder)
        rejected_for_field = any(
            "active_repos_7d" in error
            and "partial" in error.casefold()
            and ("activity" in error.casefold() or "push" in error.casefold())
            for error in validation.errors
        )
        self.assertEqual(
            {
                "status": "partial",
                "value_retained": True,
                "field_specific_or_rejected": True,
            },
            {
                "status": model["data_quality"]["metric_statuses"][
                    "active_repos_7d"
                ],
                "value_retained": model["scorecard"]["active_repos_7d"] is not None,
                "field_specific_or_rejected": field_specific or rejected_for_field,
            },
            {
                "validation_errors": list(validation.errors),
                "visible_text": visible_text,
            },
        )

    def test_complete_live_profile_remains_ready_valid_and_live_labeled(self):
        from tests.pipeline.test_compute_metrics_accuracy import AccuracyTests

        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            result = self._generate_collected(
                output_root,
                AccuracyTests()._collected(),
                source_kind="github-api",
            )
            validation = self._validate_output(output_root)
            builder = (output_root / "assets/builder_scorecard.svg").read_text(
                encoding="utf-8"
            )

        self.assertEqual("READY", _decision_state(result["publication_decision"]))
        self.assertEqual(
            "exact",
            result["model"]["data_quality"]["metric_statuses"]["active_repos_7d"],
        )
        self.assertTrue(validation.ok, validation.errors)
        self.assertIn("GitHub API", builder)

    def test_manifest_identity_inputs_match_render_key_and_snapshot(self):
        from scripts import contracts

        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            baseline = parent / "baseline"
            baseline.mkdir()
            result = self._generate_fixture(baseline)
            baseline_generation = copy.deepcopy(result["generation"])
            self.assertTrue(
                self._validate_output(baseline).ok,
                self._validate_output(baseline).errors,
            )

            alternatives = {
                "generated_at": "2000-01-01T00:00:00Z",
                "generator_revision": "0" * 40,
                "generator_source_digest": "0" * 64,
                "claim_input_digest": "0" * 64,
            }
            for field, replacement in alternatives.items():
                if baseline_generation.get(field) == replacement:
                    replacement = ("f" * 40) if field == "generator_revision" else (
                        "f" * 64 if field.endswith("digest") else "2001-01-01T00:00:00Z"
                    )
                case_root = parent / f"snapshot-{field}"
                shutil.copytree(baseline, case_root)
                snapshot_path = case_root / "site/data/profile_snapshot.json"
                snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
                snapshot["generation"][field] = replacement
                self._write_json(snapshot_path, snapshot)
                manifest = contracts.build_artifact_manifest(
                    baseline_generation,
                    root=case_root,
                )
                self._write_json(
                    case_root / contracts.PROFILE_ARTIFACT_MANIFEST_PATH,
                    manifest,
                )
                validation = self._validate_output(case_root)
                with self.subTest(snapshot_field=field):
                    self.assertFalse(validation.ok, validation.errors)
                    self.assertTrue(
                        any(
                            field in error or "generation identity" in error.casefold()
                            for error in validation.errors
                        ),
                        validation.errors,
                    )

            relation_root = parent / "render-key-relation"
            shutil.copytree(baseline, relation_root)
            changed_generation = copy.deepcopy(baseline_generation)
            changed_generation["claim_input_digest"] = (
                "f" * 64
                if changed_generation["claim_input_digest"] != "f" * 64
                else "e" * 64
            )
            snapshot_path = relation_root / "site/data/profile_snapshot.json"
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            snapshot["generation"] = contracts.public_generation_record(
                changed_generation
            )
            self._write_json(snapshot_path, snapshot)
            manifest = contracts.build_artifact_manifest(
                changed_generation,
                root=relation_root,
            )
            self._write_json(
                relation_root / contracts.PROFILE_ARTIFACT_MANIFEST_PATH,
                manifest,
            )
            validation = self._validate_output(relation_root)
            with self.subTest(identity_relation="claim_input_digest"):
                self.assertFalse(validation.ok, validation.errors)
                self.assertTrue(
                    any(
                        "render_key" in error or "identity" in error.casefold()
                        for error in validation.errors
                    ),
                    validation.errors,
                )

    def test_source_equivalent_absent_revision_remains_valid(self):
        from scripts import contracts

        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            result = self._generate_fixture(output_root)
            generation = copy.deepcopy(result["generation"])
            absent_revision = "0" * 40
            if generation["generator_revision"] == absent_revision:
                absent_revision = "f" * 40
            generation["generator_revision"] = absent_revision
            generation["render_key"] = contracts.canonical_digest(
                {
                    key: value
                    for key, value in generation.items()
                    if key != "render_key"
                }
            )
            snapshot_path = output_root / "site/data/profile_snapshot.json"
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            snapshot["generation"] = contracts.public_generation_record(generation)
            self._write_json(snapshot_path, snapshot)
            from scripts.rendering.generate_dashboard_summary import render_svg
            for mobile, name in ((False, "dashboard_summary.svg"), (True, "dashboard_summary_mobile.svg")):
                (output_root / "assets" / name).write_text(
                    render_svg(snapshot["dashboard_summary"], mobile=mobile, generation=generation), encoding="utf-8"
                )
            manifest = contracts.build_artifact_manifest(
                generation,
                root=output_root,
            )
            self._write_json(
                output_root / contracts.PROFILE_ARTIFACT_MANIFEST_PATH,
                manifest,
            )
            validation = self._validate_output(output_root)

        object_check = subprocess.run(
            ["git", "cat-file", "-e", absent_revision],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(0, object_check.returncode)
        self.assertEqual(
            contracts.generator_source_digest(),
            generation["generator_source_digest"],
        )
        self.assertTrue(validation.ok, validation.errors)

    def test_fixture_builder_does_not_claim_live_api_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            result = self._generate_fixture(output_root)
            validation = self._validate_output(output_root)
            builder = (output_root / "assets/builder_scorecard.svg").read_text(
                encoding="utf-8"
            )
            payloads_written = all(
                (output_root / relative_path).exists()
                for relative_path in PROFILE_ARTIFACT_PATHS
            )

        self.assertEqual("HOLD_NONLIVE_SOURCE", _decision_state(result["publication_decision"]))
        self.assertTrue(payloads_written)
        self.assertTrue(validation.ok, validation.errors)
        self.assertNotIn("GitHub API", builder)

    def test_untouched_fixture_output_remains_locally_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            self._generate_fixture(output_root)
            validation = self._validate_output(output_root)
            payloads = {
                relative_path: (output_root / relative_path).exists()
                for relative_path in PROFILE_PAYLOAD_PATHS
            }

        self.assertTrue(all(payloads.values()), payloads)
        self.assertTrue(validation.ok, validation.errors)

    def test_incomplete_private_population_holds_every_canonical_publish_effect(self):
        from dataclasses import replace

        from scripts.pipeline import profile_pipeline
        from tests.pipeline.test_compute_metrics_accuracy import AccuracyTests

        collected = AccuracyTests()._collected()
        counts = dict(collected.repo_counts)
        counts["private_owned"] = 2
        counts["private_owned_nonfork"] = 2
        partial = replace(collected, repo_counts=counts)

        with patch.object(
            profile_pipeline,
            "dirty_generator_source_paths",
            return_value=(),
        ), patch.object(profile_pipeline, "ensure_output_dirs") as ensure_dirs, patch.object(
            profile_pipeline, "generate_assets"
        ) as generate_assets, patch.object(
            profile_pipeline, "write_dashboard_json"
        ) as write_dashboard_json, patch.object(
            profile_pipeline, "render_readme"
        ) as render_readme:
            result = profile_pipeline.run_profile_pipeline_with_collected(
                partial,
                logger=lambda *_args, **_kwargs: None,
                allow_network_calls=False,
                source_kind="github-api",
            )

        model = result["model"]
        observed = {
            "private_inventory_status": model["data_quality"].get(
                "private_aggregate_status"
            ),
            "decision": _decision_state(result["publication_decision"]),
            "canonical_writer_calls": {
                "directories": ensure_dirs.call_count,
                "assets": generate_assets.call_count,
                "snapshot": write_dashboard_json.call_count,
                "readme": render_readme.call_count,
            },
            "observed_private_row_retained": any(
                row.get("name") == "secret-api"
                for row in model.get("repo_overview_rows", ())
                if isinstance(row, dict)
            ),
        }
        self.assertEqual(
            {
                "private_inventory_status": "partial",
                "decision": "HOLD_INCOMPLETE_PRIVATE_EVIDENCE",
                "canonical_writer_calls": {
                    "directories": 0,
                    "assets": 0,
                    "snapshot": 0,
                    "readme": 0,
                },
                "observed_private_row_retained": True,
            },
            observed,
        )

    def test_exact_empty_repository_population_remains_ready(self):
        from dataclasses import replace

        from scripts.pipeline import profile_pipeline
        from tests.pipeline.test_compute_metrics_accuracy import AccuracyTests

        collected = AccuracyTests()._collected()
        exact_empty = replace(
            collected,
            repo_counts={
                "public_owned_total": 0,
                "public_owned_forks": 0,
                "public_owned_nonfork": 0,
                "private_owned": 0,
                "private_owned_nonfork": 0,
            },
            repos=[],
            all_repos=[],
            private_repos=[],
            language_bytes={},
            events=[],
            latest_push_message_by_repo={},
        )

        with patch.object(
            profile_pipeline,
            "dirty_generator_source_paths",
            return_value=(),
        ), patch.object(profile_pipeline, "ensure_output_dirs") as ensure_dirs, patch.object(
            profile_pipeline, "generate_assets"
        ) as generate_assets, patch.object(
            profile_pipeline, "write_dashboard_json"
        ) as write_dashboard_json, patch.object(
            profile_pipeline, "render_readme"
        ) as render_readme:
            result = profile_pipeline.run_profile_pipeline_with_collected(
                exact_empty,
                logger=lambda *_args, **_kwargs: None,
                allow_network_calls=False,
                source_kind="github-api",
            )

        self.assertEqual("exact", result["model"]["data_quality"]["private_aggregate_status"])
        self.assertEqual("READY", _decision_state(result["publication_decision"]))
        self.assertEqual(
            (1, 1, 1, 1),
            (
                ensure_dirs.call_count,
                generate_assets.call_count,
                write_dashboard_json.call_count,
                render_readme.call_count,
            ),
        )

    def test_fixture_generation_is_identified_and_not_publishable(self):
        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            result = self._generate_fixture(output_root)
            snapshot = json.loads(
                (output_root / "site/data/profile_snapshot.json").read_text(
                    encoding="utf-8"
                )
            )
            readme = (output_root / "README.md").read_text(encoding="utf-8")
            payloads_written = all(
                (output_root / relative_path).exists()
                for relative_path in PROFILE_PAYLOAD_PATHS
            )

        generation = snapshot.get("generation", {})
        observed = {
            "source_kind": generation.get("source_kind"),
            "decision": _decision_state(result["publication_decision"]),
            "fixture_provenance_visible": "fixture" in readme.casefold()
            or "local data" in readme.casefold(),
            "live_provenance_claim_absent": "from the GitHub API." not in readme,
            "payloads_written": payloads_written,
        }
        self.assertEqual(
            {
                "source_kind": "fixture",
                "decision": "HOLD_NONLIVE_SOURCE",
                "fixture_provenance_visible": True,
                "live_provenance_claim_absent": True,
                "payloads_written": True,
            },
            observed,
        )

    def test_profile_artifact_manifest_binds_exact_payload_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            self._generate_fixture(output_root)
            manifest_path = output_root / "site/data/profile_artifact_manifest.json"
            self.assertTrue(
                manifest_path.exists(),
                "profile generation must finish with an external artifact manifest",
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            records = manifest.get("files")
            self.assertIsInstance(records, list)
            self.assertEqual(
                sorted(PROFILE_PAYLOAD_PATHS),
                [record.get("path") for record in records],
            )

            expected_records = []
            for relative_path in sorted(PROFILE_PAYLOAD_PATHS):
                payload_bytes = (output_root / relative_path).read_bytes()
                expected_records.append(
                    {
                        "path": relative_path,
                        "byte_length": len(payload_bytes),
                        "sha256": hashlib.sha256(payload_bytes).hexdigest(),
                    }
                )
            self.assertEqual(expected_records, records)
            self.assertEqual(
                _canonical_json_digest(expected_records),
                manifest.get("artifact_set_digest"),
            )

            valid = self._validate_output(output_root)
            self.assertTrue(valid.ok, valid.errors)

            snapshot_path = output_root / "site/data/profile_snapshot.json"
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            snapshot_path.write_text(
                json.dumps(snapshot, ensure_ascii=True, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            altered = self._validate_output(output_root)
            self.assertTrue(
                not altered.ok
                and any(
                    "profile_snapshot.json" in error
                    and any(word in error.casefold() for word in ("byte", "digest", "hash"))
                    for error in altered.errors
                ),
                altered.errors,
            )

    def test_profile_artifact_manifest_records_generation_identity(self):
        from importlib import metadata

        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            self._generate_fixture(output_root)
            manifest_path = output_root / "site/data/profile_artifact_manifest.json"
            manifest = (
                json.loads(manifest_path.read_text(encoding="utf-8"))
                if manifest_path.exists()
                else {}
            )

        execution = manifest.get("execution_identity", {})
        render_config = manifest.get("render_config", {})
        expected_packages = {
            package: metadata.version(distribution)
            for package, distribution in (
                ("jinja2", "jinja2"),
                ("pillow", "Pillow"),
                ("requests", "requests"),
            )
        }
        if sys.version_info < (3, 11):
            expected_packages["tomli"] = metadata.version("tomli")
        self.assertEqual("profile-artifact-manifest/v1", manifest.get("schema"))
        for field in (
            "render_key",
            "generator_source_digest",
            "claim_input_digest",
            "artifact_set_digest",
        ):
            with self.subTest(field=field):
                self.assertRegex(str(manifest.get(field, "")), r"^[0-9a-f]{64}$")
        self.assertRegex(str(manifest.get("generator_revision", "")), r"^[0-9a-f]{40}$")
        self.assertEqual(sys.implementation.name, execution.get("python_implementation"))
        self.assertEqual(
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            execution.get("python_version"),
        )
        self.assertEqual(expected_packages, execution.get("packages"))
        self.assertEqual("fixture", manifest.get("source_kind"))
        self.assertEqual("fixture", render_config.get("source_kind"))
        self.assertEqual(
            {"username", "profile_timezone", "activity_timezone", "source_kind"},
            set(render_config),
        )

    def test_generation_workflows_use_one_decision_and_an_exact_artifact_roster(self):
        for workflow in (
            ROOT / ".github/workflows/metrics.yml",
            ROOT / ".github/workflows/analytics.yml",
        ):
            with self.subTest(workflow=workflow.name):
                steps = _workflow_steps(workflow)
                gate_index = _step_index(
                    steps,
                    lambda step: any(
                        "python scripts/profile_cli.py" in line
                        and "publication" in line
                        and "status" in line
                        for line in _step_run_lines(step)
                    ),
                )
                self.assertIsNotNone(
                    gate_index,
                    "generation must ask the product publication evaluator once",
                )
                gate_step = steps[gate_index]
                gate_id = _step_field(gate_step, "id")
                self.assertTrue(gate_id)

                upload_index = _step_index(
                    steps,
                    lambda step: _step_field(step, "uses") == "actions/upload-artifact@v4"
                    and "README.md" in "\n".join(step),
                )
                commit_index = _step_index(
                    steps,
                    lambda step: _step_field(step, "uses")
                    == "stefanzweifel/git-auto-commit-action@v5",
                )
                self.assertIsNotNone(upload_index)
                self.assertIsNotNone(commit_index)
                expected_condition = f"success() && steps.{gate_id}.outputs.publish == 'true'"
                for effect_index in (upload_index, commit_index):
                    condition = _step_field(steps[effect_index], "if") or ""
                    self.assertTrue(
                        _condition_matches(condition, expected_condition),
                        f"canonical effect is not guarded by {gate_id}: {condition}",
                    )
                    effect_text = "\n".join(steps[effect_index])
                    self.assertNotIn("*", effect_text)
                    for relative_path in PROFILE_ARTIFACT_PATHS:
                        self.assertIn(relative_path, effect_text)

    def test_pages_requires_stored_artifact_readiness_before_upload(self):
        workflow = ROOT / ".github/workflows/deploy-site.yml"
        steps = _workflow_steps(workflow)
        validate_index = _step_index(
            steps,
            lambda step: _step_runs(step, "python scripts/profile_cli.py validate"),
        )
        readiness_index = _step_index(
            steps,
            lambda step: any(
                "python scripts/profile_cli.py" in line
                and "publication" in line
                and "status" in line
                and "--require-ready" in line
                for line in _step_run_lines(step)
            ),
        )
        upload_index = _step_index(
            steps,
            lambda step: _step_field(step, "uses") == "actions/upload-pages-artifact@v3",
        )
        self.assertIsNotNone(validate_index)
        self.assertIsNotNone(
            readiness_index,
            "Pages must require readiness for the stored artifact set",
        )
        self.assertIsNotNone(upload_index)
        self.assertLess(validate_index, readiness_index)
        self.assertLess(readiness_index, upload_index)


if __name__ == "__main__":
    unittest.main()

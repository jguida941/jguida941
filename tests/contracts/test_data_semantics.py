"""Regression coverage for generated profile metric meaning and formatting.

A displayed value must preserve the meaning and availability of its source. In
particular, missing data must not be presented as a measured zero.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
import types
import unittest
import xml.etree.ElementTree as ET
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from scripts.pipeline.collect_data import CollectedProfileData
from scripts.pipeline.compute_metrics import compute_profile_model


class OptionalIntegerMetricTests(unittest.TestCase):
    def test_optional_integer_format_rejects_inexact_or_invalid_values(self):
        from scripts.contracts.profile_contract import format_metric_value

        definition = {"format": "int_or_na"}
        invalid_values = (None, True, False, "7", 7.0, -1, [], {})

        for value in invalid_values:
            with self.subTest(value=value):
                self.assertEqual("n/a", format_metric_value(value, definition))

    def test_optional_integer_format_preserves_zero_and_large_integers(self):
        from scripts.contracts.profile_contract import format_metric_value

        definition = {"format": "int_or_na"}
        large_value = 10**30 + 234_567_890

        self.assertEqual("0", format_metric_value(0, definition))
        self.assertEqual(f"{large_value:,}", format_metric_value(large_value, definition))


class GeneratedCardTruthTests(unittest.TestCase):
    @staticmethod
    def _card_model(*, ci_status="exact", language_status="exact"):
        ci_partial = ci_status == "partial"
        ci_unavailable = ci_status == "unavailable"
        language_partial = language_status == "partial"
        ci_repositories = None if ci_unavailable else 1
        ci_percentage = None if ci_unavailable else 100 / 3
        scope_suffix = {
            "exact": "exact",
            "partial": "partial-observation",
            "unavailable": "unavailable",
        }
        metric_statuses = {
            "active_repos_7d": "exact",
            "days_since_last_push": "exact",
            "automation_repos": ci_status,
            "automation_workflows": ci_status,
            "ci_coverage_pct": ci_status,
            "ci_repos": ci_status,
            "top_languages": language_status,
            "primary_lang_share_pct": language_status,
            "languages_over_5pct": language_status,
            "languages_count": language_status,
        }
        metric_scopes = {
            metric: (
                "owned-public-private-nonfork-profile-excluded-"
                f"{scope_suffix[status]}"
            )
            for metric, status in metric_statuses.items()
        }
        snapshot = {
            "last_year_contributions": 120,
            "public_scope_commits": 40,
            "total_repos": 3,
            "public_forks": 0,
            "private_owned_repos": 1,
            "total_stars": 7,
            "languages_count": 2,
            "prs_merged": 5,
            "releases": 2,
            "ci_repos": ci_repositories,
            "streak_days": 4,
        }
        snapshot_rows = [
            {
                "key": key,
                "label": key.replace("_", " ").title(),
                "dashboard_label": key.replace("_", " ").title(),
                "value": value,
                "display_value": "n/a" if value is None else str(value),
            }
            for key, value in snapshot.items()
        ]
        data_quality = {
            "ci_status": (
                "partial"
                if ci_partial
                else ("fallback" if ci_unavailable else "ok")
            ),
            "ci_note": (
                "CI observation is Partial: 1 known automated, "
                "1 known not automated, and 1 unknown repository."
                if ci_partial
                else (
                    "CI observation is unavailable."
                    if ci_unavailable
                    else "CI observation is complete for three repositories."
                )
            ),
            "commits_status": "ok",
            "releases_status": "ok",
            "events_status": "ok",
            "private_aggregate_status": "exact",
            "metric_statuses": metric_statuses,
            "language_note": (
                "Language evidence is Partial; values describe observed bytes."
                if language_partial
                else "Language evidence is exact."
            ),
        }
        scorecard = {
            "last_year_contributions": 120,
            "active_days_last_year": 80,
            "active_repos_7d": 3,
            "ci_coverage_pct": ci_percentage,
            "automation_workflows": ci_repositories,
            "releases_30d": 2,
            "primary_lang_share_pct": 60.0,
        }
        engineering = {
            "active_days_last_year": 80,
            "weekly_cadence": [3, 5, 8],
            "automation_workflows": ci_repositories,
            "automation_repos": ci_repositories,
            "automation_eligible_repos": 3,
            "primary_lang_share_pct": 60.0,
            "public_repos_total": 2,
            "public_nonfork_repos": 2,
            "private_repos_total": 1,
            "private_nonfork_repos": 1,
        }
        # Qualified standalone fixture: public two + private one, with a
        # single configured repository and a distinct unknown-pair scenario.
        from scripts.pipeline.compute_metrics import _build_automation_summary
        public = [
            {"name": "public-config", "has_ci_workflows": None if ci_unavailable else True,
             "workflow_file_count": None if ci_unavailable else 1},
            {"name": "public-other", "has_ci_workflows": None if ci_partial or ci_unavailable else False,
             "workflow_file_count": None if ci_partial or ci_unavailable else 0},
        ]
        private = [{"name": "private-other", "has_ci_workflows": None if ci_unavailable else False,
                    "workflow_file_count": None if ci_unavailable else 0}]
        automation = _build_automation_summary(
            {"public_owned_nonfork": 2, "private_owned_nonfork": 1}, public, private)
        return {
            "automation": automation,
            "dashboard_data": {
                "username": "jguida941",
                "generated_at": "2026-08-26T12:00:00Z",
            },
            "snapshot": snapshot,
            "snapshot_rows": snapshot_rows,
            "scorecard": scorecard,
            "scorecard_cards": [],
            "engineering": engineering,
            "data_quality": data_quality,
            "data_scope": {
                "repos_included": "public + private observed, exact",
                "metric_scopes": metric_scopes,
            },
            "top_languages": [
                {"name": "Rust", "bytes": 1200, "percent": 60.0},
                {"name": "Python", "bytes": 800, "percent": 40.0},
            ],
            "language_bytes": {"Rust": 1200, "Python": 800},
            "recent_repos": [],
            "spotlight_data": [],
            "focus": {"now": [], "next": [], "shipped": []},
        }

    @staticmethod
    def _metric_fixture(family, *, control=False):
        empty_population = family == "language" and control
        push_age = 30 if family == "push" and control else 1
        pushed_at = (
            ""
            if family == "push" and not control
            else (datetime.now(timezone.utc) - timedelta(days=push_age))
            .isoformat()
            .replace("+00:00", "Z")
        )
        automation_unavailable = family == "automation" and not control
        language_unavailable = family == "language" and not control

        def repository(name, *, private, language):
            return {
                "name": name,
                "owner": {"login": "jguida941"},
                "private": private,
                "visibility": "private" if private else "public",
                "fork": False,
                "html_url": f"https://github.com/jguida941/{name}",
                "pushed_at": pushed_at,
                "created_at": "2025-01-01T00:00:00Z",
                "stargazers_count": 0,
                "forks_count": 0,
                "language": language,
                "latest_commit_message": f"Improve {name}",
                "has_ci_workflows": None if automation_unavailable else False,
                "workflow_file_count": None if automation_unavailable else 0,
                "language_bytes": {} if language_unavailable else {language: 1000},
                "language_bytes_complete": not language_unavailable,
            }

        public = [] if empty_population else [
            repository("public-service", private=False, language="Python")
        ]
        private = [] if empty_population else [
            repository("private-service", private=True, language="Rust")
        ]
        public_language_bytes = {
            language: byte_count
            for row in public
            for language, byte_count in row["language_bytes"].items()
        }
        return CollectedProfileData(
            repo_counts={
                "public_owned_total": len(public),
                "public_owned_forks": 0,
                "public_owned_nonfork": len(public),
                "private_owned": len(private),
                "private_owned_nonfork": len(private),
            },
            repos=public,
            all_repos=public,
            language_bytes=public_language_bytes,
            events=[],
            latest_push_message_by_repo={},
            public_scope_commits=12,
            ci_count_probe=0,
            calendar={
                "totalContributions": 12,
                "weeks": [{"contributionDays": [{
                    "date": datetime.now(timezone.utc).date().isoformat(),
                    "contributionCount": 1,
                }]}],
            },
            total_contributions=12,
            token_mode="none",
            cache_mode={"bypass": True, "ttl_seconds": 0},
            private_repos=private,
        )

    @classmethod
    def _aggregate_observation_fixture(cls, *, exact):
        now = datetime.now(timezone.utc)
        observed_at = now.isoformat().replace("+00:00", "Z")
        window_start = (now - timedelta(days=365)).isoformat().replace("+00:00", "Z")
        previous_at = (now - timedelta(days=1)).isoformat().replace("+00:00", "Z")

        def observation(
            metric_id,
            source_metric_id,
            value,
            status,
            population_id,
            source_id,
            source_mode,
            completion_reason,
            *,
            population_signature=None,
            window=False,
            source_time=None,
        ):
            return {
                "schema": "profile-provider-observation/v1",
                "metric_id": metric_id,
                "source_metric_id": source_metric_id,
                "value": value,
                "status": status,
                "complete": True,
                "population_id": population_id,
                "population_signature": population_signature,
                "window_start": window_start if window else None,
                "window_end": observed_at if window else None,
                "observed_at": source_time or observed_at,
                "source_id": source_id,
                "source_mode": source_mode,
                "completion_reason": completion_reason,
            }

        if exact:
            observations = {
                "public_scope_commits": observation(
                    "public_scope_commits",
                    "owned_public_nonfork_authored_commits",
                    0,
                    "ok",
                    "owned-public-nonfork-repositories",
                    "github_rest_repo_commits",
                    "live",
                    "all_components_observed",
                    population_signature="public-population-current",
                ),
                "prs_merged": observation(
                    "prs_merged",
                    "merged_prs_primary_visible_population",
                    0,
                    "ok",
                    "owned-repositories-visible-to-primary-pr-search",
                    "github_rest_merged_pr_search_primary",
                    "live",
                    "all_components_observed",
                    window=True,
                ),
                "last_year_contributions": observation(
                    "last_year_contributions",
                    "github_contribution_calendar_total_and_days",
                    {
                        "total": 0,
                        "days": ({"date": now.date().isoformat(), "count": 0},),
                    },
                    "ok",
                    "github-contribution-calendar-visible-to-provider",
                    "github_graphql_contribution_calendar",
                    "live",
                    "all_components_observed",
                    window=True,
                ),
            }
            calendar = {
                "totalContributions": 0,
                "weeks": [{"contributionDays": [{
                    "date": now.date().isoformat(),
                    "contributionCount": 0,
                }]}],
            }
            total_contributions = 0
        else:
            observations = {
                "public_scope_commits": observation(
                    "public_scope_commits",
                    "github_total_commit_contributions",
                    999,
                    "fallback",
                    "github-user-contributions-visible-to-provider",
                    "github_graphql_commit_contributions",
                    "fallback",
                    "different_metric_fallback",
                ),
                "prs_merged": observation(
                    "prs_merged",
                    "merged_prs_public_visible_population",
                    23,
                    "fallback",
                    "owned-public-repositories-visible-to-public-pr-search",
                    "github_rest_merged_pr_search_public",
                    "fallback",
                    "public_retry",
                    window=True,
                ),
                "last_year_contributions": observation(
                    "last_year_contributions",
                    "previous_profile_snapshot_contributions",
                    777,
                    "fallback",
                    "github-contribution-calendar-visible-to-provider",
                    "previous_profile_snapshot",
                    "previous_snapshot",
                    "previous_snapshot",
                    source_time=previous_at,
                ),
            }
            calendar = None
            total_contributions = None

        base = cls._metric_fixture("automation", control=True)
        return replace(
            base,
            public_scope_commits=0 if exact else None,
            calendar=calendar,
            total_contributions=total_contributions,
            metric_observations=observations,
        )

    @staticmethod
    def _text_nodes(svg):
        root = ET.fromstring(svg)
        return [
            "".join(node.itertext()).strip()
            for node in root.iter()
            if node.tag.rsplit("}", 1)[-1] == "text"
            and "".join(node.itertext()).strip()
        ]

    def _metric_value(self, svg, label):
        nodes = self._text_nodes(svg)
        self.assertIn(label, nodes)
        return nodes[nodes.index(label) + 1]

    def _compute_and_render(self, collected):
        model = compute_profile_model(
            collected,
            logger=lambda *_: None,
            allow_network_calls=False,
        )
        return model, self._render_profile_cards(model, collected=collected)

    def _render_profile_cards(self, model, collected=None):
        from scripts.pipeline.render_outputs import generate_assets

        if collected is None:
            collected = types.SimpleNamespace(
                repo_counts={
                    "public_owned_nonfork": 2,
                    "public_owned_forks": 0,
                    "private_owned": 1,
                },
                total_contributions=120,
                language_bytes=model["language_bytes"],
                events=[],
                calendar={},
            )
        outputs = {
            "language": Path("assets/lang_breakdown.svg"),
            "scorecard": Path("assets/builder_scorecard.svg"),
            "cadence": Path("assets/engineering_cadence.svg"),
            "snapshot": Path("assets/raw_snapshot.svg"),
            "general": Path("metrics.general.svg"),
        }
        ignored_generators = {
            "gen_badges": lambda *args, **kwargs: None,
            "gen_working": lambda *args, **kwargs: None,
            "gen_heatmap": lambda *args, **kwargs: None,
            "gen_contribution_panel": lambda *args, **kwargs: None,
            "gen_spotlight": lambda *args, **kwargs: None,
            "gen_focus_board": lambda *args, **kwargs: None,
            "gen_streak_summary": lambda *args, **kwargs: None,
        }

        with tempfile.TemporaryDirectory() as directory:
            previous_directory = Path.cwd()
            os.chdir(directory)
            try:
                Path("assets").mkdir()
                with patch.multiple(
                    "scripts.pipeline.render_outputs",
                    **ignored_generators,
                ):
                    generate_assets(model=model, collected=collected, logger=lambda *_: None)
                rendered = {
                    name: path.read_text(encoding="utf-8")
                    for name, path in outputs.items()
                }
            finally:
                os.chdir(previous_directory)
        return rendered

    @staticmethod
    def _model_value(model, path):
        value = model
        for key in path:
            value = value[key]
        return value

    def _assert_unavailable_family(self, family):
        model, cards = self._compute_and_render(self._metric_fixture(family))
        control, control_cards = self._compute_and_render(
            self._metric_fixture(family, control=True)
        )
        paths = {
            "push": (
                ("scorecard", "active_repos_7d"),
                ("scorecard", "days_since_last_push"),
                ("scorecard", "median_days_since_push"),
                ("engineering", "days_since_last_push"),
                ("engineering", "median_days_since_push"),
            ),
            "automation": (
                ("scorecard", "ci_coverage_pct"),
                ("scorecard", "automation_workflows"),
                ("engineering", "automation_repos"),
                ("engineering", "automation_workflows"),
                ("snapshot", "ci_repos"),
            ),
            "language": (
                ("scorecard", "primary_lang_share_pct"),
                ("engineering", "primary_lang_share_pct"),
                ("engineering", "languages_over_5pct"),
                ("snapshot", "languages_count"),
            ),
        }
        status_keys = {
            "push": "active_repos_7d",
            "automation": "automation_repos",
            "language": "top_languages",
        }
        unrelated_statuses = {
            "push": ("automation_repos", "top_languages"),
            "automation": ("active_repos_7d", "top_languages"),
            "language": ("active_repos_7d", "automation_repos"),
        }
        card_claims = {
            "push": (("scorecard", "Active Repos (7d)"),),
            "automation": (
                ("scorecard", "Workflow files"),
                ("cadence", "Workflow files"),
                ("general", "Workflow repos"),
            ),
            "language": (
                ("scorecard", "Primary Language"),
                ("cadence", "primary language"),
                ("general", "languages"),
            ),
        }

        for path in paths[family]:
            with self.subTest(family=family, unavailable_model=".".join(path)):
                self.assertIsNone(self._model_value(model, path))
        statuses = model["data_quality"]["metric_statuses"]
        with self.subTest(family=family, evidence="status and family isolation"):
            self.assertEqual("unavailable", statuses[status_keys[family]])
            self.assertEqual(
                ("exact", "exact"),
                tuple(statuses[key] for key in unrelated_statuses[family]),
            )
        for card, label in card_claims[family]:
            with self.subTest(family=family, unavailable_card=f"{card}:{label}"):
                self.assertEqual("n/a", self._metric_value(cards[card], label))

        status_label = {
            "push": "Push · Unavailable",
            "automation": "Workflows · Unavailable",
            "language": "Language · Unavailable",
        }[family]
        with self.subTest(family=family, evidence="visible unavailable status"):
            self.assertIn(status_label, self._text_nodes(cards["snapshot"]))
        if family == "automation":
            with self.subTest(family=family, evidence="no numeric unavailable caption"):
                self.assertNotIn("0 repos", self._text_nodes(cards["cadence"]))
        if family == "language":
            with self.subTest(family=family, evidence="empty language chart"):
                self.assertFalse(
                    any(value.endswith("%") for value in self._text_nodes(cards["language"]))
                )

        with self.subTest(family=family, evidence="nearest valid control"):
            control_statuses = control["data_quality"]["metric_statuses"]
            self.assertEqual("exact", control_statuses[status_keys[family]])
            if family == "push":
                self.assertEqual(0, control["scorecard"]["active_repos_7d"])
                self.assertGreater(control["scorecard"]["days_since_last_push"], 0)
                self.assertGreater(control["scorecard"]["median_days_since_push"], 0)
                self.assertGreater(control["engineering"]["days_since_last_push"], 0)
                self.assertGreater(control["engineering"]["median_days_since_push"], 0)
                self.assertEqual(
                    "0", self._metric_value(control_cards["scorecard"], "Active Repos (7d)")
                )
            elif family == "automation":
                for path in paths[family]:
                    self.assertEqual(0, self._model_value(control, path))
                for card, label in card_claims[family]:
                    self.assertEqual("0", self._metric_value(control_cards[card], label))
                self.assertIn("0 repos", self._text_nodes(control_cards["cadence"]))
            else:
                for path in paths[family]:
                    self.assertEqual(0, self._model_value(control, path))
                self.assertEqual(
                    "0.0%",
                    self._metric_value(control_cards["scorecard"], "Primary Language"),
                )
                self.assertEqual(
                    "0%",
                    self._metric_value(control_cards["cadence"], "primary language"),
                )
                self.assertEqual(
                    "0",
                    self._metric_value(control_cards["general"], "languages"),
                )
                self.assertIn(
                    "No language data available",
                    self._text_nodes(control_cards["language"]),
                )

    def test_unavailable_push_observations_do_not_become_zero_activity(self):
        self._assert_unavailable_family("push")

    def test_unavailable_automation_observations_do_not_become_zero_pipelines(self):
        self._assert_unavailable_family("automation")

    def test_unavailable_language_observations_do_not_become_zero_percentages(self):
        self._assert_unavailable_family("language")

    def test_general_metrics_distinguishes_missing_values_from_zero(self):
        from scripts.rendering.generate_metrics_general import generate

        numeric_keys = (
            "last_year_contributions",
            "public_scope_commits",
            "total_repos",
            "private_owned_repos",
            "total_stars",
            "languages_count",
            "prs_merged",
            "releases",
            "ci_repos",
            "streak_days",
        )
        footer_fragments = {
            "total_repos": "n/a Repositories",
            "total_stars": "n/a Stargazers",
            "releases": "n/a Releases",
        }
        baseline = {key: 7 for key in numeric_keys}

        for key in numeric_keys:
            snapshot = dict(baseline)
            snapshot[key] = None
            with self.subTest(metric=key, missing_value=None):
                with tempfile.TemporaryDirectory() as directory:
                    output = Path(directory) / "metrics.general.svg"
                    generate(
                        username="jguida941",
                        snapshot=snapshot,
                        data_scope={"metric_scopes": {}},
                        generated_at="2026-08-26T12:00:00Z",
                        output_path=str(output),
                    )
                    svg = output.read_text(encoding="utf-8")
                if key in footer_fragments:
                    self.assertIn(footer_fragments[key], svg)
                else:
                    self.assertIn(">n/a<", svg)

        invalid_snapshot = dict(baseline)
        invalid_snapshot["last_year_contributions"] = "not-a-number"
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "metrics.general.svg"
            generate(
                username="jguida941",
                snapshot=invalid_snapshot,
                data_scope={"metric_scopes": {}},
                generated_at="2026-08-26T12:00:00Z",
                output_path=str(output),
            )
            invalid_svg = output.read_text(encoding="utf-8")
        self.assertIn(">n/a<", invalid_svg)

        zero_snapshot = {key: 0 for key in numeric_keys}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "metrics.general.svg"
            generate(
                username="jguida941",
                snapshot=zero_snapshot,
                data_scope={"metric_scopes": {}},
                generated_at="2026-08-26T12:00:00Z",
                output_path=str(output),
            )
            zero_svg = output.read_text(encoding="utf-8")
        self.assertIn(">0<", zero_svg)
        self.assertNotIn(">n/a<", zero_svg)
        self.assertIn("0 Repositories", zero_svg)

    def test_readme_raw_snapshot_is_current_with_its_renderer(self):
        from scripts.rendering.generate_snapshot_panel import generate

        root = Path(__file__).resolve().parents[2]
        readme = (root / "README.md").read_text(encoding="utf-8")
        reference = re.search(
            r'<img\s+src="([^"?]*assets/raw_snapshot\.svg)(?:\?[^\"]*)?"',
            readme,
        )
        self.assertIsNotNone(reference, "README must publish the Raw Snapshot asset")
        published_path = root / reference.group(1)
        public_data = json.loads(
            (root / "site/data/profile_snapshot.json").read_text(encoding="utf-8")
        )

        with tempfile.TemporaryDirectory() as directory:
            generated_path = Path(directory) / "raw_snapshot.svg"
            generate(
                public_data["snapshot_rows"],
                public_data["data_quality"],
                data_scope=public_data.get("data_scope"),
                automation=public_data.get("automation"),
                output_path=str(generated_path),
            )
            current_renderer_output = generated_path.read_bytes()

        self.assertEqual(
            current_renderer_output,
            published_path.read_bytes(),
            "the README Raw Snapshot must be regenerated when its renderer semantics change",
        )

    def test_provider_fallbacks_stay_qualified_in_generated_cards(self):
        model, cards = self._compute_and_render(
            self._aggregate_observation_fixture(exact=False)
        )

        self.assertIsNone(model["snapshot"]["public_scope_commits"])
        self.assertIsNone(model["snapshot"]["prs_merged"])
        self.assertEqual("n/a", self._metric_value(cards["general"], "commits"))
        self.assertEqual("n/a", self._metric_value(cards["general"], "PRs merged"))

        expected_fallbacks = {
            "public_scope_commits": 999,
            "prs_merged": 23,
            "last_year_contributions": 777,
        }
        for metric, expected_value in expected_fallbacks.items():
            with self.subTest(metric=metric, evidence="typed fallback value"):
                self.assertEqual(
                    expected_value,
                    model["data_quality"]["non_exact_metrics"][metric]["value"],
                )
                self.assertEqual(
                    expected_value,
                    model["dashboard_data"]["data_quality"]
                    ["non_exact_metrics"][metric]["value"],
                )

        snapshot_nodes = self._text_nodes(cards["snapshot"])
        contribution_label_index = snapshot_nodes.index("contributions")
        self.assertEqual("n/a", snapshot_nodes[contribution_label_index - 1])
        self.assertEqual("n/a", self._metric_value(cards["snapshot"], "Commits"))
        pr_evidence = " ".join(
            node
            for node in snapshot_nodes
            if any(
                term in node.casefold()
                for term in ("prs", "pull request", "pull-request")
            )
        ).casefold()
        contribution_evidence = " ".join(
            node for node in snapshot_nodes if "contribution" in node.casefold()
        ).casefold()
        commit_evidence = " ".join(
            node for node in snapshot_nodes if "commit" in node.casefold()
        ).casefold()

        with self.subTest(metric="prs_merged", evidence="fallback status"):
            self.assertIn("fallback", pr_evidence)
        with self.subTest(metric="prs_merged", evidence="public scope"):
            self.assertIn("public", pr_evidence)
        with self.subTest(metric="last_year_contributions", evidence="fallback status"):
            self.assertIn("fallback", contribution_evidence)
        with self.subTest(metric="last_year_contributions", evidence="source currentness"):
            self.assertTrue(
                "previous" in contribution_evidence
                or "noncurrent" in contribution_evidence
            )
        for value, evidence in (
            (999, commit_evidence),
            (23, pr_evidence),
            (777, contribution_evidence),
        ):
            with self.subTest(value=value, evidence="displayed fallback qualification"):
                if any(str(value) in node for node in snapshot_nodes):
                    self.assertIn("fallback", evidence)

    def test_current_zero_provider_values_stay_exact_in_generated_cards(self):
        model, cards = self._compute_and_render(
            self._aggregate_observation_fixture(exact=True)
        )

        for metric in (
            "public_scope_commits",
            "prs_merged",
            "last_year_contributions",
        ):
            with self.subTest(metric=metric, evidence="exact zero model value"):
                self.assertEqual(0, model["snapshot"][metric])
                self.assertNotIn(
                    metric,
                    model["data_quality"].get("non_exact_metrics", {}),
                )

        self.assertEqual("0", self._metric_value(cards["general"], "commits"))
        self.assertEqual("0", self._metric_value(cards["general"], "PRs merged"))
        snapshot_nodes = self._text_nodes(cards["snapshot"])
        contribution_label_index = snapshot_nodes.index("contributions")
        self.assertEqual("0", snapshot_nodes[contribution_label_index - 1])
        self.assertEqual("0", self._metric_value(cards["snapshot"], "Commits"))

        for subject, terms in {
            "prs": ("prs", "pull request", "pull-request"),
            "contribution": ("contribution",),
        }.items():
            with self.subTest(subject=subject, evidence="current status"):
                subject_evidence = " ".join(
                    node
                    for node in snapshot_nodes
                    if any(term in node.casefold() for term in terms)
                ).casefold()
                self.assertIn("ok", subject_evidence)
                self.assertNotIn("fallback", subject_evidence)
                self.assertNotIn("noncurrent", subject_evidence)

    def test_partial_ci_values_are_qualified_on_every_card(self):
        partial = self._render_profile_cards(
            self._card_model(ci_status="partial", language_status="exact")
        )
        exact = self._render_profile_cards(
            self._card_model(ci_status="exact", language_status="exact")
        )
        unavailable = self._render_profile_cards(
            self._card_model(ci_status="unavailable", language_status="exact")
        )
        card_labels = {
            "scorecard": "Repo adoption",
            "cadence": "Repo adoption",
            "general": "Workflow repos",
            "snapshot": "Workflow observation",
        }

        for card, label in card_labels.items():
            with self.subTest(card=card, evidence="partial"):
                text = partial[card]
                self.assertIn(label, text)
                self.assertIn("Partial", text)
                self.assertIn("known", text.casefold())
                self.assertIn("unknown", text.casefold())
            with self.subTest(card=card, evidence="exact"):
                self.assertIn(label, exact[card])
                self.assertNotIn("Partial", exact[card])
                self.assertNotIn("unknown", exact[card].casefold())
            with self.subTest(card=card, evidence="unavailable"):
                self.assertIn("Unavailable", unavailable[card])
                self.assertNotIn("Partial", unavailable[card])
                if card != "snapshot":
                    self.assertIn("n/a", unavailable[card])

    def test_partial_language_values_are_qualified_on_every_card(self):
        partial = self._render_profile_cards(
            self._card_model(ci_status="exact", language_status="partial")
        )
        exact = self._render_profile_cards(
            self._card_model(ci_status="exact", language_status="exact")
        )
        card_values = {
            "language": "Rust",
            "scorecard": "Rust",
            "cadence": "Rust",
            "general": "languages",
            "snapshot": "Language",
        }

        for card, visible_value in card_values.items():
            with self.subTest(card=card, evidence="partial"):
                text = partial[card]
                self.assertIn(visible_value, text)
                self.assertIn("Partial", text)
                lower_text = text.casefold()
                self.assertTrue(
                    "observed" in lower_text or "known" in lower_text,
                    "partial language values must identify their observed basis",
                )
            with self.subTest(card=card, evidence="exact"):
                if card != "snapshot":
                    self.assertIn(visible_value, exact[card])
                self.assertNotIn("Partial", exact[card])

    def test_snapshot_reports_repository_and_metric_family_quality(self):
        from scripts.rendering.generate_snapshot_panel import generate

        base_model = self._card_model(ci_status="exact", language_status="exact")
        base_quality = dict(base_model["data_quality"])
        scenarios = {
            "private unavailable": (
                {
                    **base_quality,
                    "private_aggregate_status": "unavailable",
                    "metric_statuses": {
                        **base_quality["metric_statuses"],
                        "active_repos_7d": "partial",
                        "automation_repos": "partial",
                        "top_languages": "partial",
                    },
                },
                "public observed, private unavailable",
                (
                    "Private · Unavailable",
                    "Push · Partial",
                    "Workflows · Partial",
                    "Language · Partial",
                ),
            ),
            "mixed partial": (
                {
                    **base_quality,
                    "private_aggregate_status": "partial",
                    "metric_statuses": {
                        **base_quality["metric_statuses"],
                        "active_repos_7d": "partial",
                        "automation_repos": "partial",
                        "top_languages": "partial",
                    },
                },
                "public + private observed, partial",
                (
                    "Private · Partial",
                    "Push · Partial",
                    "Workflows · Partial",
                    "Language · Partial",
                ),
            ),
            "exact": (
                base_quality,
                "public + private observed, exact",
                (
                    "Private · Exact",
                    "Push · Exact",
                    "Workflows · Exact",
                    "Language · Exact",
                ),
            ),
        }

        for name, (quality, population, expected_labels) in scenarios.items():
            with tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "raw-snapshot.svg"
                generate(
                    base_model["snapshot_rows"],
                    quality,
                    data_scope={"repos_included": population},
                    output_path=str(output),
                )
                svg = output.read_text(encoding="utf-8")
            with self.subTest(scenario=name, assertion="family labels"):
                for label in expected_labels:
                    self.assertIn(label, svg)
            with self.subTest(scenario=name, assertion="population"):
                normalized_population = (
                    population.casefold().replace("+", " ").replace(",", " ")
                )
                for word in normalized_population.split():
                    self.assertIn(word, svg.casefold())
            with self.subTest(scenario=name, assertion="existing pipeline labels"):
                for label in ("Workflow observation · OK", "Commits · OK", "Releases · OK", "Events · OK"):
                    self.assertIn(label, svg)


class DataSemanticsContract(unittest.TestCase):
    def test_engineering_exposes_the_true_last_push_not_only_a_median(self):
        """`_build_engineering_metrics` must expose `days_since_last_push` = the FRESHEST repo's
        age (the user's real last push), so a stale-looking median across all repos can stop
        being presented as "since last push". Freshest <= median, and is non-negative."""
        from scripts.pipeline.compute_metrics import _build_engineering_metrics
        now = datetime(2026, 6, 29, tzinfo=timezone.utc)

        def _iso(days_ago: int) -> str:
            return (now - timedelta(days=days_ago)).isoformat().replace("+00:00", "Z")

        repos = [
            {"name": "fresh-today", "pushed_at": _iso(0)},
            {"name": "stale-300d", "pushed_at": _iso(300)},
            {"name": "stale-100d", "pushed_at": _iso(100)},
        ]
        collected = types.SimpleNamespace(calendar={}, repo_counts={}, private_repos=[])
        m = _build_engineering_metrics(collected, repos, [], now)
        self.assertIn("days_since_last_push", m,
                      "engineering metrics must expose days_since_last_push (the true last push)")
        self.assertEqual(m["days_since_last_push"], 0,
                         "days_since_last_push must be the FRESHEST repo's age (pushed today => 0)")
        self.assertLessEqual(m["days_since_last_push"], m["median_days_since_push"],
                             "the freshest push cannot be staler than the median across all repos")

    def test_no_presented_metric_shows_a_median_as_your_last_push(self):
        """The exact dishonesty the owner caught: a MEDIAN-across-all-repos value presented under a
        'last push' / 'last commit' label, which reads as 'you haven't pushed in N days'. No
        presented scorecard metric may pair a last-push label with the median key, and the honest
        days_since_last_push must be the one presented."""
        from scripts.contracts.profile_contract import SCORECARD_METRICS
        for metric in SCORECARD_METRICS:
            text = f"{metric.get('label', '')} {metric.get('detail', '')}".lower()
            if "last push" in text or "last commit" in text:
                self.assertNotEqual(
                    metric.get("key"), "median_days_since_push",
                    "a 'last push' metric must NOT bind the median across all repos (reads as inactivity)")
        keys = {metric.get("key") for metric in SCORECARD_METRICS}
        self.assertIn("days_since_last_push", keys,
                      "the scorecard must present the honest last-push metric (days_since_last_push)")

    def test_dashboard_binds_the_honest_last_push_metric(self):
        """The generated dashboard must bind the honest freshest-push metric, never the median
        under a last-push caption."""
        from scripts.pipeline.web_render import render_dashboard
        html = render_dashboard()
        self.assertIn("scorecard.days_since_last_push", html,
                      "the dashboard must bind the honest last-push metric (days_since_last_push)")


class ContributionTrendRenderingTests(unittest.TestCase):
    def _engineering(self, *, zero=False, missing=False):
        from tests.pipeline.test_compute_metrics_accuracy import ContributionTrendTests
        fixture = ContributionTrendTests()
        value = fixture._input(zero=zero)
        trend = fixture._trend(value)
        return {"active_days_last_year": 0 if zero else 17,
                "weekly_cadence": [p["contributions"] for p in trend["points"]],
                **({} if missing else {"contribution_trend": trend})}

    def _svg(self, engineering):
        import io
        from scripts.rendering.generate_engineering_cadence import generate
        class Sink(io.StringIO):
            def close(self):
                pass
        sink = Sink()
        with patch("builtins.open", return_value=sink):
            generate(engineering)
        return sink.getvalue()

    def _errors(self, engineering, svg):
        from scripts.quality.validate_generated_profile import _contribution_trend_claim_errors
        with patch.object(Path, "exists", return_value=True), patch.object(Path, "read_text", return_value=svg):
            return _contribution_trend_claim_errors({"engineering": engineering})

    def test_visible_context_and_plot_match_the_dated_values(self):
        for zero in (False, True):
            engineering = self._engineering(zero=zero)
            svg = self._svg(engineering)
            self.assertIn("Weekly contributions", svg)
            self.assertIn("Sep 21 – Oct 7, 2026 · 3 weeks", svg)
            self.assertIn("Mon–Sun · UTC · partial weeks included", svg)
            self.assertEqual([], self._errors(engineering, svg))

    def test_missing_dated_input_is_not_an_undated_line(self):
        svg = self._svg(self._engineering(missing=True))
        self.assertIn("Contribution trend unavailable", svg)
        self.assertNotIn("<polyline", svg)
        self.assertNotIn("Peak", svg)

    def test_guard_rejects_renamed_missing_and_corrupted_plot(self):
        engineering = self._engineering()
        svg = self._svg(engineering)
        corruptions = (
            svg.replace('data-series="weekly-contributions"', 'data-series="other"'),
            re.sub(r'<g data-series="weekly-contributions">.*?</g>', '', svg),
            svg.replace("Weekly contributions", "Weekly commits"),
            svg.replace("Mon–Sun · UTC · partial weeks included", "Mon–Sun · UTC · complete weeks"),
            re.sub(r'(<polyline[^>]*points=")[^"]+', r'\g<1>252,117 532,117 812,117', svg),
        )
        for altered in corruptions:
            with self.subTest(svg=altered):
                self.assertTrue(self._errors(engineering, altered))

    def test_rendered_effects_cannot_be_certified_by_correct_raw_text(self):
        import xml.etree.ElementTree as ET
        engineering = self._engineering()
        svg = self._svg(engineering)
        self.assertEqual([], self._errors(engineering, svg))
        mutations = (
            ("text", "display", "none"), ("text", "font-size", "0"),
            ("text", "x", "9999"), ("polyline", "opacity", "0"),
            ("polyline", "stroke-width", "0"), ("polyline", "transform", "scale(1,-1)"),
            ("polygon", "points", "312,272 780,160 780,272"),
            ("circle", "cy", "999"), ("circle", "r", "0"),
        )
        for kind, attribute, value in mutations:
            with self.subTest(kind=kind, attribute=attribute):
                root = ET.fromstring(svg)
                chart = next(n for n in root.iter() if n.get("data-series") == "weekly-contributions")
                chart.find("{*}" + kind).set(attribute, value)
                self.assertTrue(self._errors(engineering, ET.tostring(root, encoding="unicode")))
        for kind in ("root", "group"):
            root = ET.fromstring(svg)
            node = root if kind == "root" else next(n for n in root.iter() if n.get("data-series"))
            node.set("transform", "translate(0 10000)")
            self.assertTrue(self._errors(engineering, ET.tostring(root, encoding="unicode")))
        root = ET.fromstring(svg)
        root.set("viewBox", "10000 10000 840 494")
        self.assertTrue(self._errors(engineering, ET.tostring(root, encoding="unicode")))

    def test_real_axes_and_every_marker_are_guarded(self):
        import xml.etree.ElementTree as ET
        engineering = self._engineering()
        svg = self._svg(engineering)
        for role, attribute, value in (("y-tick", "text", "999"), ("x-tick", "x", "999"),
                                       ("week-point", "cx", "500"), ("y-tick", "visibility", "hidden")):
            root = ET.fromstring(svg)
            nodes = [n for n in root.iter() if n.get("data-role") == role]
            for index in range(len(nodes)):
                altered = ET.fromstring(svg)
                node = [n for n in altered.iter() if n.get("data-role") == role][index]
                if attribute == "text":
                    node.text = value
                else:
                    node.set(attribute, value)
                self.assertTrue(self._errors(engineering, ET.tostring(altered, encoding="unicode")))
        root = ET.fromstring(svg)
        points = [n for n in root.iter() if n.get("data-role") == "week-point"]
        points[-1].set("fill", points[-1].get("stroke"))
        self.assertTrue(self._errors(engineering, ET.tostring(root, encoding="unicode")))

    def test_visible_palette_and_transparent_gradient_base_are_valid(self):
        import xml.etree.ElementTree as ET
        engineering = self._engineering()
        root = ET.fromstring(self._svg(engineering))
        chart = next(n for n in root.iter() if n.get("data-series") == "weekly-contributions")
        chart.find("{*}polyline").set("stroke", "#abcdef")
        chart.find("{*}circle").set("fill", "#abcdef")
        self.assertTrue(any(n.get("stop-opacity") == "0" for n in chart.iter()))
        self.assertEqual([], self._errors(engineering, ET.tostring(root, encoding="unicode")))

    def test_unavailable_context_still_requires_visible_text(self):
        import xml.etree.ElementTree as ET
        from types import SimpleNamespace
        from scripts.pipeline.compute_metrics import _build_contribution_trend
        engineering = {"active_days_last_year": 17, "weekly_cadence": [],
                       "contribution_trend": _build_contribution_trend(SimpleNamespace(calendar=None))}
        root = ET.fromstring(self._svg(engineering))
        self.assertEqual([], self._errors(engineering, ET.tostring(root, encoding="unicode")))
        chart = next(n for n in root.iter() if n.get("data-series"))
        chart.findall("{*}text")[-1].set("fill", "transparent")
        self.assertTrue(self._errors(engineering, ET.tostring(root, encoding="unicode")))

    def test_surrounding_paint_cannot_cover_a_valid_chart(self):
        from copy import deepcopy
        engineering = self._engineering()
        svg = self._svg(engineering)
        self.assertEqual([], self._errors(engineering, svg))
        for effect in ("chart-first", "panel-last", "panel-copy", "nested-panel", "moved-tile", "moved-icon", "large-path"):
            with self.subTest(effect=effect):
                root = ET.fromstring(svg)
                chart = next(n for n in root if n.get("data-series"))
                panel = next(n for n in root if n.get("filter") == "url(#gk-shadow)")
                if effect == "chart-first":
                    root.remove(chart)
                    root.insert(0, chart)
                elif effect == "panel-last":
                    root.remove(panel)
                    root.append(panel)
                elif effect == "panel-copy":
                    root.append(deepcopy(panel))
                elif effect == "nested-panel":
                    ET.SubElement(root, "{http://www.w3.org/2000/svg}g").append(deepcopy(panel))
                elif effect == "moved-tile":
                    tile = next(n for n in list(root)[list(root).index(chart) + 1:] if n.get("fill-opacity") == "0.55")
                    tile.set("y", "100")
                else:
                    icon = next(n for n in list(root)[list(root).index(chart) + 1:] if "translate" in n.get("transform", ""))
                    if effect == "moved-icon":
                        icon.set("transform", "translate(252,96) scale(0.667)")
                    else:
                        icon.find("{*}path").set("d", "M0 -999 L24 -999")
                self.assertTrue(self._errors(engineering, ET.tostring(root, encoding="unicode")))

    def test_document_and_chart_elements_require_svg_identity(self):
        engineering = self._engineering()
        svg = self._svg(engineering)
        for kind in ("svg", "g", "text", "polyline", "circle", "linearGradient", "stop"):
            with self.subTest(kind=kind):
                root = ET.fromstring(svg)
                chart = next(n for n in root if n.get("data-series"))
                node = root if kind == "svg" else chart if kind == "g" else chart.find(".//{*}" + kind)
                node.tag = "{urn:not-svg}" + kind
                self.assertTrue(self._errors(engineering, ET.tostring(root, encoding="unicode")))
        for state in ("unavailable", "empty"):
            from types import SimpleNamespace
            from scripts.pipeline.compute_metrics import _build_contribution_trend
            engineering = {"active_days_last_year": 17 if state == "unavailable" else 0,
                           "weekly_cadence": [], "contribution_trend": _build_contribution_trend(SimpleNamespace(calendar=None))}
            root = ET.fromstring(self._svg(engineering))
            self.assertEqual([], self._errors(engineering, ET.tostring(root, encoding="unicode")))
            root.tag = "{urn:not-svg}svg"
            self.assertTrue(self._errors(engineering, ET.tostring(root, encoding="unicode")))

    def test_svg_prefix_alias_and_native_lower_row_effects_remain_valid(self):
        engineering = self._engineering()
        root = ET.fromstring(self._svg(engineering))
        self.assertTrue(any("translate" in n.get("transform", "") for n in root.iter()))
        self.assertTrue(any(n.get("filter") == "url(#gk-shadow)" for n in root.iter()))
        ET.register_namespace("svg", "http://www.w3.org/2000/svg")
        try:
            prefixed = ET.tostring(root, encoding="unicode")
            self.assertIn("<svg:svg", prefixed)
            self.assertEqual([], self._errors(engineering, prefixed))
        finally:
            ET.register_namespace("", "http://www.w3.org/2000/svg")

    def test_compatibility_values_cannot_disagree_with_dated_points(self):
        engineering = self._engineering()
        svg = self._svg(engineering)
        engineering["weekly_cadence"] = [999]
        self.assertTrue(self._errors(engineering, svg))




if __name__ == "__main__":
    unittest.main()

import copy
import json
import os
import re
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from scripts.pipeline.collect_data import CollectedProfileData
from scripts.pipeline.compute_metrics import (
    _build_scorecard_cards,
    _compute_current_streak_days,
    compute_profile_model,
)


def _iso(dt):
    return dt.isoformat().replace("+00:00", "Z")


def _noop(*a, **k):
    pass


def _with_metric_observations(collected, observations):
    copied = replace(collected)
    object.__setattr__(copied, "metric_observations", observations)
    return copied


def _provider_observation(
    *,
    metric_id,
    source_metric_id,
    value,
    status,
    complete,
    population_id,
    population_signature,
    window_start,
    window_end,
    observed_at,
    source_id,
    source_mode,
    completion_reason,
):
    return {
        "schema": "profile-provider-observation/v1",
        "metric_id": metric_id,
        "source_metric_id": source_metric_id,
        "value": value,
        "status": status,
        "complete": complete,
        "population_id": population_id,
        "population_signature": population_signature,
        "window_start": window_start,
        "window_end": window_end,
        "observed_at": observed_at,
        "source_id": source_id,
        "source_mode": source_mode,
        "completion_reason": completion_reason,
    }


def _publication_hold_reasons(model):
    direct = model.get("publication_hold_reasons", ())
    if direct:
        return tuple(direct)
    quality = model.get("data_quality", {})
    return tuple(quality.get("publication_hold_reasons", ()))


_PRIVATE_AGGREGATE_METRICS = (
    "active_repos_7d",
    "days_since_last_push",
    "automation_repos",
    "automation_workflows",
    "top_languages",
)


def _scope_names_profile_exclusion(scope):
    normalized = str(scope or "").casefold()
    compact = normalized.replace("-", "").replace("_", "").replace(" ", "")
    return (
        "owned" in compact
        and "nonfork" in compact
        and "exclud" in compact
        and ("profile" in compact or "self" in compact)
    )


class ContributionRhythmTests(unittest.TestCase):
    def _input(self, length=17, zero=False):
        from types import SimpleNamespace
        rows = [{"date": str(date(2026, 9, 21) + timedelta(days=i)),
                 "contributionCount": 0 if zero else i + 1} for i in range(length)]
        return SimpleNamespace(calendar={"totalContributions": sum(r["contributionCount"] for r in rows),
                                        "weeks": [{"contributionDays": rows}]}, metric_observations={})

    def _rhythm(self, value):
        from scripts.pipeline.compute_metrics import _build_contribution_rhythm
        return _build_contribution_rhythm(value)

    def test_full_calendar_sums_and_unequal_coverage(self):
        value = self._input()
        result = self._rhythm(value)
        self.assertEqual([24, 27, 30, 15, 17, 19, 21], [r["contributions"] for r in result["weekdays"]])
        self.assertEqual([3, 3, 3, 2, 2, 2, 2], [r["days_observed"] for r in result["weekdays"]])
        self.assertEqual((153, 17, "unknown"), (result["total"], result["days_observed"], result["completeness"]))
        value.calendar["weeks"][0]["contributionDays"].reverse()
        self.assertEqual(result, self._rhythm(value))
        self.assertEqual(5050, self._rhythm(self._input(100))["total"])

    def test_zero_single_day_and_missing_are_distinct(self):
        from scripts.contracts.profile_contract import contribution_rhythm_display
        zero = self._rhythm(self._input(1, zero=True))
        self.assertEqual("available", zero["status"])
        self.assertEqual([1, 0, 0, 0, 0, 0, 0], [r["days_observed"] for r in zero["weekdays"]])
        self.assertEqual("No contributions in the observed dates", contribution_rhythm_display(zero)["message"])
        value = self._input()
        value.calendar = None
        missing = self._rhythm(value)
        self.assertEqual(("unavailable", None, []), (missing["status"], missing["total"], missing["weekdays"]))
        self.assertEqual("Contribution rhythm unavailable", contribution_rhythm_display(missing)["message"])

    def test_invalid_calendar_refuses_without_coercion(self):
        for kind in ("boolean", "float", "string", "negative", "date", "gap", "duplicate", "total"):
            value = self._input()
            rows = value.calendar["weeks"][0]["contributionDays"]
            if kind in {"boolean", "float", "string", "negative"}:
                rows[0]["contributionCount"] = {"boolean": True, "float": 1.0, "string": "1", "negative": -1}[kind]
            elif kind == "date": rows[0]["date"] = "20260921"
            elif kind == "gap": rows.pop(4)
            elif kind == "duplicate": rows.append(dict(rows[0]))
            else: value.calendar["totalContributions"] = 152
            with self.subTest(kind=kind):
                self.assertEqual("unavailable", self._rhythm(value)["status"])

    def test_supplied_invalid_observation_cannot_disappear(self):
        for observation in (None, {}, {"status": "ok", "complete": True}):
            value = self._input()
            value.metric_observations = {"last_year_contributions": observation}
            self.assertEqual("unavailable", self._rhythm(value)["status"])

    def test_matching_observation_progress_and_malformed_date(self):
        value = ContributionTrendTests()._input()
        value.calendar["totalContributions"] = 153
        result = self._rhythm(value)
        self.assertEqual(("available", "known", True),
                         (result["status"], result["completeness"], result["last_day_in_progress"]))
        obs = value.metric_observations["last_year_contributions"]
        obs["window_end"] = obs["observed_at"] = "2026-10-08T00:00:00Z"
        self.assertFalse(self._rhythm(value)["last_day_in_progress"])
        obs["value"]["days"][0]["date"] = "2026-9-21"
        self.assertEqual("unavailable", self._rhythm(value)["status"])

    def test_last_supported_date_does_not_require_following_date(self):
        value = self._input(1)
        value.calendar["weeks"][0]["contributionDays"][0]["date"] = "9999-12-31"
        result = self._rhythm(value)
        self.assertEqual(("available", "9999-12-31"), (result["status"], result["window_end"]))


class AccuracyTests(unittest.TestCase):
    def _collected(self):
        now = datetime.now(timezone.utc)
        public_push = _iso(now - timedelta(days=2))
        private_push = _iso(now - timedelta(hours=12))
        recent_event = _iso(now - timedelta(days=1))
        created = _iso(now - timedelta(days=200))

        def repo(
            name,
            msg,
            lang,
            private=False,
            ci=True,
            pushed_at=public_push,
            workflow_file_count=None,
        ):
            return {
                "name": name,
                "owner": {"login": "jguida941"},
                "private": private,
                "visibility": "private" if private else "public",
                "fork": False,
                "html_url": f"https://github.com/jguida941/{name}",
                "pushed_at": pushed_at,
                "created_at": created,
                "stargazers_count": 1,
                "forks_count": 0,
                "language": lang,
                "has_ci_workflows": ci,
                "workflow_file_count": (
                    workflow_file_count
                    if workflow_file_count is not None
                    else (2 if ci else 0)
                ),
                "latest_commit_message": msg,
                "language_bytes": {lang: 1000},
            }

        repos = [
            repo("jguida941", "update canonical profile artifacts", "Python"),
            repo("pub1", "Add real feature X", "Python"),
            repo("pub2", "chore: refresh badges [skip ci]", "Java", ci=False),
        ]
        private_repos = [
            repo(
                "secret-api",
                "private internal commit text",
                "Rust",
                private=True,
                ci=True,
                pushed_at=private_push,
                workflow_file_count=5,
            )
        ]
        events = [
            {
                "type": "PushEvent",
                "actor": {"login": "github-actions[bot]"},
                "repo": {"name": "jguida941/jguida941"},
                "created_at": recent_event,
                "payload": {"commits": [{"message": "update canonical profile artifacts"}]},
            },
            {
                "type": "PushEvent",
                "actor": {"login": "jguida941"},
                "repo": {"name": "jguida941/pub1"},
                "created_at": recent_event,
                "payload": {"commits": [{"message": "Add real feature X"}]},
            },
        ]
        calendar = {
            "totalContributions": 1000,
            "weeks": [
                {
                    "contributionDays": [
                        {"date": (now - timedelta(days=d)).date().isoformat(),
                         "contributionCount": 3 if d <= 2 else 0}
                        for d in range(6, -1, -1)
                    ]
                }
            ],
        }
        return CollectedProfileData(
            repo_counts={"public_owned_total": 3, "public_owned_forks": 0,
                         "public_owned_nonfork": 3, "private_owned": 1,
                         "private_owned_nonfork": 1},
            repos=repos,
            all_repos=repos,
            language_bytes={"Python": 2000, "Java": 1000},
            events=events,
            latest_push_message_by_repo={"jguida941/pub1": "Add real feature X"},
            public_scope_commits=500,
            ci_count_probe=2,
            calendar=calendar,
            total_contributions=1000,
            token_mode="personal_github_token",
            cache_mode={"bypass": True, "ttl_seconds": 0},
            private_repos=private_repos,
        )

    @staticmethod
    def _with_private_evidence(collected, expected_nonfork, private_repos):
        counts = dict(collected.repo_counts)
        counts["private_owned"] = expected_nonfork
        counts["private_owned_nonfork"] = expected_nonfork
        return replace(
            collected,
            repo_counts=counts,
            private_repos=list(private_repos),
        )

    @staticmethod
    def _language_totals(model):
        return {
            row["name"]: row["bytes"]
            for row in model["top_languages"]
        }

    def _synthetic_repo(
        self,
        name,
        headline,
        *,
        minutes_ago,
        private=False,
        language="Python",
    ):
        row = dict(self.collected.repos[1])
        row.update(
            {
                "name": name,
                "private": private,
                "visibility": "private" if private else "public",
                "fork": False,
                "html_url": f"https://github.com/jguida941/{name}",
                "pushed_at": _iso(
                    datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
                ),
                "language": language,
                "latest_commit_message": headline,
                "language_bytes": {language: 1000},
                "language_bytes_complete": True,
                "has_ci_workflows": True,
                "workflow_file_count": 1,
            }
        )
        return row

    def _collected_with_repositories(self, public_repos, private_repos):
        public_repos = list(public_repos)
        private_repos = list(private_repos)
        public_language_bytes = {}
        for repository in public_repos:
            for language, byte_count in repository.get("language_bytes", {}).items():
                public_language_bytes[language] = (
                    public_language_bytes.get(language, 0) + byte_count
                )
        return replace(
            self.collected,
            repo_counts={
                "public_owned_total": len(public_repos),
                "public_owned_forks": 0,
                "public_owned_nonfork": len(public_repos),
                "private_owned": len(private_repos),
                "private_owned_nonfork": len(private_repos),
            },
            repos=public_repos,
            all_repos=public_repos,
            language_bytes=public_language_bytes,
            events=[],
            latest_push_message_by_repo={},
            private_repos=private_repos,
        )

    def setUp(self):
        collected = self._collected()
        self.collected = collected
        self.model = compute_profile_model(collected, logger=_noop, allow_network_calls=False)
        public_only_counts = dict(collected.repo_counts)
        public_only_counts["private_owned"] = 0
        public_only_counts["private_owned_nonfork"] = 0
        public_only = replace(
            collected,
            repo_counts=public_only_counts,
            private_repos=[],
        )
        self.public_only_model = compute_profile_model(
            public_only,
            logger=_noop,
            allow_network_calls=False,
        )
        truncated = self._with_private_evidence(
            collected,
            expected_nonfork=2,
            private_repos=collected.private_repos[:1],
        )
        self.truncated_private_model = compute_profile_model(
            truncated,
            logger=_noop,
            allow_network_calls=False,
        )
        unavailable = self._with_private_evidence(
            collected,
            expected_nonfork=None,
            private_repos=[],
        )
        self.unavailable_private_model = compute_profile_model(
            unavailable,
            logger=_noop,
            allow_network_calls=False,
        )
        self.blob = json.dumps(self.model, default=str)

    def test_self_repo_excluded_everywhere(self):
        names = [r["name"] for r in self.model["recent_repos"]]
        self.assertNotIn("jguida941", names)
        matrix = [r["name"] for r in self.model["repo_overview_rows"]]
        self.assertNotIn("jguida941", matrix)
        created = [r["name"] for r in self.model["recent_created"]]
        self.assertNotIn("jguida941", created)

    def test_no_bot_commit_text_anywhere(self):
        self.assertNotIn("update canonical profile artifacts", self.blob)
        self.assertNotIn("[skip ci]", self.blob)

    def test_no_fabricated_next(self):
        for item in self.model["focus"]["next"]:
            self.assertFalse(item["title"].startswith("Next pass:"))

    def test_complete_private_repository_metadata_reaches_published_surfaces(self):
        private_rows = [
            row for row in self.model["recent_repos"] if row["name"] == "secret-api"
        ]
        self.assertEqual(
            1,
            len(private_rows),
            "a complete private inventory must feed the recent-repository surface",
        )
        private_row = private_rows[0]
        self.assertEqual(
            {
                "name": "secret-api",
                "html_url": "https://github.com/jguida941/secret-api",
                "language": "Rust",
                "pushed_at": self.collected.private_repos[0]["pushed_at"],
                "last_commit_msg": "private internal commit text",
                "is_private": True,
            },
            {key: private_row.get(key) for key in (
                "name",
                "html_url",
                "language",
                "pushed_at",
                "last_commit_msg",
                "is_private",
            )},
        )

        public_row = next(
            row for row in self.model["recent_repos"] if row["name"] == "pub1"
        )
        public_control = next(
            row for row in self.public_only_model["recent_repos"] if row["name"] == "pub1"
        )
        self.assertEqual(public_control, public_row)

        private_focus = next(
            item for item in self.model["focus"]["now"] if item["title"] == "secret-api"
        )
        self.assertTrue(private_focus["is_private"])
        self.assertEqual(
            "https://github.com/jguida941/secret-api",
            private_focus["url"],
        )
        self.assertIn("Rust", private_focus["detail"])
        self.assertIn("pushed", private_focus["detail"])

        from scripts.pipeline.render_outputs import _public_dashboard_data

        published = _public_dashboard_data(self.model["dashboard_data"])
        published_private_focus = next(
            item for item in published["focus"]["now"] if item["title"] == "secret-api"
        )
        self.assertEqual(private_focus, published_private_focus)

        from scripts.rendering.generate_currently_working import generate

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "currently-working.svg"
            with patch(
                "scripts.rendering.generate_currently_working._time_ago",
                side_effect=lambda value: f"activity:{value}",
            ):
                generate(self.model["recent_repos"], output_path=str(output))
            svg = output.read_text(encoding="utf-8")

        for expected in (
            "secret-api",
            "private internal commit text",
            "Rust",
            f"activity:{self.collected.private_repos[0]['pushed_at']}",
            "pub1",
            "Add real feature X",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, svg)
        self.assertIn(
            'd="M7 11V7a5 5 0 0 1 10 0v4"',
            svg,
            "a private repository needs the lock distinction",
        )

    def test_secret_shaped_private_commit_headline_is_not_published(self):
        fake_credential = "Bearer ghp_NOT_A_REAL_TOKEN"
        hostile_private = dict(
            self.collected.private_repos[0],
            latest_commit_message=fake_credential,
        )
        hostile_collected = replace(
            self.collected,
            private_repos=[hostile_private],
        )
        hostile_model = compute_profile_model(
            hostile_collected,
            logger=_noop,
            allow_network_calls=False,
        )
        private_rows = [
            row for row in hostile_model["recent_repos"] if row["name"] == "secret-api"
        ]
        self.assertEqual(
            1,
            len(private_rows),
            "redacting a headline must not remove the private repository row",
        )
        private_row = private_rows[0]
        self.assertTrue(private_row["is_private"])
        self.assertEqual("Rust", private_row["language"])
        self.assertEqual(hostile_private["pushed_at"], private_row["pushed_at"])
        self.assertNotEqual(fake_credential, private_row["last_commit_msg"])

        from scripts.pipeline.render_outputs import _public_dashboard_data
        from scripts.rendering.generate_currently_working import generate

        published = _public_dashboard_data(hostile_model["dashboard_data"])
        self.assertNotIn(fake_credential, json.dumps(published, sort_keys=True))

        with tempfile.TemporaryDirectory() as directory:
            ordinary_output = Path(directory) / "ordinary.svg"
            hostile_output = Path(directory) / "hostile.svg"
            generate(self.model["recent_repos"], output_path=str(ordinary_output))
            generate(hostile_model["recent_repos"], output_path=str(hostile_output))
            ordinary_svg = ordinary_output.read_text(encoding="utf-8")
            hostile_svg = hostile_output.read_text(encoding="utf-8")

        self.assertIn("private internal commit text", ordinary_svg)
        self.assertNotIn(fake_credential, hostile_svg)
        self.assertNotIn("ghp_NOT_A_REAL_TOKEN", hostile_svg)
        self.assertIn("secret-api", hostile_svg)

    def test_security_domain_metadata_survives_model_json_and_svg(self):
        harmless_repository_names = (
            "github_pat_migration_helper",
            "ghp_tokenformatvalidator",
        )
        harmless_headlines = (
            "Improve Bearer token refresh handling",
            "Document bearer authentication support",
            "Refactor Authorization header parser",
        )
        rows = [
            self._synthetic_repo(
                harmless_repository_names[0],
                "Improve migration reporting",
                minutes_ago=1,
            ),
            self._synthetic_repo(
                harmless_repository_names[1],
                "Improve validator reporting",
                minutes_ago=2,
            ),
            self._synthetic_repo(
                "ordinary-control",
                "Improve cache invalidation",
                minutes_ago=3,
            ),
        ]
        rows.extend(
            self._synthetic_repo(
                f"security-docs-{index}",
                headline,
                minutes_ago=10 + index,
            )
            for index, headline in enumerate(harmless_headlines, start=1)
        )
        model = compute_profile_model(
            self._collected_with_repositories(rows, []),
            logger=_noop,
            allow_network_calls=False,
        )

        from scripts.pipeline.render_outputs import _public_dashboard_data
        from scripts.rendering.generate_currently_working import generate

        published = _public_dashboard_data(model["dashboard_data"])
        model_text = json.dumps(
            {"recent_repos": model["recent_repos"], "focus": model["focus"]},
            sort_keys=True,
        )
        published_text = json.dumps(published, sort_keys=True)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "currently-working.svg"
            generate(model["recent_repos"], output_path=str(output))
            svg = output.read_text(encoding="utf-8")

        for value in (*harmless_repository_names, *harmless_headlines):
            with self.subTest(value=value, surface="model"):
                self.assertIn(value, model_text)
            with self.subTest(value=value, surface="dashboard-json"):
                self.assertIn(value, published_text)
            with self.subTest(value=value, surface="svg"):
                self.assertIn(value, svg)

        for control in ("ordinary-control", "Improve cache invalidation"):
            with self.subTest(control=control):
                self.assertIn(control, model_text)
                self.assertIn(control, published_text)
                self.assertIn(control, svg)

    def test_credential_shaped_headlines_are_removed_from_model_and_svg(self):
        synthetic_credentials = (
            (
                "Authorization: token ABCDEFGHIJKLMNOPQRST",
                "Authorization: token",
            ),
            (
                "github_pat_SYNTHETIC_VALUE_1234567890",
                "github_pat_SYNTHETIC_VALUE",
            ),
            (
                "".join(("AKIA", "ABCDEFGHIJKLMNOP")),
                "".join(("AKIA", "ABCDEFGHIJKLMNOP")),
            ),
            (
                "".join(("xoxb", "-", "111111111111", "-", "abcdefghijklmnop")),
                "".join(("xoxb", "-", "111111111111")),
            ),
            (
                "".join(
                    (
                        "eyJhbGciOiJIUzI1NiJ9",
                        ".",
                        "eyJzdWIiOiJzeW50aGV0aWMifQ",
                        ".",
                        "c3ludGhldGljc2lnbmF0dXJl",
                    )
                ),
                "eyJhbGciOiJIUzI1NiJ9",
            ),
        )
        private_rows = [
            self._synthetic_repo(
                f"synthetic-private-{index}",
                credential,
                minutes_ago=index,
                private=True,
            )
            for index, (credential, _marker) in enumerate(
                synthetic_credentials,
                start=1,
            )
        ]
        private_rows.append(
            self._synthetic_repo(
                "private-control",
                "Improve cache invalidation",
                minutes_ago=len(private_rows) + 1,
                private=True,
            )
        )
        model = compute_profile_model(
            self._collected_with_repositories([], private_rows),
            logger=_noop,
            allow_network_calls=False,
        )

        from scripts.rendering.generate_currently_working import generate

        model_text = json.dumps(model["recent_repos"], sort_keys=True)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "currently-working.svg"
            generate(model["recent_repos"], output_path=str(output))
            svg = output.read_text(encoding="utf-8")

        for credential, marker in synthetic_credentials:
            with self.subTest(credential=credential, surface="model"):
                self.assertNotIn(marker, model_text)
            with self.subTest(credential=credential, surface="svg"):
                self.assertNotIn(marker, svg)
        self.assertIn("Improve cache invalidation", model_text)
        self.assertIn("Improve cache invalidation", svg)

    def test_private_commit_headline_reaches_published_shipped_fallback(self):
        newer_public_rows = [
            self._synthetic_repo(
                f"active-public-{index}",
                f"Active public change {index}",
                minutes_ago=index,
            )
            for index in range(1, 4)
        ]
        headline = "Improve private release reporting"
        private_target = self._synthetic_repo(
            "private-release-tools",
            headline,
            minutes_ago=20,
            private=True,
            language="Rust",
        )
        public_target = dict(private_target)
        public_target.update({"private": False, "visibility": "public"})

        public_control = compute_profile_model(
            self._collected_with_repositories(
                [*newer_public_rows, public_target],
                [],
            ),
            logger=_noop,
            allow_network_calls=False,
        )
        private_model = compute_profile_model(
            self._collected_with_repositories(newer_public_rows, [private_target]),
            logger=_noop,
            allow_network_calls=False,
        )

        public_items = [
            item for item in public_control["focus"]["shipped"]
            if item.get("title") == headline
        ]
        self.assertEqual(1, len(public_items), "the public fallback control must ship")
        private_items = [
            item for item in private_model["focus"]["shipped"]
            if item.get("title") == headline
        ]
        self.assertEqual(
            1,
            len(private_items),
            "an ordinary private headline is repository metadata and must use the same fallback",
        )
        private_item = private_items[0]
        public_item = public_items[0]
        self.assertEqual(public_item["title"], private_item["title"])
        self.assertEqual(public_item["detail"], private_item["detail"])
        self.assertEqual(public_item["url"], private_item["url"])
        self.assertTrue(private_item["is_private"])

        from scripts.pipeline.render_outputs import _public_dashboard_data

        published = _public_dashboard_data(private_model["dashboard_data"])
        self.assertIn(private_item, published["focus"]["shipped"])

    def test_general_metrics_footer_labels_public_and_all_owned_domains(self):
        from scripts.rendering.generate_metrics_general import generate
        from scripts.rendering.svg_utils import fmt_int
        from tests.contracts.test_label_legibility import (
            _exact_total_count,
            _footer_layout_errors,
            _positioned_text_lines,
        )

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "metrics.general.svg"
            generate(
                username="jguida941",
                snapshot=self.model["snapshot"],
                data_scope=self.model["data_scope"],
                generated_at="2026-08-26T12:00:00Z",
                output_path=str(output),
            )
            svg = output.read_text(encoding="utf-8")

        semantic_markers = ("Repositories", "Stargazers", "Releases", "Languages")
        # One shared, visibility-aware extractor decides what the reader can read.
        _root, text_lines = _positioned_text_lines(svg)
        semantic_lines = [
            line
            for line in text_lines
            if any(marker in line.text for marker in semantic_markers)
        ]
        self.assertTrue(semantic_lines, "the generated footer must remain visible")
        self.assertEqual(
            [],
            [line.text for line in semantic_lines if not line.visible],
            "footer claims may not be satisfied by hidden text",
        )
        self.assertEqual(
            [],
            [line.text for line in semantic_lines if line.squeezed],
            "footer claims may not be squeezed with textLength/lengthAdjust",
        )
        footer = " ".join(
            line.text
            for line in semantic_lines
            if line.visible and not line.transformed
        )

        totals = (
            f"{fmt_int(self.model['snapshot']['total_repos'])} Repositories",
            f"{fmt_int(self.model['snapshot']['total_stars'])} Stargazers",
            f"{fmt_int(self.model['snapshot']['releases'])} Releases",
        )
        for claim in totals:
            self.assertEqual(
                1,
                _exact_total_count(footer, claim),
                f"the wrapped footer must conserve {claim!r} exactly once as a complete"
                " numeric total, never as a substring of a larger number",
            )
        self.assertNotIn(self.model["data_scope"]["repos_included"], footer)
        readable_lines = [
            line.text
            for line in semantic_lines
            if line.visible and not line.transformed
        ]
        public_scope_line = "Repositories/Stargazers/Releases: public-owned-nonfork"
        self.assertEqual(
            1,
            readable_lines.count(public_scope_line),
            "the public totals scope must read back as one complete line, so a broadened"
            " variant cannot satisfy it",
        )
        language_scope_line = (
            f"Languages: {self.model['data_scope']['metric_scopes']['languages_count']}"
        )
        self.assertEqual(
            1,
            readable_lines.count(language_scope_line),
            "the all-owned language scope must read back as one complete line",
        )
        self.assertTrue(
            _scope_names_profile_exclusion(
                self.model["data_scope"]["metric_scopes"]["languages_count"]
            ),
            "the language scope must name exclusion of the profile repository",
        )
        self.assertEqual(
            [],
            _footer_layout_errors(
                svg,
                totals,
                expected_scope_lines=(public_scope_line, language_scope_line),
            ),
            "the shared footer oracle must accept the rendered footer's wrapping,"
            " geometry, visibility, and conserved totals",
        )

    def test_now_reflects_recent_pushes(self):
        now_titles = [i["title"] for i in self.model["focus"]["now"]]
        self.assertIn("pub1", now_titles)
        self.assertIn("secret-api", now_titles)
        self.assertNotIn("jguida941", now_titles)

    def test_engineering_block_present(self):
        eng = self.model["engineering"]
        self.assertIn("weekly_cadence", eng)
        self.assertGreaterEqual(eng["automation_workflows"], 2)
        self.assertEqual(eng["private_repos_total"], 1)

    def test_private_repository_contributes_to_all_owned_aggregates(self):
        engineering = self.model["engineering"]
        public_engineering = self.public_only_model["engineering"]
        metric_scopes = self.model["data_scope"].get("metric_scopes", {})
        all_owned_scope = metric_scopes.get("active_repos_7d")

        observed = {
            "active_repositories_7d_delta": (
                self.model["scorecard"]["active_repos_7d"]
                - self.public_only_model["scorecard"]["active_repos_7d"]
            ),
            "freshest_push_days": (
                engineering["days_since_last_push"],
                public_engineering["days_since_last_push"],
            ),
            "automation_repository_delta": (
                engineering["automation_repos"]
                - public_engineering["automation_repos"]
            ),
            "automation_file_delta": (
                engineering["automation_workflows"]
                - public_engineering["automation_workflows"]
            ),
            "private_totals": (
                engineering["private_repos_total"],
                engineering["recent_private_count"],
            ),
            "metric_scopes": {
                metric: metric_scopes.get(metric)
                for metric in (
                    "active_repos_7d",
                    "days_since_last_push",
                    "automation_repos",
                    "automation_workflows",
                )
            },
        }
        expected = {
            "active_repositories_7d_delta": 1,
            "freshest_push_days": (0.0, 2.0),
            "automation_repository_delta": 1,
            "automation_file_delta": 5,
            "private_totals": (1, 1),
            "metric_scopes": {
                "active_repos_7d": all_owned_scope,
                "days_since_last_push": all_owned_scope,
                "automation_repos": all_owned_scope,
                "automation_workflows": all_owned_scope,
            },
        }

        self.assertEqual(expected, observed)
        self.assertTrue(
            _scope_names_profile_exclusion(all_owned_scope),
            "shared aggregate scope must name exclusion of the profile repository",
        )

    def test_complete_private_evidence_marks_all_owned_aggregates_exact(self):
        metric_scopes = self.model["data_scope"].get("metric_scopes", {})
        exact_scopes = {
            metric_scopes.get(metric) for metric in _PRIVATE_AGGREGATE_METRICS
        }
        observed = {
            "quality": self.model["data_quality"].get("private_aggregate_status"),
            "metric_statuses": {
                metric: self.model["data_quality"]["metric_statuses"].get(metric)
                for metric in _PRIVATE_AGGREGATE_METRICS
            },
        }
        expected = {
            "quality": "exact",
            "metric_statuses": {
                metric: "exact"
                for metric in _PRIVATE_AGGREGATE_METRICS
            },
        }

        self.assertEqual(expected, observed)
        self.assertEqual(1, len(exact_scopes))
        self.assertTrue(
            _scope_names_profile_exclusion(next(iter(exact_scopes))),
            "exact scopes must name the self-excluded population",
        )

    def test_truncated_private_evidence_is_partial_and_never_exactly_all_owned(self):
        metric_scopes = self.truncated_private_model["data_scope"].get(
            "metric_scopes", {}
        )
        exact_scope = self.model["data_scope"]["metric_scopes"]["active_repos_7d"]
        observed = {
            "quality": self.truncated_private_model["data_quality"].get(
                "private_aggregate_status"
            ),
            "metrics_still_labeled_exact_all_owned": [
                metric
                for metric in _PRIVATE_AGGREGATE_METRICS
                if metric_scopes.get(metric) == exact_scope
            ],
        }

        self.assertEqual(
            {
                "quality": "partial",
                "metrics_still_labeled_exact_all_owned": [],
            },
            observed,
        )

    def test_unavailable_private_evidence_is_unavailable_and_never_exactly_all_owned(self):
        metric_scopes = self.unavailable_private_model["data_scope"].get(
            "metric_scopes", {}
        )
        exact_scope = self.model["data_scope"]["metric_scopes"]["active_repos_7d"]
        observed = {
            "quality": self.unavailable_private_model["data_quality"].get(
                "private_aggregate_status"
            ),
            "metrics_still_labeled_exact_all_owned": [
                metric
                for metric in _PRIVATE_AGGREGATE_METRICS
                if metric_scopes.get(metric) == exact_scope
            ],
        }

        self.assertEqual(
            {
                "quality": "unavailable",
                "metrics_still_labeled_exact_all_owned": [],
            },
            observed,
        )

    def test_complete_private_language_bytes_change_only_all_owned_composition(self):
        complete_languages = self._language_totals(self.model)
        public_languages = self._language_totals(self.public_only_model)
        observed = {
            "complete_private_rust_bytes": complete_languages.get("Rust"),
            "public_only_rust_bytes": public_languages.get("Rust"),
            "complete_public_language_bytes": {
                name: complete_languages.get(name)
                for name in ("Python", "Java")
            },
            "public_only_language_bytes": {
                name: public_languages.get(name)
                for name in ("Python", "Java")
            },
        }
        expected = {
            "complete_private_rust_bytes": 1000,
            "public_only_rust_bytes": None,
            "complete_public_language_bytes": {"Python": 1000, "Java": 1000},
            "public_only_language_bytes": {"Python": 1000, "Java": 1000},
        }

        self.assertEqual(expected, observed)

    def test_exact_language_scope_uses_the_current_repository_population(self):
        public_repository = self._synthetic_repo(
            "current-public-language",
            "Improve the public language collector",
            minutes_ago=20,
            language="Python",
        )
        private_repository = self._synthetic_repo(
            "current-private-language",
            "Improve the private language collector",
            minutes_ago=10,
            private=True,
            language="Rust",
        )
        collected = self._collected_with_repositories(
            [public_repository],
            [private_repository],
        )
        stale_aggregate = replace(
            collected,
            language_bytes={"StaleLanguage": 9999},
        )

        model = compute_profile_model(
            stale_aggregate,
            logger=_noop,
            allow_network_calls=False,
        )

        self.assertEqual(
            {"Python": 1000, "Rust": 1000},
            self._language_totals(model),
        )
        self.assertEqual(
            "exact",
            model["data_quality"]["metric_statuses"]["top_languages"],
        )
        self.assertTrue(
            _scope_names_profile_exclusion(
                model["data_scope"]["metric_scopes"]["top_languages"]
            ),
            "the exact language scope must name exclusion of the profile repository",
        )

    def test_activity_feed_combines_public_events_with_known_private_pushes(self):
        public_repository = self._synthetic_repo(
            "public-event-repo",
            "Improve the public event feed",
            minutes_ago=30,
        )
        private_repository = self._synthetic_repo(
            "private-push-repo",
            "Improve private repository reporting",
            minutes_ago=10,
            private=True,
            language="Rust",
        )
        event_time = _iso(datetime.now(timezone.utc) - timedelta(minutes=20))
        public_event = {
            "type": "PushEvent",
            "actor": {"login": "jguida941"},
            "repo": {"name": "jguida941/public-event-repo"},
            "created_at": event_time,
            "payload": {"commits": [{"message": "Improve the public event feed"}]},
        }
        collected = replace(
            self._collected_with_repositories(
                [public_repository],
                [private_repository],
            ),
            events=[public_event],
        )
        model = compute_profile_model(
            collected,
            logger=_noop,
            allow_network_calls=False,
        )
        push_items = [
            item for item in model["activity_feed"]
            if item.get("state") == "PUSH"
        ]
        public_items = [
            item for item in push_items
            if item.get("repo") == "jguida941/public-event-repo"
        ]
        private_items = [
            item for item in push_items
            if item.get("repo") == "jguida941/private-push-repo"
        ]

        with self.subTest(arm="event observation remains preferred"):
            self.assertEqual(1, len(public_items))
            self.assertEqual(
                "Improve the public event feed",
                public_items[0].get("title"),
            )
            self.assertEqual(event_time, public_items[0].get("created_at"))

        with self.subTest(arm="private repository push remains visible"):
            self.assertEqual(1, len(private_items))

        private_item = private_items[0] if private_items else {}
        with self.subTest(arm="private push metadata"):
            self.assertEqual(
                {
                    "title": "Improve private repository reporting",
                    "url": "https://github.com/jguida941/private-push-repo",
                    "created_at": private_repository["pushed_at"],
                    "is_private": True,
                },
                {
                    "title": private_item.get("title"),
                    "url": private_item.get("url"),
                    "created_at": private_item.get("created_at"),
                    "is_private": private_item.get("is_private"),
                },
            )
            self.assertTrue(
                all(
                    key not in private_item
                    for key in ("actor", "payload", "commits", "commit_body")
                ),
                "repository metadata fallback must not invent an event payload",
            )

        public_source = " ".join(
            str(public_items[0].get(key, ""))
            for key in ("source", "source_type", "observation_source")
        ).casefold()
        private_source = " ".join(
            str(private_item.get(key, ""))
            for key in ("source", "source_type", "observation_source")
        ).casefold()
        with self.subTest(arm="observation sources"):
            self.assertIn("event", public_source)
            self.assertTrue(
                "repo" in private_source or "push" in private_source,
                "the private item must identify its repository-push source",
            )

    def test_private_only_push_retains_its_ordinary_headline(self):
        headline = "Preserve ordinary private repository metadata"
        private_repository = self._synthetic_repo(
            "private-metadata-only",
            headline,
            minutes_ago=10,
            private=True,
            language="Rust",
        )
        collected = self._collected_with_repositories([], [private_repository])
        model = compute_profile_model(
            collected,
            logger=_noop,
            allow_network_calls=False,
        )
        pushes = [
            item
            for item in model["activity_feed"]
            if item.get("state") == "PUSH"
            and item.get("repo") == "jguida941/private-metadata-only"
        ]

        self.assertEqual(1, len(pushes))
        self.assertEqual(
            {
                "title": headline,
                "url": "https://github.com/jguida941/private-metadata-only",
                "is_private": True,
                "observation_source": "repository push metadata",
            },
            {
                key: pushes[0].get(key)
                for key in (
                    "title",
                    "url",
                    "is_private",
                    "observation_source",
                )
            },
        )

    def test_non_push_and_empty_push_activity_titles_remain_stable(self):
        from scripts.pipeline.compute_metrics import (
            _build_activity_feed,
            _build_recent_activity,
        )

        non_push = _build_activity_feed(
            [],
            [],
            [
                {
                    "repo": "jguida941/activity-controls",
                    "url": "https://github.com/jguida941/activity-controls",
                    "activity": "issue comment",
                    "time_ago": "just now",
                    "created_at": "2026-08-26T15:00:00Z",
                    "is_private": False,
                    "observation_source": "event",
                }
            ],
            [],
            [],
            "jguida941",
        )
        empty_headline_repository = {
            "name": "empty-headline",
            "html_url": "https://github.com/jguida941/empty-headline",
            "pushed_at": "2026-08-26T15:00:00Z",
            "last_commit_msg": "",
            "is_private": False,
        }
        contributions, releases, prs, *_rest = _build_recent_activity(
            [],
            [empty_headline_repository],
            [],
            "jguida941",
        )
        empty_push = _build_activity_feed(
            releases,
            prs,
            contributions,
            [],
            [empty_headline_repository],
            "jguida941",
        )

        self.assertEqual("issue comment", non_push[0].get("title"))
        self.assertEqual("push", empty_push[0].get("title"))

    def test_recent_created_uses_public_and_private_repository_rows(self):
        now = datetime.now(timezone.utc)
        public_newer = self._synthetic_repo(
            "public-newer",
            "Create the public service",
            minutes_ago=30,
        )
        public_newer["created_at"] = _iso(now - timedelta(days=2))
        public_older = self._synthetic_repo(
            "public-older",
            "Create the public library",
            minutes_ago=40,
        )
        public_older["created_at"] = _iso(now - timedelta(days=4))
        private_newest = self._synthetic_repo(
            "private-newest",
            "Create the private service",
            minutes_ago=10,
            private=True,
            language="Rust",
        )
        private_newest["created_at"] = _iso(now - timedelta(days=1))
        private_middle = self._synthetic_repo(
            "private-middle",
            "Create the private library",
            minutes_ago=20,
            private=True,
            language="Go",
        )
        private_middle["created_at"] = _iso(now - timedelta(days=3))
        profile_repository = self._synthetic_repo(
            "jguida941",
            "Refresh the profile",
            minutes_ago=1,
        )
        profile_repository["created_at"] = _iso(now)

        model = compute_profile_model(
            self._collected_with_repositories(
                [profile_repository, public_newer, public_older],
                [private_newest, private_middle],
            ),
            logger=_noop,
            allow_network_calls=False,
        )
        rows = model["recent_created"]
        names = [row.get("name") for row in rows]
        public_names = [name for name in names if str(name).startswith("public-")]

        with self.subTest(arm="shared descending order"):
            self.assertEqual(
                ["private-newest", "public-newer", "private-middle", "public-older"],
                names,
            )
        with self.subTest(arm="public ordering"):
            self.assertEqual(["public-newer", "public-older"], public_names)
        with self.subTest(arm="profile repository exclusion"):
            self.assertNotIn("jguida941", names)
            self.assertLessEqual(len(rows), 10)
        private_rows = [row for row in rows if row.get("name") == "private-newest"]
        with self.subTest(arm="private visibility marker"):
            self.assertEqual(1, len(private_rows))
            private_row = private_rows[0] if private_rows else {}
            self.assertTrue(
                private_row.get("is_private") is True
                or private_row.get("private") is True
            )

    def test_partial_private_inventory_keeps_observed_rows_and_qualifies_aggregates(self):
        public_repository = self._synthetic_repo(
            "observed-public",
            "Improve public reporting",
            minutes_ago=20,
        )
        private_repository = self._synthetic_repo(
            "observed-private",
            "Improve private reporting",
            minutes_ago=10,
            private=True,
            language="Rust",
        )
        collected = self._collected_with_repositories(
            [public_repository],
            [private_repository],
        )
        partial_counts = dict(collected.repo_counts)
        partial_counts["private_owned"] = 2
        partial_counts["private_owned_nonfork"] = 2
        partial_model = compute_profile_model(
            replace(collected, repo_counts=partial_counts),
            logger=_noop,
            allow_network_calls=False,
        )
        exact_model = compute_profile_model(
            collected,
            logger=_noop,
            allow_network_calls=False,
        )

        observed = {
            "overview_private_rows": sum(
                row.get("name") == "observed-private"
                for row in partial_model["repo_overview_rows"]
            ),
            "recent_private_rows": sum(
                row.get("name") == "observed-private"
                for row in partial_model["recent_repos"]
            ),
            "focus_private_rows": sum(
                row.get("title") == "observed-private"
                for row in partial_model["focus"]["now"]
            ),
            "active_repositories": partial_model["scorecard"]["active_repos_7d"],
            "automated_repositories": partial_model["engineering"]["automation_repos"],
            "workflow_files": partial_model["engineering"]["automation_workflows"],
        }
        with self.subTest(arm="observed values remain available"):
            self.assertEqual(
                {
                    "overview_private_rows": 1,
                    "recent_private_rows": 1,
                    "focus_private_rows": 1,
                    "active_repositories": 2,
                    "automated_repositories": 2,
                    "workflow_files": 2,
                },
                observed,
            )

        with self.subTest(arm="partial family qualification"):
            self.assertEqual(
                "partial",
                partial_model["data_quality"]["private_aggregate_status"],
            )
            for metric in (
                "active_repos_7d",
                "days_since_last_push",
                "automation_repos",
                "automation_workflows",
            ):
                self.assertEqual(
                    "partial",
                    partial_model["data_quality"]["metric_statuses"][metric],
                )
                self.assertIn(
                    "partial",
                    partial_model["data_scope"]["metric_scopes"][metric].casefold(),
                )

        incomplete_private = dict(private_repository)
        incomplete_private.update(
            {
                "pushed_at": "",
                "has_ci_workflows": None,
                "workflow_file_count": None,
            }
        )
        incomplete_model = compute_profile_model(
            replace(
                self._collected_with_repositories(
                    [public_repository],
                    [incomplete_private],
                ),
                repo_counts=partial_counts,
            ),
            logger=_noop,
            allow_network_calls=False,
        )
        with self.subTest(arm="missing facts do not become measured values"):
            self.assertEqual(1, incomplete_model["scorecard"]["active_repos_7d"])
            self.assertEqual(1, incomplete_model["engineering"]["automation_repos"])
            self.assertEqual(1, incomplete_model["engineering"]["automation_workflows"])

        with self.subTest(arm="complete inventory remains exact"):
            self.assertEqual(
                {
                    "private_quality": "exact",
                    "active_repositories": 2,
                    "automated_repositories": 2,
                    "workflow_files": 2,
                },
                {
                    "private_quality": exact_model["data_quality"][
                        "private_aggregate_status"
                    ],
                    "active_repositories": exact_model["scorecard"][
                        "active_repos_7d"
                    ],
                    "automated_repositories": exact_model["engineering"][
                        "automation_repos"
                    ],
                    "workflow_files": exact_model["engineering"][
                        "automation_workflows"
                    ],
                },
            )

    def test_partial_private_language_keeps_observed_bytes(self):
        public_repository = self._synthetic_repo(
            "python-service",
            "Improve Python reporting",
            minutes_ago=20,
            language="Python",
        )
        private_repository = self._synthetic_repo(
            "rust-service",
            "Improve Rust reporting",
            minutes_ago=10,
            private=True,
            language="Rust",
        )
        collected = self._collected_with_repositories(
            [public_repository],
            [private_repository],
        )
        partial_counts = dict(collected.repo_counts)
        partial_counts["private_owned"] = 2
        partial_counts["private_owned_nonfork"] = 2
        partial_model = compute_profile_model(
            replace(collected, repo_counts=partial_counts),
            logger=_noop,
            allow_network_calls=False,
        )

        with self.subTest(arm="observed language bytes"):
            self.assertEqual(
                {"Python": 1000, "Rust": 1000},
                self._language_totals(partial_model),
            )
        with self.subTest(arm="observed private row"):
            self.assertEqual(
                1,
                sum(
                    row.get("name") == "rust-service"
                    for row in partial_model["recent_repos"]
                ),
            )
        with self.subTest(arm="language qualification"):
            self.assertEqual(
                "partial",
                partial_model["data_quality"]["metric_statuses"]["top_languages"],
            )
            self.assertIn(
                "partial",
                partial_model["data_scope"]["metric_scopes"]["top_languages"].casefold(),
            )

        exact_model = compute_profile_model(
            replace(collected, language_bytes={"StaleLanguage": 9999}),
            logger=_noop,
            allow_network_calls=False,
        )
        with self.subTest(arm="exact current repository values"):
            self.assertEqual(
                {"Python": 1000, "Rust": 1000},
                self._language_totals(exact_model),
            )

        incomplete_private = dict(private_repository)
        incomplete_private["language_bytes_complete"] = False
        incomplete_model = compute_profile_model(
            self._collected_with_repositories(
                [public_repository],
                [incomplete_private],
            ),
            logger=_noop,
            allow_network_calls=False,
        )
        with self.subTest(arm="incomplete language connection does not invent bytes"):
            self.assertNotIn("Rust", self._language_totals(incomplete_model))
            self.assertEqual(
                "partial",
                incomplete_model["data_quality"]["metric_statuses"]["top_languages"],
            )

    def test_population_descriptions_match_observed_repository_evidence(self):
        public_repository = self._synthetic_repo(
            "population-public",
            "Improve population reporting",
            minutes_ago=20,
        )
        private_repository = self._synthetic_repo(
            "population-private",
            "Improve private population reporting",
            minutes_ago=10,
            private=True,
            language="Rust",
        )
        exact_mixed_collected = self._collected_with_repositories(
            [public_repository],
            [private_repository],
        )
        public_only_collected = self._collected_with_repositories(
            [public_repository],
            [],
        )
        unavailable_private_counts = dict(public_only_collected.repo_counts)
        unavailable_private_counts["private_owned"] = None
        unavailable_private_counts["private_owned_nonfork"] = None
        partial_private_counts = dict(exact_mixed_collected.repo_counts)
        partial_private_counts["private_owned"] = 2
        partial_private_counts["private_owned_nonfork"] = 2
        no_rows_collected = self._collected_with_repositories([], [])
        unavailable_counts = dict(no_rows_collected.repo_counts)
        unavailable_counts["public_owned_nonfork"] = None
        unavailable_counts["private_owned"] = None
        unavailable_counts["private_owned_nonfork"] = None

        cases = {
            "exact public and private": (
                exact_mixed_collected,
                "exact",
                ("public", "private", "exact"),
            ),
            "public observed and private unavailable": (
                replace(public_only_collected, repo_counts=unavailable_private_counts),
                "partial",
                ("public", "private", "unavailable"),
            ),
            "public and partial private observed": (
                replace(exact_mixed_collected, repo_counts=partial_private_counts),
                "partial",
                ("public", "private", "partial"),
            ),
            "no usable facts": (
                replace(no_rows_collected, repo_counts=unavailable_counts),
                "unavailable",
                ("unavailable",),
            ),
            "confirmed empty": (
                no_rows_collected,
                "exact",
                ("empty", "exact"),
            ),
        }

        for name, (collected, expected_status, scope_words) in cases.items():
            model = compute_profile_model(
                collected,
                logger=_noop,
                allow_network_calls=False,
            )
            with self.subTest(case=name, assertion="family statuses"):
                for metric in (
                    "active_repos_7d",
                    "automation_repos",
                    "top_languages",
                ):
                    self.assertEqual(
                        expected_status,
                        model["data_quality"]["metric_statuses"][metric],
                    )
            description = model["data_scope"]["repos_included"].casefold()
            with self.subTest(case=name, assertion="population description"):
                for word in scope_words:
                    self.assertIn(word, description)
            with self.subTest(case=name, assertion="metric scope"):
                scope = model["data_scope"]["metric_scopes"]["top_languages"]
                if expected_status == "exact":
                    self.assertTrue(_scope_names_profile_exclusion(scope))
                else:
                    self.assertIn(expected_status, scope.casefold())

        public_only_model = compute_profile_model(
            replace(public_only_collected, repo_counts=unavailable_private_counts),
            logger=_noop,
            allow_network_calls=False,
        )
        with self.subTest(case="known public values remain available"):
            self.assertEqual(1, public_only_model["scorecard"]["active_repos_7d"])
            self.assertEqual(1, public_only_model["engineering"]["automation_repos"])
            self.assertEqual({"Python": 1000}, self._language_totals(public_only_model))

    def test_private_only_population_distinguishes_exact_empty_public_inventory(self):
        private_repository = self._synthetic_repo(
            "private-only-service",
            "Improve private-only reporting",
            minutes_ago=10,
            private=True,
            language="Rust",
        )
        exact_private_only = self._collected_with_repositories(
            [],
            [private_repository],
        )
        unavailable_public_counts = dict(exact_private_only.repo_counts)
        unavailable_public_counts["public_owned_total"] = None
        unavailable_public_counts["public_owned_nonfork"] = None
        cases = {
            "public inventory is exact empty": (
                exact_private_only,
                ("private", "public", "exact", "empty"),
                ("partial", "unavailable"),
                "exact",
            ),
            "public inventory is unavailable": (
                replace(
                    exact_private_only,
                    repo_counts=unavailable_public_counts,
                ),
                ("private", "public", "unavailable"),
                ("exact empty", "partial"),
                "partial",
            ),
        }

        for name, (collected, required, forbidden, expected_family_status) in cases.items():
            model = compute_profile_model(
                collected,
                logger=_noop,
                allow_network_calls=False,
            )
            description = model["data_scope"]["repos_included"].casefold()
            with self.subTest(case=name, assertion="population description"):
                for word in required:
                    self.assertIn(word, description)
                for phrase in forbidden:
                    self.assertNotIn(phrase, description)
            with self.subTest(case=name, assertion="family status remains independent"):
                for metric in (
                    "active_repos_7d",
                    "automation_repos",
                    "top_languages",
                ):
                    self.assertEqual(
                        expected_family_status,
                        model["data_quality"]["metric_statuses"][metric],
                    )

    def test_profile_repository_is_excluded_from_all_shared_metric_families(self):
        profile_repository = self._synthetic_repo(
            "jguida941",
            "Refresh profile artifacts",
            minutes_ago=1,
            language="Haskell",
        )
        profile_repository["language_bytes"] = {"Haskell": 9000}
        external_haskell = self._synthetic_repo(
            "haskell-service",
            "Improve Haskell service",
            minutes_ago=20,
            language="Haskell",
        )
        external_haskell["language_bytes"] = {"Haskell": 1000}
        public_python = self._synthetic_repo(
            "python-service",
            "Improve Python service",
            minutes_ago=30,
            language="Python",
        )
        private_rust = self._synthetic_repo(
            "rust-service",
            "Improve Rust service",
            minutes_ago=10,
            private=True,
            language="Rust",
        )
        model = compute_profile_model(
            self._collected_with_repositories(
                [profile_repository, external_haskell, public_python],
                [private_rust],
            ),
            logger=_noop,
            allow_network_calls=False,
        )

        with self.subTest(arm="language population"):
            self.assertEqual(
                {"Haskell": 1000, "Python": 1000, "Rust": 1000},
                self._language_totals(model),
            )
        with self.subTest(arm="row and activity populations"):
            published_names = {
                row.get("name") for row in model["repo_overview_rows"]
            } | {
                row.get("name") for row in model["recent_repos"]
            } | {
                str(item.get("repo", "")).split("/")[-1]
                for item in model["activity_feed"]
            }
            self.assertNotIn("jguida941", published_names)
            self.assertEqual(3, model["scorecard"]["active_repos_7d"])
            self.assertEqual(3, model["engineering"]["automation_repos"])

        scope_ids = {
            model["data_scope"]["metric_scopes"][metric]
            for metric in (
                "active_repos_7d",
                "automation_repos",
                "top_languages",
            )
        }
        with self.subTest(arm="one named population"):
            self.assertEqual(1, len(scope_ids))
            self.assertTrue(
                _scope_names_profile_exclusion(next(iter(scope_ids))),
                "the shared scope must name profile-repository exclusion",
            )

        nonself_model = compute_profile_model(
            self._collected_with_repositories(
                [external_haskell, public_python],
                [private_rust],
            ),
            logger=_noop,
            allow_network_calls=False,
        )
        with self.subTest(arm="ordinary repository language remains"):
            self.assertEqual(
                1000,
                self._language_totals(nonself_model).get("Haskell"),
            )

    def test_public_metrics_stay_public_while_overview_includes_private_metadata(self):
        for key in (
            "total_repos",
            "public_forks",
            "public_scope_commits",
            "total_stars",
            "prs_merged",
            "releases",
        ):
            with self.subTest(metric=key):
                self.assertEqual(
                    self.public_only_model["snapshot"][key],
                    self.model["snapshot"][key],
                )

        self.assertEqual(
            self.public_only_model["recent_releases"],
            self.model["recent_releases"],
        )
        self.assertEqual(
            self.public_only_model["recent_pull_requests"],
            self.model["recent_pull_requests"],
        )

        overview_by_name = {
            row["name"]: row for row in self.model["repo_overview_rows"]
        }
        self.assertEqual({"pub1", "pub2", "secret-api"}, set(overview_by_name))
        self.assertEqual(
            {
                "name": "secret-api",
                "url": "https://github.com/jguida941/secret-api",
                "language": "Rust",
                "is_private": True,
            },
            {
                key: overview_by_name["secret-api"].get(key)
                for key in ("name", "url", "language", "is_private")
            },
        )

        dashboard_names = {
            row["name"]
            for row in self.model["dashboard_data"]["repo_language_matrix"]
        }
        self.assertIn("secret-api", dashboard_names)

    def test_partial_event_metadata_merges_with_public_and_private_pushes(self):
        now = datetime.now(timezone.utc)
        public_push = _iso(now - timedelta(minutes=20))
        private_push = _iso(now - timedelta(minutes=10))
        public_repository = self._synthetic_repo(
            "partial-event-public",
            "Publish provider metadata",
            minutes_ago=20,
        )
        public_repository.update(
            {
                "pushed_at": public_push,
                "latest_commit_message": "Publish provider metadata",
            }
        )
        private_repository = self._synthetic_repo(
            "partial-event-private",
            "Publish private repository metadata",
            minutes_ago=10,
            private=True,
            language="Rust",
        )
        private_repository.update(
            {
                "pushed_at": private_push,
                "latest_commit_message": "Publish private repository metadata",
            }
        )
        canonical_event = {
            "event_id": "event-partial-public",
            "event_type": "PushEvent",
            "repo_full_name": "jguida941/partial-event-public",
            "repo_url": "https://github.com/jguida941/partial-event-public",
            "actor_login": "jguida941",
            "occurred_at": public_push,
            "is_private": False,
            "source_id": "github_rest_public_events",
            "evidence_status": "partial",
            "commit_headlines": ("Publish provider metadata",),
        }
        event_observation = _provider_observation(
            metric_id="recent_public_events",
            source_metric_id="github_public_event_metadata_rows",
            value=(canonical_event,),
            status="partial",
            complete=False,
            population_id="public-user-events-feed",
            population_signature="jguida941:100:3:300",
            window_start=None,
            window_end=None,
            observed_at=_iso(now - timedelta(minutes=5)),
            source_id="github_rest_public_events",
            source_mode="live",
            completion_reason="page_error",
        )
        collected = self._collected_with_repositories(
            [public_repository],
            [private_repository],
        )
        collected = replace(collected, events=[canonical_event])
        collected = _with_metric_observations(
            collected,
            {"recent_public_events": event_observation},
        )

        model = compute_profile_model(
            collected,
            logger=_noop,
            allow_network_calls=False,
        )
        push_items = [
            item for item in model["activity_feed"] if item.get("state") == "PUSH"
        ]
        public_items = [
            item
            for item in push_items
            if item.get("repo") == "jguida941/partial-event-public"
        ]
        private_items = [
            item
            for item in push_items
            if item.get("repo") == "jguida941/partial-event-private"
        ]

        with self.subTest(assertion="duplicate public push is event-preferred"):
            self.assertEqual(1, len(public_items))
            public_source = " ".join(
                str(public_items[0].get(key, ""))
                for key in ("source", "source_id", "observation_source")
            ).casefold() if public_items else ""
            self.assertIn("event", public_source)
            self.assertEqual(public_push, public_items[0].get("created_at") if public_items else None)
        with self.subTest(assertion="distinct private push survives"):
            self.assertEqual(1, len(private_items))
            private_item = private_items[0] if private_items else {}
            self.assertEqual("Publish private repository metadata", private_item.get("title"))
            self.assertEqual(private_push, private_item.get("created_at"))
            self.assertIs(private_item.get("is_private"), True)
        with self.subTest(assertion="partial quality remains attached"):
            self.assertEqual("partial", model["data_quality"].get("events_status"))
            provenance = model["data_quality"].get("metric_provenance", {}).get(
                "recent_public_events",
                {},
            )
            self.assertEqual("partial", provenance.get("status"))
            self.assertNotIn("value", provenance)

    def test_partial_push_rows_deduplicate_only_on_normalized_observation_identity(self):
        now = datetime.now(timezone.utc)
        first_time = _iso(now - timedelta(minutes=40))
        second_time = _iso(now - timedelta(minutes=30))
        duplicate_time = _iso(now - timedelta(minutes=20))
        repository = self._synthetic_repo(
            "ACTIVITY-MATRIX",
            "Ship gamma\nprivate implementation detail",
            minutes_ago=20,
        )
        repository.update(
            {
                "pushed_at": duplicate_time,
                "latest_commit_message": "Ship gamma\nprivate implementation detail",
            }
        )

        event_specs = (
            ("event-alpha-first", "jguida941/activity-matrix", first_time, "Ship alpha"),
            ("event-beta-first", "jguida941/activity-matrix", first_time, "Ship beta"),
            ("event-alpha-second", "jguida941/activity-matrix", second_time, "Ship alpha"),
            ("event-gamma", "jguida941/activity-matrix", duplicate_time, "Ship gamma"),
            ("event-gamma-case", "jguida941/Activity-Matrix", duplicate_time, "Ship gamma"),
        )
        event_rows = tuple(
            {
                "event_id": event_id,
                "event_type": "PushEvent",
                "repo_full_name": repo_full_name,
                "repo_url": f"https://github.com/{repo_full_name}",
                "actor_login": "jguida941",
                "occurred_at": occurred_at,
                "is_private": False,
                "source_id": "github_rest_public_events",
                "evidence_status": "partial",
                "commit_headlines": (headline,),
            }
            for event_id, repo_full_name, occurred_at, headline in event_specs
        )
        event_observation = _provider_observation(
            metric_id="recent_public_events",
            source_metric_id="github_public_event_metadata_rows",
            value=event_rows,
            status="partial",
            complete=False,
            population_id="public-user-events-feed",
            population_signature="jguida941:100:3:300",
            window_start=None,
            window_end=None,
            observed_at=_iso(now - timedelta(minutes=10)),
            source_id="github_rest_public_events",
            source_mode="live",
            completion_reason="page_error",
        )
        collected = self._collected_with_repositories([repository], [])
        collected = replace(
            collected,
            events=list(event_rows),
            latest_push_message_by_repo={
                "jguida941/ACTIVITY-MATRIX": "Ship gamma\nprivate implementation detail"
            },
        )
        collected = _with_metric_observations(
            collected,
            {"recent_public_events": event_observation},
        )

        model = compute_profile_model(
            collected,
            logger=_noop,
            allow_network_calls=False,
        )
        pushes = [
            item
            for item in model["activity_feed"]
            if item.get("state") == "PUSH"
            and str(item.get("repo", "")).casefold()
            == "jguida941/activity-matrix"
        ]

        with self.subTest(assertion="headline and timestamp distinctions survive"):
            self.assertEqual(4, len(pushes))
            self.assertEqual(
                sorted((first_time, first_time, second_time, duplicate_time)),
                sorted(item.get("created_at") for item in pushes),
            )
            self.assertCountEqual(
                ("Ship alpha", "Ship beta", "Ship alpha", "Ship gamma"),
                [item.get("title") for item in pushes],
            )
        duplicate_rows = [
            item for item in pushes if item.get("created_at") == duplicate_time
        ]
        with self.subTest(assertion="normalized exact duplicate prefers event evidence"):
            self.assertEqual(1, len(duplicate_rows))
            source = " ".join(
                str(duplicate_rows[0].get(key, ""))
                for key in ("source", "source_id", "observation_source")
            ).casefold() if duplicate_rows else ""
            self.assertIn("event", source)
        with self.subTest(assertion="partial status remains explicit"):
            self.assertEqual("partial", model["data_quality"].get("events_status"))

    def test_nonexact_aggregates_round_trip_without_entering_exact_scalars(self):
        observed_at = "2026-08-26T15:00:00Z"
        window_start = "2025-08-27T00:00:00Z"
        window_end = "2026-08-26T15:00:00Z"
        observations = {
            "public_scope_commits": _provider_observation(
                metric_id="public_scope_commits",
                source_metric_id="github_total_commit_contributions",
                value=999,
                status="fallback",
                complete=True,
                population_id="github-user-contributions-visible-to-provider",
                population_signature=None,
                window_start=None,
                window_end=None,
                observed_at=observed_at,
                source_id="github_graphql_commit_contributions",
                source_mode="fallback",
                completion_reason="different_metric_fallback",
            ),
            "prs_merged": _provider_observation(
                metric_id="prs_merged",
                source_metric_id="merged_prs_public_visible_population",
                value=23,
                status="fallback",
                complete=True,
                population_id="owned-public-repositories-visible-to-public-pr-search",
                population_signature=None,
                window_start=window_start,
                window_end=window_end,
                observed_at=observed_at,
                source_id="github_rest_merged_pr_search_public",
                source_mode="fallback",
                completion_reason="public_retry",
            ),
            "releases_30d": _provider_observation(
                metric_id="releases_30d",
                source_metric_id="public_release_events",
                value=2,
                status="fallback",
                complete=True,
                population_id="public-user-events-feed",
                population_signature=None,
                window_start="2026-07-28T00:00:00Z",
                window_end=window_end,
                observed_at=observed_at,
                source_id="github_rest_public_events",
                source_mode="fallback",
                completion_reason="different_metric_fallback",
            ),
        }
        collected = replace(
            self.collected,
            events=[],
            public_scope_commits=None,
            calendar=None,
            total_contributions=None,
        )
        collected = _with_metric_observations(collected, observations)
        model = compute_profile_model(
            collected,
            logger=_noop,
            allow_network_calls=False,
        )

        exact_fields = {
            "public_scope_commits": "public_scope_commits",
            "prs_merged": "prs_merged",
            "releases_30d": "releases",
        }
        for metric_id, snapshot_key in exact_fields.items():
            with self.subTest(metric=metric_id, assertion="exact scalar excluded"):
                self.assertIsNone(model["snapshot"].get(snapshot_key))

        carriers = model["data_quality"].get("non_exact_metrics", {})
        expected_values = {
            "public_scope_commits": 999,
            "prs_merged": 23,
            "releases_30d": 2,
        }
        for metric_id, expected_value in expected_values.items():
            carrier = carriers.get(metric_id, {})
            source = observations[metric_id]
            with self.subTest(metric=metric_id, assertion="fallback value retained"):
                self.assertEqual(expected_value, carrier.get("value"))
                for key in (
                    "metric_id",
                    "source_metric_id",
                    "status",
                    "population_id",
                    "population_signature",
                    "window_start",
                    "window_end",
                    "observed_at",
                    "source_id",
                    "source_mode",
                    "completion_reason",
                ):
                    self.assertEqual(source.get(key), carrier.get(key))

            provenance = model["data_quality"].get("metric_provenance", {}).get(
                metric_id,
                {},
            )
            with self.subTest(metric=metric_id, assertion="public provenance is value-less"):
                self.assertEqual("fallback", provenance.get("status"))
                self.assertNotIn("value", provenance)

            published_carrier = (
                model["dashboard_data"]
                .get("data_quality", {})
                .get("non_exact_metrics", {})
                .get(metric_id, {})
            )
            with self.subTest(metric=metric_id, assertion="dashboard JSON retains fallback"):
                self.assertEqual(expected_value, published_carrier.get("value"))

    def test_exact_aggregate_controls_have_no_nonexact_carrier(self):
        observed_at = "2026-08-26T15:00:00Z"
        window_start = "2025-08-27T00:00:00Z"
        window_end = "2026-08-26T15:00:00Z"
        observations = {
            "public_scope_commits": _provider_observation(
                metric_id="public_scope_commits",
                source_metric_id="owned_public_nonfork_authored_commits",
                value=500,
                status="ok",
                complete=True,
                population_id="owned-public-nonfork-repositories",
                population_signature="public-population-a",
                window_start=None,
                window_end=None,
                observed_at=observed_at,
                source_id="github_rest_repo_commits",
                source_mode="live",
                completion_reason="all_components_observed",
            ),
            "prs_merged": _provider_observation(
                metric_id="prs_merged",
                source_metric_id="merged_prs_primary_visible_population",
                value=42,
                status="ok",
                complete=True,
                population_id="owned-repositories-visible-to-primary-pr-search",
                population_signature=None,
                window_start=window_start,
                window_end=window_end,
                observed_at=observed_at,
                source_id="github_rest_merged_pr_search_primary",
                source_mode="live",
                completion_reason="all_components_observed",
            ),
            "releases_30d": _provider_observation(
                metric_id="releases_30d",
                source_metric_id="owned_public_nonfork_releases",
                value=7,
                status="ok",
                complete=True,
                population_id="owned-public-nonfork-repositories",
                population_signature="public-population-a",
                window_start="2026-07-28T00:00:00Z",
                window_end=window_end,
                observed_at=observed_at,
                source_id="github_rest_repo_releases",
                source_mode="live",
                completion_reason="all_components_observed",
            ),
        }
        collected = _with_metric_observations(self.collected, observations)
        with patch(
            "scripts.pipeline.compute_metrics.gh.get_merged_prs_last_n_days",
            return_value=42,
        ), patch(
            "scripts.pipeline.compute_metrics.gh.get_releases_last_n_days",
            return_value=7,
        ):
            model = compute_profile_model(
                collected,
                logger=_noop,
                allow_network_calls=True,
            )

        self.assertEqual(500, model["snapshot"]["public_scope_commits"])
        self.assertEqual(42, model["snapshot"]["prs_merged"])
        self.assertEqual(7, model["snapshot"]["releases"])
        carriers = model["data_quality"].get("non_exact_metrics", {})
        for metric_id in observations:
            with self.subTest(metric=metric_id):
                self.assertNotIn(metric_id, carriers)

    def test_absent_or_rejected_observations_cannot_mint_exact_values(self):
        observed_at = "2026-08-26T15:00:00Z"
        exact_commit_zero = _provider_observation(
            metric_id="public_scope_commits",
            source_metric_id="owned_public_nonfork_authored_commits",
            value=0,
            status="ok",
            complete=True,
            population_id="owned-public-nonfork-repositories",
            population_signature="none",
            window_start=None,
            window_end=None,
            observed_at=observed_at,
            source_id="github_rest_repo_commits",
            source_mode="live",
            completion_reason="empty_population",
        )
        exact_pr_zero = _provider_observation(
            metric_id="prs_merged",
            source_metric_id="merged_prs_primary_visible_population",
            value=0,
            status="ok",
            complete=True,
            population_id="owned-repositories-visible-to-primary-pr-search",
            population_signature=None,
            window_start="2025-08-27T00:00:00Z",
            window_end=observed_at,
            observed_at=observed_at,
            source_id="github_rest_merged_pr_search_primary",
            source_mode="live",
            completion_reason="all_components_observed",
        )
        rejected_commit = {
            **_provider_observation(
                metric_id="public_scope_commits",
                source_metric_id="github_total_commit_contributions",
                value=999,
                status="fallback",
                complete=True,
                population_id="github-user-contributions-visible-to-provider",
                population_signature=None,
                window_start=None,
                window_end=None,
                observed_at=observed_at,
                source_id="github_graphql_commit_contributions",
                source_mode="fallback",
                completion_reason="different_metric_fallback",
            ),
            "unexpected": "field",
        }
        rejected_pr = {
            **_provider_observation(
                metric_id="prs_merged",
                source_metric_id="merged_prs_public_visible_population",
                value=23,
                status="fallback",
                complete=True,
                population_id="owned-public-repositories-visible-to-public-pr-search",
                population_signature=None,
                window_start="2025-08-27T00:00:00Z",
                window_end=observed_at,
                observed_at=observed_at,
                source_id="github_rest_merged_pr_search_public",
                source_mode="fallback",
                completion_reason="public_retry",
            ),
            "unexpected": "field",
        }
        observation_states = {
            "absent": {},
            "non-mapping": ("not", "an", "observation mapping"),
            "wrong metric key": {"nearby_commit_total": exact_commit_zero},
            "validator rejected": {
                "public_scope_commits": rejected_commit,
                "prs_merged": rejected_pr,
            },
        }
        base = replace(
            self.collected,
            events=[],
            public_scope_commits=999,
            calendar=None,
            total_contributions=None,
        )

        for state, observations in observation_states.items():
            collected = _with_metric_observations(base, observations)
            model = compute_profile_model(
                collected,
                logger=_noop,
                allow_network_calls=False,
            )
            with self.subTest(state=state, metric="commits"):
                self.assertIsNone(model["snapshot"].get("public_scope_commits"))
                self.assertEqual(
                    "unavailable",
                    model["data_quality"].get("commits_status"),
                )
            with self.subTest(state=state, metric="pull requests"):
                self.assertIsNone(model["snapshot"].get("prs_merged"))
                self.assertEqual(
                    "unavailable",
                    model["data_quality"].get("prs_status"),
                )

    def test_exact_zero_commit_and_pull_request_observations_remain_exact(self):
        observed_at = "2026-08-26T15:00:00Z"
        observations = {
            "public_scope_commits": _provider_observation(
                metric_id="public_scope_commits",
                source_metric_id="owned_public_nonfork_authored_commits",
                value=0,
                status="ok",
                complete=True,
                population_id="owned-public-nonfork-repositories",
                population_signature="none",
                window_start=None,
                window_end=None,
                observed_at=observed_at,
                source_id="github_rest_repo_commits",
                source_mode="live",
                completion_reason="empty_population",
            ),
            "prs_merged": _provider_observation(
                metric_id="prs_merged",
                source_metric_id="merged_prs_primary_visible_population",
                value=0,
                status="ok",
                complete=True,
                population_id="owned-repositories-visible-to-primary-pr-search",
                population_signature=None,
                window_start="2025-08-27T00:00:00Z",
                window_end=observed_at,
                observed_at=observed_at,
                source_id="github_rest_merged_pr_search_primary",
                source_mode="live",
                completion_reason="all_components_observed",
            ),
        }
        collected = replace(
            self.collected,
            events=[],
            public_scope_commits=999,
        )
        collected = _with_metric_observations(collected, observations)

        model = compute_profile_model(
            collected,
            logger=_noop,
            allow_network_calls=False,
        )

        self.assertEqual(0, model["snapshot"].get("public_scope_commits"))
        self.assertEqual(0, model["snapshot"].get("prs_merged"))
        self.assertEqual("ok", model["data_quality"].get("commits_status"))
        self.assertEqual("ok", model["data_quality"].get("prs_status"))
        carriers = model["data_quality"].get("non_exact_metrics", {})
        self.assertNotIn("public_scope_commits", carriers)
        self.assertNotIn("prs_merged", carriers)

    def test_previous_contribution_total_retains_time_and_holds_publication(self):
        previous_observation = _provider_observation(
            metric_id="last_year_contributions",
            source_metric_id="previous_profile_snapshot_contributions",
            value=777,
            status="fallback",
            complete=True,
            population_id="github-contribution-calendar-visible-to-provider",
            population_signature=None,
            window_start=None,
            window_end=None,
            observed_at="2026-08-25T09:30:00Z",
            source_id="previous_profile_snapshot",
            source_mode="previous_snapshot",
            completion_reason="previous_snapshot",
        )
        collected = replace(
            self.collected,
            calendar=None,
            total_contributions=777,
        )
        collected = _with_metric_observations(
            collected,
            {"last_year_contributions": previous_observation},
        )
        model = compute_profile_model(
            collected,
            logger=_noop,
            allow_network_calls=False,
        )

        with self.subTest(assertion="exact contribution fields excluded"):
            self.assertIsNone(model["snapshot"]["last_year_contributions"])
            self.assertIsNone(model["scorecard"]["last_year_contributions"])
        carrier = model["data_quality"].get("non_exact_metrics", {}).get(
            "last_year_contributions",
            {},
        )
        with self.subTest(assertion="previous value and source time retained"):
            self.assertEqual(777, carrier.get("value"))
            self.assertEqual("2026-08-25T09:30:00Z", carrier.get("observed_at"))
            self.assertEqual("fallback", carrier.get("status"))
            self.assertEqual("previous_snapshot", carrier.get("source_mode"))
        with self.subTest(assertion="one publication hold fact"):
            self.assertEqual(
                ("NONCURRENT_CONTRIBUTIONS",),
                _publication_hold_reasons(model),
            )
        with self.subTest(assertion="status and provenance stay metric-specific"):
            self.assertEqual("fallback", model["data_quality"].get("contributions_status"))
            provenance = model["data_quality"].get("metric_provenance", {}).get(
                "last_year_contributions",
                {},
            )
            self.assertEqual("2026-08-25T09:30:00Z", provenance.get("observed_at"))
            self.assertNotIn("value", provenance)

    def test_misbound_degraded_observation_does_not_reach_nonexact_output(self):
        observation = _provider_observation(
            metric_id="prs_merged",
            source_metric_id="merged_prs_public_visible_population",
            value=23,
            status="fallback",
            complete=True,
            population_id="owned-public-repositories-visible-to-public-pr-search",
            population_signature=None,
            window_start="2025-08-27T00:00:00Z",
            window_end="2026-08-26T15:00:00Z",
            observed_at="2026-08-26T15:00:00Z",
            source_id="github_rest_merged_pr_search_public",
            source_mode="fallback",
            completion_reason="public_retry",
        )
        base = replace(self.collected, events=[])
        valid_model = compute_profile_model(
            _with_metric_observations(base, {"prs_merged": observation}),
            logger=_noop,
            allow_network_calls=False,
        )
        misbound_model = compute_profile_model(
            _with_metric_observations(
                base,
                {
                    "prs_merged": {
                        **copy.deepcopy(observation),
                        "source_mode": "previous_snapshot",
                    }
                },
            ),
            logger=_noop,
            allow_network_calls=False,
        )
        valid_carrier = valid_model["data_quality"].get(
            "non_exact_metrics", {}
        ).get("prs_merged", {})
        misbound_carriers = misbound_model["data_quality"].get(
            "non_exact_metrics", {}
        )

        self.assertEqual("fallback", valid_carrier.get("source_mode"))
        self.assertEqual(
            {
                "snapshot_value": None,
                "status": "unavailable",
                "has_nonexact_carrier": False,
            },
            {
                "snapshot_value": misbound_model["snapshot"].get("prs_merged"),
                "status": misbound_model["data_quality"].get("prs_status"),
                "has_nonexact_carrier": "prs_merged" in misbound_carriers,
            },
            "a public pull-request retry cannot be projected as previous-snapshot evidence",
        )

    def test_exact_zero_contributions_remain_current(self):
        observation = _provider_observation(
            metric_id="last_year_contributions",
            source_metric_id="github_contribution_calendar_total_and_days",
            value={
                "total": 0,
                "days": ({"date": "2026-08-26", "count": 0},),
            },
            status="ok",
            complete=True,
            population_id="github-contribution-calendar-visible-to-provider",
            population_signature=None,
            window_start="2025-08-27T00:00:00Z",
            window_end="2026-08-26T15:00:00Z",
            observed_at="2026-08-26T15:00:00Z",
            source_id="github_graphql_contribution_calendar",
            source_mode="live",
            completion_reason="all_components_observed",
        )
        collected = replace(
            self.collected,
            calendar={
                "totalContributions": 0,
                "weeks": [
                    {
                        "contributionDays": [
                            {"date": "2026-08-26", "contributionCount": 0}
                        ]
                    }
                ],
            },
            total_contributions=0,
        )
        collected = _with_metric_observations(
            collected,
            {"last_year_contributions": observation},
        )
        model = compute_profile_model(
            collected,
            logger=_noop,
            allow_network_calls=False,
        )

        self.assertEqual(0, model["snapshot"]["last_year_contributions"])
        self.assertEqual(0, model["scorecard"]["last_year_contributions"])
        self.assertNotIn(
            "last_year_contributions",
            model["data_quality"].get("non_exact_metrics", {}),
        )
        self.assertNotIn("NONCURRENT_CONTRIBUTIONS", _publication_hold_reasons(model))

    def test_duplicate_repository_identity_is_rejected_before_output(self):
        from scripts.pipeline import profile_pipeline

        public_repo = copy.deepcopy(self.collected.repos[1])
        public_duplicate = copy.deepcopy(public_repo)
        public_case_collision = copy.deepcopy(public_repo)
        public_case_collision["name"] = public_repo["name"].upper()
        public_case_collision["owner"] = {
            "login": public_repo["owner"]["login"].upper()
        }
        private_collision = copy.deepcopy(public_repo)
        private_collision.update(
            {
                "private": True,
                "visibility": "private",
            }
        )

        candidates = {
            "exact duplicate": replace(
                self.collected,
                repo_counts={
                    "public_owned_total": 2,
                    "public_owned_forks": 0,
                    "public_owned_nonfork": 2,
                    "private_owned": 0,
                    "private_owned_nonfork": 0,
                },
                repos=[public_repo, public_duplicate],
                all_repos=[public_repo, public_duplicate],
                private_repos=[],
            ),
            "case-fold collision": replace(
                self.collected,
                repo_counts={
                    "public_owned_total": 2,
                    "public_owned_forks": 0,
                    "public_owned_nonfork": 2,
                    "private_owned": 0,
                    "private_owned_nonfork": 0,
                },
                repos=[public_repo, public_case_collision],
                all_repos=[public_repo, public_case_collision],
                private_repos=[],
            ),
            "public-private collision": replace(
                self.collected,
                repo_counts={
                    "public_owned_total": 1,
                    "public_owned_forks": 0,
                    "public_owned_nonfork": 1,
                    "private_owned": 1,
                    "private_owned_nonfork": 1,
                },
                repos=[public_repo],
                all_repos=[public_repo],
                private_repos=[private_collision],
            ),
        }

        for label, collected in candidates.items():
            with self.subTest(collision=label), patch.object(
                profile_pipeline, "ensure_output_dirs"
            ) as ensure_dirs, patch.object(
                profile_pipeline, "generate_assets"
            ) as generate_assets, patch.object(
                profile_pipeline, "write_dashboard_json"
            ) as write_dashboard_json, patch.object(
                profile_pipeline, "render_readme"
            ) as render_readme:
                error = None
                try:
                    profile_pipeline.run_profile_pipeline_with_collected(
                        collected,
                        logger=lambda *_args, **_kwargs: None,
                        allow_network_calls=False,
                        source_kind="fixture",
                    )
                except ValueError as exc:
                    error = str(exc)

                self.assertEqual(
                    {
                        "duplicate_rejected": True,
                        "writer_calls": (0, 0, 0, 0),
                    },
                    {
                        "duplicate_rejected": bool(
                            error and "duplicate" in error.casefold()
                        ),
                        "writer_calls": (
                            ensure_dirs.call_count,
                            generate_assets.call_count,
                            write_dashboard_json.call_count,
                            render_readme.call_count,
                        ),
                    },
                )

    def test_unique_repository_identities_remain_distinct(self):
        first = copy.deepcopy(self.collected.repos[1])
        second = copy.deepcopy(first)
        first["owner"] = {"login": "owner-one"}
        first["html_url"] = "https://github.com/owner-one/service-one"
        first["name"] = "service-one"
        second["owner"] = {"login": "owner-two"}
        second["html_url"] = "https://github.com/owner-two/service-two"
        second["name"] = "service-two"
        collected = replace(
            self.collected,
            repo_counts={
                "public_owned_total": 2,
                "public_owned_forks": 0,
                "public_owned_nonfork": 2,
                "private_owned": 0,
                "private_owned_nonfork": 0,
            },
            repos=[first, second],
            all_repos=[first, second],
            private_repos=[],
        )
        model = compute_profile_model(
            collected,
            logger=_noop,
            allow_network_calls=False,
        )
        full_names = {
            row.get("full_name")
            for row in model["repo_overview_rows"]
            if isinstance(row, dict)
        }
        self.assertEqual(
            {"owner-one/service-one", "owner-two/service-two"},
            full_names,
        )

    def test_same_repository_name_under_different_owners_keeps_both_rows(self):
        first = copy.deepcopy(self.collected.repos[1])
        second = copy.deepcopy(first)
        first["owner"] = {"login": "owner-one"}
        first["html_url"] = "https://github.com/owner-one/shared-service"
        first["name"] = "shared-service"
        second["owner"] = {"login": "owner-two"}
        second["html_url"] = "https://github.com/owner-two/shared-service"
        second["name"] = "shared-service"
        collected = replace(
            self.collected,
            repo_counts={
                "public_owned_total": 2,
                "public_owned_forks": 0,
                "public_owned_nonfork": 2,
                "private_owned": 0,
                "private_owned_nonfork": 0,
            },
            repos=[first, second],
            all_repos=[first, second],
            private_repos=[],
        )
        model = compute_profile_model(
            collected,
            logger=_noop,
            allow_network_calls=False,
        )
        full_names = [
            row.get("full_name")
            for row in model["repo_overview_rows"]
            if isinstance(row, dict)
        ]
        self.assertCountEqual(
            ["owner-one/shared-service", "owner-two/shared-service"],
            full_names,
        )

    def test_capped_collections_render_bounded_readme_claims(self):
        now = datetime.now(timezone.utc)
        repositories = []
        for index in range(20):
            repository = copy.deepcopy(self.collected.repos[1])
            language = f"Language-{index:02d}"
            repository.update(
                {
                    "name": f"service-{index:02d}",
                    "html_url": f"https://github.com/jguida941/service-{index:02d}",
                    "created_at": _iso(now - timedelta(hours=index)),
                    "pushed_at": _iso(now - timedelta(minutes=index + 1)),
                    "latest_commit_message": f"Improve service {index:02d}",
                    "language": language,
                    "language_bytes": {language: 1000 + index},
                    "language_bytes_complete": True,
                }
            )
            repositories.append(repository)

        collected = self._collected_with_repositories(repositories, [])
        model = compute_profile_model(
            collected,
            logger=_noop,
            allow_network_calls=False,
        )
        self.assertEqual(12, len(model["top_languages"]))
        self.assertEqual(10, len(model["recent_created"]))
        self.assertEqual(18, len(model["activity_feed"]))
        self.assertGreater(len(repositories), 18)
        self.assertEqual(18, len(model["repo_overview_rows"]))

        from scripts.pipeline.render_outputs import render_readme

        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            (output_root / "templates").mkdir()
            shutil.copy2(
                Path("templates/README.md.tpl"),
                output_root / "templates/README.md.tpl",
            )
            original_cwd = Path.cwd()
            os.chdir(output_root)
            try:
                render_readme(model, logger=_noop)
            finally:
                os.chdir(original_cwd)
            readme = (output_root / "README.md").read_text(encoding="utf-8")

        collection_line = next(
            line for line in readme.splitlines() if "project matrix" in line.casefold()
        )
        normalized = collection_line.casefold()
        self.assertIn("Open the full dashboard", readme)
        self.assertIn("curated", normalized)
        self.assertIn("recent delivery", normalized)
        self.assertIn("top-language", normalized)
        self.assertIn("recent repositor", normalized)
        self.assertIsNone(
            re.search(r"\b(full|complete|all|preserved)\b", normalized),
            collection_line,
        )

    def test_missing_optional_scorecard_value_stays_unavailable(self):
        cards = _build_scorecard_cards({}, {"CYAN": "#00ffff"})
        contributions = next(
            card for card in cards if card["key"] == "last_year_contributions"
        )

        self.assertIsNone(contributions["value"])
        self.assertEqual("n/a", contributions["display_value"])


    def test_workflow_summary_uses_valid_pairs_in_both_visibility_partitions(self):
        collected = self._collected()
        invalid = dict(collected.private_repos[0], has_ci_workflows=False, workflow_file_count=7)
        model = compute_profile_model(replace(collected, private_repos=[invalid]),
                                      logger=_noop, allow_network_calls=False)
        public, private, combined = (model["automation"][key] for key in ("public", "private", "combined"))
        self.assertEqual((1, 2, 2), (public["configured_repos"], public["eligible_repos"], public["workflow_files"]))
        self.assertEqual((None, None, 1), (private["configured_repos"], private["workflow_files"], private["unknown_workflow_repos"]))
        self.assertEqual((1, 2, 3, "partial"), (combined["configured_repos"], combined["workflow_files"], combined["eligible_repos"], combined["status"]))
        self.assertAlmostEqual(100 / 3, combined["adoption_pct"])
        self.assertEqual(combined["workflow_files"], model["scorecard"]["automation_workflows"])
        self.assertEqual(combined["configured_repos"], model["snapshot"]["ci_repos"])

    def test_missing_private_inventory_preserves_public_subtotal_without_ratio(self):
        collected = self._collected()
        counts = dict(collected.repo_counts, private_owned=None, private_owned_nonfork=None)
        model = compute_profile_model(replace(collected, repo_counts=counts, private_repos=[]),
                                      logger=_noop, allow_network_calls=False)
        self.assertEqual("exact", model["automation"]["public"]["status"])
        self.assertEqual(1, model["automation"]["combined"]["configured_repos"])
        self.assertIsNone(model["automation"]["combined"]["eligible_repos"])
        self.assertIsNone(model["scorecard"]["ci_coverage_pct"])

    def test_workflow_projection_contract_rejects_independent_scalar_or_display_edits(self):
        from scripts.contracts import _automation_contract_errors
        from scripts.pipeline.render_outputs import _public_dashboard_data
        model = compute_profile_model(self._collected(), logger=_noop, allow_network_calls=False)
        payload = _public_dashboard_data(model["dashboard_data"])
        self.assertEqual([], _automation_contract_errors(payload))
        for section, key in (("engineering", "automation_workflows"),
                             ("scorecard", "ci_coverage_pct"), ("snapshot", "ci_repos")):
            altered = copy.deepcopy(payload)
            altered[section][key] = 999
            self.assertTrue(_automation_contract_errors(altered))
        altered = copy.deepcopy(payload)
        altered["automation_display"]["combined"]["workflow_files"] = "999"
        self.assertTrue(_automation_contract_errors(altered))


class StreakTimezoneTests(unittest.TestCase):
    def test_streak_counts_back_from_local_today(self):
        today = date(2026, 6, 28)
        days = [
            {"date": "2026-06-26", "contributionCount": 0},
            {"date": "2026-06-27", "contributionCount": 4},
            {"date": "2026-06-28", "contributionCount": 8},
            {"date": "2099-01-01", "contributionCount": 0},  # future ignored
        ]
        calendar = {"weeks": [{"contributionDays": days}]}
        streak = _compute_current_streak_days(calendar, datetime(2026, 6, 28, tzinfo=timezone.utc), today)
        self.assertEqual(streak, 2)


class ContributionTrendTests(unittest.TestCase):
    def _input(self, length=17, *, zero=False):
        from types import SimpleNamespace
        first = date(2026, 9, 21)
        rows = [{"date": (first + timedelta(days=i)).isoformat(),
                 "contributionCount": 0 if zero else i + 1} for i in range(length)]
        # Deliberately non-week containers: dates, not input ordering, own buckets.
        calendar = {"weeks": [{"contributionDays": rows}]}
        observation = {
            "schema": "profile-provider-observation/v1", "metric_id": "last_year_contributions",
            "source_metric_id": "github_contribution_calendar_total_and_days",
            "value": {"total": sum(row["contributionCount"] for row in rows),
                      "days": tuple({"date": row["date"], "count": row["contributionCount"]} for row in rows)},
            "status": "ok", "complete": True,
            "population_id": "github-contribution-calendar-visible-to-provider", "population_signature": None,
            "window_start": "2026-09-21T00:00:00Z", "window_end": "2026-10-07T18:00:00Z",
            "observed_at": "2026-10-07T18:00:00Z", "source_id": "github_graphql_contribution_calendar",
            "source_mode": "live", "completion_reason": "all_components_observed",
        }
        return SimpleNamespace(calendar=calendar, metric_observations={"last_year_contributions": observation})

    def _trend(self, value):
        from scripts.pipeline.compute_metrics import _build_contribution_trend
        return _build_contribution_trend(value)

    def test_dated_sums_and_partial_week(self):
        value = self._input()
        result = self._trend(value)
        self.assertEqual([28, 77, 48], [point["contributions"] for point in result["points"]])
        self.assertEqual([False, False, True], [point["partial"] for point in result["points"]])
        self.assertEqual(("2026-09-21", "2026-10-07", "UTC"),
                         (result["window_start"], result["window_end"], result["timezone"]))
        value.calendar["weeks"][0]["contributionDays"].reverse()
        self.assertEqual(result, self._trend(value))

    def test_zero_is_available_and_missing_cutoff_is_unknown(self):
        value = self._input(7, zero=True)
        value.metric_observations = {}
        result = self._trend(value)
        self.assertEqual(("available", "unknown"), (result["status"], result["completeness"]))
        self.assertEqual((0, True), (result["points"][0]["contributions"], result["points"][0]["partial"]))

    def test_observation_not_generation_establishes_coverage(self):
        value = self._input(7)
        observation = value.metric_observations["last_year_contributions"]
        observation["window_end"] = observation["observed_at"] = "2026-09-27T23:59:59Z"
        self.assertTrue(self._trend(value)["points"][0]["partial"])
        observation["window_end"] = observation["observed_at"] = "2026-09-28T00:00:00Z"
        self.assertFalse(self._trend(value)["points"][0]["partial"])
        observation["window_start"] = "2026-09-21T12:00:00Z"
        self.assertTrue(self._trend(value)["points"][0]["partial"])

    def test_unmatched_and_naive_observations_cannot_certify_coverage(self):
        for change in ("different", "naive", "order", "observed_before_window"):
            value = self._input(7)
            observation = value.metric_observations["last_year_contributions"]
            if change == "different":
                observation["value"]["days"][0]["count"] = 100
            elif change == "naive":
                observation["window_end"] = "2026-10-07T18:00:00"
            elif change == "order":
                observation["window_end"] = "2026-01-01T00:00:00Z"
            else:
                observation["observed_at"] = "2026-01-01T00:00:00Z"
            self.assertEqual("unknown", self._trend(value)["completeness"])

    def test_invalid_dates_counts_duplicates_and_gaps_are_unavailable(self):
        for invalid in (True, -1, 1.5, "2", None):
            value = self._input()
            value.calendar["weeks"][0]["contributionDays"][0]["contributionCount"] = invalid
            self.assertEqual("unavailable", self._trend(value)["status"])
        for change in ("gap", "duplicate", "malformed", "outside_window"):
            value = self._input()
            rows = value.calendar["weeks"][0]["contributionDays"]
            if change == "gap":
                rows.pop(3)
            elif change == "duplicate":
                rows.append(dict(rows[0]))
            elif change == "malformed":
                rows[0]["date"] = "2026-9-21"
            else:
                value.metric_observations["last_year_contributions"]["window_end"] = "2026-10-06T18:00:00Z"
            self.assertEqual("unavailable", self._trend(value)["status"])

    def test_latest_twelve_weeks_and_viewer_zone_invariance(self):
        value = self._input(98)
        value.metric_observations = {}
        expected = self._trend(value)
        self.assertEqual(12, len(expected["points"]))
        self.assertEqual("2026-10-05", expected["window_start"])
        self.assertEqual([sum(range(i + 1, i + 8)) for i in range(14, 98, 7)],
                         [point["contributions"] for point in expected["points"]])
        for zone in ("UTC", "America/New_York", "Asia/Tokyo"):
            with patch.dict(os.environ, {"PROFILE_TIMEZONE": zone, "TZ": zone}):
                self.assertEqual(expected, self._trend(value))




if __name__ == "__main__":
    unittest.main()

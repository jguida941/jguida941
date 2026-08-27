"""Privacy regressions for data published by the profile generator.

site/data/profile_snapshot.json is served on GitHub Pages and fetched by the web
dashboard, so it IS the public profile — one curl away. The static index.html being
clean is NOT enough (the sensitive data arrives client-side from this JSON). The owner
rule: the internal token mode (whether the bot ran authenticated) and any credential
must never appear on the public profile; private-repo COUNTS/metadata are allowed,
contents and tokens are not.

These tests cover both the committed public JSON and the projection used for each
pipeline run.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "scripts").is_dir() and (parent / "tests").is_dir():
            return parent
    raise RuntimeError("repo root not found")


ROOT = _repo_root()
PUBLIC_JSON = ROOT / "site" / "data" / "profile_snapshot.json"


class PublicDataPrivacyContract(unittest.TestCase):
    def setUp(self):
        self.text = PUBLIC_JSON.read_text(encoding="utf-8")
        self.data = json.loads(self.text)

    def test_committed_snapshot_satisfies_the_publication_boundary(self):
        from scripts.pipeline.render_outputs import _public_dashboard_data

        self.assertEqual(
            self.data,
            _public_dashboard_data(self.data),
            "the committed snapshot must already be its own publishable projection",
        )

    def test_data_quality_carries_no_token_field(self):
        dq = self.data.get("data_quality", {})
        token_keys = [k for k in dq if "token" in k.lower()]
        self.assertEqual([], token_keys, f"data_quality must not expose token fields: {token_keys}")

    def test_activity_aggregations_are_counts_only(self):
        """Events and calendar data reduce to numbers, clean dates, and
        whitelisted event labels; no repo name, URL, commit message, payload, hostile
        type, or hostile date string may survive into the public JSON."""
        from scripts.pipeline.compute_metrics import (
            _WEB_EVENT_LABELS, _activity_rhythm, _public_contribution_calendar,
        )
        hostile_events = [
            {"type": "PushEvent", "created_at": "2026-06-01T13:00:00Z",
             "repo": {"name": "jguida941/secret-private-repo", "url": "https://x/secret"},
             "payload": {"commits": [{"message": "CONFIDENTIAL refactor", "sha": "deadbeef"}]},
             "actor": {"login": "someone"}},
            {"type": "EvilEvent<script>", "created_at": "2026-06-01T14:00:00Z",
             "repo": {"name": "another-private"}},  # unmapped type must be dropped
            "not-a-dict", None, {"type": "PushEvent"},  # missing created_at
        ]
        rhythm = _activity_rhythm(hostile_events)
        cal = _public_contribution_calendar({"totalContributions": 5, "weeks": [{"contributionDays": [
            {"date": "2026-06-01", "contributionCount": 3},
            {"date": "<img onerror=alert(1)>", "contributionCount": 9},  # hostile date dropped
            {"date": "2026-06-02", "contributionCount": -4},  # negative coerced to 0
        ]}]})
        blob = json.dumps({"rhythm": rhythm, "calendar": cal})
        for leak in ("secret-private-repo", "CONFIDENTIAL", "deadbeef", "payload", "commits",
                     "message", "actor", "login", "EvilEvent", "<script>", "onerror", "<img"):
            self.assertNotIn(leak, blob, f"aggregation leaked {leak!r} into the public JSON")
        # The public shapes contain aggregate values only.
        self.assertEqual({"matrix", "event_mix", "total", "timezone"}, set(rhythm))
        self.assertEqual(7, len(rhythm["matrix"]))
        self.assertTrue(all(len(row) == 24 and all(isinstance(c, int) for c in row) for row in rhythm["matrix"]))
        self.assertTrue(set(rhythm["event_mix"]).issubset(set(_WEB_EVENT_LABELS.values())),
                        "event_mix keys must come only from the fixed label whitelist")
        self.assertIsInstance(rhythm["total"], int)
        for week in cal["weeks"]:
            for day in week:
                self.assertEqual({"date", "count"}, set(day), "calendar day must be date+count only")
                self.assertRegex(day["date"], r"^\d{4}-\d{2}-\d{2}$", "date must be clean ISO")
                self.assertIsInstance(day["count"], int)
                self.assertGreaterEqual(day["count"], 0)

    def test_scrubber_strips_token_fields_but_keeps_health(self):
        """The publication projection removes credentials without hiding source health."""
        from scripts.pipeline.render_outputs import _public_dashboard_data
        out = _public_dashboard_data(
            {"data_quality": {"token_mode": "authenticated", "ci_status": "ok", "ci_note": "x"},
             "username": "u"}
        )
        self.assertNotIn("token_mode", out["data_quality"])
        self.assertEqual("ok", out["data_quality"]["ci_status"], "public source health must be preserved")
        self.assertEqual("u", out["username"], "non-sensitive fields must pass through")

    def test_public_projection_keeps_private_repository_metadata_and_aggregate_counts(self):
        from scripts.pipeline.render_outputs import _public_dashboard_data

        payload = {
            "snapshot": {"private_owned_repos": 2},
            "engineering": {"private_repos_total": 2},
            "focus": {
                "now": [
                    {"title": "public-project", "is_private": False},
                    {
                        "title": "confidential-repository",
                        "url": "https://github.com/jguida941/confidential-repository",
                        "detail": "Rust · pushed 2h ago",
                        "last_commit_msg": "Improve the release dashboard",
                        "language": "Rust",
                        "pushed_at": "2026-08-26T12:00:00Z",
                        "is_private": True,
                    },
                ]
            },
            "recent_pull_requests": [
                {"title": "Public change", "repo": "jguida941/public-project"},
                {
                    "title": "Confidential change",
                    "repo": "jguida941/confidential-repository",
                    "is_private": True,
                },
            ],
        }

        published = _public_dashboard_data(payload)

        self.assertEqual(payload, published)

    def test_public_projection_keeps_public_marked_mapping_values(self):
        from scripts.pipeline.render_outputs import _public_dashboard_data

        payload = {
            "snapshot": {"private_owned_repos": 3, "public_owned_repos": 5},
            "direct": {"name": "public-direct", "is_private": False},
            "nested": {
                "value": {"name": "public-nested", "private": False},
                "mixed": [
                    {
                        "branch": {
                            "value": {"name": "public-deep", "visibility": "PUBLIC"}
                        }
                    }
                ],
            },
        }

        self.assertEqual(payload, _public_dashboard_data(payload))

    def test_public_projection_recursively_removes_credentials_without_dropping_repo_metadata(self):
        from scripts.pipeline.render_outputs import _public_dashboard_data

        payload = {
            "snapshot": {"private_owned_repos": 3, "public_owned_repos": 5},
            "direct_private": {
                "name": "secret-api",
                "last_commit_msg": "Improve cache invalidation",
                "language": "Rust",
                "pushed_at": "2026-08-26T12:00:00Z",
                "is_private": True,
                "deploy_token": "ghp_NOT_A_REAL_TOKEN",
                "source": "print('not repository metadata')",
            },
            "direct_public": {"name": "public-direct", "is_private": False},
            "nested": {
                "private_value": {
                    "name": "private-nested",
                    "private": True,
                    "credential": "definitely-fake",
                    "file_contents": "fake file body",
                },
                "public_value": {"name": "public-nested", "private": False},
                "mixed": [
                    {
                        "name": "private-list",
                        "visibility": "PRIVATE",
                        "client_secret": "not-a-real-secret",
                    },
                    {"name": "public-list", "visibility": "PUBLIC"},
                    {
                        "branch": {
                            "private_leaf": {
                                "name": "private-deep",
                                "visibility": "private",
                                "notes": "Bearer ghp_NOT_A_REAL_TOKEN",
                            },
                            "public_leaf": {
                                "name": "public-deep",
                                "visibility": "public",
                            },
                            "deeper": [
                                {
                                    "private_value": {
                                        "name": "private-deepest",
                                        "is_private": True,
                                        "Authorization": "Bearer github_pat_NOT_REAL",
                                    },
                                    "public_value": {
                                        "name": "public-deepest",
                                        "is_private": False,
                                    },
                                }
                            ],
                        }
                    },
                ],
            },
            "data_quality": {
                "token_mode": "authenticated",
                "ci_status": "ok",
            },
            "notes": [
                "ordinary repository metadata",
                "Bearer ghp_NOT_A_REAL_TOKEN",
            ],
        }

        published = _public_dashboard_data(payload)
        published_text = json.dumps(published, sort_keys=True)

        self.assertEqual(3, published["snapshot"]["private_owned_repos"])
        self.assertEqual(5, published["snapshot"]["public_owned_repos"])
        self.assertEqual("ok", published["data_quality"]["ci_status"])
        self.assertIn(
            "direct_private",
            published,
            "private classification is repository metadata, not a credential",
        )
        self.assertEqual(
            {
                "name": "secret-api",
                "last_commit_msg": "Improve cache invalidation",
                "language": "Rust",
                "pushed_at": "2026-08-26T12:00:00Z",
                "is_private": True,
            },
            published["direct_private"],
        )
        for repository_name in (
            "private-nested",
            "private-list",
            "private-deep",
            "private-deepest",
            "public-direct",
            "public-nested",
            "public-list",
            "public-deep",
            "public-deepest",
        ):
            with self.subTest(repository_name=repository_name):
                self.assertIn(repository_name, published_text)

        for credential_value in (
            "ghp_NOT_A_REAL_TOKEN",
            "definitely-fake",
            "not-a-real-secret",
            "github_pat_NOT_REAL",
            "Bearer ",
            "authenticated",
            "print('not repository metadata')",
            "fake file body",
        ):
            with self.subTest(credential_value=credential_value):
                self.assertNotIn(credential_value, published_text)

        self.assertEqual(["ordinary repository metadata"], published["notes"])
        self.assertNotIn("token_mode", published["data_quality"])

    def test_exact_credential_shapes_are_rejected_across_publication_surfaces(self):
        from scripts.pipeline.profile_helpers import (
            contains_credential_material,
            safe_commit_headline,
        )
        from scripts.pipeline.render_outputs import _public_dashboard_data
        from scripts.quality.validate_generated_profile import (
            _contains_credential_material as validator_contains_credential_material,
        )

        legacy_personal_token = (
            "PERSONAL_GITHUB_TOKEN=" + ("0123456789abcdef" * 2) + "01234567"
        )
        classic_personal_token = (
            "ghp_" + "abcdefghijklmnopqrstuvwxyz" + "abcdefghij"
        )
        aws_secret_assignment = "AWS_SECRET_ACCESS_KEY=" + ("a1B2" * 10)
        self.assertEqual(40, len(legacy_personal_token.rsplit("=", 1)[1]))
        self.assertEqual(36, len(classic_personal_token.removeprefix("ghp_")))
        self.assertEqual(40, len(aws_secret_assignment.rsplit("=", 1)[1]))
        synthetic_credentials = (
            legacy_personal_token,
            classic_personal_token,
            aws_secret_assignment,
        )

        for value in synthetic_credentials:
            with self.subTest(value=value, surface="shared classifier"):
                self.assertTrue(contains_credential_material(value))
            with self.subTest(value=value, surface="validator"):
                self.assertTrue(validator_contains_credential_material(value))
            with self.subTest(value=value, surface="commit headline"):
                self.assertEqual("", safe_commit_headline(f"Deploy update {value}"))

        published = _public_dashboard_data(
            {
                "repository": {
                    "name": "private-observability-service",
                    "language": "Rust",
                    "last_commit_msg": "Improve deployment observability",
                    "is_private": True,
                },
                "samples": list(synthetic_credentials),
            }
        )
        self.assertEqual(
            "private-observability-service",
            published["repository"]["name"],
        )
        self.assertEqual(
            "Improve deployment observability",
            published["repository"]["last_commit_msg"],
        )
        self.assertEqual([], published["samples"])

    def test_nested_credential_alias_fields_are_removed_without_hiding_repo_metadata(self):
        from scripts.pipeline.render_outputs import _public_dashboard_data

        access_token_value = "Ab3d" * 9
        aws_secret_value = "a1B2" * 10
        self.assertEqual(36, len(access_token_value))
        self.assertEqual(40, len(aws_secret_value))
        payload = {
            "repository": {
                "name": "private-release-tools",
                "language": "Python",
                "last_commit_msg": "Document token rotation support",
                "is_private": True,
            },
            "transport": {
                "accessTokenValue": access_token_value,
                "nested": {
                    "aws_secret_access_key_value": aws_secret_value,
                },
            },
        }

        published = _public_dashboard_data(payload)

        self.assertEqual(payload["repository"], published["repository"])
        credential_aliases = (
            ("accessTokenValue", published.get("transport", {})),
            (
                "aws_secret_access_key_value",
                published.get("transport", {}).get("nested", {}),
            ),
        )
        for key, container in credential_aliases:
            with self.subTest(key=key):
                self.assertNotIn(key, container)

    def test_harmless_security_vocabulary_remains_publishable_metadata(self):
        from scripts.pipeline.profile_helpers import (
            contains_credential_material,
            safe_commit_headline,
        )
        from scripts.pipeline.render_outputs import _public_dashboard_data

        harmless_metadata = (
            "Improve Bearer token refresh handling",
            "Document bearer authentication support",
            "Refactor Authorization header parser",
            "Document PERSONAL_GITHUB_TOKEN rotation support",
            "Refactor AWS_SECRET_ACCESS_KEY validation",
            "Review accessTokenValue form help",
            "Review aws_secret_access_key_value mapping",
            "github_pat_migration_helper",
            "ghp_tokenformatvalidator",
        )

        for value in harmless_metadata:
            with self.subTest(value=value, surface="classifier"):
                self.assertFalse(contains_credential_material(value))
            with self.subTest(value=value, surface="commit headline"):
                self.assertEqual(value, safe_commit_headline(value))

        payload = {"metadata": list(harmless_metadata)}
        self.assertEqual(payload, _public_dashboard_data(payload))

    def test_basic_authentication_prose_and_credentials_keep_their_distinct_boundaries(self):
        from scripts.pipeline.collect_data import CollectedProfileData
        from scripts.pipeline.compute_metrics import compute_profile_model
        from scripts.pipeline.profile_helpers import (
            contains_credential_material,
            safe_commit_headline,
        )
        from scripts.pipeline.render_outputs import _public_dashboard_data
        from scripts.rendering.generate_currently_working import generate

        harmless_basic = "Add Basic authentication support"
        harmless_bearer = "Add Bearer authentication support"
        basic_credential = (
            "Authorization: Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ=="
        )
        arms = {
            "basic-docs": harmless_basic,
            "bearer-docs": harmless_bearer,
            "basic-credential-boundary": basic_credential,
        }
        now = datetime.now(timezone.utc)

        def repository(name: str, headline: str, *, private: bool, age: int) -> dict:
            return {
                "name": name,
                "owner": {"login": "jguida941"},
                "private": private,
                "visibility": "private" if private else "public",
                "fork": False,
                "html_url": f"https://github.com/jguida941/{name}",
                "pushed_at": (
                    now - timedelta(minutes=age)
                ).isoformat().replace("+00:00", "Z"),
                "created_at": "2026-01-01T00:00:00Z",
                "stargazers_count": 0,
                "forks_count": 0,
                "language": "Python",
                "language_bytes": {"Python": 1000},
                "language_bytes_complete": True,
                "has_ci_workflows": True,
                "workflow_file_count": 1,
                "latest_commit_message": headline,
            }

        public_repos = [
            repository(f"public-{suffix}", headline, private=False, age=index)
            for index, (suffix, headline) in enumerate(arms.items(), start=1)
        ]
        private_repos = [
            repository(f"private-{suffix}", headline, private=True, age=index + 10)
            for index, (suffix, headline) in enumerate(arms.items(), start=1)
        ]
        collected = CollectedProfileData(
            repo_counts={
                "public_owned_total": len(public_repos),
                "public_owned_forks": 0,
                "public_owned_nonfork": len(public_repos),
                "private_owned": len(private_repos),
                "private_owned_nonfork": len(private_repos),
            },
            repos=public_repos,
            all_repos=public_repos,
            language_bytes={"Python": len(public_repos) * 1000},
            events=[],
            latest_push_message_by_repo={},
            public_scope_commits=0,
            ci_count_probe=len(public_repos),
            calendar=None,
            total_contributions=None,
            token_mode="authenticated",
            cache_mode={"bypass": True, "ttl_seconds": 0},
            private_repos=private_repos,
        )
        model = compute_profile_model(
            collected,
            logger=lambda *_args, **_kwargs: None,
            allow_network_calls=False,
        )
        model_rows = {row["name"]: row for row in model["recent_repos"]}
        published = _public_dashboard_data({"recent_repos": model["recent_repos"]})
        published_rows = {
            row["name"]: row for row in published["recent_repos"]
        }
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "currently-working.svg"
            generate(published["recent_repos"], output_path=str(output))
            svg = output.read_text(encoding="utf-8")

        expected_names = {
            f"{visibility}-{suffix}"
            for visibility in ("public", "private")
            for suffix in arms
        }
        self.assertEqual(expected_names, set(model_rows))
        self.assertEqual(expected_names, set(published_rows))
        for name in expected_names:
            with self.subTest(name=name, surface="svg repository row"):
                self.assertIn(name, svg)

        self.assertFalse(contains_credential_material(harmless_bearer))
        self.assertEqual(harmless_bearer, safe_commit_headline(harmless_bearer))
        for visibility in ("public", "private"):
            name = f"{visibility}-bearer-docs"
            with self.subTest(visibility=visibility, arm="harmless Bearer control"):
                self.assertEqual(harmless_bearer, model_rows[name]["last_commit_msg"])
                self.assertEqual(harmless_bearer, published_rows[name]["last_commit_msg"])
        self.assertEqual(2, svg.count(harmless_bearer))

        self.assertTrue(contains_credential_material(basic_credential))
        self.assertEqual("", safe_commit_headline(basic_credential))
        for visibility in ("public", "private"):
            name = f"{visibility}-basic-credential-boundary"
            with self.subTest(visibility=visibility, arm="Basic credential boundary"):
                self.assertNotEqual(basic_credential, model_rows[name]["last_commit_msg"])
                self.assertNotEqual(basic_credential, published_rows[name]["last_commit_msg"])
        self.assertNotIn(basic_credential, json.dumps(published, sort_keys=True))
        self.assertNotIn(basic_credential, svg)

        observed_basic = {
            "classifier_allows": not contains_credential_material(harmless_basic),
            "safe_headline": safe_commit_headline(harmless_basic),
            "public_model": model_rows["public-basic-docs"]["last_commit_msg"],
            "private_model": model_rows["private-basic-docs"]["last_commit_msg"],
            "public_projection": published_rows["public-basic-docs"]["last_commit_msg"],
            "private_projection": published_rows["private-basic-docs"]["last_commit_msg"],
            "svg_occurrences": svg.count(harmless_basic),
        }
        self.assertEqual(
            {
                "classifier_allows": True,
                "safe_headline": harmless_basic,
                "public_model": harmless_basic,
                "private_model": harmless_basic,
                "public_projection": harmless_basic,
                "private_projection": harmless_basic,
                "svg_occurrences": 2,
            },
            observed_basic,
        )

    def test_repository_identity_and_password_validation_prose_remain_publishable(self):
        from scripts.pipeline.profile_helpers import (
            contains_credential_material,
            safe_commit_headline,
        )
        from scripts.pipeline.render_outputs import _public_dashboard_data

        access_key_shaped_text = "".join(("AKIA", "ABCDEFGHIJKLMNOP"))
        documentation_headline = "Fix password=validation123 handling"

        repositories = [
            {
                "name": f"{access_key_shaped_text}-public-tools",
                "url": (
                    "https://github.com/jguida941/"
                    f"{access_key_shaped_text}-public-tools"
                ),
                "last_commit_msg": documentation_headline,
                "language": "Python",
                "pushed_at": "2026-08-26T12:00:00Z",
                "is_private": False,
            },
            {
                "name": f"{access_key_shaped_text}-private-tools",
                "url": (
                    "https://github.com/jguida941/"
                    f"{access_key_shaped_text}-private-tools"
                ),
                "last_commit_msg": documentation_headline,
                "language": "Rust",
                "pushed_at": "2026-08-26T13:00:00Z",
                "is_private": True,
            },
        ]
        ordinary_repository = {
            "name": "release-dashboard",
            "url": "https://github.com/jguida941/release-dashboard",
            "last_commit_msg": "Improve release notes",
            "language": "TypeScript",
            "pushed_at": "2026-08-26T14:00:00Z",
            "is_private": False,
        }

        for repository in repositories:
            with self.subTest(
                visibility="private" if repository["is_private"] else "public",
                field="name",
            ):
                self.assertFalse(contains_credential_material(repository["name"]))
            with self.subTest(
                visibility="private" if repository["is_private"] else "public",
                field="url",
            ):
                self.assertFalse(contains_credential_material(repository["url"]))

        with self.subTest(field="documentation_headline"):
            self.assertEqual(
                documentation_headline,
                safe_commit_headline(documentation_headline),
            )
        payload = {
            "repositories": repositories,
            "ordinary_repository": ordinary_repository,
        }
        self.assertEqual(payload, _public_dashboard_data(payload))

    def test_explicit_aws_credentials_are_removed_without_dropping_repository_identity(self):
        from scripts.pipeline.profile_helpers import (
            contains_credential_material,
            safe_commit_headline,
        )
        from scripts.pipeline.render_outputs import _public_dashboard_data

        explicit_assignment = "".join(
            ("AWS_ACCESS_KEY_ID=", "AKIA", "ABCDEFGHIJKLMNOP")
        )
        repository = {
            "name": "private-release-tools",
            "url": "https://github.com/jguida941/private-release-tools",
            "last_commit_msg": explicit_assignment,
            "language": "Rust",
            "pushed_at": "2026-08-26T15:00:00Z",
            "is_private": True,
            "credential": explicit_assignment,
        }

        self.assertTrue(contains_credential_material(explicit_assignment))
        self.assertEqual("", safe_commit_headline(explicit_assignment))

        published = _public_dashboard_data({"repository": repository})
        expected_repository = {
            "name": repository["name"],
            "url": repository["url"],
            "language": repository["language"],
            "pushed_at": repository["pushed_at"],
            "is_private": True,
        }
        self.assertEqual(expected_repository, published["repository"])

    def test_ambiguous_password_prose_is_retained_while_credentials_are_removed(self):
        from scripts.pipeline.profile_helpers import (
            contains_credential_material,
            safe_commit_headline,
        )
        from scripts.pipeline.render_outputs import _public_dashboard_data

        ordinary_phrase = "password hunter2"
        explicit_assignment = "password=Abcd1234"
        authorization_value = "Authorization: Bearer Abcdefghijklmnop123456789"
        payload = {
            "repository": {
                "name": "private-password-documentation",
                "last_commit_msg": ordinary_phrase,
                "notes": ordinary_phrase,
                "language": "Python",
                "pushed_at": "2026-08-26T16:00:00Z",
                "is_private": True,
                "password": "hunter2",
            },
            "credential_samples": [explicit_assignment, authorization_value],
        }

        self.assertFalse(contains_credential_material(ordinary_phrase))
        self.assertEqual(ordinary_phrase, safe_commit_headline(ordinary_phrase))
        for value in (explicit_assignment, authorization_value):
            with self.subTest(value=value):
                self.assertTrue(contains_credential_material(value))
                self.assertEqual("", safe_commit_headline(value))

        published = _public_dashboard_data(payload)
        self.assertEqual(
            {
                "name": "private-password-documentation",
                "last_commit_msg": ordinary_phrase,
                "notes": ordinary_phrase,
                "language": "Python",
                "pushed_at": "2026-08-26T16:00:00Z",
                "is_private": True,
            },
            published["repository"],
        )
        self.assertEqual([], published["credential_samples"])

    def test_shell_style_password_assignments_are_removed_without_dropping_repository_rows(self):
        from scripts.pipeline.profile_helpers import (
            contains_credential_material,
            safe_commit_headline,
        )
        from scripts.pipeline.render_outputs import _public_dashboard_data

        credential_assignments = (
            "export password=Abcd1234",
            "password=Abcd1234;",
            "password=Abcd1234 # rotate",
        )
        documentation_controls = (
            "Document export password=Abcd1234 syntax",
            "Explain password=Abcd1234; validation",
            "Document password=Abcd1234 # rotate examples",
        )

        repositories = []
        for index, assignment in enumerate(credential_assignments, start=1):
            with self.subTest(assignment=assignment, surface="classifier"):
                self.assertTrue(contains_credential_material(assignment))
            with self.subTest(assignment=assignment, surface="commit headline"):
                self.assertEqual("", safe_commit_headline(assignment))
            repositories.append(
                {
                    "name": f"private-release-tool-{index}",
                    "url": f"https://github.com/jguida941/private-release-tool-{index}",
                    "last_commit_msg": assignment,
                    "language": "Python",
                    "pushed_at": f"2026-08-26T1{index}:00:00Z",
                    "is_private": True,
                }
            )

        for headline in documentation_controls:
            with self.subTest(headline=headline, surface="documentation classifier"):
                self.assertFalse(contains_credential_material(headline))
            with self.subTest(headline=headline, surface="documentation headline"):
                self.assertEqual(headline, safe_commit_headline(headline))

        published = _public_dashboard_data(
            {
                "repositories": repositories,
                "documentation": list(documentation_controls),
            }
        )

        self.assertEqual(list(documentation_controls), published["documentation"])
        self.assertEqual(len(repositories), len(published["repositories"]))
        for source, projected in zip(repositories, published["repositories"], strict=True):
            with self.subTest(repository=source["name"], surface="public projection"):
                self.assertEqual(
                    {key: value for key, value in source.items() if key != "last_commit_msg"},
                    projected,
                )

    def test_standalone_aws_access_key_headline_is_removed_without_hiding_repository_identity(self):
        from scripts.pipeline.profile_helpers import (
            contains_credential_material,
            safe_commit_headline,
        )
        from scripts.pipeline.render_outputs import _public_dashboard_data

        access_key = "".join(("AKIA", "ABCDEFGHIJKLMNOP"))
        sensitive_headline = f"Rotate {access_key} now"
        repository_name = f"{access_key}-release-tools"
        repository_url = f"https://github.com/jguida941/{repository_name}"

        self.assertFalse(contains_credential_material(access_key))
        self.assertEqual("", safe_commit_headline(access_key))
        self.assertEqual("", safe_commit_headline(sensitive_headline))
        self.assertEqual(repository_name, safe_commit_headline(repository_name))
        self.assertEqual(repository_url, safe_commit_headline(repository_url))

        published = _public_dashboard_data(
            {
                "repository": {
                    "name": repository_name,
                    "url": repository_url,
                    "last_commit_msg": safe_commit_headline(sensitive_headline),
                    "language": "Rust",
                    "pushed_at": "2026-08-26T17:00:00Z",
                    "is_private": True,
                }
            }
        )
        self.assertEqual(
            {
                "name": repository_name,
                "url": repository_url,
                "last_commit_msg": "",
                "language": "Rust",
                "pushed_at": "2026-08-26T17:00:00Z",
                "is_private": True,
            },
            published["repository"],
        )

    def test_ci_skip_documentation_is_not_treated_as_automation(self):
        from scripts.pipeline.profile_helpers import (
            is_bot_commit_message,
            safe_commit_headline,
        )
        from scripts.pipeline.render_outputs import _public_dashboard_data

        documentation_headlines = (
            "Document [skip ci] behavior",
            "Explain how [ci skip] works",
        )

        for headline in documentation_headlines:
            with self.subTest(headline=headline):
                self.assertFalse(is_bot_commit_message(headline))
                self.assertEqual(headline, safe_commit_headline(headline))

        payload = {"commit_headlines": list(documentation_headlines)}
        self.assertEqual(payload, _public_dashboard_data(payload))

    def test_ci_control_directives_and_automation_origins_remain_suppressed(self):
        from scripts.pipeline.profile_helpers import (
            is_bot_actor,
            is_bot_commit_message,
            safe_commit_headline,
        )

        automation_headlines = (
            "Update canonical profile artifacts",
            "chore: refresh badges [skip ci]",
            "chore: refresh metrics [ci skip]",
        )

        for headline in automation_headlines:
            with self.subTest(headline=headline):
                self.assertTrue(is_bot_commit_message(headline))
                self.assertEqual("", safe_commit_headline(headline))

        self.assertTrue(is_bot_actor("github-actions[bot]"))
        self.assertFalse(is_bot_actor("jguida941"))

    def test_harmless_sk_prefixed_repository_name_remains_publishable(self):
        from scripts.pipeline.profile_helpers import (
            contains_credential_material,
            safe_commit_headline,
        )
        from scripts.pipeline.render_outputs import _public_dashboard_data

        repository_name = "sk-learn-migration-helper"
        payload = {
            "repository": {
                "name": repository_name,
                "url": f"https://github.com/jguida941/{repository_name}",
                "language": "Python",
                "last_commit_msg": "Upgrade the migration helper",
                "is_private": True,
            }
        }

        self.assertFalse(contains_credential_material(repository_name))
        self.assertEqual(repository_name, safe_commit_headline(repository_name))
        self.assertEqual(payload, _public_dashboard_data(payload))


if __name__ == "__main__":
    unittest.main()

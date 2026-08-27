import copy
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import requests

from scripts.github import github_client as gh


class _FakeResponse:
    def __init__(self, status_code: int, payload):
        self.status_code = status_code
        self._payload = payload
        self.headers = {}

    def json(self):
        return self._payload


def _graphql_public_repository(name: str) -> dict:
    return {
        "name": name,
        "owner": {"login": gh.USERNAME},
        "visibility": "PUBLIC",
        "isPrivate": False,
        "isFork": False,
        "description": "repository fixture",
        "url": f"https://github.com/{gh.USERNAME}/{name}",
        "pushedAt": "2026-08-26T00:00:00Z",
        "createdAt": "2026-01-01T00:00:00Z",
        "stargazerCount": 0,
        "forkCount": 0,
        "primaryLanguage": {"name": "Python"},
        "defaultBranchRef": None,
        "workflowsDir": None,
        "languages": {
            "pageInfo": {"hasNextPage": False, "endCursor": None},
            "edges": [],
        },
    }


def _graphql_repository_page(nodes: list[object]) -> dict:
    return {
        "user": {
            "repositories": {
                "totalCount": len(nodes),
                "pageInfo": {"hasNextPage": False, "endCursor": None},
                "nodes": copy.deepcopy(nodes),
            }
        }
    }


def _rest_public_repository(name: str) -> dict:
    return {
        "name": name,
        "owner": {"login": gh.USERNAME},
        "visibility": "public",
        "private": False,
        "fork": False,
    }


def _graphql_private_repository(
    name: str,
    *,
    language: str = "Python",
    language_bytes: int = 100,
) -> dict:
    repository = _graphql_public_repository(name)
    repository.update(
        {
            "visibility": "PRIVATE",
            "isPrivate": True,
            "languages": {
                "pageInfo": {"hasNextPage": False, "endCursor": None},
                "edges": [
                    {
                        "size": language_bytes,
                        "node": {"name": language},
                    }
                ]
            },
        }
    )
    return repository


def _graphql_paginated_repository_page(
    nodes: list[object],
    *,
    total_count: int,
    has_next_page: bool,
    end_cursor: str | None,
) -> dict:
    return {
        "user": {
            "repositories": {
                "totalCount": total_count,
                "pageInfo": {
                    "hasNextPage": has_next_page,
                    "endCursor": end_cursor,
                },
                "nodes": copy.deepcopy(nodes),
            }
        }
    }


def _provider_observation_accepted(observation: dict) -> bool:
    validator = next(
        (
            function
            for function in (
                getattr(gh, "validate_provider_observation", None),
                getattr(gh, "_validate_provider_observation", None),
            )
            if callable(function)
        ),
        None,
    )
    if validator is None:
        return False
    try:
        result = validator(copy.deepcopy(observation))
    except (TypeError, ValueError, RuntimeError):
        return False
    return result is not False


def _events_observation(*, per_page: int, max_pages: int) -> dict:
    getter = next(
        (
            function
            for function in (
                getattr(gh, "get_events_observation", None),
                getattr(gh, "get_recent_public_events_observation", None),
            )
            if callable(function)
        ),
        None,
    )
    if getter is not None:
        return getter(per_page=per_page, max_pages=max_pages)

    rows = gh.get_events(per_page=per_page, max_pages=max_pages)
    return {
        "schema": "legacy-unqualified-events",
        "metric_id": "recent_public_events",
        "source_metric_id": "github_public_event_metadata_rows",
        "value": rows,
        "status": "ok",
        "complete": True,
        "population_id": "public-user-events-feed",
        "population_signature": None,
        "window_start": None,
        "window_end": None,
        "observed_at": None,
        "source_id": "github_rest_public_events",
        "source_mode": "cache",
        "completion_reason": "legacy_unqualified",
    }


def _merged_pr_observation(*, days: int) -> dict:
    getter = next(
        (
            function
            for function in (
                getattr(gh, "get_merged_prs_last_n_days_observation", None),
                getattr(gh, "get_merged_pr_observation", None),
            )
            if callable(function)
        ),
        None,
    )
    if getter is not None:
        return getter(days=days)

    value = gh.get_merged_prs_last_n_days(days=days)
    return {
        "schema": "legacy-unqualified-pr-total",
        "metric_id": "prs_merged",
        "source_metric_id": "merged_prs_primary_visible_population",
        "value": value,
        "status": "ok" if value is not None else "unavailable",
        "complete": value is not None,
        "population_id": "owned-repositories-visible-to-primary-pr-search",
        "population_signature": None,
        "window_start": None,
        "window_end": None,
        "observed_at": None,
        "source_id": "github_rest_merged_pr_search_primary",
        "source_mode": "live",
        "completion_reason": "all_components_observed" if value is not None else "unavailable",
    }


def _provider_observation(
    *,
    metric_id: str,
    source_metric_id: str,
    value,
    status: str,
    complete: bool,
    population_id: str,
    population_signature: str | None,
    window_start: str | None,
    window_end: str | None,
    observed_at: str | None,
    source_id: str,
    source_mode: str,
    completion_reason: str,
) -> dict:
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


def _observe_missing_workflow_directory_from_rest_listing(
    repository: str,
    rows: list[object],
) -> dict:
    writes = []

    def record_write(key, value):
        writes.append((key, copy.deepcopy(value)))

    with patch.object(gh, "TOKEN", "test-token"), patch.object(
        gh, "_get_cached", return_value=None
    ), patch.object(
        gh, "_set_cached", side_effect=record_write
    ), patch.object(
        gh, "_graphql_query", side_effect=RuntimeError("GraphQL unavailable")
    ) as graphql_query, patch.object(
        gh, "paginated_get", return_value=copy.deepcopy(rows)
    ) as rest_listing, patch.object(
        gh, "_request_with_retry", return_value=_FakeResponse(404, {})
    ), patch.object(
        gh,
        "_request_public_with_retry",
        side_effect=AssertionError("public retry should not be needed"),
    ):
        observation = gh.get_repo_workflow_observation(gh.USERNAME, repository)

    return {
        "observation": observation,
        "writes": writes,
        "graphql_calls": graphql_query.call_count,
        "rest_listing_calls": rest_listing.call_count,
    }


class GitHubClientTests(unittest.TestCase):
    def test_graphql_repository_listing_requires_explicit_public_identity(self):
        repository = "identity-fields-target"
        valid = _graphql_public_repository(repository)
        cases = {}
        for field in ("owner", "visibility", "isPrivate", "isFork"):
            cases[f"missing-{field}"] = {
                key: copy.deepcopy(value)
                for key, value in valid.items()
                if key != field
            }
        cases.update(
            {
                "empty-owner": {**copy.deepcopy(valid), "owner": {}},
                "numeric-visibility": {
                    **copy.deepcopy(valid),
                    "visibility": 7,
                },
                "string-private": {
                    **copy.deepcopy(valid),
                    "isPrivate": "false",
                },
                "string-fork": {
                    **copy.deepcopy(valid),
                    "isFork": "false",
                },
                "different-owner": {
                    **copy.deepcopy(valid),
                    "owner": {"login": "another-owner"},
                },
                "private-visibility": {
                    **copy.deepcopy(valid),
                    "visibility": "PRIVATE",
                },
                "private-flag": {
                    **copy.deepcopy(valid),
                    "isPrivate": True,
                },
                "fork-flag": {
                    **copy.deepcopy(valid),
                    "isFork": True,
                },
            }
        )

        violations = {}
        for case_name, node in cases.items():
            writes = []
            with patch.object(gh, "_get_cached", return_value=None), patch.object(
                gh, "_set_cached", side_effect=lambda key, value: writes.append((key, value))
            ), patch.object(
                gh, "_graphql_query", return_value=_graphql_repository_page([node])
            ):
                try:
                    returned = gh._graphql_public_owned_repos(False)
                except RuntimeError:
                    returned = None
                except Exception as exc:
                    violations[f"{case_name}:exception"] = type(exc).__name__
                    returned = None

            if returned is not None:
                violations[f"{case_name}:returned"] = [
                    {
                        "name": repo.get("name"),
                        "owner": repo.get("owner"),
                        "visibility": repo.get("visibility"),
                        "private": repo.get("private"),
                        "fork": repo.get("fork"),
                    }
                    for repo in returned
                ]
            if writes:
                violations[f"{case_name}:cache_writes"] = [key for key, _ in writes]

        self.assertEqual({}, violations)

    def test_graphql_repository_listing_accepts_explicit_public_identity(self):
        repository = "identity-fields-control"
        node = _graphql_public_repository(repository)
        writes = []

        with patch.object(gh, "_get_cached", return_value=None), patch.object(
            gh, "_set_cached", side_effect=lambda key, value: writes.append((key, value))
        ), patch.object(
            gh, "_graphql_query", return_value=_graphql_repository_page([node])
        ):
            repositories = gh._graphql_public_owned_repos(False)

        self.assertEqual([repository], [repo["name"] for repo in repositories])
        self.assertEqual("public", repositories[0]["visibility"])
        self.assertIs(repositories[0]["private"], False)
        self.assertIs(repositories[0]["fork"], False)
        self.assertEqual(1, len(writes))
        self.assertEqual("graphql_public_owned_repos_0", writes[0][0])

    def test_rest_fallback_rejects_conflicting_duplicate_repository_rows(self):
        repository = "duplicate-rest-listing-target"
        valid = _rest_public_repository(repository)
        conflicting = {
            **copy.deepcopy(valid),
            "visibility": "private",
            "private": True,
        }
        unknown = {
            "observed": False,
            "has_actions_config": None,
            "workflow_yaml_file_count": None,
            "unavailable_reason": "capability_unavailable",
        }

        for rows in ([valid, conflicting], [conflicting, valid]):
            with self.subTest(order=[row["visibility"] for row in rows]):
                result = _observe_missing_workflow_directory_from_rest_listing(
                    repository,
                    rows,
                )
                self.assertEqual(1, result["graphql_calls"])
                self.assertEqual(1, result["rest_listing_calls"])
                self.assertEqual(unknown, result["observation"])
                self.assertEqual([], result["writes"])

    def test_rest_fallback_accepts_one_explicit_public_repository_row(self):
        control = _observe_missing_workflow_directory_from_rest_listing(
            "unique-rest-listing-control",
            [_rest_public_repository("unique-rest-listing-control")],
        )
        self.assertEqual(
            {
                "observed": True,
                "has_actions_config": False,
                "workflow_yaml_file_count": 0,
                "unavailable_reason": None,
            },
            control["observation"],
        )
        self.assertEqual(1, len(control["writes"]))

    def test_rest_fallback_requires_complete_unique_public_identity_facts(self):
        valid = _rest_public_repository("rest-identity-control")
        malformed_rows = {}
        for field in ("name", "owner", "visibility", "private", "fork"):
            malformed_rows[f"missing-{field}"] = {
                key: copy.deepcopy(value)
                for key, value in valid.items()
                if key != field
            }
        malformed_rows.update(
            {
                "empty-name": {**copy.deepcopy(valid), "name": ""},
                "empty-owner": {**copy.deepcopy(valid), "owner": {}},
                "numeric-visibility": {
                    **copy.deepcopy(valid),
                    "visibility": 7,
                },
                "string-private": {
                    **copy.deepcopy(valid),
                    "private": "false",
                },
                "string-fork": {
                    **copy.deepcopy(valid),
                    "fork": "false",
                },
                "contradictory-private": {
                    **copy.deepcopy(valid),
                    "private": True,
                },
            }
        )

        def returned(rows):
            with patch.object(gh, "TOKEN", ""), patch.object(
                gh, "_get_cached", return_value=None
            ), patch.object(
                gh, "paginated_get", return_value=copy.deepcopy(rows)
            ):
                try:
                    return gh.get_repos(False)
                except RuntimeError:
                    return []

        for case_name, row in malformed_rows.items():
            with self.subTest(case=case_name):
                self.assertEqual([], returned([row]))

        self.assertEqual([], returned([valid, copy.deepcopy(valid)]))
        self.assertEqual([valid], returned([valid]))
        self.assertEqual(
            [],
            returned(
                [
                    {
                        **copy.deepcopy(valid),
                        "visibility": "private",
                        "private": True,
                    }
                ]
            ),
        )

    def test_get_repos_rejects_invalid_cached_public_repository_lists(self):
        valid_cached = _rest_public_repository("valid-cached-control")
        private_cached = {
            **copy.deepcopy(valid_cached),
            "visibility": "private",
            "private": True,
        }
        off_owner_cached = {
            **copy.deepcopy(valid_cached),
            "owner": {"login": "another-owner"},
        }
        fork_cached = {**copy.deepcopy(valid_cached), "fork": True}
        invalid_caches = {
            "private": [private_cached],
            "off-owner": [off_owner_cached],
            "malformed": [{"name": "missing-identity-fields"}],
            "duplicate": [valid_cached, copy.deepcopy(valid_cached)],
            "fork": [fork_cached],
        }
        fallback_public = _rest_public_repository("fallback-public-control")
        fallback_private = {
            **_rest_public_repository("fallback-private-row"),
            "visibility": "private",
            "private": True,
        }

        for case_name, cached in invalid_caches.items():
            with self.subTest(case=case_name), patch.object(
                gh, "TOKEN", "test-token"
            ), patch.object(
                gh, "_get_cached", return_value=copy.deepcopy(cached)
            ), patch.object(
                gh,
                "_graphql_public_owned_repos",
                side_effect=RuntimeError("GraphQL unavailable"),
            ) as graphql_listing, patch.object(
                gh,
                "paginated_get",
                return_value=[
                    copy.deepcopy(fallback_private),
                    copy.deepcopy(fallback_public),
                ],
            ) as rest_listing:
                repositories = gh.get_repos(False)
                self.assertEqual([fallback_public], repositories)
                graphql_listing.assert_called_once_with(False)
                rest_listing.assert_called_once()

    def test_bare_cached_public_rows_do_not_bypass_the_provider(self):
        cached = [_rest_public_repository("bare-cache-row")]
        refreshed = [_rest_public_repository("provider-row")]

        with patch.object(
            gh, "_get_cached", return_value=copy.deepcopy(cached)
        ), patch.object(
            gh,
            "_graphql_public_owned_repos",
            return_value=copy.deepcopy(refreshed),
        ) as provider:
            repositories = gh.get_repos(False)

        self.assertEqual(refreshed, repositories)
        provider.assert_called_once_with(False)

    def test_complete_provider_cache_can_bypass_the_same_scoped_query(self):
        node = _graphql_public_repository("complete-cache-control")
        writes = []
        with patch.object(gh, "_get_cached", return_value=None), patch.object(
            gh,
            "_set_cached",
            side_effect=lambda key, value: writes.append((key, copy.deepcopy(value))),
        ), patch.object(
            gh, "_graphql_query", return_value=_graphql_repository_page([node])
        ):
            provider_rows = gh._graphql_public_owned_repos(False)

        self.assertEqual(1, len(writes))
        cached_payload = writes[0][1]
        with patch.object(
            gh, "_get_cached", return_value=copy.deepcopy(cached_payload)
        ), patch.object(
            gh,
            "_graphql_public_owned_repos",
            side_effect=AssertionError("complete same-scope cache should be used"),
        ), patch.object(
            gh,
            "paginated_get",
            side_effect=AssertionError("complete same-scope cache should be used"),
        ):
            cached_rows = gh.get_repos(False)

        self.assertEqual(provider_rows, cached_rows)

    def test_nonfork_cache_does_not_bypass_an_include_forks_query(self):
        node = _graphql_public_repository("nonfork-cache-control")
        writes = []
        with patch.object(gh, "_get_cached", return_value=None), patch.object(
            gh,
            "_set_cached",
            side_effect=lambda key, value: writes.append((key, copy.deepcopy(value))),
        ), patch.object(
            gh, "_graphql_query", return_value=_graphql_repository_page([node])
        ):
            gh._graphql_public_owned_repos(False)

        include_forks_rows = [_rest_public_repository("include-forks-provider-row")]
        with patch.object(
            gh, "_get_cached", return_value=copy.deepcopy(writes[0][1])
        ), patch.object(
            gh,
            "_graphql_public_owned_repos",
            return_value=copy.deepcopy(include_forks_rows),
        ) as provider:
            repositories = gh.get_repos(True)

        self.assertEqual(include_forks_rows, repositories)
        provider.assert_called_once_with(True)

    def test_language_connection_completeness_is_preserved_on_repository_rows(self):
        for privacy, node in (
            ("public", _graphql_public_repository("public-language-control")),
            ("private", _graphql_private_repository("private-language-control")),
        ):
            with self.subTest(privacy=privacy, state="complete"):
                normalized = gh._normalize_graphql_repo(copy.deepcopy(node))
                self.assertIs(normalized.get("language_bytes_complete"), True)

            truncated = copy.deepcopy(node)
            truncated["languages"]["pageInfo"] = {
                "hasNextPage": True,
                "endCursor": "next-language-page",
            }
            with self.subTest(privacy=privacy, state="truncated"):
                normalized = gh._normalize_graphql_repo(truncated)
                self.assertIs(normalized.get("language_bytes_complete"), False)

            missing = copy.deepcopy(node)
            missing["languages"].pop("pageInfo")
            with self.subTest(privacy=privacy, state="missing"):
                normalized = gh._normalize_graphql_repo(missing)
                self.assertIs(normalized.get("language_bytes_complete"), False)

    def test_language_queries_request_connection_completeness(self):
        public_node = _graphql_public_repository("public-language-query")
        private_node = _graphql_private_repository("private-language-query")
        cases = (
            (
                "public",
                lambda: gh._graphql_public_owned_repos(False),
                _graphql_repository_page([public_node]),
            ),
            (
                "private",
                lambda: gh._graphql_private_owned_repos(limit=40),
                _graphql_paginated_repository_page(
                    [private_node],
                    total_count=1,
                    has_next_page=False,
                    end_cursor=None,
                ),
            ),
        )

        for privacy, fetch, response in cases:
            with self.subTest(privacy=privacy), patch.object(
                gh, "TOKEN", "test-token"
            ), patch.object(
                gh, "_get_cached", return_value=None
            ), patch.object(
                gh, "_set_cached"
            ), patch.object(
                gh, "_graphql_query", return_value=response
            ) as graphql_query:
                fetch()

            query = graphql_query.call_args.args[0]
            language_clause = query.split("languages(first:", 1)[1]
            self.assertIn("pageInfo", language_clause)

    def test_private_repository_inventory_paginates_to_reported_cardinality(self):
        first_page_nodes = [
            _graphql_private_repository(f"private-repository-{index:02d}")
            for index in range(40)
        ]
        final_node = _graphql_private_repository(
            "private-repository-40",
            language="Rust",
            language_bytes=4096,
        )
        pages = [
            _graphql_paginated_repository_page(
                first_page_nodes,
                total_count=41,
                has_next_page=True,
                end_cursor="private-page-40",
            ),
            _graphql_paginated_repository_page(
                [final_node],
                total_count=41,
                has_next_page=False,
                end_cursor=None,
            ),
        ]
        writes = []

        with patch.object(gh, "TOKEN", "test-token"), patch.object(
            gh, "_get_cached", return_value=None
        ), patch.object(
            gh,
            "_set_cached",
            side_effect=lambda key, value: writes.append((key, copy.deepcopy(value))),
        ), patch.object(
            gh, "_graphql_query", side_effect=copy.deepcopy(pages)
        ) as graphql_query:
            repositories = gh._graphql_private_owned_repos(limit=40)

        self.assertEqual(41, len(repositories))
        self.assertEqual(2, graphql_query.call_count)
        query = graphql_query.call_args_list[0].args[0]
        self.assertIn("after: $cursor", query)
        self.assertIn("totalCount", query)
        self.assertIn("pageInfo", query)
        self.assertIn("languages(first:", query)
        first_variables = graphql_query.call_args_list[0].args[1]
        second_variables = graphql_query.call_args_list[1].args[1]
        self.assertIsNone(first_variables["cursor"])
        self.assertEqual("private-page-40", second_variables["cursor"])
        self.assertEqual({"Rust": 4096}, repositories[-1]["language_bytes"])
        self.assertTrue(
            all(
                repository["owner"]["login"] == gh.USERNAME
                and repository["visibility"] == "private"
                and repository["private"] is True
                and repository["fork"] is False
                for repository in repositories
            )
        )
        self.assertEqual(
            [("graphql_private_owned_repos_40", repositories)],
            writes,
        )

    def test_private_repository_inventory_rejects_untrusted_later_pages(self):
        first_node = _graphql_private_repository("first-private-repository")
        valid_second = _graphql_private_repository("second-private-repository")
        duplicate_second = copy.deepcopy(first_node)
        malformed_second = {"name": "missing-private-identity"}
        public_second = {
            **copy.deepcopy(valid_second),
            "visibility": "PUBLIC",
            "isPrivate": False,
        }
        off_owner_second = {
            **copy.deepcopy(valid_second),
            "owner": {"login": "another-owner"},
        }
        fork_second = {**copy.deepcopy(valid_second), "isFork": True}
        cases = {
            "duplicate": ([duplicate_second], 2),
            "malformed": ([malformed_second], 2),
            "public": ([public_second], 2),
            "off-owner": ([off_owner_second], 2),
            "fork": ([fork_second], 2),
            "incomplete-cardinality": ([valid_second], 3),
        }

        for case_name, (second_nodes, total_count) in cases.items():
            pages = [
                _graphql_paginated_repository_page(
                    [first_node],
                    total_count=total_count,
                    has_next_page=True,
                    end_cursor="next-private-page",
                ),
                _graphql_paginated_repository_page(
                    second_nodes,
                    total_count=total_count,
                    has_next_page=False,
                    end_cursor=None,
                ),
            ]
            writes = []
            with self.subTest(case=case_name), patch.object(
                gh, "TOKEN", "test-token"
            ), patch.object(
                gh, "_get_cached", return_value=None
            ), patch.object(
                gh,
                "_set_cached",
                side_effect=lambda key, value: writes.append((key, value)),
            ), patch.object(
                gh, "_graphql_query", side_effect=copy.deepcopy(pages)
            ) as graphql_query:
                with self.assertRaises(RuntimeError):
                    gh._graphql_private_owned_repos(limit=40)
                self.assertEqual(2, graphql_query.call_count)
                self.assertEqual([], writes)

    def test_private_repository_inventory_accepts_exact_one_page_control(self):
        node = _graphql_private_repository(
            "one-page-private-control",
            language="TypeScript",
            language_bytes=2048,
        )
        page = _graphql_paginated_repository_page(
            [node],
            total_count=1,
            has_next_page=False,
            end_cursor=None,
        )
        writes = []

        with patch.object(gh, "TOKEN", "test-token"), patch.object(
            gh, "_get_cached", return_value=None
        ), patch.object(
            gh,
            "_set_cached",
            side_effect=lambda key, value: writes.append((key, copy.deepcopy(value))),
        ), patch.object(
            gh, "_graphql_query", return_value=page
        ) as graphql_query:
            repositories = gh._graphql_private_owned_repos(limit=40)

        self.assertEqual(1, graphql_query.call_count)
        self.assertEqual("one-page-private-control", repositories[0]["name"])
        self.assertEqual("private", repositories[0]["visibility"])
        self.assertIs(repositories[0]["private"], True)
        self.assertIs(repositories[0]["fork"], False)
        self.assertEqual({"TypeScript": 2048}, repositories[0]["language_bytes"])
        self.assertEqual(
            [("graphql_private_owned_repos_40", repositories)],
            writes,
        )

    def test_bare_cached_private_rows_do_not_bypass_the_provider(self):
        cached_row = gh._normalize_graphql_repo(
            _graphql_private_repository("bare-private-cache-row")
        )
        provider_node = _graphql_private_repository("provider-private-row")
        provider_page = _graphql_paginated_repository_page(
            [provider_node],
            total_count=1,
            has_next_page=False,
            end_cursor=None,
        )

        with patch.object(gh, "TOKEN", "test-token"), patch.object(
            gh, "token_mode_from_env", return_value="personal_github_token"
        ), patch.object(
            gh, "last_query_used_fallback_token", return_value=False
        ), patch.object(
            gh, "_get_cached", return_value=[copy.deepcopy(cached_row)]
        ), patch.object(
            gh, "_set_cached"
        ), patch.object(
            gh, "_graphql_query", return_value=provider_page
        ) as provider:
            repositories = gh._graphql_private_owned_repos(limit=40)

        self.assertEqual(["provider-private-row"], [row["name"] for row in repositories])
        provider.assert_called_once()

    def test_complete_private_cache_is_bound_to_scope_and_capability(self):
        node = _graphql_private_repository("private-cache-control")
        page = _graphql_paginated_repository_page(
            [node],
            total_count=1,
            has_next_page=False,
            end_cursor=None,
        )
        writes = []
        provider_context = (
            patch.object(gh, "TOKEN", "test-token"),
            patch.object(
                gh, "token_mode_from_env", return_value="personal_github_token"
            ),
            patch.object(gh, "last_query_used_fallback_token", return_value=False),
        )

        with provider_context[0], provider_context[1], provider_context[2], patch.object(
            gh, "_get_cached", return_value=None
        ), patch.object(
            gh,
            "_set_cached",
            side_effect=lambda key, value: writes.append((key, copy.deepcopy(value))),
        ), patch.object(
            gh, "_graphql_query", return_value=page
        ):
            provider_rows = gh._graphql_private_owned_repos(limit=40)

        self.assertEqual(1, len(writes))
        cache_key, envelope = writes[0]
        self.assertEqual("graphql_private_owned_repos_40", cache_key)
        self.assertIsInstance(envelope, dict)
        self.assertEqual("graphql-private-owned-repositories/v1", envelope.get("schema"))
        self.assertEqual(gh.USERNAME.casefold(), envelope.get("username"))
        self.assertEqual(40, envelope.get("limit"))
        self.assertIs(envelope.get("complete"), True)
        self.assertEqual(1, envelope.get("provider_total_count"))
        self.assertEqual(
            "personal_github_token",
            envelope.get("private_capability"),
        )
        self.assertEqual(provider_rows, envelope.get("repositories"))

        with patch.object(gh, "TOKEN", "test-token"), patch.object(
            gh, "token_mode_from_env", return_value="personal_github_token"
        ), patch.object(
            gh, "last_query_used_fallback_token", return_value=False
        ), patch.object(
            gh, "_get_cached", return_value=copy.deepcopy(envelope)
        ), patch.object(
            gh,
            "_graphql_query",
            side_effect=AssertionError("complete same-scope cache should be used"),
        ):
            cached_rows = gh._graphql_private_owned_repos(limit=40)

        self.assertEqual(provider_rows, cached_rows)

        mismatches = {
            "username": {**copy.deepcopy(envelope), "username": "another-owner"},
            "limit": {**copy.deepcopy(envelope), "limit": 20},
            "total": {**copy.deepcopy(envelope), "provider_total_count": 2},
            "complete": {**copy.deepcopy(envelope), "complete": False},
            "capability": {
                **copy.deepcopy(envelope),
                "private_capability": "github_token",
            },
        }
        for field, mismatched in mismatches.items():
            with self.subTest(field=field), patch.object(
                gh, "TOKEN", "test-token"
            ), patch.object(
                gh, "token_mode_from_env", return_value="personal_github_token"
            ), patch.object(
                gh, "last_query_used_fallback_token", return_value=False
            ), patch.object(
                gh, "_get_cached", return_value=mismatched
            ), patch.object(
                gh, "_set_cached"
            ), patch.object(
                gh, "_graphql_query", return_value=page
            ) as provider:
                gh._graphql_private_owned_repos(limit=40)
            provider.assert_called_once()

    def test_paginated_get_discards_a_partial_listing_after_later_page_failure(self):
        pages = [
            _FakeResponse(200, [{"id": 1}, {"id": 2}]),
            _FakeResponse(500, {"message": "synthetic failure"}),
        ]
        writes = []

        with patch.object(gh, "_get_cached", return_value=None), patch.object(
            gh,
            "_set_cached",
            side_effect=lambda key, value: writes.append((key, copy.deepcopy(value))),
        ), patch.object(
            gh, "_request_with_retry", side_effect=pages
        ) as provider:
            try:
                returned = gh.paginated_get("synthetic/items", per_page=2)
            except Exception:
                returned = None

        self.assertNotEqual([{"id": 1}, {"id": 2}], returned)
        self.assertEqual([], writes)
        self.assertEqual(2, provider.call_count)

    def test_bare_paginated_cache_cannot_hide_a_later_page_failure(self):
        legacy_partial = [{"id": "legacy-first-page"}]
        pages = [
            _FakeResponse(200, [{"id": 1}, {"id": 2}]),
            _FakeResponse(500, {"message": "synthetic later-page failure"}),
        ]
        writes = []

        with patch.object(
            gh, "_get_cached", return_value=copy.deepcopy(legacy_partial)
        ), patch.object(
            gh,
            "_set_cached",
            side_effect=lambda key, value: writes.append((key, copy.deepcopy(value))),
        ), patch.object(
            gh, "_request_with_retry", side_effect=pages
        ) as provider:
            with self.assertRaises(RuntimeError):
                gh.paginated_get("synthetic/items", per_page=2)

        self.assertEqual(2, provider.call_count)
        self.assertEqual([], writes)

    def test_paginated_get_caches_only_a_complete_listing(self):
        pages = [
            _FakeResponse(200, [{"id": 1}, {"id": 2}]),
            _FakeResponse(200, [{"id": 3}]),
        ]
        request_params = {"state": "open"}
        writes = []

        with patch.object(gh, "_get_cached", return_value=None), patch.object(
            gh,
            "_set_cached",
            side_effect=lambda key, value: writes.append((key, copy.deepcopy(value))),
        ), patch.object(gh, "_request_with_retry", side_effect=pages) as provider:
            returned = gh.paginated_get(
                "synthetic/items",
                params=request_params,
                per_page=2,
            )

        self.assertEqual([{"id": 1}, {"id": 2}, {"id": 3}], returned)
        self.assertEqual(1, len(writes))
        self.assertEqual(2, provider.call_count)
        cache_key, envelope = writes[0]
        self.assertEqual(
            'paginated_synthetic/items_{"state": "open"}',
            cache_key,
        )
        self.assertEqual(
            {
                "schema": "rest-pagination/v1",
                "endpoint": "synthetic/items",
                "params": request_params,
                "per_page": 2,
                "complete": True,
                "pages_fetched": 2,
                "results": returned,
            },
            envelope,
        )

        with patch.object(
            gh, "_get_cached", return_value=copy.deepcopy(envelope)
        ), patch.object(
            gh,
            "_request_with_retry",
            side_effect=AssertionError("complete same-scope cache should be reused"),
        ) as replay_provider:
            replayed = gh.paginated_get(
                "synthetic/items",
                params=request_params,
                per_page=2,
            )

        self.assertEqual(returned, replayed)
        replay_provider.assert_not_called()

    def test_population_free_language_cache_cannot_replace_current_rows(self):
        repositories = [
            {
                "name": "current-public",
                "owner": {"login": gh.USERNAME},
                "visibility": "public",
                "private": False,
                "fork": False,
                "language_bytes": {"Python": 1200},
                "language_bytes_complete": True,
            },
            {
                "name": "current-private",
                "owner": {"login": gh.USERNAME},
                "visibility": "private",
                "private": True,
                "fork": False,
                "language_bytes": {"Rust": 800},
                "language_bytes_complete": True,
            },
        ]
        stale_population_free_cache = {"StaleLanguage": 9999}

        with patch.object(
            gh,
            "_get_cached",
            return_value=copy.deepcopy(stale_population_free_cache),
        ), patch.object(gh, "_set_cached"):
            totals = gh.get_all_languages(copy.deepcopy(repositories))

        self.assertEqual({"Python": 1200, "Rust": 800}, totals)

    def test_get_releases_last_n_days_counts_recent_releases(self):
        now = datetime.now(timezone.utc)
        recent = (now - timedelta(days=2)).isoformat().replace("+00:00", "Z")
        old = (now - timedelta(days=45)).isoformat().replace("+00:00", "Z")
        repos = [{"owner": {"login": "jguida941"}, "name": "voiceterm"}]

        with patch("scripts.github.github_client._get_cached", return_value=None), patch(
            "scripts.github.github_client._set_cached",
        ), patch(
            "scripts.github.github_client._request_with_retry",
            return_value=_FakeResponse(200, [{"published_at": recent}, {"published_at": old}]),
        ):
            total = gh.get_releases_last_n_days(repos=repos, days=30, max_workers=1)

        self.assertEqual(total, 1)

    def test_get_owned_repo_scope_counts_masks_private_zero_for_default_token(self):
        payload = {
            "user": {
                "publicOwned": {"totalCount": 66},
                "publicOwnedForks": {"totalCount": 4},
                "publicOwnedNonFork": {"totalCount": 62},
                "privateOwned": {"totalCount": 0},
            }
        }

        with patch("scripts.github.github_client.TOKEN", "x"), patch(
            "scripts.github.github_client._get_cached",
            return_value=None,
        ), patch(
            "scripts.github.github_client._set_cached",
        ), patch(
            "scripts.github.github_client._graphql_query",
            return_value=payload,
        ), patch(
            "scripts.github.github_client.token_mode_from_env",
            return_value="github_token",
        ):
            counts = gh.get_owned_repo_scope_counts()

        self.assertEqual(counts["public_owned_nonfork"], 62)
        self.assertIsNone(counts["private_owned"])

    def test_get_merged_prs_last_n_days_returns_total(self):
        with patch("scripts.github.github_client._get_cached", return_value=None), patch(
            "scripts.github.github_client._set_cached",
        ), patch(
            "scripts.github.github_client._calendar_window",
            return_value=(
                datetime(2025, 3, 6, tzinfo=timezone.utc),
                datetime(2026, 3, 6, tzinfo=timezone.utc),
                "2026-03-06",
            ),
        ), patch(
            "scripts.github.github_client._request_with_retry",
            return_value=_FakeResponse(200, {"total_count": 42}),
        ):
            total = gh.get_merged_prs_last_n_days(days=365)

        self.assertEqual(total, 42)

    def test_get_contribution_calendar_uses_aligned_window(self):
        start = datetime(2026, 3, 1, 0, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 3, 6, 23, 59, 59, tzinfo=timezone.utc)
        graphql_payload = {
            "data": {
                "user": {
                    "contributionsCollection": {
                        "contributionCalendar": {
                            "totalContributions": 4288,
                            "weeks": [],
                        }
                    }
                }
            }
        }

        with patch("scripts.github.github_client._get_cached", return_value=None), patch(
            "scripts.github.github_client._set_cached",
        ), patch(
            "scripts.github.github_client._calendar_window",
            return_value=(start, end, "2026-03-06"),
        ), patch(
            "scripts.github.github_client.requests.post",
            return_value=_FakeResponse(200, graphql_payload),
        ) as post_mock:
            calendar = gh.get_contribution_calendar(days=365)

        self.assertEqual(calendar["totalContributions"], 4288)
        call_kwargs = post_mock.call_args.kwargs
        variables = call_kwargs["json"]["variables"]
        self.assertEqual(variables["from"], "2026-03-01T00:00:00Z")
        self.assertEqual(variables["to"], "2026-03-06T23:59:59Z")

    def test_partial_event_page_preserves_safe_rows_without_complete_cache(self):
        occurred_at = "2026-08-26T14:30:00Z"
        raw_event = {
            "id": "event-101",
            "type": "PushEvent",
            "actor": {"login": gh.USERNAME},
            "repo": {"name": f"{gh.USERNAME}/public-service"},
            "created_at": occurred_at,
            "payload": {
                "commits": [
                    {
                        "message": "Publish the provider metric\nimplementation details",
                        "sha": "f" * 40,
                    }
                ],
                "body": "implementation details that are not repository metadata",
            },
        }
        writes = []
        pages = [
            _FakeResponse(200, [raw_event]),
            _FakeResponse(500, {"message": "later page unavailable"}),
        ]

        with patch.object(gh, "_get_cached", return_value=None), patch.object(
            gh,
            "_set_cached",
            side_effect=lambda key, value: writes.append((key, copy.deepcopy(value))),
        ), patch.object(gh, "_request_with_retry", side_effect=pages) as provider:
            observation = _events_observation(per_page=1, max_pages=3)

        expected_row = {
            "event_id": "event-101",
            "event_type": "PushEvent",
            "repo_full_name": f"{gh.USERNAME}/public-service",
            "repo_url": f"https://github.com/{gh.USERNAME}/public-service",
            "actor_login": gh.USERNAME,
            "occurred_at": occurred_at,
            "is_private": False,
            "source_id": "github_rest_public_events",
            "evidence_status": "partial",
            "commit_headlines": ("Publish the provider metric",),
        }
        observed_rows = observation.get("value") if isinstance(observation, dict) else None
        observed_row = observed_rows[0] if isinstance(observed_rows, (list, tuple)) and observed_rows else {}
        if isinstance(observed_row, dict) and isinstance(observed_row.get("commit_headlines"), list):
            observed_row = {**observed_row, "commit_headlines": tuple(observed_row["commit_headlines"])}

        with self.subTest(assertion="typed partial result"):
            self.assertEqual("partial", observation.get("status"))
            self.assertIs(observation.get("complete"), False)
            self.assertEqual("page_error", observation.get("completion_reason"))
        with self.subTest(assertion="safe first-page metadata"):
            self.assertEqual(expected_row, observed_row)
        with self.subTest(assertion="no complete cache"):
            self.assertEqual([], writes)
        with self.subTest(assertion="later page was attempted"):
            self.assertEqual(2, provider.call_count)

    def test_event_terminal_and_provider_cap_controls_remain_complete(self):
        terminal_event = {
            "id": "event-terminal",
            "type": "PushEvent",
            "actor": {"login": gh.USERNAME},
            "repo": {"name": f"{gh.USERNAME}/terminal-control"},
            "created_at": "2026-08-26T12:00:00Z",
            "payload": {"commits": [{"message": "Terminal control"}]},
        }
        capped_events = [
            {**copy.deepcopy(terminal_event), "id": "event-cap-1"},
            {**copy.deepcopy(terminal_event), "id": "event-cap-2"},
        ]

        cases = {
            "short terminal page": {
                "per_page": 2,
                "max_pages": 3,
                "pages": [_FakeResponse(200, [terminal_event])],
                "expected_rows": 1,
                "expected_calls": 1,
            },
            "provider cap": {
                "per_page": 1,
                "max_pages": 2,
                "pages": [
                    _FakeResponse(200, [capped_events[0]]),
                    _FakeResponse(200, [capped_events[1]]),
                ],
                "expected_rows": 2,
                "expected_calls": 2,
            },
        }
        for name, case in cases.items():
            writes = []
            with self.subTest(case=name), patch.object(
                gh, "_get_cached", return_value=None
            ), patch.object(
                gh,
                "_set_cached",
                side_effect=lambda key, value: writes.append((key, copy.deepcopy(value))),
            ), patch.object(
                gh, "_request_with_retry", side_effect=case["pages"]
            ) as provider:
                rows = gh.get_events(
                    per_page=case["per_page"],
                    max_pages=case["max_pages"],
                )

            self.assertEqual(case["expected_rows"], len(rows))
            self.assertEqual(case["expected_calls"], provider.call_count)
            self.assertEqual(1, len(writes))

    def test_incomplete_event_caches_do_not_bypass_current_provider(self):
        raw_event = {
            "id": "event-current",
            "type": "PushEvent",
            "actor": {"login": gh.USERNAME},
            "repo": {"name": f"{gh.USERNAME}/current-events"},
            "created_at": "2026-08-26T13:00:00Z",
            "payload": {"commits": [{"message": "Current event"}]},
        }
        partial_row = {
            "event_id": "event-stale",
            "event_type": "PushEvent",
            "repo_full_name": f"{gh.USERNAME}/stale-events",
            "repo_url": f"https://github.com/{gh.USERNAME}/stale-events",
            "actor_login": gh.USERNAME,
            "occurred_at": "2026-08-25T13:00:00Z",
            "is_private": False,
            "source_id": "github_rest_public_events",
            "evidence_status": "partial",
            "commit_headlines": ["Stale partial event"],
        }
        invalid_caches = {
            "bare rows": [raw_event],
            "incomplete envelope": _provider_observation(
                metric_id="recent_public_events",
                source_metric_id="github_public_event_metadata_rows",
                value=[partial_row],
                status="partial",
                complete=False,
                population_id="public-user-events-feed",
                population_signature=f"{gh.USERNAME}:2:2:300",
                window_start=None,
                window_end=None,
                observed_at="2026-08-25T13:05:00Z",
                source_id="github_rest_public_events",
                source_mode="live",
                completion_reason="page_error",
            ),
        }

        for name, cached in invalid_caches.items():
            with self.subTest(cache=name), patch.object(
                gh, "_get_cached", return_value=copy.deepcopy(cached)
            ), patch.object(gh, "_set_cached"), patch.object(
                gh, "_request_with_retry", return_value=_FakeResponse(200, [raw_event])
            ) as provider:
                returned = gh.get_events(per_page=2, max_pages=2)

            self.assertEqual(1, provider.call_count)
            self.assertNotEqual(cached, returned)

    def test_broad_commit_fallback_never_becomes_the_exact_repository_total(self):
        repositories = [
            {
                "owner": {"login": gh.USERNAME},
                "name": "known-commits",
                "visibility": "public",
                "private": False,
                "fork": False,
            },
            {
                "owner": {"login": gh.USERNAME},
                "name": "unknown-commits",
                "visibility": "public",
                "private": False,
                "fork": False,
            },
        ]
        writes = []

        def commit_count(_owner, name):
            return 4 if name == "known-commits" else None

        with patch.object(gh, "_get_cached", return_value=None), patch.object(
            gh,
            "_set_cached",
            side_effect=lambda key, value: writes.append((key, copy.deepcopy(value))),
        ), patch.object(
            gh, "get_repo_user_commit_count", side_effect=commit_count
        ), patch.object(
            gh, "get_total_commit_contributions_via_graphql", return_value=999
        ), patch.object(
            gh,
            "get_contribution_calendar",
            side_effect=AssertionError("the first fallback already returned a value"),
        ):
            exact_total = gh.get_total_commits(
                repositories,
                max_workers=1,
                use_global_fallback=True,
            )

        with self.subTest(assertion="exact compatibility result"):
            self.assertIsNone(exact_total)
        with self.subTest(assertion="degraded cache cannot claim exactness"):
            fallback_writes = [
                payload
                for _key, payload in writes
                if isinstance(payload, dict)
                and (payload.get("total") == 999 or payload.get("value") == 999)
            ]
            self.assertTrue(fallback_writes)
            self.assertTrue(
                all(payload.get("status") == "fallback" for payload in fallback_writes)
            )

    def test_exact_and_empty_commit_populations_remain_exact_controls(self):
        repositories = [
            {"owner": {"login": gh.USERNAME}, "name": "one"},
            {"owner": {"login": gh.USERNAME}, "name": "two"},
        ]
        with patch.object(gh, "_get_cached", return_value=None), patch.object(
            gh, "_set_cached"
        ), patch.object(
            gh,
            "get_repo_user_commit_count",
            side_effect=lambda _owner, name: {"one": 2, "two": 3}[name],
        ), patch.object(
            gh,
            "get_total_commit_contributions_via_graphql",
            side_effect=AssertionError("exact repository counts need no broad fallback"),
        ):
            exact_total = gh.get_total_commits(
                repositories,
                max_workers=1,
                use_global_fallback=True,
            )

        with patch.object(gh, "_get_cached", return_value=None), patch.object(
            gh, "_set_cached"
        ):
            empty_total = gh.get_total_commits([], max_workers=1, use_global_fallback=True)

        self.assertEqual(5, exact_total)
        self.assertEqual(0, empty_total)

    def test_unobserved_repository_commit_count_does_not_become_exact_zero(self):
        repositories = [
            {
                "owner": {"login": gh.USERNAME},
                "name": "not-observed",
                "visibility": "public",
                "private": False,
                "fork": False,
            }
        ]
        writes = []

        def http_error(status):
            response = requests.Response()
            response.status_code = status
            response.url = (
                f"https://api.github.com/repos/{gh.USERNAME}/not-observed/commits"
            )
            return requests.HTTPError(
                f"provider returned {status}", response=response
            )

        with patch.object(gh, "_get_cached", return_value=None), patch.object(
            gh,
            "_set_cached",
            side_effect=lambda key, value: writes.append(
                (key, copy.deepcopy(value))
            ),
        ), patch.object(
            gh, "paginated_get", side_effect=http_error(404)
        ), patch.object(
            gh,
            "_count_commits_from_commits_endpoint",
            side_effect=(http_error(404), http_error(404)),
        ) as commits_endpoint:
            observation = gh.get_total_commits_observation(
                repositories,
                max_workers=1,
                use_global_fallback=False,
            )

        exact_cache_keys = [
            key
            for key, _value in writes
            if key.startswith("repo_user_commits_v2_")
            or key.startswith("total_commits_observation_v1_")
        ]
        self.assertEqual(
            {
                "commit_endpoint_calls": 2,
                "value": None,
                "status": "unavailable",
                "complete": False,
                "exact_cache_keys": [],
            },
            {
                "commit_endpoint_calls": commits_endpoint.call_count,
                "value": observation.get("value"),
                "status": observation.get("status"),
                "complete": observation.get("complete"),
                "exact_cache_keys": exact_cache_keys,
            },
            "an unreadable repository is unknown and cannot mint exact component or aggregate cache entries",
        )

    def test_observed_and_empty_repository_commit_zero_remain_exact(self):
        repositories = [
            {
                "owner": {"login": gh.USERNAME},
                "name": "observed-zero",
                "visibility": "public",
                "private": False,
                "fork": False,
            }
        ]

        with patch.object(gh, "_get_cached", return_value=None), patch.object(
            gh, "_set_cached"
        ), patch.object(
            gh,
            "paginated_get",
            return_value=[{"login": gh.USERNAME, "contributions": 0}],
        ), patch.object(
            gh,
            "_count_commits_from_commits_endpoint",
            side_effect=AssertionError(
                "an explicit contributor zero needs no fallback"
            ),
        ):
            explicit_zero = gh.get_total_commits_observation(
                repositories,
                max_workers=1,
                use_global_fallback=False,
            )

        empty_response = requests.Response()
        empty_response.status_code = 409
        empty_response.url = (
            f"https://api.github.com/repos/{gh.USERNAME}/observed-zero/commits"
        )
        with patch.object(gh, "_get_cached", return_value=None), patch.object(
            gh, "_set_cached"
        ), patch.object(gh, "paginated_get", return_value=[]), patch.object(
            gh,
            "_count_commits_from_commits_endpoint",
            side_effect=requests.HTTPError(
                "empty repository", response=empty_response
            ),
        ) as commits_endpoint:
            empty_repository = gh.get_total_commits_observation(
                repositories,
                max_workers=1,
                use_global_fallback=False,
            )

        for source, observation in (
            ("explicit contributor zero", explicit_zero),
            ("empty repository", empty_repository),
        ):
            with self.subTest(source=source):
                self.assertEqual(0, observation.get("value"))
                self.assertEqual("ok", observation.get("status"))
                self.assertIs(observation.get("complete"), True)
        self.assertEqual(1, commits_endpoint.call_count)

    def test_release_cache_from_another_repository_population_is_not_reused(self):
        repositories = [
            {
                "owner": {"login": gh.USERNAME},
                "name": "population-a",
                "visibility": "public",
                "private": False,
                "fork": False,
            }
        ]
        wrong_population_cache = _provider_observation(
            metric_id="releases_30d",
            source_metric_id="owned_public_nonfork_releases",
            value=7,
            status="ok",
            complete=True,
            population_id="owned-public-nonfork-repositories",
            population_signature="population-b",
            window_start="2026-07-28T00:00:00Z",
            window_end="2026-08-26T23:59:59Z",
            observed_at="2026-08-26T23:59:59Z",
            source_id="github_rest_repo_releases",
            source_mode="cache",
            completion_reason="same_scope_cache",
        )

        with patch.object(
            gh, "_get_cached", return_value=copy.deepcopy(wrong_population_cache)
        ), patch.object(gh, "_set_cached"), patch.object(
            gh, "_count_repo_releases_since", return_value=None
        ), patch.object(
            gh, "_get_recent_release_cache", return_value=7, create=True
        ) as cross_population_lookup:
            total = gh.get_releases_last_n_days(
                repositories,
                days=30,
                max_workers=1,
            )

        self.assertIsNone(total)
        cross_population_lookup.assert_not_called()

    def test_live_release_total_remains_an_exact_control(self):
        repositories = [{"owner": {"login": gh.USERNAME}, "name": "population-a"}]
        with patch.object(gh, "_get_cached", return_value=None), patch.object(
            gh, "_set_cached"
        ), patch.object(gh, "_count_repo_releases_since", return_value=7):
            total = gh.get_releases_last_n_days(
                repositories,
                days=30,
                max_workers=1,
            )

        self.assertEqual(7, total)

    def test_prior_day_pr_cache_cannot_replace_the_current_rolling_window(self):
        current_window = (
            datetime(2025, 8, 27, tzinfo=timezone.utc),
            datetime(2026, 8, 26, tzinfo=timezone.utc),
            "2026-08-26",
        )
        stale_cache = {"total": None, "since": "2025-08-26"}
        with patch.object(gh, "TOKEN", ""), patch.object(
            gh, "_calendar_window", return_value=current_window
        ), patch.object(
            gh, "_get_cached", return_value=stale_cache
        ), patch.object(gh, "_set_cached"), patch.object(
            gh, "_get_recent_merged_pr_cache", return_value=41, create=True
        ) as prior_day_lookup, patch.object(
            gh, "_request_with_retry", return_value=_FakeResponse(500, {})
        ):
            total = gh.get_merged_prs_last_n_days(days=365)

        self.assertIsNone(total)
        prior_day_lookup.assert_not_called()

    def test_public_pr_retry_retains_its_fallback_population(self):
        current_window = (
            datetime(2025, 8, 27, tzinfo=timezone.utc),
            datetime(2026, 8, 26, tzinfo=timezone.utc),
            "2026-08-26",
        )
        writes = []
        with patch.object(gh, "TOKEN", "configured"), patch.object(
            gh, "_calendar_window", return_value=current_window
        ), patch.object(gh, "_get_cached", return_value=None), patch.object(
            gh,
            "_set_cached",
            side_effect=lambda key, value: writes.append((key, copy.deepcopy(value))),
        ), patch.object(
            gh, "_request_with_retry", return_value=_FakeResponse(403, {})
        ), patch.object(
            gh, "_request_public_with_retry", return_value=_FakeResponse(200, {"total_count": 23})
        ):
            observation = _merged_pr_observation(days=365)

        with self.subTest(assertion="fallback identity"):
            self.assertEqual("fallback", observation.get("status"))
            self.assertEqual(23, observation.get("value"))
            self.assertEqual(
                "merged_prs_public_visible_population",
                observation.get("source_metric_id"),
            )
            self.assertEqual(
                "owned-public-repositories-visible-to-public-pr-search",
                observation.get("population_id"),
            )
            self.assertEqual("public_retry", observation.get("completion_reason"))
        with self.subTest(assertion="window identity"):
            self.assertEqual("2025-08-27T00:00:00Z", observation.get("window_start"))
            self.assertEqual("2026-08-26T00:00:00Z", observation.get("window_end"))
        with self.subTest(assertion="no unqualified exact cache"):
            unqualified = [
                payload
                for _key, payload in writes
                if isinstance(payload, dict)
                and payload.get("total") == 23
                and payload.get("status") != "fallback"
            ]
            self.assertEqual([], unqualified)

    def test_bare_contribution_calendar_cache_does_not_gain_a_current_window(self):
        current_window = (
            datetime(2025, 8, 27, tzinfo=timezone.utc),
            datetime(2026, 8, 26, tzinfo=timezone.utc),
            "2026-08-26",
        )
        bare_calendar = {"totalContributions": 777, "weeks": []}
        with patch.object(gh, "_calendar_window", return_value=current_window), patch.object(
            gh, "_get_cached", return_value=copy.deepcopy(bare_calendar)
        ), patch.object(gh, "_set_cached"), patch.object(
            gh, "_graphql_query", return_value=None
        ) as provider:
            calendar = gh.get_contribution_calendar(days=365)

        self.assertIsNone(calendar)
        provider.assert_called_once()

    def test_provider_observation_contract_accepts_only_closed_value_families(self):
        observed_at = "2026-08-26T15:00:00Z"
        window_start = "2025-08-27T00:00:00Z"
        window_end = "2026-08-26T15:00:00Z"
        event_row = {
            "event_id": "event-valid",
            "event_type": "PushEvent",
            "repo_full_name": f"{gh.USERNAME}/provider-contract",
            "repo_url": f"https://github.com/{gh.USERNAME}/provider-contract",
            "actor_login": gh.USERNAME,
            "occurred_at": observed_at,
            "is_private": False,
            "source_id": "github_rest_public_events",
            "evidence_status": "ok",
            "commit_headlines": ("Validate provider metadata",),
        }
        exact_variants = {
            "commit exact": _provider_observation(
                metric_id="public_scope_commits",
                source_metric_id="owned_public_nonfork_authored_commits",
                value=0,
                status="ok",
                complete=True,
                population_id="owned-public-nonfork-repositories",
                population_signature="public-population-a",
                window_start=None,
                window_end=None,
                observed_at=observed_at,
                source_id="github_rest_repo_commits",
                source_mode="live",
                completion_reason="empty_population",
            ),
            "contributions exact": _provider_observation(
                metric_id="last_year_contributions",
                source_metric_id="github_contribution_calendar_total_and_days",
                value={
                    "total": 3,
                    "days": ({"date": "2026-08-26", "count": 3},),
                },
                status="ok",
                complete=True,
                population_id="github-contribution-calendar-visible-to-provider",
                population_signature=None,
                window_start=window_start,
                window_end=window_end,
                observed_at=observed_at,
                source_id="github_graphql_contribution_calendar",
                source_mode="live",
                completion_reason="all_components_observed",
            ),
            "release exact": _provider_observation(
                metric_id="releases_30d",
                source_metric_id="owned_public_nonfork_releases",
                value=2,
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
            "pull request exact": _provider_observation(
                metric_id="prs_merged",
                source_metric_id="merged_prs_primary_visible_population",
                value=4,
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
            "events terminal": _provider_observation(
                metric_id="recent_public_events",
                source_metric_id="github_public_event_metadata_rows",
                value=(event_row,),
                status="ok",
                complete=True,
                population_id="public-user-events-feed",
                population_signature=f"{gh.USERNAME}:100:3:300",
                window_start=None,
                window_end=None,
                observed_at=observed_at,
                source_id="github_rest_public_events",
                source_mode="live",
                completion_reason="terminal_page",
            ),
        }
        fallback_variants = {
            "commit fallback": _provider_observation(
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
            "previous contributions": _provider_observation(
                metric_id="last_year_contributions",
                source_metric_id="previous_profile_snapshot_contributions",
                value=777,
                status="fallback",
                complete=True,
                population_id="github-contribution-calendar-visible-to-provider",
                population_signature=None,
                window_start=None,
                window_end=None,
                observed_at="2026-08-25T15:00:00Z",
                source_id="previous_profile_snapshot",
                source_mode="previous_snapshot",
                completion_reason="previous_snapshot",
            ),
            "release event fallback": _provider_observation(
                metric_id="releases_30d",
                source_metric_id="public_release_events",
                value=1,
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
            "public pull request fallback": _provider_observation(
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
            "partial events": _provider_observation(
                metric_id="recent_public_events",
                source_metric_id="github_public_event_metadata_rows",
                value=({**event_row, "evidence_status": "partial"},),
                status="partial",
                complete=False,
                population_id="public-user-events-feed",
                population_signature=f"{gh.USERNAME}:100:3:300",
                window_start=None,
                window_end=None,
                observed_at=observed_at,
                source_id="github_rest_public_events",
                source_mode="live",
                completion_reason="page_error",
            ),
        }
        unavailable_templates = {
            name: {
                **copy.deepcopy(observation),
                "value": None,
                "status": "unavailable",
                "complete": False,
                "observed_at": None,
                "source_mode": "live",
                "completion_reason": "unavailable",
            }
            for name, observation in exact_variants.items()
        }

        for name, observation in {
            **exact_variants,
            **fallback_variants,
            **{f"{name} unavailable": value for name, value in unavailable_templates.items()},
        }.items():
            with self.subTest(variant=name):
                self.assertTrue(
                    _provider_observation_accepted(observation),
                    f"the provider contract rejected its {name} value shape",
                )

    def test_provider_observation_contract_rejects_open_or_misbound_values(self):
        valid = _provider_observation(
            metric_id="releases_30d",
            source_metric_id="owned_public_nonfork_releases",
            value=2,
            status="ok",
            complete=True,
            population_id="owned-public-nonfork-repositories",
            population_signature="public-population-a",
            window_start="2026-07-28T00:00:00Z",
            window_end="2026-08-26T15:00:00Z",
            observed_at="2026-08-26T15:00:00Z",
            source_id="github_rest_repo_releases",
            source_mode="live",
            completion_reason="all_components_observed",
        )
        valid_event = _provider_observation(
            metric_id="recent_public_events",
            source_metric_id="github_public_event_metadata_rows",
            value=(
                {
                    "event_id": "event-valid",
                    "event_type": "PushEvent",
                    "repo_full_name": f"{gh.USERNAME}/provider-contract",
                    "repo_url": f"https://github.com/{gh.USERNAME}/provider-contract",
                    "actor_login": gh.USERNAME,
                    "occurred_at": "2026-08-26T15:00:00Z",
                    "is_private": False,
                    "source_id": "github_rest_public_events",
                    "evidence_status": "ok",
                    "commit_headlines": ("Validate provider metadata",),
                },
            ),
            status="ok",
            complete=True,
            population_id="public-user-events-feed",
            population_signature=f"{gh.USERNAME}:100:3:300",
            window_start=None,
            window_end=None,
            observed_at="2026-08-26T15:00:00Z",
            source_id="github_rest_public_events",
            source_mode="live",
            completion_reason="terminal_page",
        )
        raw_event = copy.deepcopy(valid_event)
        raw_event["value"] = [
            {
                **copy.deepcopy(valid_event["value"][0]),
                "payload": {"commits": [{"message": "Provider body"}]},
            }
        ]
        extra_event_key = copy.deepcopy(valid_event)
        extra_event_key["value"] = [
            {**copy.deepcopy(valid_event["value"][0]), "body": "not metadata"}
        ]
        invalid_cases = {
            "boolean aggregate": {**copy.deepcopy(valid), "value": True},
            "negative aggregate": {**copy.deepcopy(valid), "value": -1},
            "missing required window": {**copy.deepcopy(valid), "window_start": None},
            "wrong population signature type": {
                **copy.deepcopy(valid),
                "population_signature": 7,
            },
            "unknown source metric": {
                **copy.deepcopy(valid),
                "source_metric_id": "nearby_release_total",
            },
            "extra envelope key": {**copy.deepcopy(valid), "unexpected": "field"},
            "complete flag contradicts status": {**copy.deepcopy(valid), "complete": False},
            "unavailable value is present": {
                **copy.deepcopy(valid),
                "status": "unavailable",
                "complete": False,
                "completion_reason": "unavailable",
            },
            "raw event payload": raw_event,
            "extra event body": extra_event_key,
            "private row in public event feed": {
                **copy.deepcopy(valid_event),
                "value": [{**copy.deepcopy(valid_event["value"][0]), "is_private": True}],
            },
        }

        for name, observation in invalid_cases.items():
            with self.subTest(case=name):
                self.assertFalse(
                    _provider_observation_accepted(observation),
                    f"the provider contract accepted {name}",
                )

    def test_exact_observations_bind_source_mode_to_current_evidence(self):
        observed_at = "2026-08-26T15:00:00Z"
        window_start = "2025-08-27T00:00:00Z"
        window_end = "2026-08-26T15:00:00Z"
        exact_variants = {
            "commits": (
                _provider_observation(
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
                "empty_population",
            ),
            "contributions": (
                _provider_observation(
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
                    window_start=window_start,
                    window_end=window_end,
                    observed_at=observed_at,
                    source_id="github_graphql_contribution_calendar",
                    source_mode="live",
                    completion_reason="all_components_observed",
                ),
                "all_components_observed",
            ),
            "releases": (
                _provider_observation(
                    metric_id="releases_30d",
                    source_metric_id="owned_public_nonfork_releases",
                    value=0,
                    status="ok",
                    complete=True,
                    population_id="owned-public-nonfork-repositories",
                    population_signature="none",
                    window_start="2026-07-28T00:00:00Z",
                    window_end=window_end,
                    observed_at=observed_at,
                    source_id="github_rest_repo_releases",
                    source_mode="live",
                    completion_reason="empty_population",
                ),
                "empty_population",
            ),
            "pull requests": (
                _provider_observation(
                    metric_id="prs_merged",
                    source_metric_id="merged_prs_primary_visible_population",
                    value=0,
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
                "all_components_observed",
            ),
            "events": (
                _provider_observation(
                    metric_id="recent_public_events",
                    source_metric_id="github_public_event_metadata_rows",
                    value=(),
                    status="ok",
                    complete=True,
                    population_id="public-user-events-feed",
                    population_signature=f"{gh.USERNAME}:100:3:300",
                    window_start=None,
                    window_end=None,
                    observed_at=observed_at,
                    source_id="github_rest_public_events",
                    source_mode="live",
                    completion_reason="terminal_page",
                ),
                "terminal_page",
            ),
        }

        for metric, (template, live_reason) in exact_variants.items():
            controls = {
                "live": {
                    **copy.deepcopy(template),
                    "source_mode": "live",
                    "completion_reason": live_reason,
                },
                "same-scope cache": {
                    **copy.deepcopy(template),
                    "source_mode": "cache",
                    "completion_reason": "same_scope_cache",
                },
            }
            for control, observation in controls.items():
                with self.subTest(metric=metric, control=control):
                    self.assertTrue(
                        _provider_observation_accepted(observation),
                        f"the exact {metric} {control} control was rejected",
                    )

            for source_mode in ("fallback", "previous_snapshot"):
                for completion_reason in (live_reason, "same_scope_cache"):
                    observation = {
                        **copy.deepcopy(template),
                        "source_mode": source_mode,
                        "completion_reason": completion_reason,
                    }
                    with self.subTest(
                        metric=metric,
                        source_mode=source_mode,
                        completion_reason=completion_reason,
                    ):
                        self.assertFalse(
                            _provider_observation_accepted(observation),
                            "an exact observation accepted fallback source identity",
                        )

    def test_degraded_observations_bind_source_mode_to_their_metric_family(self):
        observed_at = "2026-08-26T15:00:00Z"
        window_start = "2025-08-27T00:00:00Z"
        window_end = observed_at
        common = {
            "observed_at": observed_at,
        }
        event_row = {
            "event_id": "event-partial",
            "event_type": "PushEvent",
            "repo_full_name": f"{gh.USERNAME}/provider-contract",
            "repo_url": f"https://github.com/{gh.USERNAME}/provider-contract",
            "actor_login": gh.USERNAME,
            "occurred_at": observed_at,
            "is_private": False,
            "source_id": "github_rest_public_events",
            "evidence_status": "partial",
            "commit_headlines": ("Preserve observed metadata",),
        }
        families = {
            "commit fallback": (
                _provider_observation(
                    **common,
                    metric_id="public_scope_commits",
                    source_metric_id="github_total_commit_contributions",
                    value=999,
                    status="fallback",
                    complete=True,
                    population_id="github-user-contributions-visible-to-provider",
                    population_signature=None,
                    window_start=None,
                    window_end=None,
                    source_id="github_graphql_commit_contributions",
                    source_mode="fallback",
                    completion_reason="different_metric_fallback",
                ),
                {"fallback", "cache"},
            ),
            "release fallback": (
                _provider_observation(
                    **common,
                    metric_id="releases_30d",
                    source_metric_id="public_release_events",
                    value=2,
                    status="fallback",
                    complete=True,
                    population_id="public-user-events-feed",
                    population_signature=None,
                    window_start="2026-07-28T00:00:00Z",
                    window_end=window_end,
                    source_id="github_rest_public_events",
                    source_mode="fallback",
                    completion_reason="different_metric_fallback",
                ),
                {"fallback", "cache"},
            ),
            "public pull request retry": (
                _provider_observation(
                    **common,
                    metric_id="prs_merged",
                    source_metric_id="merged_prs_public_visible_population",
                    value=23,
                    status="fallback",
                    complete=True,
                    population_id=(
                        "owned-public-repositories-visible-to-public-pr-search"
                    ),
                    population_signature=None,
                    window_start=window_start,
                    window_end=window_end,
                    source_id="github_rest_merged_pr_search_public",
                    source_mode="fallback",
                    completion_reason="public_retry",
                ),
                {"fallback", "cache"},
            ),
            "previous contributions": (
                _provider_observation(
                    **common,
                    metric_id="last_year_contributions",
                    source_metric_id="previous_profile_snapshot_contributions",
                    value=777,
                    status="fallback",
                    complete=True,
                    population_id=(
                        "github-contribution-calendar-visible-to-provider"
                    ),
                    population_signature=None,
                    window_start=None,
                    window_end=None,
                    source_id="previous_profile_snapshot",
                    source_mode="previous_snapshot",
                    completion_reason="previous_snapshot",
                ),
                {"previous_snapshot"},
            ),
            "partial events": (
                _provider_observation(
                    **common,
                    metric_id="recent_public_events",
                    source_metric_id="github_public_event_metadata_rows",
                    value=(event_row,),
                    status="partial",
                    complete=False,
                    population_id="public-user-events-feed",
                    population_signature=f"{gh.USERNAME}:100:3:300",
                    window_start=None,
                    window_end=None,
                    source_id="github_rest_public_events",
                    source_mode="live",
                    completion_reason="page_error",
                ),
                {"live"},
            ),
        }

        for family, (template, accepted_modes) in families.items():
            for source_mode in ("live", "cache", "fallback", "previous_snapshot"):
                observation = {
                    **copy.deepcopy(template),
                    "source_mode": source_mode,
                }
                with self.subTest(family=family, source_mode=source_mode):
                    self.assertEqual(
                        source_mode in accepted_modes,
                        _provider_observation_accepted(observation),
                        f"{family} accepted a contradictory source mode",
                    )

    def test_legacy_component_commit_cache_cannot_mint_current_exact_provenance(self):
        repositories = [
            {
                "owner": {"login": gh.USERNAME},
                "name": "cached-component",
                "visibility": "public",
                "private": False,
                "fork": False,
            }
        ]

        def cached_value(key):
            if key.startswith("total_commits_observation_v1_"):
                return None
            if key.startswith("repo_user_commits_v2_"):
                return {"count": 3}
            return None

        with patch.object(gh, "_get_cached", side_effect=cached_value), patch.object(
            gh, "_set_cached"
        ), patch.object(gh, "paginated_get", return_value=[]), patch.object(
            gh, "_count_commits_from_commits_endpoint", return_value=None
        ):
            observation = gh.get_total_commits_observation(
                repositories,
                max_workers=1,
                use_global_fallback=False,
            )

        with self.subTest(assertion="no exact value"):
            self.assertIsNone(observation.get("value"))
        with self.subTest(assertion="no exact status"):
            self.assertEqual("unavailable", observation.get("status"))
        with self.subTest(assertion="no invented observation time"):
            self.assertIsNone(observation.get("observed_at"))

        class _FirstObservationTime(datetime):
            @classmethod
            def now(cls, tz=None):
                value = datetime(2026, 8, 25, 10, 11, 12, tzinfo=timezone.utc)
                return value.astimezone(tz) if tz is not None else value

        class _ReplayTime(datetime):
            @classmethod
            def now(cls, tz=None):
                value = datetime(2026, 8, 26, 15, 0, 0, tzinfo=timezone.utc)
                return value.astimezone(tz) if tz is not None else value

        writes = []
        with patch.object(gh, "datetime", _FirstObservationTime), patch.object(
            gh, "_get_cached", return_value=None
        ), patch.object(
            gh,
            "_set_cached",
            side_effect=lambda key, value: writes.append((key, copy.deepcopy(value))),
        ), patch.object(
            gh,
            "paginated_get",
            return_value=[{"login": gh.USERNAME, "contributions": 3}],
        ):
            live_observation = gh.get_total_commits_observation(
                repositories,
                max_workers=1,
                use_global_fallback=False,
            )

        component_payloads = [
            payload
            for key, payload in writes
            if key.startswith("repo_user_commits_v2_")
        ]
        self.assertEqual(1, len(component_payloads))

        def replay_cache(key):
            if key.startswith("total_commits_observation_v1_"):
                return None
            if key.startswith("repo_user_commits_v2_"):
                return copy.deepcopy(component_payloads[0])
            return None

        with patch.object(gh, "datetime", _ReplayTime), patch.object(
            gh, "_get_cached", side_effect=replay_cache
        ), patch.object(gh, "_set_cached"), patch.object(
            gh,
            "paginated_get",
            side_effect=AssertionError("the timestamped component cache should bypass the provider"),
        ):
            replay = gh.get_total_commits_observation(
                repositories,
                max_workers=1,
                use_global_fallback=False,
            )

        with self.subTest(assertion="timestamped component value remains exact"):
            self.assertEqual(3, replay.get("value"))
            self.assertEqual("ok", replay.get("status"))
        with self.subTest(assertion="component replay is identified as cache evidence"):
            self.assertEqual("cache", replay.get("source_mode"))
        with self.subTest(assertion="component replay has a same-scope cache reason"):
            self.assertEqual("same_scope_cache", replay.get("completion_reason"))
        with self.subTest(assertion="component replay preserves source time"):
            self.assertEqual(live_observation.get("observed_at"), replay.get("observed_at"))

    def test_timestamped_commit_cache_preserves_its_source_time(self):
        repositories = [
            {
                "owner": {"login": gh.USERNAME},
                "name": "cached-component",
                "visibility": "public",
                "private": False,
                "fork": False,
            }
        ]
        observed_at = "2026-08-25T10:11:12Z"
        cached_observation = _provider_observation(
            metric_id="public_scope_commits",
            source_metric_id="owned_public_nonfork_authored_commits",
            value=3,
            status="ok",
            complete=True,
            population_id="owned-public-nonfork-repositories",
            population_signature=gh._repo_signature(repositories),
            window_start=None,
            window_end=None,
            observed_at=observed_at,
            source_id="github_rest_repo_commits",
            source_mode="live",
            completion_reason="all_components_observed",
        )

        with patch.object(
            gh,
            "_get_cached",
            return_value=copy.deepcopy(cached_observation),
        ), patch.object(
            gh,
            "get_repo_user_commit_count",
            side_effect=AssertionError("the complete aggregate cache should bypass components"),
        ):
            replay = gh.get_total_commits_observation(
                repositories,
                max_workers=1,
                use_global_fallback=False,
            )

        self.assertEqual(3, replay.get("value"))
        self.assertEqual("ok", replay.get("status"))
        self.assertEqual("cache", replay.get("source_mode"))
        self.assertEqual("same_scope_cache", replay.get("completion_reason"))
        self.assertEqual(observed_at, replay.get("observed_at"))


if __name__ == "__main__":
    unittest.main()

import os
import unittest
from pathlib import Path
from unittest import mock

import requests

from scripts.github import github_client as gh
from scripts.github import github_graphql, github_transport
from scripts.core.settings import Settings


def _settings(tokens):
    return Settings(
        username="u",
        token=tokens[0] if tokens else "",
        cache_dir=Path("/tmp/x"),
        cache_ttl_seconds=0,
        bypass_cache=True,
        tokens=tuple(tokens),
    )


class _Resp:
    def __init__(self, status, json_data=None, *, headers=None):
        self.status_code = status
        self._json = json_data or {}
        self.headers = dict(headers or {})

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            err = requests.HTTPError(f"{self.status_code}")
            err.response = self
            raise err


class TransportFallbackTests(unittest.TestCase):
    def test_401_falls_back_to_next_token(self):
        seen = []

        def fake_get(url, headers=None, params=None):
            seen.append(headers.get("Authorization"))
            return _Resp(401) if "bad" in headers.get("Authorization", "") else _Resp(200)

        with mock.patch.object(github_transport.requests, "get", side_effect=fake_get):
            resp = github_transport.request_with_retry("https://x", _settings(["bad", "good"]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(seen, ["Bearer bad", "Bearer good"])

    def test_401_on_last_token_raises(self):
        def fake_get(url, headers=None, params=None):
            return _Resp(401)

        with mock.patch.object(github_transport.requests, "get", side_effect=fake_get):
            with self.assertRaises(requests.HTTPError):
                github_transport.request_with_retry("https://x", _settings(["bad"]))


class GraphqlFallbackTests(unittest.TestCase):
    def test_401_then_success(self):
        calls = []

        def fake_post(url, headers=None, json=None):
            calls.append(headers.get("Authorization"))
            if "bad" in headers.get("Authorization", ""):
                return _Resp(401)
            return _Resp(200, {"data": {"ok": True}})

        with mock.patch.object(github_graphql.requests, "post", side_effect=fake_post):
            data = github_graphql.graphql_query("q", {}, _settings(["bad", "good"]))
        self.assertEqual(data, {"ok": True})
        self.assertEqual(calls, ["Bearer bad", "Bearer good"])

    def test_401_only_returns_none(self):
        def fake_post(url, headers=None, json=None):
            return _Resp(401)

        with mock.patch.object(github_graphql.requests, "post", side_effect=fake_post):
            self.assertIsNone(github_graphql.graphql_query("q", {}, _settings(["bad"])))


class PrivateRepositoryCountFallbackTests(unittest.TestCase):
    @staticmethod
    def _count_payload(private_count=0):
        return {
            "user": {
                "publicOwned": {"totalCount": 2},
                "publicOwnedForks": {"totalCount": 0},
                "publicOwnedNonFork": {"totalCount": 2},
                "privateOwned": {"totalCount": private_count},
                "privateOwnedNonFork": {"totalCount": private_count},
            }
        }

    def _run_counts(self, tokens, responses, *, cached=None):
        settings = _settings(tokens)
        environment = {
            "PROFILE_TOKEN_MODE": "personal_github_token",
            "PERSONAL_GITHUB_TOKEN": tokens[0] if tokens else "",
            "GITHUB_TOKEN": tokens[1] if len(tokens) > 1 else "",
        }
        writes = []

        def cached_value(key):
            if key == "owned_repo_scope_counts":
                return cached
            return None

        with mock.patch.dict(os.environ, environment, clear=False), mock.patch.object(
            gh, "_settings", settings
        ), mock.patch.object(
            gh, "TOKEN", settings.token
        ), mock.patch.object(
            gh, "_get_cached", side_effect=cached_value
        ), mock.patch.object(
            gh,
            "_set_cached",
            side_effect=lambda key, value: writes.append((key, value)),
        ), mock.patch.object(
            github_graphql.requests, "post", side_effect=responses
        ):
            counts = gh.get_owned_repo_scope_counts()
        return counts, writes

    def _get_counts(self, tokens, responses):
        counts, _writes = self._run_counts(tokens, responses)
        return counts

    def test_private_counts_become_unknown_when_personal_token_falls_back(self):
        counts = self._get_counts(
            ["expired-personal", "default-token"],
            [
                _Resp(401),
                _Resp(200, {"data": self._count_payload(private_count=0)}),
            ],
        )

        self.assertIsNone(counts["private_owned"])
        self.assertIsNone(counts["private_owned_nonfork"])

    def test_zero_private_counts_are_exact_with_verified_full_repo_scope(self):
        counts = self._get_counts(
            ["opaque-primary-token"],
            [
                _Resp(
                    200,
                    {"data": self._count_payload(private_count=0)},
                    headers={"X-OAuth-Scopes": "repo, read:user"},
                )
            ],
        )

        self.assertEqual(0, counts["private_owned"])
        self.assertEqual(0, counts["private_owned_nonfork"])

    def test_authenticated_primary_pat_without_full_repo_scope_is_not_complete(self):
        responses = {
            "unknown-capability": _Resp(
                200,
                {"data": self._count_payload(private_count=0)},
            ),
            "repository-restricted": _Resp(
                200,
                {"data": self._count_payload(private_count=0)},
                headers={"X-OAuth-Scopes": "read:user"},
            ),
            "token-visible-subset": _Resp(
                200,
                {"data": self._count_payload(private_count=1)},
            ),
        }

        for case_name, response in responses.items():
            with self.subTest(case=case_name):
                counts, writes = self._run_counts(
                    ["opaque-primary-token"],
                    [response],
                )

                self.assertEqual(2, counts["public_owned_nonfork"])
                self.assertIsNone(counts["private_owned"])
                self.assertIsNone(counts["private_owned_nonfork"])
                self.assertEqual(1, len(writes))
                self.assertEqual(counts, writes[0][1].get("counts"))

    def test_bare_owned_count_cache_does_not_bypass_the_provider(self):
        bare_counts = {
            "public_owned_total": 2,
            "public_owned_forks": 0,
            "public_owned_nonfork": 2,
            "private_owned": 0,
            "private_owned_nonfork": 0,
        }

        counts, writes = self._run_counts(
            ["healthy-personal"],
            [
                _Resp(
                    200,
                    {"data": self._count_payload(private_count=4)},
                    headers={"X-OAuth-Scopes": "repo"},
                )
            ],
            cached=bare_counts,
        )

        self.assertEqual(4, counts["private_owned"])
        self.assertEqual(4, counts["private_owned_nonfork"])
        self.assertEqual(1, len(writes))

    def test_fallback_capability_loss_remains_unknown_through_cache(self):
        counts, writes = self._run_counts(
            ["expired-personal", "default-token"],
            [
                _Resp(401),
                _Resp(200, {"data": self._count_payload(private_count=0)}),
            ],
        )

        self.assertIsNone(counts["private_owned"])
        self.assertIsNone(counts["private_owned_nonfork"])
        self.assertEqual(1, len(writes))
        cache_key, envelope = writes[0]
        self.assertEqual("owned_repo_scope_counts", cache_key)
        self.assertEqual("owned-repo-scope-counts/v1", envelope.get("schema"))
        self.assertEqual(gh.USERNAME.casefold(), envelope.get("username"))
        self.assertEqual("owned-public-private-counts", envelope.get("query_scope"))
        self.assertIs(envelope.get("complete"), True)
        self.assertEqual("unavailable", envelope.get("private_capability"))
        self.assertEqual(counts, envelope.get("counts"))

        replayed, _replay_writes = self._run_counts(
            ["expired-personal", "default-token"],
            [
                _Resp(401),
                _Resp(200, {"data": self._count_payload(private_count=0)}),
            ],
            cached=envelope,
        )
        self.assertIsNone(replayed["private_owned"])
        self.assertIsNone(replayed["private_owned_nonfork"])


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path
from unittest import mock

import requests

from scripts import github_graphql, github_transport
from scripts.settings import Settings


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
    def __init__(self, status, json_data=None):
        self.status_code = status
        self._json = json_data or {}
        self.headers = {}

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


if __name__ == "__main__":
    unittest.main()

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

        def fake_get(url, headers=None, params=None, timeout=None):
            seen.append(headers.get("Authorization"))
            return _Resp(401) if "bad" in headers.get("Authorization", "") else _Resp(200)

        with mock.patch.object(github_transport.requests, "get", side_effect=fake_get):
            resp = github_transport.request_with_retry("https://x", _settings(["bad", "good"]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(seen, ["Bearer bad", "Bearer good"])

    def test_401_on_last_token_raises(self):
        def fake_get(url, headers=None, params=None, timeout=None):
            return _Resp(401)

        with mock.patch.object(github_transport.requests, "get", side_effect=fake_get):
            with self.assertRaises(requests.HTTPError):
                github_transport.request_with_retry("https://x", _settings(["bad"]))


class GraphqlFallbackTests(unittest.TestCase):
    def test_401_then_success(self):
        calls = []

        def fake_post(url, headers=None, json=None, timeout=None):
            calls.append(headers.get("Authorization"))
            if "bad" in headers.get("Authorization", ""):
                return _Resp(401)
            return _Resp(200, {"data": {"ok": True}})

        with mock.patch.object(github_graphql.requests, "post", side_effect=fake_post):
            data = github_graphql.graphql_query("q", {}, _settings(["bad", "good"]))
        self.assertEqual(data, {"ok": True})
        self.assertEqual(calls, ["Bearer bad", "Bearer good"])

    def test_401_only_returns_none(self):
        def fake_post(url, headers=None, json=None, timeout=None):
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


class TransportTimeoutTests(unittest.TestCase):
    """Exercise real loopback sockets without external network or credentials."""

    def _observe(self, route, *, stalled):
        # HARNESS / RUN A BOUNDED LOOPBACK HTTP PROVIDER AND THE REAL REQUESTS SEND
        import json
        import math
        import threading
        import time
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        received, release_headers = threading.Event(), threading.Event()
        requests_seen, sends, errors = [], [], []
        expected_data = {"ok": True, "source": "bounded-loopback-provider"}

        class Handler(BaseHTTPRequestHandler):
            def answer(self):
                size = int(self.headers.get("Content-Length", "0"))
                if size:
                    self.rfile.read(size)
                requests_seen.append((self.command, self.path))
                received.set()
                if stalled:
                    release_headers.wait(3)
                payload = {"data": expected_data} if route == "graphql" else expected_data
                raw = json.dumps(payload).encode()
                try:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(raw)))
                    self.end_headers()
                    self.wfile.write(raw)
                except (BrokenPipeError, ConnectionResetError):
                    pass  # The real timed-out client may have closed its socket.

            do_GET = do_POST = answer

            def log_message(self, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.daemon_threads = True
        worker = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
        worker.start()
        url = "http://127.0.0.1:" + str(server.server_port) + "/probe"
        original_send = requests.sessions.Session.send

        def observed_send(session, prepared, **kwargs):
            if prepared.url != url:
                raise RuntimeError("SETUP_UNAVAILABLE: request left the loopback fixture")
            supplied = kwargs.get("timeout")
            sends.append({"method": prepared.method, "timeout": supplied})
            # ARRANGE / PREPARE PRECONDITION / SCALE ONLY AN ACTUALLY SUPPLIED FINITE POLICY
            if (isinstance(supplied, tuple) and len(supplied) == 2 and
                    all(isinstance(value, (float, int)) and not isinstance(value, bool) and
                        math.isfinite(value) and value > 0 for value in supplied)):
                kwargs["timeout"] = tuple(min(value, 1.0) for value in supplied)
            try:
                return original_send(session, prepared, **kwargs)
            except requests.RequestException as error:
                errors.append(type(error).__name__)
                raise

        outcome, data = None, None
        started = time.monotonic()
        try:
            # ARRANGE / PREPARE PRECONDITION / KEEP LOOPBACK OUTSIDE PROXY AND NETRC CONFIGURATION
            with mock.patch.dict(os.environ, {"NO_PROXY": "127.0.0.1", "no_proxy": "127.0.0.1", "NETRC": os.devnull}), \
                    mock.patch.object(requests.sessions.Session, "send", observed_send), \
                    mock.patch.object(github_graphql, "GRAPHQL_ENDPOINT", url):
                # ACT / CALL THE EXISTING REQUEST ROUTE AGAINST THE REAL HTTP PROVIDER
                try:
                    if route == "graphql":
                        data = github_graphql.graphql_query("query { fixture }", {}, _settings(["fixture-token"]))
                        outcome = "unavailable" if data is None else "success"
                    else:
                        response = (github_transport.request_with_retry(url, _settings(["fixture-token"]), max_retries=1)
                                    if route == "authenticated" else
                                    github_transport.request_public_with_retry(url, max_retries=1))
                        data, outcome = response.json(), "success"
                except requests.Timeout:
                    outcome = "timeout"
        finally:
            elapsed = time.monotonic() - started
            release_headers.set()
            server.shutdown()
            server.server_close()
            worker.join(timeout=2)
        # ARRANGE / VERIFY PRECONDITION / ONE REAL REQUEST REACHED THE READY PROVIDER
        self.assertFalse(worker.is_alive(), "SETUP_UNAVAILABLE: loopback server did not stop")
        self.assertTrue(received.is_set(), "SETUP_UNAVAILABLE: provider received no request")
        self.assertEqual(1, len(requests_seen), "SETUP_UNAVAILABLE: unexpected provider request count")
        self.assertEqual(1, len(sends), "SETUP_UNAVAILABLE: actual Requests send was not observed once")
        observation = {"route": route, "stalled_headers": stalled, "outcome": outcome, "data": data,
                       "requests": requests_seen, "sends": sends, "transport_errors": errors,
                       "elapsed_seconds": round(elapsed, 4), "scale_seconds": 1.0, "header_delay_bound_seconds": 3}
        print("TRANSPORT_TIMEOUT_OBSERVATION " + json.dumps(observation, sort_keys=True), flush=True)
        return observation, expected_data

    def test_authenticated_get_stalled_headers_times_out(self):
        observation, _ = self._observe("authenticated", stalled=True)
        # ASSERT / PRODUCT ORACLE / AUTHENTICATED GET DELEGATES THE POLICY AND RETAINS A REAL READ TIMEOUT
        self.assertEqual(((10.0, 30.0), "timeout", ["ReadTimeout"]),
                         (observation["sends"][0]["timeout"], observation["outcome"], observation["transport_errors"]),
                         "[PROFILE-GITHUB-AUTHENTICATED-GET-TIMEOUT] authenticated GET must delegate its connect/read policy")

    def test_public_get_stalled_headers_times_out(self):
        observation, _ = self._observe("public", stalled=True)
        # ASSERT / PRODUCT ORACLE / PUBLIC GET DELEGATES THE POLICY AND RETAINS A REAL READ TIMEOUT
        self.assertEqual(((10.0, 30.0), "timeout", ["ReadTimeout"]),
                         (observation["sends"][0]["timeout"], observation["outcome"], observation["transport_errors"]),
                         "[PROFILE-GITHUB-PUBLIC-GET-TIMEOUT] public GET must delegate its connect/read policy")

    def test_graphql_stalled_headers_returns_unknown(self):
        observation, _ = self._observe("graphql", stalled=True)
        # ASSERT / PRODUCT ORACLE / GRAPHQL DELEGATES THE POLICY AND PRESERVES UNKNOWN ON A REAL READ TIMEOUT
        self.assertEqual(((10.0, 30.0), "unavailable", ["ReadTimeout"], None),
                         (observation["sends"][0]["timeout"], observation["outcome"], observation["transport_errors"], observation["data"]),
                         "[PROFILE-GITHUB-GRAPHQL-TIMEOUT] GraphQL must delegate the policy and preserve unknown on timeout")

    def _healthy(self, route):
        observation, expected = self._observe(route, stalled=False)
        # ASSERT / CONTROL ORACLE / THE SAME ROUTE CONSUMES AN ACTUAL HEALTHY HTTP RESPONSE
        self.assertEqual(("success", expected, []),
                         (observation["outcome"], observation["data"], observation["transport_errors"]))

    def test_control_authenticated_get_immediate_response(self):
        self._healthy("authenticated")

    def test_control_public_get_immediate_response(self):
        self._healthy("public")

    def test_control_graphql_immediate_response(self):
        self._healthy("graphql")


class TransportPolicyControls(unittest.TestCase):
    """Preserve retry, credential, cache and unknown semantics with finite requests."""

    def _get(self, route, *, max_retries=None):
        kwargs = {"params": {"page": 2}}
        if max_retries is not None:
            kwargs["max_retries"] = max_retries
        if route == "public":
            return github_transport.request_public_with_retry("https://fixture.invalid/items", **kwargs)
        if route == "explicit_headers":
            kwargs["headers"] = {"Accept": "application/vnd.github+json", "X-Fixture": "explicit"}
        return github_transport.request_with_retry("https://fixture.invalid/items", _settings(["primary", "secondary"]), **kwargs)

    def test_get_policy_is_passed_on_each_retry_without_changing_inputs(self):
        for route in ("authenticated", "explicit_headers", "public"):
            response = _Resp(200, {"ok": True})
            with self.subTest(route=route), mock.patch.object(
                github_transport.requests, "get", side_effect=[requests.ConnectTimeout("connect unavailable"), response]
            ) as provider, mock.patch.object(github_transport.time, "sleep") as pause:
                self.assertIs(response, self._get(route))
                self.assertEqual(2, provider.call_count)
                for call in provider.call_args_list:
                    self.assertEqual((10.0, 30.0), call.kwargs["timeout"])
                    self.assertEqual({"page": 2}, call.kwargs["params"])
                    headers = call.kwargs["headers"]
                    if route == "authenticated":
                        self.assertEqual("Bearer primary", headers["Authorization"])
                    elif route == "explicit_headers":
                        self.assertEqual("explicit", headers["X-Fixture"])
                        self.assertNotIn("Authorization", headers)
                    else:
                        self.assertEqual({"Accept": "application/vnd.github+json"}, headers)
                pause.assert_called_once_with(1)

    def test_get_timeout_exhaustion_preserves_attempts_backoff_and_token_choice(self):
        for route, attempts in (("authenticated", 3), ("explicit_headers", 3), ("public", 2)):
            failure = requests.ReadTimeout("provider sent no headers")
            with self.subTest(route=route), mock.patch.object(
                github_transport.requests, "get", side_effect=failure
            ) as provider, mock.patch.object(github_transport.time, "sleep") as pause:
                with self.assertRaises(requests.ReadTimeout) as raised:
                    self._get(route)
                self.assertIs(failure, raised.exception)
                self.assertEqual(attempts, provider.call_count)
                self.assertEqual([mock.call(2**index) for index in range(attempts - 1)], pause.call_args_list)
                for call in provider.call_args_list:
                    self.assertEqual((10.0, 30.0), call.kwargs["timeout"])
                    if route == "authenticated":
                        self.assertEqual("Bearer primary", call.kwargs["headers"]["Authorization"])

    def test_get_429_and_503_keep_existing_retry_after_and_backoff(self):
        for route in ("authenticated", "explicit_headers", "public"):
            healthy = _Resp(200, {"ok": True})
            with self.subTest(route=route), mock.patch.object(
                github_transport.requests, "get", side_effect=[_Resp(429, headers={"Retry-After": "4"}), _Resp(503), healthy]
            ) as provider, mock.patch.object(github_transport.time, "sleep") as pause:
                self.assertIs(healthy, self._get(route, max_retries=3))
                self.assertEqual([mock.call(4), mock.call(2)], pause.call_args_list)
                self.assertEqual([(10.0, 30.0)] * 3, [call.kwargs["timeout"] for call in provider.call_args_list])

    def test_get_401_token_fallback_passes_policy_to_both_tokens(self):
        with mock.patch.object(github_transport.requests, "get", side_effect=[_Resp(401), _Resp(200)]) as provider, \
                mock.patch.object(github_transport.time, "sleep") as pause:
            self.assertEqual(200, self._get("authenticated").status_code)
        self.assertEqual(["Bearer primary", "Bearer secondary"],
                         [call.kwargs["headers"]["Authorization"] for call in provider.call_args_list])
        self.assertEqual([(10.0, 30.0)] * 2, [call.kwargs["timeout"] for call in provider.call_args_list])
        pause.assert_not_called()

    def test_graphql_policy_is_shared_and_preserves_401_fallback(self):
        with mock.patch.object(github_graphql.requests, "post", side_effect=[
                _Resp(401), _Resp(200, {"data": {"ok": True}}, headers={"X-OAuth-Scopes": "repo"})]) as provider:
            result = github_graphql.graphql_query("query fixture", {"count": 1}, _settings(["primary", "secondary"]))
        self.assertEqual({"ok": True}, result)
        self.assertEqual(["Bearer primary", "Bearer secondary"],
                         [call.kwargs["headers"]["Authorization"] for call in provider.call_args_list])
        for call in provider.call_args_list:
            self.assertEqual((10.0, 30.0), call.kwargs["timeout"])
            self.assertEqual({"query": "query fixture", "variables": {"count": 1}}, call.kwargs["json"])
        self.assertTrue(github_graphql.last_query_used_fallback_token())
        self.assertEqual(frozenset({"repo"}), github_graphql.last_query_oauth_scopes())

    def test_graphql_timeout_clears_old_capabilities_and_does_not_rotate_tokens(self):
        settings = _settings(["primary", "secondary"])
        with mock.patch.object(github_graphql.requests, "post", side_effect=[
                _Resp(401), _Resp(200, {"data": {"ok": True}}, headers={"X-OAuth-Scopes": "repo"})]):
            self.assertEqual({"ok": True}, github_graphql.graphql_query("query fixture", {}, settings))
        self.assertTrue(github_graphql.last_query_used_fallback_token())
        self.assertEqual(frozenset({"repo"}), github_graphql.last_query_oauth_scopes())
        with mock.patch.object(github_graphql.requests, "post", side_effect=requests.ConnectTimeout("unavailable")) as provider:
            self.assertIsNone(github_graphql.graphql_query("query fixture", {}, settings))
        provider.assert_called_once()
        self.assertEqual((10.0, 30.0), provider.call_args.kwargs["timeout"])
        self.assertEqual("Bearer primary", provider.call_args.kwargs["headers"]["Authorization"])
        self.assertFalse(github_graphql.last_query_used_fallback_token())
        self.assertIsNone(github_graphql.last_query_oauth_scopes())

    def test_complete_pagination_cache_still_avoids_transport(self):
        endpoint, params = "users/fixture/repos", {"type": "owner"}
        cached = {"schema": "rest-pagination/v1", "endpoint": endpoint, "params": params,
                  "per_page": 100, "complete": True, "pages_fetched": 1, "results": [{"name": "cached"}]}
        with mock.patch.object(gh, "_get_cached", return_value=cached), \
                mock.patch.object(gh, "_set_cached") as cache, \
                mock.patch.object(github_transport.requests, "get") as provider:
            self.assertEqual(cached["results"], gh.paginated_get(endpoint, params=params))
        provider.assert_not_called()
        cache.assert_not_called()

    def test_timeout_after_a_successful_page_never_caches_partial_inventory(self):
        import copy
        effects = iter([_Resp(200, [{"name": "first-page"}]), requests.ReadTimeout("stalled"),
                        requests.ReadTimeout("stalled"), requests.ReadTimeout("stalled")])
        seen = []

        def provider(_url, **kwargs):
            seen.append(copy.deepcopy(kwargs))
            response = next(effects)
            if isinstance(response, Exception):
                raise response
            return response

        with mock.patch.object(gh, "_settings", _settings(["primary", "secondary"])), \
                mock.patch.object(gh, "_get_cached", return_value=None), \
                mock.patch.object(gh, "_set_cached") as cache, \
                mock.patch.object(github_transport.requests, "get", side_effect=provider), \
                mock.patch.object(github_transport.time, "sleep") as pause:
            with self.assertRaises(requests.ReadTimeout):
                gh.paginated_get("users/fixture/repos", per_page=1)
        self.assertEqual([1, 2, 2, 2], [call["params"]["page"] for call in seen])
        self.assertEqual([(10.0, 30.0)] * 4, [call["timeout"] for call in seen])
        self.assertEqual(["Bearer primary"] * 4, [call["headers"]["Authorization"] for call in seen])
        self.assertEqual([mock.call(1), mock.call(2)], pause.call_args_list)
        cache.assert_not_called()

    def test_event_timeout_stays_incomplete_and_is_not_cached_as_observed_empty(self):
        with mock.patch.object(gh, "_settings", _settings(["primary", "secondary"])), \
                mock.patch.object(gh, "_get_cached", return_value=None), \
                mock.patch.object(gh, "_set_cached") as cache, \
                mock.patch.object(github_transport.requests, "get", side_effect=requests.ReadTimeout("stalled")) as provider, \
                mock.patch.object(github_transport.time, "sleep"):
            observation = gh.get_events_observation(per_page=1, max_pages=1)
        self.assertTrue(gh.validate_provider_observation(observation))
        self.assertEqual(("partial", False, "page_error", ()),
                         (observation["status"], observation["complete"], observation["completion_reason"], observation["value"]))
        self.assertEqual(3, provider.call_count)
        cache.assert_not_called()


if __name__ == "__main__":
    unittest.main()

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from scripts import github_client as gh


class _FakeResponse:
    def __init__(self, status_code: int, payload):
        self.status_code = status_code
        self._payload = payload
        self.headers = {}

    def json(self):
        return self._payload


class GitHubClientTests(unittest.TestCase):
    def test_get_releases_last_n_days_counts_recent_releases(self):
        now = datetime.now(timezone.utc)
        recent = (now - timedelta(days=2)).isoformat().replace("+00:00", "Z")
        old = (now - timedelta(days=45)).isoformat().replace("+00:00", "Z")
        repos = [{"owner": {"login": "jguida941"}, "name": "voiceterm"}]

        with patch("scripts.github_client._get_cached", return_value=None), patch(
            "scripts.github_client._set_cached",
        ), patch(
            "scripts.github_client._request_with_retry",
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

        with patch("scripts.github_client.TOKEN", "x"), patch(
            "scripts.github_client._get_cached",
            return_value=None,
        ), patch(
            "scripts.github_client._set_cached",
        ), patch(
            "scripts.github_client._graphql_query",
            return_value=payload,
        ), patch(
            "scripts.github_client.token_mode_from_env",
            return_value="github_token",
        ):
            counts = gh.get_owned_repo_scope_counts()

        self.assertEqual(counts["public_owned_nonfork"], 62)
        self.assertIsNone(counts["private_owned"])

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

        with patch("scripts.github_client._get_cached", return_value=None), patch(
            "scripts.github_client._set_cached",
        ), patch(
            "scripts.github_client._calendar_window",
            return_value=(start, end, "2026-03-06"),
        ), patch(
            "scripts.github_client.requests.post",
            return_value=_FakeResponse(200, graphql_payload),
        ) as post_mock:
            calendar = gh.get_contribution_calendar(days=365)

        self.assertEqual(calendar["totalContributions"], 4288)
        call_kwargs = post_mock.call_args.kwargs
        variables = call_kwargs["json"]["variables"]
        self.assertEqual(variables["from"], "2026-03-01T00:00:00Z")
        self.assertEqual(variables["to"], "2026-03-06T23:59:59Z")


if __name__ == "__main__":
    unittest.main()

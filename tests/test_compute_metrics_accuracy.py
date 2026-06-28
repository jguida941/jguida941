import json
import unittest
from datetime import date, datetime, timedelta, timezone

from scripts.pipeline.collect_data import CollectedProfileData
from scripts.pipeline.compute_metrics import _compute_current_streak_days, compute_profile_model


def _iso(dt):
    return dt.isoformat().replace("+00:00", "Z")


def _noop(*a, **k):
    pass


class AccuracyTests(unittest.TestCase):
    def _collected(self):
        now = datetime.now(timezone.utc)
        recent = _iso(now - timedelta(days=1))
        created = _iso(now - timedelta(days=200))

        def repo(name, msg, lang, private=False, ci=True):
            return {
                "name": name,
                "owner": {"login": "jguida941"},
                "private": private,
                "visibility": "private" if private else "public",
                "html_url": f"https://github.com/jguida941/{name}",
                "pushed_at": recent,
                "created_at": created,
                "stargazers_count": 1,
                "forks_count": 0,
                "language": lang,
                "has_ci_workflows": ci,
                "workflow_file_count": 2 if ci else 0,
                "latest_commit_message": msg,
                "language_bytes": {lang: 1000},
            }

        repos = [
            repo("jguida941", "update canonical profile artifacts", "Python"),
            repo("pub1", "Add real feature X", "Python"),
            repo("pub2", "chore: refresh badges [skip ci]", "Java", ci=False),
        ]
        private_repos = [repo("secret-api", "private internal commit text", "Rust", private=True, ci=False)]
        events = [
            {
                "type": "PushEvent",
                "actor": {"login": "github-actions[bot]"},
                "repo": {"name": "jguida941/jguida941"},
                "created_at": recent,
                "payload": {"commits": [{"message": "update canonical profile artifacts"}]},
            },
            {
                "type": "PushEvent",
                "actor": {"login": "jguida941"},
                "repo": {"name": "jguida941/pub1"},
                "created_at": recent,
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
                         "public_owned_nonfork": 3, "private_owned": 1},
            repos=repos,
            all_repos=repos,
            language_bytes={"Python": 2000, "Java": 1000, "Rust": 500},
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

    def setUp(self):
        self.model = compute_profile_model(self._collected(), logger=_noop, allow_network_calls=False)
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

    def test_private_repo_named_but_no_headline_leak(self):
        priv = [r for r in self.model["recent_repos"] if r.get("is_private")]
        self.assertTrue(any(r["name"] == "secret-api" for r in priv))
        secret = next(r for r in priv if r["name"] == "secret-api")
        self.assertEqual(secret["last_commit_msg"], "")  # never leak private commit text
        self.assertEqual(secret["html_url"], "")  # not linked (would 404 for visitors)
        self.assertNotIn("private internal commit text", self.blob)

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


if __name__ == "__main__":
    unittest.main()

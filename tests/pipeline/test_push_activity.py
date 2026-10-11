"""Pub-safe regression checks for recent push identity and qualified diffs."""
import unittest
from scripts.pipeline.push_activity import (
    interpret_fast_forward_comparison, present_recent_pushes, select_recent_pushes,
)


def event(repo, when, key, ref="refs/heads/main", kind="push", before="a"*40, after="b"*40):
    return {"repository": repo, "timestamp": when, "id": key,
            "activity_type": kind, "ref": ref, "before": before, "after": after}


def family(repo, *events, complete=True):
    return {"repository": repo, "activity": {"status": "ok", "complete": complete,
            "selection_valid": complete, "rows": list(events)}}


def compare(before="a"*40, after="b"*40, *, files=None):
    return {"status": "ahead", "ahead_by": 2, "behind_by": 0, "total_commits": 2,
            "base_commit": {"sha": before}, "merge_base_commit": {"sha": before},
            "commits": [{"sha": "c"*40}, {"sha": after}],
            "files": files if files is not None else [{"additions": 11, "deletions": 3}]}


class RecentPushObservationsTests(unittest.TestCase):
    def test_latest_per_repository_including_feature_branch(self):
        rows = [
            family("owner/a", event("owner/a", "2026-10-11T11:00:00Z", "a1"), event("owner/a", "2026-10-11T09:00:00Z", "a0")),
            family("owner/b", event("owner/b", "2026-10-11T12:00:00Z", "b1", "refs/heads/feature/x")),
            family("owner/c", event("owner/c", "2026-10-11T10:00:00Z", "c1")),
            family("owner/d", event("owner/d", "2026-10-11T08:00:00Z", "d1")),
        ]
        result = select_recent_pushes(rows, observed_at="2026-10-11T12:30:00Z", coverage_complete=True)
        self.assertEqual(["owner/b", "owner/a", "owner/c"], [r["repository"] for r in result["rows"]])
        self.assertEqual("refs/heads/feature/x", result["rows"][0]["ref"])
        self.assertTrue(result["complete"])

    def test_partial_selection_and_non_push_types_not_ranked(self):
        rows = [
            family("owner/a", event("owner/a", "2026-10-11T12:00:00Z", "1", kind="branch_creation"),
                   event("owner/a", "2026-10-11T10:00:00Z", "2")),
            family("owner/b", event("owner/b", "2026-10-11T11:00:00Z", "3"), complete=False),
        ]
        result = select_recent_pushes(rows, observed_at="2026-10-11T12:30:00Z", coverage_complete=False)
        self.assertEqual("partial", result["status"])
        self.assertEqual(["owner/b", "owner/a"], [r["repository"] for r in result["rows"]])

    def test_fast_forward_requires_ancestry_complete_commits_and_files(self):
        original = compare()
        ok = interpret_fast_forward_comparison(original, before="a"*40, after="b"*40)
        self.assertEqual((11, 3, ["c"*40, "b"*40]), (ok["additions"], ok["deletions"], ok["commits"]))
        for bad in (
            {**original, "status": "diverged"},
            {**original, "ahead_by": 3},
            {**original, "merge_base_commit": {"sha": "d"*40}},
            {**original, "commits": original["commits"][:1]},
            {**original, "files": [{"additions": None, "deletions": 3}]},
        ):
            with self.subTest(bad=bad):
                self.assertEqual("unavailable", interpret_fast_forward_comparison(
                    bad, before="a"*40, after="b"*40)["status"])
        self.assertEqual("unavailable", interpret_fast_forward_comparison(
            original, before="a"*40, after="b"*40, has_next_page=True)["status"])
        zero = interpret_fast_forward_comparison(
            compare(files=[{"additions": 0, "deletions": 0}]), before="a"*40, after="b"*40)
        self.assertEqual((0, 0), (zero["additions"], zero["deletions"]))

    def test_unknown_is_not_zero_and_force_push_is_not_fast_forward(self):
        old = event("owner/x", "2026-10-11T12:00:00Z", "x1", ref="refs/heads/dev")
        partial = present_recent_pushes({"status": "partial", "complete": False, "rows": [old]})
        self.assertEqual("unavailable", partial["rows"][0]["diff_status"])
        self.assertIsNone(partial["rows"][0]["additions"])
        self.assertFalse(partial["complete"])
        force = {**old, "activity_type": "force_push", "diff": {
            "status": "ok", "commits": ["b"*40], "additions": 90, "deletions": 1}}
        self.assertIsNone(present_recent_pushes({
            "status": "ok", "complete": True, "rows": [force]})["rows"][0]["additions"])

    def test_public_projection_does_not_copy_raw_provider_content(self):
        source = event("owner/x", "2026-10-11T12:00:00Z", "x1")
        source.update(raw_access_token="UNSAFE", diff={
            "status": "ok", "additions": 11, "deletions": 3, "commits": ["c"*40, "b"*40]})
        projected = present_recent_pushes({"status": "ok", "complete": True, "rows": [source]})["rows"][0]
        self.assertNotIn("raw_access_token", projected)
        self.assertEqual(11, projected["additions"])


if __name__ == "__main__":
    unittest.main()

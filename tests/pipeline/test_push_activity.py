"""Pub-safe regression checks for recent push identity and qualified diffs."""
import unittest
from scripts.pipeline.push_activity import (
    interpret_fast_forward_comparison, present_recent_pushes, select_recent_pushes,
    qualify_recent_pushes,
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



class P024NormalizedMetadataTests(unittest.TestCase):
    def test_mixed_case_alias_deduplicates_and_favors_latest(self):
        rows = [
            {"name": "repo", "url": "https://github.com/owner/repo",
             "pushed_at": "2026-10-11T19:00:00Z"},
            {"name": "repo", "url": "https://github.com/OWNER/repo",
             "pushed_at": "2026-10-11T20:00:00Z"},
        ]
        result = qualify_recent_pushes(None, rows, "2026-10-11T21:00:00Z")
        self.assertEqual(["OWNER/repo"], [r["repository"] for r in result["rows"]])
        self.assertFalse(result["complete"])
        self.assertTrue(result["rows"][0]["metadata_only"])

    def test_future_naive_and_bad_cutoff_fail_closed(self):
        rows = [
            {"name": "valid", "url": "https://github.com/owner/valid",
             "pushed_at": "2026-10-11T20:00:00Z"},
            {"name": "future", "url": "https://github.com/owner/future",
             "pushed_at": "2099-10-12T20:00:00Z"},
            {"name": "naive", "url": "https://github.com/owner/naive",
             "pushed_at": "2026-10-11T20:00:00"},
        ]
        good = qualify_recent_pushes(None, rows, "2026-10-11T21:00:00Z")
        self.assertEqual(["owner/valid"], [r["repository"] for r in good["rows"]])
        for bad in (None, "broken", "2026-10-11T21:00:00"):
            with self.subTest(cutoff=bad):
                invalid = qualify_recent_pushes(None, rows, bad)
                self.assertEqual("unavailable", invalid["status"])
                self.assertEqual([], invalid["rows"])

    def test_valid_pushes_precede_all_fallback_metadata(self):
        actual = {"status": "partial", "complete": False,
                  "rows": [{"repository": "owner/actual", "activity_type": "push"}]}
        metadata = [{"name": "other", "url": "https://github.com/owner/other",
                     "pushed_at": "2026-10-11T20:00:00Z"}]
        self.assertEqual(actual, qualify_recent_pushes(
            actual, metadata, "2026-10-11T21:00:00Z"))

    def test_metadata_remains_unknown_and_never_invents_three(self):
        one = [{"name": "one", "url": "https://github.com/owner/one",
                "pushed_at": "2026-10-11T20:00:00Z"}]
        item = qualify_recent_pushes(None, one, "2026-10-11T21:00:00Z")
        self.assertEqual(1, len(item["rows"]))
        self.assertEqual("partial", item["status"])
        self.assertFalse(item["complete"])
        self.assertNotIn("additions", item["rows"][0])
        self.assertEqual([], qualify_recent_pushes(None, [], "2026-10-11T21:00:00Z")["rows"])



class P024ObservedPushIdentityTests(unittest.TestCase):
    def test_case_variant_event_alias_cannot_displace_third_repository(self):
        rows = [
            family("owner/alpha", event("owner/alpha", "2026-10-11T10:00:00Z", "a1")),
            family("OWNER/ALPHA", event("OWNER/ALPHA", "2026-10-11T12:00:00Z", "a2")),
            family("owner/beta", event("owner/beta", "2026-10-11T11:00:00Z", "b1")),
            family("owner/gamma", event("owner/gamma", "2026-10-11T09:00:00Z", "g1")),
        ]
        result = select_recent_pushes(
            rows, observed_at="2026-10-11T13:00:00Z", coverage_complete=True)
        self.assertEqual(["OWNER/ALPHA", "owner/beta", "owner/gamma"],
                         [row["repository"] for row in result["rows"]])
        self.assertEqual(3, len({r["repository"].casefold() for r in result["rows"]}))
        self.assertTrue(result["complete"])

    def test_event_projection_deduplicates_case_aliases(self):
        raw = {"status": "partial", "complete": False, "rows": [
            event("owner/alpha", "2026-10-11T11:00:00Z", "a1"),
            event("OWNER/ALPHA", "2026-10-11T10:00:00Z", "a2"),
            event("owner/beta", "2026-10-11T09:00:00Z", "b1"),
        ]}
        public = present_recent_pushes(raw)
        self.assertEqual(["owner/alpha", "owner/beta"],
                         [row["repository"] for row in public["rows"]])
        self.assertFalse(public["complete"])

    def test_reverse_case_alias_cannot_escape_raw_identity_storage(self):
        raw = {"status": "partial", "complete": False, "rows": [
            event("OWNER/ALPHA", "2026-10-11T11:00:00Z", "a1"),
            event("owner/alpha", "2026-10-11T10:00:00Z", "a2"),
            event("owner/beta", "2026-10-11T09:00:00Z", "b1"),
        ]}
        public = present_recent_pushes(raw)
        self.assertEqual(["OWNER/ALPHA", "owner/beta"],
                         [row["repository"] for row in public["rows"]])
        self.assertFalse(public["complete"])

class P024ProjectionCompletenessTests(unittest.TestCase):
    def test_rejected_invalid_rows_cannot_claim_complete(self):
        valid = event("owner/valid", "2026-10-11T19:00:00Z", "e1")
        malformed = {**event("owner/bad", "2026-10-11T18:00:00Z", "e2"), "ref": "refs/heads/forbidden?"}
        raw = {"status": "ok", "complete": True, "rows": [valid, malformed]}
        published = present_recent_pushes(raw)
        self.assertEqual(["owner/valid"], [r["repository"] for r in published["rows"]])
        self.assertFalse(published["complete"], "a rejected raw row must not survive as a complete projection")
        self.assertEqual("partial", published["status"])

    def test_valid_rows_and_true_zero_remain_complete(self):
        valid = event("owner/good", "2026-10-11T19:00:00Z", "e1")
        for rows, expected in [([valid], ["owner/good"]), ([], [])]:
            with self.subTest(rows=len(rows)):
                result = present_recent_pushes({"status": "ok", "complete": True, "rows": rows})
                self.assertTrue(result["complete"])
                self.assertEqual("ok", result["status"])
                self.assertEqual(expected, [row["repository"] for row in result["rows"]])

    def test_truncation_never_looks_complete(self):
        raw = {"status": "ok", "complete": True, "rows": [
            event(f"owner/repo{i}", f"2026-10-11T{19-i:02d}:00:00Z", f"e{i}")
            for i in range(4)
        ]}
        result = present_recent_pushes(raw)
        self.assertEqual(3, len(result["rows"]))
        self.assertEqual("partial", result["status"])
        self.assertFalse(result["complete"])

    def test_upstream_partial_and_incomplete_never_get_upgraded(self):
        e = event("owner/normal", "2026-10-11T19:00:00Z", "id1")
        for status, claimed_complete in (("partial", True), ("ok", False)):
            with self.subTest(status=status, claimed_complete=claimed_complete):
                result = present_recent_pushes({"status": status, "complete": claimed_complete,
                                                "rows": [e]})
                self.assertFalse(result["complete"])
                self.assertEqual("partial", result["status"])

    def test_case_alias_discard_downgrades_completeness(self):
        first = event("owner/alpha", "2026-10-11T19:00:00Z", "a")
        alias = event("OWNER/ALPHA", "2026-10-11T18:00:00Z", "b")
        result = present_recent_pushes({"status": "ok", "complete": True, "rows": [first, alias]})
        self.assertEqual(["owner/alpha"], [x["repository"] for x in result["rows"]])
        self.assertFalse(result["complete"])


class P024ObservedEmptyVsUnavailableTests(unittest.TestCase):
    def test_selected_observed_empty_keeps_known_zero_without_metadata(self):
        selected = select_recent_pushes(
            [family("owner/quiet")], observed_at="2026-10-11T21:00:00Z", coverage_complete=True)
        projected = present_recent_pushes(selected)
        self.assertEqual(("ok", True, []),
                         (projected["status"], projected["complete"], projected["rows"]))
        qualified = qualify_recent_pushes(projected, [], "2026-10-11T21:00:00Z")
        self.assertEqual(("ok", True, []),
                         (qualified["status"], qualified["complete"], qualified["rows"]))

    def test_partial_and_missing_observations_do_not_look_like_zero(self):
        for recent in (None, {"status": "partial", "complete": False, "rows": []},
                       {"status": "ok", "complete": False, "rows": []}):
            with self.subTest(recent=recent):
                actual = qualify_recent_pushes(recent, [], "2026-10-11T21:00:00Z")
                self.assertFalse(actual["complete"])
                self.assertEqual("unavailable", actual["status"])

    def test_qualified_metadata_hints_remain_partial_not_observed_zero(self):
        recent = present_recent_pushes({"status": "ok", "complete": True, "rows": []})
        hints = [{"name": "reported", "url": "https://github.com/owner/reported",
                  "pushed_at": "2026-10-11T20:00:00Z"}]
        actual = qualify_recent_pushes(recent, hints, "2026-10-11T21:00:00Z")
        self.assertEqual("partial", actual["status"])
        self.assertFalse(actual["complete"])
        self.assertEqual(["owner/reported"], [r["repository"] for r in actual["rows"]])
        self.assertTrue(actual["rows"][0]["metadata_only"])

    def test_nonempty_observed_event_keeps_precedence_over_metadata(self):
        selected = {"status": "partial", "complete": False,
                    "rows": [event("owner/live", "2026-10-11T18:00:00Z", "live")]}
        actual = qualify_recent_pushes(selected, [{"name": "hint", "url": "https://github.com/owner/hint",
                                                  "pushed_at": "2026-10-11T20:00:00Z"}],
                                       "2026-10-11T21:00:00Z")
        self.assertEqual(selected, actual)

if __name__ == "__main__":
    unittest.main()

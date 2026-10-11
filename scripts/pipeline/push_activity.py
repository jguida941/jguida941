"""Verified, bounded recent-push facts shared by README and website.

Repository push timestamps, push events, commits, and before/after tree diffs are
separate observations.  A commit is never inferred to belong to a push from a
branch head alone.
"""
from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any

_REPO = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]{1,100}\\Z")
_OID = re.compile(r"[0-9a-f]{40}\\Z")
_ID = re.compile(r"[A-Za-z0-9_-]{1,200}\\Z")
_PUSH_TYPES = frozenset(("push", "force_push"))
_MAX_COMPARE_COMMITS = 25


def _timestamp(value: Any) -> datetime | None:
    if type(value) is not str:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc)


def _safe_event(value: Any, *, expected_repo: str, observed_at: datetime) -> dict | None:
    if type(value) is not dict or value.get("activity_type") not in _PUSH_TYPES:
        return None
    ref, eid, before, after = (value.get(key) for key in ("ref", "id", "before", "after"))
    occurred = _timestamp(value.get("timestamp"))
    if (value.get("repository") != expected_repo or type(eid) is not str
            or not _ID.fullmatch(eid) or type(ref) is not str
            or not ref.startswith("refs/heads/") or len(ref) > 255
            or any(c.isspace() or c in '<>"\\~^:?*[' or ord(c) < 33 for c in ref)
            or ".." in ref or "@{" in ref or ref.endswith(".")
            or not _OID.fullmatch(str(before)) or not _OID.fullmatch(str(after))
            or str(after) == "0" * 40 or occurred is None or occurred > observed_at):
        return None
    return {"id": eid, "repository": expected_repo, "timestamp": occurred.isoformat().replace("+00:00", "Z"),
            "activity_type": value["activity_type"], "ref": ref,
            "before": before, "after": after}


def select_recent_pushes(rows: Any, *, observed_at: str, coverage_complete: bool) -> dict:
    """Pick the latest observed push per repository, not one row per commit."""
    now = _timestamp(observed_at)
    if now is None or type(rows) is not list:
        return {"status": "unavailable", "complete": False, "reason": "observations_unavailable", "rows": []}
    latest, coverage_gap = {}, not coverage_complete
    for entry in rows:
        if type(entry) is not dict or type(entry.get("repository")) is not str:
            coverage_gap = True
            continue
        repository = entry["repository"]
        if not _REPO.fullmatch(repository) or ".." in repository:
            coverage_gap = True
            continue
        family = entry.get("activity")
        if type(family) is not dict or family.get("complete") is not True or family.get("selection_valid") is not True:
            coverage_gap = True
        events = family.get("rows") if type(family) is dict else None
        if type(events) is not list:
            continue
        for raw in events:
            event = _safe_event(raw, expected_repo=repository, observed_at=now)
            if event is None:
                continue
            key = (event["timestamp"], event["id"], event["ref"], event["after"])
            if repository not in latest or key > latest[repository][0]:
                latest[repository] = (key, event)
    selected = sorted((item[1] for item in latest.values()),
                      key=lambda row: (row["timestamp"], row["id"], row["repository"]), reverse=True)[:3]
    return {"status": "ok" if not coverage_gap else "partial", "complete": not coverage_gap,
            "reason": "observed" if not coverage_gap else "incomplete_activity_coverage", "rows": selected}


def interpret_fast_forward_comparison(payload: Any, *, before: str, after: str, has_next_page: bool = False) -> dict:
    """Verify small FF comparisons; tree-diff totals are not sums of commit stats."""
    unavailable = {"status": "unavailable", "reason": "comparison_not_verified",
                   "additions": None, "deletions": None, "commits": []}
    if (type(payload) is not dict or has_next_page
            or type(before) is not str or type(after) is not str
            or not _OID.fullmatch(before) or before == "0" * 40
            or not _OID.fullmatch(after) or before == after):
        return unavailable
    total, ahead, behind = (payload.get(key) for key in ("total_commits", "ahead_by", "behind_by"))
    base, mergebase = payload.get("base_commit"), payload.get("merge_base_commit")
    commits, files = payload.get("commits"), payload.get("files")
    if (payload.get("status") != "ahead" or type(total) is not int
            or not 1 <= total <= _MAX_COMPARE_COMMITS
            or type(ahead) is not int or ahead != total
            or type(behind) is not int or behind != 0
            or type(base) is not dict or base.get("sha") != before
            or type(mergebase) is not dict or mergebase.get("sha") != before
            or type(commits) is not list or len(commits) != total
            or type(files) is not list or len(files) >= 300):
        return unavailable
    oids = [row.get("sha") if type(row) is dict else None for row in commits]
    if any(type(sha) is not str or not _OID.fullmatch(sha) for sha in oids):
        return unavailable
    if len(set(oids)) != len(oids) or oids[-1] != after or before in oids:
        return unavailable
    additions = deletions = 0
    for row in files:
        if type(row) is not dict:
            return unavailable
        add, delete = row.get("additions"), row.get("deletions")
        if type(add) is not int or type(delete) is not int or add < 0 or delete < 0:
            return unavailable
        additions += add
        deletions += delete
    return {"status": "ok", "reason": "verified_fast_forward_tree_diff",
            "additions": additions, "deletions": deletions, "commits": oids}


def present_recent_pushes(raw: Any) -> dict:
    """Project safe provider-validated observations into one public display contract."""
    if type(raw) is not dict or raw.get("status") not in {"ok", "partial"} or type(raw.get("rows")) is not list:
        return {"status": "unavailable", "complete": False, "rows": []}
    rows, identities = [], set()
    now = datetime.max.replace(tzinfo=timezone.utc)
    for event in raw["rows"][:3]:
        if type(event) is not dict:
            continue
        repo = event.get("repository")
        if type(repo) is not str or not _REPO.fullmatch(repo) or ".." in repo or repo in identities:
            continue
        checked = _safe_event(event, expected_repo=repo, observed_at=now)
        if checked is None:
            continue
        identities.add(repo)
        diff = event.get("diff") if type(event.get("diff")) is dict else {}
        status = diff.get("status")
        commits = diff.get("commits")
        diff_valid = (status == "ok" and checked["activity_type"] == "push"
                      and type(commits) is list and 0 < len(commits) <= _MAX_COMPARE_COMMITS
                      and all(type(c) is str and _OID.fullmatch(c) for c in commits)
                      and commits[-1] == checked["after"] and len(commits) == len(set(commits))
                      and all(type(diff.get(k)) is int and diff[k] >= 0 for k in ("additions", "deletions")))
        checked.update(diff_status="ok" if diff_valid else "unavailable",
                       additions=diff["additions"] if diff_valid else None,
                       deletions=diff["deletions"] if diff_valid else None,
                       commits=commits if diff_valid else [],
                       compare_url=f"https://github.com/{repo}/compare/{checked['before']}...{checked['after']}" if diff_valid else None,
                       head_url=f"https://github.com/{repo}/commit/{checked['after']}")
        checked.pop("before")  # Not necessary for the public display; compare URL binds it.
        rows.append(checked)
    rows.sort(key=lambda row: (row["timestamp"], row["id"], row["repository"]), reverse=True)
    complete = raw.get("complete") is True and raw.get("status") == "ok"
    return {"status": "ok" if complete else "partial", "complete": complete, "rows": rows,
            "meaning": "Latest observed push per repository; tree-diff values require verified before/after fast-forward compare"}

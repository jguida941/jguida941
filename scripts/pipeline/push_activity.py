"""Verified, bounded recent-push facts shared by README and website.

Repository push timestamps, push events, commits, and before/after tree diffs are
separate observations.  A commit is never inferred to belong to a push from a
branch head alone.  Repository-metadata hints remain partial observations and
cannot certify branch identity, the push's commit set, or an all-repository rank.
"""
from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any

_REPO = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]{1,100}\Z")
_OID = re.compile(r"[0-9a-f]{40}\Z")
_ID = re.compile(r"[A-Za-z0-9_-]{1,200}\Z")
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
            # GitHub repository identity is case-insensitive; choose newest
            # event before limiting the panel to three distinct repositories.
            identity = repository.casefold()
            key = (event["timestamp"], event["id"], event["ref"], event["after"],
                   event["repository"])
            if identity not in latest or key > latest[identity][0]:
                latest[identity] = (key, event)
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
        if type(repo) is not str or not _REPO.fullmatch(repo) or ".." in repo or repo.casefold() in identities:
            continue
        checked = _safe_event(event, expected_repo=repo, observed_at=now)
        if checked is None:
            continue
        identities.add(repo.casefold())
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
    # Completeness is a claim about the published selection, not merely the
    # caller's declared input. Rejecting/truncating a row loses that claim.
    complete = (raw.get("complete") is True and raw.get("status") == "ok"
                and len(rows) == len(raw["rows"]))
    return {"status": "ok" if complete else "partial", "complete": complete, "rows": rows,
            "meaning": "Latest observed push per repository; tree-diff values require verified before/after fast-forward compare"}

_GITHUB_REPO_URL = re.compile(
    r"https://github\.com/([A-Za-z0-9][A-Za-z0-9-]{0,38})/([A-Za-z0-9_.-]{1,100})\Z"
)


def qualify_recent_pushes(recent: Any, working: Any, generated_at: Any) -> dict:
    """Prefer observed push events; otherwise qualify seven-day metadata hints once.

    Metadata cannot prove global top-three, branch/commit identity, or line totals.
    """
    if type(recent) is dict and type(recent.get("rows")) is list and recent["rows"]:
        return recent
    as_of = _timestamp(generated_at)
    if as_of is None:
        return {"status": "unavailable", "complete": False,
                "reason": "metadata_cutoff_unavailable", "rows": []}
    chosen = {}
    for item in working if type(working) is list else []:
        if type(item) is not dict:
            continue
        name, url, pushed_at = (item.get("name"), item.get("html_url", item.get("url")),
                                item.get("pushed_at"))
        if type(name) is not str or type(url) is not str:
            continue
        match = _GITHUB_REPO_URL.fullmatch(url)
        if match is None or match[2] != name or name in {".", ".."}:
            continue
        when = _timestamp(pushed_at)
        if when is None or when > as_of:
            continue
        repo = match[1] + "/" + match[2]
        identity = repo.casefold()
        if identity not in chosen or when > chosen[identity][0]:
            chosen[identity] = (when, repo)
    ranked = sorted(chosen.values(), key=lambda pair: (-pair[0].timestamp(),
                                                     pair[1].casefold(), pair[1]))[:3]
    rows = [{"repository": repo, "timestamp": when.isoformat().replace("+00:00", "Z"),
             "activity_type": "repository_metadata", "metadata_only": True}
            for when, repo in ranked]
    # A complete empty event observation without qualified metadata is known
    # zero; the absence of an observation is not the same state.
    if (not rows and type(recent) is dict and recent.get("status") == "ok"
            and recent.get("complete") is True and recent.get("rows") == []):
        return recent
    return {"status": "partial" if rows else "unavailable", "complete": False,
            "reason": "repository_metadata_only_seven_day_cohort" if rows else "metadata_not_observed",
            "rows": rows,
            "meaning": "Reported repository push dates only; branch, commits and change totals unverified"}


_PROJECT_ACTIVITY_TYPES = _PUSH_TYPES | frozenset((
    "branch_creation", "branch_deletion", "pr_merge", "merge_queue_merge"))
_PROJECT_REPOSITORY_LIMIT = 20
_PROJECT_ACTIVITY_PAGE_LIMIT = 3
_PROJECT_COMPLETION = {
    ("end_of_connection", "no_next_link"),
    ("window_boundary", "descending_window_boundary"),
}


def _project_timestamp(value: Any) -> datetime | None:
    """Treat an unrepresentable UTC conversion as an invalid new observation."""
    try:
        return _timestamp(value)
    except OverflowError:
        return None


def _project_event(value: Any, repository: str, cutoff: datetime) -> dict | None:
    """Validate the normalized activity vocabulary before choosing push events.

    Lifecycle observations participate in identity reconciliation even though they
    never increment a push count. This keeps one conflicting ID from choosing its
    own meaning through input order or the push-only filter.
    """
    from scripts.github import github_client as gh
    from scripts.pipeline.profile_helpers import contains_credential_material

    if type(value) is not dict:
        return None
    identity, event_id = value.get("repository"), value.get("id")
    kind, ref = value.get("activity_type"), value.get("ref")
    occurred = _project_timestamp(value.get("timestamp"))
    if (type(identity) is not str or identity.casefold() != repository.casefold()
            or type(event_id) is not str or not _ID.fullmatch(event_id)
            or contains_credential_material(event_id) or type(kind) is not str or kind not in _PROJECT_ACTIVITY_TYPES
            or occurred is None or occurred > cutoff or not gh._valid_branch_ref(ref)
            or not gh._valid_branch_oid(value.get("before"), allow_zero=True)
            or not gh._valid_branch_oid(value.get("after"), allow_zero=kind == "branch_deletion")):
        return None
    return {"id": event_id, "repository": repository.casefold(), "activity_type": kind,
            "ref": ref, "timestamp": occurred.isoformat().replace("+00:00", "Z"),
            "before": value["before"], "after": value["after"]}


def qualify_project_activity(rows: Any, *, window_start: str, window_end: str,
                             observed_at: str, owner: str, profile_name: str) -> dict:
    """Reconcile all received branch observations without changing recent cards.

    The input is the existing collector's bounded normalized repository envelope.
    Complete daily coverage requires its terminal evidence, not a Boolean alone.
    The returned events are intermediate facts; the public model emits aggregates.
    """
    from scripts.pipeline.profile_helpers import contains_credential_material

    start, end, cutoff = (_timestamp(value) for value in (window_start, window_end, observed_at))
    if (type(rows) is not list or start is None or end is None or cutoff is None
            or not start <= end == cutoff):
        return {"rows": [], "reasons": ["observations_unavailable"], "received": 0,
                "valid_repositories": 0, "complete_repositories": 0}
    grouped, reasons = {}, set()
    for envelope in rows:
        repository = envelope.get("repository") if type(envelope) is dict else None
        if (type(repository) is not str or not _REPO.fullmatch(repository)
                or repository.split("/")[1] in {".", ".."}
                or contains_credential_material(repository)
                or repository.split("/")[0].casefold() != owner.casefold()
                or repository.split("/")[1].casefold() == profile_name.casefold()):
            reasons.add("invalid_repository_identity")
            continue
        identity = repository.casefold()
        group = grouped.setdefault(identity, {"spellings": set(), "envelopes": []})
        group["spellings"].add(repository)
        group["envelopes"].append(envelope)

    qualified = []
    for identity, group in grouped.items():
        repository = min(group["spellings"])
        observations, conflicts, metadata, row_reasons = {}, set(), set(), set()
        observed = False
        privacy = set()
        for envelope in group["envelopes"]:
            family = envelope.get("activity")
            if type(family) is not dict:
                row_reasons.add("activity_unavailable")
                continue
            events = family.get("rows")
            pages = family.get("page_count")
            observed_cutoff = _project_timestamp(family.get("observed_at"))
            private = envelope.get("is_private")
            if type(private) is bool:
                privacy.add(private)
            metadata_valid = (type(private) is bool
                              and ("name" not in envelope or type(envelope["name"]) is str
                                   and envelope["name"].casefold() == repository.split("/")[1].casefold()))
            if not metadata_valid:
                row_reasons.add("invalid_repository_metadata")
            header_valid = (family.get("source") == "github_rest_activity"
                            and observed_cutoff == cutoff and type(pages) is int
                            and 1 <= pages <= _PROJECT_ACTIVITY_PAGE_LIMIT
                            and type(events) is list)
            observed = observed or header_valid
            terminal = (family.get("reason"), family.get("completion_evidence"))
            complete = (header_valid and metadata_valid and family.get("status") == "ok"
                        and family.get("complete") is True and family.get("selection_valid") is True
                        and all(type(part) is str for part in terminal) and terminal in _PROJECT_COMPLETION)
            if not complete:
                row_reasons.add("incomplete_activity_coverage")
            # Only primitive normalized metadata can enter this comparison. A
            # malformed header already loses completeness without being hashable.
            metadata.add(tuple(repr(family.get(key)) for key in
                               ("status", "complete", "reason", "source", "page_count",
                                "selection_valid", "completion_evidence"))
                         + (observed_cutoff, private if type(private) is bool else None))
            if type(events) is not list:
                continue
            previous = None
            if len(events) > _PROJECT_ACTIVITY_PAGE_LIMIT * 100:
                row_reasons.add("activity_row_limit")
            for raw in events:
                event = _project_event(raw, repository, cutoff)
                if event is None:
                    row_reasons.add("invalid_activity_row")
                    event_id = raw.get("id") if type(raw) is dict else None
                    if type(event_id) is str and _ID.fullmatch(event_id):
                        conflicts.add(event_id)
                    continue
                occurred = _timestamp(event["timestamp"])
                if previous is not None and occurred > previous:
                    row_reasons.add("invalid_activity_order")
                previous = occurred
                event_id = event["id"]
                if event_id in observations and observations[event_id] != event:
                    conflicts.add(event_id)
                else:
                    observations[event_id] = event
        if len(metadata) > 1 or len(privacy) > 1:
            row_reasons.add("conflicting_repository_metadata")
        if conflicts:
            row_reasons.add("conflicting_activity_identity")
        events = [event for event_id, event in observations.items()
                  if event_id not in conflicts and event["activity_type"] in _PUSH_TYPES
                  and start <= _timestamp(event["timestamp"]) <= end]
        events.sort(key=lambda event: (_timestamp(event["timestamp"]), event["id"], event["ref"]))
        complete = not row_reasons
        qualified.append({"repository": repository, "is_private": next(iter(privacy)) if len(privacy) == 1 else None,
                          "complete": complete, "observed": observed,
                          "status": "ok" if complete else "partial" if observed or events else "unavailable",
                          "reasons": sorted(row_reasons), "events": events,
                          "latest_push": events[-1]["timestamp"] if events else None})
    qualified.sort(key=lambda row: (-_timestamp(row["latest_push"]).timestamp()
                                   if row["latest_push"] else float("inf"), row["repository"].casefold()))
    valid_count = len(qualified)
    if valid_count > _PROJECT_REPOSITORY_LIMIT:
        reasons.add("repository_limit")
        qualified = qualified[:_PROJECT_REPOSITORY_LIMIT]
    return {"rows": qualified, "reasons": sorted(reasons), "received": len(rows),
            "valid_repositories": valid_count,
            "complete_repositories": sum(row["complete"] for row in qualified)}

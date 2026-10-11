"""Bounded repository activity observations; no raw commit bodies or logs."""
from datetime import timedelta, timezone
import re
from urllib.parse import parse_qs, urlparse

import requests
from scripts.github import github_client as gh
from scripts.pipeline.profile_helpers import contains_credential_material, is_self_repo
from scripts.pipeline.push_activity import select_recent_pushes, interpret_fast_forward_comparison


def timestamp(value):
    return gh._branch_activity_time(value)


def iso(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def count(value):
    return value if type(value) is int and value >= 0 else None


def safe_text(value, limit=160):
    if type(value) is not str or contains_credential_material(value):
        return ""
    return " ".join(value.split())[:limit]


def repository_name(value):
    if type(value) is not str or len(value.split("/")) != 2:
        return None
    return gh._branch_repository_name(*value.split("/"))


def activity_row(raw, repository, cutoff):
    if type(raw) is not dict:
        return None
    kind, ref = raw.get("activity_type"), raw.get("ref")
    if type(ref) is str and ref.startswith("refs/tags/"):
        return {}
    if kind not in gh._BRANCH_ACTIVITY_TYPES | {"branch_deletion"}:
        return {} if type(kind) is str else None
    identity = raw.get("repository", repository)
    if isinstance(identity, dict):
        identity = identity.get("full_name")
    event_id = raw.get("id")
    if count(event_id) is not None:
        event_id = str(event_id)
    occurred = timestamp(raw.get("timestamp"))
    if (identity != repository or type(event_id) is not str
            or re.fullmatch(r"[A-Za-z0-9_-]{1,200}", event_id) is None
            or contains_credential_material(event_id) or occurred is None or occurred > cutoff
            or not gh._valid_branch_ref(ref) or not gh._valid_branch_oid(raw.get("before"), allow_zero=True)
            or not gh._valid_branch_oid(raw.get("after"), allow_zero=kind == "branch_deletion")):
        return None
    return {"id": event_id, "repository": repository, "activity_type": kind, "ref": ref,
            "before": raw["before"], "after": raw["after"], "timestamp": iso(occurred)}


def _family(now, source, **extra):
    return {"status": "unavailable", "complete": False, "reason": "not_observed",
            "observed_at": iso(now), "source": source, "page_count": 0,
            "completion_evidence": "none", "rows": [], **extra}


class _Requests:
    def __init__(self, now):
        self.now, self.stopped, self.failed, self.quota = now, False, False, None

    def observe_headers(self, response):
        headers = getattr(response, "headers", {}) or {}
        try:
            remaining, limit, reset = (int(headers[key]) for key in
                ("X-RateLimit-Remaining", "X-RateLimit-Limit", "X-RateLimit-Reset"))
            from datetime import datetime
            reset_at = datetime.fromtimestamp(reset, timezone.utc)
            if headers.get("X-RateLimit-Resource") == "core" and 0 <= remaining <= limit and limit > 0:
                self.quota = {"remaining": remaining, "limit": limit, "reset_at": iso(reset_at), "observed_at": iso(self.now)}
                self.stopped = self.stopped or remaining == 0
        except (KeyError, TypeError, ValueError, OverflowError, OSError):
            pass
        if getattr(response, "status_code", None) == 429 or (getattr(response, "status_code", None) == 403 and headers.get("Retry-After")):
            self.stopped = True

    def get(self, url, params):
        if self.stopped:
            return None, "rate_limited"
        try:
            response = gh._request_with_retry(url, params=params)
        except requests.RequestException as error:
            response = error.response
            if response is not None:
                self.observe_headers(response)
            self.failed = True
            return None, "rate_limited" if self.stopped else "request_failed"
        if response is not None:
            self.observe_headers(response)
        if response is None or response.status_code != 200:
            self.failed = True
            return None, "rate_limited" if self.stopped else "request_failed"
        return response, "observed"


def _next_page(response, endpoint, initial, seen):
    link = (getattr(response, "links", {}) or {}).get("next")
    if not link:
        return None, None
    url = link.get("url") if isinstance(link, dict) else None
    if type(url) is not str:
        return None, "invalid_cursor"
    parsed, expected = urlparse(url), urlparse(endpoint)
    query = parse_qs(parsed.query)
    if (parsed.scheme != expected.scheme or parsed.netloc != expected.netloc or parsed.path != expected.path
            or parsed.fragment or parsed.username or set(query) - {"page", "per_page", "created", "direction", "after", "before"}
            or any(len(values) != 1 for values in query.values())):
        return None, "invalid_cursor"
    for key, value in initial.items():
        if key in query and query[key] != [str(value)]:
            return None, "invalid_cursor"
    if url in seen:
        return None, "cursor_loop"
    return url, None


def _rest_history(repository, now, start, context):
    endpoint = f"{gh.API}/repos/{repository}/activity"
    initial = {"per_page": 100, "direction": "desc"}
    result = _family(now, "github_rest_activity", selection_valid=True)
    url, seen, invalid, previous, total = endpoint, set(), False, None, None
    for _ in range(3):
        seen.add(url)
        response, reason = context.get(url, initial)
        if response is None:
            result["reason"] = reason
            break
        try:
            payload = response.json()
        except ValueError:
            result["reason"] = "invalid_response"
            break
        rows = payload
        if type(rows) is not list or len(rows) > 100:
            result["reason"] = "invalid_response"
            break
        result["page_count"] += 1
        dates = []
        for raw in rows:
            value = activity_row(raw, repository, now)
            if value is None:
                invalid = True
                result["selection_valid"] = False
                continue
            if not value:
                continue
            occurred = timestamp(value["timestamp"])
            dates.append(occurred)
            if previous is not None and occurred > previous:
                invalid = True
                result["selection_valid"] = False
            previous = occurred
            if start <= occurred <= now:
                result["rows"].append(value)
        next_url, error = _next_page(response, endpoint, initial, seen)
        if error:
            result["reason"] = error
            break
        past_start = dates and min(dates) < start and not invalid
        if not next_url or past_start:
            result.update(complete=not invalid, reason="invalid_rows" if invalid else "window_boundary" if past_start else "end_of_connection",
                          completion_evidence="descending_window_boundary" if past_start else "no_next_link")
            break
        url = next_url
    else:
        result["reason"] = "page_limit"
    result["status"] = "ok" if result["complete"] else "partial" if result["page_count"] else "unavailable"
    if invalid:
        result.update(complete=False, status="partial", reason="invalid_rows")
    return result


def _latest_activity(family):
    if not family.get("selection_valid"):
        return None
    unique, deletions = {}, {}
    for row in family["rows"]:
        if row["id"] in unique and unique[row["id"]] != row:
            family.update(selection_valid=False, complete=False, status="partial", reason="conflicting_activity")
            return None
        unique[row["id"]] = row
        if row["activity_type"] == "branch_deletion":
            occurred = timestamp(row["timestamp"])
            deletions[row["ref"]] = max(deletions.get(row["ref"], occurred), occurred)
    candidates = [row for row in unique.values() if row["activity_type"] in gh._BRANCH_ACTIVITY_TYPES
                  and (row["ref"] not in deletions or timestamp(row["timestamp"]) > deletions[row["ref"]])]
    return max(candidates, key=lambda row: (timestamp(row["timestamp"]), row["id"], row["ref"], row["after"], row["before"], row["activity_type"])) if candidates else None


_HISTORY_QUERY = """query($owner: String!, $name: String!, $oid: GitObjectID!, $since: GitTimestamp!, $until: GitTimestamp!, $cursor: String) {
  repository(owner: $owner, name: $name) { nameWithOwner object(oid: $oid) { ... on Commit {
    oid history(first: 100, after: $cursor, since: $since, until: $until) {
      nodes { oid committedDate additions deletions parents { totalCount } }
      pageInfo { hasNextPage endCursor }
    }
  } } }
}"""


def _code_history(selected, start, now, context):
    result = _family(now, "github_graphql_commit_history", commits=[])
    result.pop("rows")
    if selected is None:
        result["reason"] = "branch_unavailable"
        return result
    repository, event = selected
    result.update(repository=repository, ref=event["ref"], head_sha=event["after"], occurred_at=event["timestamp"],
                  commit_url=f"https://github.com/{repository}/commit/{event['after']}")
    owner, name = repository.split("/")
    variables = {"owner": owner, "name": name, "oid": event["after"], "since": iso(start), "until": iso(now), "cursor": None}
    seen = set()
    query = _HISTORY_QUERY
    for _ in range(10):
        if context.stopped:
            result["reason"] = "rate_limited"
            break
        try:
            payload = gh._graphql_query(query, variables)
        except requests.RequestException:
            payload = None
        if payload is None and query == _HISTORY_QUERY:
            # A smaller page may fit the provider's processing budget. Retry the
            # same anchored request once; this failed attempt still uses budget.
            query = _HISTORY_QUERY.replace("history(first: 100,", "history(first: 10,")
            continue
        repo = payload.get("repository") if type(payload) is dict else None
        obj = repo.get("object") if type(repo) is dict else None
        history = obj.get("history") if type(obj) is dict else None
        if (type(repo) is not dict or repo.get("nameWithOwner") != repository or type(obj) is not dict
                or obj.get("oid") != event["after"] or type(history) is not dict
                or type(history.get("nodes")) is not list or len(history["nodes"]) > 100
                or type(history.get("pageInfo")) is not dict):
            result["reason"] = "history_unavailable"
            context.failed = True
            break
        result["page_count"] += 1
        invalid = False
        for row in history["nodes"]:
            if type(row) is not dict or not gh._valid_branch_oid(row.get("oid")):
                invalid = True
                continue
            occurred = timestamp(row.get("committedDate"))
            if occurred is None or occurred > now:
                invalid = True
                continue
            if occurred < start:
                continue
            result["commits"].append({"oid": row["oid"], "committed_at": iso(occurred),
                "additions": count(row.get("additions")), "deletions": count(row.get("deletions")),
                "parent_count": count((row.get("parents") or {}).get("totalCount")) if type(row.get("parents")) is dict else None})
        result["invalid_rows"] = result.get("invalid_rows", False) or invalid
        info = history["pageInfo"]
        if info.get("hasNextPage") is False:
            result.update(complete=not result["invalid_rows"], reason="invalid_rows" if result["invalid_rows"] else "end_of_connection",
                          completion_evidence="hasNextPage_false")
            break
        cursor = info.get("endCursor")
        if info.get("hasNextPage") is not True or type(cursor) is not str or not cursor or cursor in seen:
            result["reason"] = "invalid_cursor"
            break
        seen.add(cursor)
        variables = {**variables, "cursor": cursor}
    else:
        result["reason"] = "page_limit"
    result["status"] = "ok" if result["complete"] else "partial" if result["page_count"] else "unavailable"
    return result


def collect_activity_observations(public_repos, private_repos, repo_counts, *, observed_at, inventory_fresh=True):
    """Observe at most twenty selected recently pushed owned repositories."""
    now = observed_at.astimezone(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=29)
    candidates, excluded = {}, {"identity": 0, "fork": 0, "profile": 0, "outside_window": 0, "invalid_hint": 0}
    for raw in list(public_repos) + list(private_repos):
        if type(raw) is not dict:
            excluded["identity"] += 1
            continue
        owner = (raw.get("owner") or {}).get("login") if type(raw.get("owner")) is dict else None
        repository = gh._branch_repository_name(owner, raw.get("name"))
        if not repository or owner.casefold() != gh.USERNAME.casefold():
            excluded["identity"] += 1
            continue
        if raw.get("fork") is True:
            excluded["fork"] += 1
            continue
        if is_self_repo(raw.get("name")):
            excluded["profile"] += 1
            continue
        pushed = timestamp(raw.get("pushed_at"))
        if pushed is None or pushed > now:
            excluded["invalid_hint"] += 1
            continue
        if pushed < start:
            excluded["outside_window"] += 1
            continue
        candidates[repository] = (pushed, raw)
    selected = sorted(candidates, key=lambda name: (-candidates[name][0].timestamp(), name.casefold(), name))[:20]
    context, rows, latest = _Requests(now), [], []
    for repository in selected:
        raw = candidates[repository][1]
        activity = _rest_history(repository, now, start, context)
        rows.append({"repository": repository, "name": repository.split("/")[1], "language": safe_text(raw.get("language"), 60),
                     "is_private": raw.get("private") is True, "activity": activity})
        event = _latest_activity(activity)
        if event:
            latest.append((repository, event))
    spotlight = max(latest, key=lambda item: (timestamp(item[1]["timestamp"]), item[1]["id"], item[1]["ref"], item[1]["after"], item[1]["before"], item[1]["activity_type"], item[0])) if latest else None
    code = _code_history(spotlight, start, now, context)
    expected = [repo_counts.get("public_owned_nonfork"), repo_counts.get("private_owned_nonfork")]
    inventory_complete = all(count(value) is not None for value in expected) and sum(expected) == len(public_repos) + len(private_repos)
    cohort = {"inventory": len(public_repos) + len(private_repos), "inventory_complete": inventory_complete,
              "eligible": len(candidates), "selected": len(selected), "queried": sum(bool(row["activity"]["page_count"]) for row in rows),
              "excluded": {**excluded, "selection_limit": max(0, len(candidates) - len(selected))}}
    cohort["inventory_fresh"] = inventory_fresh is True
    coverage = ["complete" if row["activity"]["complete"] else
                "unavailable" if row["activity"]["status"] == "unavailable" else "partial" for row in rows]
    for state in ("complete", "partial", "unavailable"):
        cohort[state] = coverage.count(state)
    reasons = []
    if not inventory_complete: reasons.append("inventory_incomplete")
    if inventory_fresh is not True: reasons.append("inventory_not_fresh")
    if excluded["identity"] or excluded["invalid_hint"]: reasons.append("invalid_inventory")
    if cohort["excluded"]["selection_limit"]: reasons.append("candidate_limit")
    failures = [{"repository": row["repository"], "reason": row["activity"]["reason"]}
                for row in rows if not row["activity"]["complete"] or not row["activity"]["selection_valid"]]
    if failures: reasons.append("activity_incomplete")
    selection = {"status": "ok" if not reasons else "partial" if spotlight else "unavailable",
                 "complete": not reasons, "reason": ", ".join(reasons) or "observed",
                 "activity_failures": failures, "occurred_at": code.get("occurred_at")}
    # A push is a separate event, not the whole history of its after-head.
    # Only a bounded verified fast-forward can yield honest tree-diff totals.
    recent_pushes = select_recent_pushes(
        rows, observed_at=iso(now), coverage_complete=selection["complete"])
    for pushed in recent_pushes["rows"]:
        if pushed["activity_type"] != "push" or pushed["before"] == "0" * 40:
            continue
        url = (f"{gh.API}/repos/{pushed['repository']}/compare/"
               f"{pushed['before']}...{pushed['after']}")
        response, _reason = context.get(url, {})
        if response is None:
            continue
        try:
            comparison = response.json()
        except ValueError:
            comparison = None
        pushed["diff"] = interpret_fast_forward_comparison(
            comparison, before=pushed["before"], after=pushed["after"],
            has_next_page=bool((getattr(response, "links", {}) or {}).get("next")))
    return {"schema": "profile-activity-observations/v1", "window_start": iso(start), "window_end": iso(now), "observed_at": iso(now),
            "cohort": cohort, "repositories": rows, "code_changes": code, "selection": selection,
            "recent_pushes": recent_pushes,
            "requests": {"status": "partial" if context.stopped or context.failed else "ok", "rest_core": context.quota}}

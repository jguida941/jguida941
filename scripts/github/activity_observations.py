"""Bounded push and owned-head activity observations, without commit bodies."""
from collections import deque
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


# These are collection budgets, not claims about GitHub's platform limits.
_OWNED_QUERY_LIMIT = 400
_OWNED_BATCH_SIZE = 8
_OWNED_REF_PAGES = 3
_OWNED_HISTORY_PAGES = 100
_OWNED_HISTORY_SIZE = 10
_OWNED_QUOTA_RESERVE = 100


class _OwnedRequests:
    """Count transport invocations; internal HTTP/token retries belong to transport."""

    def __init__(self):
        self.used = 0
        self.remaining = None
        self.reason = "observed"

    def available(self):
        if self.used >= _OWNED_QUERY_LIMIT:
            self.reason = "request_limit"
            return False
        if self.remaining is not None and self.remaining < _OWNED_QUOTA_RESERVE:
            self.reason = "rate_limited"
            return False
        return True

    def query(self, query, variables):
        if not self.available():
            return None
        self.used += 1
        try:
            payload = gh._graphql_query(query, variables)
        except (requests.RequestException, ValueError):
            payload = None
        quota = payload.get("rateLimit") if type(payload) is dict else None
        if type(quota) is dict:
            remaining, limit = count(quota.get("remaining")), count(quota.get("limit"))
            if (remaining is not None and limit is not None and limit > 0
                    and remaining <= limit and timestamp(quota.get("resetAt")) is not None):
                self.remaining = remaining
        return payload if type(payload) is dict else None


def _owned_query(jobs, kind, start, now):
    declarations, selections, variables = [], [], {}
    if kind == "history":
        declarations.extend(("$since: GitTimestamp!", "$until: GitTimestamp!"))
        variables.update(since=iso(start), until=iso(now))
    for index, job in enumerate(jobs):
        owner, name = job["repository"].split("/")
        declarations.extend((f"$owner{index}: String!", f"$name{index}: String!",
                             f"$cursor{index}: String"))
        variables.update({f"owner{index}": owner, f"name{index}": name,
                          f"cursor{index}": job["cursor"]})
        if kind == "refs":
            body = f'''refs(refPrefix: "refs/heads/", first: 100, after: $cursor{index}) {{
                totalCount nodes {{ name prefix target {{ __typename oid }} }}
                pageInfo {{ hasNextPage endCursor }}
            }}'''
        else:
            declarations.append(f"$oid{index}: GitObjectID!")
            variables[f"oid{index}"] = job["result"]["head_sha"]
            body = f'''object(oid: $oid{index}) {{ ... on Commit {{
                oid history(first: {_OWNED_HISTORY_SIZE}, after: $cursor{index}, since: $since, until: $until) {{
                    nodes {{ oid committedDate additions deletions parents(first: 1) {{ totalCount }} }}
                    pageInfo {{ hasNextPage endCursor }}
                }}
            }} }}'''
        selections.append(f"r{index}: repository(owner: $owner{index}, name: $name{index}) {{ nameWithOwner {body} }}")
    return ("query(" + ", ".join(declarations) + ") { " + " ".join(selections)
            + " rateLimit { remaining limit resetAt } }", variables)


def _owned_responses(jobs, kind, start, now, requests):
    """Retry one failed batch as single requests, against the same call budget."""
    query, variables = _owned_query(jobs, kind, start, now)
    payload = requests.query(query, variables)
    if payload is not None:
        return [payload.get(f"r{index}") for index in range(len(jobs))]
    if len(jobs) == 1:
        return [None]
    results = []
    for job in jobs:
        query, variables = _owned_query([job], kind, start, now)
        payload = requests.query(query, variables)
        results.append(payload.get("r0") if payload is not None else None)
    return results


def _owned_inventory(public_repos, private_repos, repo_counts, inventory_fresh):
    excluded = {"identity": 0, "fork": 0, "profile": 0, "privacy": 0,
                "unknown_fork": 0, "duplicate": 0}
    candidates, conflicting, partition_counts = {}, set(), []
    valid_inventory = True
    for rows, private in ((public_repos, False), (private_repos, True)):
        observed = set()
        for raw in rows:
            owner = (raw.get("owner") or {}).get("login") if type(raw) is dict and type(raw.get("owner")) is dict else None
            repository = gh._branch_repository_name(owner, raw.get("name")) if type(raw) is dict else None
            if not repository or owner.casefold() != gh.USERNAME.casefold():
                excluded["identity"] += 1
                valid_inventory = False
                continue
            if type(raw.get("fork")) is not bool:
                excluded["unknown_fork"] += 1
                valid_inventory = False
                continue
            if raw["fork"]:
                excluded["fork"] += 1
                continue
            key = repository.casefold()
            if key in observed:
                excluded["duplicate"] += 1
                valid_inventory = False
            observed.add(key)
            if type(raw.get("private")) is not bool or raw["private"] != private:
                excluded["privacy"] += 1
                valid_inventory = False
                conflicting.add(key)
                continue
            if is_self_repo(raw["name"]):
                excluded["profile"] += 1
                continue
            if key in candidates and candidates[key][1]["private"] != private:
                conflicting.add(key)
                valid_inventory = False
            elif key not in candidates:
                candidates[key] = (repository, raw)
        partition_counts.append(len(observed))
    for key in conflicting:
        candidates.pop(key, None)
    expected_parts = [count(repo_counts.get("public_owned_nonfork")),
                      count(repo_counts.get("private_owned_nonfork"))]
    counts_known = all(value is not None for value in expected_parts)
    expected = sum(expected_parts) if counts_known else None
    inventory = {"expected": expected, "eligible": len(candidates),
                 "complete": valid_inventory and counts_known and partition_counts == expected_parts,
                 "fresh": inventory_fresh is True, "excluded": excluded}
    # Push metadata determines scheduling only; quiet or undated repositories
    # remain in the annual population.
    def order(item):
        repository, raw = item
        pushed = timestamp(raw.get("pushed_at"))
        return (-(pushed.timestamp() if pushed is not None else 0), repository.casefold())
    return sorted(candidates.values(), key=order), inventory


def _owned_page_cursor(info, job):
    if info.get("hasNextPage") is False:
        return None, None
    cursor = info.get("endCursor")
    if (info.get("hasNextPage") is not True or type(cursor) is not str or not cursor
            or cursor in job["seen"]):
        return None, "invalid_cursor"
    job["seen"].add(cursor)
    return cursor, None


def _owned_refs_page(job, payload):
    result = job["result"]
    refs = payload.get("refs") if type(payload) is dict else None
    if (type(payload) is not dict or repository_name(payload.get("nameWithOwner")) is None
            or payload["nameWithOwner"].casefold() != job["repository"].casefold()
            or type(refs) is not dict or type(refs.get("nodes")) is not list
            or len(refs["nodes"]) > 100 or type(refs.get("pageInfo")) is not dict
            or count(refs.get("totalCount")) is None):
        result["reason"] = "refs_unavailable"
        return False
    result["page_count"] += 1
    total = refs["totalCount"]
    if result["total_count"] is not None and result["total_count"] != total:
        job["invalid"] = True
    result["total_count"] = total
    for node in refs["nodes"]:
        target = node.get("target") if type(node) is dict else None
        ref = "refs/heads/" + node["name"] if type(node) is dict and type(node.get("name")) is str else None
        if (type(node) is not dict or node.get("prefix") != "refs/heads/"
                or not gh._valid_branch_ref(ref) or type(target) is not dict
                or target.get("__typename") != "Commit" or not gh._valid_branch_oid(target.get("oid"))):
            job["invalid"] = True
            continue
        if ref in job["heads"] or ref in job["conflicts"]:
            job["invalid"] = True
            if job["heads"].get(ref) != target["oid"]:
                job["conflicts"].add(ref)
                job["heads"].pop(ref, None)
        elif ref not in job["conflicts"]:
            job["heads"][ref] = target["oid"]
    result["heads"] = [{"ref": ref, "head_sha": oid} for ref, oid in job["heads"].items()]
    cursor, error = _owned_page_cursor(refs["pageInfo"], job)
    if error:
        result["reason"] = error
    elif cursor is None:
        complete = not job["invalid"] and len(job["heads"]) == total
        result.update(complete=complete, reason="end_of_connection" if complete else "invalid_refs")
    elif result["page_count"] >= _OWNED_REF_PAGES:
        result["reason"] = "ref_page_limit"
    else:
        job["cursor"] = cursor
        return True
    return False


def _owned_history_page(job, payload, start, now):
    result = job["result"]
    obj = payload.get("object") if type(payload) is dict else None
    history = obj.get("history") if type(obj) is dict else None
    if (type(payload) is not dict or repository_name(payload.get("nameWithOwner")) is None
            or payload["nameWithOwner"].casefold() != job["repository"].casefold()
            or type(obj) is not dict or obj.get("oid") != result["head_sha"]
            or type(history) is not dict or type(history.get("nodes")) is not list
            or len(history["nodes"]) > _OWNED_HISTORY_SIZE or type(history.get("pageInfo")) is not dict):
        result["reason"] = "history_unavailable"
        return False
    result["page_count"] += 1
    for row in history["nodes"]:
        occurred = timestamp(row.get("committedDate")) if type(row) is dict else None
        if type(row) is not dict or not gh._valid_branch_oid(row.get("oid")):
            job["invalid"] = True
            continue
        if occurred is None or occurred > now:
            job["invalid"] = True
        parents = row.get("parents")
        # Keep the OID even when its date is rejected, so the aggregate can
        # quarantine a contradictory duplicate instead of reviving another copy.
        value = {"oid": row["oid"], "committed_at": iso(occurred) if occurred is not None else None,
                 "additions": count(row.get("additions")), "deletions": count(row.get("deletions")),
                 "parent_count": count(parents.get("totalCount")) if type(parents) is dict else None}
        if any(value[key] is None for key in ("additions", "deletions", "parent_count")):
            job["invalid"] = True
        result["commits"].append(value)
    cursor, error = _owned_page_cursor(history["pageInfo"], job)
    if error:
        result["reason"] = error
    elif cursor is None:
        result.update(complete=not job["invalid"], reason="invalid_rows" if job["invalid"] else "end_of_connection")
    elif result["page_count"] >= _OWNED_HISTORY_PAGES:
        result["reason"] = "history_page_limit"
    else:
        job["cursor"] = cursor
        return True
    return False


def _owned_collect_queue(queue, kind, start, now, requests):
    while queue and requests.available():
        jobs = [queue.popleft() for _ in range(min(_OWNED_BATCH_SIZE, len(queue)))]
        payloads = _owned_responses(jobs, kind, start, now, requests)
        for job, payload in zip(jobs, payloads):
            again = (_owned_refs_page(job, payload) if kind == "refs"
                     else _owned_history_page(job, payload, start, now))
            if again:
                queue.append(job)
            result = job["result"]
            result["status"] = "ok" if result["complete"] else "partial" if result["page_count"] else "unavailable"
            if payload is None and requests.reason != "observed":
                result["reason"] = requests.reason
    for job in queue:
        result = job["result"]
        result.update(complete=False, reason=requests.reason,
                      status="partial" if result["page_count"] else "unavailable")


def _collect_owned_code_activity(public_repos, private_repos, repo_counts, now, inventory_fresh):
    start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=364)
    candidates, inventory = _owned_inventory(public_repos, private_repos, repo_counts, inventory_fresh)
    requests, repositories, refs_queue = _OwnedRequests(), [], deque()
    for repository, raw in candidates:
        refs = {"status": "unavailable", "complete": False, "reason": "not_observed",
                "total_count": None, "heads": [], "page_count": 0}
        repositories.append({"repository": repository, "private": raw["private"], "refs": refs, "histories": []})
        refs_queue.append({"repository": repository, "result": refs, "cursor": None,
                           "seen": set(), "invalid": False, "heads": {}, "conflicts": set()})
    _owned_collect_queue(refs_queue, "refs", start, now, requests)
    by_repository = []
    for row in repositories:
        heads = dict.fromkeys(head["head_sha"] for head in row["refs"]["heads"])
        jobs = deque()
        for head in heads:
            result = {"head_sha": head, "status": "unavailable", "complete": False,
                      "reason": "not_observed", "commits": [], "page_count": 0}
            row["histories"].append(result)
            jobs.append({"repository": row["repository"], "result": result,
                         "cursor": None, "seen": set(), "invalid": False})
        by_repository.append(jobs)
    # Start one head per repository before second heads; then rotate each page
    # behind the other queued heads so a large history cannot starve the roster.
    history_queue = deque()
    while any(by_repository):
        for jobs in by_repository:
            if jobs:
                history_queue.append(jobs.popleft())
    _owned_collect_queue(history_queue, "history", start, now, requests)
    return {"schema": "profile-owned-code-observations/v1", "window_start": iso(start),
            "window_end": iso(now), "observed_at": iso(now), "inventory": inventory,
            "repositories": repositories,
            "requests": {"used": requests.used, "limit": _OWNED_QUERY_LIMIT,
                         "remaining": requests.remaining, "reason": requests.reason}}


def collect_activity_observations(public_repos, private_repos, repo_counts, *, observed_at, inventory_fresh=True):
    """Observe bounded recent pushes and annual histories of owned branch heads."""
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
            "overall_code_changes": _collect_owned_code_activity(public_repos, private_repos, repo_counts, now, inventory_fresh),
            "requests": {"status": "partial" if context.stopped or context.failed else "ok", "rest_core": context.quota}}

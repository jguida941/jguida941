"""Pure selected-branch and owned-head projections of bounded observations."""
from datetime import timedelta
from scripts.github import github_client as gh
from scripts.github.activity_observations import count, iso, repository_name, timestamp
from scripts.pipeline.profile_helpers import is_self_repo
from scripts.pipeline.push_activity import present_recent_pushes, qualify_project_activity


def _status(complete, observed):
    return "ok" if complete else "partial" if observed else "unavailable"


_MAX_EXACT_INTEGER = 2**53 - 1
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
_OWNED_MEANING = ("Repository activity · all authors · owned public and private nonfork repositories; "
                  "profile excluded. Summed distinct non-merge commit line changes reachable from "
                  "branch heads observed during collection, by committed date; not net tree size "
                  "or all commits ever pushed. Deleted and unreachable branches are outside this scope.")


def _exact_count(value):
    value = count(value)
    return value if value is not None and value <= _MAX_EXACT_INTEGER else None


def _owned_window(start, end, commits, complete):
    """Own both temporal bins and exact totals; renderers only place this data."""
    dates = [(start.date() + timedelta(days=index)).isoformat()
             for index in range((end.date() - start.date()).days + 1)]
    days = {day: {"date": day, "additions": 0, "deletions": 0,
                  "complete": complete, "stats_observed": 0} for day in dates}
    nonmerges = observed_stats = excluded_merges = observed_commits = 0
    for row in commits.values():
        if not start <= row["time"] <= end:
            continue
        observed_commits += 1
        if row["parent_count"] is None:
            continue
        if row["parent_count"] > 1:
            excluded_merges += 1
            continue
        nonmerges += 1
        if row["additions"] is None or row["deletions"] is None:
            continue
        observed_stats += 1
        day = days[row["time"].date().isoformat()]
        day["stats_observed"] += 1
        day["additions"] += row["additions"]
        day["deletions"] += row["deletions"]
    added = sum(day["additions"] for day in days.values())
    deleted = sum(day["deletions"] for day in days.values())
    overflow = added > _MAX_EXACT_INTEGER or deleted > _MAX_EXACT_INTEGER
    complete = complete and not overflow
    for day in days.values():
        day["complete"] = complete
        if (not complete and not day["stats_observed"]
                or day["additions"] > _MAX_EXACT_INTEGER or day["deletions"] > _MAX_EXACT_INTEGER):
            day["additions"] = day["deletions"] = None
        day.pop("stats_observed")
    daily = list(days.values())
    bucket_size = 7 if len(daily) == 365 else 1
    bins = []
    for first in range(0, len(daily), bucket_size):
        rows = daily[first:first + bucket_size]
        bucket = {"date": rows[0]["date"], "end_date": rows[-1]["date"],
                  "day_index": first, "end_day_index": first + len(rows) - 1,
                  "complete": all(row["complete"] for row in rows)}
        for key in ("additions", "deletions"):
            known = [row[key] for row in rows if row[key] is not None]
            total = sum(known)
            bucket[key] = total if known and total <= _MAX_EXACT_INTEGER else None
            bucket["complete"] = bucket["complete"] and len(known) == len(rows) and bucket[key] is not None
        bins.append(bucket)
    months = []
    for index, row in enumerate(daily):
        day = start.date() + timedelta(days=index)
        if index == 0 or day.day == 1:
            months.append({"date": row["date"], "day_index": index, "label": _MONTHS[day.month - 1]})
    available = not overflow and (complete or observed_stats > 0)
    return {"window_start": iso(start), "window_end": iso(end), "current_day_partial": True,
            "status": _status(complete, available), "complete": complete,
            "additions": added if available else None, "deletions": deleted if available else None,
            "observed_commits": observed_commits, "commit_count": nonmerges,
            "stats_observed": observed_stats, "excluded_merges": excluded_merges,
            "daily": daily, "bins": bins, "month_labels": months,
            "reason": "unsafe_integer_total" if overflow else "observed" if complete else "incomplete_coverage"}


def _build_owned_code_activity(source):
    source = source if type(source) is dict else {}
    start, end = timestamp(source.get("window_start")), timestamp(source.get("window_end"))
    observed = timestamp(source.get("observed_at"))
    valid_window = bool(source.get("schema") == "profile-owned-code-observations/v1"
                        and start is not None and end is not None and observed is not None
                        and start <= end <= observed and (end.date() - start.date()).days == 364
                        and start.hour == start.minute == start.second == start.microsecond == 0)
    inventory = source.get("inventory") if type(source.get("inventory")) is dict else {}
    expected, eligible = count(inventory.get("expected")), count(inventory.get("eligible"))
    coverage = {"expected": expected, "eligible": eligible, "repositories_observed": 0,
                "repositories_complete": 0, "branches_observed": 0, "branches_complete": 0,
                "conflicting_commits": 0, "reasons": []}
    reasons = set()
    if not valid_window:
        reasons.add("invalid_window")
    if (inventory.get("complete") is not True or expected is None or eligible is None
            or expected < eligible):
        reasons.add("inventory_incomplete")
    if inventory.get("fresh") is not True:
        reasons.add("inventory_not_fresh")
    excluded = inventory.get("excluded") if type(inventory.get("excluded")) is dict else {}
    coverage["excluded"] = {key: count(excluded.get(key)) for key in ("fork", "profile", "identity", "privacy", "unknown_fork", "duplicate")}
    # Omitted optional diagnostics are compatible; supplied uncertainty cannot prove quiet dates.
    if ("excluded" in inventory and type(inventory["excluded"]) is not dict
            or any(key in excluded and value is None for key, value in coverage["excluded"].items())):
        reasons.add("invalid_inventory_exclusions")
    if any(coverage["excluded"][key] for key in ("identity", "privacy", "unknown_fork", "duplicate")):
        reasons.add("uncertain_inventory_exclusions")
    requests = source.get("requests") if type(source.get("requests")) is dict else {}
    used, limit, remaining = count(requests.get("used")), count(requests.get("limit")), count(requests.get("remaining"))
    coverage["requests"] = {"used": used, "limit": limit, "remaining": remaining}
    if used is None or limit is None or limit < 1 or used > limit:
        reasons.add("invalid_request_accounting")
    if requests.get("reason") in ("request_limit", "rate_limited"):
        reasons.add(requests["reason"])
    raw_repositories = source.get("repositories")
    if type(raw_repositories) is not list:
        raw_repositories = []
        reasons.add("invalid_repository_roster")
    identities, duplicates = {}, set()
    for raw in raw_repositories:
        repository = repository_name(raw.get("repository")) if type(raw) is dict else None
        if (not repository or repository.split("/")[0].casefold() != gh.USERNAME.casefold()
                or is_self_repo(repository.split("/")[1]) or type(raw.get("private")) is not bool):
            reasons.add("invalid_repository_identity")
            continue
        key = repository.casefold()
        if key in identities:
            duplicates.add(key)
        else:
            identities[key] = raw
    if duplicates:
        reasons.add("duplicate_repository")
        for key in duplicates:
            identities.pop(key)
    if eligible is None or len(identities) != eligible:
        reasons.add("repository_roster_incomplete")
    commits, observations, conflicts, commit_owners, invalid_repositories = {}, {}, set(), {}, set()
    repository_states = {}
    for key, raw in identities.items():
        refs = raw.get("refs") if type(raw.get("refs")) is dict else {}
        head_rows = refs.get("heads")
        heads, duplicate_refs = {}, set()
        refs_valid = type(head_rows) is list
        for head in head_rows if refs_valid else []:
            ref = head.get("ref") if type(head) is dict else None
            oid = head.get("head_sha") if type(head) is dict else None
            if not gh._valid_branch_ref(ref) or not gh._valid_branch_oid(oid):
                refs_valid = False
                continue
            if ref in heads:
                duplicate_refs.add(ref)
                refs_valid = False
            else:
                heads[ref] = oid
        for ref in duplicate_refs:
            heads.pop(ref, None)
        refs_complete = (refs_valid and refs.get("complete") is True and refs.get("status") == "ok"
                         and refs.get("reason") == "end_of_connection"
                         and count(refs.get("total_count")) == len(heads))
        coverage["branches_observed"] += len(heads)
        if not refs_complete:
            reasons.add("branch_roster_incomplete")
            if refs.get("reason") in ("invalid_cursor", "ref_page_limit", "request_limit", "rate_limited"):
                reasons.add(refs["reason"])
        histories = raw.get("histories")
        if type(histories) is not list:
            histories = []
            invalid_repositories.add(key)
            reasons.add("invalid_history_roster")
        expected_heads, head_complete, seen_heads = set(heads.values()), {}, set()
        repository_observed = refs_complete and not heads
        for history in histories:
            head = history.get("head_sha") if type(history) is dict else None
            if not gh._valid_branch_oid(head) or head not in expected_heads:
                invalid_repositories.add(key)
                reasons.add("unanchored_history")
                continue
            if head in seen_heads:
                invalid_repositories.add(key)
                reasons.add("duplicate_history")
            seen_heads.add(head)
            rows = history.get("commits")
            valid = (history.get("status") in ("ok", "partial") and type(rows) is list)
            complete = (valid and history.get("complete") is True and history.get("status") == "ok"
                        and history.get("reason") == "end_of_connection")
            repository_observed = repository_observed or valid
            if history.get("reason") in ("invalid_cursor", "history_page_limit", "request_limit", "rate_limited"):
                reasons.add(history["reason"])
            if not valid or not valid_window:
                head_complete[head] = False
                continue
            for row in rows:
                oid = row.get("oid") if type(row) is dict else None
                occurred = timestamp(row.get("committed_at")) if type(row) is dict else None
                if not gh._valid_branch_oid(oid):
                    complete = False
                    invalid_repositories.add(key)
                    reasons.add("invalid_commit_row")
                    continue
                value = {"time": occurred, "parent_count": _exact_count(row.get("parent_count")),
                         "additions": _exact_count(row.get("additions")), "deletions": _exact_count(row.get("deletions"))}
                commit_owners.setdefault(oid, set()).add(key)
                if oid in conflicts:
                    invalid_repositories.update(commit_owners[oid])
                elif oid in observations and observations[oid] != value:
                    conflicts.add(oid)
                    commits.pop(oid, None)
                    invalid_repositories.update(commit_owners[oid])
                else:
                    observations[oid] = value
                if occurred is None or occurred > end:
                    complete = False
                    invalid_repositories.add(key)
                    reasons.add("invalid_commit_row")
                    continue
                if occurred < start:
                    continue
                if any(value[field] is None for field in ("parent_count", "additions", "deletions")):
                    complete = False
                    invalid_repositories.add(key)
                    reasons.add("invalid_commit_stats")
                if oid not in conflicts:
                    commits[oid] = value
            head_complete[head] = complete and head_complete.get(head, True)
        if set(head_complete) != expected_heads or not all(head_complete.values()):
            reasons.add("history_incomplete")
        branches_complete = sum(bool(head_complete.get(head)) for head in heads.values())
        repository_complete = refs_complete and set(head_complete) == expected_heads and all(head_complete.values())
        repository_states[key] = (repository_observed, repository_complete, branches_complete)
    if conflicts:
        reasons.add("conflicting_commit_observations")
    coverage["conflicting_commits"] = len(conflicts)
    for key, (observed_repo, complete_repo, branches_complete) in repository_states.items():
        coverage["repositories_observed"] += int(observed_repo)
        coverage["repositories_complete"] += int(complete_repo and key not in invalid_repositories)
        coverage["branches_complete"] += branches_complete if key not in invalid_repositories else 0
    complete = not reasons
    windows = {}
    if valid_window:
        for period, window_start in (("30d", end.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=29)),
                                     ("365d", start)):
            windows[period] = _owned_window(window_start, end, commits, complete)
        if any(window["reason"] == "unsafe_integer_total" for window in windows.values()):
            reasons.add("unsafe_integer_total")
            complete = False
    coverage["reasons"] = sorted(reasons)
    available = any(window["additions"] is not None for window in windows.values())
    return {"schema": "profile-owned-code-analytics/v1", "status": _status(complete, available),
            "complete": complete, "meaning": _OWNED_MEANING, "coverage": coverage, "windows": windows}


_PROJECT_MEANING = (
    "Observed branch pushes · UTC. Repository activity from all actors represented in the "
    "received branch feed; owned public and private nonfork repositories, profile excluded. "
    "Counts are unique observed push events, not commits, contributions, or line changes."
)


def _project_activity_scale(rows):
    """One finite distribution scale precedes every period and row display cut."""
    samples = sorted(cell["count"] for row in rows for cell in row["daily"]
                     if type(cell["count"]) is int and cell["count"] > 0)
    partial = any(cell["count"] is not None and cell["count"] > 0 and not cell["complete"]
                  for row in rows for cell in row["daily"])
    bands = []
    if samples:
        endpoints = sorted({samples[(len(samples) * quarter + 3) // 4 - 1]
                            for quarter in (1, 2, 3, 4)})
        levels = {1: (1,), 2: (1, 4), 3: (1, 3, 4), 4: (1, 2, 3, 4)}[len(endpoints)]
        lower = 1
        for upper, level in zip(endpoints, levels):
            bands.append({"lower": lower, "upper": upper, "level": level})
            lower = upper + 1
    return {"status": "partial" if samples and partial else "ok" if samples else "unavailable",
            "sample_size": len(samples), "bands": bands, "lower_bounds_included": partial,
            "basis": "Positive observed repository/day counts across all received 30 UTC dates",
            "qualification": "Scale includes observed lower bounds" if partial else
                             "Shared observed distribution" if samples else "No positive push counts to scale"}


def _build_project_activity(source):
    """Aggregate qualified push identities once for web and static projections."""
    start, end = timestamp(source.get("window_start")), timestamp(source.get("window_end"))
    observed = timestamp(source.get("observed_at"))
    valid = bool(source.get("schema") == "profile-activity-observations/v1"
                 and start is not None and end is not None and observed is not None
                 and start <= end == observed and (end.date() - start.date()).days == 29
                 and start.hour == start.minute == start.second == start.microsecond == 0)
    result = {"schema": "profile-project-activity/v1", "status": "unavailable", "complete": False,
              "window_start": iso(start) if valid else None, "window_end": iso(end) if valid else None,
              "observed_at": iso(observed) if valid else None, "timezone": "UTC", "current_day_partial": True,
              "default_days": 14, "available_days": [14, 30], "default_repositories": 8,
              "meaning": _PROJECT_MEANING, "dates": [], "rows": [], "scale": _project_activity_scale([]),
              "reason": "invalid_observation_window", "qualification": "Project activity unavailable"}
    if not valid:
        return result
    dates = [(start.date() + timedelta(days=index)).isoformat() for index in range(30)]
    received = qualify_project_activity(source.get("repositories"), window_start=iso(start), window_end=iso(end),
                                        observed_at=iso(observed), owner=gh.USERNAME, profile_name=gh.USERNAME)

    def daily(counts, complete, *, positive_only=False):
        cells = []
        for day in dates:
            known = complete and day != dates[-1]
            value = counts.get(day, 0)
            if positive_only and not value:
                continue
            cells.append({"date": day, "count": value if value or known else None,
                          "complete": known, "level": 0 if known and not value else None})
        return cells

    rows = []
    for repository in received["rows"]:
        counts, branches = {}, {}
        for event in repository["events"]:
            day = event["timestamp"][:10]
            counts[day] = counts.get(day, 0) + 1
            branch = branches.setdefault(event["ref"], {"counts": {}, "latest_push": event["timestamp"]})
            branch["counts"][day] = branch["counts"].get(day, 0) + 1
            branch["latest_push"] = max(branch["latest_push"], event["timestamp"])
        branch_rows = [{"ref": ref, "daily": daily(branch["counts"], repository["complete"], positive_only=True),
                        "observed_pushes": sum(branch["counts"].values())}
                       for ref, branch in sorted(branches.items(), key=lambda item: item[0])]
        rows.append({"repository": repository["repository"], "is_private": repository["is_private"],
                     "status": repository["status"], "complete": repository["complete"],
                     "reasons": repository["reasons"], "latest_push": repository["latest_push"],
                     "observed_pushes": sum(counts.values()), "daily": daily(counts, repository["complete"]),
                     "branch_empty_daily": daily({}, repository["complete"]), "branches": branch_rows})
    scale = _project_activity_scale(rows)
    for row in rows:
        for series in [row, *row["branches"]]:
            for cell in series["daily"]:
                if cell["count"] is not None and cell["count"] > 0:
                    cell["level"] = next(band["level"] for band in scale["bands"]
                                         if band["lower"] <= cell["count"] <= band["upper"])

    raw_cohort = source.get("cohort") if type(source.get("cohort")) is dict else {}
    cohort = {key: count(raw_cohort.get(key)) for key in ("eligible", "selected", "queried")}
    exclusions = raw_cohort.get("excluded") if type(raw_cohort.get("excluded")) is dict else {}
    cohort_complete = (not received["reasons"] and raw_cohort.get("inventory_complete") is True
                       and raw_cohort.get("inventory_fresh") is True
                       and all(value == len(rows) for value in cohort.values())
                       and received["received"] == len(rows)
                       and count(raw_cohort.get("complete")) == len(rows)
                       and count(raw_cohort.get("partial")) == count(raw_cohort.get("unavailable")) == 0
                       and all(count(exclusions.get(key)) == 0 for key in ("identity", "invalid_hint", "selection_limit"))
                       and all(row["complete"] for row in rows))
    available = cohort_complete or any(row["observed"] or row["events"] for row in received["rows"])
    cohort.update(repositories_received=len(rows), repositories_complete=received["complete_repositories"],
                  received_complete=cohort_complete, ranking_complete=cohort_complete,
                  default_visible=min(8, len(rows)), reasons=received["reasons"])
    qualification = (f"{len(rows)} received repositories · bounded recent-push cohort. "
                     + ("Observation complete through the cutoff; today is in progress." if cohort_complete else
                        "Observation incomplete; counts are lower bounds and ranking is among received repositories."))
    result.update(status="ok" if cohort_complete else "partial" if available else "unavailable",
                  complete=cohort_complete, dates=dates, rows=rows, scale=scale, cohort=cohort,
                  reason="observed" if cohort_complete else "incomplete_received_cohort",
                  qualification=qualification,
                  observed_pushes=sum(row["observed_pushes"] for row in rows))
    return result


def build_activity_analytics(source):
    """Keep observed totals separate from collection completeness and population."""
    source = source if type(source) is dict else {}
    start, end = timestamp(source.get("window_start")), timestamp(source.get("window_end"))
    observed = timestamp(source.get("observed_at"))
    valid = source.get("schema") == "profile-activity-observations/v1" and start is not None and end is not None and observed is not None
    valid = bool(valid and start <= end <= observed and (end.date() - start.date()).days == 29 and start.hour == start.minute == start.second == start.microsecond == 0)
    dates = [(start.date() + timedelta(days=i)).isoformat() for i in range(30)] if valid else []
    raw_cohort = source.get("cohort") if type(source.get("cohort")) is dict else {}
    cohort = {key: count(raw_cohort.get(key)) for key in ("inventory", "eligible", "selected", "queried", "complete", "partial", "unavailable")}
    cohort["inventory_complete"] = raw_cohort.get("inventory_complete") is True
    excluded = raw_cohort.get("excluded") or {}
    cohort["excluded"] = {key: count(excluded.get(key)) for key in ("identity", "fork", "profile", "outside_window", "invalid_hint", "selection_limit")} if type(excluded) is dict else {}
    cohort["inventory_fresh"] = raw_cohort.get("inventory_fresh") is True
    raw_code = source.get("code_changes") if valid and type(source.get("code_changes")) is dict else {}
    repository, ref, head = repository_name(raw_code.get("repository")), raw_code.get("ref"), raw_code.get("head_sha")
    code_available = bool(repository and gh._valid_branch_ref(ref) and gh._valid_branch_oid(head) and raw_code.get("status") in {"ok", "partial"})
    history_complete = code_available and raw_code.get("complete") is True and raw_code.get("status") == "ok"
    selection = source.get("selection") if type(source.get("selection")) is dict else {}
    selection_complete = selection.get("complete") is True and selection.get("status") == "ok"
    complete = history_complete and selection_complete
    commits, invalid, excluded_merges, observed_stats = {}, False, 0, 0
    for row in raw_code.get("commits", []) if code_available and type(raw_code.get("commits")) is list else []:
        if type(row) is not dict or not gh._valid_branch_oid(row.get("oid")):
            invalid = True
            continue
        occurred = timestamp(row.get("committed_at"))
        if occurred is None or occurred > end:
            invalid = True
            continue
        if occurred < start:
            continue
        value = {"oid": row["oid"], "committed_at": iso(occurred), "parent_count": count(row.get("parent_count")),
                 "additions": count(row.get("additions")), "deletions": count(row.get("deletions"))}
        if value["oid"] in commits and commits[value["oid"]] != value:
            invalid = True
            commits[value["oid"]] = {**value, "additions": None, "deletions": None}
        else:
            commits[value["oid"]] = value
    days = {day: {"date": day, "additions": 0, "deletions": 0, "complete": complete} for day in dates}
    additions, deletions, nonmerges = 0, 0, 0
    for row in commits.values():
        day = days[timestamp(row["committed_at"]).date().isoformat()]
        if row["parent_count"] is None:
            invalid, day["complete"] = True, False
            continue
        if row["parent_count"] > 1:
            excluded_merges += 1
            continue
        nonmerges += 1
        if row["additions"] is None or row["deletions"] is None:
            invalid, day["complete"] = True, False
            continue
        observed_stats += 1
        additions += row["additions"]
        deletions += row["deletions"]
        day["additions"] += row["additions"]
        day["deletions"] += row["deletions"]
    history_complete = history_complete and not invalid
    complete = history_complete and selection_complete
    for day in days.values():
        day["complete"] = day["complete"] and complete
        if not day["complete"] and not (day["additions"] or day["deletions"]):
            day["additions"] = day["deletions"] = None
    code = {"status": _status(complete, code_available), "complete": complete,
            "selection": {"status": selection.get("status", "unavailable"), "complete": selection_complete,
                          "reason": selection.get("reason", "selection_not_observed"),
                          "occurred_at": selection.get("occurred_at")},
            "history": {"status": _status(history_complete, code_available), "complete": history_complete,
                        "reason": "invalid_stats" if invalid else raw_code.get("reason", "not_observed")},
            "repository": repository if code_available else None, "ref": ref if code_available else None, "head_sha": head if code_available else None,
            "commit_url": f"https://github.com/{repository}/commit/{head}" if code_available else None,
            "additions": additions if code_available else None, "deletions": deletions if code_available else None,
            "commit_count": nonmerges, "observed_commits": len(commits), "stats_observed": observed_stats,
            "excluded_merges": excluded_merges, "daily": list(days.values()) if code_available else [],
            "meaning": "Summed non-merge commit line changes reachable from the selected head; not net tree size or all branches"}
    result = {"schema": "profile-activity-analytics/v1", "window_start": iso(start) if valid else None, "window_end": iso(end) if valid else None,
            "current_day_partial": True, "cohort": cohort, "code_changes": code,
            "recent_pushes": present_recent_pushes(source.get("recent_pushes") if valid else None)}
    if "overall_code_changes" in source:
        result["overall_code_changes"] = _build_owned_code_activity(source["overall_code_changes"])
    result["project_activity"] = _build_project_activity(source)
    return result

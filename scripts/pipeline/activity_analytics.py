"""Pure thirty-date aggregation of bounded repository observations."""
from datetime import timedelta
from scripts.github import github_client as gh
from scripts.github.activity_observations import count, iso, repository_name, timestamp


def _status(complete, observed):
    return "ok" if complete else "partial" if observed else "unavailable"


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
    return {"schema": "profile-activity-analytics/v1", "window_start": iso(start) if valid else None, "window_end": iso(end) if valid else None,
            "current_day_partial": True, "cohort": cohort, "code_changes": code}

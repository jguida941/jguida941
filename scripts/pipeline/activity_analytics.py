"""Pure thirty-date aggregation of bounded repository observations."""
from datetime import timedelta
from scripts.github import github_client as gh
from scripts.github.activity_observations import count, iso, repository_name, timestamp
from scripts.pipeline.push_activity import present_recent_pushes, qualify_project_activity


def _status(complete, observed):
    return "ok" if complete else "partial" if observed else "unavailable"


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
    result["project_activity"] = _build_project_activity(source)
    return result

"""One public presentation value for the profile's SVG and text summaries."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from urllib.parse import urlsplit

from scripts.contracts.profile_contract import (
    automation_display, contribution_rhythm_display, contribution_rhythm_errors,
    contribution_trend_display,
)

SCHEMA = "profile-dashboard-summary/v1"


def _count(value):
    return value if type(value) is int and value >= 0 else None


def _fact(identity, value, label, population, *, status="unknown", reason="matching_evidence_not_carried", window="current inventory", qualification=""):
    value = _count(value)
    if value is None:
        status, reason, qualification = "unavailable", "value_unavailable", "Unavailable"
    elif status == "unknown" and not qualification:
        qualification = "Reported inventory · freshness/completeness unverified"
    elif status not in ("exact", "ok") and not qualification:
        qualification = status.capitalize()
    return {"metric_id": identity, "value": value, "display_value": f"{value:,}" if value is not None else "n/a",
            "label": label, "unit": "count", "population_id": population, "window": window,
            "quality": {"status": status, "reason": reason, "qualification": qualification}}


def _url(value):
    value = str(value or "")
    try:
        parsed = urlsplit(value)
        return value if parsed.scheme in ("http", "https") and parsed.netloc and not parsed.username else ""
    except ValueError:
        return ""


def _rows(rows, keys):
    return [{key: row[key] for key in keys if key in row} for row in (rows or []) if isinstance(row, dict)]


def build_dashboard_summary(model, *, profile_date):
    """Select already-computed facts; only calendar runs and byte shares are derived.

    The same exclusion owner runs before any new public consumer. Raw model rows
    remain unchanged so an unsafe description cannot erase valid repository metadata.
    """
    from scripts.pipeline.render_outputs import _public_dashboard_data
    snapshot = model.get("snapshot") or {}
    scope = model.get("data_scope") or {}
    quality = model.get("data_quality") or {}
    statuses = quality.get("metric_statuses") or {}
    provenance = quality.get("metric_provenance") or {}
    data = model.get("dashboard_data") or {}
    rhythm = model.get("contribution_rhythm")
    rhythm_display = contribution_rhythm_display(rhythm)
    calendar_ok = not contribution_rhythm_errors(rhythm) and rhythm.get("status") == "available"
    calendar_status = "exact" if calendar_ok and rhythm.get("completeness") == "known" else "unknown" if calendar_ok else "unavailable"
    calendar_window = f'{rhythm["window_start"]} – {rhythm["window_end"]} · UTC' if calendar_ok else "Calendar unavailable"
    facts = []
    def add(*args, **kwargs):
        row = _fact(*args, **kwargs)
        facts.append(row)
        return row
    add("calendar.total", snapshot.get("last_year_contributions") if calendar_ok else None,
        "contributions", "github-contribution-calendar-visible-to-provider", status=calendar_status,
        reason="calendar_observation", window=calendar_window, qualification=rhythm_display.get("qualification", ""))
    for identity, value, label, population in (
        ("inventory.public_nonfork", scope.get("public_owned_nonfork_repos_total"), "public non-fork repos", "public-owned-nonfork-profile-included"),
        ("inventory.private_owned", snapshot.get("private_owned_repos"), "private owned repos", "private-owned-including-forks"),
        ("inventory.stargazers", snapshot.get("total_stars"), "stargazers", "public-owned-nonfork"),
        ("inventory.public_forks", snapshot.get("public_forks"), "public forks", "public-owned-forks"),
    ):
        add(identity, value, label, population)
    for identity, key, label in (
        ("activity.public_commits", "public_scope_commits", "Public commits"),
        ("activity.merged_prs", "prs_merged", "Merged PRs"),
        ("activity.releases_30d", "releases_30d", "Releases · 30 days"),
    ):
        observation = provenance.get(key) or {}
        status = observation.get("status", "unknown")
        value = snapshot.get("releases") if key == "releases_30d" else snapshot.get(key)
        nonexact = (quality.get("non_exact_metrics") or {}).get(key) or {}
        if nonexact:
            status = nonexact.get("status", "unavailable")
        add(identity, value, label, observation.get("population_id", "provider population unverified"),
            status="exact" if status == "ok" else status, reason="provider_observation" if observation else "matching_evidence_not_carried",
            window=(f'{observation.get("window_start")} – {observation.get("window_end")}' if observation.get("window_start") else "returned repository history"))
    activity_status = statuses.get("active_repos_7d", "unknown")
    add("activity.active_repos_7d", (model.get("scorecard") or {}).get("active_repos_7d"), "active repos",
        "owned-public-private-nonfork-profile-excluded", status=activity_status, reason="repository_observation", window="last 7 days")
    language_bytes = model.get("language_bytes") or {}
    valid_bytes = isinstance(language_bytes, dict) and all(type(k) is str and _count(v) is not None for k, v in language_bytes.items())
    language_status = statuses.get("top_languages", "unknown")
    ordered = sorted(language_bytes.items(), key=lambda item: (-item[1], item[0])) if valid_bytes and language_status != "unavailable" else []
    total_bytes = sum(value for _, value in ordered)
    language_rows = [{"name": name, "bytes": value, "percent": value / total_bytes * 100 if total_bytes else 0,
                      "display_value": f"{value / total_bytes * 100:.1f}%" if total_bytes else "0.0%"} for name, value in ordered]
    visible_languages = language_rows[:6]
    if len(language_rows) > 6:
        other = sum(row["bytes"] for row in language_rows[6:])
        visible_languages = visible_languages + [{"name": "Other", "bytes": other, "percent": other / total_bytes * 100 if total_bytes else 0,
                                                  "display_value": f"{other / total_bytes * 100:.1f}%" if total_bytes else "0.0%"}]
    add("language.count", len(ordered) if valid_bytes and language_status != "unavailable" else None, "languages",
        "owned-public-private-nonfork-profile-excluded", status=language_status, reason="language_byte_observation", window="observed repository HEADs")

    raw_calendar = data.get("contribution_calendar") or {}
    days = []
    if calendar_ok:
        try:
            days = [dict(row) for week in raw_calendar["weeks"] for row in week]
            parsed = [date.fromisoformat(row["date"]) for row in days]
            if (len(set(parsed)) != len(parsed) or any(_count(row["count"]) is None for row in days)
                    or sum(row["count"] for row in days) != rhythm["total"]):
                raise ValueError("calendar disagrees")
            days.sort(key=lambda row: row["date"])
            if (days[0]["date"] != rhythm["window_start"] or days[-1]["date"] != rhythm["window_end"]
                    or (date.fromisoformat(days[-1]["date"]) - date.fromisoformat(days[0]["date"])).days + 1 != len(days)):
                raise ValueError("calendar window disagrees")
        except (KeyError, TypeError, ValueError, IndexError):
            days = []
    cutoff = profile_date.isoformat() if isinstance(profile_date, date) else str(profile_date)
    eligible = [row for row in days if row["date"] <= cutoff]
    longest, run, current = [], [], []
    for row in eligible:
        run = run + [row] if row["count"] > 0 else []
        if len(run) > len(longest):
            longest = run[:]
    current = run
    for identity, value, label, selected in (
        ("calendar.active_days", sum(row["count"] > 0 for row in days) if days else None, "active days", []),
        ("calendar.current_streak", len(current) if days and len(current) == snapshot.get("streak_days") else None, "current observed streak", current),
        ("calendar.longest_streak", len(longest) if days else None, "longest observed streak", longest),
    ):
        fact = add(identity, value, label, "github-contribution-calendar-visible-to-provider", status=calendar_status,
                   reason="calendar_run" if value is not None else "streak_reconciliation_required" if days else "calendar_unavailable",
                   window=calendar_window, qualification=rhythm_display.get("qualification", ""))
        fact["profile_date_cutoff"] = cutoff
        fact["completeness"] = rhythm.get("completeness", "unknown") if calendar_ok else "unknown"
        fact["last_day_in_progress"] = rhythm.get("last_day_in_progress") if calendar_ok else None
        fact["range_start"] = selected[0]["date"] if selected and value is not None else None
        fact["range_end"] = selected[-1]["date"] if selected and value is not None else None
        if value is None and days:
            fact["quality"]["reason"] = "streak_reconciliation_required"
            fact["quality"]["qualification"] = "Streak unavailable · source counts differ"

    working = _rows(model.get("recent_repos"), ("name", "html_url", "language", "pushed_at", "last_commit_msg", "is_private"))
    generated_at = str(data.get("generated_at", ""))
    for row in working:
        row["url"] = _url(row.pop("html_url", ""))
        row["push_age"] = "Push date unavailable"
        try:
            elapsed = (datetime.fromisoformat(generated_at.replace("Z", "+00:00")) - datetime.fromisoformat(str(row.get("pushed_at", "")).replace("Z", "+00:00"))).total_seconds()
            if elapsed >= 0:
                row["push_age"] = "pushed <1h ago" if elapsed < 3600 else f"pushed {int(elapsed / 3600)}h ago" if elapsed < 86400 else f"pushed {int(elapsed / 86400)}d ago"
        except (TypeError, ValueError):
            pass
    projects = _rows(model.get("spotlight_data"), ("name", "description", "language", "stars", "forks", "url", "html_url", "is_private"))
    for row in projects:
        row["url"] = _url(row.get("url") or row.pop("html_url", ""))
    focus = {key: _rows((model.get("focus") or {}).get(native), ("title", "detail", "url", "is_private"))
             for key, native in (("now", "now"), ("next", "next"), ("updates", "shipped"))}
    for rows in focus.values():
        for row in rows:
            row["url"] = _url(row.get("url"))
    trend = (model.get("engineering") or {}).get("contribution_trend")
    presentation = {"schema": SCHEMA, "username": data.get("username", ""), "generated_at": generated_at,
                    "facts": facts, "weekly": {"model": trend, "display": contribution_trend_display(trend)},
                    "rhythm": {"model": rhythm, "display": rhythm_display},
                    "languages": {"rows": visible_languages, "all_rows": language_rows, "total_bytes": total_bytes,
                                  "quality": language_status, "scope": "Owned public + private non-fork repositories; profile excluded"},
                    "automation": {"model": model.get("automation"), "display": automation_display(model.get("automation"))},
                    "calendar": {"days": days, "window": calendar_window, "status": calendar_status if days else "unavailable"},
                    "working": working, "focus": focus, "projects": projects,
                    "recent_created": _rows(model.get("recent_created"), ("name", "url", "html_url", "description", "language", "created_at"))}
    return _public_dashboard_data(presentation)


def summary_facts(summary):
    return {row["metric_id"]: row for row in summary.get("facts", [])}

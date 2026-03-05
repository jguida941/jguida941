#!/usr/bin/env python3
"""Master orchestrator: fetch data, generate SVGs, render README."""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import jinja2

from scripts import github_client as gh
from scripts.config import USERNAME, FEATURED_REPOS
from scripts.generate_badges import generate as gen_badges
from scripts.generate_language_chart import generate as gen_lang_chart
from scripts.generate_currently_working import generate as gen_working
from scripts.generate_activity_heatmap import generate as gen_heatmap
from scripts.generate_repo_spotlight import generate as gen_spotlight
from scripts.generate_builder_scorecard import generate as gen_scorecard


def _time_ago(iso_str: str) -> str:
    if not iso_str:
        return "unknown"
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    delta = datetime.now(timezone.utc) - dt
    days = delta.days
    if days == 0:
        hours = int(delta.total_seconds() / 3600)
        if hours <= 1:
            return "today"
        return f"{hours} hours ago"
    if days == 1:
        return "1 day ago"
    if days < 7:
        return f"{days} days ago"
    if days < 30:
        weeks = days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    if days < 365:
        months = days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    return f"{days // 365} year{'s' if days >= 730 else ''} ago"


def _has_ci_workflow(repo: dict) -> bool | None:
    """Best-effort check for .github/workflows in repo."""
    if "has_ci_workflows" in repo:
        return bool(repo.get("has_ci_workflows"))

    try:
        owner = repo["owner"]["login"]
        name = repo["name"]
        return gh.get_repo_ci_state(owner, name)
    except Exception:
        return None


def _activity_label(event_type: str) -> str:
    labels = {
        "PushEvent": "push",
        "PullRequestEvent": "pull request",
        "PullRequestReviewEvent": "pr review",
        "ReleaseEvent": "release",
        "IssuesEvent": "issue",
        "IssueCommentEvent": "issue comment",
        "CreateEvent": "create",
        "DeleteEvent": "delete",
    }
    if event_type in labels:
        return labels[event_type]
    return (event_type or "activity").replace("Event", "").lower() or "activity"


def main():
    print("=== GitHub Profile README Builder ===")
    print(f"User: {USERNAME}")

    # Ensure generated-output dirs exist
    Path("assets").mkdir(exist_ok=True)
    Path("site/data").mkdir(parents=True, exist_ok=True)

    # ── Fetch Data ──────────────────────────────────────────
    print("\n[1/7] Fetching repo scope counts...")
    repo_counts = gh.get_owned_repo_scope_counts()
    print(
        "  Scope totals:"
        f" public non-fork={repo_counts['public_owned_nonfork']},"
        f" public forks={repo_counts['public_owned_forks']},"
        f" public total={repo_counts['public_owned_total']},"
        f" private owned={repo_counts['private_owned'] if repo_counts['private_owned'] is not None else 'n/a'}"
    )

    print("[2/7] Fetching repos...")
    repos = gh.get_repos(include_forks=False)
    all_repos = gh.get_repos(include_forks=True)
    print(
        f"  Found {len(repos)} public non-fork repos "
        f"({len(all_repos)} public owned total, {repo_counts['public_owned_forks']} forks)"
    )

    print("[3/7] Fetching language data...")
    language_bytes = gh.get_all_languages(repos)
    lang_count = len([l for l, b in language_bytes.items() if b > 0])
    print(f"  {lang_count} languages across all repos")

    print("[4/7] Fetching events...")
    events = gh.get_events()
    print(f"  {len(events)} recent events")

    # Best-effort latest push message per repo for fallback display.
    latest_push_message_by_repo: dict[str, str] = {}
    for event in events:
        if event.get("type") != "PushEvent":
            continue
        repo_full_name = event.get("repo", {}).get("name", "")
        if not repo_full_name or repo_full_name in latest_push_message_by_repo:
            continue
        commits = event.get("payload", {}).get("commits", [])
        if not commits:
            continue
        message = commits[-1].get("message", "").split("\n")[0].strip()
        if message:
            latest_push_message_by_repo[repo_full_name] = message

    print("[5/7] Fetching public repo commit count...")
    public_scope_commits = gh.get_total_commits(repos)
    print(f"  {public_scope_commits} public-scope commits")

    print("[6/7] Counting CI/CD pipelines...")
    ci_count = gh.get_repos_with_ci(repos)
    print(f"  {ci_count} repos with CI/CD")

    print("[7/7] Fetching contribution calendar...")
    calendar = gh.get_contribution_calendar()
    total_contributions = calendar.get("totalContributions", 0) if calendar else 0
    print(f"  {total_contributions} contributions in the last 12 months")

    # Derived stats
    now_utc = datetime.now(timezone.utc)
    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    total_language_bytes = sum(b for b in language_bytes.values() if b > 0)
    top_languages = []
    for lang, byte_count in sorted(language_bytes.items(), key=lambda x: x[1], reverse=True)[:12]:
        if byte_count <= 0:
            continue
        pct = (byte_count / total_language_bytes * 100) if total_language_bytes else 0
        top_languages.append({
            "name": lang,
            "bytes": byte_count,
            "percent": round(pct, 2),
        })

    # Count PRs merged (from events)
    prs_merged = sum(
        1 for e in events
        if e.get("type") == "PullRequestEvent"
        and e.get("payload", {}).get("action") == "closed"
        and e.get("payload", {}).get("pull_request", {}).get("merged")
    )

    # Count releases (from events)
    releases = sum(1 for e in events if e.get("type") == "ReleaseEvent")

    release_event_times = []
    for event in events:
        if event.get("type") != "ReleaseEvent":
            continue
        created_at = event.get("created_at", "")
        if not created_at:
            continue
        try:
            release_event_times.append(datetime.fromisoformat(created_at.replace("Z", "+00:00")))
        except ValueError:
            continue
    releases_30d = sum(1 for ts in release_event_times if (now_utc - ts).days < 30)
    avg_release_gap_days = 0.0
    if len(release_event_times) >= 2:
        sorted_times = sorted(release_event_times, reverse=True)
        gaps = []
        for idx in range(len(sorted_times) - 1):
            gaps.append((sorted_times[idx] - sorted_times[idx + 1]).total_seconds() / 86400.0)
        avg_release_gap_days = sum(gaps) / len(gaps)

    active_repos_7d = 0
    seven_days_ago = now_utc - timedelta(days=7)
    for repo in repos:
        pushed = repo.get("pushed_at", "")
        if not pushed:
            continue
        try:
            pushed_dt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
        except ValueError:
            continue
        if pushed_dt >= seven_days_ago:
            active_repos_7d += 1

    stars_per_public_repo = (total_stars / len(repos)) if repos else 0.0
    ci_coverage_pct = (ci_count / len(repos) * 100) if repos else 0.0

    # Streak days estimate from calendar
    streak_days = 0
    if calendar:
        all_days = []
        for week in calendar.get("weeks", []):
            for day in week.get("contributionDays", []):
                all_days.append(day)
        # Count current streak from most recent day backwards
        for day in reversed(all_days):
            if day["contributionCount"] > 0:
                streak_days += 1
            else:
                break

    # ── Generate SVGs ───────────────────────────────────────
    print("\n[8/8] Generating SVGs...")

    # 1. Badges
    gen_badges(
        public_nonfork_repos=repo_counts["public_owned_nonfork"],
        public_forks=repo_counts["public_owned_forks"],
        private_owned_repos=repo_counts["private_owned"],
        ci_count=ci_count,
        last_year_contributions=total_contributions,
    )
    print("  -> assets/badges.svg")

    # 2. Language chart
    gen_lang_chart(language_bytes)
    print("  -> assets/lang_breakdown.svg")

    # 3. Currently working on
    recent_repos = []
    seen = set()
    for r in sorted(repos, key=lambda x: x.get("pushed_at", ""), reverse=True):
        pushed = r.get("pushed_at", "")
        if not pushed:
            continue
        pushed_dt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
        if pushed_dt < seven_days_ago:
            break
        if r["name"] not in seen:
            seen.add(r["name"])
            # Prefer latest default-branch commit headline when available in repo payload.
            last_msg = (r.get("latest_commit_message") or "").split("\n")[0].strip()
            if not last_msg:
                # Fallback to REST commit endpoint.
                try:
                    commits_data = gh.paginated_get(
                        f"repos/{r['owner']['login']}/{r['name']}/commits",
                        {"per_page": 1},
                        per_page=1,
                    )
                    if commits_data:
                        last_msg = commits_data[0].get("commit", {}).get("message", "").split("\n")[0].strip()
                except Exception:
                    pass
            if not last_msg:
                full_name = f"{r['owner']['login']}/{r['name']}"
                last_msg = latest_push_message_by_repo.get(full_name, "")
            if not last_msg:
                last_msg = "latest commit message unavailable"
            recent_repos.append({
                "name": r["name"],
                "html_url": r.get("html_url", ""),
                "language": r.get("language"),
                "pushed_at": pushed,
                "last_commit_msg": last_msg,
            })
    gen_working(recent_repos)
    print("  -> assets/currently_working.svg")

    # 4. Activity heatmap
    gen_heatmap(events)
    print("  -> assets/activity_heatmap.svg")

    # 5. Repo spotlight
    spotlight_data = []
    for repo_name in FEATURED_REPOS:
        repo = next((r for r in all_repos if r["name"] == repo_name), None)
        if not repo:
            continue
        weekly = gh.get_repo_commits_last_n_weeks(repo["owner"]["login"], repo["name"])
        has_ci = _has_ci_workflow(repo)
        spotlight_data.append({
            "name": repo["name"],
            "description": repo.get("description", ""),
            "language": repo.get("language"),
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "html_url": repo.get("html_url", ""),
            "pushed_at": (repo.get("pushed_at") or "")[:10],
            "weekly_commits": weekly,
            "has_ci": has_ci,
        })
    gen_spotlight(spotlight_data)
    print("  -> assets/repo_spotlight.svg")

    scorecard = {
        "releases_30d": releases_30d,
        "active_repos_7d": active_repos_7d,
        "avg_release_gap_days": avg_release_gap_days,
        "stars_per_public_repo": stars_per_public_repo,
        "ci_coverage_pct": ci_coverage_pct,
        "last_year_contributions": total_contributions,
    }
    gen_scorecard(scorecard)
    print("  -> assets/builder_scorecard.svg")

    # ── Render README ───────────────────────────────────────
    print("\nRendering README.md...")

    # Prepare template data
    # Most active projects with explicit language + CI signals
    active_repos = sorted(repos, key=lambda r: r.get("pushed_at", ""), reverse=True)[:15]
    repo_language_matrix = []
    for repo in active_repos:
        ci_state = _has_ci_workflow(repo)
        if ci_state is True:
            ci_text = "yes"
        elif ci_state is False:
            ci_text = "no"
        else:
            ci_text = "unknown"

        repo_language_matrix.append({
            "name": repo.get("name", ""),
            "url": repo.get("html_url", ""),
            "language": repo.get("language") or "n/a",
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "pushed_at": (repo.get("pushed_at") or "")[:10],
            "ci": ci_text,
        })

    featured_repo_facts = []
    for repo_name in FEATURED_REPOS:
        repo = next((r for r in repos if r.get("name") == repo_name), None)
        if not repo:
            continue
        ci_state = _has_ci_workflow(repo)
        if ci_state is True:
            ci_text = "yes"
        elif ci_state is False:
            ci_text = "no"
        else:
            ci_text = "unknown"
        featured_repo_facts.append({
            "name": repo.get("name", ""),
            "url": repo.get("html_url", ""),
            "language": repo.get("language") or "n/a",
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "ci": ci_text,
            "pushed_at": (repo.get("pushed_at") or "")[:10],
        })

    data_scope = {
        "repos_included": "public + owned + non-fork",
        "activity_metric_scope": "GitHub contributionCalendar.totalContributions (last 12 months)",
        "public_owned_repos_total": repo_counts["public_owned_total"],
        "public_owned_forks_total": repo_counts["public_owned_forks"],
        "public_owned_nonfork_repos_total": repo_counts["public_owned_nonfork"],
        "private_owned_repos_total": repo_counts["private_owned"],
    }

    snapshot = {
        "last_year_contributions": total_contributions,
        "public_scope_commits": public_scope_commits,
        "total_repos": repo_counts["public_owned_nonfork"],
        "total_stars": total_stars,
        "languages_count": lang_count,
        "prs_merged": prs_merged,
        "releases": releases,
        "ci_repos": ci_count,
        "streak_days": streak_days,
    }

    # Recently created repos (top 10 non-fork by creation date)
    recent_created = sorted(repos, key=lambda r: r.get("created_at", ""), reverse=True)[:10]

    # Latest owned-repo contribution activity (from events)
    contribution_event_types = {
        "PushEvent",
        "PullRequestEvent",
        "PullRequestReviewEvent",
        "ReleaseEvent",
        "IssuesEvent",
        "IssueCommentEvent",
        "CreateEvent",
        "DeleteEvent",
    }
    owned_repo_prefix = f"{USERNAME}/"
    contributions = []
    seen_contrib = set()
    for e in events:
        if e.get("type") not in contribution_event_types:
            continue
        repo_name = e.get("repo", {}).get("name", "")
        if not repo_name.startswith(owned_repo_prefix):
            continue
        if repo_name not in seen_contrib:
            seen_contrib.add(repo_name)
            contributions.append({
                "repo": repo_name,
                "url": f"https://github.com/{repo_name}",
                "activity": _activity_label(e.get("type", "")),
                "time_ago": _time_ago(e.get("created_at", "")),
            })
        if len(contributions) >= 10:
            break

    # Recent releases
    release_list = []
    for e in events:
        if e.get("type") != "ReleaseEvent":
            continue
        payload = e.get("payload", {})
        release = payload.get("release", {})
        repo_name = e.get("repo", {}).get("name", "")
        release_tag = (release.get("tag_name") or "").strip() or "unknown"
        release_url = (release.get("html_url") or "").strip()
        if not release_url and repo_name and release_tag != "unknown":
            release_url = f"https://github.com/{repo_name}/releases/tag/{release_tag}"
        release_list.append({
            "repo": repo_name,
            "repo_url": f"https://github.com/{repo_name}",
            "tag": release_tag,
            "url": release_url,
            "time_ago": _time_ago(e.get("created_at", "")),
        })
        if len(release_list) >= 5:
            break

    # Recent PRs
    pr_list = []
    for e in events:
        if e.get("type") != "PullRequestEvent":
            continue
        pr = e.get("payload", {}).get("pull_request", {})
        repo_name = e.get("repo", {}).get("name", "")
        state = pr.get("state", "open").upper()
        if pr.get("merged"):
            state = "MERGED"
        pr_number = pr.get("number")
        pr_title = (pr.get("title") or "").strip()
        if not pr_title:
            pr_title = f"PR #{pr_number}" if pr_number else "pull request"
        pr_url = (pr.get("html_url") or "").strip()
        if not pr_url and repo_name and pr_number:
            pr_url = f"https://github.com/{repo_name}/pull/{pr_number}"
        if not pr_url and repo_name:
            pr_url = f"https://github.com/{repo_name}/pulls"
        pr_list.append({
            "title": pr_title,
            "url": pr_url,
            "repo": repo_name,
            "repo_url": f"https://github.com/{repo_name}",
            "state": state,
            "time_ago": _time_ago(e.get("created_at", "")),
        })
        if len(pr_list) >= 5:
            break

    # Focus board (Now / Next / Shipped) for fast scan value.
    focus_now = []
    for entry in contributions[:3]:
        repo_short = entry["repo"].split("/")[-1]
        focus_now.append({
            "title": repo_short,
            "detail": f"{entry['activity']} · {entry['time_ago']}",
            "url": entry["url"],
        })
    if not focus_now:
        focus_now.append({
            "title": "No recent owned-repo activity found",
            "detail": "Waiting for next push/PR/release event",
            "url": f"https://github.com/{USERNAME}",
        })

    focus_next = []
    open_prs = [pr for pr in pr_list if pr.get("state") == "OPEN"]
    for pr in open_prs[:3]:
        repo_short = pr["repo"].split("/")[-1]
        focus_next.append({
            "title": pr["title"],
            "detail": f"{repo_short} · {pr['state'].lower()}",
            "url": pr["url"],
        })
    if not focus_next:
        for repo in repo_language_matrix[:2]:
            focus_next.append({
                "title": f"Ship next iteration in {repo['name']}",
                "detail": f"{repo['language']} · last push {repo['pushed_at'] or 'n/a'}",
                "url": repo["url"],
            })

    focus_shipped = []
    for rel in release_list[:4]:
        repo_short = rel["repo"].split("/")[-1] if rel["repo"] else "repo"
        focus_shipped.append({
            "title": rel["tag"],
            "detail": f"{repo_short} · {rel['time_ago']}",
            "url": rel["url"] or rel["repo_url"],
        })
    if not focus_shipped:
        focus_shipped.append({
            "title": "No recent release events captured",
            "detail": "Release feed is event-driven and may lag",
            "url": f"https://github.com/{USERNAME}?tab=repositories",
        })

    dashboard_data = {
        "generated_at": now_utc.isoformat().replace("+00:00", "Z"),
        "username": USERNAME,
        "dashboard_url": f"https://{USERNAME}.github.io/{USERNAME}/",
        "snapshot": snapshot,
        "scorecard": scorecard,
        "data_scope": data_scope,
        "featured_repo_facts": featured_repo_facts,
        "top_languages": top_languages,
        "repo_language_matrix": repo_language_matrix[:10],
        "focus": {
            "now": focus_now,
            "next": focus_next,
            "shipped": focus_shipped,
        },
        "recent_releases": release_list,
        "recent_pull_requests": pr_list,
    }
    Path("site/data/profile_snapshot.json").write_text(
        json.dumps(dashboard_data, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print("  -> site/data/profile_snapshot.json")

    # Load and render Jinja2 template
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader("templates"),
        keep_trailing_newline=True,
    )
    template = env.get_template("README.md.tpl")

    readme = template.render(
        username=USERNAME,
        dashboard_url=f"https://{USERNAME}.github.io/{USERNAME}/",
        recent_created=recent_created,
        contributions=contributions,
        releases=release_list,
        pull_requests=pr_list,
        focus_now=focus_now,
        focus_next=focus_next,
        focus_shipped=focus_shipped,
        snapshot=snapshot,
        scorecard=scorecard,
        data_scope=data_scope,
        top_languages=top_languages,
        featured_repo_facts=featured_repo_facts,
        repo_language_matrix=repo_language_matrix,
    )

    Path("README.md").write_text(readme)
    print("-> README.md written")
    print("\nDone!")


if __name__ == "__main__":
    main()

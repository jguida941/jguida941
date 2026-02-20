#!/usr/bin/env python3
"""Master orchestrator: fetch data, generate SVGs, render README."""

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
from scripts.generate_game_card import generate as gen_game_card
from scripts.generate_playable_game_data import generate as gen_playable_game_data


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
    try:
        owner = repo["owner"]["login"]
        name = repo["name"]
        url = f"repos/{owner}/{name}/contents/.github/workflows"
        wf_data = gh.paginated_get(url, per_page=1)
        return isinstance(wf_data, list) and len(wf_data) > 0
    except Exception:
        return None


def main():
    print("=== GitHub Profile README Builder ===")
    print(f"User: {USERNAME}")

    # Ensure assets dir exists
    Path("assets").mkdir(exist_ok=True)

    # ── Fetch Data ──────────────────────────────────────────
    print("\n[1/7] Fetching repos...")
    repos = gh.get_repos(include_forks=False)
    all_repos = gh.get_repos(include_forks=True)
    fork_count = sum(1 for r in all_repos if r.get("fork"))
    print(
        f"  Found {len(repos)} public non-fork repos "
        f"({len(all_repos)} public owned total, {fork_count} forks)"
    )

    print("[2/7] Fetching language data...")
    language_bytes = gh.get_all_languages(repos)
    lang_count = len([l for l, b in language_bytes.items() if b > 0])
    print(f"  {lang_count} languages across all repos")

    print("[3/7] Fetching events...")
    events = gh.get_events()
    print(f"  {len(events)} recent events")

    print("[4/7] Fetching commit count...")
    total_commits = gh.get_total_commits(repos)
    print(f"  {total_commits} total commits")

    print("[5/7] Counting CI/CD pipelines...")
    ci_count = gh.get_repos_with_ci(repos)
    print(f"  {ci_count} repos with CI/CD")

    print("[6/7] Fetching contribution calendar...")
    calendar = gh.get_contribution_calendar()
    total_contributions = calendar.get("totalContributions", 0) if calendar else 0
    print(f"  {total_contributions} contributions this year")

    # Derived stats
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
    print("\n[7/7] Generating SVGs...")

    # 1. Badges
    gen_badges(
        total_repos=len(repos),
        ci_count=ci_count,
        lang_count=lang_count,
        stars=total_stars,
        total_commits=total_commits,
    )
    print("  -> assets/badges.svg")

    # 2. Language chart
    gen_lang_chart(language_bytes)
    print("  -> assets/lang_breakdown.svg")

    # 3. Currently working on
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
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
            # Try to get last commit message
            last_msg = ""
            try:
                commits_data = gh.paginated_get(
                    f"repos/{r['owner']['login']}/{r['name']}/commits",
                    {"per_page": 1},
                    per_page=1,
                )
                if commits_data:
                    last_msg = commits_data[0].get("commit", {}).get("message", "").split("\n")[0]
            except Exception:
                pass
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

    # 6. Game card
    gen_game_card(
        total_commits=total_commits,
        total_repos=len(repos),
        total_stars=total_stars,
        language_data=language_bytes,
        prs_merged=prs_merged,
        releases=releases,
        ci_pipelines=ci_count,
        streak_days=streak_days,
    )
    print("  -> assets/game_card.svg")

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
        "public_owned_repos_total": len(all_repos),
        "public_owned_forks_total": fork_count,
        "public_owned_nonfork_repos_total": len(repos),
    }

    snapshot = {
        "total_commits": total_commits,
        "total_repos": len(repos),
        "total_stars": total_stars,
        "languages_count": lang_count,
        "prs_merged": prs_merged,
        "releases": releases,
        "ci_repos": ci_count,
        "streak_days": streak_days,
        "total_contributions": total_contributions,
    }

    # Recently created repos (top 10 non-fork by creation date)
    recent_created = sorted(repos, key=lambda r: r.get("created_at", ""), reverse=True)[:10]

    # Latest contributions (from events)
    contributions = []
    seen_contrib = set()
    for e in events:
        repo_name = e.get("repo", {}).get("name", "")
        if repo_name and repo_name not in seen_contrib:
            seen_contrib.add(repo_name)
            contributions.append({
                "repo": repo_name,
                "url": f"https://github.com/{repo_name}",
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
        release_list.append({
            "repo": repo_name,
            "repo_url": f"https://github.com/{repo_name}",
            "tag": release.get("tag_name", ""),
            "url": release.get("html_url", ""),
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
        pr_list.append({
            "title": pr.get("title", ""),
            "url": pr.get("html_url", ""),
            "repo": repo_name,
            "repo_url": f"https://github.com/{repo_name}",
            "state": state,
            "time_ago": _time_ago(e.get("created_at", "")),
        })
        if len(pr_list) >= 5:
            break

    # Playable game data
    game_data_path = gen_playable_game_data(
        username=USERNAME,
        total_commits=total_commits,
        total_repos=len(repos),
        total_stars=total_stars,
        language_data=language_bytes,
        prs_merged=prs_merged,
        releases=releases,
        ci_pipelines=ci_count,
        streak_days=streak_days,
        total_contributions=total_contributions,
        featured_repos=spotlight_data,
        contributions=contributions,
        data_scope=data_scope,
    )
    print(f"-> {game_data_path}")

    # Resolve game URL (project page by default)
    repo_slug = os.environ.get("GITHUB_REPOSITORY", f"{USERNAME}/stats")
    repo_name = repo_slug.split("/")[-1]
    if repo_name.lower() == f"{USERNAME.lower()}.github.io":
        default_game_url = f"https://{USERNAME}.github.io/"
    else:
        default_game_url = f"https://{USERNAME}.github.io/{repo_name}/"
    game_url = os.environ.get("GAME_URL", default_game_url)

    # Load and render Jinja2 template
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader("templates"),
        keep_trailing_newline=True,
    )
    template = env.get_template("README.md.tpl")

    readme = template.render(
        username=USERNAME,
        game_url=game_url,
        recent_created=recent_created,
        contributions=contributions,
        releases=release_list,
        pull_requests=pr_list,
        snapshot=snapshot,
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

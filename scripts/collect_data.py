"""Collect profile data from GitHub APIs."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts import github_client as gh
from scripts.runtime_env import cache_mode_from_env, token_mode_from_env


def detect_token_mode() -> str:
    return token_mode_from_env()


def detect_cache_mode() -> dict[str, object]:
    return cache_mode_from_env()


@dataclass(frozen=True)
class CollectedProfileData:
    repo_counts: dict[str, int | None]
    repos: list[dict[str, Any]]
    all_repos: list[dict[str, Any]]
    language_bytes: dict[str, int]
    events: list[dict[str, Any]]
    latest_push_message_by_repo: dict[str, str]
    public_scope_commits: int | None
    ci_count_probe: int
    calendar: dict[str, Any] | None
    total_contributions: int | None
    token_mode: str
    cache_mode: dict[str, Any]


def collect_profile_data(logger=print) -> CollectedProfileData:
    logger("\n[1/7] Fetching repo scope counts...")
    repo_counts = gh.get_owned_repo_scope_counts()
    logger(
        "  Scope totals:"
        f" public non-fork={repo_counts['public_owned_nonfork']},"
        f" public forks={repo_counts['public_owned_forks']},"
        f" public total={repo_counts['public_owned_total']},"
        f" private owned={repo_counts['private_owned'] if repo_counts['private_owned'] is not None else 'n/a'}"
    )

    logger("[2/7] Fetching repos...")
    repos = gh.get_repos(include_forks=False)
    all_repos = gh.get_repos(include_forks=True)
    # Keep scope counts and fetched repo lists consistent when the scope endpoint degrades.
    if repos and int(repo_counts.get("public_owned_nonfork", 0) or 0) == 0:
        repo_counts["public_owned_nonfork"] = len(repos)
    if all_repos and int(repo_counts.get("public_owned_total", 0) or 0) == 0:
        repo_counts["public_owned_total"] = len(all_repos)
    if repo_counts.get("public_owned_total") is not None and repo_counts.get("public_owned_nonfork") is not None:
        repo_counts["public_owned_forks"] = max(
            0,
            int(repo_counts["public_owned_total"]) - int(repo_counts["public_owned_nonfork"]),
        )
    if repo_counts.get("private_owned") is None:
        previous_private = _read_previous_private_owned_count()
        if previous_private is not None:
            repo_counts["private_owned"] = previous_private
    logger(
        f"  Found {len(repos)} public non-fork repos "
        f"({len(all_repos)} public owned total, {repo_counts['public_owned_forks']} forks)"
    )

    logger("[3/7] Fetching language data...")
    language_bytes = gh.get_all_languages(repos)
    lang_count = len([lang for lang, bytes_ in language_bytes.items() if bytes_ > 0])
    logger(f"  {lang_count} languages across all repos")

    logger("[4/7] Fetching events...")
    events = gh.get_events()
    logger(f"  {len(events)} recent events")

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

    logger("[5/7] Fetching public repo commit count...")
    public_scope_commits = gh.get_total_commits(repos, use_global_fallback=True)
    if public_scope_commits is None:
        logger("  n/a public-scope commits (data unavailable for this run)")
    else:
        logger(f"  {public_scope_commits} public-scope commits")

    logger("[6/7] Counting CI/CD pipelines...")
    ci_count_probe = gh.get_repos_with_ci(repos)
    logger(f"  Probe found {ci_count_probe} repos with CI/CD")

    logger("[7/7] Fetching contribution calendar...")
    calendar = gh.get_contribution_calendar()
    total_contributions: int | None = None
    if calendar:
        try:
            total_contributions = int(calendar.get("totalContributions", 0))
        except (TypeError, ValueError):
            total_contributions = None
    if total_contributions is None:
        logger("  n/a contributions in the last 12 months (calendar unavailable for this run)")
    else:
        logger(f"  {total_contributions} contributions in the last 12 months")

    return CollectedProfileData(
        repo_counts=repo_counts,
        repos=repos,
        all_repos=all_repos,
        language_bytes=language_bytes,
        events=events,
        latest_push_message_by_repo=latest_push_message_by_repo,
        public_scope_commits=public_scope_commits,
        ci_count_probe=ci_count_probe,
        calendar=calendar,
        total_contributions=total_contributions,
        token_mode=detect_token_mode(),
        cache_mode=detect_cache_mode(),
    )


def _read_previous_private_owned_count() -> int | None:
    """Read the last known private-owned repo count from snapshot output."""
    snapshot_path = Path("site/data/profile_snapshot.json")
    payloads: list[dict[str, Any]] = []
    if snapshot_path.exists():
        try:
            loaded = json.loads(snapshot_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                payloads.append(loaded)
        except (OSError, ValueError):
            pass

    try:
        result = subprocess.run(
            ["git", "show", "HEAD:site/data/profile_snapshot.json"],
            check=True,
            text=True,
            capture_output=True,
        )
        loaded = json.loads(result.stdout)
        if isinstance(loaded, dict):
            payloads.append(loaded)
    except (OSError, ValueError, subprocess.CalledProcessError):
        pass

    for payload in payloads:
        snapshot = payload.get("snapshot") if isinstance(payload, dict) else None
        if not isinstance(snapshot, dict):
            continue
        value = snapshot.get("private_owned_repos")
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            continue
        if parsed >= 0:
            return parsed
    return None

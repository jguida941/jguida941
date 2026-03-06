"""Small helper functions shared by profile pipeline modules."""

from __future__ import annotations

from datetime import datetime, timezone

from scripts import github_client as gh


def time_ago(iso_str: str) -> str:
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


def activity_label(event_type: str) -> str:
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


def ci_text(ci_state: bool | None) -> str:
    if ci_state is True:
        return "yes"
    if ci_state is False:
        return "no"
    return "n/a"


def has_ci_workflow(repo: dict, allow_network_calls: bool = True) -> bool | None:
    """Best-effort check for .github/workflows in repo."""
    if "has_ci_workflows" in repo:
        return bool(repo.get("has_ci_workflows"))

    if not allow_network_calls:
        return None

    try:
        owner = repo["owner"]["login"]
        name = repo["name"]
        return gh.get_repo_ci_state(owner, name)
    except Exception:
        return None

"""Small helper functions shared by profile pipeline modules."""

from __future__ import annotations

import base64
import binascii
import re
from datetime import datetime, timezone

from scripts.github import github_client as gh
from scripts.core.config import BOT_ACTOR_PREFIXES, BOT_COMMIT_MARKERS, SELF_REPO, USERNAME


_CREDENTIAL_TEXT_PATTERNS = (
    # Exact legacy PAT and AWS secret assignments.  The assignment delimiter is
    # load-bearing: documentation about either environment variable stays safe.
    re.compile(
        r"\b(?:personal_github_token|github_token|gh_token)\s*[:=]\s*['\"]?"
        r"[0-9a-f]{40}(?![0-9a-f])",
        re.IGNORECASE,
    ),
    re.compile(
        r"\baws_secret_access_key\s*[:=]\s*['\"]?"
        r"[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])",
        re.IGNORECASE,
    ),
    re.compile(
        r"\baws_access_key_id\s*[:=]\s*['\"]?"
        r"AKIA[A-Z0-9]{16}(?![A-Z0-9])",
        re.IGNORECASE,
    ),
    # Explicit HTTP authorization syntax. Basic credentials are handled below
    # because their payload has a stronger, decodable user:password boundary.
    re.compile(
        r"\bauthorization\s*[:=]\s*(?:bearer|token)\s+"
        r"[A-Za-z0-9._~+/=-]{8,}",
        re.IGNORECASE,
    ),
    # A standalone bearer value must look opaque, not like the phrase
    # "Bearer token refresh handling" or "bearer authentication support".
    re.compile(
        r"\bbearer\s+(?=[A-Za-z0-9._~+/=-]{12,}\b)"
        r"(?=[A-Za-z0-9._~+/=-]*[0-9._~+/=-])"
        r"[A-Za-z0-9._~+/=-]+",
        re.IGNORECASE,
    ),
    # The classic GitHub PAT has an exact 36-character payload.  Preserve the
    # uppercase/digit heuristic as a backstop for synthetic/non-classic shapes
    # used by hostile fixtures while exact length prevents ordinary names such
    # as ghp_tokenformatvalidator from matching.
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36}(?![A-Za-z0-9])"),
    re.compile(
        r"\b(?:gh[pousr]|github_pat)_"
        r"(?=[A-Za-z0-9_]{8,}\b)(?=[A-Za-z0-9_]*[A-Z0-9])"
        r"[A-Za-z0-9_]+"
    ),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b", re.IGNORECASE),
    re.compile(
        r"\bsk-(?:proj-)?(?=[A-Za-z0-9_-]{16,}\b)"
        r"(?=[A-Za-z0-9_-]*[0-9_])[A-Za-z0-9_-]+"
    ),
    re.compile(r"\bAIza[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----"),
    re.compile(r"\b[a-z][a-z0-9+.-]*://[^/\s:@]+:[^/\s@]+@", re.IGNORECASE),
    re.compile(
        r"^\s*(?:export\s+)?['\"]?(?:api[_ -]?key|access[_ -]?token|"
        r"refresh[_ -]?token|password|"
        r"client[_ -]?secret|secret[_ -]?access[_ -]?key)"
        r"['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9._~+/=-]{8,}['\"]?"
        r"\s*;?\s*(?:#.*)?$",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\."
        r"[A-Za-z0-9_-]{10,}\b"
    ),
)

_HEADLINE_CREDENTIAL_PATTERNS = (
    # A bare AWS access-key identifier is high-confidence in prose only when it
    # is a standalone token. Repository slugs and URLs may legitimately contain
    # the same byte shape as part of a larger identity.
    re.compile(r"(?<![A-Za-z0-9_-])AKIA[A-Z0-9]{16}(?![A-Za-z0-9_-])"),
)

_CI_CONTROL_MARKERS = frozenset(("[skip ci]", "[ci skip]"))
_KNOWN_BOT_COMMIT_MARKERS = tuple(
    marker for marker in BOT_COMMIT_MARKERS if marker not in _CI_CONTROL_MARKERS
)
_TERMINAL_CI_CONTROL_PATTERN = re.compile(
    r"(?:^|\s)(?:\[skip ci\]|\[ci skip\])\s*$",
    re.IGNORECASE,
)

_BASIC_CREDENTIAL_PATTERN = re.compile(
    r"(?:\bauthorization\s*[:=]\s*)?\bbasic\s+"
    r"([A-Za-z0-9+/]+={0,2})(?![A-Za-z0-9+/=])",
    re.IGNORECASE,
)


def _contains_basic_credential(value: str) -> bool:
    """Return true only for Basic payloads that decode to user:password bytes."""
    for match in _BASIC_CREDENTIAL_PATTERN.finditer(value):
        payload = match.group(1)
        try:
            decoded = base64.b64decode(payload, validate=True)
        except (binascii.Error, ValueError):
            continue
        if b":" in decoded:
            return True
    return False


def is_bot_commit_message(message: str | None) -> bool:
    """True for empty or automation-generated commit messages."""
    if not message or not message.strip():
        return True
    headline = message.strip()
    lowered = headline.lower()
    return any(marker in lowered for marker in _KNOWN_BOT_COMMIT_MARKERS) or bool(
        _TERMINAL_CI_CONTROL_PATTERN.search(headline)
    )


def contains_credential_material(value: str | None) -> bool:
    """Classify credential-shaped text while retaining security-domain prose."""
    if not isinstance(value, str) or not value:
        return False
    return _contains_basic_credential(value) or any(
        pattern.search(value) for pattern in _CREDENTIAL_TEXT_PATTERNS
    )


# Backward-compatible public name; both call sites use the same classifier.
is_credential_bearing_text = contains_credential_material


def safe_commit_headline(message: str | None) -> str:
    """Return one publishable commit-headline line, or an empty redaction."""
    if not isinstance(message, str):
        return ""
    headline = message.split("\n", 1)[0].strip()
    contains_headline_credential = contains_credential_material(headline) or any(
        pattern.search(headline) for pattern in _HEADLINE_CREDENTIAL_PATTERNS
    )
    if is_bot_commit_message(headline) or contains_headline_credential:
        return ""
    return headline


def is_bot_actor(login: str | None) -> bool:
    """True when the event actor is an automation account (e.g. github-actions[bot])."""
    if not login:
        return False
    lowered = login.lower()
    return any(lowered.startswith(prefix) for prefix in BOT_ACTOR_PREFIXES)


def is_self_repo(name: str | None, full_name: str | None = None) -> bool:
    """True when the repo is the profile repo itself (username/username)."""
    if name and name == SELF_REPO:
        return True
    if full_name and full_name == f"{USERNAME}/{SELF_REPO}":
        return True
    return False


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
        state = repo.get("has_ci_workflows")
        return state if isinstance(state, bool) else None

    if not allow_network_calls:
        return None

    try:
        owner = repo["owner"]["login"]
        name = repo["name"]
        return gh.get_repo_ci_state(owner, name)
    except Exception:
        return None

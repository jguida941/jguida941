"""Audit and update required branch checks."""

from __future__ import annotations

from dataclasses import dataclass

from scripts.gh_cli import run_json


DEFAULT_REQUIRED_CHECKS = (
    "Test Profile Pipeline",
    "Build Analytics & README",
)


@dataclass(frozen=True)
class BranchProtectionAudit:
    repo: str
    branch: str
    required_checks: list[str]
    configured_checks: list[str]
    missing_checks: list[str]
    extra_checks: list[str]


def _run_gh_json_dict(cmd: list[str]) -> dict:
    """Call run_json and verify the result is a dict."""
    payload = run_json(cmd)
    if not isinstance(payload, dict):
        raise RuntimeError("Unexpected response shape from `gh api`")
    return payload


def _normalized_unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        output.append(normalized)
    return output


def get_configured_required_checks(repo: str, branch: str) -> list[str]:
    try:
        payload = _run_gh_json_dict(
            [
                "gh",
                "api",
                f"repos/{repo}/branches/{branch}/protection",
                "-H",
                "Accept: application/vnd.github+json",
            ]
        )
    except RuntimeError as exc:
        message = str(exc)
        if "Branch not protected" in message:
            return []
        raise

    required_status = payload.get("required_status_checks", {})
    if not isinstance(required_status, dict):
        return []

    checks: list[str] = []
    contexts = required_status.get("contexts", [])
    if isinstance(contexts, list):
        checks.extend(str(item) for item in contexts if isinstance(item, str))

    checks_nodes = required_status.get("checks", [])
    if isinstance(checks_nodes, list):
        for node in checks_nodes:
            if not isinstance(node, dict):
                continue
            context = node.get("context")
            if isinstance(context, str):
                checks.append(context)

    return _normalized_unique(checks)


def audit_required_checks(
    repo: str,
    branch: str,
    required_checks: list[str] | tuple[str, ...],
) -> BranchProtectionAudit:
    required = _normalized_unique([str(item) for item in required_checks])
    configured = get_configured_required_checks(repo, branch)
    missing = [name for name in required if name not in configured]
    extra = [name for name in configured if name not in required]
    return BranchProtectionAudit(
        repo=repo,
        branch=branch,
        required_checks=required,
        configured_checks=configured,
        missing_checks=missing,
        extra_checks=extra,
    )


def apply_required_checks(
    repo: str,
    branch: str,
    required_checks: list[str] | tuple[str, ...],
    *,
    strict: bool = True,
) -> None:
    checks = _normalized_unique([str(item) for item in required_checks])
    cmd_patch = [
        "gh",
        "api",
        "--method",
        "PATCH",
        f"repos/{repo}/branches/{branch}/protection/required_status_checks",
        "-H",
        "Accept: application/vnd.github+json",
        "-F",
        f"strict={str(strict).lower()}",
    ]
    for check in checks:
        cmd_patch.extend(["-F", f"contexts[]={check}"])

    try:
        _run_gh_json_dict(cmd_patch)
        return
    except RuntimeError as exc:
        message = str(exc)
        if "Branch not protected" not in message:
            raise

    # Branch protection is not enabled yet. Create it with required checks.
    cmd_put = [
        "gh",
        "api",
        "--method",
        "PUT",
        f"repos/{repo}/branches/{branch}/protection",
        "-H",
        "Accept: application/vnd.github+json",
        "-F",
        f"required_status_checks[strict]={str(strict).lower()}",
        "-F",
        "enforce_admins=false",
        "-F",
        "required_pull_request_reviews=null",
        "-F",
        "restrictions=null",
    ]
    for check in checks:
        cmd_put.extend(["-F", f"required_status_checks[contexts][]={check}"])

    _run_gh_json_dict(cmd_put)

#!/usr/bin/env python3
"""Validate generated profile artifacts for obvious data-quality regressions."""

import os
import re
from pathlib import Path


USERNAME = os.environ.get("GITHUB_USERNAME", "jguida941")
README_PATH = Path("README.md")
WORKING_SVG_PATH = Path("assets/currently_working.svg")


def _section(text: str, heading: str) -> str:
    pattern = rf"### {re.escape(heading)}\n(.*?)(?:\n### |\Z)"
    match = re.search(pattern, text, flags=re.S)
    return match.group(1) if match else ""


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    if not README_PATH.exists():
        errors.append("README.md not found")
        _finish(errors, warnings)
        return 1

    readme = README_PATH.read_text(encoding="utf-8")

    activity = _section(readme, "Latest Owned Repo Activity")
    if not activity:
        errors.append("Missing section: Latest Owned Repo Activity")
    else:
        repos = re.findall(r"\[\*\*([^*]+)\*\*\]\(https://github\.com/[^\)]+\)", activity)
        for repo in repos:
            if "/" in repo and not repo.startswith(f"{USERNAME}/"):
                errors.append(f"Unexpected external repo in owned-activity section: {repo}")

    twelve_month_match = re.search(
        r"\| Last 12 Months Contributions \| `([^`]+)` \|",
        readme,
    )
    if twelve_month_match:
        value = twelve_month_match.group(1).strip()
        normalized = value.replace(",", "")
        try:
            contribution_value = int(normalized)
        except ValueError:
            warnings.append("Last 12 months contribution value is not numeric")
            contribution_value = 0
        if contribution_value <= 0:
            warnings.append("Last 12 months contribution value is 0")
    else:
        errors.append("Missing row: Last 12 Months Contributions")

    if WORKING_SVG_PATH.exists():
        working_svg = WORKING_SVG_PATH.read_text(encoding="utf-8")
        placeholder_hits = working_svg.count("latest commit message unavailable")
        if placeholder_hits >= 3:
            warnings.append(
                f"Currently working card has {placeholder_hits} placeholder commit messages"
            )
    else:
        warnings.append("assets/currently_working.svg not found")

    _finish(errors, warnings)
    return 1 if errors else 0


def _finish(errors: list[str], warnings: list[str]) -> None:
    if errors:
        print("Profile validation failed:")
        for err in errors:
            print(f"  - {err}")
    else:
        print("Profile validation passed")

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")


if __name__ == "__main__":
    raise SystemExit(main())

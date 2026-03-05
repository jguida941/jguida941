#!/usr/bin/env python3
"""Validate generated profile artifacts for obvious data-quality regressions."""

import os
import re
from pathlib import Path


USERNAME = os.environ.get("GITHUB_USERNAME", "jguida941")
README_PATH = Path("README.md")
WORKING_SVG_PATH = Path("assets/currently_working.svg")
METRICS_SVG_PATH = Path("metrics.general.svg")


def _section(text: str, heading: str) -> str:
    pattern = rf"### {re.escape(heading)}\n(.*?)(?:\n### |\Z)"
    match = re.search(pattern, text, flags=re.S)
    return match.group(1) if match else ""


def _parse_int(value: str) -> int | None:
    normalized = value.strip().replace(",", "")
    try:
        return int(normalized)
    except ValueError:
        return None


def _extract_readme_metric(readme: str, label: str) -> int | None:
    match = re.search(rf"\| {re.escape(label)} \| `([^`]+)` \|", readme)
    if not match:
        return None
    return _parse_int(match.group(1))


def _extract_svg_metric(svg_text: str, label: str) -> int | None:
    match = re.search(rf"([0-9][0-9,]*)\s+{re.escape(label)}\b", svg_text)
    if not match:
        return None
    return _parse_int(match.group(1))


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
        contribution_value = _parse_int(twelve_month_match.group(1))
        if contribution_value is None:
            warnings.append("Last 12 months contribution value is not numeric")
            contribution_value = 0
        if contribution_value <= 0:
            warnings.append("Last 12 months contribution value is 0")
    else:
        errors.append("Missing row: Last 12 Months Contributions")

    total_stars = _extract_readme_metric(readme, "Total Stars")
    if total_stars is None:
        errors.append("Missing or invalid row: Total Stars")

    recent_releases = _extract_readme_metric(readme, "Releases (Recent Events)")
    if recent_releases is None:
        errors.append("Missing or invalid row: Releases (Recent Events)")

    blank_pr_links = readme.count("| []() |")
    if blank_pr_links > 0:
        warnings.append(f"README contains {blank_pr_links} blank PR links")

    if METRICS_SVG_PATH.exists():
        metrics_svg = METRICS_SVG_PATH.read_text(encoding="utf-8")

        metrics_repositories = _extract_svg_metric(metrics_svg, "Repositories")
        metrics_releases = _extract_svg_metric(metrics_svg, "Releases")
        metrics_stargazers = _extract_svg_metric(metrics_svg, "Stargazers")

        if metrics_repositories is None:
            errors.append("metrics.general.svg missing Repositories metric")
        elif metrics_repositories <= 0:
            errors.append("metrics.general.svg has non-positive Repositories metric")

        if metrics_releases is None:
            errors.append("metrics.general.svg missing Releases metric")

        if metrics_stargazers is None:
            errors.append("metrics.general.svg missing Stargazers metric")

        if (
            total_stars is not None
            and total_stars > 0
            and metrics_stargazers is not None
            and metrics_stargazers == 0
        ):
            errors.append(
                "metrics.general.svg reports 0 Stargazers while README snapshot reports non-zero Total Stars"
            )

        if (
            recent_releases is not None
            and recent_releases > 0
            and metrics_releases is not None
            and metrics_releases == 0
        ):
            errors.append(
                "metrics.general.svg reports 0 Releases while README snapshot reports non-zero recent releases"
            )
    else:
        errors.append("metrics.general.svg not found")

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

#!/usr/bin/env python3
"""Validate generated profile artifacts for obvious data-quality regressions."""

import json
import os
import re
from pathlib import Path


USERNAME = os.environ.get("GITHUB_USERNAME", "jguida941")
README_PATH = Path("README.md")
WORKING_SVG_PATH = Path("assets/currently_working.svg")
METRICS_SVG_PATH = Path("metrics.general.svg")
PROFILE_SNAPSHOT_PATH = Path("site/data/profile_snapshot.json")


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

    if PROFILE_SNAPSHOT_PATH.exists():
        try:
            profile_snapshot = json.loads(PROFILE_SNAPSHOT_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            errors.append("site/data/profile_snapshot.json is not valid JSON")
            profile_snapshot = {}
        else:
            required_keys = {
                "generated_at",
                "username",
                "snapshot",
                "snapshot_rows",
                "snapshot_cards",
                "scorecard",
                "scorecard_cards",
                "data_quality",
                "focus",
                "top_languages",
                "repo_language_matrix",
                "activity_feed",
                "recent_created",
            }
            missing_keys = sorted(key for key in required_keys if key not in profile_snapshot)
            if missing_keys:
                errors.append(
                    "site/data/profile_snapshot.json missing keys: "
                    + ", ".join(missing_keys)
                )

            snapshot_username = str(profile_snapshot.get("username", "")).strip()
            if snapshot_username and snapshot_username != USERNAME:
                warnings.append(
                    "site/data/profile_snapshot.json username does not match GITHUB_USERNAME"
                )

            focus = profile_snapshot.get("focus", {})
            if not isinstance(focus, dict):
                errors.append("site/data/profile_snapshot.json focus must be an object")
            else:
                for lane in ("now", "next", "shipped"):
                    if not isinstance(focus.get(lane), list):
                        errors.append(
                            f"site/data/profile_snapshot.json focus.{lane} must be an array"
                        )

            if not isinstance(profile_snapshot.get("scorecard", {}), dict):
                errors.append("site/data/profile_snapshot.json scorecard must be an object")
            if not isinstance(profile_snapshot.get("snapshot", {}), dict):
                errors.append("site/data/profile_snapshot.json snapshot must be an object")
            if not isinstance(profile_snapshot.get("data_quality", {}), dict):
                errors.append("site/data/profile_snapshot.json data_quality must be an object")
            if not isinstance(profile_snapshot.get("activity_feed", []), list):
                errors.append("site/data/profile_snapshot.json activity_feed must be an array")
            if not isinstance(profile_snapshot.get("repo_language_matrix", []), list):
                errors.append("site/data/profile_snapshot.json repo_language_matrix must be an array")
    else:
        errors.append("site/data/profile_snapshot.json not found")

    delivery = _section(readme, "Recent Delivery Feed")
    if not delivery:
        errors.append("Missing section: Recent Delivery Feed")

    matrix = _section(readme, "Project Matrix (Featured + Active)")
    if not matrix:
        errors.append("Missing section: Project Matrix (Featured + Active)")
    else:
        repos = re.findall(r"\[\*\*([^*]+)\*\*\]\(https://github\.com/[^\)]+\)", matrix)
        for repo in repos:
            if "/" in repo and not repo.startswith(f"{USERNAME}/"):
                errors.append(f"Unexpected external repo in project matrix: {repo}")

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

    if "No recent owned-repo activity found" in readme:
        warnings.append("README still contains old empty focus fallback text")

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

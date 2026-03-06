#!/usr/bin/env python3
"""Validate generated profile artifacts for obvious data-quality regressions."""

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from scripts.profile_contract import SNAPSHOT_METRICS


USERNAME = os.environ.get("GITHUB_USERNAME", "jguida941")
README_PATH = Path("README.md")
WORKING_SVG_PATH = Path("assets/currently_working.svg")
METRICS_SVG_PATH = Path("metrics.general.svg")
FOCUS_SVG_PATH = Path("assets/now_next_shipped.svg")
SNAPSHOT_SVG_PATH = Path("assets/raw_snapshot.svg")
PROFILE_SNAPSHOT_PATH = Path("site/data/profile_snapshot.json")


def _section(text: str, heading: str) -> str:
    pattern = rf"### {re.escape(heading)}\n(.*?)(?:\n### |\Z)"
    match = re.search(pattern, text, flags=re.S)
    return match.group(1) if match else ""


def _parse_int(value: object) -> int | None:
    normalized = str(value).strip().replace(",", "")
    if normalized.lower() == "n/a":
        return None
    try:
        return int(normalized)
    except ValueError:
        return None


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

    required_sections = (
        "Builder Scorecard",
        "Current Focus",
        "By The Numbers",
        "Raw Data Snapshot (Python Pull)",
        "Deep Dive Data",
    )
    for heading in required_sections:
        if not _section(readme, heading):
            errors.append(f"Missing section: {heading}")

    if "assets/now_next_shipped.svg" not in readme:
        errors.append("README does not embed assets/now_next_shipped.svg")
    if "assets/raw_snapshot.svg" not in readme:
        errors.append("README does not embed assets/raw_snapshot.svg")
    if "site/data/profile_snapshot.json" not in readme:
        errors.append("README does not link site/data/profile_snapshot.json")

    if not FOCUS_SVG_PATH.exists():
        errors.append("assets/now_next_shipped.svg not found")
    if not SNAPSHOT_SVG_PATH.exists():
        errors.append("assets/raw_snapshot.svg not found")

    profile_snapshot: dict = {}
    if PROFILE_SNAPSHOT_PATH.exists():
        try:
            profile_snapshot = json.loads(PROFILE_SNAPSHOT_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            errors.append("site/data/profile_snapshot.json is not valid JSON")
            profile_snapshot = {}
    else:
        errors.append("site/data/profile_snapshot.json not found")

    if profile_snapshot:
        required_keys = {
            "generated_at",
            "username",
            "dashboard_url",
            "snapshot",
            "snapshot_rows",
            "snapshot_cards",
            "scorecard",
            "scorecard_cards",
            "data_scope",
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
                "site/data/profile_snapshot.json missing keys: " + ", ".join(missing_keys)
            )

        snapshot_username = str(profile_snapshot.get("username", "")).strip()
        if snapshot_username and snapshot_username != USERNAME:
            warnings.append("site/data/profile_snapshot.json username does not match GITHUB_USERNAME")

        snapshot = profile_snapshot.get("snapshot", {})
        if not isinstance(snapshot, dict):
            errors.append("site/data/profile_snapshot.json snapshot must be an object")
            snapshot = {}

        snapshot_rows = profile_snapshot.get("snapshot_rows", [])
        if not isinstance(snapshot_rows, list):
            errors.append("site/data/profile_snapshot.json snapshot_rows must be an array")
            snapshot_rows = []

        expected_snapshot_keys = {entry["key"] for entry in SNAPSHOT_METRICS}
        row_keys = {
            row.get("key")
            for row in snapshot_rows
            if isinstance(row, dict) and isinstance(row.get("key"), str)
        }
        missing_snapshot_rows = sorted(expected_snapshot_keys - row_keys)
        if missing_snapshot_rows:
            errors.append(
                "site/data/profile_snapshot.json snapshot_rows missing metric keys: "
                + ", ".join(missing_snapshot_rows)
            )

        missing_snapshot_values = sorted(key for key in expected_snapshot_keys if key not in snapshot)
        if missing_snapshot_values:
            errors.append(
                "site/data/profile_snapshot.json snapshot missing metric keys: "
                + ", ".join(missing_snapshot_values)
            )

        snapshot_cards = profile_snapshot.get("snapshot_cards", [])
        if not isinstance(snapshot_cards, list):
            errors.append("site/data/profile_snapshot.json snapshot_cards must be an array")
        else:
            card_keys = {
                card.get("key")
                for card in snapshot_cards
                if isinstance(card, dict) and isinstance(card.get("key"), str)
            }
            missing_card_keys = sorted(expected_snapshot_keys - card_keys)
            if missing_card_keys:
                errors.append(
                    "site/data/profile_snapshot.json snapshot_cards missing keys: "
                    + ", ".join(missing_card_keys)
                )

        focus = profile_snapshot.get("focus", {})
        if not isinstance(focus, dict):
            errors.append("site/data/profile_snapshot.json focus must be an object")
        else:
            for lane in ("now", "next", "shipped"):
                lane_items = focus.get(lane)
                if not isinstance(lane_items, list):
                    errors.append(f"site/data/profile_snapshot.json focus.{lane} must be an array")

        if not isinstance(profile_snapshot.get("scorecard", {}), dict):
            errors.append("site/data/profile_snapshot.json scorecard must be an object")
        if not isinstance(profile_snapshot.get("data_scope", {}), dict):
            errors.append("site/data/profile_snapshot.json data_scope must be an object")
        if not isinstance(profile_snapshot.get("data_quality", {}), dict):
            errors.append("site/data/profile_snapshot.json data_quality must be an object")
        if not isinstance(profile_snapshot.get("activity_feed", []), list):
            errors.append("site/data/profile_snapshot.json activity_feed must be an array")
        if not isinstance(profile_snapshot.get("repo_language_matrix", []), list):
            errors.append("site/data/profile_snapshot.json repo_language_matrix must be an array")
        if not isinstance(profile_snapshot.get("recent_created", []), list):
            errors.append("site/data/profile_snapshot.json recent_created must be an array")

        stars_value = _parse_int(snapshot.get("total_stars"))
        if stars_value is None:
            warnings.append("Snapshot total_stars is missing or non-numeric")

        releases_value = _parse_int(snapshot.get("releases"))
        if releases_value is None:
            warnings.append("Snapshot releases is missing or non-numeric")

        if METRICS_SVG_PATH.exists():
            metrics_svg = METRICS_SVG_PATH.read_text(encoding="utf-8")
            metrics_repositories = _extract_svg_metric(metrics_svg, "Repositories")
            metrics_releases = _extract_svg_metric(metrics_svg, "Releases")
            metrics_stargazers = _extract_svg_metric(metrics_svg, "Stargazers")

            if metrics_repositories is None:
                warnings.append("metrics.general.svg missing Repositories metric")
            if metrics_releases is None:
                warnings.append("metrics.general.svg missing Releases metric")
            if metrics_stargazers is None:
                warnings.append("metrics.general.svg missing Stargazers metric")

            if (
                stars_value is not None
                and stars_value > 0
                and metrics_stargazers is not None
                and metrics_stargazers == 0
            ):
                warnings.append(
                    "metrics.general.svg reports 0 Stargazers while snapshot reports non-zero Total Stars"
                )

            if (
                releases_value is not None
                and releases_value > 0
                and metrics_releases is not None
                and metrics_releases == 0
            ):
                warnings.append(
                    "metrics.general.svg reports 0 Releases while snapshot reports non-zero recent releases"
                )
        else:
            warnings.append("metrics.general.svg not found")

    if WORKING_SVG_PATH.exists():
        working_svg = WORKING_SVG_PATH.read_text(encoding="utf-8")
        placeholder_hits = working_svg.count("latest commit message unavailable")
        if placeholder_hits >= 3:
            warnings.append(f"Currently working card has {placeholder_hits} placeholder commit messages")
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

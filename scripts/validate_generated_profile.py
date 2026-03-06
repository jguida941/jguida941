#!/usr/bin/env python3
"""Validate generated profile files and data contracts."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

from scripts.contracts import (
    DISALLOWED_README_HEADINGS,
    REQUIRED_PROFILE_SNAPSHOT_KEYS,
    REQUIRED_README_MARKERS,
    expected_snapshot_metric_keys,
    missing_required_keys,
)
from scripts.metrics_svg import parse_metrics_svg


USERNAME = os.environ.get("GITHUB_USERNAME", "jguida941")
README_PATH = Path("README.md")
WORKING_SVG_PATH = Path("assets/currently_working.svg")
METRICS_SVG_PATH = Path("metrics.general.svg")
FOCUS_SVG_PATH = Path("assets/now_next_shipped.svg")
SNAPSHOT_SVG_PATH = Path("assets/raw_snapshot.svg")
CONTRIBUTION_SVG_PATH = Path("assets/contribution_calendar.svg")
PROFILE_SNAPSHOT_PATH = Path("site/data/profile_snapshot.json")
EXPECTED_CARD_TITLES = {
    Path("assets/badges.svg"): "By The Numbers",
    Path("assets/builder_scorecard.svg"): "Builder Scorecard",
    Path("assets/contribution_calendar.svg"): "Contribution Calendar",
    Path("assets/now_next_shipped.svg"): "Current Focus",
    Path("assets/currently_working.svg"): "Currently Working On",
    Path("assets/lang_breakdown.svg"): "Language Breakdown",
    Path("assets/activity_heatmap.svg"): "When I Code",
    Path("assets/repo_spotlight.svg"): "Flagship Projects",
    Path("assets/raw_snapshot.svg"): "Raw Data Snapshot (Python Pull)",
    Path("assets/streak_summary.svg"): "Streak Summary",
}


@dataclass(frozen=True)
class ValidationResult:
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def _parse_int(value: object) -> int | None:
    normalized = str(value).strip().replace(",", "")
    if normalized.lower() == "n/a":
        return None
    try:
        return int(normalized)
    except ValueError:
        return None


def validate_profile() -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not README_PATH.exists():
        errors.append("README.md not found")
        return ValidationResult(errors=tuple(errors), warnings=tuple(warnings))

    readme = README_PATH.read_text(encoding="utf-8")

    for marker in REQUIRED_README_MARKERS:
        if marker not in readme:
            errors.append(f"README missing required marker: {marker}")

    for heading in DISALLOWED_README_HEADINGS:
        if heading in readme:
            errors.append(f"README should not contain duplicate heading: {heading}")

    if "assets/now_next_shipped.svg" not in readme:
        errors.append("README does not embed assets/now_next_shipped.svg")
    if "assets/raw_snapshot.svg" not in readme:
        errors.append("README does not embed assets/raw_snapshot.svg")
    if "assets/contribution_calendar.svg" not in readme:
        errors.append("README does not embed assets/contribution_calendar.svg")
    if "site/data/profile_snapshot.json" not in readme:
        errors.append("README does not link site/data/profile_snapshot.json")

    if not FOCUS_SVG_PATH.exists():
        errors.append("assets/now_next_shipped.svg not found")
    if not SNAPSHOT_SVG_PATH.exists():
        errors.append("assets/raw_snapshot.svg not found")
    if not CONTRIBUTION_SVG_PATH.exists():
        errors.append("assets/contribution_calendar.svg not found")

    for svg_path, title in EXPECTED_CARD_TITLES.items():
        if not svg_path.exists():
            errors.append(f"{svg_path} not found")
            continue
        svg_text = svg_path.read_text(encoding="utf-8")
        title_hits = len(re.findall(rf">{re.escape(title)}</text>", svg_text))
        if title_hits != 1:
            errors.append(
                f"{svg_path} should contain exactly one in-image title '{title}' (found {title_hits})"
            )

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
        missing_keys = missing_required_keys(profile_snapshot, REQUIRED_PROFILE_SNAPSHOT_KEYS)
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

        expected_snapshot_keys = expected_snapshot_metric_keys()
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
        releases_status = str(profile_snapshot.get("data_quality", {}).get("releases_status", "")).strip().lower()
        if releases_value is None and releases_status not in {"unavailable", "events_fallback", "partial", "fallback"}:
            warnings.append("Snapshot releases is missing or non-numeric")

        if METRICS_SVG_PATH.exists():
            metrics = parse_metrics_svg(METRICS_SVG_PATH)
            metrics_repositories = metrics.repositories
            metrics_releases = metrics.releases
            metrics_stargazers = metrics.stargazers

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

    return ValidationResult(errors=tuple(errors), warnings=tuple(warnings))


def _finish(result: ValidationResult) -> None:
    if result.errors:
        print("Profile validation failed:")
        for err in result.errors:
            print(f"  - {err}")
    else:
        print("Profile validation passed")

    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"  - {warning}")


def main() -> int:
    os.chdir(ROOT)
    result = validate_profile()
    _finish(result)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

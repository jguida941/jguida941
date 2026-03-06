"""Read `metrics.general.svg` values and run basic checks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Sequence


def _normalize_labels(labels: str | Sequence[str]) -> tuple[str, ...]:
    if isinstance(labels, str):
        return (labels,)
    return tuple(labels)


def extract_metric(text: str, labels: str | Sequence[str]) -> int | None:
    """Find the first number that matches one of the labels."""
    for label in _normalize_labels(labels):
        match = re.search(rf"([0-9][0-9,]*)\s+{re.escape(label)}\b", text)
        if not match:
            continue
        try:
            return int(match.group(1).replace(",", ""))
        except ValueError:
            continue
    return None


@dataclass(frozen=True)
class MetricsSvgSnapshot:
    repositories: int | None
    stargazers: int | None
    releases: int | None


def parse_metrics_svg_text(text: str) -> MetricsSvgSnapshot:
    return MetricsSvgSnapshot(
        repositories=extract_metric(text, ("Repositories", "Repository")),
        stargazers=extract_metric(text, "Stargazers"),
        releases=extract_metric(text, "Releases"),
    )


def parse_metrics_svg(path: Path | str) -> MetricsSvgSnapshot:
    svg_path = Path(path)
    text = svg_path.read_text(encoding="utf-8")
    return parse_metrics_svg_text(text)


@dataclass(frozen=True)
class MetricCheckResult:
    failures: tuple[str, ...]
    warnings: tuple[str, ...]
    snapshot: MetricsSvgSnapshot

    @property
    def ok(self) -> bool:
        return not self.failures


def check_metrics(
    snapshot: MetricsSvgSnapshot,
    *,
    require_repositories: bool = True,
    stargazers_min: int | None = None,
    releases_min: int | None = None,
) -> MetricCheckResult:
    failures: list[str] = []
    warnings: list[str] = []

    if require_repositories:
        repo_value = snapshot.repositories
        if repo_value is None or repo_value <= 0:
            failures.append("Repository metric missing or non-positive")

    if snapshot.stargazers is None:
        warnings.append("Stargazers metric missing from metrics.general.svg")
    if snapshot.releases is None:
        warnings.append("Releases metric missing from metrics.general.svg")

    if stargazers_min is not None and snapshot.stargazers is not None:
        if snapshot.stargazers < stargazers_min:
            failures.append(
                f"Stargazers below threshold: {snapshot.stargazers} < {stargazers_min}"
            )

    if releases_min is not None and snapshot.releases is not None:
        if snapshot.releases < releases_min:
            failures.append(f"Releases below threshold: {snapshot.releases} < {releases_min}")

    return MetricCheckResult(
        failures=tuple(failures),
        warnings=tuple(warnings),
        snapshot=snapshot,
    )


# Backward-compatible name for existing imports.
sanity_check = check_metrics

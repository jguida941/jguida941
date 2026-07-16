"""Closed physical inventory for committed rendered-fact artifacts."""
from __future__ import annotations

from scripts.quality.rendered_facts.policy import (
    active_profiles, artifact_path, load_policy, page_routes, provenance_path, root,
)


def expected_artifact_inventory() -> set[str]:
    expected = set()
    for page in page_routes():
        for theme in active_profiles():
            for viewport in load_policy()["matrix"]["viewports"]:
                artifact = artifact_path(page, theme, viewport["width"])
                expected.add(artifact.relative_to(root()).as_posix())
                expected.add(provenance_path(artifact).relative_to(root()).as_posix())
    return expected


def observed_artifact_inventory() -> set[str]:
    pages_root = root() / "assets" / "receipts" / "pages"
    return {
        path.relative_to(root()).as_posix()
        for path in pages_root.rglob("rendered-facts-*")
    }


def validate_artifact_inventory(observed: set[str] | None = None) -> None:
    expected = expected_artifact_inventory()
    actual = observed_artifact_inventory() if observed is None else observed
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        raise RuntimeError(
            f"rendered fact inventory drift: missing={missing!r}, unexpected={unexpected!r}"
        )

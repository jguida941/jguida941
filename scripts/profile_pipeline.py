"""Main pipeline orchestration for profile generation."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.collect_data import collect_profile_data
from scripts.collect_data import CollectedProfileData
from scripts.compute_metrics import compute_profile_model
from scripts.render_outputs import ensure_output_dirs, generate_assets, render_readme, write_dashboard_json


def run_profile_pipeline_with_collected(
    collected: CollectedProfileData,
    logger=print,
    *,
    allow_network_calls: bool = True,
) -> dict:
    ensure_output_dirs()
    model = compute_profile_model(
        collected,
        logger=logger,
        allow_network_calls=allow_network_calls,
    )
    generate_assets(collected, model, logger=logger)
    write_dashboard_json(model, logger=logger)
    render_readme(model, logger=logger)
    return {
        "collected": collected,
        "model": model,
    }


def run_profile_pipeline(logger=print) -> dict:
    collected = collect_profile_data(logger=logger)
    return run_profile_pipeline_with_collected(
        collected,
        logger=logger,
        allow_network_calls=True,
    )


def run_profile_pipeline_from_fixture(fixture_path: str, logger=print) -> dict:
    payload = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    collected = CollectedProfileData(**payload)
    return run_profile_pipeline_with_collected(
        collected,
        logger=logger,
        allow_network_calls=False,
    )

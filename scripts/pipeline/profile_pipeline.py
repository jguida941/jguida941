"""Run the profile build pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.contracts import (
    FIXTURE_SOURCE_KIND,
    LIVE_SOURCE_KIND,
    ProfileGenerationIdentityError,
    build_generation_identity,
    canonical_digest,
    dirty_generator_source_paths,
)
from scripts.contracts import publication as _publication
from scripts.pipeline.collect_data import collect_profile_data
from scripts.pipeline.collect_data import CollectedProfileData
from scripts.pipeline.compute_metrics import admit_repository_population, compute_profile_model
from scripts.pipeline.render_outputs import (
    _public_dashboard_data,
    ensure_output_dirs,
    generate_assets,
    render_readme,
    write_artifact_manifest,
    write_dashboard_json,
)


PublicationSubject = _publication.PublicationSubject
PublicationDecision = _publication.PublicationDecision


def evaluate_profile_publication(subject: PublicationSubject) -> PublicationDecision:
    return _publication.evaluate_profile_publication(subject)


def candidate_publication_subject(
    model: dict,
    *,
    source_kind: str,
) -> PublicationSubject:
    return _publication.candidate_publication_subject(model, source_kind=source_kind)


def stored_publication_subject(
    manifest: dict,
    snapshot: dict,
    *,
    artifact_errors: tuple[str, ...] = (),
) -> PublicationSubject:
    return _publication.stored_publication_subject(
        manifest, snapshot, artifact_errors=artifact_errors
    )


def _unqualified_partial_metrics(statuses: dict, scopes: dict) -> tuple[str, ...]:
    return _publication._unqualified_partial_metrics(statuses, scopes)


def _decision_allows_canonical_writes(decision: object) -> bool:
    for attribute in (
        "allows_canonical_publication",
        "allows_canonical_writes",
        "allows_effects",
        "ready",
        "publish",
        "allowed",
    ):
        value = getattr(decision, attribute, None)
        if isinstance(value, bool):
            return value
    return bool(decision)


def _decision_writes_local_artifacts(decision: object) -> bool:
    value = getattr(decision, "writes_local_artifacts", None)
    if isinstance(value, bool):
        return value
    return _decision_allows_canonical_writes(decision)


def refuse_dirty_generator_source() -> None:
    """A live artifact set may only be produced from committed generator bytes.

    Uncommitted source, an unstaged edit, or an untracked module under a generator
    input root cannot be identified by a recorded revision, so live generation
    stops before any output is written. Generated outputs are not generator source
    and are outside this census.
    """
    dirty = dirty_generator_source_paths()
    if dirty:
        raise ProfileGenerationIdentityError(
            "live profile generation requires clean generator inputs; uncommitted: "
            + ", ".join(sorted(dirty))
        )


def run_profile_pipeline_with_collected(
    collected: CollectedProfileData,
    logger=print,
    *,
    allow_network_calls: bool = True,
    source_kind: str | None = None,
) -> dict:
    """Compute one profile model and, when the decision allows it, write payloads.

    Live origin is the default, so it is also the default obligation: every run
    that is not an explicitly declared ``fixture`` run takes the generator-source
    census first — before admission, the model, the generation identity, and every
    writer. An omitted or ``None`` origin is a live run, not an exemption, so no
    caller can reach a writer with a live claim while generator input is dirty.
    Only an explicit ``fixture`` declaration opts out, because that output is
    local and never publishable.
    """
    if source_kind != FIXTURE_SOURCE_KIND:
        refuse_dirty_generator_source()
    bound_source_kind = source_kind or LIVE_SOURCE_KIND
    admit_repository_population(collected)
    model = compute_profile_model(
        collected,
        logger=logger,
        allow_network_calls=allow_network_calls,
    )
    generation = build_generation_identity(
        source_kind=bound_source_kind,
        generated_at=str(model["dashboard_data"].get("generated_at", "")),
        claim_input_digest=canonical_digest(_public_dashboard_data(model["dashboard_data"])),
    )
    decision = evaluate_profile_publication(
        candidate_publication_subject(model, source_kind=bound_source_kind)
    )
    artifact_set_written = _decision_writes_local_artifacts(decision)
    if artifact_set_written:
        ensure_output_dirs()
        generate_assets(collected, model, logger=logger, generation=generation)
        write_dashboard_json(model, logger=logger, generation=generation)
        render_readme(model, logger=logger, generation=generation)
    else:
        logger(f"  Canonical profile artifacts retained: {getattr(decision, 'state', decision)}")
    return {
        "collected": collected,
        "model": model,
        "generation": generation,
        "publication_decision": decision,
        "decision": decision,
        "artifact_set_written": artifact_set_written,
    }


def _seal_artifact_set(result: dict, logger=print) -> dict:
    """Close a complete generation by sealing the payloads it actually wrote."""
    if result.get("artifact_set_written"):
        write_artifact_manifest(result["generation"], logger=logger)
    return result


def run_profile_pipeline(logger=print) -> dict:
    # The census also runs here so a dirty source never triggers provider
    # collection; the shared writer re-asserts it for every live-origin path.
    refuse_dirty_generator_source()
    collected = collect_profile_data(logger=logger)
    result = run_profile_pipeline_with_collected(
        collected,
        logger=logger,
        allow_network_calls=True,
        source_kind=LIVE_SOURCE_KIND,
    )
    return _seal_artifact_set(result, logger=logger)


def run_profile_pipeline_from_fixture(fixture_path: str, logger=print) -> dict:
    payload = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    collected = CollectedProfileData(**payload)
    # The fixture front door declares its own origin; no caller may override it
    # into a live claim, and it never inherits one.
    result = run_profile_pipeline_with_collected(
        collected,
        logger=logger,
        allow_network_calls=False,
        source_kind=FIXTURE_SOURCE_KIND,
    )
    return _seal_artifact_set(result, logger=logger)

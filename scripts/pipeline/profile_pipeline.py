"""Run the profile build pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from scripts.contracts import (
    FIXTURE_SOURCE_KIND,
    LIVE_SOURCE_KIND,
    PUBLICATION_HOLD_PRECEDENCE,
    ProfileGenerationIdentityError,
    build_generation_identity,
    canonical_digest,
    dirty_generator_source_paths,
)
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


@dataclass(frozen=True)
class PublicationSubject:
    """The facts one publication decision is made from.

    A subject is either the candidate this run just computed or a stored artifact
    set recomputed from its own manifest and payloads. Nothing else may reach the
    evaluator, so a held candidate can never mark a stored set unpublishable and a
    stored set can never license unwritten candidate bytes.
    """

    subject: str
    source_kind: str
    private_inventory_status: str
    contribution_currentness: str
    metric_family_statuses: tuple[tuple[str, str], ...] = ()
    unqualified_partial_consumers: tuple[str, ...] = ()
    provider_hold_reasons: tuple[str, ...] = ()
    artifact_errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class PublicationDecision:
    state: str
    reasons: tuple[str, ...] = ()
    subject: str = "candidate_generation"
    errors: tuple[str, ...] = ()

    @property
    def allows_canonical_publication(self) -> bool:
        """Only a READY set may be uploaded, auto-committed, or deployed."""
        return self.state == "READY"

    @property
    def writes_local_artifacts(self) -> bool:
        """Fixture output stays locally inspectable; every other hold retains bytes.

        A nonlive run is barred from canonical publication but is a legitimate
        local development surface, so it still writes its own output root. A live
        hold or an invalid set writes nothing, which is what preserves the last
        accepted canonical artifacts.
        """
        return self.state in {"READY", "HOLD_NONLIVE_SOURCE"}

    @property
    def allows_canonical_writes(self) -> bool:
        return self.allows_canonical_publication

    @property
    def ready(self) -> bool:
        return self.allows_canonical_publication

    def __bool__(self) -> bool:
        return self.allows_canonical_publication

    def describe(self) -> str:
        reasons = ", ".join(self.reasons) if self.reasons else "none"
        return f"{self.state} (subject: {self.subject}; reasons: {reasons})"


def evaluate_profile_publication(subject: PublicationSubject) -> PublicationDecision:
    """The one publication decision, applied to one explicitly bound subject.

    Readiness is evidence, never a repository count: an exact zero population is
    as publishable as a large one, and a positive public count proves nothing
    about the private population.
    """
    if subject.artifact_errors:
        return PublicationDecision(
            state="ERROR_INVALID_ARTIFACT_SET",
            reasons=("INVALID_ARTIFACT_SET",),
            subject=subject.subject,
            errors=tuple(subject.artifact_errors),
        )

    family_statuses = dict(subject.metric_family_statuses)
    if subject.private_inventory_status == "exact":
        contradictions = tuple(
            metric
            for metric, status in sorted(family_statuses.items())
            if status == "unavailable"
        )
        if contradictions:
            return PublicationDecision(
                state="ERROR_INVALID_ARTIFACT_SET",
                reasons=("CONTRADICTORY_METRIC_COMPLETENESS",),
                subject=subject.subject,
                errors=tuple(
                    f"{metric} is unavailable while the repository inventory is exact"
                    for metric in contradictions
                ),
            )

    if subject.unqualified_partial_consumers:
        return PublicationDecision(
            state="ERROR_INVALID_ARTIFACT_SET",
            reasons=("UNQUALIFIED_PARTIAL_METRIC",),
            subject=subject.subject,
            errors=tuple(
                f"{metric} is partial but reaches a consumer without that qualification"
                for metric in subject.unqualified_partial_consumers
            ),
        )

    reasons: list[str] = []
    if subject.source_kind != "github-api":
        reasons.append("NONLIVE_SOURCE")
    if subject.private_inventory_status != "exact":
        reasons.append("INCOMPLETE_PRIVATE_EVIDENCE")
    if subject.contribution_currentness != "current":
        reasons.append("NONCURRENT_CONTRIBUTIONS")
    if not reasons:
        return PublicationDecision(state="READY", subject=subject.subject)

    # Every reason is retained; only the displayed state follows the precedence.
    state = next(
        hold for hold in PUBLICATION_HOLD_PRECEDENCE if hold.removeprefix("HOLD_") in reasons
    )
    return PublicationDecision(state=state, reasons=tuple(reasons), subject=subject.subject)


def candidate_publication_subject(
    model: dict,
    *,
    source_kind: str,
) -> PublicationSubject:
    """Bind the just-computed candidate facts, including provider hold reasons."""
    data_quality = model.get("data_quality") or {}
    data_scope = model.get("data_scope") or {}
    statuses = data_quality.get("metric_statuses") or {}
    scopes = data_scope.get("metric_scopes") or {}
    provider_hold_reasons = tuple(
        model.get("publication_hold_reasons")
        or data_quality.get("publication_hold_reasons")
        or ()
    )
    return PublicationSubject(
        subject="candidate_generation",
        source_kind=source_kind,
        private_inventory_status=str(data_quality.get("private_aggregate_status", "unavailable")),
        contribution_currentness=(
            "noncurrent" if "NONCURRENT_CONTRIBUTIONS" in provider_hold_reasons else "current"
        ),
        metric_family_statuses=tuple(sorted((str(k), str(v)) for k, v in statuses.items())),
        unqualified_partial_consumers=_unqualified_partial_metrics(statuses, scopes),
        provider_hold_reasons=provider_hold_reasons,
    )


def stored_publication_subject(
    manifest: dict,
    snapshot: dict,
    *,
    artifact_errors: tuple[str, ...] = (),
) -> PublicationSubject:
    """Bind the stored artifact set's own recorded facts. No provider is queried."""
    data_quality = snapshot.get("data_quality") or {} if isinstance(snapshot, dict) else {}
    data_scope = snapshot.get("data_scope") or {} if isinstance(snapshot, dict) else {}
    statuses = data_quality.get("metric_statuses") or {}
    scopes = data_scope.get("metric_scopes") or {}
    provider_hold_reasons = tuple(data_quality.get("publication_hold_reasons") or ())
    return PublicationSubject(
        subject="stored_artifact_set",
        source_kind=str((manifest or {}).get("source_kind", "")),
        private_inventory_status=str(data_quality.get("private_aggregate_status", "unavailable")),
        contribution_currentness=(
            "noncurrent" if "NONCURRENT_CONTRIBUTIONS" in provider_hold_reasons else "current"
        ),
        metric_family_statuses=tuple(sorted((str(k), str(v)) for k, v in statuses.items())),
        unqualified_partial_consumers=_unqualified_partial_metrics(statuses, scopes),
        provider_hold_reasons=provider_hold_reasons,
        artifact_errors=tuple(artifact_errors),
    )


def _unqualified_partial_metrics(statuses: dict, scopes: dict) -> tuple[str, ...]:
    """Partial values are publishable only where the scope says they are partial."""
    return tuple(
        metric
        for metric, status in sorted(statuses.items())
        if status == "partial" and "partial" not in str(scopes.get(metric, "")).casefold()
    )


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

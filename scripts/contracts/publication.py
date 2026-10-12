"""Publication subjects and decisions for candidate and stored artifacts."""

from __future__ import annotations

from dataclasses import dataclass

from scripts.contracts import PUBLICATION_HOLD_PRECEDENCE


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


# Preserve serialized class references through the pipeline's compatibility aliases.
PublicationSubject.__module__ = "scripts.pipeline.profile_pipeline"
PublicationDecision.__module__ = "scripts.pipeline.profile_pipeline"

"""Resolve one profile invariant to admissible evidence authority."""
from __future__ import annotations

from .catalog import load_catalog


GAP_KEYS = {"reason", "required_resolution"}


def _gap(reason: str, required_resolution: str) -> dict:
    return {
        "status": "gap",
        "pass_eligible": False,
        "candidate_reason": "provenance-unresolved",
        "reason": reason,
        "required_resolution": required_resolution,
    }


def resolve_invariant(profile: str, invariant: dict, *, catalog: dict[str, dict] | None = None) -> dict:
    """Return a scoped resolution; malformed/missing bindings fail closed as a gap."""
    has_clause = "clause_id" in invariant
    has_gap = "provenance_gap" in invariant
    if has_clause == has_gap:
        return _gap("invariant must name exactly one clause or provenance gap", "repair-binding")
    if has_gap:
        gap = invariant["provenance_gap"]
        if not isinstance(gap, dict) or set(gap) != GAP_KEYS \
                or not all(isinstance(gap.get(key), str) and gap[key] for key in GAP_KEYS):
            return _gap("malformed provenance gap", "repair-binding")
        return _gap(gap["reason"], gap["required_resolution"])
    clauses = catalog if catalog is not None else load_catalog()
    clause = clauses.get(invariant["clause_id"])
    if clause is None:
        return _gap("unknown design-source clause", "repair-binding")
    scope = clause["scope"]
    if profile not in scope["profiles"] or invariant.get("aspect") not in scope["aspects"] \
            or invariant.get("invariant_id") not in scope["invariant_ids"]:
        return _gap("design-source clause is out of scope", "repair-binding")
    return {
        "status": "resolved",
        "pass_eligible": clause["exactness"] != "perceptual",
        "clause_id": clause["clause_id"],
        "authority": clause["authority"],
        "source_mode": clause["source_mode"],
        "exactness": clause["exactness"],
        "sources": clause["sources"],
    }


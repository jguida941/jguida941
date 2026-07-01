"""The INVARIANT seam — `conform(profile) -> [InvariantResult]`. Walks a profile's `invariants[]`;
an EMITTED + DETERMINISTIC row renders its component, gathers verdict-free facts via the adapter,
and dispatches its `predicate_class` into the closed predicate library to DECIDE pass/fail. A
JUDGMENT / DEFERRED row becomes `candidate` (a review-anchor + visual-receipt obligation) — never a
fabricated pass. `write_receipt` serializes the results to `assets/receipts/<lang>/` (governed by
receipts_layout). The runner mints NO authority beyond the pytest verdict + the receipt (there is no
kernel here); every result is `candidate_only`. Portable: surface + profile are the only inputs.
"""
from __future__ import annotations

import json
from pathlib import Path


def _root() -> Path:
    for p in Path(__file__).resolve().parents:
        if (p / "contracts" / "design_profiles").is_dir():
            return p
    raise RuntimeError("repo root not found")


def _button_facts(profile: str, variant: str) -> dict:
    from scripts.rendering.webkit import design_render_adapter as adapter
    from scripts.rendering.webkit.components import render_button
    _, base_css = render_button(profile, variant, "rest")   # rest = the base rule (material/radius source)
    _, active = render_button(profile, variant, "active")
    html, focus = render_button(profile, variant, "focus-visible")
    # base rule sourced explicitly from `rest`; the `.is-*` recipes come from the state renders
    return adapter.button_facts(html, "\n".join([base_css, active, focus]))


def _chip_facts(profile: str, variant: str) -> dict:
    from scripts.rendering.webkit import design_render_adapter as adapter
    from scripts.rendering.webkit.components import render_chip
    _, base_css = render_chip(profile, variant, "rest")
    _, active = render_chip(profile, variant, "active")
    html, focus = render_chip(profile, variant, "focus-visible")
    return adapter.chip_facts(html, "\n".join([base_css, active, focus]))


# aspect -> (component key in profile["components"], the fact-gatherer). Adding a component = one row.
_COMPONENT_FACTS = {
    "component-button": ("button", _button_facts),
    "component-chip": ("chip", _chip_facts),
}


# The receipt claim is HONEST per status (codex 1b-ii #4): a `fail`/`candidate` row must not read
# "satisfies". Pass = satisfies; fail = VIOLATES; candidate = judgment/deferred, needs a receipt.
_CLAIM = {
    "pass": "satisfies '{aspect}' of the {profile} profile v1 — receipt",
    "fail": "VIOLATES '{aspect}' of the {profile} profile v1 — receipt",
    "candidate": "'{aspect}' of the {profile} profile v1 is a candidate (judgment/deferred) — needs a visual/probe receipt",
}


def _result(inv: dict, profile: str, status: str, evidence: dict) -> dict:
    aspect = inv.get("aspect")
    return {
        "invariant_id": inv.get("invariant_id"),
        "profile": profile,
        "aspect": aspect,
        "determinism": inv.get("determinism"),
        "status": status,                       # pass | fail | candidate (axe/ACT lineage)
        "law": inv.get("law"),
        "doc_cite": inv.get("doc_cite"),
        "evidence": evidence,
        "authority_status": "candidate_only",
        "cannot_mark_done": True,
        "claim": _CLAIM[status].format(aspect=aspect, profile=profile),
    }


def conform(profile: str) -> list[dict]:
    from scripts.contracts import design_predicates as predicates
    from scripts.rendering.design import loader

    prof = loader.load(profile)
    results: list[dict] = []
    facts_cache: dict = {}
    for inv in prof.get("invariants", []):
        emitted = inv.get("emission_status") == "emitted" and inv.get("determinism") == "deterministic"
        if not emitted:
            # judgment / deferred -> candidate (review anchor + visual receipt), never a fake pass
            results.append(_result(inv, profile, "candidate", {}))
            continue
        pred = inv.get("predicate", {})
        fn = predicates.PREDICATES.get(pred.get("predicate_class"))
        params = dict(pred.get("params", {}))
        component = _COMPONENT_FACTS.get(inv.get("aspect"))
        if component is not None:
            key, gather = component
            variant = params.pop("variant", prof["components"][key]["variants"][0])
            cache_key = (key, variant)
            if cache_key not in facts_cache:       # gather ONCE per (component, variant), not eagerly
                facts_cache[cache_key] = gather(profile, variant)
            facts = facts_cache[cache_key]
        else:
            facts = {}
        ok = bool(fn(facts, **params)) if fn else False
        results.append(_result(inv, profile, "pass" if ok else "fail", facts))
    return results


def receipt_json(profile: str) -> str:
    """PURE: the serialized conformance receipt for a profile (no disk write). The drift guard
    compares the committed bytes against THIS, so it never mutates the committed fixture (codex
    1c #1)."""
    payload = {"profile": profile, "profile_version": 1, "authority_status": "candidate_only",
               "results": conform(profile)}
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def write_receipt(profile: str) -> Path:
    """Serialize conform(profile) to assets/receipts/<profile>/conformance_receipt.json (the
    RECEIPT seam) — the artifact the showcase + settings read to stamp each cell."""
    out = _root() / "assets" / "receipts" / profile / "conformance_receipt.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(receipt_json(profile), encoding="utf-8")
    return out

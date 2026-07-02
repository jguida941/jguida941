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


def _button_facts(profile: str, variant: str, profile_data: dict | None = None) -> dict:
    from scripts.rendering.webkit import design_render_adapter as adapter
    from scripts.rendering.webkit.components import render_button
    _, base_css = render_button(profile, variant, "rest", profile_data=profile_data)   # rest = the base rule
    _, active = render_button(profile, variant, "active", profile_data=profile_data)
    html, focus = render_button(profile, variant, "focus-visible", profile_data=profile_data)
    # base rule sourced explicitly from `rest`; the `.is-*` recipes come from the state renders
    return adapter.button_facts(html, "\n".join([base_css, active, focus]))


def _chip_facts(profile: str, variant: str, profile_data: dict | None = None) -> dict:
    from scripts.rendering.webkit import design_render_adapter as adapter
    from scripts.rendering.webkit.components import render_chip
    _, base_css = render_chip(profile, variant, "rest", profile_data=profile_data)
    _, active = render_chip(profile, variant, "active", profile_data=profile_data)
    html, focus = render_chip(profile, variant, "focus-visible", profile_data=profile_data)
    return adapter.chip_facts(html, "\n".join([base_css, active, focus]))


def _card_facts(profile: str, variant: str, profile_data: dict | None = None) -> dict:
    from scripts.rendering.webkit import design_render_adapter as adapter
    from scripts.rendering.webkit.components import render_card
    html, css = render_card(profile, variant, "rest", profile_data=profile_data)   # a card is static
    return adapter.card_facts(html, css)


def _pageshell_facts(profile: str, variant: str | None = None, profile_data: dict | None = None) -> dict:
    """Gather facts for the page CHROME (P5-CHROME). Unlike a component, the page-shell has no per-
    variant block in profile["components"] — the whole shell IS the specimen — so `variant` is ignored
    and the canonical shell is rendered."""
    from scripts.rendering.pageshell.pageshell import render_page_shell
    from scripts.rendering.webkit import design_render_adapter as adapter
    html, css = render_page_shell(
        profile,
        title="Design-language surface",
        intro="Every part of this page follows the design-language process.",
        breadcrumbs=[("home", "index.html")],
        sections=[],
        profile_data=profile_data,
    )
    facts = adapter.pageshell_facts(html, css)
    # D-SHELL layout fact: the shell's panel padding equals the LANGUAGE'S declared density band
    # (design_tokens.THEME_IA density.panel_pad — cited per language) — provenance, not taste.
    from scripts.rendering import design_tokens as dt
    facts["pad_matches_density_band"] = (facts.get("pad_px") == float(dt.density(profile)["panel_pad"]))
    return facts


# aspect -> (component key in profile["components"], the fact-gatherer). Adding a component = one row.
# `page-shell` is an ASPECT with a fact-gatherer but NOT a component (no components[] block, not in the
# distinctness signature) — the whole page is the rendered instance.
_COMPONENT_FACTS = {
    "component-button": ("button", _button_facts),
    "component-chip": ("chip", _chip_facts),
    "component-card": ("card", _card_facts),
    "page-shell": ("page-shell", _pageshell_facts),
    "page-layout": ("page-layout", _pageshell_facts),
}


def _material_axis(facts: dict) -> str | None:
    if facts.get("has_backdrop_filter") is True:
        return "liquid-glass"
    if facts.get("has_backdrop_filter") is False:
        return "non-glass"
    return None


def _elevation_axis(facts: dict) -> str | None:
    if facts.get("has_box_shadow") is True:
        return "floating"
    if facts.get("has_box_shadow") is False:
        return "none"
    return None


def fingerprint_from_facts(component: str, facts: dict) -> dict:
    """Render-derived fingerprint axes. These are observations, not profile self-reporting.

    `material` intentionally collapses `flat-fill` and `opaque-fill` to `non-glass`: the static
    facts seam can prove glass-vs-not-glass, while the Carbon-vs-Apple split is carried by rendered
    radius/anatomy/mechanic/focus axes.
    """
    if component in ("button", "chip"):
        return {
            "radius_px": facts.get("radius_px"),
            "state_mechanic": facts.get("state_mechanic"),
            "focus_recipe": facts.get("focus_recipe"),
            "anatomy": facts.get("anatomy"),
            "material": _material_axis(facts),
            "elevation": _elevation_axis(facts),
        }
    if component == "card":
        radius = facts.get("radius_px")
        return {
            "radius_px": radius,
            "material": _material_axis(facts),
            "divider": "visible-1px" if facts.get("divider_1px") is True else None,
            "shape": ("square" if radius == 0 else ("rounded" if isinstance(radius, int) and radius > 0 else None)),
            "elevation": _elevation_axis(facts),
        }
    raise KeyError(f"unknown component: {component}")


def rendered_component_fingerprint(
    profile: str,
    component: str,
    variant: str | None = None,
    profile_data: dict | None = None,
) -> dict:
    """Render a component, gather facts, and return its observed fingerprint.

    The optional `profile_data` path exists for mutation proofs and settings composition: changing
    only `components.<component>.fingerprint` must not change this value.
    """
    from scripts.rendering.design import loader

    prof = profile_data if profile_data is not None else loader.load(profile)
    if variant is None:
        variant = prof["components"][component]["variants"][0]
    gather = _COMPONENT_FACTS[f"component-{component}"][1]
    return fingerprint_from_facts(component, gather(profile, variant, profile_data=profile_data))


def _material_matches(declared: str | None, rendered: str | None) -> bool:
    if declared == "liquid-glass":
        return rendered == "liquid-glass"
    if declared in ("flat-fill", "opaque-fill"):
        return rendered == "non-glass"
    return declared == rendered


def _divider_matches(declared: str | None, rendered: str | None) -> bool:
    if declared in ("hairline", "gridline"):
        return rendered == "visible-1px"
    return declared == rendered


def fingerprint_matches_rendered(declared: dict, rendered: dict, component: str) -> bool:
    """True iff a declared fingerprint is consistent with the rendered fingerprint on every
    facts-observable axis. Declared fingerprints document the design language; rendered facts decide.
    """
    for key in ("radius_px",):
        if declared.get(key) != rendered.get(key):
            return False
    if not _material_matches(declared.get("material"), rendered.get("material")):
        return False
    if component in ("button", "chip"):
        for key in ("state_mechanic", "focus_recipe", "anatomy", "elevation"):
            if declared.get(key) != rendered.get(key):
                return False
        return True
    if component == "card":
        if declared.get("shape") != rendered.get("shape"):
            return False
        if not _divider_matches(declared.get("divider"), rendered.get("divider")):
            return False
        return True
    raise KeyError(f"unknown component: {component}")


def fingerprint_matches_facts(declared: dict, facts: dict, component: str) -> bool:
    return fingerprint_matches_rendered(declared, fingerprint_from_facts(component, facts), component)


# The receipt claim is HONEST per status (codex 1b-ii #4): a `fail`/`candidate` row must not read
# "satisfies". Pass = satisfies; fail = VIOLATES; candidate = judgment/deferred, needs a receipt.
_CLAIM = {
    "pass": "satisfies '{aspect}' of the {profile} profile v1 — receipt",
    "fail": "VIOLATES '{aspect}' of the {profile} profile v1 — receipt",
    "candidate": "'{aspect}' of the {profile} profile v1 is a candidate (judgment/deferred) — needs a visual/probe receipt",
}


def _receipt_status(obligation: dict | None) -> str | None:
    if not obligation or not obligation.get("required"):
        return None
    artifact = obligation.get("artifact")
    if not artifact:
        return "pending"
    return "present" if (_root() / artifact).is_file() else "pending"


def _result(inv: dict, profile: str, status: str, evidence: dict) -> dict:
    aspect = inv.get("aspect")
    obligation = inv.get("receipt_obligation")
    receipt_status = _receipt_status(obligation)
    payload = {
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
    if inv.get("defer_reason"):
        payload["defer_reason"] = inv["defer_reason"]
    if inv.get("refute_by"):
        payload["refute_by"] = inv["refute_by"]
    if obligation:
        payload["receipt_obligation"] = obligation
    if receipt_status:
        payload["receipt_status"] = receipt_status
        payload["evidence"] = {
            **payload["evidence"],
            "receipt_status": receipt_status,
            "receipt_artifact": obligation.get("artifact"),
            "receipt_kind": obligation.get("kind"),
        }
    return payload


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
            comp = prof["components"].get(key)   # page-shell has no components[] block -> variant None
            variant = params.pop("variant", comp["variants"][0] if comp else None)
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

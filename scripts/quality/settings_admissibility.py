"""P5-SETTINGS — the governed control plane as ONE Python decision source (no second JS decider;
`site/settings.html` only DISPLAYS what this module decides).

A Customization picks a BASE design language + per-component OVERRIDES; `compose()` builds the
composed profile; `is_admissible()` ACCEPTS a composition only if every overridden component, AS
RENDERED, is a FULL valid instance of at least one active design language. A partial property mix
that is a valid instance of NONE (e.g. liquid-glass frosted material + Carbon's square 0-radius) is
UNCONSTRUCTABLE — the design twin of the bootstrap-RED gate. The verdict routes through the REAL
render -> fact-gather -> predicate path (`conform`'s machinery), so a degenerate/empty render fails
closed (the reason the anatomy gatherer had to be hardened first). candidate_only; the authority is
the local pytest contract + the visual receipt, never this module minting a verdict of its own.
"""
from __future__ import annotations

import copy

_COMPONENTS = ("button", "chip", "card")


def active_profiles() -> list[str]:
    from scripts.rendering.design import loader
    return loader.load("_index")["active_design_profiles"]


def compose(base: str, overrides: dict) -> dict:
    """The composed profile = the base profile with per-component `overrides` applied. `overrides`
    is {component: {property: value}} — a WHOLESALE swap sets a component to another language's whole
    spec; a PARTIAL mix sets only some properties (exactly what the gate rejects)."""
    from scripts.rendering.design import loader
    prof = copy.deepcopy(loader.load(base))
    for comp, props in overrides.items():
        prof.setdefault("components", {}).setdefault(comp, {}).update(props)
    return prof


def _composed_facts(base: str, composed: dict, component: str) -> dict:
    """Render the composed component (injected composed profile + the base's tokens) and gather the
    verdict-free facts — the same render/adapter path `conform` uses."""
    from scripts.rendering.webkit import components as C
    from scripts.rendering.webkit import design_render_adapter as adapter
    variant = composed["components"][component]["variants"][0]
    if component == "button":
        html, base_css = C.render_button(base, variant, "rest", profile_data=composed)
        _, active = C.render_button(base, variant, "active", profile_data=composed)
        _, focus = C.render_button(base, variant, "focus-visible", profile_data=composed)
        return adapter.button_facts(html, "\n".join([base_css, active, focus]))
    if component == "chip":
        html, base_css = C.render_chip(base, variant, "rest", profile_data=composed)
        _, active = C.render_chip(base, variant, "active", profile_data=composed)
        _, focus = C.render_chip(base, variant, "focus-visible", profile_data=composed)
        return adapter.chip_facts(html, "\n".join([base_css, active, focus]))
    html, css = C.render_card(base, variant, "rest", profile_data=composed)
    return adapter.card_facts(html, css)


def _facts_match_fingerprint(facts: dict, fp: dict, component: str) -> bool:
    """The composed component's RENDERED facts must be consistent with `fp` (the candidate profile's
    declared fingerprint) on every facts-observable axis. This closes the uncovered-axis hole (codex
    settings #5): an override on an axis NOT covered by an emitted invariant — e.g. anatomy on a
    profile that declares no anatomy invariant — still cannot slip, because the rendered anatomy must
    match the fingerprint of the language it claims to be."""
    if facts.get("radius_px") != fp.get("radius_px"):
        return False
    if facts.get("has_backdrop_filter") is not (fp.get("material") == "liquid-glass"):
        return False
    if component in ("button", "chip"):
        if facts.get("anatomy") != fp.get("anatomy"):
            return False
        if facts.get("state_mechanic") != fp.get("state_mechanic"):
            return False
        if facts.get("focus_recipe") != fp.get("focus_recipe"):
            return False
        if facts.get("has_box_shadow") is not (fp.get("elevation") == "floating"):
            return False
    return True


def _satisfies_all(facts: dict, profile_name: str, component: str) -> bool:
    """True iff `facts` satisfies EVERY emitted deterministic invariant of `profile_name` for this
    component AND is fingerprint-consistent with it — i.e. the composed component IS a full valid
    instance of that design language, on every axis (not only the invariant-covered ones)."""
    from scripts.contracts.design_predicates import PREDICATES
    from scripts.rendering.design import loader
    comp = loader.load(profile_name).get("components", {}).get(component, {})
    aspect = f"component-{component}"
    invs = [inv for inv in loader.load(profile_name).get("invariants", [])
            if inv.get("aspect") == aspect and inv.get("emission_status") == "emitted"
            and inv.get("determinism") == "deterministic"]
    if not invs:
        return False
    for inv in invs:
        fn = PREDICATES.get(inv["predicate"]["predicate_class"])
        params = {k: v for k, v in inv["predicate"].get("params", {}).items() if k != "variant"}
        if fn is None or not fn(facts, **params):
            return False
    return _facts_match_fingerprint(facts, comp.get("fingerprint", {}), component)


def matching_languages(base: str, overrides: dict, component: str) -> list[str]:
    """Which active design languages the composed `component` is a full valid instance of."""
    composed = compose(base, overrides)
    facts = _composed_facts(base, composed, component)
    return [p for p in active_profiles() if _satisfies_all(facts, p, component)]


def is_admissible(base: str, overrides: dict) -> bool:
    """ADMISSIBLE iff every OVERRIDDEN component, as rendered, is a full valid instance of at least
    one active design language. A Frankenstein (instance of NONE) is inadmissible -> unconstructable."""
    return all(matching_languages(base, overrides, component) for component in overrides)


def admissible_space() -> list[dict]:
    """The PRE-BAKED admissible combo space (ONE source): every base × per-component WHOLESALE swap
    to another active language, with admissibility COMPUTED (not asserted). The settings UI offers
    only the admissible cells; an out-of-space partial mix is rejected by `is_admissible`."""
    from scripts.rendering.design import loader
    actives = active_profiles()
    space = []
    for base in actives:
        for component in _COMPONENTS:
            for source in actives:
                spec = copy.deepcopy(loader.load(source)["components"][component])
                space.append({
                    "base": base, "component": component, "source": source,
                    "admissible": is_admissible(base, {component: spec}),
                })
    return space

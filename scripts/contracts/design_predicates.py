"""The closed design-predicate library — pure `(facts, **params) -> bool`. Each DECIDES from
verdict-free facts (gathered by `design_render_adapter`); it renders nothing and reads no disk.
This is the portable half (lifts to scout). Deterministic predicates only — a judgment aspect
(contrast over glass, motion feel) is declared `deferred`/candidate in the profile and never
compiles a passing body here. candidate_only.
"""
from __future__ import annotations


def button_radius(facts: dict, expected_px: int, **_) -> bool:
    return facts.get("radius_px") == expected_px


def button_anatomy(facts: dict, expected: str, **_) -> bool:
    return facts.get("anatomy") == expected


def button_state_mechanic(facts: dict, expected: str, **_) -> bool:
    """The profile's ONE signature press mechanic, mutually-exclusive: the adapter resolves exactly
    one of glass-brightness / opacity-dim / token-swap, so `== expected` also excludes the others."""
    return facts.get("state_mechanic") == expected


def button_material_glass(facts: dict, **_) -> bool:
    return facts.get("has_backdrop_filter") is True


def button_material_opaque(facts: dict, **_) -> bool:
    return facts.get("has_backdrop_filter") is False


def button_zero_elevation(facts: dict, **_) -> bool:
    return facts.get("has_box_shadow") is False


def button_focus_recipe(facts: dict, expected: str, **_) -> bool:
    return facts.get("focus_recipe") == expected


def chip_sentence_case(facts: dict, **_) -> bool:
    """The chip's cited typography rule (Apple + Carbon both sentence case, never ALL-CAPS): the
    render emits NO `text-transform: uppercase`. Deterministic character predicate (fail-closed:
    `typography_case` is None on unparseable CSS -> False)."""
    return facts.get("typography_case") == "sentence"


def material_flat(facts: dict, **_) -> bool:
    """Carbon-flat: proves the FULL 'flat' law (codex chip #4) — NO frosted blur AND NO elevation
    shadow (a blurred-but-shadowless chip would pass `zero_elevation` alone)."""
    return facts.get("has_backdrop_filter") is False and facts.get("has_box_shadow") is False


# The closed registry the conform() runner dispatches into. `predicate_class` in a profile's
# invariants[] must resolve here (test_design_conformance enforces it). The button_* predicates are
# GENERIC over facts (radius/anatomy/material/mechanic/elevation/focus); a second component (the
# chip) REUSES them via the component-neutral aliases below + adds only its NEW predicate
# (chip_sentence_case) — the skill's "a component is DATA + a render branch + only-new predicates".
PREDICATES = {
    "button_radius": button_radius,
    "button_anatomy": button_anatomy,
    "button_state_mechanic": button_state_mechanic,
    "button_material_glass": button_material_glass,
    "button_material_opaque": button_material_opaque,
    "button_zero_elevation": button_zero_elevation,
    "button_focus_recipe": button_focus_recipe,
    # component-neutral aliases (same generic predicates; used by the chip and later components)
    "radius": button_radius,
    "anatomy": button_anatomy,
    "state_mechanic": button_state_mechanic,
    "material_glass": button_material_glass,
    "material_opaque": button_material_opaque,
    "zero_elevation": button_zero_elevation,
    "focus_recipe": button_focus_recipe,
    "material_flat": material_flat,
    # chip-only
    "chip_sentence_case": chip_sentence_case,
}

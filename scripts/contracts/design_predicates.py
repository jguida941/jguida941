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


# The closed registry the conform() runner dispatches into. `predicate_class` in a profile's
# invariants[] must resolve here (test_design_conformance enforces it).
PREDICATES = {
    "button_radius": button_radius,
    "button_anatomy": button_anatomy,
    "button_state_mechanic": button_state_mechanic,
    "button_material_glass": button_material_glass,
    "button_material_opaque": button_material_opaque,
    "button_zero_elevation": button_zero_elevation,
    "button_focus_recipe": button_focus_recipe,
}

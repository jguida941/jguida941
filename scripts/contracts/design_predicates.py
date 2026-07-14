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


# --- card / grouped-metric PATTERN predicates (deterministic structural composition) --------------
def card_single_container(facts: dict, **_) -> bool:
    """The anti-'grid of chromed tiles' law: exactly ONE container element (codex card #1 — not two
    single-row groups) AND its rows carry NO independent background/radius. Fail-closed (both facts
    False on unparseable CSS). The DEEPER-REFRAME 'no giant box per stat' encoded structurally."""
    return facts.get("container_count") == 1 and facts.get("rows_chromeless") is True


def card_multi_row(facts: dict, min_rows: int = 2, **_) -> bool:
    """A metric card GROUPS >=min_rows related rows (anti 'one number per full-width card')."""
    return facts.get("row_count", 0) >= min_rows


def card_hairline_divided(facts: dict, **_) -> bool:
    """Adjacent rows divided by a <=1px hairline (a grouped list), NOT a 4-side box per stat."""
    return facts.get("divider_1px") is True


def card_rows_inline(facts: dict, **_) -> bool:
    """The row AXIS is horizontal (label + value inline), NOT stacked column. Scoped to the axis —
    it does NOT (and must not) claim the label+value visually render on one unwrapped line; that is
    a layout/judgment concern, gathered by a visual receipt."""
    return facts.get("rows_horizontal") is True


def switcher_profile_governed(facts: dict, **_) -> bool:
    """The segmented switcher covers one closed roster with full state and touch geometry."""
    html_profiles = facts.get("html_profiles")
    css_profiles = facts.get("css_profiles")
    profiles = facts.get("profiles")
    expected = facts.get("expected_profiles")
    if (not isinstance(html_profiles, tuple) or not html_profiles
            or html_profiles != css_profiles
            or facts.get("button_count") != len(html_profiles)
            or facts.get("pressed_count") != 1
            or facts.get("icon_count") != len(html_profiles)
            or not isinstance(profiles, dict) or set(profiles) != set(html_profiles)
            or not isinstance(expected, dict) or set(expected) != set(html_profiles)):
        return False
    if not all(facts.get(key) is True for key in ("has_rest", "has_pressed", "has_disabled")):
        return False
    return profiles == expected and all(row.get("height_px", 0) >= 44 for row in profiles.values())


# --- page-shell (the site's own chrome as a governed language instance) ---------------------------
def backdrop_is_token(facts: dict, **_) -> bool:
    """The page ground is the language's backdrop token: the shell root paints `var(--backdrop)`.
    Switching language switches the whole page's ground (fail-closed: False if absent)."""
    return facts.get("uses_backdrop_var") is True


def host_chrome_is_closed(facts: dict, **_) -> bool:
    """The chrome CSS is a CLOSED, simple structure: exactly ONE `.ps-<lang>` root rule + descendant
    rules of it only — no @-rules / attribute / pseudo selectors / combinators. This makes specificity
    conflicts, @media overrides, and attribute-selector spoofs UNCONSTRUCTABLE, so the token-only +
    backdrop checks reason over a clean structure (fail-closed on anything exotic)."""
    return facts.get("shell_closed") is True and facts.get("root_rule_count") == 1


def host_chrome_token_only(facts: dict, **_) -> bool:
    """The anti-vibe-code core: after the `:root` token blocks + legit `var(--…)` refs are removed, no
    declaration value carries a colour literal of ANY form (hex / rgb() / hsl() / color-mix() / named /
    currentColor) or a bare design px — every decision is a var(). A single hand-literal reddens."""
    return facts.get("body_offtoken_count") == 0


def section_grouping_flat(facts: dict, **_) -> bool:
    """D-SHELL-2 (gate MF-A): the SHELL composes ONE chrome level — no chromed box inside another
    chromed box (the audit's box-in-box). Fail-closed AND non-vacuous: an unbalanced parse (None)
    fails, and 'flat' is only claimable when >=1 chromed box actually rendered. SHELL-scoped; the
    page-level check (e.g. the showcase stage) lands with D-SHELL-3's recomposition."""
    depth = facts.get("chrome_nesting_depth")
    count = facts.get("chromed_box_count")
    return depth is not None and (count or 0) >= 1 and depth <= 1


def motion_tokens_cited(facts: dict, **_) -> bool:
    """P5-BOARD B-1 (motion.md §2/§3): the emitted motion vars trace to the language's declared
    block AND durations sit in the cited [70,700]ms band, ordered. Fail-closed."""
    return facts.get("motion_vars_provenance") is True and facts.get("motion_in_band") is True


def nav_anatomy(facts: dict, **_) -> bool:
    """P5-BOARD B-1b: the nav band renders a .site-nav container linking every surface with an
    aria-current active marker, token-only CSS. Fail-closed."""
    return all(facts.get(k) is True for k in
               ("nav_has_band", "nav_links_all", "nav_has_active", "nav_token_only"))


def page_has_orientation(facts: dict, **_) -> bool:
    """A user can tell what the page is + GET BACK: a title WITH text AND a real breadcrumb link (non-
    empty href + text) are present (fail-closed on an empty render / an empty crumbs row)."""
    return facts.get("has_title") is True and facts.get("has_breadcrumb_link") is True


def page_has_content_column(facts: dict, **_) -> bool:
    """D-SHELL (design-audit #1, the root cause): ALL page content sits in ONE centered column —
    `.ps-main` bound to the cited page measure (`var(--ps-measure-page)`, the index .wrap 980px
    precedent) and auto-centered. Full-bleed sprawl is unconstructable (fail-closed: False if the
    column rule or the wrapping div is absent)."""
    return facts.get("has_content_column") is True


def shell_type_ramp_tiered(facts: dict, **_) -> bool:
    """D-SHELL (design-audit #6): the shell ramp carries a real HEADING TIER — title > h2 > body
    as rendered :root values (HIG Title-1/Title-3/body). A flat ramp (body-sized section headers)
    reddens (fail-closed on any missing tier)."""
    return facts.get("type_ramp_tiered") is True


def shell_density_from_profile(facts: dict, **_) -> bool:
    """D-SHELL (design-audit #7): the shell's panel padding IS the language's own cited density
    band (apple-dark 'airy' 32 / carbon 'compact' 20 / liquid-glass 'medium' 28 — THEME_IA) — a
    minted constant that ignores the profile reddens (fail-closed: False if the pad var is absent)."""
    return facts.get("pad_matches_density_band") is True


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
    # card / grouped-metric pattern
    "card_single_container": card_single_container,
    "card_multi_row": card_multi_row,
    "card_hairline_divided": card_hairline_divided,
    "card_rows_inline": card_rows_inline,
    # page-shell / chrome (P5-CHROME) — the site's own frame as a governed language instance
    "backdrop_is_token": backdrop_is_token,
    "host_chrome_is_closed": host_chrome_is_closed,
    "host_chrome_token_only": host_chrome_token_only,
    "page_has_orientation": page_has_orientation,
    # D-SHELL page aspects — layout / type-ramp / spacing-rhythm as governed laws, not vibe
    "page_has_content_column": page_has_content_column,
    "shell_type_ramp_tiered": shell_type_ramp_tiered,
    "shell_density_from_profile": shell_density_from_profile,
    "section_grouping_flat": section_grouping_flat,
    "motion_tokens_cited": motion_tokens_cited,
    "nav_anatomy": nav_anatomy,
}

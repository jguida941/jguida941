"""The GATHER seam — turn a rendered component (html, css) into verdict-free FACTS. It DECIDES
nothing (the predicate library + conform() decide); it only observes. This is the profile-/host-
specific glue; everything above it is portable. Only STATICALLY-parseable facts are gathered here
(radius, anatomy, material presence, shadow presence, mechanic, focus recipe) — computed contrast
over a translucent surface + responsive-no-clip are renderer-dependent and are gathered by the
headless-probe (a declared later slice), never faked here. candidate_only.
"""
from __future__ import annotations

import re


def button_facts(html: str, css: str) -> dict:
    """Facts observable from `render_button`'s output. `css` may concatenate the rest + active +
    focus renders; the BASE rule is the first non-state `.cls { … }` block, the state recipes are
    the `.is-*` rules. Fail-closed (codex 1b-ii #1): if no base rule is parseable, material/shadow
    facts are `None` (not `False`) so a material/elevation predicate cannot pass on empty CSS."""
    base_m = re.search(r"\.[\w-]+\s*\{([^}]*)\}", css)   # first rule = the base `.cls { … }`
    base = base_m.group(1) if base_m else None

    m = re.search(r"border-radius:\s*(\d+)px", base) if base is not None else None
    radius_px = int(m.group(1)) if m else None

    # anatomy: Carbon emits a label node THEN a trailing icon sibling; the Apple capsules a
    # centered label (icon leading). Requires POSITIVE evidence of a rendered <button>, else None
    # (fail-closed) — an empty render must not pass an anatomy invariant.
    # label-left-icon-right requires a btn-label WITH text (codex: an empty-label Carbon DOM is not
    # positive evidence) BEFORE the btn-icon; centered-capsule requires a <button> with text.
    if (re.search(r'class="btn-label">[^<]*\w', html) and "btn-icon" in html
            and html.index("btn-label") < html.index("btn-icon")):
        anatomy = "label-left-icon-right"
    elif re.search(r"<button[^>]*>[^<]*\w", html):   # a <button> with actual text (empty <button></button> -> None)
        anatomy = "centered-capsule"
    else:
        anatomy = None

    # state mechanic: MUTUALLY EXCLUSIVE (codex 1b-ii #2). Count every press signal in `.is-active`;
    # resolve a mechanic ONLY when exactly one is present. Two signals (e.g. brightness + a token
    # swap) is ambiguous -> None -> the mechanic predicate fails, never a priority-picked pass.
    active = re.search(r"\.is-active\s*\{([^}]*)\}", css)
    active_css = active.group(1) if active else ""
    signals = []
    if "brightness(" in active_css:
        signals.append("glass-brightness")
    if re.search(r"\bopacity:", active_css):
        signals.append("opacity-dim")
    if "background-color" in active_css:
        signals.append("token-swap")
    mechanic = signals[0] if len(signals) == 1 else None

    # focus recipe: keyed on SPECIFIC ring geometry AND mutually exclusive (same discipline as the
    # chip). A rule with both a square inset and a halo is ambiguous -> None, never priority-picked.
    focus_recipe = _focus_recipe(css, (
        ("inset 0 0 0 2px", "square-2px-ring"),    # carbon: inset 1px+2px square ring
        ("0 0 0 5px", "capsule-halo"),             # liquid: 2px backdrop + 5px accent halo
        ("0 0 0 4px", "rounded-system-ring"),      # apple: single 4px rounded system ring
    ))

    return {
        "radius_px": radius_px,
        "anatomy": anatomy,
        "state_mechanic": mechanic,
        # None (not False) when no base rule; a `none` value is NOT presence (codex) -> fail closed
        "has_backdrop_filter": _has_prop(base, "backdrop-filter"),
        "has_box_shadow": _has_prop(base, "box-shadow"),
        "focus_recipe": focus_recipe,
    }


def _base_rule(css: str):
    """The base `.cls { … }` body (first non-state rule), or None if unparseable — shared by the
    component fact-gatherers so material/shadow facts fail closed (None) on empty CSS."""
    m = re.search(r"\.[\w-]+\s*\{([^}]*)\}", css)
    return m.group(1) if m else None


def _invisible_color(value: str) -> bool:
    """A colour that paints nothing: the `transparent`/`none` keywords OR a 0-alpha rgba/hsla."""
    v = value.strip()
    return (v in ("transparent", "none")
            or re.search(r"(?:rgba|hsla)\([^)]*,\s*0(?:\.0+)?\s*\)$", v) is not None)


def _has_prop(base, prop: str):
    """True iff `base` declares `prop` with a value that actually renders — NOT `none` (incl.
    `none !important`) and not empty. None if there is no base rule (fail-closed). codex:
    `backdrop-filter: none` / `box-shadow: none !important` must NOT read as present."""
    if base is None:
        return None
    for v in re.findall(rf"{prop}:\s*([^;]+)", base):
        v = v.replace("!important", "").strip()
        if v not in ("none", ""):
            return True
    return False


def _mechanic(css: str):
    """The MUTUALLY-EXCLUSIVE press mechanic read from `.is-active` (None if zero or >1 signals)."""
    active = re.search(r"\.is-active\s*\{([^}]*)\}", css)
    active_css = active.group(1) if active else ""
    signals = []
    if "brightness(" in active_css:
        signals.append("glass-brightness")
    if re.search(r"\bopacity:", active_css):
        signals.append("opacity-dim")
    if "background-color" in active_css:
        signals.append("token-swap")
    return signals[0] if len(signals) == 1 else None


def _focus_recipe(css: str, recipes: tuple[tuple[str, str], ...]):
    """The MUTUALLY-EXCLUSIVE focus recipe read from `.is-focus`.

    `recipes` is `(literal_signature, recipe_name)`. A missing focus rule OR multiple matching ring
    signatures returns None, so predicates fail closed instead of taking a priority branch.
    """
    focus = re.search(r"\.is-focus\s*\{([^}]*)\}", css)
    focus_css = focus.group(1) if focus else ""
    signals = [name for needle, name in recipes if needle in focus_css]
    return signals[0] if len(signals) == 1 else None


def chip_facts(html: str, css: str) -> dict:
    """Verdict-free facts for the chip/tag (instance #2). Same fail-closed / mutually-exclusive
    discipline as `button_facts`; chip-specific: `label-dismiss` anatomy (a trailing `×` close
    button), an `outline: 2px` focus recipe (Carbon Tag, distinct from the button's inset ring),
    and `typography_case` (sentence unless a `text-transform: uppercase` is emitted)."""
    base = _base_rule(css)
    m = re.search(r"border-radius:\s*(\d+)px", base) if base is not None else None
    radius_px = int(m.group(1)) if m else None

    # label-dismiss: a label node FOLLOWED BY a trailing dismiss <button> (codex chip #3 — a bare
    # `chip-dismiss` substring anywhere is not enough; it must be the close BUTTON after the label).
    # Requires POSITIVE evidence of a rendered chip pill, else None (fail-closed on an empty render).
    dismiss = '<button class="chip-dismiss"'
    # label-dismiss requires a chip-label WITH text (codex: empty label span is not evidence)
    if (re.search(r'class="chip-label">[^<]*\w', html) and dismiss in html
            and html.index("chip-label") < html.index(dismiss)):
        anatomy = "label-dismiss"
    elif re.search(r'<span class="chip-[^"]*">[^<]*\w', html):   # a chip pill with actual text (empty span -> None)
        anatomy = "centered-label"
    else:
        anatomy = None

    # focus recipe: MUTUALLY EXCLUSIVE — count signals, None on zero or >1 (same discipline as the
    # mechanic; codex chip N1 — `outline: 2px` + a halo can't both resolve to outline-2px).
    focus_recipe = _focus_recipe(css, (
        ("outline: 2px", "outline-2px"),            # carbon Tag: 2px solid outline + 1px offset
        ("0 0 0 5px", "capsule-halo"),             # liquid: capsule halo
        ("0 0 0 4px", "rounded-system-ring"),      # apple: rounded system ring
    ))

    return {
        "radius_px": radius_px,
        "anatomy": anatomy,
        "state_mechanic": _mechanic(css),
        "has_backdrop_filter": _has_prop(base, "backdrop-filter"),
        "has_box_shadow": _has_prop(base, "box-shadow"),
        "focus_recipe": focus_recipe,
        # fail-closed (codex chip #2): None (not "sentence") when no base rule -> chip_sentence_case fails
        "typography_case": (None if base is None
                            else ("upper" if "text-transform: uppercase" in base else "sentence")),
    }


def card_facts(html: str, css: str) -> dict:
    """Verdict-free STRUCTURAL facts for the card / grouped metric surface (instance #3). Only the
    composition is gathered here — declared box structure, NOT rendered ink (the 'content fills the
    card' verdict is a JUDGMENT concern, gathered by a visual receipt, never faked from a static
    parse). Fail-closed: a missing container/row rule -> the pattern facts are False/None so the
    predicate fails."""
    container = _base_rule(css)              # first rule = the `.card-<cls>` container
    m = re.search(r"border-radius:\s*(\d+)px", container) if container is not None else None
    radius_px = int(m.group(1)) if m else None

    container_count = html.count("card-group")     # each container carries the `card-group` marker
    row_count = html.count('class="card-row"')

    row_m = re.search(r"\.card-row\s*\{([^}]*)\}", css)   # the row base rule (not the `+` divider)
    row_body = row_m.group(1) if row_m else None
    # rows carry NO independent background (incl. -color/-image longhands, codex card #2) and NO
    # radius (incl. any `*-radius` longhand). A row with its own chrome IS the grid-of-tiles AI look.
    row_has_own_bg = bool(row_body is not None and any(
        v.strip() not in ("transparent", "none")
        for v in re.findall(r"background(?:-color|-image)?:\s*([^;]+)", row_body)))
    rows_chromeless = bool(
        row_body is not None
        and "-radius" not in row_body
        and not row_has_own_bg)
    # horizontal AXIS: flex, and no `column` in flex-direction OR the flex-flow shorthand (codex card #3)
    rows_horizontal = bool(
        row_body is not None
        and "display: flex" in row_body
        and not re.search(r"flex-(?:direction|flow):[^;]*column", row_body))

    # a VISIBLE 1px divider — `border-top: 1px solid <color>` with a colour that actually paints
    # (codex: `1px solid transparent` AND `1px solid rgba(0,0,0,0)` are invisible, not a hairline).
    div_m = re.search(r"\.card-row\s*\+\s*\.card-row\s*\{([^}]*)\}", css)
    div_color = re.search(r"border-top:\s*1px\s+solid\s+([^;]+)", div_m.group(1)) if div_m else None
    divider_1px = bool(div_color and not _invisible_color(div_color.group(1)))

    return {
        "radius_px": radius_px,
        "container_count": container_count,
        "row_count": row_count,
        "rows_chromeless": rows_chromeless,
        "rows_horizontal": rows_horizontal,
        "divider_1px": divider_1px,
        "has_backdrop_filter": _has_prop(container, "backdrop-filter"),
        "has_box_shadow": _has_prop(container, "box-shadow"),
    }

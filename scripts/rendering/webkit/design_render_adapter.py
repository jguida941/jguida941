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
    # centered label (icon leading). Structural, read off the DOM.
    anatomy = "centered-capsule"
    if "btn-label" in html and "btn-icon" in html and html.index("btn-label") < html.index("btn-icon"):
        anatomy = "label-left-icon-right"

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

    # focus recipe: keyed on the SPECIFIC ring geometry, not "any inset" (codex 1b-ii #3) — a
    # mutated `inset 0 0 0 999px` is no longer a 2px square ring, so the deterministic invariant bites.
    focus = re.search(r"\.is-focus\s*\{([^}]*)\}", css)
    focus_css = focus.group(1) if focus else ""
    if "inset 0 0 0 2px" in focus_css:             # carbon: inset 1px+2px square ring
        focus_recipe = "square-2px-ring"
    elif "0 0 0 5px" in focus_css:                 # liquid: 2px backdrop + 5px accent halo
        focus_recipe = "capsule-halo"
    elif "0 0 0 4px" in focus_css:                 # apple: single 4px rounded system ring
        focus_recipe = "rounded-system-ring"
    else:
        focus_recipe = None

    return {
        "radius_px": radius_px,
        "anatomy": anatomy,
        "state_mechanic": mechanic,
        # None (not False) when no base rule parsed -> `is False` material/elevation predicates fail closed
        "has_backdrop_filter": ("backdrop-filter" in base) if base is not None else None,
        "has_box_shadow": ("box-shadow" in base) if base is not None else None,
        "focus_recipe": focus_recipe,
    }


def _base_rule(css: str):
    """The base `.cls { … }` body (first non-state rule), or None if unparseable — shared by the
    component fact-gatherers so material/shadow facts fail closed (None) on empty CSS."""
    m = re.search(r"\.[\w-]+\s*\{([^}]*)\}", css)
    return m.group(1) if m else None


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
    dismiss = '<button class="chip-dismiss"'
    anatomy = ("label-dismiss"
               if ("chip-label" in html and dismiss in html
                   and html.index("chip-label") < html.index(dismiss))
               else "centered-label")

    # focus recipe: MUTUALLY EXCLUSIVE — count signals, None on zero or >1 (same discipline as the
    # mechanic; codex chip N1 — `outline: 2px` + a halo can't both resolve to outline-2px).
    focus = re.search(r"\.is-focus\s*\{([^}]*)\}", css)
    focus_css = focus.group(1) if focus else ""
    fsignals = []
    if "outline: 2px" in focus_css:                # carbon Tag: 2px solid outline + 1px offset
        fsignals.append("outline-2px")
    if "0 0 0 5px" in focus_css:                   # liquid: capsule halo
        fsignals.append("capsule-halo")
    if "0 0 0 4px" in focus_css:                   # apple: rounded system ring
        fsignals.append("rounded-system-ring")
    focus_recipe = fsignals[0] if len(fsignals) == 1 else None

    return {
        "radius_px": radius_px,
        "anatomy": anatomy,
        "state_mechanic": _mechanic(css),
        "has_backdrop_filter": ("backdrop-filter" in base) if base is not None else None,
        "has_box_shadow": ("box-shadow" in base) if base is not None else None,
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

    # a VISIBLE 1px divider — `border-top: 1px solid …`; `1px none/transparent` is NOT a divider (codex card #3)
    div_m = re.search(r"\.card-row\s*\+\s*\.card-row\s*\{([^}]*)\}", css)
    divider_1px = bool(div_m and re.search(r"border-top:\s*1px\s+solid", div_m.group(1)))

    return {
        "radius_px": radius_px,
        "container_count": container_count,
        "row_count": row_count,
        "rows_chromeless": rows_chromeless,
        "rows_horizontal": rows_horizontal,
        "divider_1px": divider_1px,
        "has_backdrop_filter": ("backdrop-filter" in container) if container is not None else None,
        "has_box_shadow": ("box-shadow" in container) if container is not None else None,
    }

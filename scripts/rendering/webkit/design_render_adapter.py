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

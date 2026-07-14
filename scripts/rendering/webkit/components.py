"""P5-WEBKIT-BUTTON — profile-driven web components (the RENDER seam).

`render_button(profile, variant, state) -> (html, css)` reads a profile's DATA (the
DTCG token block, resolved via the loader, + the `components.button` anatomy block) and emits
HTML+CSS. It branches on the per-profile ANATOMY so STRUCTURE differs across languages — Carbon
emits a `label-left / icon-right` DOM, the Apple capsules a centered row — not merely a token
swap. Token-only colour; the glass material is single-sourced from `design_tokens.material`.
candidate_only.
"""
from __future__ import annotations

from dataclasses import dataclass
from html import escape as _escape


def _is_light(hex_color: str) -> bool:
    """Perceived-brightness default (light accent → dark text, dark accent → light text) matching
    each platform's filled-button convention — Apple/Carbon put LIGHT text on their saturated
    accents. This is NOT a WCAG contrast gate: for a saturated mid-tone accent the FAITHFUL choice
    can sit below AA (Apple's own white-on-#0a84ff is ~3.65:1). The real contrast verdict is a
    DEFERRED/candidate concern (the headless-probe slice), never claimed here (codex 1a-ii-B #1)."""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return False
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return (0.299 * r + 0.587 * g + 0.114 * b) > 150


def _liquid_glass_material(dt, profile: str) -> dict | None:
    """Return the profile's glass material only if it actually renders as glass.

    `design_tokens.MATERIALS` is now a public web bridge for every active profile, including
    flat systems like Carbon. A row in that bridge is not a glass capability: blur(0) +
    opaque surfaces must not make a liquid-glass component transplant admissible.
    """
    if profile not in dt.MATERIALS:
        return None
    material = dt.material(profile)
    if float(material.get("blur", 0)) <= 0:
        return None
    if float(material.get("surface_opacity", 1)) >= 1 and float(material.get("raised_opacity", 1)) >= 1:
        return None
    return material


def render_button(profile: str, variant: str, state: str, profile_data: dict | None = None) -> tuple[str, str]:
    from scripts.rendering import design_tokens as dt
    from scripts.rendering.design import loader

    prof = profile_data if profile_data is not None else loader.load(profile)
    color = loader.resolve_tokens(profile)["color"]
    font = loader.resolve_tokens(profile).get("font", {}).get("family", "sans-serif")
    btn = prof["components"]["button"]
    accent, ink_strong = color["accent"], color["ink-strong"]
    backdrop = color.get("backdrop", "#000000")
    cls = f"btn-{profile}-{variant}"
    anatomy = btn["anatomy"]
    justify = "space-between" if anatomy == "label-left-icon-right" else "center"

    # variant surface (the filled/prominent variant = accent fill; the rest = quiet/ghost).
    # Filled text contrasts the accent (dark text on a light accent, light text on a dark one).
    filled = variant in ("prominent", "primary", "filled") or variant.endswith("-primary")
    bg, fg = (accent, (backdrop if _is_light(accent) else "#ffffff")) if filled else ("transparent", accent)

    # ANATOMY -> genuinely different DOM (the deterministic structure axis)
    if anatomy == "label-left-icon-right":
        html = (f'<button class="{cls}" data-dom-owner="webkit.button">'
                f'<span class="btn-label" data-dom-owner="webkit.button">{variant}</span>'
                f'<svg class="btn-icon" data-dom-owner="webkit.button" aria-hidden="true" '
                f'width="16" height="16"></svg></button>')
    else:  # centered-capsule
        html = f'<button class="{cls}" data-dom-owner="webkit.button">{variant}</button>'

    # padding: scalar inline, OR [leading, trailing] (Carbon's asymmetric 16/64 icon gutter)
    pi = btn["pad_inline_px"]
    pad = (f"{btn['pad_block_px']}px {pi[1]}px {btn['pad_block_px']}px {pi[0]}px"
           if isinstance(pi, (list, tuple)) else f"{btn['pad_block_px']}px {pi}px")

    base = [
        f"display: inline-flex; align-items: center; justify-content: {justify};",
        "gap: 6px; border: 0; cursor: pointer;",
        f"border-radius: {btn['radius_px']}px;",
        f"min-height: {btn['height_px']}px; padding: {pad};",
        f"background: {bg}; color: {fg};",
        f"font: 600 17px/1.2 {font};",
        f"transition: all {btn['transition_ms']}ms {btn['easing']};",
    ]
    # frosted-glass material on the button — blur/saturate single-sourced from design_tokens
    if btn.get("material") == "liquid-glass" and (m := _liquid_glass_material(dt, profile)):
        glass = f"blur({m['blur']:g}px) saturate({m['saturate']:g}%)"
        base.append(f"-webkit-backdrop-filter: {glass}; backdrop-filter: {glass};")
    if btn.get("elevation_shadow"):  # null/None for flat languages -> no box-shadow at all
        base.append(f"box-shadow: {btn['elevation_shadow']};")

    css = f".{cls} {{ {' '.join(base)} }}"

    # per-state recipe (drawn from the profile's declared mechanic — never a fake passing body)
    fr = btn.get("focus_recipe")
    if state == "active" and btn.get("active_css"):
        decl = " ".join(f"{k}: {v};" for k, v in btn["active_css"].items())
        css += f"\n.{cls}.is-active {{ {decl} }}"
    elif state == "hover" and btn.get("hover_css"):
        decl = " ".join(f"{k}: {v};" for k, v in btn["hover_css"].items())
        css += f"\n.{cls}.is-hover {{ {decl} }}"
    elif state == "hover" and btn.get("state_mechanic") == "glass-brightness":
        css += f"\n.{cls}.is-hover {{ filter: brightness(1.08); }}"
    elif state == "focus-visible" and fr == "capsule-halo":
        css += (f"\n.{cls}.is-focus {{ outline: 0; box-shadow: 0 0 0 2px {backdrop}, "
                f"0 0 0 5px color-mix(in srgb, {accent} 60%, transparent); }}")
    elif state == "focus-visible" and fr == "square-2px-ring":
        css += f"\n.{cls}.is-focus {{ outline: 0; box-shadow: inset 0 0 0 1px {accent}, inset 0 0 0 2px {backdrop}; }}"
    elif state == "focus-visible" and fr == "rounded-system-ring":
        css += f"\n.{cls}.is-focus {{ outline: 0; box-shadow: 0 0 0 4px color-mix(in srgb, {accent} 50%, transparent); }}"
    elif state == "disabled":
        css += f"\n.{cls}.is-disabled {{ opacity: 0.4; pointer-events: none; }}"

    return html, css


def render_chip(profile: str, variant: str, state: str, profile_data: dict | None = None) -> tuple[str, str]:
    """The chip/tag component (instance #2). Reads `components.chip` and branches on ANATOMY:
    a Carbon *dismissible Tag* emits `label + trailing × close button` (label-dismiss), an Apple
    pill emits a centered label. Token-only colour; glass material single-sourced from
    design_tokens; sentence case (no text-transform). candidate_only."""
    from scripts.rendering import design_tokens as dt
    from scripts.rendering.design import loader

    prof = profile_data if profile_data is not None else loader.load(profile)
    color = loader.resolve_tokens(profile)["color"]
    font = loader.resolve_tokens(profile).get("font", {}).get("family", "sans-serif")
    chip = prof["components"]["chip"]
    accent = color["accent"]
    ink_strong = color.get("ink-strong", "#111111")
    raised = color.get("surface-raised", color.get("surface", "#1c1c1e"))
    backdrop = color.get("backdrop", "#000000")
    cls = f"chip-{profile}-{variant}"
    anatomy = chip["anatomy"]
    fr = chip.get("focus_recipe")

    # chip fill: a QUIET tinted surface (metadata pill, not a primary action), token-only.
    # liquid-glass = a translucent accent tint over the frosted material; carbon/apple = an opaque
    # fill (a flat palette-step for Carbon, a raised system surface for apple-dark).
    if chip.get("material") == "liquid-glass":
        bg = f"color-mix(in srgb, {accent} 16%, transparent)"
    else:
        bg = raised
    fg = ink_strong

    # ANATOMY -> genuinely different DOM
    label = _escape(variant)  # variant is controlled profile DATA; escape at the text/attr boundary
    if anatomy == "label-dismiss":  # Carbon dismissible Tag: label + trailing × close button
        html = (f'<span class="{cls}" data-dom-owner="webkit.chip">'
                f'<span class="chip-label" data-dom-owner="webkit.chip">{label}</span>'
                f'<button class="chip-dismiss" data-dom-owner="webkit.chip" '
                f'aria-label="Remove {label}">&times;</button></span>')
    else:  # centered-label (Apple pill)
        html = f'<span class="{cls}" data-dom-owner="webkit.chip">{label}</span>'

    base = [
        "display: inline-flex; align-items: center; gap: 6px;",
        "border: 0; cursor: default;",
        f"border-radius: {chip['radius_px']}px;",
        f"min-height: {chip['height_px']}px; padding: {chip['pad_block_px']}px {chip['pad_inline_px']}px;",
        f"background: {bg}; color: {fg};",
        f"font: {chip.get('font_weight', 500)} {chip['font_size_px']}px/1.33 {font};",
        f"transition: all {chip['transition_ms']}ms {chip['easing']};",
    ]
    if chip.get("material") == "liquid-glass" and (m := _liquid_glass_material(dt, profile)):
        glass = f"blur({m['blur']:g}px) saturate({m['saturate']:g}%)"
        base.append(f"-webkit-backdrop-filter: {glass}; backdrop-filter: {glass};")
    if chip.get("elevation_shadow"):  # null for flat languages -> no box-shadow at all
        base.append(f"box-shadow: {chip['elevation_shadow']};")

    css = f".{cls} {{ {' '.join(base)} }}"

    if state == "active" and chip.get("active_css"):
        decl = " ".join(f"{k}: {v};" for k, v in chip["active_css"].items())
        css += f"\n.{cls}.is-active {{ {decl} }}"
    elif state == "hover" and chip.get("hover_css"):
        decl = " ".join(f"{k}: {v};" for k, v in chip["hover_css"].items())
        css += f"\n.{cls}.is-hover {{ {decl} }}"
    elif state == "hover" and chip.get("state_mechanic") == "glass-brightness":
        css += f"\n.{cls}.is-hover {{ filter: brightness(1.06); }}"
    elif state == "focus-visible" and fr == "capsule-halo":
        css += (f"\n.{cls}.is-focus {{ outline: 0; box-shadow: 0 0 0 2px {backdrop}, "
                f"0 0 0 5px color-mix(in srgb, {accent} 60%, transparent); }}")
    elif state == "focus-visible" and fr == "outline-2px":  # Carbon Tag: 2px outline + 1px offset
        css += f"\n.{cls}.is-focus {{ outline: 2px solid {accent}; outline-offset: 1px; }}"
    elif state == "focus-visible" and fr == "rounded-system-ring":
        css += f"\n.{cls}.is-focus {{ outline: 0; box-shadow: 0 0 0 4px color-mix(in srgb, {accent} 50%, transparent); }}"
    elif state == "disabled":
        css += f"\n.{cls}.is-disabled {{ opacity: 0.4; pointer-events: none; }}"

    return html, css


# A card GROUPS related metrics as rows (never one box per number). Fixed sample rows for the
# showcase specimen; the composition — not the data — is what the invariants test.
_CARD_ROWS = (("Commits", "1,240"), ("Current streak", "23 days"), ("Languages", "12"))


@dataclass(frozen=True)
class MetricRow:
    """Closed structured input for a grouped metric row."""

    label: str
    value: str = "—"
    detail: str | None = None
    icon: str | None = None
    label_id: str | None = None
    value_id: str | None = None
    slot: str | None = None
    bind: str | None = None
    suffix: str | None = None
    round_digits: int | None = None
    snapshot_key: str | None = None


def _metric_row_html(row: MetricRow, owner: str) -> str:
    from scripts.rendering.icons import LUCIDE

    icon = ""
    if row.icon:
        if row.icon not in LUCIDE:
            raise KeyError(f"unknown Lucide icon {row.icon!r}")
        icon = (f'<svg class="card-icon" {owner} viewBox="0 0 24 24" aria-hidden="true">'
                f'{LUCIDE[row.icon]}</svg>')
    label_id = f' id="{_escape(row.label_id)}"' if row.label_id else ""
    value_id = f' id="{_escape(row.value_id)}"' if row.value_id else ""
    attrs = [value_id]
    for name, value in (("data-slot", row.slot), ("data-bind", row.bind),
                        ("data-suffix", row.suffix), ("data-snapshot-key", row.snapshot_key)):
        if value is not None:
            attrs.append(f' {name}="{_escape(str(value))}"')
    if row.round_digits is not None:
        attrs.append(f' data-round="{row.round_digits}"')
    detail = (f'<span class="card-detail" {owner}>{_escape(row.detail)}</span>'
              if row.detail else "")
    return (
        f'<div class="card-row" {owner}>'
        f'<span class="card-label" {owner}>{icon}'
        f'<span {owner}{label_id}>{_escape(row.label)}</span>{detail}</span>'
        f'<span class="card-value" {owner}{"".join(attrs)}>{_escape(row.value)}</span>'
        f'</div>'
    )


def _card_css(
    profile: str,
    variant: str,
    selector: str,
    profile_data: dict | None = None,
    *,
    token_only: bool = False,
) -> str:
    from scripts.rendering import design_tokens as dt
    from scripts.rendering.design import loader

    prof = profile_data if profile_data is not None else loader.load(profile)
    color = loader.resolve_tokens(profile)["color"]
    font = loader.resolve_tokens(profile).get("font", {}).get("family", "sans-serif")
    card = prof["components"]["card"]
    surface = "var(--surface-raised)" if token_only else color.get("surface-raised", color["surface"])
    ink_strong = "var(--ink-strong)" if token_only else color["ink-strong"]
    ink_dim = "var(--ink-dim)" if token_only else color.get("ink-dim", color["ink"])
    hairline = "var(--hairline)" if token_only else color["hairline"]
    font_value = "var(--font-sans)" if token_only else font
    container = [
        f"background: {surface};",
        f"border-radius: {card['radius_px']}px;",
        f"border: 1px solid {hairline}; overflow: hidden;",
    ]
    if card.get("material") == "liquid-glass" and (material := _liquid_glass_material(dt, profile)):
        glass = ("blur(var(--glass-blur)) saturate(var(--glass-saturate))" if token_only
                 else f"blur({material['blur']:g}px) saturate({material['saturate']:g}%)")
        container.append(f"-webkit-backdrop-filter: {glass}; backdrop-filter: {glass};")
    if card.get("elevation_shadow"):
        container.append(f"box-shadow: {card['elevation_shadow']};")
    return (
        f"{selector} {{ {' '.join(container)} }}\n"
        f"{selector} .card-row {{ display: flex; align-items: center; justify-content: space-between; "
        f"gap: 16px; padding: {card['row_pad']}; background: transparent; }}\n"
        f"{selector} .card-row + .card-row {{ border-top: 1px solid {hairline}; }}\n"
        f"{selector} .card-label {{ display: flex; align-items: center; gap: 8px; color: {ink_dim}; "
        f"font: 400 {card['font_size_px']}px/1.3 {font_value}; min-width: 0; }}\n"
        f"{selector} .card-detail {{ color: {ink_dim}; font-size: 12px; }}\n"
        f"{selector} .card-icon {{ width: 16px; height: 16px; fill: none; stroke: currentColor; "
        f"stroke-width: 1.6; stroke-linecap: round; stroke-linejoin: round; flex: 0 0 auto; }}\n"
        f"{selector} .card-value {{ color: {ink_strong}; font: {card.get('value_weight', 600)} "
        f"{card['font_size_px']}px/1.3 {font_value}; text-align: right; white-space: nowrap; }}"
    )


def render_card(
    profile: str,
    variant: str,
    state: str,
    profile_data: dict | None = None,
    *,
    rows: tuple[MetricRow, ...] | None = None,
    switchable: bool = False,
) -> tuple[str, str]:
    """The CARD / grouped metric surface (instance #3) — the DEEPER-REFRAME answer to "giant KPI
    boxes". Emits ONE container holding N chrome-less rows (label + value inline, hierarchy from
    TYPE), rows divided by a 1px hairline — an Apple inset grouped list (rounded, frosted/opaque) or
    a Carbon flat square Tile (gridlined). The rows carry NO independent background/radius — that is
    the deterministic anti-'grid of chromed tiles' law. Token-only; glass single-sourced. `state`
    is accepted for signature parity (a card is a static container). candidate_only."""
    from scripts.rendering.design import loader

    prof = profile_data if profile_data is not None else loader.load(profile)
    owner = 'data-dom-owner="webkit.card"'
    metric_rows = rows or tuple(MetricRow(label, value) for label, value in _CARD_ROWS)
    if not metric_rows:
        raise ValueError("a grouped card requires at least one row")
    rows_html = "".join(_metric_row_html(row, owner) for row in metric_rows)
    if switchable:
        profiles = tuple(loader.load("_index")["active_design_profiles"])
        if profile not in profiles:
            raise KeyError(f"house profile {profile!r} is not active")
        classes = " ".join(f"card-{name}-{variant}" for name in profiles)
        html = f'<div class="{classes} card-group" {owner}>{rows_html}</div>'
        blocks = [
            _card_css(name, variant, f':root[data-theme="{name}"] .card-{name}-{variant}',
                      token_only=True)
            for name in profiles
        ]
        blocks.append(_card_css(profile, variant,
                                f':root:not([data-theme]) .card-{profile}-{variant}', prof,
                                token_only=True))
        css = "\n".join(blocks)
    else:
        cls = f"card-{profile}-{variant}"
        html = f'<div class="{cls} card-group" {owner}>{rows_html}</div>'
        css = _card_css(profile, variant, f".{cls}", prof)
    return html, css


def _nav_css(nav: dict, selector: str) -> str:
    rules = [
        f"{selector} {{ display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }}",
        f"{selector} a {{ color: var(--ink-dim); text-decoration: none; padding: 6px 14px;"
        f" border-radius: {nav['radius_px']}px; font-weight: 600; font-size: 13px;"
        f" transition: color var(--motion-fast) var(--ease-standard); }}",
    ]
    if nav["anatomy"] == "underline-tabs":
        rules.append(f"{selector} a[aria-current] {{ color: var(--ink); border-bottom: 2px solid var(--accent);"
                     f" border-radius: 0; }}")
    else:
        rules.append(f"{selector} a[aria-current] {{ background: var(--accent); color: var(--backdrop); }}")
    return "\n".join(rules)


def render_nav(profile: str, links: list, active: str, profile_data: dict | None = None) -> tuple[str, str]:
    """The site NAV band (P5-BOARD B-1b, docs/design/board.md §1 / test_design_nav). Anatomy from
    `components.nav` profile DATA (carbon: underline-tabs, square; capsule languages: pills with a
    filled active). CSS is VAR-BASED (var(--accent)/var(--ink…)) — portable across the dashboard's
    emit_css_root and the shell's root_block, which expose the same role vars — so the band passes
    the no-hex law on every page while the ANATOMY still branches per language."""
    from scripts.rendering.design import loader

    prof = profile_data if profile_data is not None else loader.load(profile)
    nav = prof["components"]["nav"]
    cls = f"nav-{profile}"
    items = "".join(
        f'<a href="{_escape(href)}" data-theme-propagate' + (' aria-current="page"' if href == active else "")
        + f'>{_escape(label)}</a>'
        for label, href in links)
    html = (f'<nav class="site-nav {cls}" data-dom-owner="webkit.nav.single" '
            f'aria-label="Site">{items}</nav>')
    return html, _nav_css(nav, f".{cls}")


def render_switchable_nav(house: str, links: list, active: str) -> tuple[str, str]:
    """One semantic nav whose profile-derived anatomy follows the root theme."""
    from scripts.rendering.design import loader

    profiles = tuple(loader.load("_index")["active_design_profiles"])
    if house not in profiles:
        raise KeyError(f"house profile {house!r} is not active")
    classes = " ".join(f"nav-{profile}" for profile in profiles)
    items = "".join(
        f'<a href="{_escape(href)}" data-theme-propagate' + (' aria-current="page"' if href == active else "")
        + f'>{_escape(label)}</a>'
        for label, href in links)
    html = (f'<nav class="site-nav {classes}" data-dom-owner="webkit.nav" '
            f'aria-label="Site">{items}</nav>')
    blocks = []
    for profile in profiles:
        nav = loader.load(profile)["components"]["nav"]
        blocks.append(_nav_css(nav, f':root[data-theme="{profile}"] .nav-{profile}'))
    blocks.append(_nav_css(loader.load(house)["components"]["nav"],
                           f':root:not([data-theme]) .nav-{house}'))
    return html, "\n".join(blocks)


def _switcher_profile_css(profile: str, selector: str) -> str:
    from scripts.rendering.design import loader

    button = loader.load(profile)["components"]["button"]
    justify = "space-between" if button["anatomy"] == "label-left-icon-right" else "center"
    icon_display = "block" if button["anatomy"] == "label-left-icon-right" else "none"
    states = button["switcher_css"]
    required_states = {"hover", "active", "focus-visible", "selected", "disabled"}
    if set(states) != required_states or any(not states[state] for state in required_states):
        raise ValueError(f"{profile}: switcher_css must close {sorted(required_states)}")

    def declarations(state: str) -> str:
        return " ".join(f"{key}: {value};" for key, value in states[state].items())

    return "\n".join((
        f"{selector} {{ border-radius: {button['radius_px']}px; }}",
        f"{selector} .theme-option {{ min-height: {button['height_px']}px; "
        f"border-radius: {button['radius_px']}px; justify-content: {justify}; "
        f"transition-duration: var(--motion-switcher); "
        f"transition-timing-function: var(--ease-switcher); }}",
        f"{selector} .theme-option-icon {{ display: {icon_display}; }}",
        f"{selector} .theme-option:hover {{ {declarations('hover')} }}",
        f"{selector} .theme-option:active {{ {declarations('active')} }}",
        f"{selector} .theme-option:focus-visible {{ {declarations('focus-visible')} }}",
        f"{selector} .theme-option[aria-pressed=\"true\"] {{ {declarations('selected')} }}",
        f"{selector} .theme-option:disabled {{ {declarations('disabled')} }}",
    ))


def render_theme_switcher(house: str) -> tuple[str, str]:
    """Render the one governed segmented theme control for every active profile."""
    from scripts.rendering import design_tokens as dt

    profiles = tuple(dt.ACTIVE_THEME_NAMES)
    if house not in profiles:
        raise KeyError(f"house profile {house!r} is not active")
    owner = 'data-dom-owner="webkit.switcher"'
    from scripts.rendering.icons import LUCIDE
    icon = (f'<svg class="theme-option-icon" {owner} viewBox="0 0 24 24" aria-hidden="true">'
            f'{LUCIDE["check"]}</svg>')
    buttons = "".join(
        f'<button class="theme-option" {owner} type="button" data-theme-set="{_escape(profile)}" '
        f'aria-pressed="{str(profile == house).lower()}" title="{_escape(dt.THEME_META[profile]["blurb"])}">'
        f'<span {owner}>{_escape(dt.THEME_META[profile]["label"])}</span>{icon}</button>'
        for profile in profiles
    )
    html = (f'<div class="theme-switcher" {owner} data-switcher-house="{_escape(house)}" '
            f'role="group" aria-label="Theme">'
            f'{buttons}</div>')
    blocks = [
        _switcher_profile_css(profile, f':root[data-theme="{profile}"] .theme-switcher')
        for profile in profiles
    ]
    blocks.append(_switcher_profile_css(
        house,
        f':root:not([data-theme]) .theme-switcher[data-switcher-house="{house}"]',
    ))
    blocks.append("""
.theme-switcher { display: inline-flex; gap: 3px; padding: 3px; border: 1px solid var(--hairline); background: var(--surface-raised); }
.theme-option { display: inline-flex; align-items: center; gap: 8px; border: 0; padding: 7px 13px; color: var(--ink-dim); background: transparent; font: inherit; cursor: pointer; white-space: nowrap; transition-property: color, background, filter, opacity, transform; }
.theme-option-icon { width: 16px; height: 16px; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.theme-option[aria-pressed="false"] .theme-option-icon { opacity: 0; }
.theme-option:hover { color: var(--ink); }
""".strip())
    return html, "\n".join(blocks)

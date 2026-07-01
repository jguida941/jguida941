"""P5-WEBKIT-BUTTON — profile-driven web components (the RENDER seam).

`render_button(profile, variant, state) -> (html, css)` reads a profile's DATA (the
DTCG token block, resolved via the loader, + the `components.button` anatomy block) and emits
HTML+CSS. It branches on the per-profile ANATOMY so STRUCTURE differs across languages — Carbon
emits a `label-left / icon-right` DOM, the Apple capsules a centered row — not merely a token
swap. Token-only colour; the glass material is single-sourced from `design_tokens.material`.
candidate_only.
"""
from __future__ import annotations


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


def render_button(profile: str, variant: str, state: str) -> tuple[str, str]:
    from scripts.rendering import design_tokens as dt
    from scripts.rendering.design import loader

    prof = loader.load(profile)
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
        html = (f'<button class="{cls}"><span class="btn-label">{variant}</span>'
                f'<svg class="btn-icon" aria-hidden="true" width="16" height="16"></svg></button>')
    else:  # centered-capsule
        html = f'<button class="{cls}">{variant}</button>'

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
    if btn.get("material") == "liquid-glass" and profile in dt.MATERIALS:
        m = dt.material(profile)
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

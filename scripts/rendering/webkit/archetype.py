"""P5-STUDIO — `render_archetype`: a full mini-website in ONE design language.

Composes the token-only component renderers (render_button/chip/card) with two token-only shells (a
nav bar + a hero) into a REAL example page, on the language's own backdrop. Every colour/radius/font
comes from `loader.resolve_tokens(profile)` — zero literals — so each language reads as ITSELF
(Apple looks Apple, Carbon looks Carbon), never the scorecard reskinned. `profile_data` injects a
composed profile (for the studio's governed component swaps, so the same renderer produces a swapped
component in place). candidate_only.
"""
from __future__ import annotations


def _signature_variant(component: dict) -> str:
    """The filled/prominent variant (the primary CTA)."""
    variants = component.get("variants", [])
    for v in variants:
        if v in ("prominent", "primary", "filled") or v.endswith("-primary"):
            return v
    return variants[0] if variants else "default"


def _secondary_variant(component: dict, signature: str) -> str:
    """A quiet variant distinct from the signature (the secondary button)."""
    for v in component.get("variants", []):
        if v != signature:
            return v
    return signature


def render_archetype(profile: str, profile_data: dict | None = None) -> tuple[str, str]:
    from scripts.rendering.design import loader
    from scripts.rendering.webkit.components import render_button, render_card, render_chip

    prof = profile_data if profile_data is not None else loader.load(profile)
    tokens = loader.resolve_tokens(profile)
    color = tokens["color"]
    font = tokens.get("font", {}).get("family", "sans-serif")
    backdrop = color.get("backdrop", "#0a0a0f")
    ink = color.get("ink-strong", "#e8e8ee")
    ink_dim = color.get("ink-dim", color.get("ink", "#9a9aa6"))
    hairline = color.get("hairline", "#23232e")
    ns = f"arch-{profile}"

    btn = prof["components"]["button"]
    sig, sec = _signature_variant(btn), _secondary_variant(btn, _signature_variant(btn))
    nav_cta_html, cta_css = render_button(profile, sig, "rest", profile_data=profile_data)
    hero_cta_html, _ = render_button(profile, sig, "rest", profile_data=profile_data)
    sec_html, sec_css = render_button(profile, sec, "rest", profile_data=profile_data)

    chip_variants = prof["components"]["chip"].get("variants", ["regular"])[:3]
    chip_pairs = [render_chip(profile, v, "rest", profile_data=profile_data) for v in chip_variants]
    chips_html = "".join(h for h, _ in chip_pairs)
    chips_css = "\n".join(c for _, c in chip_pairs)

    card_var = prof["components"]["card"]["variants"][0]
    card_html, card_css = render_card(profile, card_var, "rest", profile_data=profile_data)

    shell_css = "\n".join([
        f".{ns} {{ background: {backdrop}; color: {ink}; font-family: {font}; border-radius: 16px;",
        f"  overflow: hidden; border: 1px solid {hairline}; }}",
        f".{ns}-nav {{ display: flex; align-items: center; gap: 16px; padding: 16px 24px;",
        f"  border-bottom: 1px solid {hairline}; }}",
        f".{ns}-logo {{ font-weight: 700; color: {ink}; }}",
        f".{ns}-links {{ color: {ink_dim}; font-size: 14px; margin-left: auto; margin-right: 16px; }}",
        f".{ns}-hero {{ padding: 40px 24px 28px; }}",
        f".{ns}-hero h1 {{ margin: 0 0 8px; font-size: 30px; color: {ink}; }}",
        f".{ns}-hero p {{ margin: 0 0 18px; color: {ink_dim}; max-width: 52ch; }}",
        f".{ns}-chips {{ display: flex; gap: 8px; flex-wrap: wrap; margin: 0 0 20px; }}",
        f".{ns}-actions {{ display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }}",
        f".{ns}-body {{ padding: 0 24px 32px; }}",
        # the dismiss glyph is styled by the host page, not the component — scope it to this archetype
        f".{ns} .chip-dismiss {{ background: transparent; border: 0; color: inherit; cursor: pointer;",
        f"  font-size: 15px; line-height: 1; padding: 0 0 0 2px; }}",
    ])

    html = (
        f'<div class="{ns}" data-dom-owner="webkit.archetype">'
        f'<nav class="{ns}-nav" data-dom-owner="webkit.archetype">'
        f'<span class="{ns}-logo" data-dom-owner="webkit.archetype">◆ studio</span>'
        f'<span class="{ns}-links" data-dom-owner="webkit.archetype">Product · Docs · Pricing</span>'
        f'{nav_cta_html}</nav>'
        f'<header class="{ns}-hero" data-dom-owner="webkit.archetype"><h1>Build a site in this design language</h1>'
        f'<p>Every element — nav, buttons, tags, the grouped metric card — is this language, '
        f'composed from its own cited design doc.</p>'
        f'<div class="{ns}-chips" data-dom-owner="webkit.archetype">{chips_html}</div>'
        f'<div class="{ns}-actions" data-dom-owner="webkit.archetype">{hero_cta_html}{sec_html}</div></header>'
        f'<div class="{ns}-body" data-dom-owner="webkit.archetype">{card_html}</div>'
        f'</div>'
    )
    css = "\n".join([shell_css, cta_css, sec_css, chips_css, card_css])
    return html, css

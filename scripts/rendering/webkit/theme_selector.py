"""Persistent site-theme selector.

This is a local site-setting control, not a vendor button or a claim that Apple or
Carbon ships this exact component. Vendor tokens govern paint and focus; the
operator-ratified R-W3-VIS-1 clause governs its compact, equal-segment anatomy.
"""
from __future__ import annotations

from html import escape


def render_theme_selector(house: str) -> tuple[str, str]:
    """Return the single shared radiogroup used by every governed page."""
    from scripts.rendering import design_tokens as dt

    profiles = tuple(dt.ACTIVE_THEME_NAMES)
    if house not in profiles:
        raise KeyError(f"house profile {house!r} is not active")
    owner = 'data-dom-owner="webkit.theme-selector"'
    options = "".join(
        f'<button class="theme-option" {owner} type="button" role="radio" '
        f'data-theme-set="{escape(profile)}" '
        f'aria-checked="{str(profile == house).lower()}" '
        f'tabindex="{0 if profile == house else -1}" '
        f'title="{escape(dt.THEME_META[profile]["blurb"])}">'
        f'{escape(dt.THEME_META[profile]["label"])}</button>'
        for profile in profiles
    )
    markup = (
        f'<div class="theme-switcher" {owner} data-theme-selector="site" '
        f'data-switcher-house="{escape(house)}" role="radiogroup" '
        f'aria-label="Site theme">{options}</div>'
    )
    css = """
.theme-switcher {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  width: min(100%, 330px);
  margin: 0 0 8px auto;
  padding: 3px;
  border: 1px solid var(--selector-edge);
  border-radius: var(--radius-tile);
  background: var(--selector-background);
  -webkit-backdrop-filter: var(--selector-filter);
  backdrop-filter: var(--selector-filter);
}
.theme-option {
  display: grid;
  min-width: 0;
  min-height: 38px;
  place-items: center;
  padding: 6px 10px;
  border: 0;
  border-radius: max(0px, calc(var(--radius-tile) - 3px));
  color: var(--ink-dim);
  background: transparent;
  font: 600 13px/1.2 var(--font-sans);
  letter-spacing: 0;
  white-space: nowrap;
  cursor: pointer;
  transition: color var(--motion-fast) var(--ease-standard), background var(--motion-fast) var(--ease-standard);
}
.theme-option:hover { color: var(--ink); background: var(--selector-hover); }
.theme-option[aria-checked="true"] { color: var(--ink-strong); background: var(--selector-selected); }
.theme-option:focus { outline: 0; }
.theme-option:focus-visible { box-shadow: inset 0 0 0 2px var(--focus), inset 0 0 0 3px var(--focus-inset); }
.theme-option:disabled { opacity: .4; cursor: not-allowed; }
@media (max-width: 480px) {
  .theme-switcher { width: 100%; }
  .theme-option { min-height: 44px; padding-inline: 6px; }
}
""".strip()
    return markup, css

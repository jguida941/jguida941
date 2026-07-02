"""P5-CHROME — `render_page_shell`: the switchable governed page CHROME.

The site that shows off design languages must ITSELF be a rendered instance of one — not hand-written
dark CSS. `render_page_shell(profile, …)` builds the page background, header, breadcrumb, and section
panels entirely from `loader.resolve_tokens(profile)` (the language's colour/radius/font tokens) + a
shared, documented IA scale (`SHELL_SCALE`, the spacing/type rhythm) — **zero page-local palette**. So
the frame around every specimen is itself governed, and switching `profile` switches the whole page.

The honest gate (docs/design/pageshell.md §1) is provenance + mutation, not merely "no hex": every
host-chrome value is a `var()`; the `:root` vars equal the real token sources; a moved token moves the
chrome. Governed by conform()'s `page-shell` aspect + tests/contracts/test_page_shell.py. candidate_only.
"""
from __future__ import annotations

import html as _html
import re as _re


# The shell IA scale — every value CITED (design-audit D-SHELL; docs/design/pageshell.md §3):
# the page column + gutters replicate the proven index `.wrap` (DESIGN_SPEC Part 6's 980px column);
# gaps come from DESIGN_SPEC Part 0's step set {4,8,12,16,24,32} with section gap >= 24; the type
# ramp gains a real HEADING TIER (HIG Title-1 28 / Title-3 20 / body 15 / footnote 13) — the audit
# found body-sized section headers, i.e. no hierarchy. Panel PADDING is deliberately NOT here: it is
# per-language (the profile's cited density band via `design_tokens.density`), emitted by root_block.
SHELL_SCALE = {
    "--ps-measure-page": "980px",              # DESIGN_SPEC Part 6 / index.html .wrap
    "--ps-gutter": "clamp(20px, 4vw, 56px)",   # index.html .wrap fluid gutters
    "--ps-pad-tight": "12px",
    "--ps-gap": "24px",                        # DESIGN_SPEC Part 0: section gap 24
    "--ps-gap-tight": "8px",
    "--ps-gap-section": "32px",                # top step of the Part 0 gap set — language sections
    "--ps-type-title": "28px",                 # HIG Title 1 tier
    "--ps-type-h2": "20px",                    # HIG Title 3 — the missing heading tier
    "--ps-type-body": "15px",
    "--ps-type-sub": "13px",
    "--ps-measure": "76ch",
}

# The role tokens the chrome references — every one resolved from the profile (provenance == resolve_tokens).
_ROLES = ("backdrop", "surface", "surface-raised", "ink-strong", "ink", "ink-dim",
          "accent", "hairline", "status-success", "status-warning", "status-danger")


def _px(value) -> str:
    return f"{value}px" if isinstance(value, (int, float)) else str(value)


def root_block(profile: str, profile_data: dict | None = None) -> str:
    """The `:root { … }` token declaration block: the language's resolved colour/radius/font tokens +
    the shared IA scale. Every host-chrome rule references these vars — this block is the ONLY place a
    literal value appears, and the provenance gate pins each var to its real source."""
    from scripts.rendering.design import loader

    tok = loader.resolve_tokens(profile)
    color = tok["color"]
    radius = tok.get("radius", {})
    decls = {f"--{role}": color[role] for role in _ROLES}
    decls["--radius-panel"] = _px(radius.get("panel", 12))
    decls["--radius-tile"] = _px(radius.get("tile", 8))
    decls["--font-sans"] = tok.get("font", {}).get("family", "sans-serif")
    # panel padding is the LANGUAGE'S OWN cited density band (apple-dark 'airy' 32 / carbon
    # 'compact' 20 / liquid-glass 'medium' 28 — design_tokens.THEME_IA, grounded per language),
    # not a minted constant (design-audit #7). Provenance-pinned like every other :root var.
    from scripts.rendering import design_tokens as _dt
    decls["--ps-pad"] = _px(_dt.density(profile)["panel_pad"])
    decls.update(SHELL_SCALE)
    body = "\n".join(f"  {k}: {v};" for k, v in decls.items())
    return f":root {{\n{body}\n}}"


def shell_css(profile: str) -> str:
    """The host-chrome CSS. After the `:root` block is stripped, EVERY value here is a `var()` (colour
    from a profile token, spacing/size from the IA scale) — only a `1px` hairline border width is bare.
    That is the token-only half of the honest gate."""
    ns = f"ps-{profile}"
    return "\n".join([
        root_block(profile),
        f".{ns} {{ background: var(--backdrop); color: var(--ink); font-family: var(--font-sans);",
        f"  margin: 0; min-height: 100%; }}",
        # ONE centered content column — the audit's root cause was full-bleed sprawl (no container).
        # Measure + gutters are the cited index .wrap values (DESIGN_SPEC Part 6).
        f".{ns} .ps-main {{ max-width: var(--ps-measure-page); margin: 0 auto;",
        f"  padding: var(--ps-gutter); }}",
        f".{ns} .ps-title {{ margin: 0 0 var(--ps-gap-tight); color: var(--ink-strong);",
        f"  font-size: var(--ps-type-title); font-weight: 700; line-height: 1.2; }}",
        f".{ns} .ps-intro {{ margin: 0 0 var(--ps-gap-tight); color: var(--ink-dim);",
        f"  font-size: var(--ps-type-body); line-height: 1.5; max-width: var(--ps-measure); }}",
        f".{ns} .ps-crumbs {{ margin: 0 0 var(--ps-gap-section); color: var(--ink-dim);",
        f"  font-size: var(--ps-type-sub); }}",
        f".{ns} .ps-crumbs a {{ color: var(--accent); text-decoration: none; }}",
        f".{ns} .ps-panel {{ background: var(--surface); border: 1px solid var(--hairline);",
        f"  border-radius: var(--radius-panel); padding: var(--ps-pad); margin: 0 0 var(--ps-gap); }}",
        f".{ns} .ps-panel-h {{ margin: 0 0 var(--ps-pad-tight); color: var(--ink-strong);",
        f"  font-size: var(--ps-type-h2); font-weight: 600; }}",
    ])


# codex A3 #2: injected content (body_html / section bodies) must never carry the shell's own
# reserved classes — a fake `ps-title` could spoof the global-regex shell facts. `\bps-` inside a
# class attribute only (a word merely containing "ps-", e.g. `caps-lock`, is untouched).
_INJECTED_PS = _re.compile(r'class\s*=\s*["\'][^"\']*\bps-')


def render_page_shell(
    profile: str,
    *,
    title: str,
    intro: str,
    breadcrumbs: list[tuple[str, str]],
    sections: list[tuple[str, str]] | None = None,
    body_html: str = "",
    prefix_html: str = "",
    glossary=None,
    profile_data: dict | None = None,
) -> tuple[str, str]:
    """Return `(html, css)` for a page framed in `profile`'s design language.

    `breadcrumbs` = `[(label, href), …]` (the orientation row). `sections` = `[(heading, body), …]`
    (each a token-only `.ps-panel`); `body_html` = raw content a page structures itself (rendered with the
    shell's tokens) — a page uses one or the other. `prefix_html` = content a page needs as the FIRST
    children inside the shell root, before the title (the studio's pure-CSS switcher radios, whose
    `:checked ~` sibling selectors must precede the stages they reveal). The chrome (bg/header/crumbs/
    panels) is token-only + governed; all injected content is guarded (no shell-reserved ps-* classes)."""
    ns = f"ps-{profile}"
    for blob in (prefix_html, body_html, *(body for _, body in (sections or []))):
        if blob and _INJECTED_PS.search(blob):
            raise ValueError(
                "injected content carries a shell-reserved ps-* class — the shell anatomy "
                "(ps-title/ps-crumbs/ps-panel/…) may only be rendered by render_page_shell itself "
                "(codex A3 #2: an injected ps-title could spoof the page-shell facts)")
    crumbs = " · ".join(f'<a href="{_html.escape(href)}">{_html.escape(label)}</a>'
                        for label, href in breadcrumbs)
    panels = "".join(
        f'<section class="ps-panel"><h2 class="ps-panel-h">{_html.escape(heading)}</h2>{body}</section>'
        for heading, body in (sections or []))
    html = (
        f'<div class="{ns}">'
        f'<div class="ps-main">'
        f'{prefix_html}'
        f'<h1 class="ps-title">{_html.escape(title)}</h1>'
        f'<p class="ps-intro">{_html.escape(intro)}</p>'
        f'<p class="ps-crumbs">{crumbs}</p>'
        f'{panels}'
        f'{body_html}'
        f'</div>'
        f'</div>'
    )
    return html, shell_css(profile)

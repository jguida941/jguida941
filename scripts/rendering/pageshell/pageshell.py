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


# The shared shell IA scale — the chrome's spacing + type rhythm (docs/design/pageshell.md §3, cited to
# DESIGN_SPEC Part 0's 4px grid + type ramp). Consistent across languages so the site reads as ONE
# product; per-language variation is carried by the COLOUR + RADIUS tokens, not the rhythm.
SHELL_SCALE = {
    "--ps-pad": "24px",
    "--ps-pad-tight": "12px",
    "--ps-gap": "16px",
    "--ps-gap-tight": "8px",
    "--ps-type-title": "26px",
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
        f"  margin: 0; min-height: 100%; padding: var(--ps-pad); }}",
        f".{ns} .ps-title {{ margin: 0 0 var(--ps-gap-tight); color: var(--ink-strong);",
        f"  font-size: var(--ps-type-title); font-weight: 700; line-height: 1.2; }}",
        f".{ns} .ps-intro {{ margin: 0 0 var(--ps-gap-tight); color: var(--ink-dim);",
        f"  font-size: var(--ps-type-body); line-height: 1.5; max-width: var(--ps-measure); }}",
        f".{ns} .ps-crumbs {{ margin: 0 0 var(--ps-pad); color: var(--ink-dim);",
        f"  font-size: var(--ps-type-sub); }}",
        f".{ns} .ps-crumbs a {{ color: var(--accent); text-decoration: none; }}",
        f".{ns} .ps-panel {{ background: var(--surface); border: 1px solid var(--hairline);",
        f"  border-radius: var(--radius-panel); padding: var(--ps-pad); margin: 0 0 var(--ps-gap); }}",
        f".{ns} .ps-panel-h {{ margin: 0 0 var(--ps-pad-tight); color: var(--ink-strong);",
        f"  font-size: var(--ps-type-body); font-weight: 600; }}",
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
    glossary=None,
    profile_data: dict | None = None,
) -> tuple[str, str]:
    """Return `(html, css)` for a page framed in `profile`'s design language.

    `breadcrumbs` = `[(label, href), …]` (the orientation row). `sections` = `[(heading, body), …]`
    (each a token-only `.ps-panel`); `body_html` = raw content a page structures itself (rendered with the
    shell's tokens) — a page uses one or the other. The chrome (bg/header/crumbs/panels) is token-only +
    governed; the injected content is the caller's specimens, rendered in their own languages."""
    ns = f"ps-{profile}"
    for blob in (body_html, *(body for _, body in (sections or []))):
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
        f'<h1 class="ps-title">{_html.escape(title)}</h1>'
        f'<p class="ps-intro">{_html.escape(intro)}</p>'
        f'<p class="ps-crumbs">{crumbs}</p>'
        f'{panels}'
        f'{body_html}'
        f'</div>'
    )
    return html, shell_css(profile)

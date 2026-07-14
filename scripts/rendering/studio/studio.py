"""P5-STUDIO — the interactive design-system studio page (`site/studio.html`).

`render_studio()` is a PURE, deterministic (drift-guarded) function: it renders each active language's
full website archetype (`render_archetype`) and a live LANGUAGE SWITCHER implemented in PURE CSS
(radio `:checked` reveals the matching archetype) — ZERO JavaScript, so there is no verdict logic to
audit and every visible byte is committed + drift-guarded. Slice 2 = see + live-switch the languages;
the governed component swap (one Python decider embedded + looked-up) lands in the next slice. This is
the design-language surface — separate from the builder scorecard.

P5-CHROME A5: the studio's own CHROME is the governed apple-dark page-shell (`render_page_shell`), not
hand-written dark CSS — the design surface is itself a rendered instance of a design language, and its
switcher tabs / swap options derive from that language's tokens (so it follows the same process it
showcases). The pure-CSS switcher radios ride in as the shell root's FIRST children (`prefix_html`) so
their `:checked ~` sibling selectors keep reaching the switcher + stages that follow; the switcher/swap
CONTENT palette is token-only beyond a CLOSED structural allowlist (codex A3 #1). Pure + deterministic
(drift-guarded). candidate_only.
"""
from __future__ import annotations

import html as _html
import json
import re
from pathlib import Path

_COMPONENTS = ("button", "chip", "card")


def _root() -> Path:
    for p in Path(__file__).resolve().parents:
        if (p / "contracts" / "design_profiles").is_dir():
            return p
    raise RuntimeError("repo root not found")


def scope_css(css: str, scope: str) -> str:
    """Prefix every rule's selector(s) with `.{scope} ` so a pre-rendered archetype variant cannot
    collide with another that reuses the same component classes (`.btn-{base}-*` etc.) — codex's
    per-fragment namespacing. Our generated CSS is flat rules (no @media/nesting)."""
    out = []
    for rule in css.split("}"):
        rule = rule.strip()
        if "{" not in rule:
            continue
        sel, body = rule.split("{", 1)
        scoped = ", ".join(f".{scope} {s.strip()}" for s in sel.split(",") if s.strip())
        out.append(f"{scoped} {{{body}}}")
    return "\n".join(out)


def _active_profiles() -> list[str]:
    idx = _root() / "contracts" / "design_profiles" / "_index.json"
    import json
    return json.loads(idx.read_text(encoding="utf-8"))["active_design_profiles"]


# The frozen swap toggle: DOM toggling + a STUDIO_SPACE lookup ONLY. Zero admissibility/conformance
# arithmetic (the Python decider is the one source; this re-indexes it, never recomputes a verdict).
_STUDIO_JS = """
(function () {
  var SPACE = window.STUDIO_SPACE || [];
  function admissible(base, comp, src) {
    for (var i = 0; i < SPACE.length; i++) {
      var c = SPACE[i];
      if (c.base === base && c.component === comp && c.source === src) return c.admissible === true;
    }
    return false;
  }
  document.querySelectorAll('.swap-opt').forEach(function (opt) {
    opt.addEventListener('click', function () {
      if (opt.hasAttribute('disabled')) return;
      var base = opt.getAttribute('data-base');
      var comp = opt.getAttribute('data-component');
      var src = opt.getAttribute('data-source');
      if (src !== base && !admissible(base, comp, src)) return;   // never activate an inadmissible cell
      var key = (src === base) ? (base + '-base') : (base + '-' + comp + '-' + src);
      var stage = opt.closest('.stage');
      stage.querySelectorAll('.variant').forEach(function (v) {
        v.hidden = (v.getAttribute('data-variant') !== key);
      });
      stage.querySelectorAll('.swap-opt').forEach(function (o) { o.classList.remove('active'); });
      opt.classList.add('active');
    });
  });
})();
""".strip()


# The studio CHROME is the governed page-shell (apple-dark house); its CONTENT palette (the switcher tabs +
# the component-swap controls) derives from that shell's tokens — so the design surface follows the same
# process it showcases (the twin of the showcase/settings adoptions).
HOUSE = "apple-dark"

# Content CSS (the pure-CSS switcher + the swap controls live INSIDE the governed shell). Every colour is a
# shell token var(): the tabs/options take var(--surface)/var(--ink) on a var(--hairline) hairline; the
# active tab/option flips to var(--accent) bg + var(--backdrop) ink; a disabled (unconstructable) option is
# var(--status-danger) ink on var(--surface), kept line-through; hints/labels are var(--ink-dim). Only
# structural non-colour px/keywords remain — pinned in the allowlist below and scanned by content_offtokens
# (the same machinery as the shell gate). The per-language `:checked ~` reveal + active-tab rules stay in the
# generated switch_css (the switch MECHANISM, in the specimens' own DOM) — not this scanned chrome.
_CONTENT_CSS = """
.lang-radio { position: absolute; opacity: 0; pointer-events: none; }
.switcher { display: flex; gap: var(--ps-gap-tight); flex-wrap: wrap; margin: 0 0 var(--ps-gap); }
.lang-tab { padding: var(--ps-gap-tight) var(--ps-pad); border: 1px solid var(--hairline);
  border-radius: 999px; cursor: pointer; font-weight: 600; font-size: var(--ps-type-sub);
  color: var(--ink); background: var(--surface); user-select: none; }
.lang-radio:focus-visible ~ .switcher .lang-tab { outline: 2px solid var(--accent); }
.stages { position: relative; }
.stage { display: none; }
.swap-controls { margin: 0 0 var(--ps-gap); padding: var(--ps-pad-tight) var(--ps-pad);
  border: 1px solid var(--hairline); border-radius: var(--radius-panel); background: var(--surface); }
.swap-hint { margin: 0 0 var(--ps-gap-tight); color: var(--ink-dim); font-size: var(--ps-type-sub); }
.swap-row { display: flex; align-items: center; gap: var(--ps-gap-tight); flex-wrap: wrap; margin: 0 0 var(--ps-gap-tight); }
.swap-label { width: 64px; color: var(--ink-dim); font-family: ui-monospace, monospace; font-size: var(--ps-type-sub); }
.swap-opts { display: flex; gap: var(--ps-gap-tight); flex-wrap: wrap; }
.swap-opt { padding: var(--ps-gap-tight) var(--ps-pad-tight); border: 1px solid var(--hairline);
  border-radius: 999px; cursor: pointer; font-weight: 600; font-size: var(--ps-type-sub);
  color: var(--ink); background: var(--surface); }
.swap-opt.active { background: var(--accent); color: var(--backdrop); border-color: var(--accent); }
.swap-opt[disabled] { color: var(--status-danger); background: var(--surface); cursor: not-allowed;
  text-decoration: line-through; }
.variant[hidden] { display: none; }
""".strip()

# The CLOSED structural allowlist for _CONTENT_CSS (codex A3 #1): the ONLY non-token literals the content may
# carry, each a LAYOUT (never colour) decision. Anything else — a colour in any form, an off-list px — reddens
# StudioChromeContract; the allowlist is the scan's only escape and it can never admit a colour.
_CONTENT_ALLOWED_PX = frozenset({
    "2px",      # .lang-tab focus-visible outline width — the keyboard focus ring (not a scale step)
    "64px",     # .swap-label fixed column width — aligns the button/chip/card option rows
    "999px",    # .lang-tab / .swap-opt pill radius — structural "fully round", not a scale step
})
_CONTENT_ALLOWED_WORDS = frozenset({
    "ui-monospace", "monospace",   # the code-face stack for .swap-label (no colour choice)
    "not-allowed",                 # .swap-opt[disabled] cursor — the unconstructable affordance
})

# The intro (the pre-shell `.sub` text, verbatim) — framed by the shell as `.ps-intro`.
_INTRO = ("Pick a design language and see a real website built entirely in it — nav, hero, tag chips, "
          "buttons, and a grouped metric card, each from that language's own cited design doc. This is "
          "the design-language surface, separate from the builder scorecard.")


def render_studio() -> str:
    """Pure + deterministic: the active languages, their archetypes, AND the governed component swap.
    Per base, a default archetype + a pre-rendered (CSS-namespaced) archetype variant for each
    ADMISSIBLE single-component swap; inadmissible sources render disabled/unconstructable (no
    variant target). The admissible space is embedded VERBATIM from `admissible_space()` (the ONE
    Python decider); a frozen JS toggle only re-indexes it by lookup — never recomputes a verdict."""
    import copy

    from scripts.quality.settings_admissibility import admissible_space, compose
    from scripts.rendering.design import loader
    from scripts.rendering.webkit.archetype import render_archetype

    actives = _active_profiles()
    space = admissible_space()
    admissible = {(c["base"], c["component"], c["source"]): c["admissible"] for c in space}

    radios, tabs, stages, arch_css, switch_css = [], [], [], [], []
    for i, base in enumerate(actives):
        safe = _html.escape(base)
        checked = " checked" if i == 0 else ""
        radios.append(f'<input type="radio" name="studio-lang" id="lang-{safe}" class="lang-radio" '
                      f'data-dom-owner="page.studio"{checked}>')
        tabs.append(f'<label for="lang-{safe}" class="lang-tab" '
                    f'data-dom-owner="page.studio">{safe}</label>')
        switch_css.append(f'#lang-{safe}:checked ~ .stages .stage[data-lang="{safe}"] {{ display: block; }}')
        switch_css.append(f'#lang-{safe}:checked ~ .switcher label[for="lang-{safe}"] '
                          f'{{ background: var(--accent); color: var(--backdrop); border-color: var(--accent); }}')

        variants, rows = [], []
        bh, bc = render_archetype(base)                       # the base default (no swap)
        arch_css.append(scope_css(bc, f"var-{safe}-base"))
        variants.append(f'<div class="variant var-{safe}-base" data-dom-owner="page.studio" '
                        f'data-variant="{safe}-base">{bh}</div>')
        for comp in _COMPONENTS:
            opts = []
            for src in actives:
                ssrc = _html.escape(src)
                if src == base:
                    opts.append(f'<button type="button" class="swap-opt active" '
                                f'data-dom-owner="page.studio" data-base="{safe}" '
                                f'data-component="{comp}" data-source="{ssrc}">{ssrc} · base</button>')
                elif admissible.get((base, comp, src), False):
                    key, scope = f"{safe}-{comp}-{ssrc}", f"var-{safe}-{comp}-{ssrc}"
                    spec = copy.deepcopy(loader.load(src)["components"][comp])
                    vh, vc = render_archetype(base, profile_data=compose(base, {comp: spec}))
                    arch_css.append(scope_css(vc, scope))
                    variants.append(f'<div class="variant {scope}" data-dom-owner="page.studio" '
                                    f'data-variant="{key}" hidden>{vh}</div>')
                    opts.append(f'<button type="button" class="swap-opt" '
                                f'data-dom-owner="page.studio" data-base="{safe}" '
                                f'data-component="{comp}" data-source="{ssrc}">{ssrc}</button>')
                else:
                    opts.append(f'<button type="button" class="swap-opt" '
                                f'data-dom-owner="page.studio" data-base="{safe}" '
                                f'data-component="{comp}" data-source="{ssrc}" disabled '
                                f'title="unconstructable — a {ssrc} {comp} is a valid instance of no '
                                f'design language in a {safe} composition">{ssrc} ✕</button>')
            rows.append(f'<div class="swap-row" data-dom-owner="page.studio">'
                        f'<span class="swap-label" data-dom-owner="page.studio">{comp}</span>'
                        f'<span class="swap-opts" data-dom-owner="page.studio">'
                        f'{"".join(opts)}</span></div>')
        stages.append(
            f'<section class="stage" data-dom-owner="page.studio" data-lang="{safe}">'
            f'<div class="swap-controls" data-dom-owner="page.studio">'
            f'<p class="swap-hint" data-dom-owner="page.studio">swap a component to another language '
            f'— only admissible swaps are enabled; an invalid mix is unconstructable</p>'
            f'{"".join(rows)}</div>'
            f'<div class="variants" data-dom-owner="page.studio">{"".join(variants)}</div></section>')

    from scripts.rendering.pageshell.pageshell import (render_page_shell,
                                                       theme_continuity_script_tag)
    from scripts.rendering.webkit.components import render_switchable_nav

    # The switcher + stages + the (verdict-free) scripts are the page's structured content; the radios ride
    # in as the shell root's FIRST children so their `:checked ~` sibling selectors keep reaching them.
    body_html = (
        f'<div class="switcher" data-dom-owner="page.studio">{"".join(tabs)}</div>'
        f'<div class="stages" data-dom-owner="page.studio">{"".join(stages)}</div>'
        # the ONE decider, embedded verbatim; the frozen toggle only looks it up
        f'<script>window.STUDIO_SPACE = {json.dumps(space, sort_keys=True)};</script>'
        f'<script>{_STUDIO_JS}</script>'
    )
    _nav_links = [("home", "index.html"), ("showcase", "showcase.html"),
                  ("studio", "studio.html"), ("settings", "settings.html")]
    nav_html, nav_css = render_switchable_nav(HOUSE, _nav_links, active="studio.html")
    shell_html, shell_style = render_page_shell(
        HOUSE,
        title="Design-language studio",
        intro=_INTRO,
        breadcrumbs=[("home", "index.html"), ("showcase", "showcase.html"), ("settings", "settings.html")],
        prefix_html="".join(radios) + nav_html,
        body_html=body_html,
    )
    return (
        "<!doctype html>\n"
        f'<html lang="en" data-house-theme="{HOUSE}"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"{theme_continuity_script_tag()}\n"
        "<title>Design-language studio</title>\n"
        f"<style>* {{ box-sizing: border-box; }}\n"
        f"html, body {{ height: 100%; margin: 0; }}\n{shell_style}\n{nav_css}\n{_CONTENT_CSS}\n"
        # the switch MECHANISM (pure-CSS reveal + active-tab) and the pre-rendered specimen archetypes,
        # in the specimens' own languages — NOT the scanned page chrome
        + "\n".join(switch_css) + "\n" + "\n".join(arch_css) + "</style>\n"
        "</head><body>\n"
        + shell_html
        + "\n</body></html>\n"
    )


def write_studio(output_path: str = "site/studio.html") -> str:
    html = render_studio()
    out = Path(output_path)
    if not out.is_absolute():
        out = _root() / output_path
    out.write_text(html, encoding="utf-8")
    return html


if __name__ == "__main__":
    write_studio()

"""P5-STUDIO — the interactive design-system studio page (`site/studio.html`).

`render_studio()` is a PURE, deterministic (drift-guarded) function: it renders each active language's
full website archetype (`render_archetype`) and a live LANGUAGE SWITCHER implemented in PURE CSS
(radio `:checked` reveals the matching archetype) — ZERO JavaScript, so there is no verdict logic to
audit and every visible byte is committed + drift-guarded. Slice 2 = see + live-switch the languages;
the governed component swap (one Python decider embedded + looked-up) lands in the next slice. This is
the design-language surface — separate from the builder scorecard. candidate_only.
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
        radios.append(f'<input type="radio" name="studio-lang" id="lang-{safe}" class="lang-radio"{checked}>')
        tabs.append(f'<label for="lang-{safe}" class="lang-tab">{safe}</label>')
        switch_css.append(f'#lang-{safe}:checked ~ .stages .stage[data-lang="{safe}"] {{ display: block; }}')
        switch_css.append(f'#lang-{safe}:checked ~ .switcher label[for="lang-{safe}"] '
                          f'{{ background: #e8e8ee; color: #0a0a0f; border-color: #e8e8ee; }}')

        variants, rows = [], []
        bh, bc = render_archetype(base)                       # the base default (no swap)
        arch_css.append(scope_css(bc, f"var-{safe}-base"))
        variants.append(f'<div class="variant var-{safe}-base" data-variant="{safe}-base">{bh}</div>')
        for comp in _COMPONENTS:
            opts = []
            for src in actives:
                ssrc = _html.escape(src)
                if src == base:
                    opts.append(f'<button type="button" class="swap-opt active" data-base="{safe}" '
                                f'data-component="{comp}" data-source="{ssrc}">{ssrc} · base</button>')
                elif admissible.get((base, comp, src), False):
                    key, scope = f"{safe}-{comp}-{ssrc}", f"var-{safe}-{comp}-{ssrc}"
                    spec = copy.deepcopy(loader.load(src)["components"][comp])
                    vh, vc = render_archetype(base, profile_data=compose(base, {comp: spec}))
                    arch_css.append(scope_css(vc, scope))
                    variants.append(f'<div class="variant {scope}" data-variant="{key}" hidden>{vh}</div>')
                    opts.append(f'<button type="button" class="swap-opt" data-base="{safe}" '
                                f'data-component="{comp}" data-source="{ssrc}">{ssrc}</button>')
                else:
                    opts.append(f'<button type="button" class="swap-opt" data-base="{safe}" '
                                f'data-component="{comp}" data-source="{ssrc}" disabled '
                                f'title="unconstructable — a {ssrc} {comp} is a valid instance of no '
                                f'design language in a {safe} composition">{ssrc} ✕</button>')
            rows.append(f'<div class="swap-row"><span class="swap-label">{comp}</span>'
                        f'<span class="swap-opts">{"".join(opts)}</span></div>')
        stages.append(
            f'<section class="stage" data-lang="{safe}">'
            f'<div class="swap-controls"><p class="swap-hint">swap a component to another language '
            f'— only admissible swaps are enabled; an invalid mix is unconstructable</p>'
            f'{"".join(rows)}</div>'
            f'<div class="variants">{"".join(variants)}</div></section>')

    page_css = """
:root { color-scheme: dark; }
* { box-sizing: border-box; }
body { margin: 0; padding: 28px; background: #08080c; color: #e8e8ee;
  font: 15px/1.5 -apple-system, system-ui, 'Segoe UI', sans-serif; }
h1 { font-size: 26px; margin: 0 0 4px; }
.sub { color: #9a9aa6; margin: 0 0 6px; max-width: 76ch; }
.crumbs { color: #7f7f8c; font-size: 13px; margin: 0 0 20px; }
.crumbs a { color: #7dcfff; text-decoration: none; }
.lang-radio { position: absolute; opacity: 0; pointer-events: none; }
.switcher { display: flex; gap: 8px; flex-wrap: wrap; margin: 0 0 20px; }
.lang-tab { padding: 8px 16px; border: 1px solid #23232e; border-radius: 999px; cursor: pointer;
  font-weight: 600; font-size: 13px; color: #c9c9d6; background: #12121a; user-select: none; }
.lang-radio:focus-visible + .switcher .lang-tab { outline: 2px solid #7dcfff; }
.stages { position: relative; }
.stage { display: none; }
.swap-controls { margin: 0 0 18px; padding: 14px 16px; border: 1px solid #23232e; border-radius: 12px;
  background: #101018; }
.swap-hint { margin: 0 0 10px; color: #9a9aa6; font-size: 12px; }
.swap-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin: 0 0 8px; }
.swap-label { width: 64px; color: #c9c9d6; font-family: ui-monospace, monospace; font-size: 12px; }
.swap-opts { display: flex; gap: 6px; flex-wrap: wrap; }
.swap-opt { padding: 5px 12px; border: 1px solid #23232e; border-radius: 999px; cursor: pointer;
  font: 600 12px/1 -apple-system, system-ui, sans-serif; color: #c9c9d6; background: #16161c; }
.swap-opt.active { background: #7dcfff; color: #08080c; border-color: #7dcfff; }
.swap-opt[disabled] { color: #6b1f2b; background: #1a1013; border-color: #3a1a20; cursor: not-allowed;
  text-decoration: line-through; }
.variant[hidden] { display: none; }
""".strip()

    return (
        "<!doctype html>\n"
        '<html lang="en"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>Design-language studio</title>\n"
        f"<style>{page_css}\n" + "\n".join(switch_css) + "\n" + "\n".join(arch_css) + "</style>\n"
        "</head><body>\n"
        # radios FIRST so the pure-CSS `~` sibling selectors reach the switcher + stages
        + "".join(radios) + "\n"
        "<h1>Design-language studio</h1>\n"
        '<p class="sub">Pick a design language and see a real website built entirely in it — nav, '
        "hero, tag chips, buttons, and a grouped metric card, each from that language's own cited "
        "design doc. This is the design-language surface, separate from the builder scorecard.</p>\n"
        '<p class="crumbs">proof tables: <a href="showcase.html">conformance showcase</a> · '
        '<a href="settings.html">governed settings</a></p>\n'
        f'<div class="switcher">{"".join(tabs)}</div>\n'
        f'<div class="stages">{"".join(stages)}</div>\n'
        # the ONE decider, embedded verbatim; the frozen toggle only looks it up
        f'<script>window.STUDIO_SPACE = {json.dumps(space, sort_keys=True)};</script>\n'
        f"<script>{_STUDIO_JS}</script>\n"
        "</body></html>\n"
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

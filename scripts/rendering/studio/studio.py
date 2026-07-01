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
from pathlib import Path


def _root() -> Path:
    for p in Path(__file__).resolve().parents:
        if (p / "contracts" / "design_profiles").is_dir():
            return p
    raise RuntimeError("repo root not found")


def _active_profiles() -> list[str]:
    idx = _root() / "contracts" / "design_profiles" / "_index.json"
    import json
    return json.loads(idx.read_text(encoding="utf-8"))["active_design_profiles"]


def render_studio() -> str:
    """Pure: the active languages + their archetypes -> the studio HTML (deterministic; pure-CSS
    switcher, no JS)."""
    from scripts.rendering.webkit.archetype import render_archetype

    actives = _active_profiles()
    radios, tabs, stages, arch_css, switch_css = [], [], [], [], []
    for i, name in enumerate(actives):
        safe = _html.escape(name)
        checked = " checked" if i == 0 else ""
        radios.append(f'<input type="radio" name="studio-lang" id="lang-{safe}" class="lang-radio"{checked}>')
        tabs.append(f'<label for="lang-{safe}" class="lang-tab">{safe}</label>')
        ah, ac = render_archetype(name)
        stages.append(f'<section class="stage" data-lang="{safe}">{ah}</section>')
        arch_css.append(ac)
        # PURE CSS: the checked radio reveals its stage + lights its tab (sibling selectors)
        switch_css.append(f'#lang-{safe}:checked ~ .stages .stage[data-lang="{safe}"] {{ display: block; }}')
        switch_css.append(f'#lang-{safe}:checked ~ .switcher label[for="lang-{safe}"] '
                          f'{{ background: #e8e8ee; color: #0a0a0f; border-color: #e8e8ee; }}')

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

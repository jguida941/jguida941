"""P5-SETTINGS view — `render_settings()` -> `site/settings.html`. The governed control plane made
visible: it DISPLAYS the admissible combo-space that `scripts/quality/settings_admissibility.py`
COMPUTES (the ONE Python decider) — per base language, which component swaps are admissible and
which are UNCONSTRUCTABLE. The page carries NO verdict JS of its own (no `<script>`); the Python
module is the single source of the decision.

P5-CHROME A4: the page's own CHROME is the governed apple-dark page-shell (`render_page_shell`), not
hand-written dark CSS — the control plane is itself a rendered instance of a design language, and its
verdict pills derive from that language's status tokens (so it follows the very process it governs).
Its CONTENT palette (the law panel body, the per-base grids, the pills) is token-only beyond a CLOSED
structural allowlist (codex A3 #1). Pure + deterministic (drift-guarded). candidate_only."""
from __future__ import annotations

import html as _html
from pathlib import Path


def _root() -> Path:
    for p in Path(__file__).resolve().parents:
        if (p / "contracts" / "design_profiles").is_dir():
            return p
    raise RuntimeError("repo root not found")


_COMPONENTS = ("button", "chip", "card")

# The settings CHROME is the governed page-shell (apple-dark house); its CONTENT palette (the law panel,
# the per-base grids, the verdict pills) derives from that shell's tokens — so the control plane follows
# the same process it governs.
HOUSE = "apple-dark"

# Content CSS (the law panel body + admissibility grids + verdict pills live INSIDE the governed shell).
# Every colour is a shell token var(); the verdict pills reuse the language's own status roles (drop the
# extra hand border, like the showcase badges). Only structural non-colour px/keywords remain — pinned in
# the allowlist below and scanned by content_offtokens (the same machinery as the shell gate).
_CONTENT_CSS = """
.law { color: var(--ink); font-size: var(--ps-type-sub); }
.law b { color: var(--accent); }
.base { background: var(--surface); border: 1px solid var(--hairline); border-radius: var(--radius-panel);
  padding: var(--ps-pad); margin: 0 0 var(--ps-gap); }
.base h2 { margin: 0 0 var(--ps-gap-tight); font-size: var(--ps-type-h2); color: var(--ink-strong); }
.hint { color: var(--ink-dim); font-size: var(--ps-type-sub); margin: 0 0 var(--ps-gap); }
.table-scroll { overflow-x: auto; }
table.grid { width: 100%; border-collapse: collapse; font-size: var(--ps-type-sub); }
.grid th { text-align: left; color: var(--ink-dim); font-weight: 600; padding: var(--ps-gap-tight) var(--ps-pad-tight);
  border-bottom: 1px solid var(--hairline); }
.grid td { padding: var(--ps-pad-tight); border-bottom: 1px solid var(--hairline); vertical-align: top; }
.comp { font-family: ui-monospace, monospace; color: var(--ink); white-space: nowrap; }
.cell .src { display: block; color: var(--ink); font-family: ui-monospace, monospace; margin-bottom: var(--ps-gap-tight); }
.verdict { display: inline-block; padding: 2px var(--ps-pad-tight); border-radius: 999px; font-weight: 600;
  font-size: var(--ps-type-sub); white-space: nowrap; }
.verdict.ok { background: var(--status-success); color: var(--backdrop); }
.verdict.no { background: var(--status-danger); color: var(--backdrop); }
""".strip()

# The CLOSED structural allowlist for _CONTENT_CSS (codex A3 #1): the ONLY non-token literals the content
# may carry, each a LAYOUT (never colour) decision. Anything else — a colour in any form, an off-list px —
# reddens SettingsChromeContract; the allowlist is the scan's only escape and it can never admit a colour.
_CONTENT_ALLOWED_PX = frozenset({
    "2px",      # .verdict pill vertical padding nudge (mirrors the showcase .badge)
    "999px",    # .verdict pill radius — structural "fully round", not a scale step
})
_CONTENT_ALLOWED_WORDS = frozenset({
    "ui-monospace", "monospace",   # the code-face stack for .comp / .cell .src (no colour choice)
    "inline-block",                # the .verdict pill display box
})

# The intro (the pre-shell `.sub` text, verbatim) — framed by the shell as `.ps-intro`.
_INTRO = ("Compose a design language: pick a base, then swap any component to another language. "
          "This is the design surface — separate from the builder scorecard.")

# The law text (the pre-shell `.law` inner HTML, verbatim) — rendered as a governed shell panel; only its
# emphasised term is re-tinted to the shell's accent token via `.law b`.
_LAW_HTML = (
    '<div class="law">An <b>invalid combination is unconstructable</b>. A swap is admissible '
    "ONLY if the composed component, as rendered, is a FULL valid instance of some active design "
    "language — a partial mix that belongs to no language (e.g. a frosted material on a square "
    "0-radius card) is refused. The verdict below is computed by ONE Python source "
    "(<code>scripts/quality/settings_admissibility.py</code>), routed through the real "
    "render → conform path; this page only displays it (no verdict JS).</div>")


def render_settings() -> str:
    """Pure: the computed admissible space -> the governed control-plane HTML, framed in the governed
    apple-dark page-shell (deterministic; no JS)."""
    from scripts.quality.settings_admissibility import active_profiles, admissible_space
    from scripts.rendering.pageshell.pageshell import render_page_shell
    from scripts.rendering.webkit.components import render_nav

    actives = sorted(active_profiles())
    space = {(c["base"], c["component"], c["source"]): c["admissible"] for c in admissible_space()}

    base_sections = []
    for base in actives:
        rows = []
        for comp in _COMPONENTS:
            cells = []
            for source in actives:
                ok = space.get((base, comp, source), False)
                own = source == base
                cls = "ok" if ok else "no"
                mark = "admissible" if ok else "unconstructable"
                note = " (base)" if own else ""
                cells.append(
                    f'<td class="cell {cls}"><span class="src">{_html.escape(source)}{note}</span>'
                    f'<span class="verdict {cls}">{mark}</span></td>')
            rows.append(f'<tr><th class="comp">{comp}</th>{"".join(cells)}</tr>')
        head = "".join(f"<th>{_html.escape(s)}</th>" for s in actives)
        base_sections.append(
            f'<section class="base" data-base="{_html.escape(base)}">'
            f'<h2>base: {_html.escape(base)}</h2>'
            f'<p class="hint">swap each component to another language; only ADMISSIBLE swaps can be applied</p>'
            f'<div class="table-scroll"><table class="grid">'
            f'<thead><tr><th>component ↓ / source →</th>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div></section>')

    _nav_links = [("home", "index.html"), ("showcase", "showcase.html"),
                  ("studio", "studio.html"), ("settings", "settings.html")]
    nav_html, nav_css = render_nav(HOUSE, _nav_links, active="settings.html")
    shell_html, shell_style = render_page_shell(
        HOUSE,
        title="Governed control plane",
        intro=_INTRO,
        breadcrumbs=[("home", "index.html"), ("showcase", "showcase.html"), ("studio", "studio.html")],
        prefix_html=nav_html,
        sections=[("The law", _LAW_HTML)],
        body_html="\n".join(base_sections),
    )
    return (
        "<!doctype html>\n"
        '<html lang="en"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>Design-language settings — governed control plane</title>\n"
        f"<style>:root {{ color-scheme: dark; }}\n* {{ box-sizing: border-box; }}\n"
        f"html, body {{ height: 100%; margin: 0; }}\n{shell_style}\n{nav_css}\n{_CONTENT_CSS}\n"
        "</style>\n"
        "</head><body>\n"
        + shell_html
        + "\n</body></html>\n"
    )


def write_settings(output_path: str = "site/settings.html") -> str:
    html = render_settings()
    out = Path(output_path)
    if not out.is_absolute():
        out = _root() / output_path
    out.write_text(html, encoding="utf-8")
    return html


if __name__ == "__main__":
    write_settings()

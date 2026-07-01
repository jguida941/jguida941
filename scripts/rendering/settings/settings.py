"""P5-SETTINGS view — `render_settings()` -> `site/settings.html`. The governed control plane made
visible: it DISPLAYS the admissible combo-space that `scripts/quality/settings_admissibility.py`
COMPUTES (the ONE Python decider) — per base language, which component swaps are admissible and
which are UNCONSTRUCTABLE. The page carries NO verdict JS of its own (no `<script>`); the Python
module is the single source of the decision. Pure + deterministic (drift-guarded). candidate_only."""
from __future__ import annotations

import html as _html
from pathlib import Path


def _root() -> Path:
    for p in Path(__file__).resolve().parents:
        if (p / "contracts" / "design_profiles").is_dir():
            return p
    raise RuntimeError("repo root not found")


_COMPONENTS = ("button", "chip", "card")


def render_settings() -> str:
    """Pure: the computed admissible space -> the governed control-plane HTML (deterministic; no JS)."""
    from scripts.quality.settings_admissibility import active_profiles, admissible_space
    actives = sorted(active_profiles())
    space = {(c["base"], c["component"], c["source"]): c["admissible"] for c in admissible_space()}

    sections = []
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
        sections.append(
            f'<section class="base" data-base="{_html.escape(base)}">'
            f'<h2>base: {_html.escape(base)}</h2>'
            f'<p class="hint">swap each component to another language; only ADMISSIBLE swaps can be applied</p>'
            f'<table class="grid"><thead><tr><th>component ↓ / source →</th>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></section>')

    page_css = """
:root { color-scheme: dark; }
* { box-sizing: border-box; }
body { margin: 0; padding: 32px; background: #0a0a0f; color: #e8e8ee;
  font: 15px/1.5 -apple-system, system-ui, 'Segoe UI', sans-serif; }
h1 { font-size: 26px; margin: 0 0 4px; }
.sub { color: #9a9aa6; margin: 0 0 8px; max-width: 74ch; }
.law { margin: 16px 0 28px; padding: 12px 16px; border: 1px solid #23232e; border-radius: 12px;
  background: #12121a; font-size: 13px; color: #c9c9d6; max-width: 90ch; }
.law b { color: #f2d06b; }
.base { margin: 0 0 32px; padding: 20px; border: 1px solid #23232e; border-radius: 16px; background: #101018; }
.base h2 { margin: 0 0 2px; font-size: 18px; }
.hint { color: #9a9aa6; font-size: 12px; margin: 0 0 14px; }
table.grid { width: 100%; border-collapse: collapse; font-size: 13px; }
.grid th { text-align: left; color: #9a9aa6; font-weight: 600; padding: 8px 10px; border-bottom: 1px solid #23232e; }
.grid td { padding: 8px 10px; border-bottom: 1px solid #1a1a24; vertical-align: top; }
.comp { font-family: ui-monospace, 'SF Mono', monospace; color: #c9c9d6; white-space: nowrap; }
.cell .src { display: block; color: #c9c9d6; font-family: ui-monospace, monospace; margin-bottom: 4px; }
.verdict { display: inline-block; padding: 2px 8px; border-radius: 999px; font-weight: 600; font-size: 11px; }
.verdict.ok { background: #0f3d2e; color: #55e0a8; border: 1px solid #1c6b4f; }
.verdict.no { background: #451118; color: #ff8a9b; border: 1px solid #7a1f2b; }
""".strip()

    return (
        "<!doctype html>\n"
        '<html lang="en"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>Design-language settings — governed control plane</title>\n"
        f"<style>{page_css}</style>\n"
        "</head><body>\n"
        "<h1>Governed control plane</h1>\n"
        '<p class="sub">Compose a design language: pick a base, then swap any component to another '
        "language. This is the design surface — separate from the builder scorecard.</p>\n"
        '<div class="law">An <b>invalid combination is unconstructable</b>. A swap is admissible '
        "ONLY if the composed component, as rendered, is a FULL valid instance of some active design "
        "language — a partial mix that belongs to no language (e.g. a frosted material on a square "
        "0-radius card) is refused. The verdict below is computed by ONE Python source "
        "(<code>scripts/quality/settings_admissibility.py</code>), routed through the real "
        "render → conform path; this page only displays it (no verdict JS).</div>\n"
        + "\n".join(sections)
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

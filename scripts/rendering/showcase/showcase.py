"""P5-SHOWCASE 1c — the conformance run RENDERED (the RECEIPT seam made visible).

`render_showcase(receipts)` is a PURE function of the committed conformance receipts (+ the
deterministic webkit renderer): for every active profile it emits its REAL rendered button on
the profile's own backdrop AND a per-invariant verdict table whose status is READ from the
receipt JSON — never recomputed here. The honest three-state legend (axe/ACT lineage): `pass`
/ `fail` (a cell may ship visibly failing) / `candidate` stamped **"cannot certify"** — the
portion automation cannot decide (contrast over glass, motion feel), NOT coupled to any probe
(codex H4). `write_showcase` refreshes each receipt then writes `site/showcase.html`. The
showcase is the design-language surface; it is a SEPARATE concern from the scorecard.
candidate_only — the page mints no authority beyond the receipts it renders.
"""
from __future__ import annotations

import html as _html
import json
from pathlib import Path


def _root() -> Path:
    for p in Path(__file__).resolve().parents:
        if (p / "contracts" / "design_profiles").is_dir():
            return p
    raise RuntimeError("repo root not found")


def _active_profiles() -> list[str]:
    idx = json.loads((_root() / "contracts" / "design_profiles" / "_index.json").read_text(encoding="utf-8"))
    return idx["active_design_profiles"]


def _load_receipts() -> dict:
    out = {}
    for name in _active_profiles():
        p = _root() / "assets" / "receipts" / name / "conformance_receipt.json"
        out[name] = json.loads(p.read_text(encoding="utf-8"))
    return out


# The honest three-state badge text (the verdict is READ from the receipt, never recomputed).
_BADGE_TEXT = {"pass": "pass", "fail": "fail", "candidate": "cannot certify"}


def _signature_variant(btn: dict) -> str:
    """The filled/signature variant to show (Apple's variants[0] is `plain`, not filled)."""
    variants = btn.get("variants", [])
    for v in variants:
        if v in ("prominent", "primary", "filled") or v.endswith("-primary"):
            return v
    return variants[0] if variants else "default"


def _stage_block(profile: str) -> tuple[str, str, str]:
    """Return (scoped_css, stage_html, backdrop) for a profile's signature button + chip rendered
    on its own backdrop, or a graceful placeholder if the profile isn't loadable (receipts are
    always for known profiles, but stay resilient)."""
    try:
        from scripts.rendering.design import loader
        from scripts.rendering.webkit.components import render_button, render_card, render_chip
        prof = loader.load(profile)
        bvar = _signature_variant(prof["components"]["button"])
        btn_html, btn_css = render_button(profile, bvar, "rest")
        cvar = prof["components"]["chip"]["variants"][0]
        chip_html, chip_css = render_chip(profile, cvar, "rest")
        dvar = prof["components"]["card"]["variants"][0]
        card_html, card_css = render_card(profile, dvar, "rest")
        backdrop = loader.resolve_tokens(profile).get("color", {}).get("backdrop", "#000000")
        stage = (f'<div class="stage-row">{btn_html}{chip_html}</div>'
                 f'<div class="stage-row">{card_html}</div>')
        return f"{btn_css}\n{chip_css}\n{card_css}", stage, backdrop
    except Exception:
        return "", '<span class="no-render">[[component-not-rendered]]</span>', "#111111"


def _rows(results: list[dict]) -> str:
    """One <tbody class="aspect-group"> per aspect (D-SHELL-2 L-SHOW-1): rows group by their
    aspect field in FIRST-APPEARANCE order (receipt order preserved within a group), each group
    headed by a subheader th[scope=colgroup] carrying the group's SINGLE hoisted doc cite — the
    per-row doc column died (it repeated one path ~17×). Fail-closed: a row without an aspect is
    a KeyError; a group with MIXED cites raises (hoisting must never silently drop provenance)."""
    groups: dict[str, list[dict]] = {}
    for r in results:
        groups.setdefault(r["aspect"], []).append(r)
    out = []
    for aspect, rows in groups.items():
        cites = sorted({str(r.get("doc_cite", "")) for r in rows})
        if len(cites) != 1:
            raise ValueError(f"aspect group {aspect!r} carries mixed doc cites {cites} — "
                             f"hoisting would lose provenance (regroup or split the aspect)")
        out.append(f'<tbody class="aspect-group" data-aspect="{_html.escape(aspect)}">')
        out.append(f'<tr class="aspect-head"><th colspan="4" scope="colgroup">'
                   f'{_html.escape(aspect)} · <span class="cite">{_html.escape(cites[0])}</span>'
                   f'</th></tr>')
        out.extend(_row(r) for r in rows)
        out.append('</tbody>')
    return "\n".join(out)


def _row(r: dict) -> str:
    if True:
        status = r.get("status")
        if status not in _BADGE_TEXT:               # closed enum — fail closed (codex 1c #3): a
            raise ValueError(                       # malformed status can't inject an attr/class
                f"invariant {r.get('invariant_id')!r} has non-canonical status {status!r} "
                f"(expected one of {sorted(_BADGE_TEXT)})")
        badge = _BADGE_TEXT[status]
        inv = _html.escape(str(r.get("invariant_id", "")))
        law = _html.escape(str(r.get("law", "")))
        cite = _html.escape(str(r.get("doc_cite", "")))
        obligation = r.get("receipt_obligation") or {}
        if r.get("status") == "candidate" and obligation:
            receipt = (
                f'{_html.escape(str(r.get("receipt_status", "pending")))} · '
                f'{_html.escape(str(obligation.get("kind", "")))}<br>'
                f'<code>{_html.escape(str(obligation.get("artifact", "")))}</code>'
            )
        else:
            receipt = ""                            # an empty cell renders EMPTY (L-SHOW-5), never a dash
        return (
            f'<tr data-invariant="{inv}" data-status="{status}">'
            f'<td class="inv">{inv}</td>'
            f'<td class="law">{law}</td>'
            f'<td class="verdict"><span class="badge badge-{status}">{badge}</span></td>'
            f'<td class="receipt">{receipt}</td>'
            f'</tr>'
        )


# The showcase CHROME is the governed page-shell (apple-dark house); its CONTENT palette (legend / verdict
# badges / table) derives from that shell's tokens — so the proof page follows the same process it displays.
HOUSE = "apple-dark"

# Content CSS (the specimen stages + verdict table live INSIDE the governed shell). Every colour is a shell
# token var(); the verdict palette is the language's own status roles. Only structural non-colour px remain.
_CONTENT_CSS = """
.legend { display: flex; gap: var(--ps-gap); flex-wrap: wrap; font-size: var(--ps-type-sub); color: var(--ink); }
.legend b { font-weight: 600; }
.lang { margin: 0 0 var(--ps-gap); padding: var(--ps-pad); border: 1px solid var(--hairline);
  border-radius: var(--radius-panel); background: var(--surface); }
.lang header { display: flex; align-items: baseline; justify-content: space-between; gap: var(--ps-gap); }
.lang h2 { margin: 0 0 var(--ps-pad-tight); font-size: var(--ps-type-h2); color: var(--ink-strong); }
.tally { color: var(--ink-dim); font-size: var(--ps-type-sub); margin: 0; }
.stage { display: flex; flex-direction: column; align-items: center; gap: var(--ps-gap);
  min-height: 96px; padding: var(--ps-pad); margin: var(--ps-gap-tight) 0 var(--ps-gap);
  border-radius: var(--radius-tile); }
.stage-row { display: flex; align-items: center; justify-content: center; gap: var(--ps-gap); flex-wrap: wrap; }
.card-group { min-width: 260px; }
.chip-dismiss { background: transparent; border: 0; color: inherit; cursor: pointer;
  font-size: var(--ps-type-body); line-height: 1; padding: 0 0 0 2px; }
.no-render { color: var(--ink-dim); font-style: italic; }
.table-scroll { overflow-x: auto; }
table.invariants { width: 100%; border-collapse: collapse; font-size: var(--ps-type-sub); }
.invariants th { text-align: left; color: var(--ink-dim); font-weight: 600; padding: var(--ps-gap-tight) var(--ps-pad-tight);
  border-bottom: 1px solid var(--hairline); }
.invariants td { padding: var(--ps-pad-tight); border-bottom: 1px solid var(--hairline); vertical-align: top; }
.inv { font-family: ui-monospace, monospace; color: var(--ink); white-space: nowrap; }
.cite { color: var(--ink-dim); font-family: ui-monospace, monospace; }
.receipt { color: var(--ink-dim); font-size: var(--ps-type-sub); }
.receipt code { color: var(--ink); font-family: ui-monospace, monospace; }
.badge { display: inline-block; padding: 2px var(--ps-pad-tight); border-radius: 999px; font-weight: 600;
  font-size: var(--ps-type-sub); white-space: nowrap; }
.badge-pass { background: transparent; color: var(--status-success); border: 1px solid var(--status-success); }
.badge-fail { background: var(--status-danger); color: var(--backdrop); }
.badge-candidate { background: var(--status-warning); color: var(--backdrop); }
.aspect-head th { text-align: left; color: var(--ink-strong); font-weight: 600;
  font-size: var(--ps-type-sub); padding: var(--ps-gap) var(--ps-pad-tight) var(--ps-gap-tight);
  border-bottom: 1px solid var(--hairline); }
.aspect-head .cite { font-weight: 400; }
""".strip()

# The CLOSED structural allowlist for _CONTENT_CSS (codex A3 #1): the ONLY non-token literals the
# content may carry, each a LAYOUT (never colour) decision. Anything else — a colour in any form,
# an off-list px — reddens ShowcaseChromeContract; the scan is content_offtokens (same machinery as
# the shell gate, with this explicit escape hatch instead of the shell's none).
_CONTENT_ALLOWED_PX = frozenset({
    "96px",     # .stage min-height — the specimen stage floor
    "260px",    # .card-group min-width — the card specimen's natural measure
    "2px",      # .chip-dismiss padding nudge
    "999px",    # .badge pill radius — structural "fully round", not a scale step
})
_CONTENT_ALLOWED_WORDS = frozenset({
    "column", "space-between", "inline-block",   # flex/display structure
    "ui-monospace", "monospace",                 # the code-face stack (no colour choice)
    "inherit",                                   # .chip-dismiss color: inherit — takes the parent
                                                 # CHIP's own ink (content), unlike chrome where
                                                 # inherit would escape the token system
})


def render_showcase(receipts: dict) -> str:
    """Pure: committed receipts -> the showcase HTML, framed in the governed apple-dark page-shell.
    Deterministic (profiles sorted; receipt order preserved). No timestamps, no probe coupling."""
    from scripts.rendering.pageshell.pageshell import render_page_shell
    from scripts.rendering.webkit.components import render_nav

    button_css = []
    sections = []
    for name in sorted(receipts):
        rc = receipts[name]
        css, stage_html, backdrop = _stage_block(name)
        if css:
            button_css.append(css)
        claim = _html.escape(str(rc.get("profile", name)))
        n_pass = sum(1 for r in rc.get("results", []) if r.get("status") == "pass")
        n_cand = sum(1 for r in rc.get("results", []) if r.get("status") == "candidate")
        n_fail = sum(1 for r in rc.get("results", []) if r.get("status") == "fail")
        sections.append(
            f'<section class="lang" data-profile="{_html.escape(name)}">'
            f'<header><h2>{claim}</h2>'
            f'<p class="tally">{n_pass} pass · {n_fail} fail · {n_cand} cannot certify</p></header>'
            f'<div class="stage" style="background:{backdrop}">{stage_html}</div>'
            f'<div class="table-scroll"><table class="invariants"><thead><tr>'
            f'<th>invariant</th><th>law</th><th>verdict</th><th>receipt</th></tr></thead>'
            f'\n{_rows(rc.get("results", []))}\n</table></div>'
            f'</section>'
        )

    legend = (
        '<div class="legend">'
        '<span><b class="badge badge-pass">pass</b> a deterministic invariant the render satisfies</span>'
        '<span><b class="badge badge-fail">fail</b> a deterministic invariant the render violates '
        "(shown honestly)</span>"
        '<span><b class="badge badge-candidate">cannot certify</b> a judgment/deferred aspect '
        "(e.g. contrast over glass) — automation cannot decide it; a human/visual receipt does</span>"
        "</div>"
    )
    _nav_links = [("home", "index.html"), ("showcase", "showcase.html"),
                  ("studio", "studio.html"), ("settings", "settings.html")]
    nav_html, nav_css = render_nav(HOUSE, _nav_links, active="showcase.html")
    shell_html, shell_style = render_page_shell(
        HOUSE,
        title="Design-language conformance",
        intro="Every active design language, rendered from its own cited doctrine, with the conformance "
              "receipt for each invariant. The page's own frame is the apple-dark design language — the "
              "proof surface follows the very process it displays.",
        breadcrumbs=[("home", "index.html"), ("studio", "studio.html"), ("settings", "settings.html")],
        prefix_html=nav_html,
        sections=[("How to read this", legend)],
        body_html="\n".join(sections),
    )
    return (
        "<!doctype html>\n"
        '<html lang="en"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>Design-language conformance — showcase</title>\n"
        f"<style>:root {{ color-scheme: dark; }}\n* {{ box-sizing: border-box; }}\n"
        f"html, body {{ height: 100%; margin: 0; }}\n{shell_style}\n{nav_css}\n{_CONTENT_CSS}\n"
        + "\n".join(button_css) + "</style>\n"
        "</head><body>\n"
        + shell_html
        + "\n</body></html>\n"
    )


def write_showcase(output_path: str = "site/showcase.html") -> str:
    """Refresh each active profile's committed receipt, then render + write the showcase. The
    receipt is the interface between the conform() runner and this surface (verdicts flow only
    through the JSON)."""
    from scripts.quality.design_invariants import write_receipt
    receipts = {}
    for name in _active_profiles():
        write_receipt(name)
        p = _root() / "assets" / "receipts" / name / "conformance_receipt.json"
        receipts[name] = json.loads(p.read_text(encoding="utf-8"))
    html = render_showcase(receipts)
    out = Path(output_path)
    if not out.is_absolute():
        out = _root() / output_path
    out.write_text(html, encoding="utf-8")
    return html


if __name__ == "__main__":
    write_showcase()

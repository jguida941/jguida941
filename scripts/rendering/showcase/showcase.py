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
    out = []
    for r in results:
        status = r.get("status")
        if status not in _BADGE_TEXT:               # closed enum — fail closed (codex 1c #3): a
            raise ValueError(                       # malformed status can't inject an attr/class
                f"invariant {r.get('invariant_id')!r} has non-canonical status {status!r} "
                f"(expected one of {sorted(_BADGE_TEXT)})")
        badge = _BADGE_TEXT[status]
        inv = _html.escape(str(r.get("invariant_id", "")))
        law = _html.escape(str(r.get("law", "")))
        cite = _html.escape(str(r.get("doc_cite", "")))
        out.append(
            f'<tr data-invariant="{inv}" data-status="{status}">'
            f'<td class="inv">{inv}</td>'
            f'<td class="law">{law}</td>'
            f'<td class="cite">{cite}</td>'
            f'<td class="verdict"><span class="badge badge-{status}">{badge}</span></td>'
            f'</tr>'
        )
    return "\n".join(out)


def render_showcase(receipts: dict) -> str:
    """Pure: committed receipts -> the showcase HTML. Deterministic (profiles sorted; receipt
    order preserved). No timestamps, no probe coupling."""
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
            f'<table class="invariants"><thead><tr>'
            f'<th>invariant</th><th>law</th><th>doc</th><th>verdict</th></tr></thead>'
            f'<tbody>\n{_rows(rc.get("results", []))}\n</tbody></table>'
            f'</section>'
        )

    page_css = """
:root { color-scheme: dark; }
* { box-sizing: border-box; }
body { margin: 0; padding: 32px; background: #0a0a0f; color: #e8e8ee;
  font: 15px/1.5 -apple-system, system-ui, 'Segoe UI', sans-serif; }
h1 { font-size: 26px; margin: 0 0 4px; }
.sub { color: #9a9aa6; margin: 0 0 8px; max-width: 70ch; }
.legend { display: flex; gap: 16px; flex-wrap: wrap; margin: 16px 0 32px; padding: 12px 16px;
  border: 1px solid #23232e; border-radius: 12px; background: #12121a; font-size: 13px; }
.legend b { font-weight: 600; }
.lang { margin: 0 0 40px; padding: 20px; border: 1px solid #23232e; border-radius: 16px;
  background: #101018; }
.lang header { display: flex; align-items: baseline; justify-content: space-between; gap: 16px; }
.lang h2 { margin: 0 0 12px; font-size: 19px; }
.tally { color: #9a9aa6; font-size: 13px; margin: 0; }
.stage { display: flex; flex-direction: column; align-items: center; gap: 18px;
  min-height: 96px; padding: 24px; margin: 8px 0 20px; border-radius: 12px; }
.stage-row { display: flex; align-items: center; justify-content: center; gap: 20px; flex-wrap: wrap; }
.card-group { min-width: 260px; }
.chip-dismiss { background: transparent; border: 0; color: inherit; cursor: pointer;
  font-size: 15px; line-height: 1; padding: 0 0 0 2px; }
.no-render { color: #9a9aa6; font-style: italic; }
table.invariants { width: 100%; border-collapse: collapse; font-size: 13px; }
.invariants th { text-align: left; color: #9a9aa6; font-weight: 600; padding: 6px 10px;
  border-bottom: 1px solid #23232e; }
.invariants td { padding: 8px 10px; border-bottom: 1px solid #1a1a24; vertical-align: top; }
.inv { font-family: ui-monospace, 'SF Mono', monospace; color: #c9c9d6; white-space: nowrap; }
.cite { color: #7f7f8c; font-family: ui-monospace, monospace; }
.badge { display: inline-block; padding: 2px 10px; border-radius: 999px; font-weight: 600;
  font-size: 12px; white-space: nowrap; }
.badge-pass { background: #0f3d2e; color: #55e0a8; border: 1px solid #1c6b4f; }
.badge-fail { background: #451118; color: #ff8a9b; border: 1px solid #7a1f2b; }
.badge-candidate { background: #3a3410; color: #f2d06b; border: 1px solid #6b5f1c; }
""".strip()

    return (
        "<!doctype html>\n"
        '<html lang="en"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>Design-language conformance — showcase</title>\n"
        f"<style>{page_css}\n" + "\n".join(button_css) + "</style>\n"
        "</head><body>\n"
        "<h1>Design-language conformance</h1>\n"
        '<p class="sub">Every active design language, rendered from its own cited doctrine, with the '
        "conformance receipt for each invariant. This is the design-language surface — separate from "
        "the builder scorecard.</p>\n"
        '<div class="legend">'
        '<span><b class="badge badge-pass">pass</b> a deterministic invariant the render satisfies</span>'
        '<span><b class="badge badge-fail">fail</b> a deterministic invariant the render violates '
        "(shown honestly)</span>"
        '<span><b class="badge badge-candidate">cannot certify</b> a judgment/deferred aspect '
        "(e.g. contrast over glass) — automation cannot decide it; a human/visual receipt does</span>"
        "</div>\n"
        + "\n".join(sections)
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

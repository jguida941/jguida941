# PLAN LEDGER — finished work (folded out of the active plan)

The live plan is `docs/plans/ACTIVE.md`. This ledger keeps finished phases/slices durable
without cluttering the active routing. Newest last.

## Phase 1–3 — pipeline + honest metrics + canonical packages (DONE / LIVE)
- Fixed the frozen automation; honest GitHub-API metrics; private-repo handling (name + metadata,
  never contents); token resilience / last-known-good.
- Canonical `scripts/` packages (core/contracts/github/pipeline/quality/rendering/cli/organization) +
  the self-enforcing scripts/tests layout guards (WS1).
- Governed Liquid Glass SVG card kit (Power BI IA + Apple restraint); per-card red-first contracts;
  `DESIGN_SPEC.md` (cited Apple HIG + Power BI + GitHub-SVG) + `DESIGN_AUDIT.md`.

## Phase 4 — legible cards + the generated web dashboard (DONE / LIVE)
- **B4** legible tiles — fixed the Raw-Data-Snapshot truncation + the confusing primary-language
  metric ("Python / 50% / share of code"); red-first `test_label_legibility` (anchor-aware width-fit
  proof + caption-qualifier rule); adversarial review AMBER→GREEN.
- **C1** single design-token source (`design_tokens.py`) + the 3-theme system (Liquid Glass / Apple
  Dark / Power BI) with `test_theme_system` (completeness / WCAG-AA legibility / restraint / SVG↔web
  parity / IA-independence).
- **C2** the web dashboard **generated** from the token source (`web_render.render_dashboard()` →
  `site/index.html`), drift-guarded, with the theme switcher; privacy fix — `token_mode` scrubbed from
  the public `profile_snapshot.json` (`render_outputs._public_dashboard_data` + `test_public_data_privacy`).
- **C3** contribution calendar + activity heatmap added to the web (counts-only privacy-safe
  aggregations); 5-lens adversarial verification workflow folded (legend / hour-axis / cell aspect /
  ramp / py3.12 SyntaxWarning).
- **C4** web status chips by shape + label, not hue alone (`DESIGN_SPEC 3.6`); fixed a `safeUrl` regex
  regression. ~142 contracts green.

## Phase 5 — Organization-as-invariant + governed multi-theme design system (IN PROGRESS)
- **P5-0 slice 1 (commit `b51fbf8`, LIVE)** — the org meta-gate keystone: `contracts/repo_layout.json`
  (canonical target-shape as portable zero-literal DATA) + `tests/contracts/test_structural_layout.py`
  (closed-cover RED, mutation-proven — an undeclared/misplaced file reddens). 150 tests green.
- (remaining P5-0 + P5-1…P5-6 tracked in `docs/plans/ACTIVE.md`.)

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
- **P5-0 slice 2** — durable plan moved into the repo (`docs/plans/ACTIVE.md` +
  `docs/history/PLAN-LEDGER.md`), declared in `repo_layout.json`.
- **P5-0 slice 3 (0c, keystone)** — the add-RED-before-artifact gate
  (`scripts/organization/bootstrap_red_ref.py` + `tests/contracts/test_bootstrap_red_ref.py`):
  mutation task with no named RED rejected; shape task's RED must be a target-shape contract.
  Mutation-proven, dogfooded. 163 green. Remaining P5-0 (system-graph gather, docs-currency,
  claim lowering, MODULE_HOMES/TEST_GROUPS subsume) resumes after the W3 correction.
- **P5-COVERAGE W1 (D1, owner-ratified 2026-07-13)** — one governed theme-continuous site: shared
  head bootstrap applies `?theme=` → persisted `dash-theme` → house precedence pre-paint on every
  route; runtime proof route × profile × {1280,390} with real Chrome facts + provenance. D1
  superseded P5-ARCH's "freeze scorecard, drop switcher" (content freeze stayed; theme ban lifted).
  Design record folded: `handoff/w1-theme-continuity-design.md` (APPROVE r2; suite 345 green).
- **P5-COVERAGE W2/W3 — closed-world DOM ownership; index into the governed emitter world** —
  every static body element resolves to an emitter-owned signature (`contracts/dom_cover.json`);
  `site/index.html` generated via pageshell + webkit emitters; hydration = frozen singleton
  program, typed writers, closed bounds; hermetic Chrome receipts; 367 green at W3. Design
  records folded: `handoff/w2-dom-cover-design.md` (APPROVE, 351 green),
  `handoff/d-shell-0-design.md` (DOM-ownership law precedent; its centered-column/breadcrumb/
  shared-rhythm clauses were later superseded by the W3 correction),
  `handoff/d-shell-2-design.md` (page-manifest schema, still live via `contracts/page_manifest.json`).
- **P5-THEME-ROSTER-AUTHORITY** — `_index.json.active_design_profiles` is the public roster
  authority; exactly `liquid-glass, carbon, apple-dark` ship; `power-bi` reserved.
- **P5-RECEIPT-GATE** — deferred visual invariants carry `receipt_obligation` + `refute_by`;
  receipts serialize `receipt_status`; showcase displays pending-proof honestly.
- **P5-1 slices 1–8 (themes diverge)** — retired the convergence lock; per-theme IA (radius/type/
  density/motion); `test_design_distinctness` + `test_design_character` (doctrine-cited, caught
  real regressions); per-theme chart anatomy; KPI-grid density; mobile as contracted rule (44px
  targets, no page overflow, true-390 iframe probe); KPI density preserved per-language on
  mobile. 179 green at slice 7.
- **P5-DATA slice 1** — the 204-day freshness lie fixed: `days_since_last_push` (honest last-push)
  + `tests/contracts/test_data_semantics.py` (label-honesty law). 183 green.
- **P5-PATTERN slices 0–1** — retired the bad "Apple hides the heatmap" invariant (distinctness
  never trumps content-to-chrome); the de-AI readout: grouped Value-1 rows replace giant KPI
  boxes (`test_metric_readout_is_grouped_not_giant_boxes`, codex VERDICT: agree). Lessons:
  prove composition PATTERNS, not padding tokens.
- **P5-SKILL slice 1** — `skills/design-language-tdd/` codifies the loop; guarded by
  `test_skill_structure` (to be strengthened executable in correction slice 9).
- **P5-ARCH (workflow `wf_8ea0e7d9-544`) decisions** — separation of concerns (scorecard ≠
  design-language system); profile-as-DATA architecture → `docs/plans/DESIGN-SYSTEM.md`; critic
  must-fixes incl. the honesty fix now doctrine: **local enforcement = pytest contracts + visual
  receipts; NO Rust kernel operates here** (the old ACTIVE.md Workstream-0 "decided by the Rust
  kernel / semproof adjudicates" text is historical/aspirational only; the kernel is the
  portability destination, never a local gate).
- **Operator doctrine reframes (2026-06-29, binding)** — (1) separation of concerns: the Builder
  Scorecard is ONE frozen concern; the design-language system is a component library + proof
  surfaces per language, built from each language's actual published docs. (2) prove REAL
  properties, not proxies: pattern invariants over token invariants; data under contract
  (label-honesty); pixels over strings (visual/runtime receipts are a required gate). These
  reframes seeded the W3 correction's composition-authority laws.
- **Board workstream records folded:** `handoff/b-0-design.md` (motion/nav/charts aspect specs,
  B-0/B-1 arcs; motion + component-nav emitted) and `handoff/codex-batch-prompt.md` (the
  retroactive D-SHELL-1/2 + B-0/B-1 review batch — superseded by the per-slice three-gate cadence
  of the W3 correction program). Old `handoff/HANDOFF.md` (2026-07-02 reorientation) content is
  superseded by the refreshed reentry card; git history retains it.
- **W3 index migration** — `handoff/w3-index-migration-design.md` approval VOID/superseded by
  `handoff/w3-visual-regression-correction.md` (its own banner + the correction record).

## 2026-07-15 — Program adoption: the universal design-compiler

The operator ratified the product statement + program now leading `docs/plans/ACTIVE.md`
(universal engine; Apple/Carbon/Liquid as fixtures; DEMO A/B acceptance; per-slice codex
DESIGN + CODE + ADVERSARIAL cadence; T0 doc-authority law). Session plan source:
`~/.claude/plans/the-previous-handoff-transient-donut.md` (adopted here; the in-repo plan wins).
Odinproject O0 landed (`bad950a`). Codex rounds: advisory PLAN REVISE (folded); slice-0 DESIGN
gate r1 REVISE (folded to rev 2); r2 REVISE (folding to rev 3). Transcripts:
`scratchpad/work/codex-*.md`.

## 2026-07-22 — operator post-review execution law + `/root`-conductor adoption

- Adopted the operator-amended landing `AGENTS.md`/`ACTIVE.md` (sha256 `89de86f1…`/`cf4e82e4…`):
  `/root` conducts; Fable authors DESIGN + RED; Opus builds GREEN; Codex reviews. Review history
  is append-only across corrections/renames/versions; terminal findings become typed
  `FindingToEvidenceTransition` rows (12 rows live in the currency policy); no review-of-review;
  after right-reason RED plus ONE bounded conformance check, a DIFFERENT Opus builder is
  dispatched immediately.
- Law data: `contracts/process_docs_currency_policy.toml` · RED:
  `tests/contracts/test_process_docs_currency.py` · design:
  `scratchpad/active/process/process-doc-currentness-adoption-design-r1.md`.

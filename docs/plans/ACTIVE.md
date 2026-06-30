# ACTIVE PLAN — Phase 5: Organization-as-invariant + governed multi-theme design-language system

> This is the durable, committed source of truth for the current plan and status. The
> ephemeral `~/.claude/plans/*.md` mirror can be lost; THIS file (deployed with the repo)
> cannot. Finished history is folded into `docs/history/PLAN-LEDGER.md`.

## STATUS — where we are (updated each slice)

- **Phases 1–4: DONE / LIVE** — see `docs/history/PLAN-LEDGER.md`. ~142 contracts green before Phase 5.
- **Phase 5 in progress.** Current workstream: **P5-0 — the organization-as-invariant meta-gate.**
  - ✅ **P5-0 slice 1 (LIVE, commit `b51fbf8`)** — canonical repo target-shape as DATA
    (`contracts/repo_layout.json`, zero-literal portable LAW) + the closed-cover
    structural-layout RED (`tests/contracts/test_structural_layout.py`), mutation-proven
    (an undeclared/misplaced file reddens). 150 tests green.
  - ✅ **P5-0 slice 2 (durable plan)** — moved the plan into the repo (`docs/plans/ACTIVE.md` +
    `docs/history/PLAN-LEDGER.md`); declared in `repo_layout.json`.
  - ✅ **P5-0 slice 3 (0c, the keystone)** — the add-RED-before-file gate
    (`scripts/organization/bootstrap_red_ref.py` + `tests/contracts/test_bootstrap_red_ref.py`):
    a mutation-capable task with no named RED is rejected; a shape/reorg task's RED must be an
    executable target-shape contract. Mutation-proven + dogfooded (admits its own slice). 163 green.
  - ⏭ **P5-0 next:** system-graph connectivity gather (`system_graph_policy.toml`) → docs-currency
    RED + retire stale docs (`DESIGN_AUDIT`) → chat→`ClaimIntakeClaim` lowering → then SUBSUME the
    old `MODULE_HOMES`/`TEST_GROUPS` guards into the single `repo_layout.json` cover (kill the
    transitional double-maintenance).
- ✅ **P5-1 slice 1 (themes diverge — the visible payoff)** — retired the convergence lock
  (`test_ia_tokens_are_theme_independent` → `test_ia_is_complete_and_bounded`); promoted PER-THEME
  IA (`design_tokens.THEME_IA`: radius + type ramp; Apple rounder/larger, Power BI sharper/denser,
  Liquid Glass == config anchor); `emit_css_root` now emits each theme's full axis. New
  `test_design_distinctness` (anti-convergence law: every theme pair differs on a quorum of
  structural signature axes — mutation-proven). Power BI now reads sharp/dense, Apple rounded/large.
  166 green. (Density/motion/charts still to diverge in P5-2/P5-3.)
- ✅ **P5-1 slice 2 (DENSITY + the CHARACTER law — proper-style invariants)** — researched the 3
  design languages' PROPER structural characteristics from their docs (a 3-agent workflow:
  Apple HIG Layout airy 32/24, Power BI report-design tight 16/8, Liquid Glass medium). Added
  per-theme `density` to THEME_IA; routed the component CSS (panel/tile padding + grid gaps)
  through `--pad-*`/`--gap-grid` so the BOXES diverge — Power BI packs tight/sharp, Apple breathes.
  NEW `test_design_character` (design_languages authority): each theme must POSITIVELY express its
  language (Apple airy + large + rounded; Power BI tight + sharp; ordered + distinct), grounded with
  doctrine cites — the answer to "where are the invariants for their respective proper styles." It
  already bit (caught Power BI's radius being too round). 170 green.
- ✅ **P5-1 slice 3 (per-theme chart ANATOMY begins)** — Power BI now renders the Language Breakdown as
  a DATA TABLE/matrix (Language | Share | bar, gridlined) while Apple/Liquid Glass keep the stacked bar;
  CSS-gated on `[data-theme="power-bi"]` so the switcher reflows it. `test_design_character` extended
  (Power BI table-forward; others bar/stat-forward — grounded in the research). 171 green. Same data,
  different chart per design language — the start of each theme being a different *website*.
- ✅ **P5-SKILL slice 1 (the repeatable engine exists)** — `skills/design-language-tdd/` (SKILL.md +
  references add-design-language / prove-theme / boundaries) codifies the loop (research → cited
  doctrine → closed proper-style + character invariant set RED-first → GENERATE the themed
  anatomy → prove: GREEN both surfaces + mutation + receipts + codex → honest receipt, never "is
  Apple"). Org gate baked in. Guarded by `test_skill_structure` (new `skill` authority). 175 green.
  "Add Material / Stripe / a brand guide" = run this skill = another complete distinct website.
- ✅ **P5-1 slice 4 (per-theme KPI-grid density)** — `.tiles` now `auto-fit minmax(var(--tile-min),1fr)`;
  Power BI tile_min 150 packs a dense 5-6-KPI row, Apple tile_min 380 spreads to 2 large cards, Liquid
  280 (3-up). `test_design_character` extended (KPI density inverts padding, distinct). 176 green.
- ✅ **P5-1 slice 5 (Apple drops the dense heatmap)** — under `[data-theme="apple-dark"]` the dense 7x24
  activity matrix is hidden, leaving the simpler event-mix summary (Apple HIG is stat/summary-forward,
  avoids dense grids); Power BI/Liquid keep the matrix. `test_design_character` extended + grounded. 177 green.
- ✅ **P5-1 slice 6 (mobile is now a contracted rule)** — phone breakpoint (<=480px), >=44px touch
  targets (Apple HIG / WCAG 2.5.5), the dense heatmap scrolls inside `.heat-wrap` (no distortion at
  ~375px), `body overflow-x:hidden` (no page-level horizontal overflow), `-webkit-backdrop-filter`
  for Safari. New `test_web_dashboard.test_responsive_mobile_and_touch_targets`. Verified at 390px.
  178 green. (Per-LANGUAGE mobile character — e.g. Apple touch-first sizing vs Power BI grid reflow —
  is the next responsive layer.)
- ✅ **P5-1 slice 7 (KPI density stays per-language on mobile)** — fixed a convergence BUG in the mobile
  CSS: the `<=760px` rule was flattening `.tiles` to one column for EVERY theme, erasing the per-language
  KPI density on phones. Now only section layout collapses; `.tiles` keeps its per-theme `--tile-min`
  auto-fit (Power BI stays dense, Apple goes to one card). New `test_design_character.test_kpi_density_
  character_survives_on_mobile` (RED-first, mutation-proven). 179 green.

### ⟐ REFRAME (owner, 2026-06-29): SEPARATION OF CONCERNS — stop dressing the scorecard, build the design system

The owner's correction, now doctrine: **the Builder Scorecard is ONE concern and it's done.** It mimics a
GitHub-metrics page because it's bound to GitHub data — that was the constraint; as a *data dashboard* it
looks good and should be **one frozen style**. We must STOP polishing the scorecard surface. The **design-
language system is a SEPARATE concern**: a **component library** (buttons, tags, cards, inputs, charts in
every state) + **per-theme SHOWCASE pages** where each language renders its OWN kind of website (an Apple
page looks like Apple, a Stripe page like Stripe, a Carbon app like Carbon), each built from that language's
**actual published design doc**. NOT the scorecard reskinned 10 ways. Clean boundary: **analytics surface ≠
design-language surface.** Every aspect of every theme follows its definition doc; the skill makes it
repeatable for all 11 languages.

- 🔄 **P5-ARCH (in progress) — doc-grounded architecture workflow** (`scratchpad/work/design-language-
  architecture.workflow.js`, run `wf_8ea0e7d9-544`): 11 researchers extract each language's REAL component
  anatomy + page archetype from its published spec → synthesis derives the separation-of-concerns
  architecture + closed component roster + **component-level** character/distinctness invariants + the first
  RED-first slice → adversarial critique. Output folds into this plan + P5-3/P5-6 below.
- ⏭ **Next (post-workflow), under the gate:** stand up `scripts/rendering/webkit/` component library +
  `render_showcase()` → `site/showcase.html`; first real component (button across all variants/states) with
  a character+distinctness contract for the 3 existing themes; then add themes 4–10 via the skill, each a
  full distinct archetype page. (Per-language mobile character rides along inside each component contract.)
### ⟐ DEEPER REFRAME (owner, 2026-06-29 pt2): we've been proving PROXIES, not the things that make it correct

The owner looked at the live mobile site and named three failures that are really ONE: **we prove what's
easy to measure (token numbers, string presence), not what actually makes it pro and honest.**

1. **The design invariants REWARD the AI look.** They measure tokens (`panel_pad>=24`, `radius>=18`,
   "airy"). A giant box with one number floating in 70% dead space *passes* "airy" — the invariant pushes
   us toward the tell. Real Apple = **grouped inset lists** (Settings/Health): related stats share ONE card
   as hairline-divided rows; type makes the hierarchy; content FILLS the card. No real system gives each
   metric its own full-width card. **Missing PATTERN invariants:** content-to-chrome ratio (number fills the
   card, not floats), no single-stat full-width cards on a stat readout, grouped composition,
   hierarchy-from-type-not-chrome, and the real per-language ARCHETYPE. → These must come out of P5-ARCH
   (derive from the real docs) and REPLACE/augment the token-only `test_design_character` checks. The
   token tests that reward emptiness get retired or inverted.
2. **The DATA isn't under contract (semantic-TDD on data).** `median_days_since_push=204` is a real median
   across all 68 public repos, but the card label "median freshness · since last push" reads as "no push in
   204 days" while the same snapshot shows pushes TODAY. The number is honest; the LABEL lies, and nothing
   tests it. → NEW workstream **P5-DATA**: plausibility + cross-consistency + label-honesty invariants over
   the computed metrics (RED-first), e.g. "a headline metric's label must match its true semantic" and "no
   metric may imply staleness contradicting the freshest-repo signal." First fix: the 204 metric (relabel to
   its true meaning, or replace with a meaningful freshness signal) behind a data contract.
3. **Tests check STRINGS, not PIXELS.** Slice 5 "Apple drops the heatmap" went green on a CSS-rule
   string-match, but at runtime the hydration JS sets inline `display:grid` which BEATS the CSS, so the
   heatmap renders anyway and its 460px min-width overflows the page. A string-green with a wrong render is
   the same failure class as the lying label. → **Visual/runtime receipts become a REQUIRED gate**, not
   decoration; judgment invariants must be checked against the actual render. Fix the apple-heat runtime
   defeat + the residual mobile overflow (MEASURE the overflowing element, don't guess).

- ✅ **P5-1 slice 8 (KPI/snapshot cards stop overflowing the phone)** — Apple's `tile_min` (380px) exceeded a
  ~390px viewport, so `minmax(380px,1fr)` forced a track wider than the screen (the cards you saw running off
  the right). Now `minmax(min(var(--tile-min),100%),1fr)` keeps the airy large-card density on desktop but
  collapses to one FITTING card on a phone. New `test_design_character.test_kpi_grid_never_overflows_a_narrow_
  viewport` (RED-first, mutation-proven). 179 green. NOTE: a SEPARATE residual overflow remains (the heatmap;
  see pt2 #3) — tracked, fixed next by measurement.

- ✅ **P5-DATA slice 1 (semantic-TDD on the metrics — the 204-day lie)** — the freshness figure was a
  median across all ~68 public repos presented as "since last push", reading as months of inactivity while
  pushes happened TODAY. Added `days_since_last_push` (the FRESHEST repo = the true last push) in
  `compute_metrics`; the scorecard + dashboard now present "Last Push · days since last commit" (honest),
  median kept in raw data only. NEW `tests/contracts/test_data_semantics.py` (new `data_semantics` authority):
  a real unit test on `_build_engineering_metrics` (freshest <= median, pushed-today => 0) + presentation-
  honesty (no metric pairs a last-push label with the median key; the dashboard binds the honest metric).
  RED-first (all 3 bit). 183 green. (Next P5-DATA: plausibility + cross-consistency sweep over the rest.)

### ⟐ ARCHITECTURE (P5-ARCH workflow `wf_8ea0e7d9-544` landed — 11 doc dossiers + synthesis + adversarial critique)

**Decisions adopted:**
- **The Builder Scorecard FREEZES to ONE language (liquid-glass) and DROPS the runtime switcher.** It stays the
  GitHub-data surface (SVG cards + `site/index.html` + README), tokens pinned at build time. The PATTERN
  invariants (content-to-chrome, grouped composition, no giant empty boxes) ALSO apply to it — so the one
  liquid-glass scorecard stops looking AI — but no more theme-chasing on it.
- **Separate design-language system, NO GitHub data in it (synthetic fixtures):** (A) a CLOSED component library
  (button, chip, card, input, nav, kpi, table, chart, hero, type-specimen — every variant+state); (B) per-theme
  archetype pages `site/showcase/<lang>.html` where each language renders its OWN kind of website (Apple editorial
  scroll, Carbon UI-Shell+SideNav+DataTable, Power BI fixed 1280×720 report w/ page-tabs + cross-filter, Stripe
  gradient marketing, Linear midnight hairline); plus `site/showcase.html` gallery (component-matrix + per-theme).
- **Packages:** `scripts/rendering/design/<lang>.py` (profiles), `scripts/rendering/webkit/` (portable
  component+chart emitters — incl. a per-profile component-ANATOMY hook so Carbon's label-left/icon-right is
  STRUCTURE not a token-swap), `scripts/rendering/showcase/`, `scripts/quality/design_invariants.py` (portable
  `(surface,profile)->[InvariantResult]` engine, runs on the scorecard AND the showcase). `design_tokens.py`
  becomes a thin shim **DERIVED from config.py** (single source — must-fix #5).
- **Invariants are PATTERN/anatomy-level, grounded in cited doc values** (Carbon radius:0 except .cds--tag; Apple
  zero box-shadow; anti-Material state-mechanic; Stripe angled gradient + `rgba(50,50,93,.25)` shadow; pairwise
  distinctness fingerprint forbidding near-sibling convergence). Determinism split honest (deterministic predicate
  vs judgment review-anchor+visual-receipt).

**Critic verdict `revise` — must-fixes folded into the plan (in order):**
1. **HONESTY: drop the "Rust kernel decides / candidate_only" framing LOCALLY.** Grep proved no kernel / no
   `semproof` / no `candidate_only` in THIS repo; receipts already self-write "satisfied". Local enforcement =
   pytest contracts + visual receipts. Kernel-adjudication is the PORTABILITY destination (repo-surface-scout /
   semantic-tdd), not a current local gate. Stop claiming it operates here.
2. **Verify every magic constant against a real published-doc URL** in `docs/design/<lang>.md` BEFORE writing the
   RED (the predicates currently encode unverified numbers: rim `rgba(255,255,255,0.22)`, `saturate>=180%`, spring
   `cubic-bezier(0.34,1.56,0.64,1)`, Stripe shadow). Spot-verify ≥ liquid-glass materials + Stripe shadow. ← the
   owner's exact demand: follow the ACTUAL design docs.
3. **The repo_layout meta-gate is INERT for non-`scripts/**/*.py`** (P5-0 not finished; `layout_audit` only walks
   `scripts/**/*.py`). Either land the repo_layout-consuming gate or treat P5-0 as a hard precondition before the
   showcase files' homes mean anything.
4. **Component ANATOMY deterministic** (above). 5. **liquid-glass DERIVED from config** (above). 6. Make the
   reusable half repo-literal-free (skill must not hardcode MODULE_HOMES / repo_layout.json / receipt sinks).

**First design slice (after the docs/design verification of #2):** BUTTON across all variants+states for 3
profiles (liquid-glass, carbon, apple-dark) — character + distinctness deterministic contract + the first visual
receipt. The loudest "genuinely different component, not a reskin" moment.

- **Roadmap:** **P5-DATA semantic-TDD on the metrics (NOW)** → docs/design verification → P5-3 webkit button slice
  → showcase scaffold → themes 4–10 via the skill → P5-4 settings/customization → P5-6 showcase polish + the
  runtime/visual receipt gate. P5-0 org-gate completion gates the showcase-file homes. The `design-language-tdd`
  skill dogfoods on the first 3 themes.

## Context

Phases 1–4 shipped the README SVG cards + the **generated** web dashboard (`web_render.py` →
`site/index.html`, drift-guarded, token-sourced), a 3-theme switcher, calendar + heatmap,
status-by-shape, the `token_mode` privacy scrub. Two structural problems + a keystone reframe
this phase:
1. **The web is a "token-and-skin" artifact** — per-aspect design rules (4px-grid, type-on-scale,
   hierarchy, tile anatomy, chart correctness, responsive, motion, contrast-on-tints, buttons/tags)
   are enforced for the SVG cards but **not the web** (the `--space-*` vars are emitted yet used
   **zero** times). That's why it still reads "AI" in spots.
2. **Themes are contractually forced to CONVERGE** — `test_theme_system.py::test_ia_tokens_are_theme_independent`
   *forbids* a theme from changing type/spacing/radius, so Power BI can't help looking like Apple.
3. **THE KEYSTONE.** Organization is not a Python audit — it is a **target-shape invariant**, rule:
   **"you must add the RED before you add the artifact."** A misorganized tree must be *structurally
   unconstructable to ship*, decided by the Rust kernel (as it already decides proof / connectivity /
   claim-intake), **portable to every repo** (LAW carries zero literals; only per-repo DATA differs).
   The design-language work is the **first surface** governed by this gate.

**Composition boundary (verified in the siblings).** `semantic-tdd` = Rust authority kernel;
**Python GATHERS verdict-free facts → Rust DECIDES → Python relays.** `repo-surface-scout` is the
read-only `candidate_only` PROPOSER. Everything here is built as a **gatherer/proposer + per-repo
DATA**, emitting verdict-free `*Claim` JSON the kernel adjudicates via the `semproof` CLI. We never
re-implement a kernel verdict (preflight RED-sufficiency, plan-graph reachability, claim-intake
EVIDENCE-BASIS, construct-placement homing). Can't touch Rust → build the half it consumes, and
REUSE the sibling mechanisms rather than reinvent.

## Workstream 0 — Organization-as-Invariant (the meta-gate; FIRST; governs everything after)

Generalize this repo's WS1 guards (`scripts/organization/{layout_contract,tests_layout_contract}.py`)
into ONE portable target-shape over **every** surface, by **reusing** the proven sibling artifacts:
- **0a. Canonical repo-shape as DATA** — `contracts/repo_layout.json`, mirroring scout's
  `structural_layout` (groups→members + `placement_enforced`, required/live docs, stale tokens,
  `active_plan`). Whole-codebase inventory: `scripts/**`, `tests/**`, `docs/**`, `contracts/**`,
  `site/**`, `assets/**`, `skills/**`, the new `design/`+`webkit/` packages, the design profiles.
  Zero repo literals in the LAW; DATA is the per-repo parameterization. **[slice 1 DONE]**
- **0b. Closed-cover structural-layout RED** — `tests/contracts/test_structural_layout.py`: every file
  declared or it reddens. Subsumes the two WS1 guards. **[slice 1 DONE]**
- **0c. Add-the-RED-before-the-artifact gate** — copy `semantic-tdd/scripts/check_bootstrap_red_ref.py`
  (invariant is repo-independent; only WHICH RED is repo-specific); a shape task's RED must itself be a
  target-shape contract. Emits a verdict-free `ArchitecturePreflightClaim`; `MissingRedTestRef` stays
  the kernel's (`preflight.rs`).
- **0d. Connectivity gather** — `tests/system_graph_policy.toml` + a `check_system_graph.py`-style
  gatherer (every artifact wired/declared, no orphans); emits `PlanGraphClaim`; reachability/cycle stays
  the kernel's (`plan_graph.rs`).
- **0e. Docs-currency + cleanup** — `live_docs` + `stale_reference_tokens` + a docs-currency RED. Retire
  stale docs: fold finished history → `docs/history/PLAN-LEDGER.md`, keep one live `docs/plans/ACTIVE.md`,
  reconcile `DESIGN_SPEC`, retire the stale task list + superseded `DESIGN_AUDIT` sections.
- **0f. Claim-intake lowering** — reuse scout `claim_audit.py::_build_semantic_tdd_ingress`/`_strict_v2_record`
  to lower the operator's redirect into a **candidate** `ClaimIntakeClaim`; EVIDENCE-BASIS admissibility stays
  the kernel's (`claim_intake.rs`).
- **0g. Scout target-shape lane points here** — don't write a new proposer; run scout `target_shape.py`
  against this repo; the repo adopts + proves.

**Reuse map:** scout `repo_layout.json`+`test_structural_layout.py` (0a/0b); `check_bootstrap_red_ref.py`
(0c); `check_system_graph.py`+`system_graph_policy.toml` (0d); scout `claim_audit.py` lowering (0f);
`target_shape.py` (0g). **Kernel's job (never re-implement):** verdicts in `preflight.rs`/`plan_graph.rs`/
`claim_intake.rs`/`placement_law.rs`, via the `semproof` CLI; the repo-side relays fail-closed.

## Doctrine extension (design-language)
- A theme = a design LANGUAGE spanning every axis (color roles + categorical chart palette, type ramp,
  spacing+density, shape/radius/elevation/material, motion, component variants, chart selection, layout);
  themes must be provably **DISTINCT** + each provably **EXPRESS** its language.
- **Every ASPECT** has a red-first variance contract whose expected values come from that language's
  **cited doctrine doc** (`docs/design-languages/<lang>.md`). Analytics (data + chart modules) is separate
  from theme. Honest claim: *"satisfies the `<language>` profile vN — here are the receipts,"* never "is
  Apple"; profiles `candidate_only`; judgment invariants → review anchor + visual receipt (never a fake
  RED); DEFAULT language IA stays `== config.py`.

## The 10 themes (skill researches each; extensible)
Liquid Glass (origin) · Apple HIG · Power BI · Material 3 · Fluent 2 · IBM Carbon · Shopify Polaris ·
Atlassian · Linear · Vercel/Geist · Stripe.

## The SKILL — `skills/design-language-tdd/` (built here, portable to scout)
One skill, three lanes (mirrors scout `semantic-tdd-claim-audit`): `SKILL.md` router + `references/`
(`add-design-language`/`add-aspect-contract`/`prove-theme` + `predicate-library`/`determinism-split`/
`distinctness-and-character`/`visual-receipts`/`doctrine-sourcing`/`boundaries`) + templates. The org gate
is baked in (name the RED first; declare the new file's home in `repo_layout.json` same slice). Loop:
research→cited doctrine → closed invariant set → RED-first → implement → mutation-prove → GREEN (SVG+web)
+ visual receipts → distinctness/character → codex folds disagreements RED-first → honest receipt.

## Architecture
- **`scripts/rendering/design/`** (design_tokens.py → thin shim): `schema.py` (`DesignLanguage` over every
  axis), `languages/<name>.py` (liquid-glass IA `==config`), `registry.py`, `emit.py` (per-`[data-theme]`
  full-axis CSS incl. `--type-*/--space-*/--radius-*/--dur-*/--bento-cols/--cat-*`), `spec.py` (hex-free
  `THEME_SPEC` for chart-selection + component-variants).
- **`scripts/rendering/webkit/`**: `components.py`+`component_css.py` (button/chip/card/kpi/section/nav/row/
  empty/badge, variant attribute-gated, token-only), `charts_runtime.py` (+ bar/column, line/area, data-table,
  multi-series, stat-card), `charts_models.py` (SVG↔web parity), `layout.py` (breakpoint + container-query +
  density — fixes 375px heatmap).
- **Pages (generated, drift-guarded):** `render_dashboard()` (morphs per theme), `render_settings()` →
  `site/settings.html` (per-aspect override panel + localStorage/URL + iframe live-preview + component
  gallery), `render_showcase()` → `site/showcase.html` (languages×variants×charts), `write_site()`.

## Contract structure (~10 themes × ~15 aspects)
Profile-JSON-as-data + ONE generic conformance runner + a per-aspect predicate library:
`contracts/design_profiles/<lang>.json` (+ `_index.json` + `design_aspect_roster.json`); `scripts/contracts/
design_predicates.py` (`on_scale_type`, `grid_multiple`, `contrast_on_actual_bg`, `hierarchy_dominance`,
`chart_segment_cap`, `motion_bounds`, `responsive_no_clip`, `token_only_color`, `status_shape`,
`button_state_semantics`, `density_band`, `radius_band`, `categorical_palette`, `elevation_material`) +
loader + `design_render_adapter.py` (the portability seam); `tests/contracts/test_design_{profiles_schema,
conformance,character,distinctness,visual_receipts}.py`; add `xfail_strict=true`. `test_design_distinctness`
**inverts** the retired convergence test. `docs/design-languages/<lang>.md` = cited doctrine; `assets/
receipts/<lang>/` = before/after + `conformance_receipt.json`.

## Portability to repo-surface-scout
Built behind the `RenderedTheme`/adapter seam. **Reusable → ports:** the skill, predicate library, profile
schema + roster, conformance/distinctness/character LAW shapes, doctrine+receipt templates, the org-gate
gatherers. **Profile-specific → stays:** `design_render_adapter.py`, per-language token values, receipts,
data binding.

## Verification (per slice)
`pytest tests/` (and `unittest discover`) green; the org guards green AND mutation-proven; the design
conformance/character/distinctness runners green (distinctness RED before Phase 1); every judgment invariant
has a receipt; visual receipts per theme/breakpoint; drift guards green for `index/settings/showcase.html`;
live Pages deploy; codex agrees per theme. **Every slice: name the RED → declare the home in `repo_layout.json`
(same slice) → implement → GREEN → visual receipt → codex folded RED-first → commit → CI green → keep docs fresh.**

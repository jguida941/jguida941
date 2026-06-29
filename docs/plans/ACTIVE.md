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
- **After P5-0:** P5-1 engine + retire convergence contract (distinctness RED-first) → P5-2
  diverge the 3 themes → P5-3 webkit chart/component library → P5-4 settings page → P5-5
  themes 4–10 via the skill → P5-6 showcase + portability. The `design-language-tdd` skill is
  built alongside P5-1 (dogfoods on the first 3 themes).

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

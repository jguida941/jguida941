# Design-language system — the self-demonstrating architecture (plan)

> Durable plan for the design-language system (separate from the frozen GitHub-data scorecard).
> Grounded in how **repo-surface-scout** + **semantic-tdd** organize a full codebase and build
> RED-contract-first (study + design + codex workflow `w17p9c4rv`). `docs/plans/ACTIVE.md` carries
> live STATUS + points here; finished slices fold into `docs/history/PLAN-LEDGER.md`.
>
> **The proof IS the product.** The showcase a visitor opens *is* the conformance run rendered; the
> settings page is the governance working in their hands. Honest claims only — "satisfies the
> `<language>` profile vN — receipts", `candidate_only`, never "is Apple". Enforcement here is
> **local pytest contracts + visual receipts** — there is NO Rust kernel in this repo; we mirror the
> sibling DISCIPLINE + organization, not a phantom adjudicator.

## 1. One data-flow: `PROFILE (data) → RENDER (webkit) → INVARIANT (predicate) → RECEIPT`

Four seams, three instances (scorecard / showcase / settings-preview) share the SAME pipeline.

- **Seam 1 — PROFILE (data):** `contracts/design_profiles/<lang>.json` is the source of truth (scout
  `design_profiles.json` style). `scripts/rendering/design/loader.py` resolves it into a VIEW (plain
  resolved dicts today — codex #7; a frozen typed view is a later hardening, not claimed now). No design
  values live in Python; `design_tokens.py` becomes a config-derived shim and
  the liquid-glass profile is `derived_from: "config"` (single source — the SVG-parity anchor).
- **Seam 2 — RENDER (webkit):** `scripts/rendering/webkit/components.py::render_<component>(profile,
  variant, state) -> (html, css)`, token-only, reading the profile's per-component **ANATOMY** block
  so STRUCTURE differs (Carbon label-left/icon-right DOM vs centered capsule), not just tokens. The
  portability seam `webkit/design_render_adapter.py` turns a render into **verdict-free FACTS**
  (geometry, radius, shadow presence, focus recipe, easing, and — only via the headless probe —
  computed contrast). The adapter GATHERS; it never decides.
- **Seam 3 — INVARIANT (decide):** `scripts/quality/design_invariants.py::conform(surface, profile)
  -> [InvariantResult]` walks the profile's `invariants[]`, dispatches each *emitted + deterministic*
  row's `predicate_class` into `scripts/contracts/design_predicates.py`, decides pass/fail from the
  facts. Judgment/deferred rows become `candidate` (review-anchor, never a fake pass/fail). The
  gather→decide split lives exactly at seam 2→3 — the kernel-boundary discipline, kernel-free.
- **Seam 4 — RECEIPT:** `assets/receipts/<lang>/conformance_receipt.json` (the serialized
  `[InvariantResult]`, shaped like `bootstrap_red_ref.gate()`'s envelope) + before/after PNGs for
  judgment rows. The showcase + settings READ these to stamp each cell — the receipt rendered.

`InvariantResult = {invariant_id, profile, profile_version, aspect, component, state, determinism,
status: pass|fail|candidate, evidence, refute_by, doc_cite, authority_status:"candidate_only",
cannot_mark_done:true, claim:"satisfies <lang> profile v<N> — receipts"}`.

## 2. Profile-as-DATA (JSON is the single source; the loader is a view)

`contracts/design_profiles/` (already a declared `group_dir`):
1. `_index.json` — `active_design_profiles[]` + `reserved_design_profiles[]` (scout's roster; a
   profile not in the index can't ship).
2. `design_aspect_roster.json` — the CLOSED COVER of aspects (color-roles, type-ramp,
   spacing/density, radius/elevation/material, motion, components{button,chip,card,kpi,input,nav,
   table,chart,hero,type-specimen}, charts, responsive, touch-target). Each aspect is
   `emission_status: emitted` OR a declared `deferred` + `defer_reason`. Omitting an aspect reddens.
3. `<lang>.json` — one CLOSED profile: tokens|derived-pointer, ia, components{...with per-component
   anatomy+fingerprint}, archetype, and a self-describing `invariants[]` (scout style):
   `{invariant_id, aspect, component, law, determinism, predicate{predicate_class, params},
   emission_status, refute_by, doc_cite, derived:bool}`. `predicate_class` is the load-bearing
   partition — a deterministic class compiles to a real red/green predicate; a judgment class
   demotes to review-anchor + visual receipt and NEVER compiles a fake passing body.

The DATA itself is tested before any render: `test_design_profiles_schema.py` pins the closed cover
(per-profile **ENVELOPE** validity, aspect-roster set-equality, index↔files parity both directions) +
a DERIVED-PARITY assertion (liquid-glass tokens == `config.py`). **(codex D1: today this is ENVELOPE
validity — `contract_id`/`authority_status`/`derived_from`/`aspect_coverage` shape; a GENERIC
`$value/$type` DTCG-shape + `components`/`fingerprint`-shape assertion lands with the conformance
runner in 1b, so a malformed token block can't pass silently.)**

## 3. One generic runner + one predicate library (new theme = data + zero code)

`conform()` is parameterized entirely by the profile data. `design_predicates.py` is the closed set
(`on_scale_type`, `grid_multiple`, `contrast_on_actual_bg`, `hierarchy_dominance`, `chart_segment_cap`,
`motion_bounds`, `responsive_no_clip`, `token_only_color`, `status_shape`, `button_state_semantics`,
`density_band`, `radius_band`, `elevation_material`, `categorical_palette`, `distinctness_fingerprint`)
— pure `facts -> bool`, seeded from the proven `_contrast`/`_is_chromatic`/`_signature` helpers.
`test_design_conformance.py` is the genericity proof: every active profile × emitted-deterministic
invariant resolves to a real predicate, is non-vacuous (mutating the cited value reddens), and traces
to a `doc_cite`. Adding theme 4 adds zero predicates; adding a component adds only its new predicates.

## 4. The two proof surfaces

- **Showcase (`render_showcase() -> site/showcase.html`):** the live invariant-stamped matrix —
  rows=components, cols=themes, sub-cells=states; each cell renders the REAL webkit component AND a
  verdict badge read from the receipt (`pass` / `candidate`+thumbnail / `fail` — a cell may ship
  visibly failing, the honest state); hover shows invariant_id/law/doc_cite/refute_by. Per-theme
  pages, if added later, are INTERNAL receipt/proof fixtures only — never the public theme
  architecture. The canonical public product surface remains `site/index.html` with one
  active-profile theme selector. Closed-cover guard `test_showcase_coverage.py`: declared cells ==
  rendered cells (both directions); drift-guarded.
- **Settings (`render_settings() -> site/settings.html`):** the governed control plane — the design
  twin of the bootstrap-RED gate. Compose base theme + per-aspect overrides (the control space IS the
  roster/profile allowlists), live-preview re-renders, the SAME `conform(composed_profile)` runs, and
  per-aspect verdicts show live. **A composition with any `fail` is unconstructable** (Apply disabled)
  — `test_settings_composition.py` proves bad-rejected / good-accepted, mutation-proven. Persist to
  URL/localStorage, re-validated on load (never trusted). Drift-guarded; its own artifact, not via
  `web_render.py`.

## 5. Organization (mirror the siblings; closed-cover + per-authority + RED gate)

- **Homes (`repo_layout.json` `source_layout`):** new groups `design` (`rendering/design`: loader,
  schema, registry), `webkit` (`rendering/webkit`: components, component_css, charts, layout,
  design_render_adapter), `showcase` (`rendering/showcase`: render_showcase, render_settings);
  `quality` gains `design_invariants.py`; `contracts` gains `design_predicates.py`. The NEW `site_layout`
  closed cover (DONE in P5-0-FINISH) gates `site/*.html` (allowlist index/showcase/settings) — closing
  the gap that the meta-gate was inert for non-`scripts/**/*.py`. **(codex must-fix #1: `assets/` is
  STILL ungoverned — the `assets/receipts/<lang>/` closed cover is NOT yet declared; it lands RED-first
  in the 1b slice that first WRITES a receipt, so an undeclared receipt reddens. P5-0-FINISH gated ONLY
  `site/`.)**
- **3-PLACE test registration (codex must-fix #5)** for every new design test: (a) `repo_layout.json`
  `test_layout.contracts.members`, (b) `tests_layout_contract.py` `TEST_GROUPS['contracts']`, AND
  (c) a governing authority in `DESIGN_CONTRACT_GROUPS` — `test_tests_layout_contract` enforces
  set-equality, so missing any one reddens. New authorities: `design_profiles`, `webkit`, `showcase`,
  `settings`; `design_languages` gains the per-component character/distinctness rows.
- **Bootstrap RED-first gate** runs first every slice (mutation ⇒ named executable RED; shape/move ⇒
  RED is `test_structural_layout`); declaring the new file's home is the SAME slice.
- **Cuts (right-sized for this repo):** NO 45-lane sprawl, NO claim_intake/authority_leak/relay
  plumbing, NO Rust subprocess. One runner, one predicate library, one schema, one prove lane.

## 6. The skill (repeatable RED-first driver, portable in DISCIPLINE)

`skills/design-language-tdd/` gains lanes: `doctrine-ingest` (docs/examples/screenshots→candidate
obligation packet: typed axes + negative_cases + refute_by + receipt_obligation), `add-design-language`
(obligations→`docs/design/<lang>.md`→profile JSON→RED), `add-component` (DONE), `add-aspect-contract`,
and `prove-theme` (GREEN + mutation + true-viewport receipts + codex). Org gate baked in. The portable
half (predicate LOGIC, profile schema, roster shape, runner, LAW shapes) is portable in DISCIPLINE.
**(codex must-fix #6: "zero repo literals" is NOT literally true today — the skill/boundaries TEXT
names this repo's paths (`repo_layout.json`, `DESIGN_CONTRACT_GROUPS`, `bootstrap_red_ref`,
`design_predicates.py`). On lift to scout those paths get templated / isolated into a "this-repo
bindings" section; the governance shape lifts, the paths don't — reword, don't overclaim.)** The
profile-specific half (`design_render_adapter`, token values, receipts) stays.

## 7. Phased build order (RED-first; each: name RED → declare homes+authority → implement → prove+mutation → receipt → codex)

1. **P5-0-FINISH** ✅ — gated `site/` with a NEW `site_layout` closed cover (a BESPOKE root+allowlist
   method, NOT an `_ENUMERATED` extension — codex R7, since `site/` isn't a groups shape) + an
   anti-tautology forge test; green over `index.html`. (Did NOT add an assets/receipts home — 1b.)
2. **P5-PROFILE-SPINE** ✅ (split: SPINE-a data-skeleton + SPINE-b DTCG loader) — `test_design_profiles_
   schema` RED; `_index`/roster/liquid-glass envelope + closed 18-aspect cover; the DTCG-subset loader
   aliases liquid-glass into config (single source, no literal copy) + DERIVED-PARITY (resolved==config).
3. **P5-WEBKIT-BUTTON** (instance #1, split greens): 1a-i ✅ `render_button` seam + liquid-glass
   character; 1a-ii-A ✅ carbon (label-left/icon-right DOM, radius 0, token-swap, square focus, flat) +
   pairwise distinctness fingerprint; 1a-ii-B ✅ apple-dark (aliases `THEMES['apple-dark']`, opaque-fill,
   opacity-dim, rounded-system-ring); **1b ✅** conform()+predicate library+adapter+receipts (codex folded
   4 honesty must-fixes: adapter fails-closed on empty CSS, mutually-exclusive mechanic, 2px-inset focus
   geometry, per-status honest claim — each RED-proven); **1c ✅** `render_showcase()` → `site/showcase.html`
   renders the committed receipts (real button per language + receipt-driven verdict table; `candidate`
   stamped "cannot certify", never fake-green), closed-cover + drift-guarded + mutation-proven. 210 green.
   Constants doc-grounded against PRIMARY URLs first (`docs/design/<lang>.md`); `[derived]` marked.
   fingerprint over {radius, state_mechanic, focus_recipe, anatomy, **material**, **elevation**}.
   **Codex audit guards (must land in the named slice):**
   - **1a-ii-B (apple-dark):** apple-dark aliases `design_tokens.THEMES['apple-dark']`; Carbon owns
     literal profile tokens and the public web bridge projects them now that Carbon is active. Do NOT
     hand-type a duplicate apple-dark palette; the loader aliases `THEMES['apple-dark']`
     (`derived_from: "theme:apple-dark"`) with a derived-parity test (codex H1). Give it a
     DISTINCT `material` so its button fingerprint clears the ≥3 quorum with MARGIN vs liquid-glass, not
     exactly 3 (codex H2). No new render branch needed (rounded-system-ring + opacity-dim already exist).
   - **1b (conform):** flip roster `component-button` deferred→emitted ONLY in the same commit that lands
     a mutation-proven deterministic predicate (codex H3); keep `contrast`/`responsive` `candidate`
     (never fake-green over glass); AND add the `assets/receipts/<lang>/` closed cover RED-first BEFORE
     writing the first receipt (codex must-fix #1 — `assets/` is currently ungoverned). Gather boundary:
     geometry/radius/shadow/focus/elevation static-parse deterministic; contrast/responsive candidate.
   - **1c (showcase):** verdicts from receipt-JSON only; `candidate` cells rendered with the R5 "cannot
     certify" label — do NOT couple to the nonexistent Playwright/PNG probe (codex H4).
4. **P5-SHOWCASE** ✅ — `test_showcase_coverage` RED-first; `render_showcase` reads the receipts +
   badges each cell (per-section multiset closed cover + drift guard + honest "cannot certify");
   the stage renders each language's real button + chip. (Per-language pages are demoted to internal
   receipt fixtures only; public theme options stay on `site/index.html`.)
5. **P5-COMPONENTS-GROW** — one component per slice via the skill (chip, card, kpi, input, nav, table,
   chart, hero, type-specimen): data rows + only-new predicates + cells. **chip ✅** (instance #2:
   render_chip anatomy branch [Carbon dismissible Tag vs Apple centered pill], chip_facts adapter,
   conform() generalized via `_COMPONENT_FACTS`, chip_sentence_case + neutral predicate aliases,
   component-chip emitted in all 3 profiles, doc-grounded from primary docs, fingerprint pairwise
   ≥3-distinct, mutation-proven, codex-reviewed). **card ✅** (instance #3 — THE DEEPER-REFRAME answer
   to "giant KPI boxes are 100% AI": the grouped-metric PATTERN. render_card = ONE container + N
   CHROME-LESS rows (label+value, hierarchy from type); NEW deterministic pattern predicates
   card_single_container / card_multi_row / card_hairline_divided / card_rows_inline make the
   "grid-of-chromed-tiles / one-box-per-stat" AI look STRUCTURALLY UNCONSTRUCTABLE; "content fills
   the card" ships `candidate`+visual-receipt, NEVER a fake-green static number (the string-green
   trap). Apple inset grouped list [insetGrouped LITERAL] vs Carbon flat square Tile ["do not add a
   drop shadow to tiles" LITERAL]. Distinctness = two HONEST walls (material glass↔opaque; shape
   square↔rounded), NOT a padded quorum — the near-pair rests on material alone, per the research.
   Mutation-proven, codex-reviewed). NEXT: kpi / input / nav via the skill, then P5-SETTINGS.
6. **P5-SETTINGS** ✅ — the governed control plane (picked next by an ultracode judge-panel + codex
   cross-check, over P5-DATA — the owner froze the scorecard). `compose(base, overrides)` +
   `is_admissible()` (`scripts/quality/settings_admissibility.py`) are the ONE Python decider;
   `render_settings()` → `site/settings.html` DISPLAYS the computed admissible space with NO verdict
   JS. An INVALID combination is UNCONSTRUCTABLE: a composed component is admissible only if, AS
   RENDERED, it satisfies some active language's emitted invariants AND matches that language's full
   fingerprint (so an override on an axis with no invariant can't slip). Honest, not a rubber stamp —
   `admissible_space()` COMPUTES 25 admissible + 2 unconstructable (frosted button/chip can't
   transplant onto a non-glass base). Routed through the real render→conform path, which required the
   **enabling first RED: the anatomy gatherer hardened fail-closed** (empty render → anatomy None).
   Codex cross-check REVISE folded (5 fail-open holes: empty-element anatomy, `backdrop-filter:none`,
   `1px solid transparent` divider, conform-by-name avoided, uncovered-axis fingerprint completeness).
   Mutation-proven; the render_* seams gained a `profile_data` injection for in-memory composed profiles.
   (DEFERRED to a follow-up: the interactive URL/localStorage UI + persistence; the visual "looks
   right" verdict stays candidate → the receipt gate.)
7. **P5-THEME-ROSTER-AUTHORITY** ✅ — `_index.json.active_design_profiles` is the ONE public roster
   authority. `design_tokens.py` is now the web projection bridge keyed exactly to active profiles, and
   `site/index.html` exposes exactly that set (`liquid-glass`, `carbon`, `apple-dark`) from one canonical
   theme selector. Reserved profiles (including `power-bi`) cannot leak into the public switcher; the RED
   contract binds `THEMES` / `THEME_META` / `MATERIALS` / `THEME_IA` + generated HTML to the active roster.
   Carbon is now a public option, but its palette/radius remain profile-owned and projected into the bridge.
8. **P5-THEMES-4-10** — via the skill: Material 3, Fluent 2, Polaris, Atlassian, Linear, Geist, Stripe
   — each a profile JSON + cited doctrine doc + usually zero new predicates + optional internal receipt
   fixture, NOT a separate public product page.
   **Pre-theme hardening now folded:** button focus uses the same mutually-exclusive signal counting
   as chip focus (ambiguous rings → None), and the anti-convergence gate is bound to RENDERED
   button/chip/card fingerprints, with declared `components.*.fingerprint` checked only for
   consistency. The skill now begins with `doctrine-ingest.md`, so Scout emits obligations (typed axes,
   negative cases, `refute_by`, visual receipt obligations), not summaries. A model can still propose
   profile data, but distinctness is decided by observed rendered facts, not JSON self-reporting.
9. **P5-RECEIPT-GATE** ✅ (obligation layer) — every deferred/judgment row now carries structured
   `receipt_obligation` + `refute_by`; `conform()` serializes those into the committed receipts with
   `receipt_status: pending|present`, and `showcase.html` surfaces the pending artifact path beside
   "cannot certify". This makes visual/runtime claims executable debt instead of prose. NEXT: build the
   actual headless contrast probes + viewport PNG producers so pending obligations become present
   receipts without promoting fake static greens.

## 8. Deferred until instance #1 + one archetype actually ship (codex must-fix #7)

Self-closing `xfail(strict)` per-theme convergence promotion; the full 10 archetype pages; the
`add-component`/`add-aspect` skill lanes; any `[[accepted_debt]]` expiry machinery. **Draw the
per-archetype deterministic-vs-visual-judgment split BEFORE building theme 4** so layout-feel is never
over-claimed as deterministic (Carbon UI-Shell / Power BI 1280×720 chrome are largely visual judgment).

## 9. Codex must-fixes (workflow `w17p9c4rv`) — where each lands

1 gather boundary → §1/§7-3 (contrast/responsive = candidate until a probe slice). 2 settings
pre-bake/JS-parity → §7-6. 3 split the button → §7-3. 4 reconcile (this doc supersedes ACTIVE.md's
typed `design/languages/*.py` source; JSON is the single source) + slim ACTIVE.md toward its 120-line
cap → ACTIVE.md edit. 5 three-place test registration → §5. 6 edit `_ENUMERATED` for `site_layout` →
§7-1. 7 defer ceremony → §8.

## 10. Best-practice review (research `wkmog3t63` + codex: **APPROACH-SOUND**) — additive refinements

External web-research (W3C DTCG, Style Dictionary, Storybook/Chromatic/axe-core, contrast-over-
translucency, living/governed design systems) + adversarial codex both returned **approach-sound, no
material rethink**: profile-as-data + thin loader = the DTCG/USWDS direction; the gather→decide split
IS axe-core's checks-vs-rules + the W3C ACT Rules Format; the pass/fail/candidate triad IS axe
`pass/fail/incomplete` = ACT `passed/failed/cantTell` (the recognized honest posture, not a hack); the
deterministic slice EXCEEDS Chromatic (machine verdicts vs human pixel-approval); the closed-cover
roster = Vanilla-Extract `createThemeContract`; the unconstructable-invalid settings = mature
constraint-based CPQ / make-illegal-states-unrepresentable, correctly kept at the `conform()` RUNTIME
layer. The refinements below are ADDITIVE and binding; they AMEND the sections noted.

- **R1 — adopt the W3C DTCG FORMAT for the token block (amends §2; high).** Shape each profile's token
  sub-block to the **W3C Design Tokens Format Module (2025.10)**: `$value`/`$type`/`$description`,
  group-level `$type` inheritance, `{alias}` curly-brace refs as the mechanism behind `derived_from`,
  and the closed type vocab (`dimension {value,unit}` for spacing/radius, `duration`+`cubicBezier` for
  motion, `shadow` composite for elevation, `number` for the ramp, `color` for roles). **It's just JSON
  — zero node cost** (the no-npm constraint forbids the TOOLS, not the FORMAT). The spec explicitly
  scopes theming/components/computation OUT, so `invariants[]`/`anatomy`/`fingerprint`/`archetype`/`ia`/
  roster stay **bespoke at profile TOP-LEVEL** (NEVER buried in `$extensions` — that would hide the
  load-bearing partition from the tools whose recognition is the only reason to align). `loader.py` is a
  ~50-line **DTCG-SUBSET** resolver: `{alias}` resolution + typed primitives + only the shadow/motion
  composites actually needed; **defer** `$ref` JSON-Pointer sub-addressing + chained-alias edge cases so
  it stays thin (codex). Buys: predicates read already-typed facts, a free `.tokens.json` export path
  LATER (no tool imported now), and a W3C-citable single-source claim.
- **R2 — reclaim glass contrast out of blanket-candidate (amends §1/§7-3; high), GATED.** Contrast is
  DETERMINISTIC when the background stack is statically known + opaque-or-flat-alpha: port axe-core's
  `flattenColors` alpha-composite + WCAG2 luminance into `design_predicates.py`, PLUS a Lea-Verou
  contrast-BOUND predicate (composite the translucent stack over pure black AND pure white, assert the
  guaranteed LOWER bound ≥ threshold — browser-free). It stays **candidate ONLY** for `backdrop-filter`
  blur over arbitrary content / gradient / image / dynamic stacking — exactly axe-core's own `incomplete`
  set. **HARD GATE (codex):** deterministic green is claimable only once (a) `_contrast` is promoted to
  importable source, (b) it gains alpha-compositing (today opaque-6-hex-only), and (c) the adapter emits
  a statically-known `resolved_bg_stack` fact. Until all three, contrast stays candidate; **liquid-glass
  WITH blur always stays candidate.** Claiming deterministic green before that would itself be a fake-green.
- **R3 — promote the proven helpers to source (amends §3; medium).** `_contrast`/`_is_chromatic`/
  `_signature` currently live in `tests/` (test_theme_system, test_design_distinctness), so the predicate
  library cannot import them. Move them to `scripts/contracts/` source with a **clean import redirect** so
  the existing tests keep passing; extend `_contrast` with alpha-compositing (for R2).
- **R4 — NAME + budget the visual/probe layer; it does NOT exist yet (amends §1/§4/§7-8; high).** The
  repo is **SVG-only** — no headless, no Playwright, no PNGs (`requirements.txt` = requests+jinja2). The
  Seam-4 judgment receipts + the probe slice are net-new infra. Adopt **Playwright-for-Python** as the
  single sanctioned browser tool (pip, bundles its OWN browser, **NOT a node chain — "no node" ≠ "no
  browser"**) for PNG receipts + the probe (computed contrast on the real render, `responsive_no_clip`,
  optionally a single vendored `axe.min.js` injected at runtime). **Codex hard pins:** gate it to a
  **manual/`prove` lane, NEVER the hourly regeneration CI**; keep the probe slice **OPTIONAL** so the
  portable-to-scout half installs + passes on jinja2/requests/pytest alone; declare **Pillow** in
  requirements (present in .venv, undeclared) and use a Pillow-only pixel-diff with a tolerance threshold
  (no numpy); generate PNG baselines in the SAME environment they're diffed against.
- **R5 — label status with the ACT/axe lineage (amends §1/§4; medium).** Map `InvariantResult.status` to
  `passed/failed/cantTell`; in the showcase legend, frame the candidate cells as the portion automation
  "cannot certify" and cite axe-core `incomplete` + its ~57% auto-coverage. Turns candidate from a
  perceived weakness into a standards-conformant, citable honesty claim.
- **R6 — settings: PRE-BAKE (amends §7-6; resolves prior must-fix #2).** Pre-bake the admissible combo
  space from the SAME Python `conform()` (ONE engine; the UI only reflects/disables what it rejects — the
  canonical CPQ configurator shape). A JS mirror only as a last resort, restricted to deterministic
  predicates, WITH a committed Python↔JS parity test. The constraint stays at the `conform()` runtime
  layer, never baked into types.
- **R7 — `_ENUMERATED` honesty (amends §7-1; codex correction).** `_ENUMERATED=('source_layout',
  'test_layout')` deliberately omits `contracts_layout`, which is NOT inert (it has its own
  `test_every_contract_json_has_a_declared_home` over a `group_dirs` shape). So `site_layout` joins the
  `_ENUMERATED` loop **only if** it shares the `groups`/`target_dir`/`placement_enforced` shape; otherwise
  it gets a bespoke method like `contracts_layout`. Do not blindly extend the tuple.

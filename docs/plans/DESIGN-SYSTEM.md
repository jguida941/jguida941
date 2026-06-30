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
  `design_profiles.json` style). `scripts/rendering/design/loader.py` validates + hydrates a frozen
  typed VIEW. No design values live in Python; `design_tokens.py` becomes a config-derived shim and
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
(schema validity, aspect-roster set-equality, emitted/deferred counts, index↔files parity both
directions) + a DERIVED-PARITY assertion (liquid-glass tokens/IA == `config.py`).

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
  archetype pages `site/showcase/<lang>.html` (each a different *kind* of website). Closed-cover
  guard `test_showcase_coverage.py`: declared cells == rendered cells (both directions); drift-guarded.
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
  `quality` gains `design_invariants.py`; `contracts` gains `design_predicates.py`. NEW `site_layout`
  closed cover gates `site/*.html` (allowlist index/showcase/settings) + an `assets/receipts/<lang>/`
  home — closing the gap that the meta-gate was inert for non-`scripts/**/*.py`.
- **3-PLACE test registration (codex must-fix #5)** for every new design test: (a) `repo_layout.json`
  `test_layout.contracts.members`, (b) `tests_layout_contract.py` `TEST_GROUPS['contracts']`, AND
  (c) a governing authority in `DESIGN_CONTRACT_GROUPS` — `test_tests_layout_contract` enforces
  set-equality, so missing any one reddens. New authorities: `design_profiles`, `webkit`, `showcase`,
  `settings`; `design_languages` gains the per-component character/distinctness rows.
- **Bootstrap RED-first gate** runs first every slice (mutation ⇒ named executable RED; shape/move ⇒
  RED is `test_structural_layout`); declaring the new file's home is the SAME slice.
- **Cuts (right-sized for this repo):** NO 45-lane sprawl, NO claim_intake/authority_leak/relay
  plumbing, NO Rust subprocess. One runner, one predicate library, one schema, one prove lane.

## 6. The skill (repeatable RED-first driver, repo-literal-free)

`skills/design-language-tdd/` gains lanes: `add-design-language` (research→cited doctrine
`docs/design/<lang>.md`→profile JSON→RED), `add-component`, `add-aspect-contract`, and `prove-theme`
(GREEN both surfaces + mutation + true-viewport receipts + codex). Org gate baked in. The portable
half (skill, predicates, schema, roster, runner, templates) carries **zero repo literals** so it
lifts to scout; the profile-specific half (`design_render_adapter`, token values, receipts) stays.

## 7. Phased build order (RED-first; each: name RED → declare homes+authority → implement → prove+mutation → receipt → codex)

1. **P5-0-FINISH** — gate `site/`: extend `test_structural_layout._ENUMERATED` to include a new
   `site_layout` section (editing the LAW, not just data — codex must-fix #6) + `assets/receipts/`;
   prove a forged undeclared `site/*.html` reddens; green over the existing single `index.html`.
2. **P5-PROFILE-SPINE** (data, no render) — `test_design_profiles_schema` RED; schema + roster
   (button emitted, rest deferred) + liquid-glass profile `derived_from: config`; DERIVED-PARITY test.
3. **P5-WEBKIT-BUTTON** (instance #1, **split into 3 greens** — codex must-fix #3): (3a) `render_button`
   emits visible HTML (RED=ModuleNotFoundError) with the anatomy hook; (3b) runner + button predicates
   stamp it (carbon radius:0+token-swap+2px-square-focus+zero-shadow; liquid capsule+glass+spring;
   apple capsule+opacity-dim+zero-shadow); (3c) the first showcase cells + receipt. Verify carbon +
   apple + liquid constants against PRIMARY doc URLs first → `docs/design/<lang>.md` cites; mark
   `[derived]`. distinctness_fingerprint over {radius, state_mechanic, focus_recipe, anatomy,
   **elevation**}. **Gather boundary pinned (codex must-fix #1):** geometry/radius/shadow/focus/
   elevation are static-parse deterministic; `contrast_on_actual_bg` + `responsive_no_clip` ship as
   **judgment/candidate** until a declared headless-probe slice — never fake-green over glass.
4. **P5-SHOWCASE** — `test_showcase_coverage` RED; `render_showcase` reads receipts + badges cells;
   drift-guarded.
5. **P5-COMPONENTS-GROW** — one component per slice via the skill (chip, card, kpi, input, nav, table,
   chart, hero, type-specimen): data rows + only-new predicates + cells.
6. **P5-SETTINGS** — `test_settings_composition` RED; compose→conform→reject-invalid→persist. **Decide
   pre-bake-vs-JS-mirror (codex must-fix #2):** pre-bake the admissible combo space (one Python source)
   OR a JS mirror of only the deterministic predicates WITH a committed parity test — never a second
   verdict source that can disagree with Python.
7. **P5-THEMES-4-10** — via the skill: Material 3, Fluent 2, Polaris, Atlassian, Linear, Geist, Stripe
   — each a profile JSON + cited doctrine doc + usually zero new predicates + an archetype page;
   distinctness fingerprint forbids convergence.
8. **P5-RECEIPT-GATE** — make the true-viewport visual/runtime receipt a REQUIRED prove-lane step
   (the apple-heat 500px-clamp lesson); one `prove` lane = runner + pytest + regen + coverage + drift.

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

# ACTIVE PLAN — Phase 5: Organization-as-invariant + governed multi-theme design-language system

> This is the durable, committed source of truth for the current plan and status. The
> ephemeral `~/.claude/plans/*.md` mirror can be lost; THIS file (deployed with the repo)
> cannot. Finished history is folded into `docs/history/PLAN-LEDGER.md`.


## STATUS — where we are (updated each slice)

### CI-RECEIPT-01 — real-browser evidence route (2026-10-16, GREEN candidate / UNACCEPTED)

- **Prior actual RED:** [GitHub Actions 38855651229](https://github.com/jguida941/jguida941/actions/runs/38855651229) at `1ea158e4` executed 424 tests. `test_google_chrome_available_on_linux_runner_is_discoverable` failed with `FileNotFoundError` for a Mac-only `/Applications/Google Chrome` path; the missing-Google-Chrome healthy control remained valid. The other TWO failures are the intentionally stale `index` screenshot/true-390 provenance hashes, unrelated to browser discovery. These are three distinct evidence obligations, not justification for weakening tests.
- **Architecture:** RETAIN the original `scripts.quality.headless_receipts` producer, its PNG/DOM/provenance format and Mac path. IMPROVE only runtime Google Chrome discovery on the existing Linux PR test runner, with genuine version validation, and one fixed `index#ci-observatory` focused screenshot target. Chrome without a genuine binary is still UNAVAILABLE. No Chromium substitute, fake geometry, new runner, privileged action token or output publisher.
- **CI candidate:** Existing `.github/workflows/tests.yml` on the single `development` PR captures 1280 original screenshot, separate focused CI-region screenshot, and true-390 DOM probe with original producer and raw provenance. It runs *after* tests, *before* the fixture smoke generator so synthetic fixture metrics cannot enter the candidate capture. Artifacts upload even if stale committed receipts leave ordinary tests red; these are **candidate-only**, not auto-published or silently accepted. The snapshot currently lacks `ci_timeline`; an actual empty/unavailable screenshot is not proof of a populated chart or visual reference match.
- **Next exact gate:** read actual PR CI run/artifact and Chrome logs; ensure three artifacts have original producer provenance and page source SHA, inspect the focused image and 390 measured containment. Only after independently reviewing real binary bytes, manually commit the **actual** new browser artifacts and rerun tests against tracked receipt hashes. Do not type replacement digests or weaken fail-closed predicates. Real populated public/private Actions observations, 12-month completeness, Safari parity, native methods, and separate reviews remain OWED.
- **Counterfactual:** if Chrome is unavailable or probe finds overflow, the candidate CI step fails and must not be described as visual acceptance. If fixture-generated runs appear, reject the receipt. Return to original selected `JG-CI-VIS-001` after this bounded evidence repair.

### CI-REPO-TIMELINE-01 — ACTIVE / UNACCEPTED (operator visual target, 2026-10-15)

- **One active development line:** `development` was assembled at `dbec9174` from the live multi-repository CI candidate and current `main` generated artifacts. Historical Codex and preview commit DAGs are retained via explicit archive-only merge parents; those obsolete changes are NOT accepted source. Keep `main` stable, preserve `w3-correction`, and do not open another feature branch. Legacy branch refs still exist and require verified retirement after cleanup is possible.
- **Operator references are acceptance requirements, not decorative inspiration:** GIT//INTEL's multi-repository Commit & CI Activity, repository-performance comparisons and workflow signals; Developer Observatory's dated success/failure/queued/cancelled CI Workflow Timeline; Code Chronicle's interactive event timeline and selected-day detail. Layout hierarchy, spacing, theme character, 1280/390 actual browser pixels and real outcomes must be compared before declaring acceptance.
- **Current candidate is narrower, not finished:** the static shared README/Pages SVG has up to six observed **public-only** repository lanes, a bounded 84-day window and at most 20 newest workflow runs per repository. It does NOT prove a full-year timeline, commit density, account-wide action success rate, PR merge percentage, twelve-week trends or selected-day details. Empty provider history is not zero. Existing profile-repository execution list is a useful data canary but visually rejected.
- **Privacy policy correction:** publicly display private repository **names, links, ordinary metadata, and aggregate GitHub Actions / performance metrics** when qualified. Never publish private source, credentials, raw logs or internal evidence. The already-established [private producer / public artifact plan](https://github.com/jguida941/profile-private-continuation/blob/codex/profile-ci-inventory-20261015/records/privacy-output-migration-v1/PLAN.md) is the migration owner. Real protected-Mac P2C full four-page output parity and P2D HTTP diagnostics exist; P3 publisher and P4 public-source minimization remain **OWED**, not implicitly solved by a public-site code change.
- **Real architecture defect identified:** private `product-source/**` CI candidate changed six imported files while the immutable 179-file custody manifest still pins their original blobs. Do not rewrite historical hashes. Preserve the original evidence baseline separately from mutable private development input before claiming `make source-check`, private build or output parity.
- **Selected private goal remains JG-CI-VIS-001, ACTIVE / UNACCEPTED** (A2 queued/paused and unaccepted); reconcile its stale single-profile canary narrative with the operator's full visual/mixed-repo request rather than starting a competing goal.
- **Nearest bounded next slice:** prove one real, mixed-visibility repository/day/actions observation end-to-end using the existing data owners, with named REDs for absent/duplicate/malformed/out-of-window/private-name handling and healthy controls; add a theme-correct accessible visualization in the existing shared projection (not a second frontend). Capture a *populated* CI chart at desktop and true phone, compare against the three source images, run full source/product/CI + mutations, request independent DESIGN/CODE/ADVERSARIAL review, and update this plan + handoff after each admitted slice. All proof gates remain open until actual receipts.

### P5-THEME-MATERIAL-01 — QUEUED / UNACCEPTED (2026-10-16; NOT the selected product slice)

- **Operator reference:** a new Liquid Glass example image was supplied in this conversation on 2026-10-16. It is a visual reference, not a committed browser acceptance receipt or license to replicate arbitrary decoration. Preserve and inspect the original image during the later theme slice; avoid declaring pixel parity against a verbal description.
- **Official design law:** [Apple HIG Materials](https://developer.apple.com/design/human-interface-guidelines/materials) assigns Liquid Glass primarily to a distinct floating navigation/controls layer, not content cards, and recommends sparing use, adapting luminance/contrast to the content beneath it. Standard materials belong in the content layer. `docs/design/apple-dark.md` and `docs/design/liquid-glass.md` already describe these separations.
- **Confirmed source/model contradictions on `development`:** `scripts/rendering/design_tokens.py::MATERIALS["apple-dark"]` currently has `blur=30`, `surface_opacity=.60` and `raised_opacity=.50`, contradicting the source-owned Apple Dark opaque-content doctrine. `scripts/pipeline/web_render.py::_component_css` unconditionally applies `backdrop-filter` and fixed panel shadows across themes and content panels, rather than limiting Liquid Glass to the floating functional layer. `_nav_parts()` always builds `render_nav("liquid-glass", ...)`, although `webkit/components.py::render_nav` has different Carbon/Apple anatomy. The primary `_canonical_profile_picture()` uses the SAME fixed SVG assets for every theme; the CSS selector cannot change the rendered pixels inside the referenced SVG image. The theme switcher lives in the collapsed interactive-detail `_hero`, not on the dominant visible summary. These are concrete contract/projection gaps, not merely subjective differences.
- **Why current tests missed it:** `tests/contracts/test_design_nav.py` checks standalone per-profile renderers and nav presence, not that the selected page actually paints the selected profile. `test_design_character.py` checks token bands and grouped rows, not glass placement in the composed dashboard or active overview. `contracts/design_profiles/design_aspect_roster.json` still defers `charts`, `page-visual-receipt`, `responsive` and related judged aspects; passing deterministic specimen checks is not full theme acceptance.
- **Preserved prior work:** `w3-correction` already carries the operator's historical visual-regression rejection and `tests/contracts/test_theme_continuity.py` with cross-page, bootstrap, anatomy and receipt gates. It was explicitly retained as the old branch; do not delete it, claim it is on development, or wholesale merge it. Inspect and selectively re-prove relevant contracts against live code in the later theme slice.
- **Next theme slice only after appropriate selection/admission:** compare user image and the real 3-theme 1280/390 screenshots on all shipped routes; freeze right-reason REDs and healthy/mutation controls for (1) Apple Dark content is opaque/no glass and no fixed glass-only elevation; (2) Liquid Glass is restrained to floating nav/controls with legible adapted presentation, not chart/data content layers; (3) switching theme changes actually visible overview/navigation geometry, including Carbon's distinct structure, without splitting metric meaning or violating the shared README/Pages data contract; (4) source rendering and screenshot provenance; (5) reduced transparency, contrast and keyboard/focus. Architecture challenge before implementation: evaluate SVG default-card/HTML selected-theme contract versus per-theme artifacts; no invented parallel renderer. Run real Chrome screenshots, independent design/code/adversarial review and preserve a concise source-owned reentry.
- **Priority:** queue this theme/material correction alongside code quality after the current `JG-CI-VIS-001` CI visualization slice. Never interrupt the selected CI work or call current themes fully HIG-compliant on token/specimen tests alone.

### CI-REPO-TIMELINE-01c — received-date coverage guard (candidate, 2026-10-16)

- **RED observed in real GitHub CI:** [PR run 38850647322](https://github.com/jguida941/jguida941/actions/runs/38850647322) at `62c55f3a` ran 419 tests and failed `test_out_of_window_runs_cannot_mean_zero_in_window` (`available` instead of `partial`), `test_future_and_healthy_runs_keep_independent_timeline_meaning` (`available` instead of `partial`), and `test_real_empty_sample_remains_distinct_from_clipped_history` (no `outside_window` field). These are product-semantic failures, not setup errors. The SAME run also observed the separate status-marker-shape RED authored on `0ceb6ec`; do not confuse the two failures or claim a full suite pass from one focused repair.
- **Architecture challenge:** RETAIN the existing one `actions_audit.normalize_public_ci_timeline` source and schema. IMPROVE truthful coverage with one per-repository `outside_window` flag set only for qualified dated run identities outside the inclusive chart window, and downgrade a nominal `available` sample to `partial`. An actually empty provider list remains `empty`, unavailable remains `unavailable`, clipped history is not zero. No second provider/chart renderer and no fabricated CI denominator.
- **GREEN candidate:** fix and tests are committed on the same `development` line after right-reason RED. **Runtime status remains UNVERIFIED until the exact new commit's CI run is read back.** Mutation expectations: deleting the partial downgrade, the clipped flag, or the date check fails one of the frozen controls.
- **Next agent:** recheck HEAD and exact CI outcome, then continue independent status-shape GREEN and populated 1280/390 browser comparison. This guard does NOT prove a 12-month timeline, private-run coverage, real website visual fidelity or independent review.

### P5-DESIGN-OBSERVATORY-01 — QUEUED / UNACCEPTED (Showcase + Studio + Settings, 2026-10-16)

**Operator's directly observed problem:** Three actual 2026-10-16 Safari screenshots in the source conversation show `site/showcase.html` displaying one button/chip/grouped card on a flat black stage followed by a very long pass/candidate table; the visitor cannot explore individual variants, state changes, spatial/material differences or meaningfully connect a law to the component on screen. `site/studio.html` has three language tabs and three swap rows but a large mostly generic mini-marketing page. The user asked for a visually compelling interactive **design-contract demonstration**, with native theme expression, independent component selection, real-time observable changes, and eventually an optional animated/light-reactive backdrop. Visual evidence must use these user screenshots as the before-reference, not invent before/after imagery.

**Verified source problems and real owners:** `scripts/rendering/showcase/showcase.py::_stage_block` renders only one signature button, first chip and first card at rest; `_rows` emits every invariant as a table row with no connection to the preview. `scripts/rendering/studio/studio.py::render_studio` pre-renders exactly one component override at a time and `_STUDIO_JS` hides all other variants whenever any swap is clicked; a user cannot keep a button selection while changing a chip. Both routes use `HOUSE="apple-dark"`, so preview changes do not restyle the surrounding page shell. `docs/design/board.md` and `charts.md` already specify data-driven pre-rendered views and frozen verdict-free lookup; `tests/contracts/test_studio.py` proves composition admissibility is AND of the existing per-slot cells but the UI does not exploit it. `w3-correction` preserves earlier cross-page theme-continuity/before-after research with REVISE verdicts; do not blindly merge it or treat old screenshots as current approval.

**Product direction:** Evolve the existing `Showcase` into the gallery + evidence inspector (what each component, variant, interaction state and rule **looks like**) and `Studio` into a live, explicitly governed composition workbench (what happens as a user swaps **independent** button/chip/card designs, states and profiles). Keep `Settings` as the explanation/admissibility matrix and avoid duplicating that verdict algorithm inside JavaScript. Same profile DATA/renderer/receipt owners: `contracts/design_profiles/<profile>.json` → `webkit/components.py` / `webkit/archetype.py` → `quality/settings_admissibility.py` → static admissible specimens + frozen selection lookups → displayed committed conformance receipts. A browser interaction can report the visible property/state that changed; it CANNOT mint `pass` without a matching already-qualified invariant receipt.

**Bounded slices, in order (each separately admitted RED → GREEN → native/independent review → real Chrome 1280/true-390 receipts → source+handoff update):**

1. **DSO-1, theme continuity and navigation (structural):** freeze wrong/healthy tests proving a selected Apple Dark/Carbon/Liquid Glass theme reaches the page shell, nav anatomy, selected specimen and cross-page links/reload, instead of fixed `HOUSE` or hardcoded liquid nav. Challenge `w3-correction` partial solution against current sources; no visual change is accepted solely because tokens differ.
2. **DSO-2, live Showcase specimen explorer:** pre-render an exact closed roster of each profile's real button/chip/card **variants and states** from their one component renderer; present a compact visual gallery and selectable inspect pane beside the specimen, linking each relevant emitted invariant and source receipt with explicit `pass / fail / cannot certify`. Put the full textual proof table behind expandable detail; preserve all receipt IDs and provenance in DOM (both directions). Predict RED: selecting `pressed` must visibly change the specimen in the profile's correct mechanic, and selecting a law must focus/identify its target; a static signature specimen and always-expanded tall table fail.
3. **DSO-3, independent Studio composition:** selector state is a tuple `(base, button-source, chip-source, card-source, variant, visual-state)`. Use the existing Python `is_admissible`/composition owner to pre-render only admitted combinations or safely composed slots; frozen JS may only select and reveal prepared variants. Predict RED: changing chip after a button swap must preserve the button choice; invalid joint tuples must remain unconstructable; shared CSS must not leak across variants. Keyboard and touch inputs are first-class.
4. **DSO-4, governed ambient/material demonstration (OPTIONAL after 1–3):** experiment with layered moving light/backdrop or short illustrative animation that makes Liquid Glass's background dependence visible while leaving content opaque and readable. No autoplay decorative video, invented refraction claim, off-token CSS or infinite high-motion default. Honor `prefers-reduced-motion`, reduced-transparency/accessibility, pause/play and focus. A real two-background contrast and material response is the acceptance witness; otherwise defer/remove effects.
5. **DSO-5, interaction/receipt matrix:** browser probes on all three active languages and 390/1280 for keyboard, touch, focus, hover/press, reset, permalink/persistence, no page overflow, no stale `pass`, and failure/adversarial vectors. Independent DESIGN/CODE/ADVERSARIAL/FRESH-READER visual review before website/public output acceptance.

**Architecture challenge:** RETAIN existing profile-as-DATA, pure Python renderer, `settings_admissibility`, page manifest, receipt and token owners; IMPROVE their visual projection and real interactions; DEFER an unrelated SPA framework or canvas/video engine until a small native rendering experiment disproves simpler DOM/CSS. Do not reproduce the mockup verbatim with hardcoded numbers. A `pass` table and responsive screenshot do not prove design-system fidelity. **Scheduling:** this remains QUEUED until the selected `JG-CI-VIS-001` multi-repo dashboard slice closes or the work register explicitly selects it; do not create a competing development branch.

### CI-WEB-TIMELINE-01d — visible HTML time-axis candidate (2026-10-16, UNACCEPTED)

- **Real RED:** [GitHub CI 38851321326](https://github.com/jguida941/jguida941/actions/runs/38851321326) at `7a870a97` showed the first of two new design-admission controls failing because `id="ci-observatory"` did not exist; the existing site buried the only CI execution list in collapsed `interactive-details`. The second control requires same `profile-ci-timeline/v1` data, run identities and an observed-day inspector. Other concurrent shape-marker controls were also RED; do not conflate them with this implementation.
- **Architecture choice:** RETAIN one `ci_timeline` source model for README SVG and Pages HTML. The new `web_render.py::_ci_observatory` is a distinct interactive *web projection*, not a second GitHub collector or invented metric source; `hydrateCITimeline` only positions validated existing identities on a UTC axis, groups selected-day observed runs, and emits links built from verified IDs. Keep the SVG parity source unchanged and the rejected profile-only feed available as legacy detail. Source and exact generated `site/index.html` must remain byte identical to `render_dashboard()`.
- **Actual CI result:** [run 38851927235](https://github.com/jguida941/jguida941/actions/runs/38851927235) on `cfcc77c9` ran **422 tests**; all new CI timeline JS/coverage tests passed, including three deliberate wrong-implementation mutant controls (duplicate repository, invalid ID, future run). Overall FAILED because two separate SVG status-shape REDs remain, plus two legitimate **stale index Chrome screenshot/390 DOM receipt hashes** caused by the page change. Neither receipt was fabricated or rewritten. `site/index.html` has the expected generator bytes (no drift failure). Real 1280/true-390 populated browser reference comparison, touch target and marker-overlap review remain PENDING. CSS is token-driven but cross-theme Apple Dark/Liquid Glass material fidelity is separately queued under P5-THEME-MATERIAL-01. The published snapshot may not contain `ci_timeline`; it must explicitly say unavailable rather than fabricate dots.
- **Next:** inspect the exact PR CI and screenshot of the ACTUAL populated CI region, attack hostile provider/date/status samples and keyboard focus/scroll, integrate privately authorized mixed public/private aggregates later under the existing protected Mac publisher contract, and require independent DESIGN/CODE/ADVERSARIAL review before merging or declaring reference parity.


### CI-REPO-TIMELINE-01b — shared SVG outcome geometry (candidate, 2026-10-16)

- **Grounded SemVariants closure seed:** the real [GitHub Actions test run 38852245228](https://github.com/jguida941/jguida941/actions/runs/38852245228) at `c9b08837` ran 422 tests, failed both `test_real_ci_outcomes_use_independent_shapes_on_both_ii` cases on desktop and mobile (expected a `ring` for in-progress, received no `data-shape`), and separately failed two stale page-receipt hashes. Source read at that revision shows `normalize_public_ci_timeline` preserves qualified status but `generate_dashboard_summary._ci_timeline` paints every outcome as `<circle>`; the problem is rendering, not fabricated provider status. Competing explanations considered: wrong oracle (refuted by the operator's multi-shape reference and repo status-by-shape contract), stale/wrong-subject run (refuted by exact HEAD and source), provider state collapse (refuted by existing normalized states), or missing marker anatomy (confirmed).
- **Falsifiable prediction before patch:** both legend and run marks will fail if status is represented by hue alone. Geometry must be distinct: success=filled circle, failure=square, queued=triangle, cancelled=diamond, running=hollow ring, unknown=cross; aliases (timeouts, skipped, attention) inherit their semantic category without inventing an outcome. Actual `<title>` labels must preserve workflow, observed UTC instant and status. Healthy controls retain exact run identifiers on both desktop/mobile and unavailable rows emit no fabricated marks. Wrong-fix predictions: dropping `data-shape` or mapping ring/diamond to success circles is rejected by the frozen existing test; still independently challenge alias/unknown cases.
- **Architecture decision:** RETAIN one existing SVG owner and provider carrier; IMPROVE a single status-marker primitive reused in legend and runs, no extra data collector, duplicate frontend renderer, hardcoded status percentages, or CSS-only color fix. This slice must not change the selected goal or publish private source.
- **Observed exact-commit CI:** [run 38854414501](https://github.com/jguida941/jguida941/actions/runs/38854414501) on SVG geometry commit `2224926230fe8254c56f8a7fafe65c585cdc0e33` executed **422 tests and FAILED (2 failures)**. Both frozen desktop/mobile status-by-shape checks now pass; the only reported failures are the existing `test_ci_index_receipt_is_pinned_and_no_overflow_at_true_390` and `test_committed_headless_page_receipts_are_real_and_provenanced` because generated index hash `bfa865...` differs from pinned receipt `200c72...`. Do not edit the sidecar hash to pass; recapture genuine Chrome 1280 screenshot and measured 390 DOM probe on the actual populated page, inspect the pixel result against the operator's three CI references. SemLoop native RED/GREEN/ATTACK/RESTORE, private Mac exact-SHA run, independent review and publication are **OWED**, not passed. Overall gate stays RED until a later source-bound run passes.

### CI-EXEC-01 — LIVE DATA CANARY, VISUAL REJECTED

- PR #8 merged (`418a2f0`) and deployed with actual profile-repo Actions
  evidence. Operator rejected its visual presentation. Preserve the useful
  observed-data contract; replace the generic run-list presentation in bounded
  reviewed slices. Technical tests do not prove visual quality.

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
- ✅ **P5-THEME-ROSTER-AUTHORITY (supersedes the old public Power BI theme experiment)** —
  `contracts/design_profiles/_index.json.active_design_profiles` is the public roster authority;
  `site/index.html` remains the one canonical public surface with one selector exposing exactly
  `liquid-glass`, `carbon`, and `apple-dark`. `power-bi` is reserved-only until it has an active
  profile; no `[data-theme="power-bi"]` public switch path or `lang-table` branch ships now.
- ✅ **P5-RECEIPT-GATE (obligation layer)** — visual/runtime candidate rows are no longer loose
  prose. Each deferred invariant now declares `receipt_obligation` + `refute_by`; conformance
  receipts serialize `receipt_status: pending|present`, and `showcase.html` displays the pending
  proof artifact beside "cannot certify". Actual headless probes/screenshots are the next layer.
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
- ✅ **P5 private authoring process (historical)** — Its procedural files and reference lanes are maintained in authenticated private source, not the public checkout. Public theme behavior and runtime contracts remain in this repository, which has no dependency on those private method files.
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
every state) + proof/receipt surfaces where each language renders its OWN components (an Apple
component looks like Apple, a Stripe component like Stripe, a Carbon component like Carbon), each built from that language's
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
  viewport` (RED-first, mutation-proven). 179 green. VERIFIED by a headless DOM probe at a TRUE 390px
  viewport (iframe — Chrome headless otherwise clamps to 500px and skips the phone breakpoint):
  `documentElement.scrollWidth == clientWidth`, **PAGE_OVERFLOW=0, zero uncontained culprits**, and
  apple-dark correctly drops the heatmap. The "residual overflow" + "apple-heat runtime defeat" I feared
  were both 500px-clamp ARTIFACTS, not real bugs — measuring at the true width avoided two wrong fixes
  (unnecessary `!important` + min-width:0 containment). Receipt: `scratchpad/receipts/apple390_clean.png`.

- ✅ **P5-DATA slice 1 (semantic-TDD on the metrics — the 204-day lie)** — the freshness figure was a
  median across all ~68 public repos presented as "since last push", reading as months of inactivity while
  pushes happened TODAY. Added `days_since_last_push` (the FRESHEST repo = the true last push) in
  `compute_metrics`; the scorecard + dashboard now present "Last Push · days since last commit" (honest),
  median kept in raw data only. NEW `tests/contracts/test_data_semantics.py` (new `data_semantics` authority):
  a real unit test on `_build_engineering_metrics` (freshest <= median, pushed-today => 0) + presentation-
  honesty (no metric pairs a last-push label with the median key; the dashboard binds the honest metric).
  RED-first (all 3 bit). 183 green. (Next P5-DATA: plausibility + cross-consistency sweep over the rest.)

- ✅ **P5-PATTERN slice 0 (retire a BAD invariant — the empty "When I Code" panel)** — the owner caught
  Apple Dark's activity-rhythm panel rendering near-empty. Cause: slice 5's `test_apple_drops_the_dense_
  heatmap_grid` told Apple to HIDE the heatmap ("summary-forward"), which deleted the rhythm visualization
  and left a content-poor panel — a DISTINCTNESS invariant producing the content-to-chrome anti-pattern it
  should forbid. Measured (true 390/desktop): panel 181px, heat `display:none`. RETIRED that invariant +
  its CSS; Apple shows the rhythm like every theme (distinctness comes from colour/type/density/material).
  After: panel 364px, heat back, filled. 182 green. **Lesson: distinctness never trumps content-to-chrome.**
- ✅ **P5-PATTERN slice 1 (the de-AI readout — giant KPI boxes GONE, codex-agreed)** — the first PATTERN
  invariant. Doc-grounded via workflow `w497dsesl` (`docs/design/liquid-glass.md`, cited Apple HIG: grouped
  inset lists, Value-1 rows, 44pt row, 1pt hairline @16pt inset, type ramp; derived numbers marked). Codex
  caught two escapes in a geometric formulation + that the research agents read the STALE `~/Downloads` repo
  → folded a COLUMN-INDEPENDENT structural gate (per-metric rows bare, only the group chromed) and re-grounded
  to the real `web_render.py`/`.tiles`. Refactored both readouts (`.tiles`/`.tile` cards → `.mgroup`/`.mrow`
  grouped Value-1 rows; ring/hero exempt). New `test_metric_readout_is_grouped_not_giant_boxes` (RED-first,
  mutation-proven). Retired 3 obsolete `.tiles`-grid invariants + the dead `--tile-min` emission (codex
  must-fixes folded; codex re-reviewed the diff → **VERDICT: agree**). 180 green; before/after visual receipt
  captured. The scorecard reads like an Apple grouped list now, not AI boxes. **Lesson: prove composition
  PATTERNS, not padding tokens.**

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
  → showcase scaffold → themes 4–10 under private authoring guidance → P5-4 settings/customization → P5-6 showcase polish + the
  runtime/visual receipt gate. P5-0 org-gate completion gates the showcase-file homes. The private authoring process was historically exercised on the first three themes.

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

## Access-controlled authoring guidance

Internal design-language authoring methods and supporting reference documents now live outside this public product repository. Public documentation covers the product's architecture and observable outputs; authorized agents load private method instructions from the authenticated continuation.

## Architecture & contract structure → `docs/plans/DESIGN-SYSTEM.md`
The full SELF-DEMONSTRATING design-system architecture — the one `PROFILE→render→invariant→receipt`
data-flow; profile-as-DATA; the conformance runner + predicate library; the showcase + settings as
PROOF surfaces; the closed-cover organization mirroring scout/semantic-tdd; the phased RED-first build
order; the codex-folded must-fixes — now lives in **`docs/plans/DESIGN-SYSTEM.md`** (study+design+codex
workflow `w17p9c4rv`, codex conditional-agree). It SUPERSEDES the earlier typed `design/languages/
<name>.py` + `emit.py`/`spec.py`-as-source sketch: **a design profile is DATA
(`contracts/design_profiles/<lang>.json`); the typed loader is a thin VIEW, never the source** — which
is what makes true single-source, scout-portability, and "new theme = data + zero code" fall out
together. (TODO cleanup: slim this ACTIVE.md toward its declared 120-line cap by folding finished-slice
history into `docs/history/PLAN-LEDGER.md`.)

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

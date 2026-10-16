# CURRENT REENTRY — jguida941 dashboard, 2026-10-15

This section is the authoritative next-agent entry; older July handoff is archived below, not an alternate work selection.

**Refs:** Public `jguida941/jguida941` `development` starts at `dbec9174` (candidate CI commits and newest `main` generated assets, archive-only parents retain old `codex/p024` and preview history); `main` remained `af9731f` when assembled; `w3-correction` preserved. Re-read *live* heads before any edit, and preserve local unpublished work. Obsolete remote branches still need real deletion after verification; do not claim cleanup done or create another work branch. Do not merge unreviewed candidate to `main`.

**Read first:** `AGENTS.md`, `docs/plans/ACTIVE.md`, `docs/DESIGN_SPEC.md`, `docs/design/charts.md`, the latest actual source and tests, then the authenticated private [work selector and selected case](https://github.com/jguida941/profile-private-continuation/blob/codex/profile-ci-inventory-20261015/docs/development/work-slices.toml) (`JG-CI-VIS-001`, selected and unaccepted) and [existing privacy/output plan](https://github.com/jguida941/profile-private-continuation/blob/codex/profile-ci-inventory-20261015/records/privacy-output-migration-v1/PLAN.md). A2 stays paused/unaccepted. No invented new production runner or writer.

**Operator requirement (corrected):** public repository names, including private SemLoop / SemVariants / BlamBridge / SemBridge / CS405 / SemCompose, and *qualified* aggregate metrics are allowed; private **implementation**, credentials, raw logs and sensitive source are not. Private source + protected Mac generator → checked output package → minimally scoped publisher → public profile README/GitHub Pages is already the approved architecture. P2 private output diagnostics have passed; P3/P4 cutover has not.

**Live CI code and gap (the older sentence below predates CI-WEB-TIMELINE-01d):** Existing `scripts/github/actions_audit.py` → `collect_data.py` → `compute_metrics.py` → `scripts/contracts/dashboard_summary.py` → `scripts/rendering/generate_dashboard_summary.py` produces a shared SVG for README and website. The current 84-day/newest-20 public-only timeline is **not** the GIT//INTEL / Developer Observatory / Code Chronicle screen. It lacks mixed-visibility lanes, complete commit+CI matrices, denominator-qualified repo comparison and independently accepted selected-day timeline (a new candidate is implemented outside the old details). The rejected oversized activity list survives in collapsed detail and must not be mistaken for the product. Private `development` at `f119439f` restored all 179 immutable imported blobs and retained six changed candidate files separately under `product-candidate/`. That separation is Git-tree verified; actual private Mac/native CI remains pending.

**Latest bounded CI coverage slice (right-reason RED, GREEN candidate):** On `development`, tests committed `62c55f3a` exposed a false exactness bug: dated Actions rows older/future than the sample window vanished while `normalize_public_ci_timeline` still claimed `available`. [GitHub CI 38850647322](https://github.com/jguida941/jguida941/actions/runs/38850647322) observed all three expected failing controls; separate status-shape REDs were also running. A same-owner collector fix retains an `outside_window` flag and demotes completeness without altering actual empty/unavailable samples. New-window coverage controls passed in CI 38850811975; full suite still RED for other independently authored marker-shape tests. No visual/independent or private Mac acceptance implied. The selected goal is still CI-REPO-TIMELINE-01 / JG-CI-VIS-001, unaccepted.

**Newest CI visual candidate (unit/node observed, browser and independent still pending):** `CI-WEB-TIMELINE-01d` is the first visible, interactive HTML CI time-axis view outside the collapsed legacy feed. RED at [GitHub CI 38851321326](https://github.com/jguida941/jguida941/actions/runs/38851321326) confirmed the plotted `ci-observatory` did not exist. Its GREEN candidate reads only `d.ci_timeline` (the same schema/observed identities as README SVG), gives dated per-repository status markers, and on selection lists only provider-observed runs for that UTC day. No success-rate denominators or 12-month completeness claim. CI run 38851927235 at `cfcc77c9` ran 422 tests; emitted-JS behavior and three wrong-fix mutants passed, as did generated-page drift controls. Four failures remain: two independent SVG marker-shape REDs and stale index 1280 screenshot + true-390 page-receipt hashes. Do NOT patch sidecar hashes. Run actual Chrome producer in the verified Mac checkout, inspect a populated timeline rather than top-only/empty state, and obtain independent review. The HTML dot currently has a 28px target under the stated 44px interactive-target guideline and may overlap densely placed run markers; fix with a measured interaction design, not a cosmetic radius change.

**Current next-slice execution: CI status shapes, exact RED and outstanding acceptance.** Public `development` began this correction at `c9b08837d772`; earlier [GitHub CI 38852245228](https://github.com/jguida941/jguida941/actions/runs/38852245228) executed 422 tests and failed both desktop/mobile CI marker-shape oracles plus two stale `index` Chrome receipt identity checks. Existing SVG `_ci_timeline` used circles for every outcome. The new primitive emits circle/square/triangle/diamond/ring/cross shapes and titles from the *same observed statuses* in legend and run rows, without changing data, static page, or private code authority. This is a **candidate** until the exact resulting HEAD CI is read back. SemVariants case explanation and falsifiable wrong-fix controls are in `docs/plans/ACTIVE.md` CI-REPO-TIMELINE-01b. Native SemLoop and independent reviews remain OWED; no native lifecycle or Mac acceptance is inferred from unit tests. **Immediate next action:** inspect new CI failures, then make the real 1280/390 screenshot + interaction/overflow receipts via the existing Chrome producer on the proper authenticated runner, not by editing provenance JSON; review full visual references and private-build route before promotion. Preserve selected `JG-CI-VIS-001` and active `CI-REPO-TIMELINE-01`.\n\n**Next executable slice:** (1) refresh public `development` and private `development` HEADs and preserve all newer work; (2) inspect the separate SVG marker-shape RED and implement independently with status-by-shape; (3) run genuine Chrome 1280 full page + focused CI-region screenshot, true 390 DOM probe/interaction on a populated, source-qualified Actions sample, refreshing `assets/receipts/pages/index` via the real producer and reviewing all per-theme material/contrast issues; (4) check touch targets, dot overlap, hostile provider/day selection and empty/partial semantics; (5) request separate DESIGN/CODE/ADVERSARIAL verdicts and complete existing private output-only build/publication chain. Remaining 12-month history and public/private repo aggregation require separate observed-source qualification before rate or sparkline display. Keep `main` stable and no extra branches; persist exact code/test/screenshot identities in this handoff after each slice.

**Theme fidelity follow-up (queued, not selected):** Operator supplied a Liquid Glass reference image on 2026-10-16. `docs/plans/ACTIVE.md#p5-theme-material-01--queued--unaccepted-2026-10-16-not-the-selected-product-slice` records source-backed faults: Apple Dark content shares translucent/blurred panel CSS; global glass/shadow is applied even to data cards; the page uses `render_nav("liquid-glass")` for every selected theme; the visible summary remains a static SVG shared across all CSS modes. Official Apple HIG requires restrained floating navigation/controls glass over standard-material content. `w3-correction` contains prior independent continuity/visual-redesign gates, but is archived and not incorporated. When selected later, first add RED tests for actual composed page/viewport behavior and visual evidence, preserve current theme/README metrics parity, and fold code quality/mutations/reviews. DO NOT divert the active CI goal to cosmetic palette edits.

**Queued design-demonstration work (user Safari screenshots, source-audited):** `P5-DESIGN-OBSERVATORY-01` in `docs/plans/ACTIVE.md` now binds five bounded future Studio/Showcase/Settings slices. Current Showcase only renders one static state per profile and dumps all invariant receipts as a long table. Studio's `_STUDIO_JS` can select only one pre-rendered component override; a second swap erases the first, although the Python decider already proves the joint tuple law. The user wants actual live native variant/state exploration, a spatially useful component+receipt inspector, independent joint swapping, theme continuity, and later optionally subtle controlled background/motion demonstration with reduced-motion controls. Screenshots were uploaded in this conversation on 2026-10-16. Preserve `w3-correction` as design evidence (REVISE, not acceptance); implement these sequentially after CI selection, test without inventing conformance verdicts, update handoff after EACH slice. No workbench runtime changes yet.

**Branch retirement status:** Only `development`, `main`, and `w3-correction` should remain eventually. The old feature, Codex, preview refs are still present; their histories are now reachable from `development` and deletion remains unperformed. Use an authenticated branch-delete capability with current-head checks; do not force-reset branches or erase their unpublished work.

## Archived handoff, 2026-07-02 (historical, not the active goal)

# HANDOFF — full state + new-agent reorientation (2026-07-02, post B-1)

## Where things stand (all pushed; main deployed to jguida941.github.io)
- main @ a3ff6ad3 == branch d-board. Suite: **333 tests OK** (`python3 -m unittest discover -s tests -q`).
- Shipped arcs: A1–A5 governed chrome → D-SHELL-0/1/2 (page layout/type/spacing/grouping aspects,
  page manifest, showcase-as-report; see prior section below) → **P5-BOARD B-0 + B-1**:
  - B-0 (0cc65c81): cited doctrine docs `docs/design/{motion,board,charts}.md` + the arc design
    record `docs/plans/handoff/b-0-design.md` (aspect specs, RED banks, Q-rulings, board-probe spec).
  - B-1a (b42704f6): `motion` aspect EMITTED — per-language duration/easing tokens in THEME_IA →
    `--motion-*`/`--ease-*` with provenance + band law [70,700]ms; page transitions tokenized;
    the 2.4s pulse is a DECLARED motion.md §4 exception pending its gate.
  - B-1b (a3ff6ad3): `component-nav` EMITTED — `render_nav` (per-language anatomy from
    `components.nav` DATA; var-based CSS so it passes the no-hex law everywhere); the `.site-nav`
    band connects ALL four pages with `aria-current`; manifest `site-nav` region per page.
- Operator plan (approved): `~/.claude/plans/181-any-form-sprightly-tulip.md` — P5-BOARD arc:
  B-2 free-form board → B-3 multi-view charts → B-4 operator-OK + handoff. B-2/B-3 laws are
  ALREADY RATIFIED in `docs/design/board.md` / `charts.md` + `b-0-design.md`.

## Review debt (run FIRST when codex quota returns — was out until ~20:25)
`codex exec --sandbox read-only` with `docs/plans/handoff/codex-batch-prompt.md` from repo root.
Scope: everything since f004d184 (`git diff f004d184..main`) — D-SHELL-1/2 (346a71d1 is
post-build-unreviewed) AND B-0/B-1 (interim gates were Fable self-review + Opus stand-ins;
attack lists recorded in b-0-design.md + commit messages). Fold findings RED-first.

## Known debt (fold with the codex round or at the B-2 gate)
- showcase.py `_row`: leftover `if True:` scaffold + unused `cite` var.
- `var(--motion-*)` referenced by nav CSS is UNDEFINED on shell pages (root_block emits no motion
  vars → transition silently off there). Fold motion vars into `root_block` at B-2.
- Design-lab index panel (P5-INDEX-PANEL) deferred out of B-1b.
- D-SHELL-3/4 backlog: stage shrink-wrap (declared depth-2 gap, pageshell.md §6), settings
  refusal-first, specimen microcopy (E-BTN-LABELS), receipt links, then switcher/themes/completeness
  gate (operator plan file + task board hold the full list).

## NEW-AGENT REORIENTATION PROTOCOL (read in this order; ~30 min)
1. `AGENTS.md` (repo root) — the constitution: roles (Fable/Claude designs+builds+commits; codex
   is REVIEW-ONLY with DESIGN/CODE/ADVERSARIAL verdict lines), the visible-surface law (if it's
   visible, it's governed: surface → candidate law → doctrine/gap → RED → data → render → facts →
   fail-closed predicate → receipt → adversarial review), the MF1 receipt rule, the slice SOP
   (admission gate → RED observed → build → suite → mutation proofs → receipts → gate → commit).
2. THIS file, then `docs/plans/handoff/b-0-design.md` + `d-shell-0-design.md` (+ ADDENDA — the
   ratified laws and gate rulings that BIND current work).
3. The doctrine docs the next slices implement: `docs/design/board.md` (B-2), `charts.md` (B-3),
   `motion.md`, `pageshell.md`.
4. SIBLING REPOS — yes, but TARGETED, read-only (do not wander):
   - `/Users/jguida941/semantic-tdd/docs/developer/operating-guide.md` §0.5 — the canonical
     12-step slice ritual this repo adapts (no local Rust kernel — deliberate, see
     the privately retained design-method boundaries (access-controlled)).
   - `/Users/jguida941/repo-surface-scout/docs/process/WRITING-GOOD-INVARIANTS.md` +
     `SLICE-PROOF-TEMPLATE.md` — RED-for-the-right-reason, gap→pending-contract, surface-to-law.
5. Verify ground truth yourself (never trust this doc over the tree): `git log --oneline -12`,
   run the suite (expect 333 OK), probe codex quota with a one-line exec.
6. Then work: (a) codex retro batch if quota; (b) B-2 per the ratified board.md — new
   `tests/contracts/test_board.py` (3-registry home!), BOARD_DEFAULT parity, frozen `_BOARD_JS`
   (studio-law: embedded data, lookup/persist only), Python collision twin + pinned vectors,
   `chrome-headless-board-probe` receipt kind, manifest `board` region. RED-first, receipts,
   gate, commit to d-board, merge main per clean slice, operator look before B-3.
Working clone: `/Users/jguida941/dev/jguida941` (`~/Downloads/jguida941-main` is a STALE decoy).
Backups: `~/dev/jguida941-backup/`. The session scratchpad dies — everything binding lives here.

---
## Prior handoff (D-SHELL arc, superseded but kept for provenance)
D-SHELL-1 (747d54cd + fold c6c5f3bf): page-layout/type-ramp/spacing-rhythm emitted; .ps-main
980px column; HIG tier; density per language; hairline #38383a; radius 14/12; MF1 receipts
(1280 screenshots + TRUE-390 iframe probes, byte-pinned, fail-closed producer). D-SHELL-2
(346a71d1): page manifest (closed archetype enum, committed-bytes-primary regions) +
page-section-grouping emitted + showcase-as-report (aspect-grouped, quiet-pass/loud-fail).

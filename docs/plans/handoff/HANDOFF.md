# CURRENT REENTRY — jguida941 CI dashboard, 2026-10-16

**This current checkpoint supersedes the archived July handoff below.** The
operator asked for the supplied reference-based multi-repository CI visualization,
not another oversized profile-repo run list. `main` has the rejected CI-EXEC-01
data canary; the selected unaccepted slice is **CI-REPO-TIMELINE-01** on
`feature/profile-multi-repo-ci-timeline-20261015`. Verified starting remote HEAD `07013be1`; always
refresh head and inspect local uncommitted/unpublished work before editing.
Do not reset, assume a past handoff is live, or open a competing timeline branch.

## Owner, files, and visual target

`AGENTS.md` governs the RED-first/mutation/Chrome+390/independent
DESIGN-CODE-ADVERSARIAL review gates. Fable is the implementation owner;
Codex independently reviews. No review has approved this slice yet.
The data flow is `scripts/github/actions_audit.py` -> `collect_data.py` ->
`compute_metrics.py` -> `scripts/contracts/dashboard_summary.py` ->
`scripts/rendering/generate_dashboard_summary.py` -> the same desktop/mobile
SVG bytes on GitHub README and Pages overview. Do not add another projection.

Operator references: GIT//INTEL / Developer Observatory / Code Chronicle.
Their distinguishing requirements: **real repository lanes**, a true chronological
Actions time axis, dots encoding observed run outcomes (shape/label equivalents),
and legible cross-repository visual hierarchy. The figures in the screenshots
are illustrative; never hard-code their success rates or private repo histories.

## CI-REPO-TIMELINE-01a evidence correction

Two independent negative tests were first observed FAILING: repeated repo
observations inflated `observed_runs` (1 became 2); missing `private` metadata
allowed an unverified repository into the public cohort. A dedup/partial guard and
explicit-public admission rule now pass. Existing positive fixture declares
`private: False`. Local focused test group:
`python -m unittest tests.github.test_actions_audit
tests.contracts.test_dashboard_summary tests.contracts.test_readme_projection
tests.contracts.test_web_dashboard -q` -> **88 green**. General
`unittest discover` exceeded the sandbox timeout (many tests advanced),
so no full-green claim is made. Record exact GitHub CI qualification when run.

## Exact next action

1. Refresh the live branch head, `main` drift, local worktree and
   `docs/plans/ACTIVE.md`; do not overwrite newer work.
2. Run focused and full CI plus RED/mutation probes. Verify provider privacy,
   replay dedup, sample limit, stale timestamps and unavailable-vs-zero.
3. Capture **populated, real API** multi-repo timeline at desktop and true phone
   widths. Inspect the CI region, not only the top of the tall profile card.
   Align repo-axis/legend/marker composition to operator references and carry
   honest `<=20` runs/repo limitation; a full 12-month series is NOT proved.
4. Run Chrome 1280 screenshot, 390 DOM horizontal-overflow receipt and source
   identity/pixel review. Don't publish a synthetic/empty-state image as accepted.
5. Get independent DESIGN/CODE/ADVERSARIAL verdicts, fold findings RED first;
   update active plan/handoff with proof and bounded next goal in same commit.
6. Only then consider PR/merge/publication. Next visual slice: 12-month
   referenced timeline and repository comparative metrics, separately proving
   complete denominators before percentages or sparklines.

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

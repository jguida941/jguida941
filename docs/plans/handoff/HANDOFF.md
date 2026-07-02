# HANDOFF — D-SHELL arc state (2026-07-02, operator-directed push at usage limit)

## Where things stand
- main == branch d-shell-1 merged: A1..A5 chrome plumbing + D-SHELL-0/1/2. 325 tests green.
- Protocol: AGENTS.md (repo root) — Fable designs/builds/commits; codex is review-only
  (DESIGN/CODE/ADVERSARIAL gates, machine-checkable verdict lines). Ratified designs + gate
  rulings: docs/plans/handoff/d-shell-0-design.md (+ADDENDUM), d-shell-2-design.md (+ADDENDUM).
- D-SHELL-1 (747d54cd + fold c6c5f3bf): page-layout/type-ramp/spacing-rhythm emitted; .ps-main
  980px column; HIG tier 28/20/15/13; density from THEME_IA per language; hairline #38383a;
  radius 14/12; MF1 receipts (1280 screenshots + TRUE-390 iframe dom-probes, byte-pinned via
  page_sha256, fail-closed producer scripts/quality/headless_receipts.py). Interim stand-in
  review (Opus): REVISE -> all 4 findings folded.
- D-SHELL-2 (346a71d1): contracts/page_manifest.json (intent + closed archetype enum + required
  regions, committed-bytes primary, route parity) + test_page_manifest.py; page-section-grouping
  emitted ({p}-grouping-depth, non-vacuous nesting facts); page-archetype honestly deferred
  (enforcement home named); showcase recomposed (aspect-grouped tbodies, hoisted cites, quiet-pass/
  loud-fail, empty-not-dash). DESIGN gate: REVISE -> folded.
  ** 346a71d1 IS BUILD-COMPLETE BUT POST-BUILD-UNREVIEWED (spend limit killed the stand-in). **

## First action on resume (codex quota back)
Run docs/plans/handoff/codex-batch-prompt.md via `codex exec --sandbox read-only` from repo root.
Diffs to review = git log/diff f004d184..HEAD (A5 -> D-SHELL-2). Fold findings RED-first.

## Known debt (fold with the codex round)
- showcase.py::_row: leftover `if True:` scaffold + unused `cite` var (split-loop artifact).
- The D-SHELL-2 adversarial attack list (unexecuted): nesting parser vs hostile HTML (self-closing
  SVG, unclosed <p>); alias-grammar false positives; mixed-cite landmine when themes add own docs;
  badge-inversion mutation; content-scan over .aspect-head CSS.

## Then, in order (designs/laws already ratified in d-shell-0-design.md)
1. D-SHELL-3 per-page recomposition: stage shrink-wrap (kills the black void + the declared
   depth-2 gap in pageshell.md §6), settings refusal-first (3 grids kept per gate Q3), studio
   instrument-cluster + specimen microcopy (variant-id -> caption; scratchpad e-btn-labels brief
   is folded here), index design-lab panel. MF1 receipts per changed page, in-slice.
2. D-SHELL-4: generalize the receipt gate into roster receipt-obligations.
3. Backlog (approved plan, ~/.claude/plans/181-*.md + tasks): A2-SWITCH chrome switcher, PC-1
   theme-completeness gate, PC-2 docs-currency, B-NAV/C-NAV-BAND, E-BTN-VARIANTS, P2-RECEIPTS,
   themes wave 1 (stripe/linear/geist), P8-README/P9-GALLERY.

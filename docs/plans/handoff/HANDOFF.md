# HANDOFF — reentry card (refreshed 2026-07-16; verify ground truth before trusting)

This is the reentry surface the semantic-tdd sibling registry points at
(`repo_type: adopter`, kernel-free, proof = `python3 -m pytest tests/contracts -q`).
It ORIENTS, never decides: the plan-of-record and the live tree win over this card.

## Read in this order
1. `docs/plans/ACTIVE.md` — THE plan (product statement, DEMO A/B acceptance, orchestration,
   status, slice map). One plan; `contracts/doc_authority_policy.toml` fails closed on sprawl.
2. `AGENTS.md` — the SOP + the role protocol (build routing becomes DATA in `contracts/role_registry.*`
   when the W7 design lands; until then the SOP prose is binding); slice SOP, visible-surface law, MF1 receipts.
3. `docs/plans/handoff/w3-visual-regression-correction.md` — the BINDING gate record (13 design
   must-fixes; bounded slices 0–10). Its 102/39F/13E figure was measured in the DIRTY main
   worktree; the ratchet-authoritative baseline is the CLEAN patched-worktree run: 75 tests /
   7F / 9E / 16 observed identities (see the seed `contracts/correction_baseline.json`).
4. `docs/plans/handoff/w3c-0-design-closure.md` — the slice-0 design record: rev 16 (rev15 max
   review REVISE; r2 xhigh REVISE folded — converged; §16: A+H1 resolved, B–G/H2 pending); §15.
5. Conductor's live continuation record (ignored scratch, the ONLY live scratch plan):
   `scratchpad/work/CONTINUATION-PLAN.md`; lane receipts under `scratchpad/active/<lane>/`.
6. `docs/history/PLAN-LEDGER.md` — folded history + binding doctrine reframes.

## Current truth (2026-07-16 — reverify with `git status` / `git log --oneline -5`)
- Development/integration branch `w3-correction` (base `64b09040`); worktree intentionally dirty
  and preserved. `main` is out of scope: slice 10 is acceptance only; merge/push requires a later
  explicit operator decision after completed-system and receipt review. NO destructive git ops.
- Slice-0 design at rev 16 (r13 "approve" superseded; r14 REVISE folded into rev15; combined
  rev15 + branch-addendum max review REVISE; r2 xhigh REVISE folded — converged, binding verdicts
  = CODE + ADVERSARIAL on the exact landing patch). Slice 0 (text-only) lands via plain-diff
  review → FIRST commit on `w3-correction`; org L1/L2 intake is future work sequenced after it.
- T0 consolidation lands in the slice-0 commit (ACTIVE.md is the single plan-of-record;
  `test_doc_authority.py` the admission RED, witnessed failing on the pre-fold sprawl and
  green in the committed snapshot).
- Odinproject (`/Users/jguida941/repos/odinproject`): O0 `bad950a`, O1-tokenize `e593d28`,
  O2-receipts `037d3e2` (governance only — no design imposed).

## Commands
- Focused correction baseline: the 17-module unittest command in the gate record (lines 292–311).
- Full suite: `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v`.
- Doc law: `python3 -m unittest tests.contracts.test_doc_authority -v`.
- Receipts (Chrome-capable env only): `python -m scripts.quality.headless_receipts`.

## Standing rules
Continuation routing (operator 2026-07-22): `/root` conducts — dispatches, verifies, integrates,
and commits; Fable authors every bounded design and executable RED; Opus builds GREEN only from
packet-bound work; Codex reviews (DESIGN + CODE + ADVERSARIAL) and never codes. Opus read-only
fan-outs; author-never-approves; three gates per slice. Slice lifecycle, role seats, review
gates, and commit authority are governed by `AGENTS.md`.
Everything found in any review folds into ACTIVE.md or the named design record — never a new
plan doc. Session scratch dies; everything binding lives in the tree.

## Known live debt (carried from prior handoff; not yet fixed)
- `scripts/rendering/showcase/showcase.py::_row` — leftover `if True:` scaffold + unused `cite`
  var (fold at a showcase slice). Other prior-arc debt is in `docs/history/PLAN-LEDGER.md`.

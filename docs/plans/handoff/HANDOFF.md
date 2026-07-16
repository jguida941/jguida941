# HANDOFF — reentry card (refreshed 2026-07-15; verify ground truth before trusting)

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
4. `docs/plans/handoff/w3c-0-design-closure.md` — the slice-0 design record: **DESIGN-VERDICT:
   APPROVE (r13, 2026-07-15; rev 14 on disk)**; ratification block §16.
5. `docs/history/PLAN-LEDGER.md` — folded history + binding doctrine reframes.

## Current truth (2026-07-15 — reverify with `git status` / `git log --oneline -5`)
- Branch `w3-correction` (off `main` @ `64b09040`, 3 ahead of origin); worktree heavily dirty
  (intentional, preserved; reconciliation = slice-0 design §13; NO destructive git ops).
- Slice-0 DESIGN gate: **APPROVE (r13)** after r1–r12 REVISE folds. Slice 0 (text-only design/law)
  is LANDING via a plain-diff CODE+ADVERSARIAL review → first commit on `w3-correction`.
- T0 consolidation is STAGED for the slice-0 commit (ACTIVE.md is the single plan-of-record;
  `test_doc_authority.py` the admission RED, witnessed failing on the pre-fold sprawl). It is
  green in the working tree; the slice-0 commit makes it green in the committed snapshot.
- Odinproject (`/Users/jguida941/repos/odinproject`): O0 `bad950a`, O1-tokenize `e593d28`,
  O2-receipts `037d3e2` (governance only — no design imposed).

## Commands
- Focused correction baseline: the 17-module unittest command in the gate record (lines 292–311).
- Full suite: `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v`.
- Doc law: `python3 -m unittest tests.contracts.test_doc_authority -v`.
- Receipts (Chrome-capable env only): `python -m scripts.quality.headless_receipts`.

## Standing rules
Read-only fan-outs run as Opus workers. Opus builds all tiers; Codex reviews (CODE + ADVERSARIAL)
+ DESIGN-gates; author-never-approves. Every slice gets DESIGN + CODE + ADVERSARIAL.
Everything found in any review folds into ACTIVE.md or the named design record — never a new
plan doc. Session scratch dies; everything binding lives in the tree.

## Known live debt (carried from prior handoff; not yet fixed)
- `scripts/rendering/showcase/showcase.py::_row` — leftover `if True:` scaffold + unused `cite`
  var (fold at a showcase slice). Other prior-arc debt is in `docs/history/PLAN-LEDGER.md`.

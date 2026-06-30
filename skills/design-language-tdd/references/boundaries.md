# Boundaries — the honest claim, the determinism split, the org gate, the kernel

These are non-negotiable. They are what make this design governance and not vibes.

## 1. The honest claim (never "is Apple")

The system says: *"We cannot prove this IS Apple. We can prove it satisfies these Apple-derived rules —
here are the receipts."* Every receipt reads "satisfies the `<language>` profile vN across <aspects>".
Every profile carries `authority_status: candidate_only` + `cannot_mark_done: true`. "Apple-style" /
"Power-BI-style" is a CLAIM the design agent proposes; the target repo adjudicates which invariants
become binding.

## 2. The determinism split — NEVER a fake RED

For each candidate invariant ask: *can a deterministic predicate observe this from the rendered artifact
(SVG text nodes / computed CSS / DOM geometry) without human taste?*
- **Yes** → compile a red-now/green-after predicate (`emission_status: emitted`).
- **No** (taste, motion feel, visual rhythm) → a review anchor + a deferred visual-receipt obligation
  (`emission_status: deferred`), NEVER an `assert False` dressed as a RED.

No silent gaps: every roster aspect is emitted OR declared-deferred with a reason. A deferred invariant
that quietly starts passing must fail the suite (xfail-strict) so it gets promoted.

## 3. The org gate (add-the-RED-before-the-file)

No mutation without a named RED. A cleanup/reorg/SHAPE task's RED must be the executable target-shape
contract (`tests/contracts/test_structural_layout.py`). Declare every new file's home in
`contracts/repo_layout.json` in the SAME slice. Check with
`python -m scripts.organization.bootstrap_red_ref "<task text>" "<red ref>"`.

## 4. The kernel decides; this gathers/proposes

This skill (and the repo-side guards) are the verdict-free GATHER/PROPOSE half. semantic-tdd's Rust
kernel is the eventual decider — `preflight.rs` (`MissingRedTestRef`), `plan_graph.rs` (connectivity),
`claim_intake.rs` (evidence-basis), `placement_law.rs` (homing) — reached via the `semproof` CLI. Never
re-implement a kernel verdict in Python; emit the claim and relay the verdict fail-closed.

## Portability

The reusable parts (this skill, the predicate shapes, the character/distinctness laws, the doctrine +
receipt templates) are written to lift cleanly into repo-surface-scout as `candidate_only` profiles.
What stays profile-specific: the concrete render adapter, the per-language token values, the captured
receipts. Keeping the governance logic out of the proof target is the SOP.

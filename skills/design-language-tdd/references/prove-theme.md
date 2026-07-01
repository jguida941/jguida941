# Lane D — prove a theme: GREEN + mutation + receipts + codex → honest receipt

Generation is not done until proven. A theme ships only when it provably expresses its doctrine
obligations, differs from every other active language by rendered facts, and survives adversarial
review.

## Steps

1. **GREEN on rendered obligations.** Run `python -m pytest`. Required checks include conformance
   (`conform()` over emitted invariants), component contracts, render-derived distinctness, profile
   schema, showcase/settings drift, and any projection-specific guards. Regenerate governed artifacts
   only through their generators.
2. **Mutation-prove every deterministic obligation.** For each predicate or rendered-fingerprint axis,
   revert the driving value or render output and confirm a test MUST fail. If nothing fails, the
   invariant is vacuous -> strengthen it. One killed mutant per independent obligation.
3. **Visual receipts.** For every `receipt_obligation.required: true`, render the relevant page or
   specimen in headless Chrome at the declared viewport(s); capture before/after for judgment rows.
   Receipts are the proof for visual rows and confirmation for deterministic rows. No screenshot-only
   claim can be promoted without a committed receipt or explicit candidate-only deferral.
4. **Codex review (cross-provider), folded RED-first.** An independent reviewer (a) re-derives the
   obligation set from `docs/design/<lang>.md` and flags missing axes; (b) probes each predicate for
   vacuity (would it pass on a blank/placeholder render?); (c) checks the determinism split is honest
   (no visual judgment smuggled as deterministic); (d) stress-tests distinctness (could these rendered
   facts also pass as another language?). Every disagreement becomes a NEW RED — never a prose reply.
5. **Honest receipt.** Record "satisfies the `<language>` profile vN across <aspects> — here are the
   receipts," with the invariant → predicate → pass/receipt table. NEVER "is `<language>`".

## Commit discipline (this repo)

Each slice: name the RED → declare the home in `repo_layout.json` (same slice) → implement → GREEN →
visual receipt → codex folded RED-first → commit → CI green → update `docs/plans/ACTIVE.md` STATUS →
keep docs fresh.

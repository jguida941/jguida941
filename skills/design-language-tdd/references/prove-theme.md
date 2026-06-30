# Lane D — prove a theme: GREEN + mutation + receipts + codex → honest receipt

Generation (lane C) is not done until proven. A theme ships only when it provably expresses its
language, differs from every other theme, and survives an adversarial review.

## Steps

1. **GREEN on both surfaces.** `python -m scripts.pipeline.web_render` regenerates `site/index.html`
   (the drift guard requires committed == generated). Run `python -m unittest discover -s tests -q`:
   `test_design_character` (expresses its language), `test_design_distinctness` (differs from every
   other theme), `test_theme_system` (complete + WCAG-AA + bounded), and the web/drift/privacy guards
   all green.
2. **Mutation-prove every predicate.** For each character/distinctness invariant, revert the theme's
   driving value (e.g. collapse Power BI's density/radius to the default, or its table to a bar) and
   confirm a test MUST fail. If nothing fails, the invariant is vacuous → strengthen it. One killed
   mutant per independent invariant.
3. **Visual receipts.** Render the theme in headless Chrome at the breakpoints
   (`--headless=new --screenshot=… "…/index.html?theme=<name>"`); capture before/after for any judgment
   invariant. Receipts are the proof for judgment items and the confirmation for deterministic ones.
4. **Codex review (cross-provider), folded RED-first.** An independent reviewer (a) re-derives the
   closed invariant set from the doctrine doc and flags any MISSING aspect; (b) probes each predicate
   for vacuity (would it pass on a blank/placeholder render?); (c) checks the determinism split is
   honest (no judgment smuggled as deterministic); (d) stress-tests distinctness (could these receipts
   also pass as another language?). Every disagreement becomes a NEW RED — never a prose reply.
5. **Honest receipt.** Record "satisfies the `<language>` profile vN across <aspects> — here are the
   receipts," with the invariant → predicate → pass/receipt table. NEVER "is `<language>`".

## Commit discipline (this repo)

Each slice: name the RED → declare the home in `repo_layout.json` (same slice) → implement → GREEN →
visual receipt → codex folded RED-first → commit → CI green → update `docs/plans/ACTIVE.md` STATUS →
keep docs fresh.

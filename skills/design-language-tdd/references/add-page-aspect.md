# Lane: add-page-aspect

Add or extend a governed page aspect. A visible page surface is not proven by tokens alone: it must
move through the same loop as a component, with any missing judgment left candidate and receipt-backed.

## Surface-to-law loop

1. **Observe the rendered surface.** Start from screenshots and the generated HTML/CSS. Name the page
   intent, regions, defects, and the exact visual claim being made.
2. **Model the candidate law.** Convert the surface claim into a typed law: layout, type ramp,
   spacing rhythm, archetype, grouping, content density, scan path, responsive measure, or visual
   receipt. Keep separate failure names for separate laws.
3. **Ground or declare the gap.** Cite each value to `docs/DESIGN_SPEC.md`, `docs/design/<lang>.md`, or
   the owning doctrine. If a value is empirical, mark it derived. If the claim needs rendered judgment,
   declare a receipt obligation instead of a deterministic predicate.
4. **Write the RED first.** Add the failing contract before source changes. The RED should fail on the
   old surface and on a crafted negative vector, not only on a missing function.
5. **Lower to DATA / RENDER / FACTS / PREDICATE.** Add roster coverage, profile invariants for emitted
   deterministic aspects, render changes, adapter facts, and pure predicates. Do not add green
   placeholder predicates for deferred aspects.
6. **Materialize receipts when the slice changes layout.** Per MF1, any visible layout slice commits
   Chrome-headless screenshots at 1280 width and 390px DOM overflow probes for every changed page,
   with honest provenance sidecars. Missing Chrome must fail closed; never write placeholder
   artifacts.
7. **Prove and mutation-prove.** Run the full suite and kill one mutant per independent law: remove the
   fact source, flatten the ramp, mint a constant, change a cited colour, or force overflow. If the
   mutant stays green, strengthen the law before shipping.

## Aspect split

- `page-layout`: centered column, measure, gutters.
- `page-type-ramp`: tier count and ordering.
- `page-spacing-rhythm`: step-set membership and density-band provenance.
- `page-archetype` + `page-section-grouping`: manifest, regions, grouping, and nesting depth.
- `page-content-density`: dead-space and fill facts.
- `page-scan-path`, `page-responsive-measure`, `page-visual-receipt`: judgment aspects. They require
  receipts and must stay candidate until the receipt gate generalizes.

## Honest boundary

A passing test proves only the encoded law. It does not prove missing page laws, visual quality, or
brand authority. Deferred page aspects need explicit `covered-deferred` coverage and named slice
reasons, never placeholder predicates.

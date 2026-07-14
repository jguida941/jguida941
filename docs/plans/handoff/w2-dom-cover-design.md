# W2 - CLOSED-WORLD DOM COVER design (slice design doc; DESIGN gate input)

Admission observed 2026-07-13: `bootstrap_red_ref` returned `admit: true` for task
"implement closed-world DOM cover", RED `tests/contracts/test_dom_cover.py`.

DESIGN gate round 1: **REVISE**. The review found that source substring checks did not prove an
emitter was on the manifest render path, runtime debt had no executable change detector, the debt
hash/row grammar was underspecified, and W3 could launder debt by attaching a blanket `page.index`
owner. The candidate law and mutation plan below fold all four must-fixes.

DESIGN gate round 2 (after all folds): `DESIGN-VERDICT: APPROVE`.

CODE/ADVERSARIAL round 1: **REVISE**. Finished-diff attacks found that return-value replacement
could mutate passed-through markers, owner ids/emitters were mutable DATA (so `page.dashboard`
could alias-launder index debt), and only index hydration was runtime-pinned while Studio also
mutates classes. Folded RED-first with function-bytecode mint-site mutation plus AST function-scope
uniqueness, an independently pinned admitted owner/emitter and index-owner roster, and a closed
per-manifest inventory/hash of every inline script, external-script/handler bans, and exact runtime
class debt for both index hydration and Studio's toggle.

ADVERSARIAL round 2: **REVISE**. The mint-site sentinel proved the declared emitter was exercised,
but a caller could copy a legitimate marker from that emitter's returned bytes and the copied
sentinel would follow the mutation. The lineage RED now records marker counts in every direct
instrumented invocation before control returns to the caller and requires the final manifest page
to equal their sum. A synthetic copied-return-marker attack is mutation-proven red.

ADVERSARIAL round 3: **REVISE**. The inline-script census omitted classless active embedding
surfaces, so `iframe[srcdoc]` could execute a parent-DOM mutation without changing that census. The
runtime closure now rejects active embedding tags, `srcdoc`, executable URL schemes, meta refresh,
external HTML/SVG script references, and inline handlers on normal or self-closing elements. The
exact classless `srcdoc` parent-mutation attack is a negative RED that leaves the script multiset
unchanged, proving the additional browser-surface guard is non-vacuous.

Final review after all RED-first folds: `VERDICT: approve` and
`ADVERSARIAL-VERDICT: approve`. Exact final suite: 351 tests green.

## Observed surface (the wrongness)

The design predicates govern known component and page-shell renderers, but no closed cover proves
that every class-bearing element in the four committed pages came from one of those renderers.
Coincidental reuse of a governed class can therefore pass a class-name check, and index still owns
dozens of bespoke classes outside the webkit/pageshell path. Runtime index hydration adds another
set of class-bearing elements that cannot be observed by parsing committed start tags alone.

## Candidate law (the RED: `tests/contracts/test_dom_cover.py`)

1. **Explicit ownership, never class-name inference.** Every class-bearing element emitted by a
   governed pageshell, webkit component, or registered page renderer carries
   `data-dom-owner="<closed-id>"`. An owner is valid only on the pages declared for it and only for
   the exact `(page, tag, sorted class tuple, count)` signatures in `contracts/dom_cover.json`.
2. **Emitter binding plus exercised lineage.** Each owner names one `module::function`. The function
   must be the manifest renderer or a transitive governed renderer, its function body must contain
   that exact owner marker, and no other Python function body may mint it. For every declared
   `(page, owner)` edge the RED temporarily wraps that exact callable, substitutes the owner's
   marker with a unique sentinel in its return value, rerenders through the manifest source, and
   requires every expected occurrence (and no unrelated owner) to change. The probe records the
   sentinel count in each direct emitter return before its caller receives the bytes; the final
   page must contain exactly that summed count. This proves the declared emitter was exercised on
   the real page-render path and prevents a caller from extracting and copying a valid child marker.
   A copied `.ps-title` plus a forged `pageshell` marker therefore fails on lineage, source, tag,
   page, or signature.
3. **Committed-page closure.** Page ids/routes equal `page_manifest.json`; every page is reproduced
   byte-for-byte from its declared render source before its DOM is parsed with `HTMLParser`. Every
   static class-bearing start tag is either owned or is one exact active debt fingerprint. Unknown
   owners, duplicate class tokens, phantom signatures, unused owners, undeclared pages, and count
   drift are failures.
4. **Index debt is a ratchet, not an allowlist.** The existing bespoke index fingerprints are
   frozen as exact rows whose only keys are `page`, `tag`, `classes`, `baseline_count`, and
   `resolved_count`. Rows are unique and canonically ordered by `(page, tag, classes)`; classes are
   unique, sorted tokens; counts are integers with `baseline_count > 0` and
   `0 <= resolved_count <= baseline_count`; unknown keys fail. The immutable hash input is canonical
   compact JSON over ONLY `(page, tag, classes, baseline_count)` (never `resolved_count`), pinned in
   the contract and independently as a RED constant. Rows remain after resolution as history.
   Actual unowned counts must equal `baseline_count - resolved_count`. New fingerprints, more uses
   of an existing fingerprint, a class moved to another tag/class set, deletion without resolution,
   malformed/duplicate rows, or simultaneous baseline/count rewriting all fail. W3 must resolve
   every static index row.
5. **Runtime debt is declared, bounded, and temporary.** The contract says this slice covers
   `committed-static-dom` and inventories every inline script on every manifest page as a pinned
   `dom-mutator` or `data-only` producer; a new script, external script, or inline handler fails.
   Classless browser execution surfaces also fail: active embedding tags (`iframe`, `object`,
   `embed`, frames/applets/portals), `srcdoc`, executable URL schemes, meta refresh, and external
   HTML/SVG script references are forbidden rather than left outside the inventory.
   It records exact runtime class debt for index hydration and Studio's toggle. W2 independently
   pins the SHA-256 of the producer bytes in both contract and RED. Any script change therefore
   fails before a new runtime class can enter unnoticed; updating a pin requires explicit RED review
   of the vocabulary. The test extracts index `class="..."` templates and its closed dynamic status
   axis, and extracts Studio's exact `classList` token (`active`). It names W4 as the closing slice
   and may not claim `rendered-dom` until the headless facts stream proves post-hydration closure.
   W4 will replace these source pins with exact rendered
   `(page, theme, viewport, state, tag, classes, owner, count)` facts. The gap is executable and
   visible rather than silently omitted.
6. **Classless/style law remains separate.** This contract covers class-bearing DOM ownership. It
   does not claim that classless nodes or inline declarations are governed; existing literal/token
   guards remain binding, W3 removes index's bespoke CSS surface, and W4 observes rendered boxes and
   computed style. The contract's purpose text states this boundary.

## Ownership model

Closed owner ids:

- `pageshell` -> `scripts.rendering.pageshell.pageshell::render_page_shell`
- `webkit.nav` -> `scripts.rendering.webkit.components::render_switchable_nav`
- `webkit.button` / `webkit.chip` / `webkit.card` -> their component emitters
- `webkit.archetype` -> `scripts.rendering.webkit.archetype::render_archetype`
- `page.settings` / `page.showcase` / `page.studio` -> the corresponding manifest renderer

Index's nav is governed by `webkit.nav`. Its remaining static classes are debt until W3. Page-local
owners are admitted because those functions are the manifest render sources, committed bytes are
already drift-checked, their exact signatures are closed here, and their CSS remains under the
existing page composition/token guards.

There is deliberately NO `page.index` owner in W2. W3 may not resolve a fingerprint by stamping
unchanged bespoke markup with such a blanket marker. A fingerprint resolves only because it was
deleted or because the migrated node is emitted by pageshell/webkit (or a narrowly admitted new
dashboard component with its own DATA/FACTS/PREDICATE guard and explicit resolution evidence).

## Contract shape

`contracts/dom_cover.json` contains:

- schema/contract metadata and `marker_attribute`;
- `coverage` with the current `committed-static-dom` claim and explicit W4 runtime transition;
- `owners`, each with one emitter, allowed pages, and exact per-page signature/count rows;
- `pages`, exactly matching the manifest, with route and debt object;
- index static debt fingerprints plus canonical baseline hash and W3 target;
- bounded hydrated index vocabulary plus W4 target.

Rows and arrays are canonical sorted data. Broad prefixes, regexes, wildcards, token-only debt, and
page-independent signatures are structurally inadmissible.

## RED and mutation plan

The first RED lands with its registry homes and fails because `dom_cover.json` and ownership markers
do not exist. After implementation, the test must independently prove these mutations red:

1. append a new `.rogue` element;
2. put an otherwise valid `pageshell` owner on the wrong tag/signature;
3. use a valid owner on the wrong page;
4. reuse an index debt class on another tag or increment its count;
5. remove index debt without increasing `resolved_count`;
6. expand the frozen debt baseline or runtime vocabulary;
7. add a phantom signature/owner;
8. forge an owner marker outside its declared emitter;
9. replace an emitter's compiled marker literal (not its completed output) with a sentinel and prove
   manifest rerender lineage; a same-module helper/pass-through forgery stays unchanged and reds;
10. mutate/add any manifest script or handler without updating its independently pinned roster;
11. add an off-enum dynamic runtime class;
12. add an unknown ratchet key, violate count bounds, reorder/duplicate a row, or rewrite baseline
    and count together while leaving the active result unchanged;
13. introduce a blanket `page.index` owner for unchanged debt.
14. copy a valid marker attribute out of a child emitter's return onto caller-owned debt.
15. add a classless `iframe[srcdoc]` that executes a parent-DOM insertion while leaving the inline
    script multiset unchanged.

## Render changes

- Add literal owner markers at the renderer that creates each class-bearing element. No generic
  post-render annotator is permitted because it would launder arbitrary injected DOM.
- Regenerate all four pages. Marker attributes are non-visual but page hashes change, so regenerate
  every MF1 receipt and continuity fact/sidecar reached by the shared page bytes.
- Update `docs/design/pageshell.md` and ACTIVE.md with the closed-cover law and the explicit W4
  runtime handoff. The attached plan file is not edited.

## Open forks (decided here; critique welcome)

- **F1 - token catalog vs element signatures.** DECIDED exact element signatures and counts. A
  token allowlist could hide duplicated or structurally moved elements.
- **F2 - postprocessor vs emitter markers.** DECIDED literal emitter markers. A postprocessor would
  assert ownership after the fact without proving which function created the node.
- **F3 - static-only claim vs premature rendered claim.** DECIDED honest static claim plus bounded
  runtime debt in W2, promoted to rendered closure in W4. Receipt scraping is not silently called a
  deterministic predicate before the facts producer and provenance channel exist.
- **F4 - page-local owners vs index debt everywhere.** DECIDED admit registered proof-page emitters
  under exact closure; keep only index as debt because W3 is its already-ratified migration.
- **F5 - debt hash authority.** DECIDED contract hash plus an independent frozen constant in the RED.
  Recomputing a hash from mutable debt and trusting the same file would be vacuous.
- **F6 - runtime source pin vs early browser predicate.** DECIDED pin the exact hydration producer
  plus its closed template/dynamic axes now; W4 replaces that conservative tripwire with observed
  post-hydration facts. This is executable without overstating static parsing as browser truth.
- **F7 - index page owner.** DECIDED forbidden as a blanket W3 escape. Only deletion or migration to
  an already governed/narrowly admitted component can advance `resolved_count`.

## Verification and registry homes

`contracts/dom_cover.json` joins the contracts root allowlist. `test_dom_cover.py` joins
`repo_layout.json`, `tests_layout_contract.TEST_GROUPS["contracts"]`, and
`DESIGN_CONTRACT_GROUPS["page_chrome"]` in the RED slice. Full pytest green; all mutation families
above red; regenerated Chrome 1280 screenshots and 390 probes for every page with honest
provenance; independent CODE and ADVERSARIAL verdicts approve before commit.

# D-SHELL-2 design — page manifest + archetype/grouping + showcase report recomposition
(Fable-authored; DESIGN gate required. Context: D-SHELL-0 ratified [scratchpad/d-shell-0-design.md,
DESIGN-VERDICT: APPROVE + MF1-4 addendum]; D-SHELL-1 committed on branch d-shell-1 @ c6c5f3bf,
317 green. This slice implements the D-SHELL-2 scope named there, on top of d-shell-1.)

## Scope
1. **contracts/page_manifest.json** (ratified MF2 schema): pages[] of {id, route, render_source,
   intent (one sentence), archetype ∈ {landing, proof-report, control-plane, workbench} (CLOSED
   enum), required_regions[], region_aliases{region→CSS-selector hints}, receipt_obligations[]}.
   Entries: index=landing, showcase=proof-report, settings=control-plane, studio=workbench, with
   regions per the D-SHELL-0 surface models (e.g. showcase: orientation, legend, language-section,
   verdict-table, specimen-stage; settings: orientation, law, control-groups; studio: orientation,
   language-switcher, swap-controls, stage). 3-registry home declaration.
2. **PageManifestContract** (new tests/contracts/test_page_manifest.py → 3 registries), fail-closed:
   every generated site/*.html page (site_layout allowlist) has a manifest entry; archetype in the
   closed enum; every required_region resolves to ≥1 rendered element (via region_aliases selector
   → regex/string check against the RENDERED html from the page's render_source, not committed
   bytes); a manifest page whose render lacks a region REDDENS; a page absent from the manifest
   REDDENS (both directions). Negative vectors: an in-memory manifest with a bogus archetype and
   with a missing region must fail.
3. **Roster flips**: page-archetype + page-section-grouping → emitted.
   - page-section-grouping: per-profile conform rows. New FACTS in pageshell_facts: chrome_nesting_depth
     (max depth of chromed boxes — elements whose class matches a rule declaring background+border/
     radius — inside another chromed box in the SHELL render; shell render nests panels only 1 deep).
     Predicate section_grouping_flat: depth ≤ 1, fail-closed. Invariants {p}-grouping-depth ×3 profiles.
   - page-archetype: manifest-backed. _pageshell_facts gains manifest_covers_all_pages +
     archetypes_valid facts (computed once from page_manifest.json + site_layout — identical across
     profiles; honest: it is a SITE property surfaced per profile row, doc_cite pageshell.md).
     Invariant {p}-page-archetype ×3. FORK Q1 below.
4. **Showcase recomposition (the laws L-SHOW-1/2/5 made real, visible half of this slice)**:
   - _rows groups by the aspect field: one <tbody class="aspect-group" data-aspect=…> per aspect
     with a subheader row (aspect name + the group's single doc cite hoisted — kills ~17× repetition);
     row doc cell dropped (cite lives on the group header).
   - Verdict prominence inversion (exception-first): .badge-pass → QUIET (transparent bg,
     var(--status-success) ink + 1px border); .badge-fail/.badge-candidate stay SOLID (loud).
     New deterministic fact/predicate: verdict_prominence_inverted — from the page CSS: the pass
     badge rule must NOT set a solid status background while fail/candidate rules do (string-level
     facts on _CONTENT_CSS, fail-closed). Invariant {p}-verdict-quietpass? — FORK Q2 (page-level law
     vs profile invariant; proposal: showcase-only contract test, NOT a conform row — it is a
     report-surface law, not a language law).
   - Empty receipt cells render EMPTY ("" not "—") — existing coverage tests updated where they
     pin "—" (none known; verify).
   - Existing multiset closed-cover tests (cells == receipt rows per profile) must stay green —
     grouping preserves <tr data-invariant data-status> shape inside the new tbodies.
5. **MF1 receipts**: showcase (and any page whose bytes change) → refresh 1280 screenshot + 390
   dom-probe (byte-pinned, so ALL pages regenerate receipts if shell/site bytes change).
6. Docs same slice: docs/design/pageshell.md gains §archetypes (the four archetypes + region
   requirements, citing the D-SHELL-0 surface models; where doctrine is silent → declared gap
   lines); showcase.md does NOT exist yet (owned by PC-2/docs-currency later) — manifest doc_cites
   point at pageshell.md §archetypes.

## RED bank (observed-failing before implementation)
manifest absent → PageManifestContract errors; bogus-archetype + missing-region in-memory vectors;
showcase table UNGROUPED (regex: no tbody[data-aspect]) → grouping test red; pass badge currently
SOLID → prominence test red; "—" present → empty-cell test red; chrome_nesting_depth fact absent →
conform {p}-grouping-depth rows missing.

## Forks for the gate
Q1 page-archetype as per-profile conform rows carrying a SITE-level fact (3× redundant but visible
on the proof surface) vs manifest-contract-only (roster aspect flips but its law lives in
test_page_manifest, referenced by defer-note)? Proposal: per-profile rows (visible + mutation-
provable), with the fact honestly documented as site-scoped.
Q2 verdict-prominence: profile invariant vs showcase-only contract test? Proposal: contract test
(report-surface law; profiles shouldn't legislate one page's table styling).
Q3 subheader row inside tbody vs separate <thead>-like row: proposal tbody-first-row subheader
(keeps table semantics + the multiset regexes scoped per section).

## ADDENDUM — round-1 gate folds (DESIGN-VERDICT: REVISE → all folded)
MF-A: chrome_nesting_depth defined precisely — chromed class = shell-CSS rule declaring a painting
background (not transparent/none/0-alpha) AND (visible border OR border-radius); balanced tag-stack
depth over the render, unbalanced → None (fail-closed); facts = max depth + chromed_box_count;
predicate = depth is not None AND count >= 1 AND depth <= 1 (count conjunct kills vacuity);
canonical _pageshell_facts render includes one section so a panel exists; RED vector = hand-built
chromed-box-in-chromed-box → depth 2 → False.
MF-B/Q1: FALLBACK form chosen — page_manifest law enforced by test_page_manifest.py only;
page-archetype roster aspect STAYS deferred, defer_reason names the contract as enforcement home
(the conjunction form would duplicate page_has_orientation as padding). Only page-section-grouping
flips to emitted ({p}-grouping-depth ×3).
MF-C: region checks run against COMMITTED site bytes as primary; in-memory negative vectors use
rendered html; plus per-manifest-page rendered==committed assertion inside the contract.
SF-1: mixed cites in a group → generator RAISES; groups aggregate in first-appearance order,
receipt order preserved within (no contiguous groupby). SF-2: subheader = tr.aspect-head >
th[colspan=4][scope=colgroup], no data-attrs. SF-3: three-way route parity (manifest ==
headless_receipts.PAGE_ROUTES == receipts_layout.page_allowlist); alias mini-grammar CLOSED:
".class-token" or "[data-attr]" only, unparseable → fail; aliases written from ACTUAL DOM.
SF-4: slice also edits 3 profile JSONs, roster, _COMPONENT_FACTS. N-3: only showcase receipts +
3 conformance receipts + site/showcase.html regenerate. N-4: {p}-grouping-depth law text is
SHELL-scoped; pageshell.md declares the page-level gap (stage depth-2) landing in D-SHELL-3.
N-5: aspect-head styling var()-only; allowlist pins untouched.

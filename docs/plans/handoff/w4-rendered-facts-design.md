# W4 - RENDERED FACTS design (slice design doc; DESIGN gate input)

> **BLOCKED AS AN INDEPENDENT COMPLETION PATH (2026-07-14):** raw rendered facts are necessary but
> cannot certify page composition. W4 must serve the binding W3 corrective gate and may not claim
> independent completion, merge, push, or publication while that gate remains `REVISE`. A bounded
> correction-branch dependency commit is permitted only after its own `AGENTS.md` slice/review gates. See the
> [Codex corrective audit](w3-visual-regression-correction.md#codex-corrective-audit--binding-gate-2026-07-14).

Historical pre-hardening observation (non-authorizing), 2026-07-13: `bootstrap_red_ref` returned
`admit: true` for task "implement headless rendered facts", RED
`tests/contracts/test_rendered_facts.py`. Before any new mutation, re-observe under the corrected
closed scope and persist the observation+claim admission envelope required by the W3 correction.

## Observed gap

The static adapter proves emitted HTML/CSS grammar, while MF1 proves screenshots and a narrow mobile
overflow probe. Neither exposes a closed post-hydration fact packet to the conformance runner. Runtime
clones, computed colours, actual control boxes, and per-theme mobile geometry can therefore be seen by
Chrome yet remain unavailable to deterministic profile predicates.

## Candidate law

1. **Facts, never verdicts.** A new `contracts/rendered_fact_policy.json` closes page/theme/viewport
   matrix, selectors, fact fields, readiness, and provenance inputs. Chrome emits raw computed styles,
   boxes, text/role metadata, ancestor backgrounds, and scroll ancestry. It emits no pass/fail flags,
   contrast ratios, target-floor booleans, overflow verdicts, or density ratios.
2. **Closed matrix and reachable states.** Every page in `page_manifest.json` × every active profile ×
   viewports 1280 and 390 has exactly one committed `rendered-facts-<theme>-<viewport>.json.gz` plus
   provenance sidecar under its existing page receipt home. Unknown/missing/duplicate rows red. Each row
   binds exact page, profile, viewport, policy, Chrome, and (for index) hydrated-data hashes. Each packet
   also carries the policy's exact reachable-state set. Ordinary pages have `default`; Studio has each
   base-language radio state plus every enabled component swap in the embedded admissibility space. The
   packet stores one immutable DOM preorder/node-identity table (tag, id, owner, parent, stable data
   identity) and a complete index-aligned mutable-attribute/property (`class`, `hidden`, `checked`,
   `disabled`, relevant ARIA), computed-style, box, scroll, pseudo, and text-range observation vector per
   state. Policy pins the canonical activation recipe: select the base radio, reset its base option, then
   activate the named enabled swap when present, then run two bounded task turns that each force a
   computed-style and layout read. Chrome `--dump-dom` does not advance `requestAnimationFrame`; the
   packet therefore names `forced-style-layout-task-turn` rather than making a false paint-frame claim.
   After the second turn, every document animation is recorded and none may be running or pending.
   Each state records raw post-action witnesses: selected base radio id, the exact sole visible stage,
   expected active option identity, and the exact sole visible variant key. The validator derives expected
   state ids and witnesses from active profiles plus the Python `admissible_space()` authority; wrong-state,
   duplicated-default-vector, missing/duplicate state, or vector length mismatches red. Hidden default-state
   controls therefore cannot escape the promoted laws.
3. **Readiness is binding.** Facts are collected only after the selected theme is observed, index
   hydration is `complete`, fonts are ready, and two bounded forced-style/layout task turns have run
   with no running or pending document animations. Index sentinels,
   prototype counts, and empty-state facts must equal the same pinned public snapshot used by W3.
4. **Subject closure.** The producer enumerates every `body *` node in deterministic preorder,
   including hidden/no-box nodes, and records raw tag/role/tabindex/contenteditable/href/disabled/type,
   style, geometry, scroll, parent, and pseudo-element fields. Subject sets are indices into that full
   table, never producer-decided `visible` rows. The potential-interactive selector covers anchors,
   buttons, all non-hidden form controls, `summary`, `label[for]`, interactive ARIA roles, non-negative
   tabindex, and contenteditable. Density uses every nonblank text-node Range plus replaced media.
   Unknown selectors/fields, missing preorder indices, or a truncated list red.
5. **Predicates own decisions.** `conform(profile, *, rendered_facts=None)` dispatches invariants with
   `fact_source: rendered` to a closed rendered-fact bundle, never the static component cache. The
   four deterministic predicates, aggregated over every applicable reachable state, are: eligible opaque shell text contrast; WCAG 2.5.8 target minimum;
   no uncontained horizontal clipping; and shrink-wrapped content containers with no unexplained
   vertical reservation. Supplying mutated facts must pass the same matrix/schema/provenance validator
   as committed packets and flip the relevant result to fail.
6. **Honest contrast scope.** W4 promotes roster `color-roles`, not every existing component contrast
   candidate. The exact `.ps-title` (large text) and `.ps-intro` (normal text) pairs are required in all
   eight cells per profile. Facts record foreground/ancestor alpha, opacity, background image/gradient,
   pseudo content, blend modes, filters, backdrop filters, font size/weight, and the full paint stack.
   The WCAG 2 relative-luminance algorithm and 1.4.3 thresholds (3:1 large, 4.5:1 normal) apply only to
   a parseable opaque, interference-free stack; ineligible/missing required pairs fail. Translucent
   component backgrounds and Apple's accent button remain candidate until composited-pixel/source law.
7. **Touch scope is complete and correctly cited.** Predicates decide visibility/applicability from raw
   facts. WCAG 2.5.8 Target Size (Minimum), Level AA, supplies the 24×24 CSS px floor and its spacing,
   equivalent-target, user-agent, and inline exceptions. Inline exemption requires recorded surrounding
   prose text and ancestry, not `display:inline` alone; a hidden input cannot erase its `label[for]` target.
   Any stronger Apple 44pt / WCAG 2.5.5 rule remains profile-specific until separately sourced.
8. **Responsive scope is complete.** The predicate reasons over every visible element box at 390 and
   allows horizontal excess only when its recorded nearest scroll ancestor exactly matches the existing
   page/location-bound scroll policy. Root/body scroll widths are also raw facts. No sliced offender list.
9. **Density is an exact owner-ratified whitespace budget, not a self-baseline.** Clause
   `D-W4-DENSITY-1` (operator adoption of W4's deterministic `page-content-density` workstream,
   2026-07-13) closes the measured container selectors and their permitted profile spacing tokens:
   index `.db-section` -> padding `--ps-pad`, showcase `.ps-panel` / `.lang` -> padding `--ps-pad`,
   settings `.ps-panel` / `.base` -> padding `--ps-pad`, and studio `.swap-controls` -> block padding
   `--ps-pad-tight` plus inline padding `--ps-pad`. Their used row/column gap must be zero or an exact
   declared root spacing token (`--ps-gap`, `--ps-gap-tight`, `--gap-grid` where the selector's authored
   rule names it). Applicable direct-child block margins are likewise closed per selector to the exact
   authored token or ratified literal named by the policy; zero is permitted only where the authored
   rule computes zero. Container outer margins are explicitly outside this page-interior law. Counts are
   policy-pinned. Each container must carry nonblank content and its content box may reserve no vertical
   space beyond the union of visible in-flow child margin boxes plus its exact authored row gaps, within
   one device pixel of rounding. Facts carry raw container/direct-child
   boxes, margins, positioning, box-model styles, and resolved root token values only; the predicate
   computes token equality and residual space. A giant-padding or giant-gap mutation fails even when the
   container remains shrink-wrapped. A fixed/min-height is not categorically wrong; it fails only when
   the resulting residual exceeds the ratified allowance. This promotes the page-container law while
   leaving each component's separate geometric ink-fill judgment deferred.
10. **One producer path.** The new producer extends `headless_receipts.py` and reuses its hermetic HTTP
    server/readiness grammar. Artifact publication is staged and artifact-hash-bound. W3's DOM probe
    remains MF1; rendered facts are a separate deterministic evidence product.
11. **Aggregation and evidence are closed.** Each rendered predicate consumes all four pages × both
    viewports for that profile, except the responsive minimum specifically consumes all four 390 cells;
    every applicable cell/subject must pass. `fact_source` is required and closed (`static|rendered`) for
    every emitted deterministic row, backfilling existing rows. Conformance receipts contain a stable
    decision summary (counts/minima/maxima, no page/policy/artifact hashes or capture IDs), and a tested
    facts → receipts → pages → facts → receipts regeneration reaches identical receipt/page bytes on the
    second pass, preventing a showcase provenance cycle.
12. **Complete facts stay repository-bounded.** Each artifact is one canonical gzip member containing
    the unchanged canonical JSON packet: empty filename, no comment/extra/name fields, `mtime=0`, and a
    64 MiB uncompressed ceiling. Provenance records canonical-content and compressed-artifact hashes,
    the pinned writer path, Python version, zlib build/runtime versions, and makes no cross-version
    compressed-byte claim. Schema rejects concatenated members, trailing bytes, oversized output, and
    decompressed bytes that differ from `packet_bytes(parsed)`. A two-run/header fixture proves local
    determinism. The runner releases each decompressed matrix after its predicate rather than retaining
    all raw vectors for the complete conformance pass.

## Gate-driven correction design (2026-07-14)

The first CODE/ADVERSARIAL pass reproduced six false-greens. The following corrections are binding
before W4 may land:

1. Canonical transport validation always decodes the supplied artifact and compares it with the exact
   canonical writer bytes. Sidecar runtime strings are closed to the admitted writer runtime and can
   never disable recompression. The complete Chrome argv, localhost capture URL, query identity,
   viewport, scale, and numeric version grammar are validated.
2. Each state records closed computed/pseudo/style geometry for `html` and `body`. Every predicate
   rejects root/body opacity, filters, masks, clips, computed-hidden state, or generated pseudo paint
   rather than treating the first body descendant as the paint root. A raw `hidden` attribute that CSS
   explicitly overrides remains rendered; computed output, not attribute folklore, decides visibility.
3. Contrast facts carry deterministic dense hit samples over every governed text-range rectangle,
   once normally and once with `pointer-events: none` neutralized. Both top nodes must be the exact
   subject; descendants, foreign overlays, generated pseudo paint, inset shadows, and text strokes fail.
   This is a bounded sampled-occlusion claim, not full pixel equivalence.
4. Touch overlap and spacing consider every other applicable target. Same-action identity is used only
   by the already separate equivalent-target exception, and only when another target meets 24x24.
5. Density requires every policy-counted surface to remain visible. Direct-child occupancy is checked
   against merged recursively clipped painted-text and governed runtime-prototype intervals; tag identity
   and arbitrary wrapper backgrounds are not content. The owner-ratified maximum internal blank run is
   policy-pinned, while the existing one-device-pixel surface residual remains binding.
6. One independently pinned canonical policy digest closes every predicate-affecting matrix value,
   selector, subject cardinality, exception allowlist, scroll lane, density lane, threshold, and source
   reference. A weakened policy cannot become authority merely by recapturing facts.

## Open forks

- **F1 - one giant browser packet vs aspect-specific files.** DECIDED one facts packet per matrix cell;
  all aspect predicates consume the same observed page session and provenance.
- **F2 - all component contrast vs opaque shell pairs.** DECIDED opaque shell pairs now. A computed
  rgba value is not the composited pixel behind glass, and Apple accent text cannot be silently rewritten
  to make a generic threshold green.
- **F3 - 44px project floor vs standards AA.** DECIDED WCAG 2.5.8's sourced 24 CSS px floor and exact
  exceptions. A stronger 44pt/44px claim requires its own platform mapping or owner clause.
- **F4 - ratio vs shrink-wrap.** DECIDED box-model shrink-wrap. A numeric occupancy ratio would be
  self-authorizing without a frozen approved reference or operator-ratified threshold.
- **F5 - automatic facts loading vs required injection.** DECIDED default `conform(profile)` loads the
  committed closed matrix so existing receipt/showcase callers remain deterministic; tests may inject an
  exact replacement bundle for mutation proof.

## RED and mutation plan

The RED first requires the policy/test homes and fails because no fact matrix or rendered dispatch exists.
Persistent mutations delete a cell or reachable state, substitute the default vector or wrong activation
witness under another state id, change page/policy/data hash, truncate an element
or state vector, insert an
unknown selector, lower a target box below 24px, introduce paint-stack interference, add a 390px
overflowing element, add unexplained container slack, or replace one ratified padding/gap token with a
giant literal while preserving shrink-wrap, or replace an applicable direct-child margin with a giant
value while the parent remains shrink-wrapped. Settle mutations alter the mechanism/turn count or leave
an animation running/pending. A legitimate target `min-height` whose content consumes
its box remains green. A receipt/page two-pass regeneration mutation must also prove byte stability. Each
mutation must fail the contract or exactly one predicate. The full suite, fresh Chrome matrix, MF1
artifacts for any CSS change, `git diff --check`, and independent DESIGN/CODE/ADVERSARIAL verdicts
precede commit.

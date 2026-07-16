# W6 — Universal capture engine (design record, 2026-07-15)

> Conductor-authored (Fable). The universal design-compiler's capture engine — the PRODUCT, not a
> post-correction afterthought (ACTIVE.md THE PRODUCT). Folds and supersedes the scratch
> `scratchpad/work/w6-reference-capture-requirements.md`. Awaits Codex `DESIGN-VERDICT`. Authorizes
> no build until gated. Builds on its own branch in parallel with the fixture-correction; INTEGRATES
> into `main` only after the correction merges (advisory: don't contaminate the correction review).
> Effort: first gate round max/ultra; re-rounds xhigh.

## 1. What it is (the completeness promise)

Given ANY browser-accessible website, URL, local snapshot, or design document, the engine captures
it and measures **every visible aspect** — nothing the user wants is out of scope: routes, region
topology, layout, spacing/margins, palette, typography, size/geometry, radius, borders, dividers,
elevation/shadow, material/blur, iconography, motion, component anatomy, and every reachable
interaction state, at every viewport. The closed **31-id aspect vocabulary** (slice-0 §3.1:
`page.*` ×10, `visual.*` ×10, `component.*` ×11 with per-component subaspects) is the completeness
cover; the coverage join (slice-0 §3.2, `route × profile/context × viewport × state × region ×
aspect`) forces one classified row per cell so no aspect is silently skipped. The promise is
quantified over a DECLARED ROUTE ROSTER (r2-3): the completeness report names the routes it
captured, the routes it discovered but did not capture (each a loud row — §10.2 SCOPE law), and
asserts nothing beyond the roster; "every route" is a claim about the roster, never about
undiscovered space. The user selects the
aspects they like; the engine compiles them into provenance-bound invariants their target site
must match exactly — official docs first, captured references where docs are silent, owner forks
for tweaks, nothing invented by AI.

## 2. Authority ladder (unchanged from slice-0 §2/§8)

official code/spec (Mode A/B) → operator-approved measured reference (Mode C) → owner-ratified law
(Mode D). No mode = no authority. Discovery (crawl/capture) is EVIDENCE-ONLY until per-aspect
operator approval; approval recorded BEFORE measurement; a crawl can never promote itself, copy a
whole style, or cite popularity. Accessibility floors non-waivable. Brand claims are always
"satisfies the approved reference / <profile> vN — receipts attached", never "is X".

## 3. Reuses the slice-0-approved schemas (no new schema kinds; §8 is the contract)

`UncoveredAspectReport`, `ReferenceCandidateRecord`, `ReferenceAspectApproval`,
`ExternalReferencePack`, `MeasurementRun`, promoted `references.json` clause rows +
`reference_bindings.json`, consumer-side `ReferenceOverrideRecord` — all defined and design-locked
in slice-0 §8, shaped by R1–R8 (producer≠approver principals; one hashed vocabulary; source≠target
full occurrence key; four rights dimensions; per-aspect lifecycle; content-addressed immutable pack
graph; file-driven promotion; dynamic homes with inverse/phantom checks). W6 WRITES these records;
the slice-9 manual lane and the promotion pipeline CONSUME them unchanged.

## 4. Engine build lanes (each its own design→gate→build→review under the SOP; buildable AFTER the standing fix packet integrates — §15.4 build-order law, r2-2)

- **W6-K — reference-lane contracts + validators.** The §8 schemas as real closed contracts under
  `contracts/reference_*` + `contracts/reference_aspects.json` (the vocabulary), each with a
  fail-closed validator + hostile tests (unknown key, dup key, producer==approver, unapproved
  candidate reaching a predicate, rejected-evidence pack citation). INDEPENDENT — build first;
  everything else references it.
- **W6-P — generic rendered-facts probe.** Measures EVERY §3.1 aspect of any served page — the
  "invariant against every aspect" measurement core. Reuses `scripts/quality/rendered_facts/`
  probe skeleton (identity table + per-state computed/box/pseudo vectors, deterministic gzip) but
  with NO `data-dom-owner`/hydration sentinels; subjects found by heuristics (buttons/landmarks/
  card clusters/type tuples) and pinned by operator-confirmed `rendered-subject-selector-v1`
  selectors; outputs the observable-anatomy record (slice-0 §2 candidate shape). Same probe the
  odinproject reduced lane consumes.
- **W6-C — capture pipeline.** Chrome `--dump-dom`/`--screenshot` per viewport (live artifacts =
  gallery evidence only) → stdlib+requests asset localization (stylesheets/@import/url()/img/srcset/
  fonts; scripts STRIPPED, recorded; per-URL failures → honest `capture_gaps[]`) → post-approval
  freeze (deterministic content-addressed archive) → serve the frozen tree via the existing
  `reference_pack/browser.py` local-server + exact-viewport iframe (same-origin → computed styles
  readable) → W6-P measures. Forced pseudo-states on the frozen copy we own (`:hover/:focus/:active`
  rules → marker classes; JS states via operator `state_recipes`; else declared gap). Fidelity is
  operator-confirmed (live-vs-frozen side-by-side; the `confirm-fidelity` SUBCOMMAND of the §15.2
  reference CLI — the flag form is retired, r2-6).
- **W6-G — static gallery** (jinja2, file:// viewable; non-normative pre-approval observations,
  fidelity pair, outlined subjects, rights + gaps) + **W6-X multi-site crawl/cluster** (own
  sub-design; single-URL first). Later lanes.

## 5. URL security boundary (required; hostile-tested, W6-C)

Public unauthenticated HTTP(S) only; clean Chrome profile, no cookies; deny private/link-local/
loopback targets AND redirects to them; size/time/MIME limits; active-content sanitization;
credential/PII checks on captured bytes; robots.txt verdict + any operator override recorded.

## 6. Rights, custody, look-preservation (operator-directed)

Per-resource `source_rights` (four independent dimensions: publication / raw-byte custody /
redistribution / retention). Third-party default: derived artifacts (our measurements + manifests
+ hash-pinned) committed; bulky frozen bytes + full screenshots in durable PRIVATE content-
addressed custody the owner designates, never gitignored-in-public; fonts never published. A pack
is a NAMED LOOK RESTORE POINT (frozen bytes + screenshots + measurement-exact facts, sha256-pinned,
immutable, tagged): capture-as-restore-point + a restore command re-deriving DATA from a chosen
pack; Mode D overrides preserve the original measured value beside any tweak (`forked_from_measured:
true`); git + locked invariants are the coarse timeline + drift-lock — recovery of the original or
any named past look is hash-verified WHENEVER ITS CUSTODY HOLDS (r2-8): pack validation
REVALIDATES custody — every referenced private-custody byte set must exist AND match its pinned
digest; a miss flips the pack to the declared `custody-lost` lifecycle state (slice-0 §8), every
predicate citing that pack then fails, and restore refuses honestly rather than partially.
Publication is a PROJECTION derived from the four rights dimensions per resource: a
`publication`/`redistribution` deny excludes that resource from EVERY published artifact set; an
incompatible-rights publication request refuses outright; retention expiry (`dated-expiry`
passed) is a validated lifecycle event, not an exception path. REDs: §15.1 row F8.

**BACKUP-BEFORE-TRANSFORM (hard law, ACTIVE.md).** The restore-point machinery is mandatory on the
TARGET, not only captured references. Before any restyle transforms a user's site, the engine
FIRST snapshots the target's current state as a committed `pre-restyle` pack (bytes + screenshots
+ facts, hash-pinned) + a git tag, THEN applies the transform reversibly. Revert = git restore to
the tag / re-derive from the pre-restyle pack / drop the Mode D overrides. The O5/DEMO-B restyle
lane FAILS CLOSED if no committed pre-restyle snapshot exists — overwriting without a restore point
is inadmissible. The transform covers every capturable HTML/CSS/JS aspect (ACTIVE.md completeness),
each an invariant the target must satisfy, all reversible via the pre-restyle restore point.

## 7. Design-document lane (the other half of "any design doc")

Reading a design document → clauses is the Mode B pipeline that already exists
(`contracts/design_sources/` + `scripts/quality/design_sources/`): a doc-cited clause lowers to
profile DATA → rendered fact → predicate → mutation → receipt, with the slice-0 §4
`SourceEvidenceRecord` (frozen proposition bytes + reviewer independence) making it non-circular.
W6's uncovered-aspect report routes each gap official-doc-first; only where docs are silent does
capture (Mode C) fill it. "Any design doc or language" = new `docs/design/<lang>.md` + a
`design_sources/<lang>.json` catalog + a profile — the design-language-tdd skill's repeatable loop
(to be refreshed by the docs-currency slice so an agent can actually run it).

Binding dependencies this lane DECLARES rather than implies (r2-9): the slice-0 §4
`SourceEvidenceRecord` for every doc-cited clause; the vocabulary projection (AB-2) so doc-lowered
clauses land in canonical ids; the profile-lowering pipeline (doc clause → profile DATA); and the
new-language ingestion contract (`docs/design/<lang>.md` + catalog + profile) as a repeatable,
parameterized loop — never a hand-authored one-off presented as arbitrary-document capability.
OFFICIAL-SOURCE-SEARCH DISPOSITION (fail-closed; r2-6/r2-9): before ANY Mode-C aspect approval, a
recorded disposition row `{aspect_id, sources_searched[], verdict: docs-cover | docs-silent,
principal_id, date}` must exist; `docs-cover` BLOCKS Mode-C (official precedence is a validated
law, not a habit); a Mode-C approval with no disposition row REJECTS. REDs: §15.1 row F9.

## 8. Milestones (each a full-SOP slice; W6-K → W6-P → W6-C first)

W6-K contracts+validators · W6-P generic probe · W6-C capture+security+custody · end-to-end DEMO
(capture a real owner-chosen site → gallery → approve TWO aspects → freeze → fidelity → measure →
propose-promotion; parity green from committed facts; mutation-proven) · W6-G gallery · W6-X crawl.
DEMO B (promote → apply to odinproject) rides slice 9's promotion pipeline.

## 9. Codex DESIGN gate (history)

- **r1 — 2026-07-15 — `DESIGN-VERDICT: REVISE`** (max/ultra; notes:
  `scratchpad/work/codex-w6-design-gate-2026-07-15.md`): nine must-fixes on the base §1–§9. The
  §10–§14 extension was drafted in response.
- **r2 — 2026-07-16 — `DESIGN-VERDICT: REVISE`** (xhigh; notes:
  `scratchpad/work/codex-w6-design-gate-r2-2026-07-16.md`): 19 findings — the nine r1 must-fixes
  judged not fully resolved, nine new blocking findings on the extension, one minor.
- **CONVERGENCE INVOKED 2026-07-16** (AGENTS.md review-convergence law; ACTIVE.md orchestration):
  two REVISE rounds on this artifact — every remaining finding is converted to an executable RED
  in this design's test plan (§15.1 maps finding → RED), and the work moves to BUILD under the
  three bound packets of §15.4 plus the standing prerequisite
  `scratchpad/work/packet-w6-fixes-2026-07-16.md`. From here Codex reviews CODE + TEST OUTPUT on
  the patches (CODE + ADVERSARIAL gates), never prose re-descriptions of these mechanisms.

---

# W6-E — completeness / copyright / animation / round-trip extension (landed on main 2026-07-16)

> Provenance: drafted in lane G (worktree a872c72); **Fable re-audited and corrected 2026-07-16**;
> design re-gate pending. Extends §1–§9 under the operator's standing laws (recorded in
> `scratchpad/work/SESSION-HANDOFF-2026-07-16.md §13`): (1) the fail-closed completeness question —
> anything not scanned properly means the capture is NOT complete; a gap reddens, never silently
> skips; (2) no copyright exposure — measured VALUES under OUR names, never source identifiers;
> (3) no "done" on anything visual until receipts exist AND the operator has SEEN them; nothing is
> usable until a ZERO-CONTEXT agent can drive it from the skill alone; (4) JS animation — capture
> what is honestly capturable now, DECLARE the rest. This block binds the AS-BUILT engine
> (`scripts/quality/reference_intake/{schema,probe_generic,capture,security,restore}.py` +
> `contracts/reference_aspects.json`). DESIGN ONLY: schemas/signatures below are illustrative
> contracts; a build lane implements after the Codex DESIGN gate on this extension.

**As-built divergences the build lane MUST close first** (this extension's schemas assume them
closed; building on top of them unclosed is inadmissible):

- **AB-1** — `capture.build_candidate_record` emits a shape that
  `schema.validate_reference_candidate_record` REJECTS: producer lacks `principal_id`/`run_id`;
  `source.url`/`fetched_at` vs the validator's `url_or_path`/`fetched_utc`; rights rows lack
  `resource`, put the asset URL in `publication` instead of the closed enum, and default
  `redistribution`/`retention` to strings outside their closed shapes; `capture.live_evidence` is
  a dict-or-null where the validator requires a list; `status: "candidate_only"` is outside the
  lifecycle enum; extra keys `script_policy` / `authority_status` / `cannot_mark_done`; missing
  `candidate_id`, `record_sha256`, `observable_anatomy`, `uncovered_aspects_claimed`. The candidate
  `schema_version` 2 (§10.4) closes this: the builder emits the validator's closed v2 shape (with
  `script_policy` folded into the closed `capture` block) or the lane is red.
- **AB-2** — two DIFFERENT closed 31-id vocabularies coexist: the contract vocabulary
  (`contracts/reference_aspects.json`: `page.*`×10 / `visual.*`×10 / `component.*`×11) and the
  probe's measurement vocabulary (`probe_generic.ASPECT_VOCABULARY`: palette/type/spacing/geometry/
  radius/border/shadow/material/motion/structure/state families). Both stay closed and UNEXPANDED,
  and neither may grow silently — but coexistence alone leaves the measure→contract seam dead (the
  standing engine finding: probe ids can never feed `validate_measurement_run`). The build lane
  therefore adds the seam as pinned DATA, in TWO tables (r2-1/r2-4; together they supersede the
  earlier single-bridge sketch `reference_probe_bridge.json`):
  (a) `contracts/reference_vocabulary_projection.json` — a TOTAL, validated projection of
  `contracts/reference_aspects.json` ids into the slice-0-approved canonical authority
  `contracts/visible_design_vocabulary.json` (w3c-0 §3.1). The approved vocabulary REMAINS the
  authority; the reference contract is its projection, never a rival. Until the canonical file
  lands on disk, the projection pins the approved 31-id set as data and must equal that file the
  day it exists.
  (b) `contracts/reference_capability_matrix.json` — one row per contract OBLIGATION (31 aspect
  ids PLUS the 53 component subaspects = 84 rows), each naming {fact_sources[] (probe fact
  families; one-to-many, subject-sensitive lowering), applicability rule, state-acquisition
  method, gap_code, predicate_family}. The matrix is the obligation cover the coverage join
  consumes; component rows name CONCRETE obligation ids — a `component.* occurrence` wildcard is
  not a contract id and appears nowhere in it.
  `MeasurementRun.measured_aspects` carries CONTRACT ids only (the standing RED
  `test_measured_aspects_are_contract_ids`, packet-w6-fixes item 5, makes the probe emit them;
  projection + matrix must AGREE with that as-fixed mapping, lifted to data). §10.2's bridge
  column and §12.2's animations channel stay OUTSIDE both id sets. The reference-lane operational
  homes r1 asked for (principals/custody registries, lifecycle CLI, bindings + inverse/phantom
  homes) are enumerated in §15.2.
- **AB-3** — the engine's batch review r1 stands at REVISE; the WHOLE standing fix packet is the
  binding prerequisite (r2-10): `scratchpad/work/packet-w6-fixes-2026-07-16.md` — 17 items,
  20 REDs + 1 existing-test correction, bound BY PATH here and BY sha256 in each §15.4 build
  packet envelope at dispatch. ALL 17 items are load-bearing, including the ones the earlier
  draft omitted (4 redirect/host binding, 8 fail-open peer validators, 9 matrix/evidence
  completeness, 11 restore round-trip, 14 URL/CSS grammar, 15 height/determinism, 17 served-tree
  custody + shared Chrome discovery) and their masking-test/fixture work (13, 16). Those REDs
  belong to the fix lane and are PREREQUISITES for §13's flow; nothing in this extension waives
  or re-litigates them — and §13's local lane uses the post-fix intake surface
  (`ingest_local_tree`, D1), never a `file://` acquire, which item 1 forbids: the earlier
  draft's `acquire(file://…)` demo step contradicted the packet and is retired.

## 10. COMPLETENESS-GAP DETECTOR (per capture; the fail-closed answer to "did we miss anything")

New module `scripts/quality/reference_intake/completeness.py` (detector + validator), new pinned
contracts `contracts/completeness_feature_classes.json` (the closed class list + per-lane
capturable truth table + at-rule triage + measured-property closure + the shorthand→longhand
expansion table) and `contracts/completeness_tag_allowlist.json` (HTML living standard + SVG +
MathML element names).

MODULARITY (ACTIVE.md operator law 2026-07-16; binding on every §10–§14 mechanism): detector,
validators, probe, compiler, and gates take EVERY input explicitly — contract tables as
paths/parsed data, the lane, the capture inputs, the target descriptor — and never resolve a
repo-relative literal internally. The contract/receipt paths named in this document are THIS
repo's DEFAULT BINDINGS, declared as data (§15.3); the same engine runs unchanged against any
target's bindings, and a hardwired path is a design defect.

### 10.1 Detector inputs (all already produced by the as-built ladder)

- **I1** the PRE-strip live DOM string (`LiveEvidence.dom` — inline scripts still legible; the
  only place source JS text is readable, since localize drops every `<script>` and external script
  bytes are never fetched);
- **I2** the localized staging tree (post-strip HTML + `assets/` CSS/fonts/images);
- **I3** `LocalizeResult.gaps[]` (fetch failures incl. `CaptureRefused` MIME/size refusals) +
  `script_policy` (v2: gains `sources[]` — one row per removed script,
  `{kind: "inline" | "external", src?}` — the U4 input);
- **I4** the probe packets for the probed matrix (schema v2 with `animations[]` +
  `subject_truncation[]`, §12);
- **I5** the probed context matrix AS DATA — `{viewports[], states[], media_contexts[]}` with a
  canonical digest (`matrix_sha256`): a validator input equal in rank to I1–I4, re-run by deep
  mode (CD8; r2-14);
- **I6** the lane — a MECHANICAL fact, not a rights claim: `frozen-third-party` ⇔ scripts were
  stripped at localize; `first-party-live` ⇔ the probe serves the source directory directly and
  scripts execute. Ownership/rights live in the rights rows, not in the lane id.

### 10.2 The closed feature-class checklist (v1 = exactly 21 ids, fixed order)

Predicates: `dom(x)` = frozen tree markup, `live(x)` = I1 incl. inline script text, `css(x)` = any
localized stylesheet / `<style>` block, `pkt(x)` = probe packets. `capturable_today` is given per
lane as frozen/first-party and is a CONTRACT CONSTANT (CD7), not a per-run opinion.

| # | class_id | present iff | capturable (frozen/1st-party) | bridge → contract aspect |
|---|----------|-------------|-------------------------------|--------------------------|
| 1 | `canvas-2d` | dom∨live `<canvas>` | no / no (frozen canvas renders blank) | page.data-presentation |
| 2 | `webgl` | #1 ∧ live `getContext("webgl…")` | no / no | page.data-presentation |
| 3 | `video-audio` | dom∨live `<video>`/`<audio>` ∨ I3 MIME-refused row whose RECORDED refused MIME is audio/* or video/* (refusal rows carry the offered MIME; an unrelated refused type never feeds this class — r2-19) | no / no (poster img localizes = partial, still a gap) | page.data-presentation |
| 4 | `iframe-embed` | dom∨live `<iframe>`; `cross_origin` flag when resolved src host ≠ capture base host | no / no (localizer does not descend into frames) | page.grouping |
| 5 | `web-font` | css `@font-face` | yes / yes (font/ MIME fetches; §6 custody: fonts never published) | visual.typography |
| 6 | `svg-smil` | dom `<svg>` descendant `<animate>`/`<animateTransform>`/`<animateMotion>`/`<set>` | no / no (bytes survive and SMIL plays, but nothing MEASURES it: not in FAMILIES, absent from getAnimations()) | visual.motion |
| 7 | `css-motion` | pkt motion.* non-neutral (animation-name≠none ∨ transition-duration≠0s) ∨ css `@keyframes` | yes / yes (motion.* family + §12 animations[]) | visual.motion |
| 8 | `waapi-animation` | live `.animate(` ∨ `new KeyframeEffect` ∨ `new Animation(` ∨ pkt animations[] row kind="Animation" | no / yes (frozen trees have no scripts) | visual.motion |
| 9 | `raf-canvas-loop` | live `requestAnimationFrame` | no / no — the DECLARED GAP of §12 v1 | visual.motion |
| 10 | `fetch-xhr-content` | live `fetch(` ∨ `XMLHttpRequest` | no / no (the at-capture rendered result IS frozen; the dynamic refresh behavior is not reproducible) | page.data-presentation |
| 11 | `websocket` | live `new WebSocket(` | no / no | page.data-presentation |
| 12 | `service-worker` | live `serviceWorker.register` ∨ `navigator.serviceWorker` | no / no | page.navigation |
| 13 | `form-post-flow` | dom `<form>` with effective method get\|post — `method=dialog` emits no row; the row RECORDS the method (r2-19) | no / no (markup+styles measured; the submit flow is not exercisable) | component.input |
| 14 | `auth-walled-route` | dom `input[type=password]` ∨ I3 rows carrying HTTP 401/403 | no / no — plus the SCOPE law below | page.navigation |
| 15 | `shadow-dom` | live `attachShadow(` ∨ dom `<template shadowrootmode` | no / no (--dump-dom does not serialize shadow roots) | component.* occurrence |
| 16 | `custom-element` | any hyphenated tag outside the pinned tag allowlist ∨ live `customElements.define(` | no / no (upgrade needs JS) | component.* occurrence |
| 17 | `scripted-behavior` | `script_policy.removed > 0` ∨ dom `on*=` handler attributes | no / yes | umbrella (see U4) |
| 18 | `media-query-unprobed` | css width/height queries PARTITIONED into their satisfiable REGIONS (the intervals cut by every breakpoint); present iff any region contains NO probed viewport — one gap row PER unsampled region (breakpoints {480, 760} under probes {390, 1280} leave (480, 760] unsampled ⇒ one row; per-breakpoint "straddling" is retired, r2-11) — or any non-width feature (orientation/hover/pointer/resolution/aspect-ratio) outside I5 and not claimed by #19/#21 | no / no (remediation: extend I5; one gap row per unsampled region/branch) | page.responsive-composition |
| 19 | `print-style` | css `@media print` ∨ `<link media="print">` | no / no | page.responsive-composition |
| 20 | `rtl-dir-variant` | dom `dir=` ∨ css `:dir(` ∨ `[dir=` | no / no | page.alignment |
| 21 | `pref-media-variant` | css `@media (prefers-…)` (reduced-motion, color-scheme, contrast, …) | no / no (v1.1 candidate: lower `prefers-*` branches by the same marker-class rewrite the probe uses for pseudos — a gap until BUILT) | visual.motion / visual.palette per feature |

SCOPE law (class 14 and the report as a whole; r2-3): the report carries a structured ROUTE
ROSTER — `routes: {declared[], captured[], discovered_not_captured[]}` — where
`discovered_not_captured` is COMPUTED from the captured evidence itself (same-origin anchor and
redirect targets in I1/I2 that resolve outside `captured`); every such route is an automatic row
(`kind: route-uncaptured`), so "we saw a door and did not open it" is loud. Beyond the roster the
report asserts nothing; `scope` says so verbatim, and gate G1 (§14) reads "zero undeclared gaps
ON THE CAPTURED SET", never "the whole site is known".

@media ROUTING PRECEDENCE (r2-19): a `print` branch feeds #19 ONLY and a `prefers-*` branch feeds
#21 ONLY; #18 takes width/height regions plus the non-width features neither claims — the three
classes PARTITION the at-media surface (no overlap, no double-count). The bridge column above is
INFORMATIVE routing; the AUTHORITATIVE obligation cover is
`contracts/reference_capability_matrix.json` (AB-2, r2-4).

### 10.3 The unknown-feature arms (automatic rows — never a silent skip)

- **U1 unknown element tags** — tag set of I2 (+I1) minus `completeness_tag_allowlist.json` minus
  hyphenated tags already claimed by class 16 ⇒ one row each (`kind: element-tag`).
- **U2 unknown at-rules** — every at-rule name in I2 CSS is triaged by the pinned three-verdict
  table in `completeness_feature_classes.json`: MEASURED (`@keyframes`→#7, `@font-face`→#5,
  `@media`→#18/#19/#21, `@import`/`@charset`/`@namespace`/`@supports`/`@layer` structural-neutral),
  KNOWN-GAP (`@container`, `@property`, `@scope`, `@starting-style`, `@page`, `@counter-style`,
  `@font-feature-values` ⇒ gap rows), and ANY name outside the table ⇒ automatic unknown row
  (`kind: at-rule`; e.g. `@view-transition` is caught the day it appears, not skipped).
- **U3 authored-property closure** — the closure is over LONGHANDS: probe FAMILIES props ∪
  {width,height via boundingClientRect} ∪ the pinned structural-neutral set (small, enumerated in
  the contract; nothing waved through by category). Every property name authored in I2 CSS
  declarations is normalized (case-fold; vendor form `-webkit-x` ≡ the probe's `webkit-x` key)
  and, when it is a shorthand, EXPANDED through the pinned shorthand→longhand table; the authored
  property is covered iff EVERY expanded longhand is in the closure, else one row
  (`kind: css-property`) naming the unmeasured longhand(s). So authored `margin: 0` emits nothing
  (all four longhands measured) while `background: …` emits a row for its unmeasured longhands
  (position/size/repeat today), and `clip-path`, `mask`, `object-fit` each emit a row — the arm
  that literally answers "is there a style channel we didn't measure". Custom-property
  declarations (`--x`) are NOT unknown-property rows (their values land in real properties which
  U3 checks) but ARE recorded into the §11 identifier inventory.
- **U4 script behavior, PER SCRIPT — unconditional, no aggregation, no catch-all (r2-13)** —
  EVERY removed script emits its OWN row (`kind: script-behavior`): external rows keyed by `src`
  (bytes never fetched ⇒ never scanned); inline rows keyed by `inline:<index>:<sha256[:12] of
  text>`. Class 8–12 regex matches over a script's OWN text add classification detail to ITS row;
  a match in one script can NEVER silence any other script (per-script classification, never
  document-global — one inline `fetch(` match hides nothing). Dynamic behaviors with no static
  signature (delayed DOM insertion, `matchMedia` listeners, CSSOM/adopted-stylesheet writes,
  event-driven state, aliased/minified animation calls) are exactly why the row is UNCONDITIONAL
  in the frozen lane: stripped ⇒ unscanned ⇒ one row each, until an executable state recipe
  covers that specific script and records that it does.
- **U5 subject truncation** — every packet `subject_truncation[]` row (§12.2:
  `{kind, found, measured}` with found > measured — the probe's 16-per-kind cap made loud) ⇒ one
  row (`kind: subject-truncation`). An unmeasured subject is an unscanned thing; it reddens.
- **U6 unmeasured-occupant census (r2-12)** — subject coverage is a CENSUS, not a heuristic's
  opinion: every rendered element in the frozen tree must be either (a) inside some measured
  subject's node-or-descendant set, or (b) counted into one row per tag family
  (`kind: unmeasured-occupant`, token = tag, with count + first evidence selector). Discovery
  heuristics may stay heuristic; the census is TOTAL — a known-tag element (or a `div`-built
  custom component) the five heuristics never saw is a loud row, and CD8 recomputes the census,
  so a forged "all covered" rejects.
- **U7 pseudo-class / pseudo-element triage (r2-12)** — every pseudo token authored in I2 CSS is
  triaged by a pinned three-verdict table (same pattern as U2, pinned in
  `completeness_feature_classes.json`): MEASURED (`:hover`, `:focus`, `:active` — probe-forced;
  `::before`/`::after` — pseudo vectors), KNOWN-GAP (`:checked`, `:open`, `:target`,
  `:focus-within`, `:focus-visible`, `:has()`, and ANCESTOR-STATE dependencies — a state selector
  whose stateful subject is an ancestor of the styled node, e.g. `.parent:hover .child` — each ⇒
  a row), and ANY token outside the table ⇒ an automatic unknown row (`kind: pseudo-unmeasured`).
  Nothing pseudo-shaped passes silently.

### 10.4 Binding into ReferenceCandidateRecord (schema.py validates it)

`ReferenceCandidateRecord` `schema_version` 1 → **2**; version 2 is the only accepted version (no
v1 custody exists yet; AB-1 closes in the same change). The v2 delta, exactly: the top-level
closed key set gains `completeness`; the closed `capture` block gains `script_policy` (with
`sources[]`); `capture.live_evidence` is list-typed; `status` comes from the lifecycle enum. Raw
source tokens inside the report are LEGAL — the candidate record is private evidence custody;
§11's boundary is generation/publication. Illustrative closed shape:

```json
"completeness": {
  "schema_version": 1, "detector_version": 1, "checklist_version": 1,
  "lane": "frozen-third-party | first-party-live",
  "inputs": {"live_dom_sha256": "…", "staging_tree_sha256": "…", "packet_sha256s": ["…"],
             "probed_viewports": [1280, 390], "probed_states": ["rest", "hover", "focus", "active"],
             "probed_media_contexts": ["…"], "matrix_sha256": "…"},
  "routes": {"declared": ["…"], "captured": ["…"], "discovered_not_captured": []},
  "scope": "captured roster only; absence beyond it is not asserted",
  "feature_classes": [{"class_id": "canvas-2d", "present": false, "capturable_today": false,
                       "evidence": []} /* … exactly the 21 ids of §10.2, fixed order … */],
  "unknown_features": [{"kind": "element-tag|at-rule|css-property|script-behavior|subject-truncation|route-uncaptured|unmeasured-occupant|pseudo-unmeasured",
                        "token": "…", "evidence_selector_or_url": "…", "reason": "…"}],
  "gap_rows": [{"feature_class": "…", "evidence_selector_or_url": "…", "reason": "…",
                "reason_code": "not-capturable | missed-this-run"}],
  "matrix_gaps": [{"route": "…", "viewport": 0, "state": "…", "reason": "…"}],
  "complete": false
}
```

### 10.5 Validator laws (CD1–CD9; `ReferenceContractError` on first proven violation)

- **CD1** closed keys everywhere; `feature_classes` = exactly the 21 ids, fixed order, once each —
  a MISSING class row is a rejection, so silence about a class is structurally impossible.
- **CD2** `present ∧ ¬capturable_today` ⇒ ≥1 `gap_rows` row naming that `feature_class` — a record
  claiming complete coverage WITH a live gap condition and no gap row is the contradiction the
  operator law names, and it rejects.
- **CD3** inverse: every gap row references a class row with `present`, and its `reason_code`
  obeys the lane truth table — `not-capturable` requires `¬capturable_today`; `missed-this-run`
  requires `capturable_today` and is the honest "capturable in principle, missed by THIS run"
  declaration (r2-15: an authored `@keyframes` with no enumerated animation row, an unreadable
  keyframe set, a state-triggered animation the toggles never provoked — each owes one). Unknown
  `feature_class` ids reject (no decorative gaps).
- **CD4** `complete` is DERIVED: `complete ⇔ gap_rows=[] ∧ unknown_features=[] ∧ capture.gaps=[]
  ∧ matrix_gaps=[] ∧ routes.discovered_not_captured=[]` (r2-14/r2-3 — a candidate can never say
  complete while its pack honestly declares missing matrix cells or an unopened route). The
  validator recomputes and rejects a mismatch in BOTH directions (complete-with-a-gap-row is
  rejected; incomplete-with-zero-gaps is rejected too — no fake humility).
- **CD5** `present=true` ⇒ `evidence` nonempty; every gap/unknown row carries
  `evidence_selector_or_url` + `reason`.
- **CD6** `schema_version`/`detector_version`/`checklist_version` pinned; unknown values reject.
- **CD7** `lane` in the closed set; every row's `capturable_today` must EQUAL the pinned truth
  table for `(class_id, lane)` — "canvas is capturable" is rejected on the record alone.
- **CD8** DEEP MODE (mandatory at freeze): the validator re-runs the §10.2/§10.3 predicates over
  (I1, I2, I3, I4, I5) — I5 INCLUDED (r2-14): `inputs.matrix_sha256` must equal the canonical
  digest of the probed context matrix, and the #18 region / #21 feature verdicts, the census
  (U6), the pseudo triage (U7), and the route discovery (CD10) are all recomputed from the
  inputs — then diffs against the record; any divergence — e.g. a `<canvas>` in the tree with a
  report row `present=false`, or a packet truncation row with no U5 row — rejects. Shallow mode
  (record-only) enforces CD1–CD7 + CD10.
- **CD9** pack propagation, TWO-WAY (r2-14): at freeze, every completeness gap/unknown row must
  appear in `ExternalReferencePack.capture_gaps[]` AND every pack matrix gap must appear in the
  candidate's `matrix_gaps`; `validate_external_reference_pack`, when handed the candidate,
  rejects laundering in EITHER direction.
- **CD10** route roster laws (r2-3): every `captured` route carries evidence (its I1/I2/I4
  inputs); `discovered_not_captured` is recomputed in deep mode from the captured evidence;
  every entry in it has a matching `route-uncaptured` unknown row; a roster that asserts a
  captured route with no evidence, or hides a discovered route, rejects.

### 10.6 Acceptance tests (`tests/contracts/test_reference_completeness.py`; hostile-first)

1. `test_canvas_fixture_no_gap_row_fails_validation` — THE named hostile case: a fixture page with
   `<canvas>` and a report carrying no canvas gap row must FAIL (CD2 when `present=true`; CD7 when
   `capturable_today` lies; CD8 deep mode when `present` is forged false).
2. `test_canvas_capturable_today_true_rejected` (CD7 truth table).
3. `test_forged_present_false_rejected_in_deep_mode` (CD8).
4. `test_missing_class_row_rejected` (20 of 21 rows).
5. `test_phantom_gap_row_rejected` + `test_gap_row_with_unknown_class_id_rejected` (CD3).
6. `test_complete_true_with_gap_row_rejected` + `test_complete_false_with_zero_gaps_rejected` (CD4).
7. `test_unknown_at_rule_emits_row` (`@view-transition` fixture) — U2.
8. `test_unknown_element_tag_emits_row` (`<acme-widget>`) — U1.
9. `test_authored_property_outside_closure_emits_row` (`clip-path` fixture) — U3;
   `test_shorthand_with_measured_longhands_emits_no_row` (`margin: 0`) +
   `test_shorthand_with_unmeasured_longhand_emits_row` (`background: …`) — the expansion law.
10. `test_unstraddled_breakpoint_emits_gap` (`min-width:1600px`, probes {390, 1280} — the
    (1600, ∞) region) + `test_unsampled_region_between_breakpoints_emits_gap` (breakpoints
    {480, 760}, probes {390, 1280} ⇒ exactly one row for (480, 760]; r2-11) — #18 partition.
11. `test_scripts_stripped_marks_scripted_behavior` + `test_every_removed_script_emits_its_own_row`
    (TWO inline scripts, one matching `fetch(` — the match never silences the sibling's row;
    r2-13) + `test_minified_bundle_still_emits_per_script_row` +
    `test_external_script_src_emits_row` (U4: per-script rows, inline and external alike).
12. `test_smil_detected_and_gapped` (#6) · `test_video_mime_refusal_feeds_class_row` (#3 via I3).
13. `test_subject_truncation_emits_row` (17-button fixture vs the 16-per-kind cap) — U5.
14. `test_pack_omitting_candidate_gap_rejected` (CD9) · `test_capture_gaps_nonempty_forces_incomplete`.
15. `test_route_roster_required_and_recomputed` + `test_discovered_uncaptured_route_forces_incomplete`
    (fixture DOM with a same-origin anchor to an uncaptured route ⇒ `route-uncaptured` row;
    CD10/CD4) — r2-3.
16. `test_unmeasured_occupant_census_emits_rows` (a rendered element outside the five heuristics ⇒
    U6 row) + `test_forged_census_cover_rejected_in_deep_mode` — r2-12.
17. `test_untriaged_pseudo_emits_unknown_row` (`:has(` fixture) + `test_known_gap_pseudo_emits_row`
    (`:checked`) + `test_ancestor_state_dependency_emits_row` (`.parent:hover .child`) — U7, r2-12.
18. `test_deep_mode_rerun_includes_context_matrix` (I5 digest mismatch ⇒ reject; CD8) +
    `test_complete_true_with_matrix_gap_rejected` (CD4) +
    `test_pack_matrix_gap_missing_from_candidate_rejected` (CD9 two-way) — r2-14.
19. `test_missed_this_run_gap_row_legal_and_forces_incomplete` (CD3 amendment) — r2-15.
20. `test_unrelated_mime_refusal_does_not_mark_video_audio` + `test_dialog_form_emits_no_flow_row`
    + `test_pref_media_routes_to_dedicated_class` (predicate precision + precedence) — r2-19.
21. `test_candidate_v2_closed_shape_round_trip` (producer emits v2; validator accepts; returns the
    candidate id) + `test_candidate_v1_rejected` (version pinning, AB-1/§10.4).
22. `test_detector_runs_from_parameterized_contract_tables` (MODULARITY witness: detector +
    validator run from copies of the contract tables in a tmp dir, no repo-relative resolution).
23. In `tests/contracts/test_reference_vocabulary_projection.py`:
    `test_projection_total_into_canonical_vocabulary` + `test_projection_agrees_with_probe_emitted_ids`;
    in `tests/contracts/test_reference_capability_matrix.py`:
    `test_matrix_total_over_all_84_obligations` + `test_matrix_rows_bind_real_fact_sources_and_gap_codes`
    (r2-1/r2-4); in `tests/contracts/test_reference_layout_integrity.py`:
    `test_reference_intake_homes_are_tracked` (r2-2 — turns green when the conductor integrates
    and commits the standing fixes packet; the engine tree is untracked today).

## 11. NO-VERBATIM-IDENTIFIER LAW (the copyright boundary)

The APPLY/generation path may carry **measured VALUES only** — colors, dimensions, radii, timing
curves/durations, font metrics, keyframe offsets — reproduced under OUR names. It may NEVER carry
source identifiers verbatim: class names, ids, CSS custom-property names, `@keyframes`/animation
names, data-attribute names, or non-generic font-family names, beyond the standard allowlist.
Scripts are stripped at localize (`capture.py::_Localizer` drops every `<script>`; `script_policy.
strategy = drop-all-script-elements`). The STRUCTURAL guarantee that source function names cannot
reach any output is §11.3's compile boundary — the generator only ever receives the compiled,
redacted invariant set, never the frozen tree — with the strip meaning no JS parser is needed on
the generation side. (Inline `on*=` handler text DOES survive localization as-built; its
neutralization is an AB-3 RED — evidence custody may hold it, generation can never see it.)
Private evidence copies (review-only custody: frozen trees, live DOM, completeness reports) MAY
retain source identifiers — the boundary is generation/publication, not custody.

### 11.1 The guard (`scripts/quality/reference_intake/identifier_guard.py`)

`assert_no_verbatim(evidence_root, generated_root, allowlist) -> list[IdentifierViolation]`:

- **Extract** identifier sets from both sides, each token TYPED with its channel. From HTML:
  class tokens, `id` values, `data-*` attribute NAMES (inline `style` handled as CSS). From CSS:
  selector class/`#id` tokens, custom-property declarations and `var(--x)` references,
  `@keyframes` names + `animation(-name)` values, `font-family` list items minus generic
  families — PLUS the channels r2-16 names: `grid-template-areas`/`grid-area` names, counter
  names (`counter-reset`/`counter-increment`/`counter()`/`counters()`), `container-name`/
  `@container` names, `view-transition-name` values, `url(…)` tokens (path stems), and string
  literals in generated `content`. From our token JSON: token-name key paths, plus string values
  of font-family- and animation-typed fields.
- **Normalize** before comparison: Unicode NFC, quote/whitespace trim, case-fold font names, and
  STRIP SIGILS/PREFIXES (`.`, `#`, `--`, `data-`) — stripping normalizes WITHIN a channel; the
  token keeps its channel type, so an identifier cannot cross namespaces OR categories to hide.
- **Decide**, PER CHANNEL TYPE (r2-16): with channel set T = {class, id, custom-property,
  keyframes-name, font-family, data-attr-name, grid-area, counter-name, container-name,
  view-transition-name, url-token, content-string},
  `V = ⋃_{t∈T} (extract_t(generated) ∩ extract_t(evidence)) − allowlist_t`; an allowlist entry is
  a (type, token) PAIR, so an allowlisted token in one category can never launder another (a
  source CLASS spelled like a CSS keyword, ARIA attribute, or generic font still intersects in
  the class channel and reds). `V ≠ ∅` is a FAILING TEST in the apply path — red, with every
  violation listed as {type, token, source occurrences, generated occurrences}. The guard also
  runs as the publication gate for any artifact leaving private custody.

### 11.2 The allowlist (`contracts/identifier_allowlist.json`, sha256-pinned)

Closed groups, enumerated not categorical, and TYPED — every entry is a (type, token) pair per
§11.1, never a bare token: HTML/SVG/MathML tag names; CSS property names and
keyword values (pinned tables); generic font families (`serif`, `sans-serif`, `monospace`,
`cursive`, `fantasy`, `system-ui`, `ui-serif`, `ui-sans-serif`, `ui-monospace`, `ui-rounded`,
`math`); the well-known system-stack tokens (enumerated: `-apple-system`, `BlinkMacSystemFont`,
`Segoe UI`, `Roboto`, `Helvetica`, `Helvetica Neue`, `Arial`, `Noto Sans`, `SFMono-Regular`,
`Menlo`, `Monaco`, `Consolas`, `Courier New`); ARIA roles + standard attribute names. Two hard
rules: (a) the pinned digest lives in an INDEPENDENT lock home,
`contracts/identifier_allowlist.lock.json` `{path, sha256, version}` (a separate registered
artifact — r2-16); the guard loads BOTH files and REFUSES to run if the allowlist bytes don't
match the lock (no allowlist-stuffing, no self-certification); (b) OUR namespace — the target
descriptor's `namespace` parameter, bound to `jg` for this repo (`jg-*`, `--jg-*`, `data-jg-*`,
`__probe_*`) — is NEVER allowlisted: a source that already uses our prefix still intersects and
forces review.

### 11.3 Identifier redaction at invariant compile

Motion invariants carry timing/keyframe VALUES, but `animation-name` is an identifier: the compiler
REDACTS name fields to opaque ordinals (`anim-1`, `anim-2` in document order) at compile time, so
the generator's input — the compiled invariant set — is identifier-free by construction. The
generator never receives the frozen tree.

The compiled invariant set is itself a CLOSED SCHEMA (r2-16/r2-17):
`validate_compiled_invariant_set` (home: §15.2) enforces value-typed fields only; the compiled
occurrence key replaces `subject_selector` with an opaque deterministic `subject_id`
(document-order ordinal), and identifier-bearing fields (selectors, class lists, source animation
names) are STRUCTURALLY ABSENT from the schema — not merely redacted at write time. The
evidence-side 12-field occurrence key (slice-0 §8, `subject_selector` intact) stays in custody
records unchanged; the private `subject_id ↔ selector` join map is evidence custody — never
published, never readable by the generator.

### 11.4 Acceptance tests (`tests/contracts/test_identifier_guard.py`)

1. `test_source_class_in_generated_css_fails`.
2. `test_source_class_smuggled_via_custom_property_name_fails` — THE required hostile case: source
   has `.acme-hero-cta`; generated CSS declares `--acme-hero-cta: …`; sigil-strip normalization
   makes them intersect ⇒ red.
3. `test_source_class_smuggled_via_data_attribute_fails` (same mechanism, `data-acme-hero-cta`).
4. `test_source_animation_name_reuse_fails` · `test_invariant_compile_redacts_animation_names`.
5. `test_measured_values_under_our_names_pass` (identical hex/px/cubic-bezier values, our tokens ⇒
   green — values are the deliverable).
6. `test_generic_font_family_allowed` · `test_system_stack_tokens_allowed` ·
   `test_proprietary_font_name_fails`.
7. `test_guard_refuses_unpinned_allowlist` · `test_our_namespace_never_allowlisted`.
8. `test_typed_allowlist_blocks_cross_category_laundering` — THE r2-16 hostile case: source has a
   CLASS named `serif`; `serif` is allowlisted as a generic FONT; the generated CSS reuses class
   `serif` ⇒ red (the font-channel allowlist row cannot excuse a class-channel token).
9. `test_grid_counter_container_viewtransition_url_content_channels_extracted` — a source
   identifier smuggled through `grid-template-areas`, a counter name, `container-name`,
   `view-transition-name`, a `url(…)` stem, or generated `content` ⇒ red.
10. `test_allowlist_lock_home_binds_digest` — guard refuses when allowlist bytes mismatch
    `contracts/identifier_allowlist.lock.json`.
11. `test_compiled_invariant_schema_closed_and_identifier_free` +
    `test_subject_join_map_never_reaches_generated_output` (r2-16/r2-17).

## 12. JS-ANIMATION PHASING

### 12.1 v1 (design now, buildable): `document.getAnimations()` enumeration in the probe

Extend `probe_generic._HOST_HTML` `measure()`: enumerate animations at REST once per document,
after subject discovery and BEFORE the first per-subject `stateVectors` toggle — `__probe_no_anim`
(`transition:none/animation:none`) would cancel the very CSSTransition/CSSAnimation objects being
enumerated, and marker-class toggles can themselves START transitions — and RE-ENUMERATE after
each forced-state application, recording the delta rows tagged with the provoking state (r2-15):
an animation that exists only under `:hover` is captured by its post-toggle pass, never lost to
rest-pass timing. Illustrative lowering:

```js
function animationRows(doc) {
  var list = (typeof doc.getAnimations === "function") ? doc.getAnimations() : [];
  return list.map(function (a) {
    var eff = a.effect, tgt = eff && eff.target;
    var t = (eff && eff.getComputedTiming) ? eff.getComputedTiming() : {};
    var frames = null, readable = false;
    try { frames = eff.getKeyframes(); readable = true; } catch (e) {}
    return {
      kind: (a.constructor && a.constructor.name) || "Animation",   // CSSAnimation | CSSTransition | Animation
      name: a.animationName || a.transitionProperty || a.id || "",
      target_dom_path: tgt ? domPath(tgt) : "", target_selector: tgt ? selectorOf(tgt) : "",
      pseudo: (eff && eff.pseudoElement) || "",
      timing: { duration_ms: Number(t.duration) || 0, delay_ms: t.delay || 0,
                end_delay_ms: t.endDelay || 0,
                iterations: t.iterations === Infinity ? "infinite" : t.iterations,
                direction: t.direction || "", fill: t.fill || "", easing: t.easing || "" },
      keyframes_readable: readable,
      keyframes: readable ? frames.map(function (f) { /* {offset|computedOffset, easing, composite,
                 props:{property:value}} */ }) : null
    };
  }).sort(/* by (target_dom_path, kind, name) — deterministic */);
}
```

Determinism law: clock-dependent fields (`startTime`, `currentTime`, `playState`) are EXCLUDED from
the packet by design. Declared caveats, each with its fail-closed cross-check: (a) finished
non-filling animations vanish from `getAnimations()` and the probe's `--virtual-time-budget=5000`
may fast-forward past short ones — the §10.2 #7 static scan (`@keyframes` authored) still marks
the class present, AND the run-level cross-check DERIVES a `missed-this-run` gap row (§10.5 CD3,
r2-15) for every authored `@keyframes` name with no enumerated row and for every
`keyframes_readable:false` row, so "capturable but missed here" is a declared,
completeness-blocking fact, never silence; (b) keyframes are readable for
same-origin stylesheets (the probe serves target + host from one loopback origin) and
`getKeyframes()` is still try/caught — `keyframes_readable:false` is an honest row, per "keyframes
where readable"; (c) on frozen third-party trees scripts are stripped, so only CSS-origin
animations (CSSAnimation/CSSTransition) can appear; WAAPI rows appear only on first-party direct
probes — which is exactly the #8 truth-table split; (d) the `name` field is a SOURCE IDENTIFIER:
retained in the evidence packet (private custody), redacted to ordinals at invariant compile
(§11.3).

### 12.2 Facts schema addition

`ExternalReferenceRenderedFacts` `schema_version` 1 → **2**: exactly TWO new top-level closed keys,
both always present (possibly `[]`) — `"animations": [rows]` (shape above, sorted) and
`"subject_truncation": [{kind, found, measured}]` (one row per subject kind whose found count
exceeded the measured cap; the §10.3-U5 input; this is the CLOSED home of packet-w6-fixes item 7's
truncation honesty — the animation lane normalizes whatever field layout that fix lands).
Enforcement home (schema.py carries no facts-packet validator today): the probe's closed emit +
`tests/contracts/test_reference_probe_animations.py` pins the v2 key set — kept OUT of
`test_reference_probe_generic.py`, whose surface the standing fixes packet owns (no RED-file
collision) — and CD8 deep mode consumes both channels. `aspects_measured` and both 31-id
vocabularies are UNCHANGED — the animations block is a richer facts channel under the existing
`motion.*` family. Rejected alternative: minting a 32nd aspect id, because it breaks the closed-31
symmetry of AB-2 on both sides for zero coverage gain.

### 12.3 The declared v1 gap

Pure rAF/canvas-driven animation exposes no API surface — it is feature class #9
`raf-canvas-loop`: `present ⇒ capturable_today=false ⇒ a named gap row` in every packet's candidate
record, honest in every gallery and pack. Never a silent skip.

### 12.4 v2 (sketch ONLY — a future slice; not buildable from this doc)

Time-series characterization: drive Chrome via CDP `Emulation.setVirtualTimePolicy` (pause →
advance in N fixed steps over T ms; fallback: a `--virtual-time-budget` ladder), taking per step a
screenshot + a computed-style sample of the pinned subjects; output
`{t_i, style_vector_i, screenshot_sha256_i}` rows. This CHARACTERIZES motion the API cannot express
(rAF loops, canvas, scroll-linked) — bounded evidence for receipts and diffing, explicitly labeled
`characterization`, never claimed as capture; #9 stays a gap row until an operator ratifies a
characterization-based predicate family.

## 13. FIDELITY ROUND-TRIP DEMO (DEMO-B first acceptance)

Target: a TARGET DESCRIPTOR is DATA — `{target_root, routes[], viewports[], states[], namespace,
receipts_dir, custody_root}` — and the round-trip pipeline consumes descriptors ONLY (ACTIVE.md
MODULARITY: the same engine runs unchanged on any repo). The DEMO binds one instance,
`contracts/demo_b_target.json`: this repo's `site/` served locally — zero rights risk, ground
truth in hand; the operator pre-authorized their own site as the demo surface; any EXTERNAL
reference remains the operator's to name first (standing law: the operator picks the reference).
Bound values: routes `index.html`, `settings.html`, `studio.html`, `showcase.html`; viewports
1280×800 and 390×844 — MF1's receipt WIDTHS (1280 screenshot / 390 probe); the heights are pinned
in the descriptor for the demo, not a repo-wide canon; namespace `jg` — the §11.2
never-allowlisted namespace IS this parameter. States: rest + forced hover/focus/active via the
probe's marker classes; the probe leaves `:focus-visible`/`:focus-within` untouched and has NO
forcing for `selected`/`disabled` — those are captured only as the rest vectors of subjects
already carrying them; every unreached (route × state) cell is a declared matrix gap, never a
silent skip. The demo yields TWO completeness contexts: the FROZEN capture (lane
`frozen-third-party` mechanically — scripts stripped; owes the per-script U4 rows) and the direct
source observation (lane `first-party-live` — scripts execute, class 17 capturable, no row owed);
the candidate record carries the frozen capture's report. Although the target is owned, the §11
guard runs in ENFORCE mode — the demo proves the mechanism under third-party constraints;
ownership merely removes legal risk.

ORDER LAW (r2-5; slice-0 §8 lifecycle): approval → hash-identical freeze → fidelity confirmation
→ measurement. Everything before approval is typed EVIDENCE-ONLY (`ObservationRun`, never a
`MeasurementRun`); authoritative values come from the APPROVED FROZEN BYTES; an aspect the frozen
tree cannot faithfully reproduce is a fidelity/measurement gap for that aspect — an honest halt
or a recorded de-selection, never a silent substitution of live values.

Flow (each step names its artifact and its red condition):

- **D0 preflight** — `capture.chrome_available()`; halt honestly when Chrome is absent (the probe
  raises `ChromeUnavailable`; the capture helper raises `FileNotFoundError` today — the build lane
  unifies the preflight on one exception; nothing fabricated).
- **D1 source intake** — LOCAL lane: `ingest_local_tree(target_root)` — a DISTINCT,
  operator-authorized entry for local trees (typed first-party; refuses any path/symlink escaping
  `target_root`, r2-7) that never touches `acquire()`; `acquire()` keeps refusing `file://` and
  private hosts outright (packet-w6-fixes item 1 — r2-10's contradiction is resolved by this
  SPLIT, not by a file:// exemption). REMOTE lane (post-fixes): `acquire(https://…)` under the §5
  boundary with EVERY Chrome request routed through the boundary (interception/proxy pinned in
  the launch command line; storage + download containment pinned; r2-7). Live evidence: DOM +
  screenshots at both descriptor widths; `localize(dom, staging, base_url=…)` unchanged; the §5
  SSRF boundary is NOT weakened for remote work.
- **D2 evidence-only observation** — probe the staging tree AND the live source as
  `ObservationRun` records (`authority_status: evidence-only`, slice-0 §8): 4 routes × 2
  viewports = 8 packets each (schema v2 with `animations[]` + `subject_truncation[]`, §12),
  states per the descriptor. These feed the gallery and the operator's aspect selection; they can
  NEVER validate as MeasurementRuns (typed; r2-5). Live-vs-frozen divergence observed here is
  evidence feeding class #17.
- **D3 completeness** — detector over (I1, I2, I3, I4, I5); deep-mode validation (CD8). The
  EXPECTED declared-gap set for the frozen capture, from the 2026-07-16 scan of `site/`:
  `scripted-behavior` PER-SCRIPT rows (6 inline blocks: index 2, settings 1, studio 2,
  showcase 1; zero external srcs — one U4 row EACH); `fetch-xhr-content` (`site/index.html`);
  `pref-media-variant` ×2 (`prefers-reduced-motion` `site/index.html:494`,
  `prefers-reduced-transparency` `site/index.html:495`); `form-post-flow` absent (no `<form>`
  exists today); `media-query-unprobed` PRESENT for widths — r2-11 corrects the earlier
  "expected EMPTY" claim: the region partition of breakpoints {480, 760} under probes {390, 1280}
  leaves (480, 760] unsampled ⇒ exactly one declared region gap row (extending I5 with a width
  inside the region, e.g. 600, is the optional remediation; v1 DECLARES rather than extends);
  census (U6), pseudo-triage (U7), and U3 rows as computed by the run. The run recomputes the
  full set; ANY undeclared gap — or any divergence from the run's own recomputation — is RED, halt.
- **D4 approval** — operator approves the selected aspect rows (`ReferenceAspectApproval`;
  producer principal = engine, approver = operator, R1; `candidate_sha256` binds the record
  BYTES — recomputed, never label-compared — BEFORE any authority, R5/r2-6).
- **D5 freeze** — `freeze(staging, pack_dir)` promotes the APPROVED bytes hash-identically →
  `source_tree_sha256`; the pack is the custody / restore-point artifact; CD9 two-way gap
  propagation validates here.
- **D6 fidelity confirmation** — the operator's recorded act on the FROZEN artifact vs live
  evidence (side-by-side; the `confirm-fidelity` subcommand). Transition `frozen →
  fidelity-confirmed` per the PINNED lifecycle graph (`contracts/reference_lifecycle_graph.json`
  — the slice-0 §8 edge set as data; a backwards edge such as `measured → fidelity-confirmed`
  REJECTS, r2-6). FAIL-CLOSED principals law, unlike the as-built optional-peer pattern: a
  transitions row with `to: "fidelity-confirmed"` REQUIRES the principals map at validation;
  validating such a record WITHOUT the principals map, or with a non-operator principal,
  rejects — green tests alone can NEVER set it.
- **D7 authoritative measurement** — `MeasurementRun`s exist only from here (`measure` requires
  `fidelity-confirmed`; r2-5/r2-6): same probe, over the SERVED FROZEN BYTES (`serve_frozen`; the
  packet pins the served-tree sha derived from the pack's `source_tree_sha256` — packet-w6-fixes
  item 17 — so approval, pack, and facts share byte identity, r2-17). Any selected aspect the
  frozen tree cannot faithfully render (stripped script behavior) is a fidelity gap: recorded,
  and the aspect is either de-selected by the operator or the demo halts honestly.
- **D8 compile invariants** — per approved aspect × route × viewport × state × subject: rows
  {occurrence-key PROJECTION, fact field, expected value} drawn from the D7 packets ONLY. The
  compiled set is the §11.3 CLOSED schema: the evidence-side 12-field occurrence key
  (`subject_selector` intact) stays in custody; the compiled key replaces `subject_selector` with
  the opaque deterministic `subject_id`; identifier-bearing fields are structurally absent; §11.3
  redaction applied; the set BINDS the pack tree sha it was measured from (r2-17).
- **D9 regenerate** — the generator (`regenerate.py`) consumes ONLY the compiled invariant set +
  the descriptor's namespace and stamps every regenerated subject
  `data-<namespace>-subject="<subject_id>"` (our name — legal; the deterministic re-measure join
  key, r2-17). Output goes to a FRESH directory — `target_root` is untouched, so
  BACKUP-BEFORE-TRANSFORM is not triggered; the in-place variant, if ever chosen, MUST run behind
  `guarded_transform(snapshot_target(target), …)` (§6 law; `SnapshotRequired` otherwise). The §11
  guard runs here in ENFORCE mode: any violation = RED, halt.
- **D10 re-measure + per-aspect diff** — same probe, same routes × viewports × states over the
  regenerated tree; subjects joined by `data-<namespace>-subject` = `subject_id`. For every
  compiled invariant row: expected (frozen reference) vs measured (regenerated). Comparison is
  over VALUE fields only; identifier-bearing fields (selectors, class lists, animation names) are
  excluded BY LAW — they must differ under §11. Target: ZERO divergence on selected aspects; ANY
  diff = a RED row showing {aspect, occurrence key, expected, got}. Serialized to
  `<receipts_dir>/demo-b/diff-table.json` + a human table in the gallery page.
- **D11 receipts (MF1-COMPLETE; r2-18)** — reference vs regenerated screenshots, labeled pairs,
  at BOTH descriptor widths for every route → `<receipts_dir>/demo-b/side-by-side-<route>-<vw>.png`,
  PLUS the 390 DOM-overflow probes for every route, PLUS honest `.provenance.json` sidecars
  naming producer, command, Chrome version, viewport (AGENTS.md MF1; producer
  `scripts/quality/headless_receipts.py`, parameterized by the descriptor's routes) — each
  sha256-pinned, plus a `file://`-viewable gallery page (W6-G style).
- **D12 operator confirmation** — DONE only on the operator's visual confirmation of D11,
  recorded in the `g3` row of the GATES RECEIPT (§14): operator principal + per-receipt
  {path, sha256} evidence. This is a GATE record, not an aspect-lifecycle edge — the earlier
  `measured → fidelity-confirmed` transition is retired as backwards (r2-6); aspect rows reached
  `fidelity-confirmed` at D6, per the pinned graph.

Acceptance tests (`tests/contracts/test_demo_b_roundtrip.py`, plus
`test_reference_lifecycle_graph.py` for the order laws and
`test_reference_acquire_containment.py` for the D1 boundary; Chrome-gated where live):
`test_demo_b_zero_divergence_on_selected_aspects` (end-to-end);
`test_diff_red_on_single_value_mutation` (perturb one radius in the regenerated tree ⇒ exactly
that row RED, shown — and identifier fields provably excluded from comparison);
`test_subject_join_via_namespaced_subject_attribute`;
`test_compiled_key_uses_opaque_subject_id` + `test_compiled_set_binds_frozen_tree_sha` (r2-17);
`test_measurement_rejected_before_fidelity_confirmed` +
`test_observation_run_never_validates_as_measurement` (r2-5);
`test_lifecycle_graph_pinned_and_backward_edge_rejected` (r2-6);
`test_identifier_guard_enforced_in_demo` (inject a source class into the generator output ⇒ red);
`test_fidelity_confirmed_requires_operator_principal` +
`test_fidelity_confirmed_without_principals_map_rejected` (schema-level, no browser);
`test_demo_ingests_local_target_without_acquire` +
`test_local_snapshot_ingest_refuses_symlink_escape` (r2-7/r2-10);
`test_regeneration_never_writes_into_target` (fresh-dir law);
`test_roundtrip_runs_on_parameterized_target_descriptor` (MODULARITY witness: the same pipeline
over a fixture descriptor pointing at a tmp tree, never `site/`).

## 14. COMPLETION-GATES (the engine is "in progress" until ALL THREE hold)

- **G1 — zero undeclared gaps on the demo target.** Deep-mode completeness (CD8) green on every
  DEMO-B capture AND the operator countersigns the declared gap list. A gap row is a DECLARATION;
  an undeclared gap is any feature the deep validator or the operator's review finds missing from
  the report ⇒ red. Scope per §10.2: the captured ROUTE ROSTER (r2-3); the deep re-run includes
  I5 (r2-14).
- **G2 — a ZERO-CONTEXT agent can drive it from the skill alone.** Protocol: a FRESH agent whose
  only repo context is `skills/design-language-tdd/` (SKILL.md + references/) is handed "capture
  <fixture>, measure at 1280 and 390, produce the completeness report + receipts"; pass ⇔ the
  artifacts exist, validators are green, and the transcript consulted no other doc. The run's
  transcript is persisted and its path + sha256 recorded in the `g2` row of `gates.json`; the
  protocol file, committed under the skill's `references/`, pins the allowed-context list so the
  check is repeatable. Declared dependency RESOLVED IN-LANE (r2-17/r2-18): the round-trip packet
  AUTHORS `skills/design-language-tdd/references/reference-capture-runbook.md` AND the pinned
  protocol file `skills/design-language-tdd/references/zero-context-protocol.md`; the fresh-agent
  RUN (transcript persisted, hash-pinned) remains the gate — G2 cannot pass before the run.
- **G3 — operator visual confirmation.** The gates receipt's `g3` row (D12) exists with the
  operator principal and per-receipt evidence hashes, AND the D6 `fidelity-confirmed` transition
  rows exist for every selected aspect (fail-closed per D6). G1 and G3 are DERIVED by the gates
  validator from the completeness records and the transition rows — never read off labels
  (r2-18). Receipts SEEN, not merely generated.

**Claims ban (binding).** Until G1 ∧ G2 ∧ G3 hold — witnessed by `<receipts_dir>/gates.json`
(this repo's binding: `assets/receipts/reference_intake/gates.json`), a CLOSED schema validated
by `gates.py::validate_gates_receipt` `{schema_version, g1|g2|g3: {value, principal_id, date,
evidence: {path, sha256}}}`, whose validator RECOMPUTES every evidence hash from disk, requires
the operator principal on g3, and DERIVES g1/g3 from the validated completeness records and
transition rows (labels alone can never set a gate; r2-18) — status docs (`docs/plans/ACTIVE.md`,
`docs/plans/handoff/*.md`) may not claim W6 "works" / "done" / "complete". Enforcement:
`tests/contracts/test_w6_claims_ban.py` — the forbidden patterns are pinned DATA in the test
(works / done / complete / shipped / landed / READY / OPERATIONAL / DEMONSTRABLE,
case-insensitive; r2-18 extends the set), and the scan binds to the STRUCTURED STATUS surfaces:
ACTIVE.md's W6 status row and this doc's `status:` line carry a machine-readable token (the only
completion-claiming value is checked against a VALID gates receipt), so negated/historical prose
elsewhere stops false-positiving; a completion-claiming token or pattern hit on those surfaces
while `gates.json` is absent or invalid (or any gate false) reddens. A lint by nature — the
receipt file is the law — and this design record keeps its DocAuthorityPolicy row
`class = "design-record"`; it never becomes a completion claim by drift.

### New-surface rollup for the build lane (all fail-closed, hostile-tested per §10.6/§11.4/§13; r2-17/r2-18 close the earlier omissions)

Engine: `scripts/quality/reference_intake/{completeness.py, identifier_guard.py,
invariant_compiler.py, regenerate.py, gates.py, gallery.py, rights.py, cli.py}` ·
`capture.py::ingest_local_tree` + acquisition containment (D1) · `probe_generic.py` packet v2
(`animations[]` + `subject_truncation[]`, post-toggle re-enumeration) · `schema.py` candidate v2
(+ AB-1 closure, ObservationRun typing, lifecycle-graph / disposition / custody laws).
Contracts: `contracts/completeness_feature_classes.json` (class list + truth table + at-rule AND
pseudo triage + property closure + shorthand expansion) ·
`contracts/completeness_tag_allowlist.json` · `contracts/identifier_allowlist.json` +
`contracts/identifier_allowlist.lock.json` · `contracts/reference_vocabulary_projection.json` ·
`contracts/reference_capability_matrix.json` (these two supersede `reference_probe_bridge.json`) ·
`contracts/reference_lifecycle_graph.json` · `contracts/demo_b_target.json`.
Skill (G2): `skills/design-language-tdd/references/reference-capture-runbook.md` +
`skills/design-language-tdd/references/zero-context-protocol.md`.
Tests: `tests/contracts/{test_reference_completeness, test_reference_vocabulary_projection,
test_reference_capability_matrix, test_reference_layout_integrity, test_identifier_guard,
test_reference_probe_animations, test_reference_lifecycle_graph, test_reference_rights_custody,
test_reference_acquire_containment, test_reference_gates, test_reference_cli,
test_demo_b_roundtrip, test_w6_claims_ban}.py`.
Receipts: `assets/receipts/reference_intake/` (incl. `demo-b/` + `gates.json`) — this repo's
`receipts_dir` binding. Every new home declared in `contracts/repo_layout.json` in the same slice
that creates it (AGENTS.md homing law; registry rows are conductor/org-lane work at integration).

## 15. CONVERGENCE REGISTER (r2 findings → executable REDs; build proceeds under these)

Two REVISE rounds have run on this artifact; per the AGENTS.md review-convergence law every r2
finding below is folded into the sections cited and, where probeable, converted to an exact RED.
Convention: a RED against a not-yet-built module fails today at import — the mechanism does not
exist, which is the right reason for an unbuilt surface; a RED against an existing module fails
on the missing behavior, verified at packet time. No finding is answered with prose alone.

### 15.1 Finding → RED map

| r2 | folded where | executable RED(s) — file :: test | fails today because |
|----|--------------|----------------------------------|---------------------|
| 1 vocabulary authority + §8 homes | AB-2, §15.2 | `test_reference_vocabulary_projection.py :: test_projection_total_into_canonical_vocabulary` · `:: test_projection_agrees_with_probe_emitted_ids` · `test_reference_cli.py :: test_lifecycle_subcommands_exposed` | projection contract + CLI module absent |
| 2 ownership/dependency | §4, AB-3, §15.4 | `test_reference_layout_integrity.py :: test_reference_intake_homes_are_tracked` | engine tree + `reference_aspects.json` untracked at HEAD; greens when the conductor integrates + commits the fixes packet |
| 3 route universe | §1, §10.2 SCOPE, CD10 | `test_reference_completeness.py :: test_route_roster_required_and_recomputed` · `:: test_discovered_uncaptured_route_forces_incomplete` | `completeness.py` absent |
| 4 84-obligation matrix | AB-2(b) | `test_reference_capability_matrix.py :: test_matrix_total_over_all_84_obligations` · `:: test_matrix_rows_bind_real_fact_sources_and_gap_codes` | matrix contract absent |
| 5 evidence-only vs measurement order | §13 ORDER LAW, D2, D7 | `test_reference_lifecycle_graph.py :: test_measurement_rejected_before_fidelity_confirmed` · `:: test_observation_run_never_validates_as_measurement` | `validate_measurement_run` has no lifecycle-order law; no ObservationRun type exists |
| 6 lifecycle graph + CLI laws | D6, §7, §15.2 | `test_reference_lifecycle_graph.py :: test_lifecycle_graph_pinned_and_backward_edge_rejected` · `:: test_lifecycle_isolation_per_aspect` · `:: test_approval_binds_candidate_bytes_recomputed` · `:: test_accessibility_floor_never_reference_waived` · `:: test_docs_cover_disposition_blocks_mode_c` | no pinned graph file; the as-built validator checks enum labels only |
| 7 hostile-capture boundary | D1, §5 | `test_reference_acquire_containment.py :: test_acquire_requests_route_through_boundary_interception` · `:: test_acquire_pins_storage_and_download_containment` · `:: test_local_snapshot_ingest_refuses_symlink_escape` | no interception/containment flags in the launch line; no local-ingest entry exists |
| 8 rights/custody/restoration | §6 | `test_reference_rights_custody.py :: test_publication_projection_excludes_unpublishable` · `:: test_custody_revalidation_detects_missing_or_drifted_bytes` · `:: test_incompatible_rights_refuse_publication` | no projector/revalidator exists |
| 9 design-document lane | §7 | `test_reference_lifecycle_graph.py :: test_mode_c_requires_official_search_disposition` | approval validator has no disposition requirement |
| 10 prerequisite binding + file:// contradiction | AB-3, D1 | `test_demo_b_roundtrip.py :: test_demo_ingests_local_target_without_acquire` (+ fixes item 1's own RED, unduplicated) | no demo driver/ingest split exists; the old design step used `acquire(file://…)` |
| 11 breakpoint regions | §10.2 #18, D3 | `test_reference_completeness.py :: test_unsampled_region_between_breakpoints_emits_gap` | detector absent; prior text asserted the false "expected EMPTY" (corrected in D3) |
| 12 census + pseudo triage | U6, U7 | `test_reference_completeness.py :: test_unmeasured_occupant_census_emits_rows` · `:: test_forged_census_cover_rejected_in_deep_mode` · `:: test_untriaged_pseudo_emits_unknown_row` · `:: test_known_gap_pseudo_emits_row` · `:: test_ancestor_state_dependency_emits_row` | detector absent |
| 13 per-script classification | U4 | `test_reference_completeness.py :: test_every_removed_script_emits_its_own_row` · `:: test_minified_bundle_still_emits_per_script_row` | detector absent; prior design aggregated inline scripts into a catch-all |
| 14 CD8/CD4/CD9 inputs | §10.5 | `test_reference_completeness.py :: test_deep_mode_rerun_includes_context_matrix` · `:: test_complete_true_with_matrix_gap_rejected` · `:: test_pack_matrix_gap_missing_from_candidate_rejected` | detector absent; CD laws previously omitted I5/matrix/two-way |
| 15 animation misses | §12.1, CD3 | `test_reference_probe_animations.py :: test_authored_keyframes_without_enumeration_emit_missed_row` · `:: test_unreadable_keyframes_emit_missed_row` · `:: test_state_triggered_animation_enumerated_after_toggle` · `test_reference_completeness.py :: test_missed_this_run_gap_row_legal_and_forces_incomplete` | the probe emits no animations channel today (v1 packet) |
| 16 typed identifier boundary | §11 | `test_identifier_guard.py :: test_typed_allowlist_blocks_cross_category_laundering` · `:: test_grid_counter_container_viewtransition_url_content_channels_extracted` · `:: test_allowlist_lock_home_binds_digest` · `:: test_compiled_invariant_schema_closed_and_identifier_free` | guard module absent |
| 17 round-trip join + homes | D8, D9, §11.3, §15.2 | `test_demo_b_roundtrip.py :: test_compiled_key_uses_opaque_subject_id` · `:: test_compiled_set_binds_frozen_tree_sha` · `:: test_subject_join_via_namespaced_subject_attribute` · `test_identifier_guard.py :: test_subject_join_map_never_reaches_generated_output` | compiler/generator absent |
| 18 receipts + gates fail-open | D11, D12, §14 | `test_reference_gates.py :: test_gates_receipt_schema_closed_and_evidence_hashes_recomputed` · `:: test_g1_g3_derived_from_records_not_labels` · `:: test_d11_receipts_include_390_probe_and_provenance` · `test_w6_claims_ban.py :: test_extended_claim_patterns_red_without_gates_receipt` · `:: test_structured_status_rows_checked_against_gates` | gates validator + claims tests absent |
| 19 predicate precision (minor) | §10.2 #3/#13 + precedence | `test_reference_completeness.py :: test_unrelated_mime_refusal_does_not_mark_video_audio` · `:: test_dialog_form_emits_no_flow_row` · `:: test_pref_media_routes_to_dedicated_class` | detector absent |

### 15.2 Reference-lane operational homes (the r1/r2-1 enumeration)

- Vocabulary AUTHORITY: `contracts/visible_design_vocabulary.json` (slice-0 §3.1; design-approved,
  lands with slice 0). As-built source: `contracts/reference_aspects.json`, bound by
  `contracts/reference_vocabulary_projection.json` (total, validated — AB-2a).
- Obligation cover: `contracts/reference_capability_matrix.json` (84 rows — AB-2b).
- Principals: the slice-0 §4.2 principals registry · custody: `contracts/custody_stores.json`
  rows (slice-0 §8 rights shape) — both consumed as parameters, never re-declared here.
- Lifecycle graph: `contracts/reference_lifecycle_graph.json` (slice-0 §8 edge set as pinned data).
- CLI: `scripts/quality/reference_intake/cli.py` — subcommands `capture`, `observe`, `approve`,
  `freeze`, `confirm-fidelity`, `measure`, `compile`, `regenerate`, `gates` (r2-6).
- Bindings + inverse/phantom checks: `reference_bindings.json` + the promotion validator
  (slice-0 §8, unchanged).
- Compiler `invariant_compiler.py` (emits the §11.3 closed compiled-invariant sets) · generator
  `regenerate.py` · gates `gates.py` · gallery `gallery.py` · rights projection/custody
  revalidation `rights.py` · guard `identifier_guard.py` · local ingest
  `capture.py::ingest_local_tree` · allowlist lock `contracts/identifier_allowlist.lock.json` ·
  demo target descriptor `contracts/demo_b_target.json`.

### 15.3 Modularity bindings (ACTIVE.md operator law 2026-07-16)

Every engine entry point takes explicit parameters — {contract tables, lane, target descriptor,
namespace, custody_root, receipts_dir} — and engine code carries NO repo literal. This repo's
canonical paths are DEFAULT BINDINGS declared as data (`contracts/demo_b_target.json` for the
demo; `contracts/repo_layout.json` homes for this repo). RED witnesses:
`test_detector_runs_from_parameterized_contract_tables` (§10.6-22) and
`test_roundtrip_runs_on_parameterized_target_descriptor` (§13). Hardwiring is a design defect the
CODE gate rejects.

### 15.4 Build order + packets (prerequisite law; r2-2/r2-10)

1. PREREQUISITE — `scratchpad/work/packet-w6-fixes-2026-07-16.md` (17 items, 20 REDs; building
   now in `.claude/worktrees/w6-fix-build`): the CONDUCTOR verifies, integrates, and COMMITS it
   first — the engine tree and vocabulary become tracked, closing r2-2 by integration, not prose.
2. `scratchpad/work/packet-w6-detector-2026-07-16.md` (§10 + the AB-2 contract-data seam) and
3. `scratchpad/work/packet-w6-animation-2026-07-16.md` (§12 packet v2) build next —
   parallel-safe (disjoint paths, disjoint test files).
4. `scratchpad/work/packet-w6-roundtrip-2026-07-16.md` (§13 + §14 + §11 guard + lifecycle /
   rights / gates) builds last; it consumes both.

Each packet: builder = Opus under the bound envelope (base sha, design hash, admission hash, RED
hash, closed allowed paths, output patch hash); base = the conductor-integrated tree after the
prerequisite lands; the conductor integrates and commits every result; Codex reviews CODE +
ADVERSARIAL on the exact final patch. No RED name or test file collides with the fixes packet's
20 (verified at authoring; overlaps are declared per packet).

---

Gate history: r1 2026-07-15 `DESIGN-VERDICT: REVISE` · r2 2026-07-16 `DESIGN-VERDICT: REVISE` ·
convergence invoked 2026-07-16 — findings converted to the §15.1 RED register; build proceeds
under the §15.4 packets; the next Codex passes are CODE + ADVERSARIAL on patches (no third prose
round). status: in-progress (§14 gates unmet)

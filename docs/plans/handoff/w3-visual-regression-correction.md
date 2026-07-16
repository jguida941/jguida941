# W3 visual-regression correction

## NEW-CONVERSATION HANDOFF — READ THIS FIRST (2026-07-14)

### Operator outcome

Finish the governed design-language system correctly. Do not roll back the governance work and do
not cosmetically patch the current screenshots. The system itself must construct genuinely
source-backed Apple Dark, Carbon, and Liquid Glass pages, and semantic TDD must make the exact
generic/token-reskin failure described below impossible to admit or call complete.

The operator explicitly rejected the current visible result. The pre-W3 dashboard is the approved
comparison for the narrow aspects frozen in its reference pack, but the goal is not to restore an
ungoverned old implementation. Preserve legitimate infrastructure, replace unsupported composition,
and close the missing gates.

### Canonical plan and authority

This file is the canonical correction plan and audit:

`docs/plans/handoff/w3-visual-regression-correction.md`

Read the whole file. In particular:

- `Codex corrective audit — binding gate` records the failure and twelve must-fixes.
- `Corrective implementation admission` records an ephemeral observed RED and its output hash. It
  is **not** a persisted admission envelope and does not authorize new mutation after its 24-hour
  freshness window.
- `Candidate implementation architecture — DESIGN gate input` records the intended direction for
  all three languages and all four routes, but the final audit below found unresolved design forks.
- `Current DESIGN-gate must-fixes` is the exact blocker list the next scratch design must close.
- The current design, code, and adversarial gates are all blocking. These are the only current
  machine-verdict lines in this file:

DESIGN-VERDICT: REVISE

VERDICT: revise

ADVERSARIAL-VERDICT: REVISE

`docs/plans/ACTIVE.md` links this correction as the active visible-design blocker. The historical
W3 approval in `docs/plans/handoff/w3-index-migration-design.md` is explicitly superseded/void.
W4 design/shape work is downstream and may not overrule this blocker.

### Actor roles and document precedence

The next conversation does not inherit a free-standing Codex builder exception. Follow the current
[`AGENTS.md`](../../../AGENTS.md) actor separation: the implementation owner writes each scratch
slice design, implementation, gates, and branch commit; Codex independently issues DESIGN, CODE, and
ADVERSARIAL verdicts. As `AGENTS.md` is currently worded, the actor named Fable is the implementation
owner.
“Model-neutral” in this handoff means no model-specific dispatch command or Opus-only dependency; it
does not erase the repository's ratified role separation. A different actor may implement only after
the operator explicitly changes that protocol.

When files disagree, use this order:

1. the operator-ratified role/SOP and visible-surface law in `AGENTS.md`, except that its abbreviated
   two-argument bootstrap example is stale and must be corrected RED-first before implementation;
2. the newest dated **current-gate** and design-closure requirements in this handoff;
3. scoped official-source clauses, approved-reference manifests, accessibility baselines, and
   owner-ratified laws, each only for the aspect it actually owns;
4. current contracts/tests/code as evidence of what is on disk, never as proof that the rejected
   design is the desired target;
5. `ACTIVE.md`, `DESIGN-SYSTEM.md`, `pageshell.md`, and the skill only where they do not conflict with
   an explicit supersession here.

The old status/architecture in those last documents is not silently co-authoritative. In particular,
the frozen/separate dashboard, “new theme = data + zero code,” universal centered `.ps-main`, universal
breadcrumb, one shared visible nav anatomy, shared Apple-derived rhythm, deferred `page-archetype`,
and “headless proof is deferred” claims are superseded for this correction. Their stable ownership,
PROFILE -> RENDER -> FACTS/PREDICATE -> RECEIPT seams remain useful. The first design slice must name
the exact obsolete clauses/tests it will retire or narrow before any renderer change.

### Required reading and source-to-gate manifest

The implementation owner must read the linked sources below before editing the surface they govern.
These links are the input set; “Apple-like,” “Carbon-ish,” screenshots from memory, and this handoff’s
prose are not source authority.

#### Repository process and architecture

| Purpose | Required source | Machine consequence |
|---|---|---|
| Roles, RED-first SOP, visible-surface law, Chrome receipts | [AGENTS.md](../../../AGENTS.md) | No mutation without executable RED; no visible-layout completion without 1280/390 Chrome evidence and review verdicts. |
| Current blocker and slice ordering | [ACTIVE.md](../ACTIVE.md) | This correction blocks downstream W4/W5 completion and may not be bypassed. |
| Stable design-system data-flow seam only | [DESIGN-SYSTEM.md](../DESIGN-SYSTEM.md) | PROFILE -> RENDER -> FACTS/PREDICATE -> RECEIPT remains admissible; conflicting frozen-dashboard, zero-code-theme, and status text is superseded above. |
| Corrective architecture and audit | [this W3 correction](w3-visual-regression-correction.md) | The blocker, current must-fixes, and bounded sequence are binding; the three target families and route compositions remain slice-0 candidates. |
| Existing pageshell doctrine to narrow | [pageshell.md](../../design/pageshell.md) | DOM ownership/mechanics survive; centered-column, breadcrumb, shared-rhythm/nav, and deferred-archetype clauses conflict and must be replaced before reuse. |
| Page intent and required route aliases | [page_manifest.json](../../../contracts/page_manifest.json) | The route set is closed; committed bytes and renderer output must agree. |
| Closed DOM ownership | [dom_cover.json](../../../contracts/dom_cover.json) | A visible element without a governed emitter/declared owner fails. |
| Repository/test homes | [repo_layout.json](../../../contracts/repo_layout.json) | Every new source, contract, test, site, skill, and receipt home lands in the same slice. |

#### Language doctrine, DATA, and source catalogs

| Language | Doctrine to read completely | Profile DATA | Scoped source catalog | Additional pinned authority |
|---|---|---|---|---|
| Apple Dark | [apple-dark.md](../../design/apple-dark.md) | [apple-dark.json](../../../contracts/design_profiles/apple-dark.json) | [apple-dark source clauses](../../../contracts/design_sources/apple-dark.json) | Apple official links below plus the approved dashboard reference only for aspects named in its manifest. |
| Carbon | [carbon.md](../../design/carbon.md) | [carbon.json](../../../contracts/design_profiles/carbon.json) | [Carbon source clauses](../../../contracts/design_sources/carbon.json) | [pinned source identity](../../../contracts/official_sources/carbon/source.json), [official token snapshot](../../../contracts/official_sources/carbon/token_snapshot.json), [pinned `@carbon/styles` 1.110.1 archive](../../../contracts/official_sources/carbon/carbon-styles-1.110.1.tgz), and [snapshot extractor](../../../scripts/quality/official_source_snapshot.py). Current parity covers the extracted token set only, not component DOM/anatomy. |
| Liquid Glass | [liquid-glass.md](../../design/liquid-glass.md) | [liquid-glass.json](../../../contracts/design_profiles/liquid-glass.json) | [Liquid source clauses](../../../contracts/design_sources/liquid-glass.json) | Apple Materials/Layout authority below; glass is functional-layer-only. |
| Shared baselines | [pageshell.md](../../design/pageshell.md), [settings.md](../../design/settings.md), [motion.md](../../design/motion.md), [charts.md](../../design/charts.md) | [profile index](../../../contracts/design_profiles/_index.json), [closed aspect roster](../../../contracts/design_profiles/design_aspect_roster.json) | [shared source clauses](../../../contracts/design_sources/shared.json), [catalog index](../../../contracts/design_sources/_index.json) | Accessibility/responsive baselines are independent and cannot be overridden by a visual reference. |

#### Official design documents to open and lower, not paraphrase from memory

Apple:

- [Layout](https://developer.apple.com/design/human-interface-guidelines/layout)
- [Materials](https://developer.apple.com/design/human-interface-guidelines/materials)
- [Lists and tables](https://developer.apple.com/design/human-interface-guidelines/lists-and-tables)
- [Buttons](https://developer.apple.com/design/human-interface-guidelines/buttons)
- [Color](https://developer.apple.com/design/human-interface-guidelines/color)
- [Typography](https://developer.apple.com/design/human-interface-guidelines/typography)
- [Dark Mode](https://developer.apple.com/design/human-interface-guidelines/dark-mode)
- [Accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility)
- [Motion](https://developer.apple.com/design/human-interface-guidelines/motion)
- [Sidebars](https://developer.apple.com/design/human-interface-guidelines/sidebars) and
  [Split views](https://developer.apple.com/design/human-interface-guidelines/split-views) only if the
  selected route topology actually uses those patterns.

Apple's 44 x 44 guidance is in platform points for a hit region. It is not a universal `44px` visible
box, and it does not authorize the current universal `50px`/`999px` web-button recipe. Button anatomy
and exact web geometry must be contextual and separately sourced or owner-ratified.

Slice 0 must declare the Apple target context (a static-web adaptation and which macOS/iOS/iPadOS
guidance is applicable), capture/access date, and version/last-updated identity. Apple HIG pages are
JavaScript-rendered; a URL-only text fetch that returns “requires JavaScript” is not doctrine ingest.
Use the in-app browser or an approved captured proposition record, then persist the bounded section/
content identity through the Mode B evidence schema.

Carbon:

- [Global header pattern](https://carbondesignsystem.com/patterns/global-header/)
- [UI Shell header usage](https://v10.carbondesignsystem.com/components/UI-shell-header/usage/)
- [2x Grid overview](https://carbondesignsystem.com/elements/2x-grid/overview/)
- [Detailed 2x Grid implementation](https://v10.carbondesignsystem.com/guidelines/2x-grid/implementation/)
- [Data Table usage](https://carbondesignsystem.com/components/data-table/usage/)
- [Structured List usage](https://carbondesignsystem.com/components/structured-list/usage/)
- [Button usage](https://carbondesignsystem.com/components/button/usage/)
- [Tag usage](https://carbondesignsystem.com/components/tag/usage/)
- [Tile usage](https://carbondesignsystem.com/components/tile/usage/)
- [Themes](https://carbondesignsystem.com/elements/themes/overview/)
- [Color](https://carbondesignsystem.com/elements/color/overview/)
- [Typography](https://carbondesignsystem.com/elements/typography/overview/)
- [Spacing](https://carbondesignsystem.com/elements/spacing/overview/)
- [Motion](https://carbondesignsystem.com/elements/motion/overview/)

Accessibility baselines:

- [WAI-ARIA Radio Group Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/radio/)
- [WCAG 2.2 contrast minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
- [WCAG 2.2 target size minimum](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)

Carbon's current Global Header pattern is configurable: header-only, side-panel-only, or a combined
shell can be appropriate depending on the information architecture. A mandatory SideNav and a Data
Table on every route are therefore target choices requiring Mode D owner ratification and route-level
justification, not blanket Carbon mandates. The pinned `@carbon/styles` 1.110.1 token archive, current
v11 documentation, and explicitly versioned v10 grid pages may not be mixed as one source-exact
version; the design slice must declare a compatibility/version policy or remove the legacy source.

If an official page is unavailable or does not actually state the claimed rule, the implementation
must record a gap or use the approved-reference/ratification lane. A URL in a catalog is insufficient:
the clause claim, exact scope, DATA field, rendered fact, predicate, negative case, and exactness mode
must agree.

#### Approved references and the gap-resolution machinery

- [dashboard pre-W3 approved-reference manifest](../../../contracts/reference_packs/dashboard-pre-w3/manifest.json)
- [reference-pack schema](../../../scripts/quality/reference_pack/schema.py)
- [reference-pack producer](../../../scripts/quality/reference_pack/producer.py)
- [reference-pack browser capture](../../../scripts/quality/reference_pack/browser.py)
- [source catalog schema](../../../scripts/quality/design_sources/schema.py)
- [source resolver](../../../scripts/quality/design_sources/resolver.py)
- [source catalog loader](../../../scripts/quality/design_sources/catalog.py)

Durable approved-reference screenshots (visual evidence only for the manifest-owned aspects):

- Apple Dark: [1280](../../../assets/receipts/reference-packs/dashboard-pre-w3/apple-dark-1280.png),
  [390](../../../assets/receipts/reference-packs/dashboard-pre-w3/apple-dark-390.png)
- Carbon: [1280](../../../assets/receipts/reference-packs/dashboard-pre-w3/carbon-1280.png),
  [390](../../../assets/receipts/reference-packs/dashboard-pre-w3/carbon-390.png)
- Liquid Glass: [1280](../../../assets/receipts/reference-packs/dashboard-pre-w3/liquid-glass-1280.png),
  [390](../../../assets/receipts/reference-packs/dashboard-pre-w3/liquid-glass-390.png)

The reference manifest’s aspect list is a closed ownership list. It does not authorize the rest of
the page. Any new discovered website/reference requires a separate approved frozen pack and may own
only the aspects the operator approved.

#### Skill instructions that must become executable

- [design-language-tdd/SKILL.md](../../../skills/design-language-tdd/SKILL.md)
- [doctrine ingest](../../../skills/design-language-tdd/references/doctrine-ingest.md)
- [add a design language](../../../skills/design-language-tdd/references/add-design-language.md)
- [add/govern a page aspect](../../../skills/design-language-tdd/references/add-page-aspect.md)
- [add/govern a component](../../../skills/design-language-tdd/references/add-component.md)
- [proof and receipts](../../../skills/design-language-tdd/references/prove-theme.md)
- [honesty and authority boundaries](../../../skills/design-language-tdd/references/boundaries.md)

The skill is presently stale in important ways: its bootstrap example omits executable observation
arguments, its proof lane still calls real headless proof deferred, and its structure test is mostly
presence/keyword based. The corrective implementation must update the instructions and the tests;
merely linking these files does not satisfy the skill requirement.

#### Executable authorities to run and preserve

| Law | Test / implementation authority |
|---|---|
| Admission mechanism (currently scope-incomplete; no persisted current receipt) | [test_bootstrap_red_ref.py](../../../tests/contracts/test_bootstrap_red_ref.py) and [bootstrap_red_ref.py](../../../scripts/organization/bootstrap_red_ref.py) |
| Page-archetype RED seed (must be strengthened for exact schema/topology) | [test_page_archetype.py](../../../tests/contracts/test_page_archetype.py) |
| Clause-or-gap resolution (currently insufficient for source-text truth or zero rendered gaps) | [test_design_source_provenance.py](../../../tests/contracts/test_design_source_provenance.py) |
| Carbon values match pinned official artifacts | [test_official_source_parity.py](../../../tests/contracts/test_official_source_parity.py) |
| Narrow reference capture hashes/scope (requires source/provenance/orientation hardening) | [test_reference_pack.py](../../../tests/contracts/test_reference_pack.py) |
| Existing narrow dashboard laws (currently has two failures and incomplete component coverage) | [test_dashboard_visual_authority.py](../../../tests/contracts/test_dashboard_visual_authority.py) |
| All route elements have governed ownership | [test_dom_cover.py](../../../tests/contracts/test_dom_cover.py) |
| Theme continuity and route switching | [test_theme_continuity.py](../../../tests/contracts/test_theme_continuity.py) |
| Page intent/required regions | [test_page_manifest.py](../../../tests/contracts/test_page_manifest.py) |
| Rendered Chrome fact schema/matrix | [test_rendered_facts.py](../../../tests/contracts/test_rendered_facts.py) |
| Vacuity and hostile rendered mutations | [rendered-fact adversarial](../../../tests/contracts/test_rendered_fact_adversarial.py), [density adversarial](../../../tests/contracts/test_rendered_fact_density_adversarial.py), [paint adversarial](../../../tests/contracts/test_rendered_fact_paint_adversarial.py) |
| Skill is wired to real mechanisms | [test_skill_structure.py](../../../tests/contracts/test_skill_structure.py), which must be strengthened RED-first |
| Source/test/contract homes are closed | [test_structural_layout.py](../../../tests/contracts/test_structural_layout.py), [test_scripts_layout_contract.py](../../../tests/contracts/test_scripts_layout_contract.py), and [test_tests_layout_contract.py](../../../tests/contracts/test_tests_layout_contract.py) |

#### Current renderer and proof seams to inspect before design

| Concern | Current code/data |
|---|---|
| Generic mini-site archetype to replace | [archetype.py](../../../scripts/rendering/webkit/archetype.py) |
| Dashboard DOM and style | [dashboard.py](../../../scripts/rendering/webkit/dashboard.py), [dashboard_style.py](../../../scripts/rendering/webkit/dashboard_style.py), and [dashboard surface contract](../../../contracts/dashboard_surface.json) |
| Site selector and component substrate | [theme_selector.py](../../../scripts/rendering/webkit/theme_selector.py), [components.py](../../../scripts/rendering/webkit/components.py), and [design adapter](../../../scripts/rendering/webkit/design_render_adapter.py) |
| Shared shell/document renderer | [pageshell.py](../../../scripts/rendering/pageshell/pageshell.py) |
| Route renderers | [dashboard generator](../../../scripts/pipeline/web_render.py), [showcase.py](../../../scripts/rendering/showcase/showcase.py), [settings.py](../../../scripts/rendering/settings/settings.py), and [studio.py](../../../scripts/rendering/studio/studio.py) |
| Rendered observation policy | [rendered_fact_policy.json](../../../contracts/rendered_fact_policy.json) and [rendered-facts design](w4-rendered-facts-design.md) |
| Deterministic/rendered predicates | [design_predicates.py](../../../scripts/contracts/design_predicates.py) and [rendered_predicates.py](../../../scripts/contracts/rendered_predicates.py) |
| Chrome evidence producer | [headless_receipts.py](../../../scripts/quality/headless_receipts.py) |
| Repository CI command | [tests workflow](../../../.github/workflows/tests.yml) |

#### Required closed visible-design coverage join

The new composition work must first add and observe a RED for these exact target homes:

- `contracts/visible_design_coverage.json` — closed aspect/applicability declarations and evidence
  joins;
- `scripts/quality/visible_design_coverage.py` — bounded schema/gather/validation authority;
- `tests/contracts/test_visible_design_coverage.py` — bidirectional closure, source-binding, and
  hostile-mutation contract.

Register all three homes in `contracts/repo_layout.json` and every still-binding legacy layout mirror
in the same slice. The contract key is
`route x profile x viewport x reachable-state x visible-region x design-aspect`. The route/runtime
authority, not the renderer under test, supplies the closed reachable-state roster. The profile route
contract supplies the closed region roster; actual post-mount Chrome DOM must match it. A closed
design-aspect vocabulary and applicability matrix must contain exactly one row for every cell:

The vocabulary is broader than the ten composition axes. At minimum it closes color/palette,
typography, spacing/density, size/geometry/target region, shape/radius, border/divider, elevation/
shadow, material/blur, iconography, motion, component anatomy, navigation, hierarchy, grouping,
alignment, scan path, data presentation, responsive recomposition, and every reachable default/
hover/focus/active/selected/disabled state. Page-archetype owns placement/topology; component aspects
separately own internal anatomy. Neither can stand in for the other.

- `applicable` rows carry `clause_id`, `authority_mode`, pinned `source_identity` plus version/section
  or approved-pack aspect, exact `profile_json_pointer`, `renderer_key`, occurrence/subject identity,
  `fact_id`, `predicate_id`, `mutation_id`, `mutation_receipt_hash`, `receipt_path`,
  `receipt_artifact_hash`, `provenance_path`, and `provenance_hash`;
- `not-applicable` rows carry a closed reason code and the route/profile law that makes the exclusion
  true. A renderer cannot make a hard aspect disappear by omitting its applicability declaration.

For every actual cell, the machine-readable record must resolve this chain:

```text
observed visible region
  -> applicable design aspect
  -> pinned, scoped clause id and authority mode
  -> exact profile DATA path / renderer occurrence
  -> state-specific rendered fact subject
  -> fail-closed predicate result
  -> named killed-mutation witness and hash
  -> current receipt artifact/provenance and hashes
```

Set equality is required in both directions: a rendered visible region/aspect without a chain fails,
and a declared chain with no rendered subject fails. The actual-route Chrome matrix, not a synthetic
fixture, is primary. After an independently reviewed source-to-clause evidence edge exists, this join
proves that the clause was lowered through the runtime/proof pipeline; it does not prove that an AI
read or interpreted a source correctly. No self-reported “I reviewed the docs” field counts as
evidence. Design literals
(geometry, color, type, material, motion, anatomy, and responsive rules) require design authority at
their exact CSS/DOM occurrence. Domain copy, GitHub data, and URLs require content/emitter ownership
but are not falsely treated as Apple/Carbon design literals. UA defaults may be accepted only through
an explicit baseline rule, never by omission.

Minimum focused command set before any completion review:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest -v \
  tests.contracts.test_bootstrap_red_ref \
  tests.contracts.test_page_archetype \
  tests.contracts.test_design_source_provenance \
  tests.contracts.test_official_source_parity \
  tests.contracts.test_reference_pack \
  tests.contracts.test_dashboard_visual_authority \
  tests.contracts.test_dom_cover \
  tests.contracts.test_page_manifest \
  tests.contracts.test_theme_continuity \
  tests.contracts.test_rendered_facts \
  tests.contracts.test_rendered_fact_adversarial \
  tests.contracts.test_rendered_fact_density_adversarial \
  tests.contracts.test_rendered_fact_paint_adversarial \
  tests.contracts.test_skill_structure \
  tests.contracts.test_structural_layout \
  tests.contracts.test_scripts_layout_contract \
  tests.contracts.test_tests_layout_contract
```

That focused set supplements, never replaces, the complete repository suite, mutation runs, Chrome
receipt production, and CODE/ADVERSARIAL review.

Current route-generation entry points (run only after the relevant implementation slice is ready to
regenerate committed bytes) are:

```text
python -m scripts.pipeline.web_render
python -m scripts.rendering.showcase.showcase
python -m scripts.rendering.settings.settings
python -m scripts.rendering.studio.studio
```

Current receipt entry point:

```text
python -m scripts.quality.headless_receipts
```

It requires real Chrome and permission to bind its local test server. In the current restricted
sandbox, the receipt command fails at local-server bind with `PermissionError`; that is not permission
to create placeholders. Run it in the authorized Chrome-capable environment, and update its policy/
inventory first so it emits the profile-specific 12 + 12 + 24 artifact matrix specified below.

### Full design-coverage rule and uncovered-aspect workflow

“Every visible aspect follows the design docs” means **every visible decision has admissible,
aspect-scoped authority**. It does not mean pretending that an official design system publishes a
literal for every full-page web decision. Apple HIG, for example, supplies principles, component
anatomy, hierarchy, layout, and material rules, but not a complete CSS specification for this exact
dashboard. When official authority is silent, the system must resolve the gap honestly rather than
guessing and calling the result Apple.

Every required visible aspect resolves through exactly one of these modes:

1. **Mode A — official code:** consume a pinned, licensable/redistributable official package or
   artifact for this target platform/runtime and prove snapshot parity for the exact aspect it
   covers. It is mandatory only when such an artifact actually covers the claimed web aspect; the
   absence/inapplicability reason must be recorded before falling back to Mode B. Native UIKit or
   SwiftUI code does not become mandatory implementation code for this static web renderer.
2. **Mode B — official specification:** lower a literal or precise rule from the official design
   documentation into profile DATA, a rendered fact, a predicate, and a negative test.
3. **Mode C — approved measured reference:** when official sources omit the decision, measure only a
   user-approved frozen reference pack. The resulting clause is measurement-exact against that
   reference, not falsely “official.”
4. **Mode D — owner-ratified:** when neither official nor appropriate reference authority exists,
   record the operator’s explicit choice as a numbered, scoped law with a mutation handle.

No mode means no authority. A required unresolved aspect blocks the affected named theme/route/state
and completion. The current Carbon Mode A parity is limited to the pinned extracted token set;
UI-Shell, Data Table, Structured List, and other component anatomy require Mode B evidence or an
explicit decision to consume and pin an applicable official web component package.
Optional unresolved aspects remain explicitly deferred and visibly unresolved; they may not acquire a
default renderer value behind the contract’s back. Official authority wins for every aspect it covers.
Overriding it requires an explicit documented fork clause. Accessibility, contrast, input, and
responsive containment floors are independent baselines that no visual reference or owner approval
can waive.

The following section is the only durable W5f **Reference-Derived Design Mode** plan currently in
this repository; there is no separate W5f file to infer. It is binding on this correction and the
`design-language-tdd` skill, but its contract/schema details must be closed in the first DESIGN slice
before implementation:

1. Run a closed coverage audit over every route, profile, viewport, visible region, and required
   composition axis. Emit an uncovered-aspect report rather than filling gaps with defaults.
2. Route each gap to official code or official documentation first.
3. If official sources are silent, accept either:
   - **user-seeded discovery:** the operator supplies URLs/screenshots and says which design or
     specific aspect they like; or
   - **AI-assisted discovery:** a research/crawler pass finds real sites using the relevant design
     language or visual family and prepares candidates.
4. Discovery is evidence-only. The crawler/AI cannot silently promote a site, copy its whole style,
   or treat popularity as authority. It produces a candidate gallery with source URL, capture date,
   theme/state/viewport, rights/availability notes, screenshots, observable anatomy, and the exact
   uncovered aspects each candidate could resolve.
5. Present candidates to the operator **per aspect**, so the operator can choose, for example,
   navigation from reference A, grouped-data treatment from reference B, and reject both for content
   material. “Use this whole page” is allowed only when its full aspect ownership is explicit.
6. Record the approval before measurement. An unapproved crawl remains candidate evidence and cannot
   make a predicate pass.
7. Freeze each approved pack under a governed contract home: source identity, permitted captured
   bytes or minimally necessary snapshots, screenshots, states, viewport set, producer/command,
   hashes, approval record, and replacement policy. Tests never depend on a mutable live website.
8. Measure the frozen pack with the rendered-facts engine across the approved states/viewports.
   Extract design grammar — region topology, alignment, hierarchy, grouping, material placement,
   density, responsive recomposition, anatomy, and forbidden substitutions — not merely isolated
   colors or an averaged aesthetic.
9. Give each reference ownership only over the approved aspects. Never blend several unrelated sites
   into an unattributed “AI average.” Conflicts fail closed.
10. Lower measured facts through the same downstream pipeline as official doctrine:
    clause/provenance -> profile DATA -> renderer -> facts -> predicate -> mutation -> receipt.
11. Revalidation occurs only on explicit operator replacement or pack-version change; a live site
    changing later cannot silently alter the governed design.

The realistic delivery boundary is:

- **Required in this correction:** a minimum manual promotion lane: uncovered-aspect report, candidate
  record supplied by the user or research pass, per-aspect approval record, frozen-pack production,
  exact aspect ownership, precedence/baseline validation, source-to-clause evidence, and executable
  promotion/rejection tests for the three active themes and four routes. No interactive gallery or
  general crawler is required for this correction.
- **Follow-on only:** a richer crawler/gallery may search candidate sites, capture comparable states,
  cluster them by aspect, and let the operator approve choices interactively over the same contracts.
  `repo-surface-scout` currently models local on-disk web surfaces; it is not a web crawler and is not
  authority for this future feature. Any web-discovery producer needs its own durable design and may
  never bypass approval or frozen-pack provenance.

Mode B also needs a real source-to-clause evidence record. Strengthen the design-source schema and
`test_design_source_provenance.py` RED-first so each official-spec clause binds the primary source
identity/domain, capture or last-updated/version identity, exact section/anchor, a minimally necessary
proposition record or content hash, the repository's interpretation/derivation, exact aspect/profile/
invariant scope, negative case, and human review status. A plausible claim plus a real Apple/Carbon
URL is not proof. The visible-coverage join proves lowering only after this reviewed source-to-clause
edge exists; it cannot prove that an AI read a document merely from an ID chain.

### What went wrong

The prior work proved infrastructure properties, not design correctness. It proved registered DOM
owners, bounded hydration, token projection, contrast/overflow checks, and authentic Chrome output.
It did not prove that a page composition came from the named design language.

The concrete failure was:

1. `page-archetype` remained deferred while named themes were still rendered publicly.
2. `scripts/rendering/webkit/archetype.py` used one nav -> hero -> chips -> actions -> card template
   for every profile.
3. The real dashboard, showcase, settings, and studio routes likewise used one shared visible page
   structure, with theme tokens/component skins creating most differences.
4. Normalized semantic DOM signatures converged across all three themes on every route. Token and
   radius changes were incorrectly treated as design-language composition.
5. Apple Dark was washed out, gained generic/full-strength panel edges, lost the stronger integrated
   hero hierarchy, and inherited oversized generic controls.
6. The site theme selector was coupled to vendor-button ideas. It became an oversized square-button
   transplant with broken proportions instead of the approved compact three-segment site control.
7. Dashboard eyebrow/title hierarchy was laid out horizontally/rightward through
   `justify-content: space-between` instead of a leading, vertically stacked hierarchy.
8. Carbon had no ratified Carbon IA/data composition. It was a generic shell rather than an
   intentionally chosen header-only or header/SideNav workspace, and it used no context-appropriate
   Grid, Data Table, or Structured List anatomy.
9. Liquid Glass was used or declared on content cards even though Apple material doctrine reserves
   Liquid Glass for the functional/navigation layer. The stronger opaque/no-CSS-blur content choice
   is a local/reference target that still needs scoped Mode C or D authority; Apple “standard
   material” does not universally mean opaque.
10. Component doctrine was promoted beyond its scope. A sourced button/card token cannot authorize
    navigation, page hierarchy, grouping, density, scan path, responsive recomposition, or an entire
    page family.
11. `D-PAGESHELL-1` overclaimed one shared shell as visible composition authority, and `D-NAV-1`
    cited an unrelated board-law section.
12. Dashboard literal provenance was effectively blanket-assigned. Occurrence stability was
    mistaken for permission to ship the value.
13. Screenshots were treated as producer/authenticity receipts. There was no acceptance predicate
    capable of rejecting an authentic but visibly wrong screenshot.
14. The old bootstrap gate accepted a named RED path without proving that the test existed, ran,
    failed nonzero, failed for the expected reason, or covered the affected scope.
15. The design-language skill was largely keyword/file-presence guidance. It did not execute the
    real admission, route matrix, mutation, and Chrome receipt gates, so “follow the skill” could
    still produce a generic reskin.
16. Visible component defects were left outside the binding proof: raw internal variant IDs can leak
    as labels, the Carbon button can emit an empty SVG, button typography is hard-coded to `17px/600`,
    noninteractive pipeline rows inherit control-like minimum sizing, and the Apple profile still
    contains an unsupported universal `50px`/`999px` button recipe. Fixing only the site selector
    would leave the operator's button/icon/status complaints unresolved.

### What has been completed in this correction session

The following changes are already on disk and are intentional:

1. The failure, operator direction, twelve original must-fixes, and three blocking review verdicts
   are recorded in this on-disk handoff. The file is currently untracked, so it is not durable on
   GitHub until an implementation-owner slice legitimately commits it.
2. The active-plan and downstream-plan links were updated so the correction cannot be silently lost
   or bypassed.
3. A candidate implementation architecture was added to this file. It proposes:
   - a profile DATA schema and ten composition axes that still require an exact authority matrix;
   - Apple editorial/grouped, Carbon UI-Shell/data-table, and Liquid functional-layer families;
   - route-specific composition for index, showcase, settings, and studio;
   - three inert profile templates plus one live mounted tree;
   - delegated theme switching and remount-safe/cached dashboard hydration;
   - selector independence and heading hierarchy; its formerly stated exact selector dimensions are
     not authorized by the current reference manifest;
   - rendered facts, cross-profile divergence predicates, mutation witnesses, receipts, and skill
     enforcement;
   - mechanical completion order and acceptance checklist.
4. `tests/contracts/test_page_archetype.py` was added and registered in two layout authorities. It
   currently checks:
   - presence and selected fields of top-level `page_archetype` DATA for every profile;
   - `page-archetype` emitted rather than deferred;
   - one deterministic rendered archetype invariant per profile;
   - apparently distinct structures from the studio mini-site and dashboard renderers;
   - Apple `editorial-masthead` + `grouped-content` anatomy;
   - the then-proposed Carbon `global-header` + `side-nav` + `data-workspace` anatomy;
   - Liquid `functional-layer` + `content-layer` anatomy;
   - three inert templates and one live host in every committed route;
   - leading/vertical dashboard headings;
   - a theme selector independent of vendor-button geometry.
   It is not yet a closed schema or anti-reskin proof: duplicate route-order entries can pass, unknown
   keys are not rejected, renderer existence/dispatch is not proven, and its skeleton comparison
   preserves profile-specific marker values. One identical topology with renamed markers can therefore
   appear “distinct.” These are required RED mutations, not reasons to weaken the existing test.
5. That provisional test was observed RED before renderer implementation. Result: 7 tests, 5 failures, 1 error,
   1 pass. It failed for missing `page_archetype`, the deferred roster row, absent templates/host,
   right-aligned heading CSS, and shared/missing archetype anatomy. Preserve its bytes and output as
   historical failure evidence, but do not mistake its hard-coded candidate family names or universal
   Carbon SideNav assertion for ratification. After slice 0 resolves those choices, replace/narrow the
   provisional assertions RED-first while retaining the anti-reskin, topology, schema, and route/state
   strength; never edit a RED merely to make current code pass.
6. `scripts/organization/bootstrap_red_ref.py` was partially hardened. CLI admission now binds:
   - actual on-disk `tests/**/*.py` identity and SHA-256;
   - current Git revision;
   - canonical unittest command;
   - nonzero exit;
   - a specific expected failure fingerprint present in bounded output;
   - output SHA-256;
   - UTC timestamp freshness;
   - nonempty route/profile/aspect strings.
   Missing, nonexistent, green, wrong-reason, stale, and path-escaping observations fail closed.
   Scope is **not closed**: nonempty bogus route/profile/aspect names currently admit because the
   script does not resolve them against the manifest/profile/aspect rosters, and direct helper calls
   can fabricate observations. Existing scope tests mutate only to empty. Close both holes RED-first.
7. `tests/contracts/test_bootstrap_red_ref.py` was expanded with mutation probes. Its focused result
   is green: 17 tests passed.
8. One CLI run observed the real page-archetype RED and returned `admit: true`:
   - task: `implement source-backed page archetypes`
   - RED: `tests/contracts/test_page_archetype.py`
   - fingerprint: `KeyError: 'page_archetype'`
   - scope: all four routes, all three profiles, `page-archetype`
   - observation SHA-256:
     `336de113c19cbf3602e30cd311cb46ba57ee05413aaa4c90ce4b008c40329229`
   The command omitted `--write`; no admission JSON exists on disk, and the hash appears only in this
   prose. Treat this as historical observation, not a reusable/persisted receipt. Re-observe after
   design approval and persist to a registered governed path before mutation.
9. Official doctrine was checked for the architecture. The source URLs are listed in the architecture
   section below and must be added as narrowly scoped catalog clauses, not used as broad aesthetic
   permission.
10. No commit or push was performed.

### Exact current worktree state and caution

- Branch: `main`
- HEAD: `64b09040eb2b7188737f44db39c284fc85f0155b`
- HEAD subject: `Migrate dashboard into governed pageshell`
- `origin/main`: `ed86f038e89bb803001f6a5fc7a07bae89e22569`
- Local `main` is three commits ahead and zero behind `origin/main`: `382ca96b`, `3c4aae20`, and
  `64b09040`. None of the 91 tracked modifications or 75 untracked entries is on GitHub.
- At the handoff point the worktree reports 91 tracked modified entries and 75 untracked entries.
- The tree was already heavily dirty before this corrective session. Many W3/W4 profile, renderer,
  receipt, source-catalog, policy, and generated-page files are prior work. Preserve them unless the
  corrective architecture requires an intentional change.
- Do not run `git reset --hard`, `git checkout --`, mass-delete files, or otherwise erase unrelated
  work. Inspect overlapping diffs before editing.
- Current rendered-fact and screenshot artifacts are stale evidence for the rejected implementation;
  they are not proof of the new architecture and must be regenerated only after the new route
  compositions exist.
- No implementation owner has been dispatched from this conversation. The next conversation starts
  with the bounded design-closure slice below, not renderer implementation and not a new recovery
  plan. Actor assignments come from `AGENTS.md` as clarified above.

### Exact current test/proof baseline (rerun 2026-07-14)

- The six-module audit command covering bootstrap, page archetypes, provenance, official parity,
  reference pack, and dashboard authority ran 40 tests: 32 passed, 7 failed, 1 errored.
- Bootstrap alone: 17/17 pass.
- Page archetype alone: 7 total = 1 pass, 5 failures, 1 `KeyError: 'page_archetype'` error.
- `test_dashboard_visual_authority` has two additional failures: committed `site/index.html` lacks
  the required box-sizing reset, and committed Showcase pass rows lack source-authority attributes.
- The full focused command listed above ran 102 tests: 39 failures and 13 errors. This is the honest
  current baseline, not a nearly-green implementation.
- Structural/layout failures include undeclared `contracts/design_sources/*.json`, undeclared
  `scripts/quality/design_sources/{catalog,resolver,schema}.py`, undeclared
  `scripts/quality/official_source_snapshot.py`, and unregistered
  `tests/contracts/test_design_source_provenance.py`. The linked files exist but are not yet legally
  homed by all current registries.
- Current page-manifest/committed-page drift also fails. Existing byte-scan aliases can falsely pass
  once inert templates exist because a required region in any template satisfies the scan; the new
  RED must validate required regions in each profile template and in the post-mount live DOM.

### Current DESIGN-gate must-fixes — all blocking

The twelve original corrective must-fixes remain binding. The final factual/coherence/source audit
adds these design-closure requirements; slice 0 must answer them in machine-lowerable detail:

1. **Resolve actor and doctrine conflicts.** Apply the role/precedence section above and enumerate the
   exact `AGENTS.md`, `DESIGN-SYSTEM.md`, `pageshell.md`, Liquid doctrine, Apple doctrine, bootstrap
   docstring, skill, invariant, and test clauses to update, retire, or narrow.
2. **Map authority, do not label it.** Supply a 3-profile x 10-composition-axis table with one or more
   narrow Mode A/B/C/D clauses, source identity/section/exactness, DATA pointer, negative case, and
   mutation per cell. Ratify the three target-family labels as Mode D; the labels own no axes by
   themselves.
3. **Close every visible aspect.** Define the complete aspect vocabulary/applicability/state matrix
   described above, including page topology and component-internal anatomy. Classify all 40 current
   provenance gaps and every rendered `covered-deferred` aspect as resolve-now or blocking; no visible
   rendered subject may remain deferred behind a green page-archetype claim.
4. **Make source grounding non-circular.** Design the Mode B source-evidence record and hostile tests
   for wrong domain/version/section, unrelated proposition, changed live content, bad scope, and
   missing reviewer approval. Declare Apple platform/context/date and Carbon v10/v11/1.110.1
   compatibility policy. Scope Mode A to applicable target-runtime artifacts.
5. **Ratify project choices honestly.** Obtain Mode C/D authority for the Apple editorial target,
   Apple palette/surface hierarchy, this site's opaque/no-CSS-blur content recipe, Liquid floating
   functional topology, Carbon route-by-route header/optional-SideNav/table mapping, exact Carbon
   border/shadow mapping, and selector dimensions. Do not attribute these choices wholesale to HIG
   or Carbon.
6. **Mechanize the actual visible complaints.** Add RED/FACT/PREDICATE/mutation obligations for washed
   Apple colors, huge/wrong buttons, typography, internal variant labels, empty/broken icons,
   noninteractive pipeline sizing, selector proportions, right/horizontal headings, universal panel
   outlines, grouping, and material placement on every affected route/state.
7. **Close archetype/schema anti-vacuity.** Specify exact keys and uniqueness, renderer existence and
   dispatch, gap-based render refusal, per-profile template/live-region validation, and a topology
   comparison that canonicalizes marker values away. Reconcile the current test's provisional hard-
   coded family names and universal Carbon SideNav with the ratified route matrix. One shared DOM with
   renamed markers must fail.
8. **Close the W5f minimum lane.** Name the contracts, JSON shapes, homes, approval identity/state
   machine, commands, source/rights metadata, pack-version/replacement rules, and REDs for uncovered
   report -> candidate -> per-aspect operator approval -> frozen pack -> measured grammar -> promoted
   clause. The richer crawler/gallery remains a separate unimplemented follow-on.
9. **Strengthen Mode C evidence.** Bind source gzip/decompressed bytes, fixture, renderer source,
   producer/command/Chrome provenance, facts, aspect-to-occurrence paths, and approval hashes. Add
   actual orientation DOM facts. Freeze the seven operator comparison images as rejected evidence or
   explicitly request reattachment; never use `/tmp` as durable proof.
10. **Close mount/runtime semantics.** Use a neutral host with valid language-owned landmarks; define
    no-JS/first-paint behavior, live-ID/heading/selector counts, per-profile manifest/DOM cover, focus
    restoration, and Dashboard/Showcase/Settings/Studio state preservation through remounts.
11. **Close admission itself.** Validate nonempty scope values against closed route/profile/aspect
    authorities, prevent fabricated helper observations, update the stale `AGENTS.md` invocation and
    phantom Rust-authority docstrings, then persist a fresh time/base/test/output-bound closed
    observation+claim envelope at a registered path before mutation.
12. **Close the evidence inventory.** Specify and register exactly 12 profile-specific 1280 PNGs, 12
    profile-specific 390 overflow probes, 24 route/profile/viewport fact packets, every reachable
    state, all provenance sidecars/hashes, and the producer/policy changes that make missing or generic
    default-theme artifacts fail.
13. **Respect bounded slices.** Reconcile the dirty main branch/ahead-of-origin state without data
    loss, split work according to the sequence below, require design/RED/review per slice, and allow
    only reviewed branch commits. Final merge/push waits for integrated CODE and ADVERSARIAL approval.

Until all thirteen are closed, the correct design verdict remains `REVISE` and no renderer mutation
is authorized by this handoff.

### What is not implemented yet

None of the following may be claimed complete:

1. The corrective design itself is not approved. It lacks a clause-by-clause authority table for all
   three profiles x ten composition axes, a full visible-aspect applicability schema, and several
   explicit owner decisions listed in the current DESIGN must-fixes below.
2. The three profile JSON files do not yet have the required closed `page_archetype` DATA.
3. `page-archetype` has not yet been honestly flipped to emitted with passing rendered facts.
4. Apple/Carbon/Liquid page-composition clauses and doctrine scopes have not been added/repaired.
   In particular, Apple universal button geometry and Liquid content-card glass claims remain wrong.
5. `render_archetype()` and `render_dashboard_surface()` have not been replaced with real
   DATA-dispatched language compositions.
6. The four routes do not yet contain three inert profile templates and one neutral live host.
7. Theme switching is not yet a one-live-tree mount lifecycle with focus and route-state restoration.
8. Dashboard hydration is not yet scoped/remount-safe against the active mounted host.
9. Showcase, settings, and studio have not yet been composed separately for all three languages.
10. Selector anatomy is ratified, but exact dimensions are not: the frozen reference owns
    `selector-edge`, not `selector-geometry`. The dimensions need a new operator-approved manifest
    aspect or a Mode D law before becoming acceptance thresholds.
11. Rendered facts do not yet capture archetype identity, ordered regions, landmarks, heading
    alignment, selector boxes, material placement, contextual layers, grouped ownership, or live-ID
    uniqueness.
12. A cross-profile actual-route divergence predicate/test has not yet landed.
13. Literal provenance is not yet occurrence-scoped across all new visible design values.
14. The active profiles contain 40 visible component/motion provenance gaps (Liquid 13, Carbon 12,
    Apple 15). Existing provenance tests allow a gap object; every invariant whose subject actually
    renders must instead resolve or block that route/profile/state from completion. Deferred KPI,
    input, table, chart, hero, button, chip, card, type, spacing, palette, icon, and motion aspects
    cannot be laundered through a completed page-archetype row.
15. The design-language skill has not yet been upgraded and forward-tested against a generic reskin.
16. The W5f uncovered-aspect/reference-derived lane is not executable: there is no closed
    uncovered-aspect report, candidate record, per-aspect approval record, or general frozen-pack
    promotion gate wired into the skill.
17. The richer AI crawler/gallery remains follow-on infrastructure; it must remain
    evidence-only and cannot be substituted with unapproved scraping.
18. The affected 4 route x 3 profile x 1280/390 evidence matrix has not been regenerated for the new
    implementation.
19. The reference pack validates its six named capture hashes, but does not yet prove all source-gzip,
    fixture, renderer-source, provenance-command/Chrome, fact-to-provenance, or orientation-DOM edges.
    Its `approval.evidence_ref` points back to this handoff; freeze the exact seven approved aspects in
    a non-circular approval record before treating the mechanism as general Mode C authority.
20. The seven operator comparison images from the original conversation are not durably present in
    this repository. `/tmp` audit captures are ephemeral and current page screenshots are stale/mixed.
    Before visual adjudication, freeze a governed **rejected-evidence** pack (explicitly
    non-authoritative/non-acceptance) or ask the operator to reattach the missing images. The approved
    pre-W3 pack remains authority only for its seven manifest aspects.
21. Focused/full tests, meaningful mutations, CODE review, ADVERSARIAL review, bounded branch commits,
    and any merge/push remain undone. There is no root Makefile or `make verify` target; the CI full
    suite is `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v`.

### Required bounded slice sequence

Do not attempt this as one 166-entry mega-slice. Every item below gets its own scratch design with
open forks, executable admission, observed RED, registered homes, mutations, receipts where visible,
and independent gates under `AGENTS.md`. Branch commits are allowed only after that slice's required
reviews; do not merge or push the correction to `main` until the final integrated CODE and
ADVERSARIAL gates approve. Preserve the dirty tree and never use destructive cleanup to create the
branch boundary.

0. **DESIGN closure, no renderer mutation.** Read every linked source/seam. Produce the exact 3
   profiles x 10 composition-axis authority table; the full visible-aspect vocabulary/applicability
   matrix; Apple platform/version context; Carbon version policy; Mode C/D decisions for palette,
   selector geometry, opaque/no-blur site content, and target families; route/state topology; neutral
   mount/first-paint/focus/state semantics; 12 screenshot + 12 mobile-probe + 24 facts artifact shape;
   W5f schemas; source-evidence schema; and the exact stale clauses/tests to retire. Codex must issue
   `DESIGN-VERDICT: APPROVE` on that scratch design before slice 1.
1. **Admission/source foundation.** RED-first close bootstrap scope against the actual route/profile/
   aspect rosters and prevent fabricated helper observations. Current `--write` stores only the raw
   observation, not the `BootstrapRedRefClaim`; change/add a CLI output that persists one closed,
   recomputable observation+claim admission envelope at a newly registered governed path. Then add
   source-to-clause evidence and strengthen reference-pack/approval verification.
2. **Coverage and fail-closed rendering admission.** Land the exact visible-design coverage contract,
   closed applicability/state rosters, gap-blocking renderer admission, hostile source mutations, and
   non-vacuous topology canonicalization. Fix page-manifest and DOM-cover checks for each inert profile
   template plus the post-mount live DOM.
3. **Neutral mount lifecycle.** Use a neutral `<div data-page-profile-host="site">`, never a shared
   `<main>`. Each cloned composer owns valid header/nav/main landmarks. Specify no-JS/first-paint
   behavior, one live tree, no live duplicate IDs, delegated switching, focus restoration to the
   corresponding radio after a keyboard remount, and preservation/restoration of Dashboard,
   Settings, Showcase, and Studio route state.
4. **Control/component substrate.** Fix and RED-test the local theme selector, all visible buttons,
   labels, icons, pipeline status rows, internal variant leakage, context-specific typography/target
   regions, and profile component gaps. Vendor button geometry may not leak into the selector.
5. **Apple route family.** Implement its approved route compositions across all four routes from DATA;
   prove palette/surface hierarchy, component anatomy, typography, grouping, responsive behavior, and
   interactive states, not just an archetype marker.
6. **Carbon route family.** Implement its approved route compositions across all four routes from
   DATA. Use SideNav/Data Table only where the ratified IA/route mapping calls for them; prove official
   token parity and separately sourced component anatomy.
7. **Liquid route family.** Implement its approved route compositions across all four routes from
   DATA. Official law forbids Liquid Glass in content; the site's exact standard/opaque content recipe
   follows its separately ratified clause.
8. **Integrated facts, predicates, and evidence.** Add cross-profile topology divergence after marker
   values are canonicalized away; run every state; produce exactly 12 profile-specific 1280 PNGs, 12
   profile-specific 390 overflow JSON probes, 24 rendered-fact packets, and a provenance sidecar for
   every artifact. Update producer policy/inventory and naming (for example
   `screenshot-<profile>-1280.png` and `dom-probe-<profile>-390.json`) so generic default-theme files
   cannot stand in for all profiles.
9. **Reference lane and skill.** Make the minimum manual W5f promotion lane executable, update and
   forward-test `skills/design-language-tdd`, and prove it rejects a generic reskin, bogus official
   claim, unapproved reference, unresolved rendered component gap, and vacuous mutation.
10. **Integrated review.** Regenerate committed pages/conformance claims, run the focused command and
    `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v`, run every named mutation, then
    obtain final Codex CODE and ADVERSARIAL approval before merge/push/completion.

### Definition of done

Completion means the system, not a human promise, rejects the old failure:

- Apple is visibly dark with a ratified palette/surface hierarchy and a leading, grouped composition;
  its exact target family is Mode D, while official sources own only their scoped anatomy/principles.
- Carbon uses the owner-ratified route-by-route shell/navigation/data anatomy with official contextual
  tokens; neither SideNav nor Data Table is treated as mandatory merely because the profile is Carbon.
- Liquid Glass exists only in the functional/navigation layer; the site's content material/opacity is
  governed by a separate Mode C/D clause rather than misquoted as an Apple universal.
- All twelve route/profile compositions carry their declared anatomy and do not collapse to one
  normalized template.
- All visible regions and design literals/occurrences have scoped authority or block completion; all
  rendered component aspects are emitted/proven rather than hidden behind deferred roster rows.
- Theme switching mounts one valid live tree and hydration works after every transition.
- The compact selector, buttons/icons/status rows, leading heading hierarchy, palette/material rules,
  and grouped-row ownership are geometry-/DOM/state-tested and mutation-proven.
- Every required visible aspect resolves through official code, official specification, an
  operator-approved frozen reference, or an owner-ratified scoped clause; no silent renderer default
  or unresolved required gap remains.
- The manual reference lane accepts user- or research-seeded candidates and operator approval per
  aspect; future AI/web discovery may propose candidates but cannot make them authoritative without
  that approval and a frozen pack.
- All 24 route/profile/viewport cells have current authentic acceptance evidence and no overflow.
- The skill rejects a synthetic generic reskin.
- Every focused/full/structural/mutation/receipt gate is green.
- The approved scratch design and finished diff contain exactly one current machine-checkable line
  per gate: `DESIGN-VERDICT: APPROVE`, `VERDICT: approve`, and
  `ADVERSARIAL-VERDICT: APPROVE`.

Anything less is still the rejected W3 implementation.

## Codex corrective audit — binding gate (2026-07-14)

Operator direction: preserve the governed infrastructure, make the visible result correct through
that system, and make semantic TDD reject this exact generic/token-skinned failure before it can
render or claim completion. A rollback or local cosmetic patch is not an acceptable completion.
Codex was directed to audit and record the correction. That did not establish a standing builder
exception for a future conversation; actor roles follow the current `AGENTS.md` protocol stated at
the top of this handoff.

### Audit finding

W3 proved the wrong proposition. It proved that the dashboard had registered owners, bounded DOM,
profile-fed tokens, and real receipts. It did not prove that Apple Dark had an Apple-grounded page
composition, Carbon had a Carbon UI-Shell/data composition, Liquid Glass respected functional versus
content material placement, or that any actual route differed beyond a shared template and component
skin. `page-archetype` remained deferred while public named themes rendered anyway. The screenshots
were authenticity receipts, not acceptance receipts. The prior W3 design approval is therefore void.

### Numbered must-fixes

1. **Close composition authority before rendering.** Every active language must resolve navigation,
   hero/orientation, hierarchy, grouping, data presentation, density, alignment, material placement,
   scan path, and responsive composition to official doctrine or a narrowly scoped operator-approved
   frozen reference. Any required `candidate`, `declared-unresolved`, or deferred `page-archetype`
   blocks named-theme completion.
2. **Make archetype top-level DATA.** Profiles must carry a closed page-archetype declaration that
   selects real renderer anatomy. Apple editorial/grouped composition, Carbon UI-Shell/data-table
   composition, and Liquid Glass functional-layer composition may share utilities, content data, and
   accessibility laws, but may not share one normalized page DOM with token/radius swaps.
3. **Write REDs against the actual failure.** Before changing renderers, tests must fail when all
   profiles use one template; when normalized route DOM converges; when only CSS/token fingerprints
   differ; when Carbon lacks its shell/data anatomy; when Apple lacks its editorial/grouped hierarchy;
   or when declared archetype DATA and rendered structure disagree.
4. **Test real routes, not a toy fixture.** Composition conformance must execute every manifest route
   under every active profile at 1280 and 390. Static synthetic component specimens may supplement
   that matrix but cannot satisfy it.
5. **Separate local controls from vendor buttons.** The persistent site theme selector owns its own
   compact geometry and interaction contract. It may consume sourced color/focus roles, but must not
   inherit vendor button height, radius, anatomy, check icons, or touch-target box size.
6. **Close literal provenance per occurrence.** A citation or approved-reference aspect may authorize
   only the exact renderer fields and rendered facts it governs. Blanket provenance across unrelated
   CSS occurrences is forbidden. A recursive literal/occurrence scan must fail unowned visible values.
7. **Promote screenshots to acceptance evidence.** MF1 remains mandatory, but acceptance also compares
   current computed geometry, hierarchy, alignment, material, density, and overflow against official
   clauses or the frozen approved reference. A real, nonblank, ugly screenshot is still a failure.
8. **Mutation-prove composition.** Right-aligning headings, enlarging/stacking the selector, adding a
   universal section outline, moving Liquid Glass into content, flattening language archetypes, or
   replacing grouped rows with generic cards must each red the predicate that names that law.
9. **Make RED admission executable and non-vacuous.** Admission must bind base revision, test identity
   and hash, nonzero exit, expected failure fingerprint, route/profile/aspect, and timestamp. Missing,
   nonexistent, already-green, stale, or unrelated RED references must be rejected.
10. **Make the skill execute the gate.** `design-language-tdd` must invoke deterministic admission,
    doctrine closure, actual-route matrix, provenance, mutation, and receipt checks. Keyword/file
    presence is not proof that the workflow was followed. Forward-test the skill on a generic reskin
    and require it to reject the result.
11. **Keep claims honest.** Public conformance rows and completion status must fail closed. Neither W4
    raw facts nor a profile-labelled render may claim `pass` while any required composition authority,
    predicate, matrix cell, mutation, or acceptance receipt is missing.
12. **Finish mechanically.** Every new source/test/contract/receipt home must be registered in the
    same slice; the focused and full suites must be green; all affected-route MF1 receipts must have
    honest Chrome provenance; and independent CODE plus ADVERSARIAL review must approve the final diff.

REJECTED-W3-DESIGN-GATE: revise

The current worktree is mechanically unfinished and the focused contract run reported failures and
errors. It is not eligible to land even apart from the design-composition failure.

REJECTED-W3-CODE-GATE: revise

The present proof surface permits arbitrary RED references, deferred page archetypes, shared-DOM
token reskins, blanket provenance, and authentic screenshots with wrong composition.

REJECTED-W3-ADVERSARIAL-GATE: revise

These verdicts remain binding until a new dated review section records the exact green commands,
mutation witnesses, receipt matrix, diff revision, and independent approvals. Editing this section
or removing its links is not resolution.

### Corrective implementation admission

One ephemeral CLI run returned `admit: true` after observing the current page-archetype test fail for
the expected missing-DATA reason:

- task: `implement source-backed page archetypes`
- RED: `tests/contracts/test_page_archetype.py`
- expected fingerprint: `KeyError: 'page_archetype'`
- scope: routes `index`, `showcase`, `settings`, `studio`; profiles `apple-dark`, `carbon`,
  `liquid-glass`; aspect `page-archetype`
- observation SHA-256: `336de113c19cbf3602e30cd311cb46ba57ee05413aaa4c90ce4b008c40329229`
- verdict returned by that run: `admit: true`

Command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m scripts.organization.bootstrap_red_ref \
  "implement source-backed page archetypes" \
  "tests/contracts/test_page_archetype.py" \
  --expect "KeyError: 'page_archetype'" \
  --routes index,showcase,settings,studio \
  --profiles apple-dark,carbon,liquid-glass \
  --aspects page-archetype
```

The command above is a historical replay record, not a persisted envelope: it omitted `--write`, and
the current scope check accepts arbitrary nonempty strings. After slice 1 closes scope, re-observe and
persist a closed `RedAdmissionReceipt`-style envelope at
`assets/receipts/admissions/w3-page-archetype-red.json`; register that receipt home in the same slice.
The envelope contains the raw observation plus a recomputable `BootstrapRedRefClaim` and binds the
then-current base revision/test hash/time/scope. Do not mistake the current raw-observation-only
`--write` behavior for that envelope. The new receipt replaces, not retroactively validates, this
ephemeral result.

The earlier named-reference-only admission for
`tests/contracts/test_dashboard_visual_authority.py` is retained in history as evidence of the
vacuous gate that this slice replaces; it does not authorize implementation.

## Candidate implementation architecture — DESIGN gate input (2026-07-14)

This section preserves the intended architecture for the repository-assigned implementation owner.
It is design input, not permission to edit renderers. The final audit found open authority, source,
mount, component, reference, and evidence forks; slice 0 above must close them and receive DESIGN
approval first.

### Outcome and non-goals

The candidate target families are three genuinely different page-language compositions from one
shared content model:

- `apple-dark` -> `apple-editorial-grouped`
- `carbon` -> `carbon-ui-shell-data-table`
- `liquid-glass` -> `liquid-functional-layer`

These family labels are owner-selected Mode D candidates, not conclusions stated by Apple or Carbon.
They become binding only when slice 0 ratifies the family and maps every composition axis to a narrow
Mode A/B/C/D clause. The label itself never authorizes all ten axes.

Shared data, escaping, accessibility utilities, URL policy, and hydration mechanics are allowed.
Shared visible wrapper anatomy, region topology, scan path, material placement, or one normalized
DOM with token/radius swaps are forbidden. This is not a rollback, a screenshot-matching CSS patch,
or permission to weaken an existing test. The current pre-W3 reference is an acceptance authority
only for the aspects its manifest names.

### Source authority

The implementation must add narrowly scoped page-composition clauses to the existing catalogs and
doctrine documents. A clause may authorize only the profile, aspect, invariant, renderer field, and
rendered fact named in its scope.

- Apple layout: `https://developer.apple.com/design/human-interface-guidelines/layout` — important
  information belongs at the top/leading edge; alignment and hierarchy communicate relationships.
- Apple materials: `https://developer.apple.com/design/human-interface-guidelines/materials` — do not
  use Liquid Glass in content; use standard materials there. “Standard” can include translucent/
  blurred material, so this site's opaque/no-CSS-blur recipe still needs Mode C/D authority.
- Apple sidebars and split views:
  `https://developer.apple.com/design/human-interface-guidelines/sidebars` and
  `https://developer.apple.com/design/human-interface-guidelines/split-views` — adaptive navigation
  anatomy, not authority for a generic card shell.
- Carbon global header: `https://carbondesignsystem.com/patterns/global-header/` — configurable UI
  Shell/global-header anatomy. Header-only, side-panel-only, or combined navigation depends on IA;
  this source does not mandate SideNav on every route.
- Carbon Data Table and Structured List:
  `https://carbondesignsystem.com/components/data-table/usage/` and
  `https://carbondesignsystem.com/components/structured-list/usage/` — primary structured-data
  presentation when the data/use case fits; they do not mandate a table on every route.
- Carbon grid: `https://carbondesignsystem.com/elements/2x-grid/overview/` and the detailed grid
  implementation at `https://v10.carbondesignsystem.com/guidelines/2x-grid/implementation/` —
  16-column desktop composition and 32px gutters.
- Owner-ratified site laws `R-W3-VIS-1` and `R-W3-VIS-2` in this document govern only the persistent
  theme selector and home orientation. They do not masquerade as Apple or Carbon doctrine.

`D-PAGESHELL-1` must be narrowed to neutral document mechanics: one valid document, persisted theme,
token projection, accessibility, bounded viewport, and mount lifecycle. It must not claim a shared
visible hierarchy or composition. `D-NAV-1` must cite the actual navigation doctrine in this document
or `pageshell.md`; its current board-law source is unrelated and cannot remain.

### Target closed profile DATA (not yet enforced by the current test)

Each active profile gains exactly one top-level `page_archetype` object. Its closed shape is:

```json
{
  "contract_id": "DesignPageArchetype",
  "schema_version": 1,
  "target_family": "apple-editorial-grouped",
  "renderer_key": "apple-editorial-grouped.v1",
  "gaps": [],
  "axes": {
    "navigation": {"value_id": "...", "clause_ids": ["..."], "refute_by": "..."},
    "hero-orientation": {"value_id": "...", "clause_ids": ["..."], "refute_by": "..."},
    "hierarchy": {"value_id": "...", "clause_ids": ["..."], "refute_by": "..."},
    "grouping": {"value_id": "...", "clause_ids": ["..."], "refute_by": "..."},
    "data-presentation": {"value_id": "...", "clause_ids": ["..."], "refute_by": "..."},
    "density": {"value_id": "...", "clause_ids": ["..."], "refute_by": "..."},
    "alignment": {"value_id": "...", "clause_ids": ["..."], "refute_by": "..."},
    "material-placement": {"value_id": "...", "clause_ids": ["..."], "refute_by": "..."},
    "scan-path": {"value_id": "...", "clause_ids": ["..."], "refute_by": "..."},
    "responsive-composition": {"value_id": "...", "clause_ids": ["..."], "refute_by": "..."}
  },
  "routes": {
    "index": {
      "manifest_archetype": "landing",
      "region_roster": ["..."],
      "wide_order": ["..."],
      "compact_order": ["..."]
    }
  }
}
```

The other three manifest routes are required and no extra route is permitted. Each route roster is
the complete set of visible semantic regions, not four generic aliases. `wide_order` and
`compact_order` must each place every roster member exactly once. A nonempty `gaps` array, missing
axis, unresolved clause, absent renderer, or renderer/profile disagreement blocks named-theme
rendering and every completion claim.

`test_page_archetype.py` does not yet prove this target: add exact-key, uniqueness, duplicate-order,
renderer-existence/dispatch, nonempty-gap render-refusal, and post-mount tests RED-first.

The aspect roster flips `page-archetype` to `emitted`. Each profile emits exactly one deterministic,
rendered invariant (`ap-page-archetype`, `cb-page-archetype`, `lg-page-archetype`) with a scoped
catalog clause, a real rendered predicate, and a mutation handle. `covered-emitted` is not sufficient
without that invariant passing the full route/profile/viewport matrix.

### Renderer boundary

There are four layers, and only the first two may be shared across design languages:

1. **Document layer:** doctype, metadata, root token blocks, scripts, CSP-compatible escaping, and one
   `data-page-profile-host="site"` mount point.
2. **Content view-model:** typed route data and semantic regions, with no wrapper tags, CSS classes,
   region order, or material decisions.
3. **Language composer:** one renderer per `renderer_key`. It owns tags, landmarks, navigation
   anatomy, region topology/order, heading placement, material roles, and responsive recomposition.
4. **Route projector:** maps route view-model regions into the selected language composer without
   branching on profile names. Dispatch is through profile DATA only.

Do not replace the current generic `render_page_shell` with a larger generic shell. Refactor it into
neutral document/mount utilities and three independent language composers. Any new source/test home
must be added to `contracts/repo_layout.json` and all legacy layout mirrors in the same diff.

### One-live-tree mount lifecycle

Every generated route contains one inert template per active profile and one live host:

```html
<div data-page-profile-host="site"></div>
<template data-page-profile="apple-dark"
          data-page-archetype="apple-editorial-grouped">...</template>
<template data-page-profile="carbon"
          data-page-archetype="carbon-ui-shell-data-table">...</template>
<template data-page-profile="liquid-glass"
          data-page-archetype="liquid-functional-layer">...</template>
```

The host is deliberately a neutral `div`. The selected language clone owns valid global-header/nav/
main landmarks; a shared `main` host would incorrectly nest or capture Carbon's shell landmarks.

The shared theme runtime validates the closed roster, chooses URL -> persisted -> house theme,
clones exactly one inert template into the host, sets `data-theme`, updates propagation links, and
dispatches `site-profile-mounted` with the selected profile. Click and keyboard behavior is
delegated from the document so remounting cannot orphan listeners. Duplicate IDs inside inert
templates are acceptable; duplicate IDs in the live tree are not. Exactly one visible page title,
intro, theme selector, selected radio, and active navigation item must exist after every mount.

Slice 0 must decide and test first-paint/no-JS behavior. A keyboard-triggered remount restores focus
to the corresponding selected radio in the new live tree. Dashboard data, Showcase filter/expansion,
Settings choices, and Studio base/swap/workbench state must survive or be intentionally reconstructed
across a profile remount; delegated listeners alone do not prove state continuity.

The dashboard fetches once, caches the validated payload, and hydrates the active host after initial
mount and every `site-profile-mounted` event. All prototype lookup, static writes, counts, and target
queries are scoped to the active host. A remount resets only that host. The existing closed write
grammar, URL allowlist, clone budgets, and hydration hash are updated intentionally; no global
`document.getElementById` may target an inert template.

### Language compositions

#### Apple Dark — editorial + grouped

- `data-arch-region="editorial-masthead"` contains the leading navigation/orientation and compact
  theme control. The title and intro stay left-stacked; the home route keeps its approved integrated
  masthead and has no self-breadcrumb.
- `data-arch-region="grouped-content"` is the proposed single editorial reading/data column of dark
  surfaces. Related facts use one inset group with chromeless rows and subtle dividers; never one
  floating card per metric.
- Once its Mode C/D clause is ratified, this site's content is opaque (`backdrop-filter: none`). A
  Liquid Glass content treatment, universal panel outline,
  full-strength hairline, right-aligned section title, or 999px/50px rule applied to the local theme
  selector is a failing mutation.
- Wide composition uses the approved 20px dashboard gutter and leading scan path. Compact uses the
  approved 12px dashboard gutter, one column, and preserves left hierarchy without horizontal
  overflow.

#### Carbon — UI Shell + data workspace

- `data-arch-region="global-header"` is the proposed Carbon global product header.
- Where the slice-0 IA mapping ratifies it, `data-arch-region="side-nav"` owns route navigation on
  wide screens and adapts to a compact navigation control at 390px. Routes not needing hierarchical
  navigation use the ratified header-only composition instead.
- `data-arch-region="data-workspace"` is the main workspace. Use Carbon grid/layer roles and, only
  where the content/ratified route mapping fits, Data Table or Structured List anatomy. It is not
  Apple grouped rows with square corners.
- Surfaces use `$background`, `$layer-01`, nested `$layer-02`, and contextual `$border-subtle` roles
  where the route-to-layer mapping calls for them. Exact outer `border`, shadow, and square-geometry
  choices require a narrow Mode B/D clause; Tile guidance is not blanket permission. Headings are
  start-aligned, compact, and grid-aligned. When both exist, the global header and SideNav remain
  distinct landmarks.

#### Liquid Glass — functional layer + separately governed content

- `data-arch-region="functional-layer"` contains navigation, theme selection, and workbench controls
  on a floating/translucent material layer.
- `data-arch-region="content-layer"` contains every report, chart, metric, table, and explanatory
  section without Liquid Glass. The site's proposed opaque `backdrop-filter: none` content recipe
  requires its own Mode C/D clause.
- Glass may never be applied to a content group merely because the active profile is Liquid Glass.
  Removing the functional/content split or moving blur into content is a failing mutation.
- Compact composition keeps the functional controls reachable without covering content or causing
  viewport overflow.

### Candidate route-specific composition (requires slice-0 Mode D ratification)

- **Index / landing:** preserve all dashboard bindings and prototype budgets. Apple is an editorial
  masthead followed by grouped readouts; Carbon uses the ratified header-only or header/SideNav data
  workspace and uses tables/structured lists only where the content fits; Liquid is a floating
  functional bar over separately governed dashboard content. `Flagship
  projects` and `Current focus` remain separate. Section eyebrow and title remain vertically stacked
  at the leading edge.
- **Showcase / proof report:** Apple is a grouped editorial dossier per language; Carbon is the
  ratified workspace whose suitable receipt rows may use a Data Table; Liquid keeps filters/navigation in the
  functional layer and report/specimen material separately governed. Existing receipt closed-cover equality is
  preserved.
- **Settings / control plane:** Apple uses Settings-style grouped label/accessory rows; Carbon uses a
  compact admissibility matrix and a Data Table only if the mapping ratifies that fit; Liquid places controls in the functional layer and laws/
  results in separately governed grouped content. Existing admissibility semantics remain unchanged.
- **Studio / workbench:** Apple uses an editorial preview and grouped swap controls; Carbon uses the
  ratified header-only or split SideNav/tooling workspace; Liquid uses a floating tool palette over
  separately governed content. The
  nested mini-site rendered by `render_archetype()` must itself have the selected base profile's real
  archetype, not the old shared nav -> hero -> chips -> actions -> card template.

### Persistent theme selector

The selector is a site control, not an Apple button, Carbon Button, or Liquid Glass Button. It owns
its own renderer and geometry, consumes only profile color/focus roles, has no icon, and remains
three equal radio segments on one row. It uses one selected/tabbable option, delegated arrow/Home/
End/Space/Enter behavior, immediate persistence, and `:focus-visible` styling. Vendor button anatomy,
radius, minimum height, padding, and variants cannot alter its output.

The WAI-ARIA Radio Group pattern grounds one checked radio, roving tab entry, arrows, and Space.
Home/End/Enter are owner-ratified local enhancements, not falsely labeled APG requirements. The
reference pack currently owns only `selector-edge`; desktop `255.47 x 37.94` and 390px values
(`52px` high; slots Apple `300px`, Carbon `324px`, Liquid `308px`) are observed candidate facts, not
acceptance authority. Slice 0 either adds an explicitly operator-approved `selector-geometry` aspect
to a new manifest version or chooses and ratifies different responsive geometry. Until then, tests
may reject stacking/obvious oversized button transplantation but may not call those exact numbers
reference-approved. The pack may not be extrapolated from dashboard/default state to other routes or
interaction states without an explicit Mode D reuse law.

### RED, FACTS, predicates, and mutation proof

The already-observed `tests/contracts/test_page_archetype.py` bytes/output are historical RED
evidence, not immutable design authority. Slice 0 must ratify or replace its provisional exact-family
and Carbon SideNav assertions, observe the corrected RED for the right reason, and persist the new
closed admission envelope before renderer edits. Add the remaining focused REDs in a separately
registered bounded test module:

1. all real route/profile visible DOM signatures converge after component skins/copy and the values
   of `data-page-archetype`/`data-arch-region` markers are removed;
2. declared archetype and live marker disagree;
3. the archetype/axis/route schema has extra or missing keys, duplicate roster/order entries, a
   missing renderer, a nonempty gap, or a renderer that fails to refuse the gap;
4. required anatomy/region order is absent from any one profile template or post-mount live DOM;
5. Carbon lacks the exact header/optional-SideNav/data anatomy ratified for that route;
6. Apple lacks its ratified leading/grouped anatomy;
7. Liquid lacks the functional/content split;
8. selector geometry after ratification, row layout, focus restoration, or independence drifts;
9. heading hierarchy moves right or horizontal;
10. content material, palette, contextual layers, or grouped-row ownership drift;
11. a visible button leaks an internal variant label, uses wrong context typography/geometry, emits an
    empty icon, or a noninteractive pipeline row inherits button-sized chrome;
12. a rendered visible component remains `covered-deferred`/gapped or a public row calls it `pass`.

Extend rendered facts with verdict-free observations for active archetype id, ordered visible-region
tree, landmark anatomy, heading coordinates/stacking, selector box/segments, content blur, contextual
layers, palette, component anatomy/state, grouped-row container ownership, and live duplicate IDs.
Facts and the coverage join include every reachable interaction state. The cross-profile divergence
predicate consumes all three profile bundles; a per-profile predicate cannot prove non-convergence.
Every affected route is tested at 1280 and 390.

Required independent mutants include: copy one renderer/profile DATA block to another; right-align a
section heading; enlarge the selector; stack selector segments; add a universal outer border; add
Liquid Glass to content; give grouped rows individual card chrome; remove a route's ratified Carbon
header/SideNav/table anatomy; remove Apple grouped/leading anatomy; leak an internal variant ID; emit
an empty icon; restore the unsupported universal Apple `50px`/`999px` button rule; retain a rendered
component gap; duplicate an order entry; insert bogus nonempty admission scope; change only marker
values while sharing one topology; and change vendor button geometry while asserting selector output
unchanged. Each mutant must fail the predicate that names its law. A probe that changes nothing is
vacuous.

### Skill enforcement

Update `skills/design-language-tdd` using the skill-creator rules. It must execute, not merely mention:

1. `bootstrap_red_ref` with `--expect`, complete route/profile/aspect scope, and a persisted closed
   observation+claim admission envelope;
2. source-catalog resolution and zero required archetype gaps;
3. page-archetype DATA/schema and renderer dispatch checks;
4. the full actual-route/profile/viewport/reachable-state rendered matrix;
5. literal occurrence provenance;
6. the named mutation suite;
7. Chrome screenshots and 390px overflow probes with real provenance sidecars;
8. CODE and ADVERSARIAL verdict parsing.

Forward-test the skill on a synthetic generic reskin. The test passes only when the workflow rejects
it before completion. Presence/keyword tests and the old claim that headless proof is deferred are
removed or replaced with executable assertions.

### Mechanical completion order

The earlier monolithic order is superseded by `Required bounded slice sequence` above. There is no
persisted admission envelope to preserve and no `make verify` target. Preserve the existing RED
bytes/output as audit history, close design, replace provisional assertions only RED-first, then
re-observe/persist the closed envelope and execute slices 1-10 with per-slice reviews.

### Design acceptance checklist

- No active profile has a deferred or gapped `page-archetype`.
- All 12 route/profile compositions have different live structural signatures where doctrine
  requires difference and carry the declared marker/anatomy.
- One live tree, one title, one selector, one selected option, and no duplicate live ID exist.
- All visible regions are in profile DATA and all literals have occurrence-scoped authority.
- Apple palette/content/grouping, Carbon route-specific shell/data anatomy, and Liquid functional/
  content separation match the slice-0 ratified matrix without overclaiming vendor scope.
- Dashboard hydration works before and after all theme transitions.
- Selector and heading regressions visible in the operator screenshots are mechanically rejected.
- Every affected route/profile has authentic 1280/390 evidence and zero horizontal overflow.
- The skill rejects a generic reskin and cannot report completion without the same evidence.
- Focused suite, full suite, structural gates, mutations, receipts, CODE review, and ADVERSARIAL review
  all approve without exclusions.

CANDIDATE-ARCHITECTURE-STATUS: design-revise

This candidate is not implementation-approved. The current numbered DESIGN must-fixes below and the
bounded slice-0 output must be approved before renderer mutation; the implementation owner may not
silently narrow them.

## Historical W3 dashboard evidence — nonbinding design history

This tail preserves the narrower dashboard audit that preceded the full-site adversarial pass. It is
evidence of why W3 was rejected, not a second implementation plan. Where it conflicts with the
current gate, bounded slice sequence, source-scope corrections, or reference manifest, the earlier
candidate language below is superseded. Only the manifest's closed aspect list and separately
ratified current laws can authorize implementation.

### Observed wrongness

W3 preserved DOM ownership but regressed the shipped dashboard. It changed the old subtle panel
edge (`hairline` mixed to 16% opacity) to the full profile hairline, applied that edge to every
section, split the dashboard title/intro away from its hero, and emitted a home breadcrumb above a
home navigation item. The user compared the two versions and explicitly selected the pre-W3
dashboard as the better reference.

The failure is procedural as well as visual. W3's own D-W3-LIT-1 record says the composition values
are `consistency-only`, `unratified`, and not vendor authority. A closed grammar made those values
stable, but stability was incorrectly treated as permission to ship them.

### Historical authority split, corrected to manifest scope

- Official Apple or Carbon sources govern only aspects those sources actually specify.
- The pre-W3 dashboard at Git revision `382ca96b` is the operator-approved frozen reference only for
  the manifest's seven aspects: `orientation`, `page-gutter`, `liquid-content-edge`,
  `apple-content-edge`, `selector-edge`, `group-edge`, and `row-divider`. It does **not** own selector
  size/anatomy, grouped-row topology, palette, content fill, or any other measured fact merely because
  that fact appears in a capture. The reference does not authorize its old Liquid Glass treatment on
  content cards because
  official Apple material guidance has higher precedence. A committed pack, not Git history,
  freezes the source bytes, deterministic data fixture, six page/theme/viewport captures,
  computed facts, producer/Chrome versions, operator approval, and evidence hashes.
- This reference does not become official Apple or Carbon doctrine. Its facts are
  `approved-reference` and `measurement-exact` against the frozen source/render.
- Accessibility, responsive containment, DOM ownership, and source precedence remain independent
  non-overridable baselines.

### Historical candidate laws (must be re-authorized by slice 0)

1. The home page has one visible H1 and one intro, both inside the hero. The pageshell may delegate
   orientation to a governed page emitter; an empty or self-referential breadcrumb row is forbidden.
2. The dashboard keeps the W2/W3 pageshell, webkit, closed prototype, and hydration ownership
   boundaries. No bespoke class debt returns.
3. Liquid Glass material stays on the functional/navigation layer. Dashboard content sections and
   grouped metric cards must have computed `backdrop-filter: none`. Their approved-reference
   container edge is measured separately from selector, group, and row separators; none may resolve
   to the raw full-strength Liquid Glass hairline.
4. Grouped metric rows retain one container and subtle dividers; the correction must not create a
   card per metric.
5. Carbon may remain on its official light canvas. Lightness is not the regression; unsourced
   generic chrome and hierarchy are.
6. Every accepted visual fact points to a scoped Mode A/B/C/D authority. `declared-unresolved`
   visible composition cannot produce a passing completion claim.
7. The theme selector is an owner-ratified persistent site-setting control, not falsely labeled an
   Apple segmented control or Carbon Content Switcher. It has one shared bounded renderer, exactly
   one instance per page, equal rendered segments, no checkmark, one selected state, an accessible
   label, radio-group semantics, arrow-key behavior, and profile-specific official color/focus roles.
8. Dashboard shell padding preserves the approved 20px desktop and 12px phone inline gutters.
   Block-start, inline, and block-end geometry are independent facts at 1280 and 390.
9. Every switchable page visibly identifies and changes its current theme; a persisted theme may
   not turn a proof page white without exposing the controlling selector and selected state.
10. Carbon content surfaces use official contextual roles where the ratified route mapping applies;
    exact border/shadow choices need a scoped clause. Apple Dark opacity/no-blur is a local Mode C/D
    target. These laws do not inherit the old dashboard's theme-independent panel recipe.
11. Public conformance rows name clause id, authority, source mode, and exactness. An unresolved or
    candidate clause cannot render as an unconditional vendor-conformance `pass`.

### Historical aspect table — gaps are explicit

| Aspect | Authority clause | Required rendered fact |
|---|---|---|
| Home orientation | `R-W3-VIS-2` + approved reference `orientation` | one H1/intro inside hero; zero self-breadcrumbs |
| Dashboard gutter | approved reference `page-gutter` | main inline inset 20px at 1280, 12px at 390 |
| Liquid content | Apple HIG Materials for “no Liquid Glass in content”; Mode C/D still needed for opacity/no-CSS-blur; reference owns only `liquid-content-edge` | no Liquid Glass; separately ratified material/fill; measured owned edge |
| Apple Dark content | Mode C/D still needed for opacity/palette; reference owns only `apple-content-edge` | separately ratified fill/blur/palette; measured owned edge |
| Carbon content | official contextual tokens plus a still-required route/layer/border/shadow clause | exact ratified contextual role per region |
| Grouped metrics | Apple Lists/Carbon Structured List for scoped anatomy; reference owns only `group-edge` and `row-divider` | topology from Mode B/D; measured owned edges/divider |
| Theme selector | owner-ratified `R-W3-VIS-1`; exact size still unresolved | one selector/page, equal boxes, one checked radio, no checkmark |
| Keyboard/focus | WAI-ARIA Radio Group for roving/arrows/Space; Mode D for Home/End/Enter | selected focus-visible ring and focus restoration after remount |
| Public claim | D2 source-backed construction law | visible clause id, authority, source mode, exactness; unresolved never says pass |

Carbon is not yet implementation-determinate. The White-theme tokens are pinned, but slice 0 must
map each route region to its contextual layer and separately authorize border/shadow/anatomy. A
universal outline or one blanket panel recipe remains forbidden.

### R-W3-VIS-1 - Site theme selector

The operator requires one persistent theme control across the governed site and explicitly rejected
W3's generic-button transplant/checkmark/oversized result in favor of the prior compact treatment.
The local control is therefore ratified as three equal-width radio segments with no selected icon.
Tab enters only the selected segment (`tabindex=0`; peers `-1`). Left/Up selects the previous
segment, Right/Down the next, Home the first, End the last, with wrap for arrows; focus moves with
selection and the choice persists immediately. Space/Enter select the focused segment. Keyboard
focus uses the active profile's sourced focus color and is visible only under `:focus-visible`.

### R-W3-VIS-2 - Home orientation

The home route integrates its one title, intro, global navigation, and selector in the primary hero.
It has no self-linking breadcrumb. This is an owner-ratified information-architecture rule grounded
by the approved pre-W3 reference, not an Apple or Carbon literal.

### Historical forks already folded into the current DESIGN gate

- **F1: revert W3 or repair its renderer.** Repair. Reverting would restore ungoverned DOM and the
  unsafe hydration grammar that W2/W3 correctly removed.
- **F2: retain universal breadcrumbs or delegate home orientation.** Delegate on home. Other pages
  may keep breadcrumbs where they provide real location context.
- **F3: invent new styling or reuse the selected reference.** Reuse only the frozen pre-W3
  composition facts an official source does not supersede. Apple material placement overrides the
  old content-card blur.
- **F4: put REDs in `test_dashboard_surface.py` or a bounded module.** Use the bounded
  `test_dashboard_visual_authority.py`; the existing structural test is already 633 lines.
- **F5: vendor component or site setting selector.** Use an owner-ratified site-setting control.
  Official vendor tokens can govern its paint/focus, but its persistent-theme semantics are local.

### Existing narrow dashboard artifacts

- `contracts/reference_packs/dashboard-pre-w3/manifest.json`: approval, per-aspect ownership,
  exclusions, hashes, state/viewport matrix, and exactness.
- `tests/fixtures/dashboard_reference.json`: bounded deterministic dashboard data.
- `assets/receipts/reference-packs/dashboard-pre-w3/`: frozen HTML/CSS, screenshots, computed facts,
  and provenance; tests never read `.git` or a live site.
- `scripts/quality/reference_pack/`: bounded codec/schema/producer modules reusing W4's verdict-free
  browser probe; no growth in `headless_receipts.py`.
- `scripts/rendering/webkit/theme_selector.py`: the bounded site-setting renderer and semantics.
- `tests/contracts/test_dashboard_visual_authority.py` and `test_reference_pack.py`: separate bounded
  RED/mutation surfaces. Every home and module cap lands in `repo_layout.json` and legacy mirrors.

### Historical proof intent

REDs fail on duplicate hero ownership, self-breadcrumbs, full-strength panel/selector/group/row
edges, content-layer blur, metric-per-card drift, Carbon layer/border/shadow drift, generic-button
selector anatomy, unequal segments, wrong selection/keyboard semantics, a missing non-index
selector, zero/duplicate/multiple selector selection, desktop/mobile gutter drift, unresolved
authority, and unratified literals. Public-claim REDs remove each visible provenance field and turn
one candidate/unresolved row into `pass`; every mutation must red.

Acceptance captures all four pages in all three themes at 1280 and 390 with deterministic dashboard
data. Facts cover resolved borders, opacity, backdrop filters, geometry, overflow, equal selector
widths, and selected state. Screenshot provenance/nonblank checks remain necessary but are no longer
sufficient. CODE and ADVERSARIAL approval follow the full matrix.

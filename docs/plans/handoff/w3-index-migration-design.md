# W3 - INDEX MIGRATION design (slice design doc; DESIGN gate input)

Admission observed 2026-07-13: `bootstrap_red_ref` returned `admit: true` for task
"migrate index onto governed pageshell and webkit components", RED
`tests/contracts/test_dashboard_surface.py`.

DESIGN gate round 1: **REVISE**. Review found that `webkit.dashboard` could become a renamed
page-sized bespoke renderer; title/intro parity conflicted with pageshell's fixed API; the proposed
DATA omitted non-pixel/runtime grammar; cloned templates needed an exact execution cover; duplicate
theme-root projections had no precedence law; and classless visible content was not closed. The
candidate law below folds every finding before implementation.

DESIGN gate round 2 found two stale checklist contradictions; both were removed. Final:
`DESIGN-VERDICT: APPROVE`.

## Observed surface

`scripts/pipeline/web_render.py` still owns a page-sized `_component_css`, seven bespoke fragment
renderers, copied icon paths, and hydration HTML templates. W2 can only admit its 49 static class
fingerprints and 21 runtime class tokens as frozen debt. The selected theme reaches index, but index
is not emitted by `render_page_shell`; its panels, switcher, and data rows therefore bypass the
same owner/emitter and token-only boundaries as the other three pages. The old panel shadow also
contains the uncited local literal `rgba(0,0,0,.65)`.

## Candidate law (RED: `tests/contracts/test_dashboard_surface.py`)

1. **Composition-only entry point.** `web_render.render_dashboard(default_theme)` validates and
   threads `default_theme`, obtains the governed nav, theme switcher, pageshell, dashboard surface,
   token bridge, and frozen hydration script, then assembles the document. It contains no local
   component CSS, icon catalog, fragment renderer, or runtime HTML template.
2. **Pageshell lineage.** Index contains the exact pageshell root/main/title/intro/orientation
   anatomy and `data-dom-owner="pageshell"`; W2's emitter-lineage mutation proves those bytes come
   from `render_page_shell`, not a copied class. `page_manifest.json` changes the landing content
   alias from retired `.wrap` to `.ps-main`.
3. **Narrow governed webkit owners and direct primitives.** `render_dashboard_surface()` owns
   layout/data-slot nodes as `webkit.dashboard`, but it may not reimplement a generic component.
   The two shipped grouped metric surfaces invoke an extended `render_card()` directly with closed
   structured row DATA, so `webkit.card`, `card_facts`, and all four deterministic card predicates
   govern the real scorecard/snapshot markup. `render_theme_switcher()` owns its segmented control
   as `webkit.switcher`; because a live switcher has multi-profile DOM/state behavior that fixed-
   profile `render_button()` does not model, W3 adds switcher-specific DATA, verdict-free FACTS, and
   predicates proving profile-derived geometry/anatomy, complete rest/hover/pressed/focus/disabled
   states, active-roster parity, and touch floor. Nav remains `webkit.nav`. There is no blanket
   `page.index` owner.
4. **Closed dashboard DATA and byte grammar.** `contracts/dashboard_surface.json` pins the ordered
   sections; all 23 DOM ids; every binding placement; every visible-copy field (including footer,
   empty states, accessibility labels, document title/description); layout modes; breakpoints;
   display caps; status mapping; intensity thresholds/opacities; weekday/hour/calendar geometry;
   language-colour authority/fallback; custom-property ranges; and every structural literal with a
   source/exactness label. Closed schema + independent source rosters reject extra/unused leaves.
   Exact independently pinned HTML/CSS/script grammar hashes close selector/property, grid/flex,
   opacity, percentage, font-weight, and arbitrary-custom-property drift that a pixel scan misses.
   Semantic row/order/id/binding/template assertions keep those hashes from being the only proof.
5. **No bespoke design literals.** The dashboard consumes only the pageshell declaration blocks,
   which are projected from `design_tokens.css_declarations(profile)`. The legacy
   `test_token_root_embedded_verbatim` assertion is replaced by exact declaration-map parity; index
   does not concatenate a second `emit_css_root()` block. Outside profile-derived component geometry,
   CSS carries no hex/rgb/hsl/named colour, no local shadow, and no off-contract literal.
   Local structural values are closed by the exact, context-sensitive D-W3-LIT-1 occurrence
   manifest; shared component literals remain owned by their profile/component contracts. The
   stray `rgba(0,0,0,.65)` and `_component_css()` die.
6. **Closed prototype-derived runtime structure.** Every dynamic shape exists once in an inert,
   owner-marked `<template>` emitted by the dashboard component. The contract and
   `dom_cover.json` carry the exact table `template id -> allowed target -> data-bounded maximum ->
   permitted text/attributes/data axes/custom properties and ranges`. Every `cloneNode` call must
   resolve a declared template/target pair; arbitrary `createElement`/`createElementNS` is banned.
   `_script()` may clone those templates, set only declared text/ARIA/title/`hidden`/safe `href`,
   set closed `data-level`/`data-status` axes, and write validated custom properties. It may not use `innerHTML`,
   `insertAdjacentHTML`, `outerHTML`, `document.write`, HTML-tag strings, `className`, `classList`,
   `setAttribute("class", ...)`, or create an element. W2's old free-form index runtime class debt
   becomes a stricter `prototype-derived` runtime cover (not erased); the independently pinned
   script remains a DOM mutator for W4's rendered count/computed-style closure.
7. **Content parity.** The migration preserves the focal contributions KPI, all existing public
   metric bindings, title/intro wording, section order, calendar/rhythm hidden-until-data behavior,
   status shape+label semantics, flagship/focus/raw snapshot surfaces, the 23 existing ids, and the
   two declared narrow scroll containers. Dynamic output remains text-safe and URL-safe.
8. **Debt resolution is historical.** Every immutable W2 index debt row stays in
   `dom_cover.json` with `resolved_count == baseline_count`; deleting history or changing its
   independent hash remains red. New exact owner signatures for pageshell/webkit nav/switcher/
   dashboard replace active debt. W3 may not make the baseline disappear.
9. **One declaration projection and explicit threading.** `design_tokens.css_declarations(profile)`
   becomes the sole ordered profile-to-CSS-var projection used by both `emit_css_root()` and
   pageshell `_profile_decls`; index includes only pageshell's blocks, never a second concatenated
   token root. Exact intersection/full-map parity is mutation-tested. `default_theme` is passed to
   pageshell, nav, switcher, dashboard/card fallback, and every scoped block; no fragment imports
   or reads `DEFAULT_THEME` directly.
10. **All visible bytes have an owner.** Pageshell gains validated optional `title_id`/`intro_id`
    parameters so the existing `hero-name`/`hero-tag` hydrate in the one real H1/intro; no duplicate
    hidden hero exists. Dashboard headings, links, footer, copy, template descendants, and inline
    attributes originate in the governed emitters from closed DATA. `web_render.py` emits document
    boilerplate only and reads document title/description from that DATA. Shared dashboard mapping
    is documented in all three active-language doctrine files, because the selected language
    changes the same surface.

## Render shape

`render_dashboard_surface()` returns `(html, css)` and is the dashboard layout/data-slot seam. Static
sections and prototypes are helpers inside that module, but only the declared top-level emitter may
mint `data-dom-owner="webkit.dashboard"`; helpers accept the marker or return data. Scorecard and
snapshot groups come from direct `render_card()` invocations with a typed `MetricRow` input, and the
dashboard concatenates their identical switchable component CSS once. `render_theme_switcher()`
remains in `rendering/webkit/components.py` and has its own adapter/predicates. `web_render.py` owns
document assembly, `DATA_URL`, language-colour JSON, and the frozen hydration program only.

## RED and mutation plan

The first RED lands with its registry homes and fails on the current bespoke index. After the
implementation, persistent negative vectors prove that each mutation reddens:

1. restore `.wrap`, `.panel`, `.switcher`, `.mgroup`, or another retired debt class;
2. add a dashboard class without `webkit.dashboard`, or alias the top-level renderer as an owner;
3. remove/reorder a section, id, binding, or template; add an undeclared one;
4. change a contract structural value without its independent/cited roster;
5. inject a raw colour, shadow, or off-contract pixel into dashboard CSS;
6. make `_script()` carry an HTML tag/class string or any banned DOM/class API;
7. add an off-enum status/intensity/data axis;
8. change `resolved_count` back below its W2 baseline or delete debt history;
9. ignore the `default_theme` argument or pin a non-selected profile in a fragment;
10. replace a Lucide geometry with a local copied icon path;
11. remove the hidden calendar/rhythm prototypes or the two scroll containers;
12. remove a direct webkit/pageshell emitter invocation and paste its returned markup.
13. add an undeclared clone target, exceed a data cap, set an off-enum data axis, write an
    undeclared custom property, or pass an unvalidated style value;
14. drift a non-pixel CSS decision (grid columns, flex direction, opacity, font weight, percentage)
    while leaving literal scans green;
15. make pageshell/design-token declarations disagree on any shared key, or let one fragment ignore
    a non-default `default_theme`;
16. hardcode visible copy/footer/attributes outside the closed dashboard contract.

Mutation proof is executable in the committed tests, not only described here: crafted CSS/JS and
contract mutations must each produce a non-empty error list, and the DOM cover's emitter nonce
probe remains binding on index.

## Open forks (decided here; critique welcome)

- **F1 - stamp old markup vs new component.** DECIDED new `webkit.dashboard` component. Stamping a
  top-level `page.index` owner would launder all W2 debt and is independently forbidden.
- **F2 - dynamic HTML vs prototypes.** DECIDED owner-marked inert templates + clone/update. Frozen
  string templates merely move the ungoverned DOM vocabulary into JavaScript.
- **F3 - duplicate card grammar vs extend the primitive.** DECIDED extend `render_card` with typed
  rows and a switchable emission mode, then invoke it directly for both shipped groups. Existing
  default calls and predicates remain stable; profile-scoped facts prove every active mode. A fixed
  liquid-glass card would not become Carbon/Apple, while a dashboard-local copy would bypass the
  component authority.
- **F4 - delete W2 debt rows vs resolve them.** DECIDED retain every row as immutable history and
  set `resolved_count` to its baseline.
- **F5 - expand W3 into the planned draggable board.** DECIDED no. W3 preserves content and closes
  governance; `docs/design/board.md` remains a later feature with its own interaction RED/receipts.
- **F6 - claim runtime closure now vs W4.** DECIDED no. W3 structurally prevents new runtime class
  vocabulary, but W4 still owns post-hydration DOM/computed-style facts and rendered predicates.
- **F7 - duplicate token roots vs one projection.** DECIDED one declaration map function consumed
  by pageshell and the legacy `emit_css_root` bridge; index ships pageshell's projection only.
- **F8 - duplicate hero for legacy ids vs pageshell API.** DECIDED validated optional title/intro
  ids on the actual pageshell nodes; exactly one H1 remains.

## Homes, receipts, and review

New homes land with the RED: `contracts/dashboard_surface.json`,
`scripts/rendering/webkit/dashboard.py`, and `tests/contracts/test_dashboard_surface.py` join
`repo_layout.json` and both legacy test registries in the same slice. `docs/design/pageshell.md`,
`docs/design/liquid-glass.md`, `docs/design/carbon.md`, and `docs/design/apple-dark.md` are updated
to point at the shared switchable surface. Regenerate `site/index.html`,
all index conformance/visual artifacts reached by its component output, and real Chrome index
receipts at 1280/390 plus all index theme/state facts. Full suite, explicit mutations,
`git diff --check`, and independent DESIGN/CODE/ADVERSARIAL approvals precede commit.

## Implementation record

Hydration-rendered output stays the explicit W4 handoff, but W3 admits only one frozen hydration
program byte sequence. Both the raw `_script()` template and its post-substitution inline program are
hash-pinned; lexical API checks remain explanatory diagnostics. Any whitespace, computed-property,
alias, or alternate DOM-write spelling is outside that singleton grammar and reddens before review.
Static text nodes are also closed by ordered owner/parent/text hashes that preserve boundary spaces and
non-breaking spaces; caller-injected text must reconcile to the direct emitter invocation just like DOM
elements. Screenshot readiness and pixels now come from one Chrome process/page session, with the
provenance sidecar's artifact hash acting as the fail-closed bundle commit marker.

### D-W3-LIT-1 - Dashboard literal gap

This slice does not claim operator ratification for agent-selected composition measurements. The
dashboard layout emitter is temporarily constrained to the following exact literal vocabulary as
the declared unresolved gap `W5-dashboard-literal-provenance`. The values are not interchangeable
between selectors or properties. The canonical occurrence manifest binds at-rule context + selector
+ property + value + multiplicity; its independent test pin makes a value swap, duplicate, deletion,
or media-query move observable. This is `consistency-only`, not design authority and not a claim
that Apple, Carbon, or another vendor published these page-composition measurements. W5 must either
ground each row in an official/measured source, obtain real owner ratification, or keep the aspect
visibly deferred; changing the manifest cannot silently manufacture approval.

`0`, `1`, `1%`, `1.6`, `100%`, `10px`, `11px`, `12px`, `13px`, `14px`, `16px`, `18%`,
`1fr`, `1px`, `2`, `20px`, `22px`, `24`, `24px`, `26px`, `28px`, `2px`, `3`, `30px`,
`38%`, `3px`, `44px`, `460px`, `480px`, `4px`, `50%`, `52px`, `560px`, `58%`, `600`,
`64px`, `6px`, `7`, `760px`, `78%`, `7px`, `8px`, `9px`.

The standard spacing/type subset follows `docs/DESIGN_SPEC.md` Part 0; the 44px interactive floor
follows `docs/design/liquid-glass.md`'s cited HIG layout target. Heatmap/calendar cell geometry,
chart percentages, measure bounds, and the two responsive breakpoints are local composition choices
remain unresolved because no vendor doctrine defines this repository dashboard's data geometry. Colour
continues to resolve only through profile tokens, runtime language-colour mappings, `currentColor`,
and transparent mixing. A future W5 clause migration may split these rows by official/measured
source without changing the emitted CSS or weakening this occurrence cover.

RED failed first on the missing dashboard contract/emitter boundary. GREEN replaces the bespoke
index renderer with pageshell composition and narrow webkit owners; the committed contract closes
visible copy, section/id/binding order, profile switcher facts, prototype units, clone budgets, write
sinks, and runtime policy. Persistent negative tests mutate source, CSS, script, contract, emitter
lineage, and debt history. W2's static/runtime index debt remains immutable resolved history.

The first hydrated localhost screenshot exposed a compositor-timing artifact that the old `file://`
capture had hidden behind a fetch error. The receipt producer now serves screenshots and mobile probes
from its existing hermetic HTTP server and flushes all compositor stages before draw. The accepted
1280 receipt contains hydrated GitHub facts and the 390 probe reports zero page overflow; provenance
records the real Chrome command, version, viewport, page hash, and capture origin.

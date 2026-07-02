# Page-shell — the site's own chrome is a governed, switchable design language

> Governs `scripts/rendering/pageshell/pageshell.py` (`render_page_shell`) and the `page-shell` aspect
> in every `contracts/design_profiles/<lang>.json`. Authority: `page_chrome`
> (`tests/contracts/test_page_shell.py`). `candidate_only`.

## §0 — Why this exists (the anti-vibe-code law)

The design system governs its **specimens** (button/chip/card/archetype). But the pages that *display*
those specimens — studio, showcase, settings — were hand-written dark CSS with ~15 raw hex colours each,
held in place by a byte-drift guard only. A design-system site whose own chrome is off-system is a
**pattern failure**: it "highlights everything" and reads as vibe-coded, exactly the AI tell the specimens
were built to avoid. The rule the owner set: **no part of the website is without the process.**

So the page **chrome IS a rendered instance of a design language**, switchable in real time, and every
switch is governed. `render_page_shell(profile, …)` builds the page background, header, breadcrumb, and
section panels entirely from that language's tokens + a documented IA scale — zero page-local palette.

## §1 — The honest gate: provenance + mutation, not merely "no hex"

Token-only is **necessary but not sufficient** — a value can be vibe-coded behind a token name
(`--accent: #7dcfff` routed everywhere). The gate has three parts:

1. **Token-only body.** After the declared `:root { … }` blocks are stripped, the host-chrome CSS carries
   **no raw hex and no bare design px** — every colour/space/size is a `var(--role)`. Only a `1px` hairline
   border width is allowed bare.
2. **Provenance.** The `:root` colour/radius/font vars equal `loader.resolve_tokens(profile)` **exactly**,
   and the IA-scale vars equal `SHELL_SCALE` — so a var can never smuggle an arbitrary literal.
3. **Mutation.** Moving a token moves the rendered chrome (proven by the mutation step: a hardcoded copy of
   a token value fails the token-only or provenance gate).

## §2 — The role tokens (per language, from the profile)

Every host-chrome colour references one of the profile's resolved role tokens
(`docs/design/<lang>.md` owns the values): `--backdrop` (the page ground), `--surface` /
`--surface-raised` (panels), `--ink-strong` / `--ink` / `--ink-dim` (title / body / secondary),
`--accent` (links + focus), `--hairline` (borders), `--status-success|warning|danger` (verdicts),
`--radius-panel` / `--radius-tile`, `--font-sans`. Cited: the same DTCG token blocks the specimens use.

## §3 — The shell IA scale (`SHELL_SCALE` + per-profile density)

The chrome's **layout rhythm** is shared so the proof surfaces read as one product; language
character still comes from each profile's colour, radius, font, and density band. Every literal below
has a cited source:

| Variable | Value | Source |
|---|---:|---|
| `--ps-measure-page` | `980px` | `docs/DESIGN_SPEC.md` Part 6 flags the 980px column as the de-facto web column; `scripts/pipeline/web_render.py` / `site/index.html` `.wrap` already ship `max-width: 980px`. |
| `--ps-gutter` | `clamp(20px, 4vw, 56px)` | The same index `.wrap` gutter pattern; it preserves the Part 6 column while giving mobile room. |
| `--ps-pad-tight` | `12px` | `docs/DESIGN_SPEC.md` Part 0 spacing set `{4,8,12,16,24,32}`. |
| `--ps-gap-tight` | `8px` | `docs/DESIGN_SPEC.md` Part 0 spacing set. |
| `--ps-gap` | `24px` | `docs/DESIGN_SPEC.md` Part 0 spacing set and section gap 24. |
| `--ps-gap-section` | `32px` | `docs/DESIGN_SPEC.md` Part 0 spacing set; the larger cross-section step. |
| `--ps-type-title` | `28px` | Apple HIG typography Title 1 tier, mapped to the shell H1. |
| `--ps-type-h2` | `20px` | Apple HIG typography Title 3 tier, mapped to section headings so h2 cannot collapse to body. |
| `--ps-type-body` | `15px` | Apple HIG body tier and `docs/DESIGN_SPEC.md` Part 0 body scale. |
| `--ps-type-sub` | `13px` | Apple HIG footnote tier and `docs/DESIGN_SPEC.md` Part 0 caption scale. |
| `--ps-measure` | `76ch` | Text measure for readable intro copy; derived from the same restrained-column law as Part 6. |

`--ps-pad` is deliberately **not** in `SHELL_SCALE`: `root_block()` emits it from
`design_tokens.density(profile)["panel_pad"]`. That pins padding to the language's cited density
band (`liquid-glass` medium 28, `carbon` compact 20, `apple-dark` airy 32) instead of a minted
constant.

## §4 — Emitted invariants (deterministic → pass/fail on the showcase)

- **`*-page-backdrop`** (`backdrop_is_token`) — the shell root paints `var(--backdrop)`.
- **`*-page-closed`** (`host_chrome_is_closed`) — the chrome CSS is a CLOSED, simple structure: exactly one
  `.ps-<lang>` root rule + descendant rules of it, **no @-rules / attribute / pseudo selectors / combinators**.
  This is the anti-adversarial-CSS discipline (the repo's closed-cover philosophy): specificity conflicts,
  `@media` overrides, and attribute-selector spoofs are *unconstructable*, so the other checks reason over a
  clean structure rather than trying to out-parse arbitrary CSS.
- **`*-page-tokenonly`** (`host_chrome_token_only`) — every declaration value is `var()` + structural
  keywords + a 1px hairline; a colour of ANY form (hex/rgb()/hsl()/color-mix()/named/currentColor) in ANY
  property reddens (prop-independent, no hand list).
- **`*-page-orient`** (`page_has_orientation`) — the page carries a title + a breadcrumb (a user can tell
  what the page is + get back). The shared glossary joins this in the explainability slice.
- **`*-layout-column`** (`page_has_content_column`, aspect `page-layout`) — all page content sits in
  one centered `.ps-main` column with `max-width: var(--ps-measure-page)` and auto margins; no
  full-bleed sprawl.
- **`*-type-tiered`** (`shell_type_ramp_tiered`, aspect `page-type-ramp`) — the shell exposes a real
  heading tier: title > h2 > body. Body-sized section headers redden.
- **`*-rhythm-density`** (`shell_density_from_profile`, aspect `page-spacing-rhythm`) — panel padding
  equals the profile's density band. A constant `--ps-pad` across languages reddens.

## §5 — Deferred / candidate (never fake-green; visual receipt required)

Visual hierarchy is good; a dark specimen does not camouflage into a dark chrome; responsive no-overlap;
contrast of chrome text over the actual ground. These are **judgment** aspects — a headless/visual receipt
decides them, per `docs/design/settings.md` §… (the live render is the final arbiter), never a static
string-match. They stay `candidate` until receipt-backed.

## §6 — Page archetypes (D-SHELL-2)

Every shipped page declares WHAT IT IS in `contracts/page_manifest.json`: intent + archetype
(CLOSED enum: landing / proof-report / control-plane / workbench) + the regions its archetype
requires — enforced fail-closed against the COMMITTED page bytes by
`tests/contracts/test_page_manifest.py` (site-scoped law; the roster's `page-archetype` aspect
stays deferred pointing there — a site fact surfaced per profile would fake per-language proof).
The SHELL-scoped grouping law is emitted per profile (`*-grouping-depth`,
`section_grouping_flat`): one chrome level, no chromed box inside a chromed box.
**Declared gap:** the PAGE-level nesting check (e.g. the showcase specimen stage, chromed inside a
chromed language panel today) lands with D-SHELL-3's stage shrink-wrap/recomposition.

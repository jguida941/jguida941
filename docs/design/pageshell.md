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

## §3 — The shell IA scale (`SHELL_SCALE`, shared)

The chrome's **rhythm** is consistent across languages so the site reads as one product; only colour +
radius vary per language. The IA scale is a small set of named constants, cited to
`docs/DESIGN_SPEC.md` Part 0 (4px spacing grid; the type ramp): spacing `--ps-pad` 24 · `--ps-pad-tight` 12 ·
`--ps-gap` 16 · `--ps-gap-tight` 8 (**all 4px multiples**, pinned by `test_page_shell`); type ramp
`--ps-type-title` 26 · `--ps-type-body` 15 · `--ps-type-sub` 13; measure `--ps-measure` 76ch. `[derived]` — the shell IA is this project's own scale,
not a third-party doc; per-language type ramps are a later slice (`type-ramp` aspect).

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

## §5 — Deferred / candidate (never fake-green; visual receipt required)

Visual hierarchy is good; a dark specimen does not camouflage into a dark chrome; responsive no-overlap;
contrast of chrome text over the actual ground. These are **judgment** aspects — a headless/visual receipt
decides them, per `docs/design/settings.md` §… (the live render is the final arbiter), never a static
string-match. They stay `candidate` until receipt-backed.

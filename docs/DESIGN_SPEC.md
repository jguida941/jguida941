# DESIGN_SPEC.md — Developer-Analytics Product

**Thesis:** "Power BI information architecture + Apple visual restraint." One analytics *contract*
(metrics, tiers, status semantics), two *projections*: (1) static GitHub README SVG cards, (2) a
GitHub Pages web dashboard. A serious analytics surface, not a decorative glass profile.

Each element below carries a **red-first testable invariant** (Part 3 `(e)`). Those invariants are the
contracts in `tests/test_design_contract.py` (+ IA/A11y/SVG/cross-projection suites). Sources: Part 6.

---

## Part 0 — Design tokens (single source of truth)

Both projections MUST draw every value from these tokens (operationalizes Power BI "report theme =
centralized style" + Apple "hierarchy via size/weight/whitespace"). No ad-hoc hex, no off-scale sizes.

**Type scale** (SVG user-units == CSS px):

| Token | Size | Weight | Use | Effective floor |
|---|---|---|---|---|
| `display` | 48–56 | 600 | PrimaryKpiCard value (the one big number) | always largest |
| `metric-lg` | 28–32 | 600 | Secondary metric values | ≥24 |
| `title` | 18–20 | 600 | Section/hero titles | ≥16 |
| `body` | 14–15 | 400/500 | Primary labels, row primary text | **≥14** |
| `caption` | 12–13 | 400 | Secondary labels, timestamps | **≥12** |
| `eyebrow` | 11–12 | 600 | Overlines (UPPERCASE +0.08em) | ≥11 |
| `chip` | 11–12 | 500 | Chip text | ≥11 |

Floors derive from GitHub's 16px Markdown base + the ~880px no-downscale column (Part 2): 12px is the
legibility floor, 14px for primary text.

**Color tiers** (neutral-forward, single accent; every *text* tier ≥4.5:1 on its surface — WCAG 1.4.3,
the ratio Power BI cites). Light-projection values track GitHub Primer (WCAG-tuned):

| Token | Hex (light) | On `#FFFFFF` | Role |
|---|---|---|---|
| `ink-1` | `#1F2328` | ~16:1 | Primary text / big numbers |
| `ink-2` | `#57606A` | ~5.6:1 | Secondary text |
| `ink-3` | `#6E7781` | ~4.6:1 | Tertiary text (floor for text) |
| `ink-disabled` | `#8B949E` | ~3.0:1 | Decorative/borders only — never text |
| `surface` | `#FFFFFF` | — | Card surface |
| `surface-subtle` | `#F6F8FA` | — | Section/inset fill |
| `hairline` | `#D0D7DE` | — | 1px borders/dividers |
| `accent` | `#0969DA` | ~4.6:1 | The single accent |

(Dark projection swaps the same *roles* to a dark ramp — see Part 5 + the open palette decision; the
token NAMES and contrast rules are projection-invariant.)

**Status palette** (each ships a text tone + tint; status is NEVER color alone — Power BI
color-independence):

| Status | Text tone | Tint bg | Redundant cue |
|---|---|---|---|
| success | `#1A7F37` | `#DAFBE1` | check icon + label |
| warning | `#9A6700` | `#FFF8C5` | triangle icon + label |
| danger | `#D1242F` | `#FFEBE9` | x/alert icon + label |
| neutral | `#57606A` | `#F6F8FA` | dot + label |

Because success(green)+danger(red) are semantically adjacent (a CVD-unsafe pair Power BI lists), both
MUST carry distinct icon *shapes*, not just hue.

**Spacing/grid:** 4px base. Gaps ∈ {4,8,12,16,24,32}. Card padding **16**, card radius **12**, chip
radius **6**, hairline **1px**. Section gap **24**. 12-col conceptual grid; README collapses to 1 col.

---

## Part 1 — Power BI IA invariants (cited)
1. **One-screen storytelling** — summary fits one viewport, no scroll; remove all but essential.
2. **Top-left reading path** — highest-level metric top-left; detail increases down/right.
3. **Size = emphasis** — exactly one dominant metric; its value is the largest text on the surface.
4. **Right visual for the purpose** — Card=one number; KPI=base+target+trend; Gauge=single value in
   min–max; Line/Area=trends over continuous time; Table=exact values; Pie/Donut/stacked=part-to-whole
   only; Slicer=on-canvas filtering.
5. **Circular charts = proportion, not comparison** — donut/gauge only for part-to-whole/single goal;
   ≤6 segments; comparisons use bars.
6. **Group into sections; align to the 4px grid; use whitespace.**
7. **Remove non-essential tiles** — no duplicate metric; cap tiles per section.
8. **Number formatting** — ≤4 numerals, scaled (k/M).
9. **Centralized theme** — all styling resolves from Part 0 tokens.
10. **Accessibility** — 4.5:1 text contrast; color-independence (text/icon, not hue alone); focus
    order matches reading order; alt text; never tooltip-only critical info.

## Part 2 — GitHub README SVG hard constraints (cited)
1. **Static — no scripts ever** (`<img>` SVG secure mode + Camo CSP `default-src 'none'`).
2. **No external resources**; forbid animation entirely (restraint + reliability) — frozen frame.
3. **Fonts: system stack or outline to `<path>`** (no external/`@font-face` fonts load).
4. **White canvas + theme bleed** — bake an explicit background rect; dual-theme via
   `<picture>`+`prefers-color-scheme` if needed.
5. **Downscaled into a ~880px column** — intrinsic width 400–880px; if rendered 2×, keep
   `font_size × min(1, 880/W) ≥ 12`.
6. **Valid XML + `viewBox`** (xmlns set; viewBox defines coordinate space).
7. **Sanitizer strips scripts/handlers/external refs/foreignObject** — primitive shapes + text/paths.
Practical floors: primary text ≥14, secondary ≥12, strokes ≥1.5px, explicit bg rect, viewBox present.

## Part 3 — Per-element spec (each has a red-first invariant `(e)`)

- **3.1 Hero band** — (e) top-most (y==0), exactly one band, ≤1 title, summary ≤ one viewport.
- **3.2 PrimaryKpiCard** — (e) `count==1`; value font == max of all value fonts; grid pos top-left;
  if KPI carries {base,target,trend}; ≥4.5:1; ≤4 numerals. **(The central missing piece today.)**
- **3.3 SecondaryMetricTile** — (e) `secondary.valueFont < primary.valueFont`; uniform label size.
- **3.4 MetricTile** — (e) one numeric value + non-empty label; ≤4 numerals; siblings share size.
- **3.5 SectionPanel** — (e) exactly one title; header ≤3 slots (eyebrow/title/right-label); uniform
  padding across sections.
- **3.6 StatusChip** — (e) text ≥4.5:1 on tint; status by icon-shape AND label (never hue alone);
  hue ∈ {success,warning,danger,neutral}; success≠danger icon shape.
- **3.7 DataQualityChip** — (e) includes a freshness/coverage word AND a quantity; never a bare dot.
- **3.8 TrendPanel** — (e) x is continuous time; ≤3 series; distinct marker shapes if >1; stroke
  ≥1.5px; axis labels ≥12; data labels off if they out-shout the line.
- **3.9 DonutGauge** — (e) ≤6 segments; sum==100% OR single value in [min,max]; not for comparing
  independent categories; every segment text-labeled.
- **3.10 LanguageBar** — (e) sum==100%; ≤6 visible (+Other); each segment name+value text; height ≥8.
- **3.11 ActivityRow** — (e) {actor, action, timestamp}; uniform row height/padding; aligned left
  edge; visible rows ≤ cap.
- **3.12 RepositoryRow** — (e) language by dot AND label; numeric columns share right edge; uniform
  row height; ≤4 numerals/cell.
- **3.13 EmptyState** — (e) rendered iff count==0; explanatory text line; **zero numeric values** (no
  fabricated metrics); no status color.
- **3.14 Icons** — (e) monochrome one family; stroke ≥1.5px; zero external font refs; meaning icons
  paired with label/`<title>`.
- **3.15 Typography** — (e) every text node maps to a scale token; no off-scale sizes; primary ≥14 /
  secondary ≥12; like-elements share size; ≤4 numerals.
- **3.16 Color** — (e) every text/bg ≥4.5:1; status never color-only; all colors ∈ token set; exactly
  one accent.
- **3.17 Spacing/grid** — (e) every x/y/padding/gap multiple of 4; one card padding; siblings one
  size; radii ∈ {6,12}.

## Part 4 — AI-look anti-patterns → professional fix
Glass/neon backgrounds → flat surface + 1px hairline, ≤1 subtle shadow · glowing big numbers → solid
`ink-1`, size+weight emphasis · rainbow per-metric hues → neutral ramp + one accent (color only for
status) · neon pills / color-only dots → 6px tinted chip, icon+label, ≥4.5:1 · emoji/mixed icons → one
monochrome `<path>` family · donut-for-everything → part-to-whole/goal only, bars for comparison ·
heavy shadows → hairlines · centered no-reading-path → top-left primary, left-aligned · lorem when
empty → real EmptyState, zero fake numbers · animated README SVG → frozen frame · tiny text → 14/12
floors · dashboard soup → one-screen, cap per section · bubbly corners → cards 12 / chips 6 · external
font in SVG → system stack/outline.

## Part 5 — README-SVG projection vs Web projection (same contract, two surfaces)
Same metrics, same primary/secondary tiers, same status semantics, same tokens. Differ only in
density, interactivity, responsiveness — never in *what* is primary or *what* a status means.

| Dimension | README-SVG | Web |
|---|---|---|
| Interactivity | none (static image) | filters/sort/drill; hover (never for critical info) |
| Animation | forbidden | restrained motion ok |
| Data | baked at render (times frozen) | live; relative times update |
| Width/layout | fixed 400–880px, 1 col | responsive 12-col |
| Fonts | system stack / outlined | one web font ok |
| Density | curated subset (hero + KPI + 2–4 secondary + 1 trend + 1 breakdown) | full sections + tables |
| Detail | overview only | overview → drill tables |

**Cross-projection invariants (both):** (1) tier(metric) identical; (2) status semantics identical;
(3) token parity; (4) same focal metric, top-left, largest; (5) color-independence + 4.5:1; (6) README
is a *subset* of web, never a different story.

## Part 6 — Sources (verified)
Power BI: dashboards-design-tips, visualizations-overview, visualization-kpi/-card/-radial-gauge/
-pie-donut-chart, line-chart, visualization-tables, visualization-slicers, desktop-accessibility-
creating-reports, desktop-report-themes, desktop-gridlines-snap-to-grid (learn.microsoft.com). GitHub
SVG: W3C SVG2 conform.html + SVG_Security wiki, Mozilla bug 628747, GitHub about-anonymized-urls +
atmos/camo + github/markup#289 + #1160, sindresorhus/github-markdown-css, github.blog dark/light
`<picture>`, MDN viewBox/preserveAspectRatio. **Flagged (derived, not officially published):** exact
sanitizer allowlist; inline-CSS-animation reliability; a published min font-size (12/14 derived from
16px base + ~880px column); the 980px column (de-facto replica — treat ~880–890px as safe).

## Notes — turning invariants into test suites
- **IA suite**: focal-metric uniqueness/position, `secondary<primary` font size, one-screen/no-scroll,
  section-header arity, tile caps, numeral ≤4.
- **A11y suite**: 4.5:1 on every text/bg, color-independence, focus/tab order (web), alt text, floors.
- **SVG-projection suite**: valid XML + viewBox, explicit bg rect, width 400–880, no script/on*/external
  refs/fonts, stroke ≥1.5, effective font ≥12/14, token-only colors.
- **Cross-projection suite**: tier parity, status-semantics parity, token parity, README ⊆ web.

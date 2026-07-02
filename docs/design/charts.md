# Charts — the governed chart language (P5-BOARD B-0)

A chart is DATA + a build-time SVG render + invariants — never a client-drawn artifact. Multi-view
panels pre-render EVERY view into the committed bytes; a frozen lookup script only toggles
visibility, so every reachable view is drift-guarded and conformant.

## §1 Doctrine sources
1. IBM Carbon Data Visualization — https://carbondesignsystem.com/data-visualization/getting-started/ —
   categorical palettes are ORDERED and finite; group beyond the cap into "Other"; legends label
   every encoded series.
2. Apple HIG Charts — https://developer.apple.com/design/human-interface-guidelines/charts —
   charts carry axis context, avoid decoration that distorts data ("depth" styling must never
   change perceived values).
3. Repo laws inherited: token-only colour (the no-hex guard, test_web_dashboard :111; the ONLY
   palette escapes are `emit_css_root` + `LANG_COLORS`); 11px legibility floor (THEME_IA law);
   status-by-shape-not-hue (test_web_dashboard :73).

## §2 The chart law
1. Palette: series colours come from the language's tokens (`accent`, `status-*`, and the
   LANG_COLORS categorical map for language series) — a raw hex in chart CSS/SVG reddens.
2. Segment cap: at most 6 categorical segments; the tail groups into "Other" (§1.1).
3. Anatomy: every chart carries a title, an axis or scale context, and a legend when >1 series;
   every text glyph ≥11px.
4. Multi-view law: a chart panel declares a CLOSED view set (e.g. `bar | line | depth`); ALL views
   are rendered at build time into the page; the switch (frozen lookup JS, studio pattern) toggles
   `hidden` only. The `depth` view is HONEST decoration: a CSS `perspective`/`rotateX` presentation
   transform of the same flat geometry — values, axes and bar lengths are identical to the flat
   view (§1.2); it must never re-scale data.
5. Wave-1 charts (data already in profile_snapshot.json — zero new collection):
   - `cadence` — engineering.weekly_cadence (12 ints) — views bar | line | depth.
   - `repo-matrix` — repo_language_matrix (stars by repo, ci markers by SHAPE) — views bars | dots.
   - `system-growth` — invariants/receipts per aspect from the conformance receipts — views bar.
6. Hydration: chart SVGs are BUILD-TIME artifacts (deterministic bytes under the drift guard);
   only textual counters may hydrate client-side via existing data-bind conventions.

## §3 Emitted invariants (roster `charts` + `component-chart` flip)
- `*-chart-palette` (`categorical_palette`): every fill/stroke in a rendered chart resolves to a
  token var or LANG_COLORS entry (fail-closed scan of the chart SVG/CSS).
- `*-chart-cap` (`chart_segment_cap`): ≤6 categorical segments + "Other" grouping observed.
- `*-chart-anatomy` (`chart_anatomy`): title + axis/scale + (legend iff >1 series) + ≥11px text.
- `*-chart-views` (`chart_views_closed`): rendered views == the declared closed set, each view
  present in committed bytes, exactly one visible by default.

# Liquid Glass — design doctrine (Apple HIG, cited)

> Default design language for the Builder Scorecard dashboard: **Apple frosted glass
> (Liquid Glass) + Tokyo Night palette**. IA is `scripts/core/config.py` /
> `scripts/rendering/design_tokens.py`. This doc records the **cited Apple values** that
> govern how a *multi-metric readout* (the Builder Scorecard KPI cluster and the Raw-Data
> Snapshot cluster) is composed. Quotes/typography carry the `developer.apple.com` URL they
> came from. Numeric geometry that is a **UIKit/empirical convention** (not published as a
> literal at the cited URL) is marked **[derived]** — those drive thresholds, not HIG literals.

## 0. The gap this closes

Our design invariants measured **tokens** (`panel_pad >= 24` ⇒ "airy"). A single number floating
in a tall rounded card *passes* the padding token while being ~70% dead space — the AI tell the
owner flagged ("huge blocks around stuff … Apple designers and pros don't do this"). Tokens can't
catch it: the failure is a **pattern** failure (content-to-chrome + grouped composition), not
padding magnitude. This doc grounds a **pattern invariant** (`test_design_character.
test_metric_readout_is_grouped_not_giant_boxes`).

## 1. Grouped-list anatomy — the canonical Apple many-metrics readout

Apple presents N small metrics as **ONE rounded inset-grouped container of N compact rows**, not
one card per number (Settings, Battery, Health "Show All Data"). The row is the UIKit **"Value 1"**
cell: a leading label + a right-aligned trailing value on one line.

| Property | Value | Source |
|---|---|---|
| Group related items into one area via separator lines / background shapes | "Group related items… use negative space, background shapes, colors, materials, or separator lines to show when elements are related and to separate information into distinct areas." | https://developer.apple.com/design/human-interface-guidelines/layout |
| Grouped style separates groups with headers/footers/space | "the grouped style uses headers, footers, and additional space to separate groups of data" | https://developer.apple.com/design/human-interface-guidelines/lists-and-tables |
| Row = "Value 1" cell (label + trailing value, lighter font, one line) | UIKit "Value 1": left-aligned title + right-aligned subtitle in a lighter font on the same line | https://developer.apple.com/design/human-interface-guidelines/lists-and-tables |
| Inset-grouped = single rounded container around the rows | `.insetGrouped` — "inset with rounded corners", continuous background around the rows | https://developer.apple.com/documentation/uikit/uitableviewstyle/uitableviewstyleinsetgrouped |
| Standard single-line row height | **44pt** **[derived: this URL publishes 44pt as the comfortable touch target, used here as the row height]** | https://developer.apple.com/design/human-interface-guidelines/layout |
| Two-line (label + caption) row | **~60pt [derived]** | https://developer.apple.com/design/human-interface-guidelines/lists-and-tables |
| Row content inset (leading/trailing) | **16pt** iPhone / 20pt iPad (8pt grid) | https://developer.apple.com/design/human-interface-guidelines/layout |
| Separator | **1pt hairline**, leading inset **16pt** | https://developer.apple.com/documentation/uikit/uitableview/separatorinset |
| Container corner radius | **~10pt [derived: Settings.app/`.insetGrouped`]** | https://developer.apple.com/documentation/uikit/uitableviewstyle/uitableviewstyleinsetgrouped |

**Rule:** the whole block shares **ONE** background/border/radius — the *container*. The rows inside
carry none; they are divided by **hairlines, not gaps between cards**. Ten metrics = one surface of
ten rows, not ten cards.

## 2. Content density (content fills the surface; space lives BETWEEN groups)

Density is the **ratio of inked content to surface area**, not padding magnitude.

| Principle | Value | Source |
|---|---|---|
| Give essential info space, don't crowd it | "Make essential information easy to find by giving it sufficient space… don't obscure it by crowding it with nonessential details." | https://developer.apple.com/design/human-interface-guidelines/layout |
| Content fills the screen/window | "Extend content to fill the screen or window…" | https://developer.apple.com/design/human-interface-guidelines/layout |
| Make the data the focus | summary → detail; make the data the focus | https://developer.apple.com/design/human-interface-guidelines/charting-data |

The 16–20pt margins and ~32pt **[derived]** section gaps frame a **dense** block — breathing room
lives AROUND/BETWEEN groups, never as padding wrapped around a single floating number. Target ink
ratio **≥ ~0.30 [derived proxy]**.

## 3. Type carries hierarchy → no per-metric box is needed

| Style | Size / leading / weight | Source |
|---|---|---|
| Title 3 | 20pt / 25pt | https://developer.apple.com/design/human-interface-guidelines/typography |
| Headline (metric LABEL) | 17pt / 22pt **Semibold** | https://developer.apple.com/design/human-interface-guidelines/typography |
| Body (metric VALUE) | 17pt / 22pt Regular | https://developer.apple.com/design/human-interface-guidelines/typography |
| Footnote (units/secondary) | 13pt / 18pt | https://developer.apple.com/design/human-interface-guidelines/typography |
| Caption 2 (legible floor) | 11pt / 13pt | https://developer.apple.com/design/human-interface-guidelines/typography |
| Hierarchy via weight/size/color | "Adjust font weight, size, and color… to emphasize important information and help people visualize hierarchy." | https://developer.apple.com/design/human-interface-guidelines/typography |

A Semibold value next to a secondary-color label + a 1pt hairline does ALL the separating work the
AI layout wrongly delegates to a bordered box.

## 4. Materials — Liquid Glass is the floating layer, used sparingly

| Rule | Quote | Source |
|---|---|---|
| Don't push material into the content layer | "Don't use Liquid Glass in the content layer." | https://developer.apple.com/design/human-interface-guidelines/materials |
| Use it sparingly | "Use Liquid Glass effects sparingly…" | https://developer.apple.com/design/human-interface-guidelines/materials |

⇒ `backdrop-filter: blur()` belongs on the **group container**, not replicated per row.

## 5. The anti-pattern (one metric per oversized card)

Inverts content-to-chrome, multiplies containers instead of grouping, re-pays chrome per number,
and (when frosted per tile) pushes material into the content layer. **The measurable, deterministic
tell:** a per-metric element that *independently* carries chrome (border / border-radius /
background). Apple grouped ⇒ only the container is chromed; anti-pattern ⇒ every metric is.

## 6. Mapping to THIS repo (the real one)

The dashboard is **generated** by `scripts/pipeline/web_render.py::render_dashboard()` into the
committed `site/index.html` (drift-guarded by `tests/contracts/test_web_dashboard.py`). The CSS is
emitted by `_component_css`. The current readout clusters use `.tiles` (grid) of `.tile` cards;
`.tile` independently carries `background` + `border` + `border-radius` (`web_render.py` ~lines
101–104) — the chrome that makes each metric its own box.

| Doctrine concept | Real artifact |
|---|---|
| KPI readout (6 scalar metrics) | the scorecard `.tiles` → `.tile` × 6 |
| Raw-Data Snapshot readout | the snapshot `.tiles` → `.tile` × N |
| Per-metric chrome (the tell) | `.tile { background; border:1px; border-radius }` |
| Target | one chromed `.mgroup` container of bare hairline-divided `.mrow` Value-1 rows |

The CI-coverage **ring** and the **hero** are single charts/headers (HIG charting-data) and are
**out of scope** — the grouped-readout rule applies only to clusters of ≥3 sibling scalar metrics.

## 7. The deterministic gate (browserless) vs the judgment (visual receipt)

Honest split — this repo's test suite has no headless browser, so (the deterministic gate
`test_design_character.test_metric_readout_is_grouped_not_giant_boxes` is **forthcoming** — it lands
RED-first WITH the web_render readout refactor, not ahead of it):
- **DETERMINISTIC (red-now/green-after):** the STRUCTURAL composition —
  per-metric rows carry **no** independent border/border-radius/background; the cluster is ONE
  chromed `.mgroup` container; adjacent rows are divided by a 1px hairline; rows are inline
  label+value (Value-1). This is **column-independent**, so it closes both codex escapes (a 2-up
  grid of chromed tiles fails; a short chromed dead-space box fails) and cannot be satisfied by
  padding tricks (re-adding per-row chrome re-fires RED — the mutation proof).
- **JUDGMENT (review anchor + before/after headless screenshot receipt, never a fake RED):** the
  geometric ink-fill / "reads dense like Settings/Health, not a template." Rendered line-box
  heights need a real layout engine, so that residue is proven by the visual receipt, not asserted
  as a deterministic number we cannot compute in the suite.

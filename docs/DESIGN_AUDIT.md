# DESIGN_AUDIT.md

Audit ahead of the design-system refactor: from ad-hoc per-card styling to a shared
**design-token + reusable-component** system (Apple HIG restraint × Power BI information
architecture) feeding **two projections** of one analytics contract — README SVG cards
(`scripts/rendering/`) and the web dashboard (`site/index.html`).

This is the *evidence*. The binding artifacts are the **red-first contracts** in
`tests/test_design_contract.py` (+ siblings): each finding below is encoded as a failing test,
driven green by the refactor, and kept as a permanent guard. RED→GREEN proofs live in
`docs/receipts/`.

## 1. What the current design does well
- One **centralized glass surface system** (`glass_kit.glass_defs/glass_panel/glass_tile`) — not 13
  hand-rolled backgrounds. Camo/GitHub-safe by construction and **tested** (`test_card_contracts.py`:
  valid XML, viewBox, no `<script>`/`<foreignObject>`/`rgba()`, geometry inside the frame, one title).
- The **de-AI passes already landed**: no per-tile accent stripe, chips are fill-OR-label (no outline),
  one calm ribbon instead of the tri-color underline, neutral icons on the scorecard.
- **Self-enforcing structure** (the new `scripts/organization/` layout guard) and **honest data**
  (no bot/self/fabricated rows; private repos named but never leaking commit text; coarse token mode).

## 2. Why it still reads AI-generated
The unifying tell: **almost every card is a flat grid of equal-weight metric tiles with a colored
icon, under a tiny all-caps eyebrow, over a gradient ribbon.** That's the "dashboard template" look.
- **No hierarchy / no `PrimaryKpiCard`.** `generate_snapshot_panel.py` renders 11 equal-weight tiles
  (value font picked by *string length*, not importance); `generate_builder_scorecard.py:117`
  hardcodes one size (29) for all 8; streak "hero" differs only by color, not scale.
- **Decorative multi-color icons** (techie look): BLUE/CYAN metric icons in `generate_metrics_general`
  and `generate_snapshot_panel`; rainbow accents in `generate_badges`.
- **Eyebrow tiny-all-caps everywhere** (~16 call sites) and **gradient ribbons on nearly every card**
  (~10) — repeated so often they stop being accents. The web mirrors this (gradient bar on every
  `.section-head`, colored left bar on every `.metric-card`).
- **Inconsistent card titles** (16/17/18/20/33px) — no shared "card title", so nothing is the hero.

## 3. Patterns that violate the Power-BI-IA × Apple direction
Equal-weight metrics (no KPI dominance) · decorative/per-metric color · one-off colors (~11 raw hex in
`rendering/` + 23 hex + 57 `rgba()` in `index.html`) · ~12 distinct corner radii with no scale ·
two unsynchronized shadow languages (SVG vs CSS) · ~24 font sizes (8.5→42) with **no type scale**.

## 4. What should become reusable components
Each is re-implemented ad hoc today; promote to a shared kit and delete the copies:
`MetricTile` (5 copies: `_stat_tile` in badges/metrics_general/contribution_panel, `_render_tile` in
scorecard, inline in snapshot_panel) · **`PrimaryKpiCard` (missing — the central gap)** · `SectionPanel`
header (~12 copies) · `StatusChip` (primitive exists; status vocab split SVG vs web) · `TrendPanel`
(3 sparkline impls incl. the browser one) · `LanguageBar` (SVG bar vs web list) · `ActivityRow`/
`RepositoryRow` (~4) · `EmptyState` (~8) · `ProgressRing`/`ProgressBar` (SVG vs CSS conic).

## 5. Assumptions that need proof from the code (→ red contracts)
| Assumption | Tested today? | Contract to add (RED first) |
|---|---|---|
| Every SVG has a viewBox / one title / inside frame / no banned tags | ✅ | keep (`test_card_contracts`) |
| **No raw color literals outside tokens** | ❌ | `test_design_contract.DesignTokenContract` (RED now) |
| **No sub-legibility font size** | ❌ | `test_design_contract.FontLegibilityContract` (RED now) |
| **Primary KPI larger than secondary** | ❌ | hierarchy contract (RED) |
| **SVG↔web token parity** | ❌ | parity contract (RED) |
| **Metric defs single-source** (labels drift: web "Releases (Recent)" vs contract "Releases (30d)") | ❌ | metric-parity contract (RED) |
| **Every metric None→"n/a"** in both projections (web coerces missing→"0") | ❌ | empty-state parity contract (RED) |
| text-width / blob overflow | partial | extend `_right_edge` |

## 6. Token reality
Exist (`scripts/core/config.py`): palette (13), glass/elevation pairs, 4 gradient pairs, `LANG_COLORS`,
`SVG_WIDTH`, fonts. **Missing entirely:** a type scale, a spacing scale, a radius scale, elevation tiers.
Duplications to collapse: the palette is defined **twice** (config.py ↔ `index.html :root`); the metric
definitions are re-typed in JS (`defaultScorecardMeta`/`defaultSnapshotCards`, with label drift);
dead legacy `card_theme.card_bg`/`title_accent` (the old tri-color underline) remain — delete.

## 7. Direction
Single highest-leverage move: one `MetricTile`/`PrimaryKpiCard`/`SectionPanel`/`StatusChip` kit + a
single metric-definition source consumed by **both** projections — deletes 5 tile + ~12 header + the JS
metric duplication at once, and makes Power-BI hierarchy (one hero KPI, grouped supporting metrics)
expressible. Each element is fixed via the owner's loop: *cite DESIGN_SPEC rule → RED contract →
implement → receipt*.

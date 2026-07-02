# P5-BOARD B-0 design record — laws, REDs, aspects, gate

Doctrine authored (cited): docs/design/motion.md, board.md, charts.md (in-repo, this commit).
Approved plan: ~/.claude/plans/181-*.md (operator-approved). Gate mode: codex OUT until 20:25
(probed); Claude agent budget constrained → B-0 gate = Fable self-review vs the attack list
below, RECORDED as interim; the retroactive codex batch covers B-0..B-3 designs + diffs.

## Aspect specs (4 roster flips)
- motion → emitted: predicates motion_tokens_cited (emitted vars == THEME_IA motion block, band
  70-700ms) + motion_token_only (no literal durations outside emission + declared-exceptions list).
  Facts from emit_css_root output + page CSS scan. ×3 profiles.
- component-nav → emitted: nav_facts (per-language nav anatomy: container, ordered links incl.
  active-page marker, token-only) + render_nav in webkit/components.py. ×3 profiles.
- charts + component-chart → emitted (B-3): categorical_palette, chart_segment_cap, chart_anatomy,
  chart_views_closed per charts.md §3. ×3 profiles.

## Manifest deltas
index.required_regions += "site-nav" (alias ".site-nav", replacing surface-links/.nav-links),
"board" (alias "[data-panel]"), later "charts" ("[data-chart]"); showcase/settings/studio +=
"site-nav". board-panels closed id set lives in manifest page entry (new key board_panels[]).

## New receipt kind
chrome-headless-board-probe: headless page + injected driver dispatches pointer events dragging
panel A onto panel B; after settle asserts (a) zero pairwise overlap of [data-panel] rects,
(b) localStorage dash-layout@v1 parses + reapplying it reproduces identical rects (round-trip).
Provenance sidecar + page_sha256 pin like all MF1 receipts. Producer extends headless_receipts.py.

## RED bank (observed-failing before each build)
B-1: literal-duration scan reddens on current .18s/2.4s; roster flip reddens profiles missing
motion invariants (SF-4); nav region absent; nav_facts fail-closed on no-nav render.
B-2: BOARD_DEFAULT absent; parity test red; frozen-script pin red; collision parity vectors red
(Python twin vs pinned table); manifest board region red; board-probe receipt missing.
B-3: chart invariants red per profile; views-closed red; palette scan red on any hex.

## Q-list (self-ruled, recorded for retro codex attack)
Q1 pulse 2.4s: keep as DECLARED exception in B-1 (retire/re-ground at B-1 gate) — ruled KEEP+list.
Q2 board rows unit: auto rows from content (h = row-span of measured units) vs fixed row height —
ruled FIXED row unit (grid-auto-rows token-derived) for deterministic collision math.
Q3 nav on index in liquid-glass while other pages house apple-dark: per plan (freeze governs
content not chrome primitives) — ruled per-page language: nav renders in the PAGE'S language.
Q4 charts per-language render: charts live on index (liquid-glass) only in wave 1; invariants
still ×3 profiles via canonical render_chart(profile,...) specimens (like buttons) — ruled YES.

## Self-review attack list (executed against the docs above)
- vacuity: every new predicate has a constructable negative (listed in RED bank) ✓
- placeholder risk: charts/component-chart flip ONLY in B-3 commit (not before their predicates) ✓
- no-hex/inline-only/44px/reduced-motion guards named and preserved per slice ✓
- WCAG 2.5.7 keyboard alternative is in board law §2.6 (not optional) ✓
- depth view honesty clause (charts.md §2.4) prevents fake-3D data distortion ✓
- declared exception (pulse) is time-boxed with owner gate ✓
DESIGN-VERDICT (interim, Fable self-review): APPROVE — queued for retroactive codex.

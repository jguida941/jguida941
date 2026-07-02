# Board — the free-form dashboard grid (P5-BOARD B-0)

The landing page's panels form a user-arrangeable BOARD: drag to move, resize on a snap grid,
persisted locally — while every reachable arrangement stays a valid instance of the layout law.

## §1 Doctrine sources
1. WCAG 2.5.7 Dragging Movements — https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements —
   any drag interaction MUST have a single-pointer/keyboard alternative → the keyboard move/resize
   mode is a law, not a nicety.
2. ARIA Authoring Practices (drag affordances, aria-grabbed lineage) —
   https://www.w3.org/WAI/ARIA/apg/ — handles are buttons with names; state changes announced.
3. Touch targets ≥44px — repo law (test_web_dashboard :99) + HIG
   https://developer.apple.com/design/human-interface-guidelines/layout .
4. Grid discipline — DESIGN_SPEC Part 0 (4px grid) + the existing `--gap-grid`/`--pad-*` tokens:
   the board's cells derive from the SAME spacing tokens (no new minted px).

## §2 The board law
1. Geometry: a 12-column snap grid inside `.wrap`; a panel occupies `{c,r,w,h}` (col 1-12, row ≥1,
   w 1-12, h ≥1 row units); rows auto-size from content rhythm.
2. CLOSED panel set: every board panel carries `data-panel="<id>"`; the id set is pinned (manifest
   `board-panels`) — an unknown id is unconstructable.
3. Collision: **overlap is unconstructable** — placement resolves by deterministic push-down
   (fixed scan order: rows then columns). The same frozen algorithm runs in JS; its Python twin is
   the decider used by tests (table-driven parity vectors pinned in the suite).
4. Persistence: `localStorage["dash-layout@v1"]` = `{schema:"v1", panels:{id:{c,r,w,h}}}`;
   unknown schema/id → ignored wholesale (fall back to default; never partial-apply).
5. Baseline: no-JS / no-saved-state renders the COMMITTED default layout — Python emits
   `window.BOARD_DEFAULT` and the DOM order/spans must equal it (parity invariant).
6. Affordances: a visible drag handle per panel (≥44px hit area, named button); keyboard mode
   (handle focus + arrows move, Shift+arrows resize, Esc cancels, Enter commits — §1.1/§1.2);
   a reset-layout control restores BOARD_DEFAULT and clears storage.
7. Motion: drag feedback/reorder transitions use ONLY `var(--motion-*)`/`var(--ease-*)`
   (docs/design/motion.md); reduced-motion collapses them.
8. The script is FROZEN + verdict-free (studio law): embedded verbatim, reads BOARD_DEFAULT +
   pointer/keyboard events, writes grid-position vars + localStorage. It never computes a design
   verdict, never restyles beyond `{c,r,w,h}` placement.

## §3 Receipts
Deterministic half: frozen-script pin, schema pin, default-layout parity, banned-token scan.
Judgment/runtime half: `chrome-headless-board-probe` — a headless run drags one panel onto
another, asserts zero overlapping panel rects after settle AND that the layout round-trips
through localStorage; committed with provenance + page_sha256 like every MF1 receipt.

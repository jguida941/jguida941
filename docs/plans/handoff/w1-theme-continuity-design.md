# W1 — THEME CONTINUITY design (slice design doc; DESIGN gate input)

Admission observed 2026-07-13: `bootstrap_red_ref` returned `admit: true` for task
"implement theme continuity law", RED `tests/contracts/test_theme_continuity.py`.

DESIGN gate round 1: **REVISE**. The review found that token overrides alone would leave the
profile-specific nav anatomy pinned to Apple, ordinary MF1 captures would not exercise a stored
non-house choice, and `root_block` currently invents fallback values. The candidate law and proof
plan below fold those must-fixes before any RED/build work.

DESIGN gate round 2 (after all folds): `DESIGN-VERDICT: APPROVE`.

CODE/ADVERSARIAL round 1: **REVISE**. The finished-diff reviews found four proof escapes: plain nav
links lost the choice when storage was denied; browser evidence exercised only valid stored state;
an invisible Carbon underline or arbitrary scrolling wrapper could pass; and proof pages pinned
native `color-scheme: dark` under Carbon. Folded RED-first by governed query propagation, six
state-machine browser vectors, resolved nav/color-scheme facts, and a closed scroll-container set.

CODE/ADVERSARIAL round 2: **REVISE**. Further mutation attacks found zero-box navigation could
retain plausible computed colors, scenario outputs were not pinned to their inputs/page hashes,
breadcrumbs did not propagate, and scroll class names could be laundered onto a broad wrapper.
Folded RED-first with ancestor/box/intersection facts, exact input + current-page hash assertions,
a denied-storage breadcrumb journey, and page/parent-bound scroll-container rules that retain
contained-offender identities.

CODE/ADVERSARIAL round 3 (finished diff): `VERDICT: approve` and
`ADVERSARIAL-VERDICT: approve`. Full suite: 345 tests green.

## Operator decision being implemented (D1, ratified 2026-07-13)

**One governed site.** The 3-theme switcher stays on `index.html` (the ONE canonical selector,
per P5-THEME-ROSTER-AUTHORITY); the visitor's chosen language FOLLOWS them across all four pages.
This supersedes the P5-ARCH "freeze index to liquid-glass + drop the switcher" text. Recorded in
ACTIVE.md in this same slice.

## Observed surface (the wrongness)

- `site/index.html`: 3-theme switcher, `document.documentElement.dataset.theme`, persisted via
  `localStorage.setItem("dash-theme", …)`, restored on load. WORKS.
- `site/{showcase,settings,studio}.html`: framed in `render_page_shell("apple-dark")` — ONE
  `:root` token block (apple-dark), no `[data-theme]` overrides, no restore script. A visitor who
  picked carbon on index lands on an apple-dark page. NO invariant demands otherwise today —
  the law does not exist. This slice writes it.
- Their governed `.site-nav` is also rendered once with `render_nav("apple-dark", ...)`. Carbon's
  active underline/square anatomy therefore cannot appear there even if variables are switched.

## Candidate law (the RED: `tests/contracts/test_theme_continuity.py`, authority `page_chrome`)

1. **Override token blocks, fail closed.** For every pageshell page, the shell CSS carries a
   `:root[data-theme="<p>"]` block for EVERY active profile `p != house`, whose var map is
   EXACTLY the same shape as the base `root_block` minus the shared `SHELL_SCALE`
   (roles + radius + font + `--ps-pad` density + motion), each value provenance-pinned to
   `resolve_tokens(p)` / `design_tokens` — the page-shell provenance law extended per theme.
   Required roles, radius, font, density, and motion keys are indexed directly and a missing value
   raises; no `12`/`8`/`sans-serif` fallback may mint an uncited theme decision.
2. **One frozen bootstrap/state machine on all four pages.** Every page embeds EXACTLY
   `pageshell.theme_continuity_script_tag()` before theme CSS in `<head>`. Each `<html>` declares
   its `data-house-theme`; the shared script embeds the ACTIVE roster and storage key, then resolves
   a canonical active name in this order: valid `?theme=` → valid stored choice → declared house.
   Invalid URL/storage values fall through rather than shadowing a valid lower-precedence value;
   unavailable localStorage is caught; the root always receives the explicit canonical
   `data-theme="<active>"`. On DOM ready the same script wires any `[data-theme-set]` controls and
   synchronizes `aria-pressed`. Index's old bottom-of-body theme state machine is removed, leaving
   only its unrelated data hydration there. Parser-blocking placement prevents a wrong-theme paint.
   Verdict-free (no admissibility tokens); roster in the script == `active_design_profiles` both ways.
3. **One storage key.** `design_tokens.THEME_STORAGE_KEY == "dash-theme"` is the single source;
   only the shared bootstrap carries it (cross-page continuity pin; no second theme decider).
4. **Index side.** Its `[data-theme]` token blocks remain from `emit_css_root()`, but theme restore,
   URL precedence, persistence, click wiring, canonical root state, and pressed-state reflection move
   into the same head bootstrap consumed by the pageshell routes.
5. **Switchable governed anatomy.** Every page nav is one semantic nav band whose per-language
   CSS anatomy is emitted from every active profile's `components.nav` DATA and scoped to the
   root theme state (house anatomy when there is no stored choice; matching anatomy for every
   valid `data-theme`). Carbon must compute as square underline tabs; Apple/Liquid Glass as
   capsule pills. Recolouring an Apple nav with Carbon tokens is explicitly a failure.
6. **Runtime restoration proof.** A real Chrome probe seeds each active theme into localStorage,
   reloads every manifest route on one HTTP origin, and records the restored root theme plus
   computed shell/nav facts at both 1280 and true 390 CSS px. The closed matrix is
   `manifest route × active theme × {1280,390}`. Each collision-free
   `theme-continuity-<theme>-<viewport>.json` has a `.provenance.json` sidecar naming the producer,
   exact Chrome command and version, viewport, seeded theme, house theme, page hash, and observed
   canonical theme. The 390 fact also carries the existing overflow/offender facts and must remain
   clean under every selected theme. A default-state screenshot is not continuity evidence.
7. **Fail-closed negatives.** A shell missing an active profile's override block, a script with a
   wrong key, a roster subset, an invented declaration fallback, a nav anatomy/profile mismatch,
   or a decider token in the script — each reddens.

## Doctrine grounding

- Continuity clause: owner-ratified D1 (2026-07-13) — to be recorded in ACTIVE.md and cited by
  `docs/design/pageshell.md` §continuity in this slice. (W5 will class this clause as
  Mode D — owner-ratified; W5e provenance: `authority: owner-ratified`.)
- House language stays apple-dark for the proof pages (ratified P5-CHROME A3/A4/A5 — unchanged);
  continuity applies to the visitor's CHOICE. Before any choice each page shows its house
  language (index: liquid-glass default; proof pages: apple-dark).
- Token block semantics mirror the proven index mechanism (`emit_css_root`'s `[data-theme]`
  blocks — DESIGN_SPEC Law 3 token parity precedent).

## Render changes

- `pageshell.py`: extract fail-closed `_profile_decls(profile)` (the per-language var map);
  `root_block` = decls + `SHELL_SCALE`; NEW `theme_override_blocks(house)` emits
  `:root[data-theme="<p>"]` for each active `p != house`; `shell_css` embeds them after the base
  block. NEW `theme_continuity_script_tag()` — one frozen blob for all four routes (roster and key
  injected from `design_tokens`; per-route house is read from the root's `data-house-theme`).
- `components.py`: add a switchable-nav emitter that derives every anatomy branch from
  `components.nav`, emits one semantic nav band, and scopes each branch to the active root theme.
- `showcase.py` / `settings.py` / `studio.py`: use the switchable nav and insert the frozen script
  tag in `<head>`;
  showcase intro sentence updated honestly ("house language + your chosen theme follows you").
- `design_tokens.py`: `THEME_STORAGE_KEY = "dash-theme"`; `web_render.py` consumes the shared head
  bootstrap and deletes its legacy theme branch from `_script` (data hydration remains unchanged).
- FACTS seam: `design_render_adapter._strip_noise` + `test_page_shell._strip_root_blocks` learn
  that `:root[data-theme="<p>"]` blocks are DECLARED token blocks (stripped before the token-only
  scan) — exactly like the base `:root`. Everything else stays var-only.

## Contract folds (RED-first, same slice)

- `test_settings_composition.test_settings_page_is_generated_and_has_no_second_verdict_source`:
  the blanket `<script` ban becomes "the ONLY script is the frozen continuity blob (exact
  equality) and no decider token appears" — the studio frozen-`_STUDIO_JS` precedent applied to
  settings. The honest law was always "no second VERDICT source"; the continuity script carries
  no verdict.

## Open forks (decided here; critique welcome)

- **F1 — restore-only vs switcher on every page.** DECIDED restore-only: P5-THEME-ROSTER-AUTHORITY
  ratified ONE public selector on index; proof pages restore the choice. A per-page switcher would
  need that decision re-ratified.
- **F2 — house default vs global default on proof pages.** DECIDED keep apple-dark house (A3/A4/A5
  ratified); continuity binds the CHOICE, not the pre-choice default.
- **F3 — script placement.** DECIDED `<head>` parser-blocking before theme CSS (zero wrong-theme
  paint); placement pinned by the RED.
- **F4 — URL `?theme=` on proof pages.** DECIDED shared URL-first bootstrap on all routes. This
  removes the prior two-state-machine drift and gives storage-unavailable navigation a valid entry.
- **F5 — token-only vs full governed continuity.** DECIDED full governed continuity: profile-
  specific shell component anatomy reached by the choice switches too. W1 covers the current
  profile-specific nav; W2's DOM cover prevents a later house-pinned component from entering
  silently.

## Proof plan

RED observed failing for the right reason → implement → full suite green → mutation proofs
(drop one override block → red; flip the storage key in the script → red; remove a roster entry
from the script → red; restore Carbon with Apple nav CSS → red; delete a required token source and
observe fail-closed extraction; reintroduce the legacy index theme decider → red; make an invalid
URL shadow a valid stored choice → red) → regenerate all four pages → MF1 receipts (1280 screenshot + 390
DOM probe + provenance) for all four routes PLUS collision-free stored-theme continuity facts and
sidecars for every route × active choice × {1280,390} → ACTIVE.md + pageshell.md updated same
commit → codex CODE + ADVERSARIAL gates.

## Registry homes (same slice)

`tests/contracts/test_theme_continuity.py` → `repo_layout.json` `test_layout.contracts.members`
+ `tests_layout_contract.TEST_GROUPS["contracts"]` + `DESIGN_CONTRACT_GROUPS["page_chrome"]`.
This design doc lives in `docs/plans/handoff/` (existing handoff home).

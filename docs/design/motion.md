# Motion — the governed animation system (P5-BOARD B-0)

Motion is DATA like colour: per-language duration/easing tokens with provenance, consumed as
`var(--motion-*)`/`var(--ease-*)`; a hardcoded duration/easing in page CSS is off-token and
reddens (the same law as hex).

## §1 Doctrine sources
1. IBM Carbon Motion — https://carbondesignsystem.com/elements/motion/overview/ — duration tokens
   fast-01 70ms · fast-02 110ms · moderate-01 150ms · moderate-02 240ms · slow-01 400ms ·
   slow-02 700ms; easings: standard-productive cubic-bezier(0.2, 0, 0.38, 0.9),
   entrance-productive cubic-bezier(0, 0, 0.38, 0.9), exit-productive cubic-bezier(0.2, 0, 1, 0.9).
2. Apple HIG Motion — https://developer.apple.com/design/human-interface-guidelines/motion —
   principles only (purposeful, brief, never blocking; honor Reduce Motion). Numeric values are
   NOT published; apple-dark durations below are **[derived]** from the platform-standard ~0.3s
   UIKit transition convention.
3. WCAG 2.3.3 / prefers-reduced-motion — https://www.w3.org/WAI/WCAG21/Understanding/animation-from-interactions —
   all motion must collapse under `prefers-reduced-motion: reduce` (the existing global kill in
   web_render stays the enforcement).

## §2 Per-language motion character (tokens)
| token | liquid-glass (anchor, [derived]) | carbon (§1.1 productive) | apple-dark ([derived] §1.2) |
|---|---|---|---|
| motion-fast | 120ms | 70ms (fast-01) | 150ms |
| motion-base | 200ms | 110ms (fast-02) | 300ms |
| motion-slow | 400ms | 240ms (moderate-02) | 500ms |
| ease-standard | ease-in-out | cubic-bezier(0.2, 0, 0.38, 0.9) | ease-out |
| ease-enter | ease-out | cubic-bezier(0, 0, 0.38, 0.9) | ease-out |
| ease-exit | ease-in | cubic-bezier(0.2, 0, 1, 0.9) | ease-in |

Bounds law: every duration token sits in **[70ms, 700ms]** (the Carbon envelope — §1.1); page CSS
may only reference tokens. The legacy pulse keyframe (2.4s ambient status dot) is a DECLARED
exception pending its own clause or retirement (see §4).

## §3 Emitted invariants (roster `motion` flips)
- `*-motion-tokens` (`motion_tokens_cited`): the emitted `--motion-*`/`--ease-*` values equal the
  language's declared THEME_IA motion block exactly (provenance), and durations sit in the §2 band.
- `*-motion-tokenonly` (`motion_token_only`): zero hardcoded `\d+m?s` durations in governed page
  CSS outside the token emission (scan; the declared §4 exceptions list is the ONLY escape).
- Reduced-motion presence stays pinned by test_web_dashboard (existing).

## §4 Declared exceptions (each needs a clause or dies)
- `.live .dot` pulse 2.4s (ambient liveness): exceeds the band; kept ONE release behind the
  exception list, to be re-grounded or retired in B-1's gate.

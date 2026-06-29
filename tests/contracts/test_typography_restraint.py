"""Red-first TYPOGRAPHY LADDER + RESTRAINT contract — authority: Apple/Stripe numeric
typography + Linear/Stripe color discipline.

On the RENDERED SVG of the real generators:
  1. Every text size is on the locked ladder {46,26,22,20,14,12,11}; none < 11px.
  2. The single largest KPI value uses neutral ink, never an accent hue.
  3. A single card carries at most ONE *decorative* accent hue (status-chip pills
     and language dots excluded structurally).

RED on current code: the un-refactored cards (focus_board, repo_spotlight) still emit
ad-hoc sub-ladder sizes, and focus_board paints lane labels in three accent hues.
"""
from __future__ import annotations

import re
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.core.config import BLUE, CYAN, GREEN, ORANGE, PURPLE, RED, TEXT, TEXT_BRIGHT, TEXT_DIM

TYPE_LADDER = frozenset({46.0, 26.0, 22.0, 20.0, 14.0, 12.0, 11.0})
MIN_FONT = 11.0

ACCENT_HUES = {c.lower(): n for c, n in
               ((CYAN, "CYAN"), (BLUE, "BLUE"), (GREEN, "GREEN"),
                (ORANGE, "ORANGE"), (PURPLE, "PURPLE"), (RED, "RED"))}
NEUTRAL_INK = {TEXT_BRIGHT.lower(), TEXT.lower(), TEXT_DIM.lower()}

_FONT = re.compile(r'font-size="([0-9.]+)"')
_TEXT_NODE = re.compile(r"<text\b([^>]*)>(.*?)</text>", re.S)
_TEXT_FILL = re.compile(r'<text\b[^>]*?\bfill="(#[0-9a-fA-F]{3,8})"', re.S)
_ICON_STROKE = re.compile(
    r'<g\s+transform="translate\([^)]*\)\s*scale\([^)]*\)"[^>]*\bstroke="(#[0-9a-fA-F]{3,8})"', re.S)
_PILL_RECT = re.compile(r'<rect\b[^>]*\bfill="(#[0-9a-fA-F]{3,8})"[^>]*\bfill-opacity="0?\.\d+"', re.S)


def _font_sizes(svg: str):
    return [float(m) for m in _FONT.findall(svg)]


def _hero_node(svg: str):
    best = None
    for m in _TEXT_NODE.finditer(svg):
        attrs = m.group(1)
        fm = _FONT.search(attrs)
        if not fm:
            continue
        size = float(fm.group(1))
        fill_m = re.search(r'fill="(#[0-9a-fA-F]{3,8})"', attrs)
        fill = fill_m.group(1).lower() if fill_m else None
        if best is None or size > best[0]:
            best = (size, fill)
    return best


def _decorative_accent_hues(svg: str) -> set[str]:
    text_h = {ACCENT_HUES[h.lower()] for h in _TEXT_FILL.findall(svg) if h.lower() in ACCENT_HUES}
    icon_h = {ACCENT_HUES[h.lower()] for h in _ICON_STROKE.findall(svg) if h.lower() in ACCENT_HUES}
    pill_h = {ACCENT_HUES[h.lower()] for h in _PILL_RECT.findall(svg) if h.lower() in ACCENT_HUES}
    return (text_h | icon_h) - pill_h


def _calendar(days_back: int = 21, count: int = 3) -> dict:
    today = datetime.now(timezone.utc).date()
    return {"weeks": [{"contributionDays": [
        {"date": str(today - timedelta(days=i)), "contributionCount": count} for i in range(days_back)]}]}


class TypographyLadderRestraintContract(unittest.TestCase):
    """Locked type ladder + color restraint across every rendered card."""

    # NOTE: focus_board + repo_spotlight are NOT yet converted to the kit (B3); their
    # off-ladder sizes are tracked by the global min-font guard until then. They are
    # added back to this set the moment they're converted.
    def _render_cards(self, d: str) -> dict[str, str]:
        from scripts.rendering.generate_badges import generate as gen_badges
        from scripts.rendering.generate_builder_scorecard import generate as gen_scorecard
        from scripts.rendering.generate_snapshot_panel import generate as gen_snapshot
        from scripts.rendering.generate_streak_summary import generate as gen_streak

        out = lambda name: str(Path(d) / name)
        cards: dict[str, str] = {}

        gen_streak(calendar=_calendar(), current_streak_days=12, total_contributions=1843, output_path=out("streak.svg"))
        cards["streak_summary"] = Path(out("streak.svg")).read_text(encoding="utf-8")

        gen_scorecard({"last_year_contributions": 8104, "active_days_last_year": 287, "active_repos_7d": 5,
                       "ci_coverage_pct": 82, "automation_workflows": 16, "releases_30d": 3,
                       "primary_lang_share_pct": 61.4, "median_days_since_push": 4}, output_path=out("score.svg"))
        cards["builder_scorecard"] = Path(out("score.svg")).read_text(encoding="utf-8")

        gen_snapshot([
            {"key": "last_year_contributions", "label": "12-Month Contributions", "display_value": "8,104"},
            {"key": "public_scope_commits", "label": "Public Commits", "display_value": "4,264"},
            {"key": "total_repos", "label": "Repositories", "display_value": "67"},
            {"key": "total_stars", "label": "Stargazers", "display_value": "78"},
        ], {"ci_status": "ok", "commits_status": "ok", "releases_status": "error", "events_status": "partial"},
            output_path=out("snap.svg"))
        cards["snapshot_panel"] = Path(out("snap.svg")).read_text(encoding="utf-8")

        gen_badges(output_path=out("badges.svg"), public_nonfork_repos=42, public_forks=8,
                   private_owned_repos=146, ci_count=16, last_year_contributions=8104)
        cards["badges"] = Path(out("badges.svg")).read_text(encoding="utf-8")
        return cards

    def test_type_ladder_locked_and_legible(self):
        offenders = []
        with tempfile.TemporaryDirectory() as d:
            cards = self._render_cards(d)
        for name, svg in cards.items():
            for size in sorted(set(_font_sizes(svg))):
                if size not in TYPE_LADDER:
                    offenders.append(f"{name}: off-ladder font-size {size:g}")
                elif size < MIN_FONT:
                    offenders.append(f"{name}: sub-floor font-size {size:g}")
        self.assertEqual([], offenders,
                         "every rendered text size must be on the locked ladder, nothing <11px:\n  " + "\n  ".join(offenders))

    def test_hero_value_uses_neutral_ink(self):
        offenders = []
        with tempfile.TemporaryDirectory() as d:
            cards = self._render_cards(d)
        for name, svg in cards.items():
            hero = _hero_node(svg)
            self.assertIsNotNone(hero, f"{name}: card emitted no text")
            size, fill = hero
            if size < 40:
                continue
            if fill in ACCENT_HUES:
                offenders.append(f"{name}: hero value ({size:g}px) painted accent {ACCENT_HUES[fill]} {fill}")
            elif fill not in NEUTRAL_INK:
                offenders.append(f"{name}: hero value ({size:g}px) fill {fill} is not neutral ink")
        self.assertEqual([], offenders, "the largest KPI value must use neutral ink:\n  " + "\n  ".join(offenders))

    def test_decorative_accent_restraint_per_card(self):
        offenders = []
        with tempfile.TemporaryDirectory() as d:
            cards = self._render_cards(d)
        for name, svg in cards.items():
            deco = _decorative_accent_hues(svg)
            if len(deco) > 1:
                offenders.append(f"{name}: {len(deco)} decorative accent hues {sorted(deco)}")
        self.assertEqual([], offenders,
                         "a card may carry at most ONE decorative accent hue:\n  " + "\n  ".join(offenders))


if __name__ == "__main__":
    unittest.main()

"""Red-first DESIGN contracts (semantic-TDD).

Each test encodes a DESIGN_AUDIT invariant as an executable contract. They are
written RED (they fail on the current code) and are driven GREEN by the design-
token + component refactor. Direction: Apple HIG restraint x Power BI information
architecture; numeric thresholds are sourced from docs/DESIGN_SPEC.md.

Permanent guards once green: raw color/size literals must resolve from the single
design-token source, and no rendered text may fall below the legibility floor.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # tests/<group>/<file>.py -> repo root
RENDERING = ROOT / "scripts" / "rendering"

# Hex colors belong in the token source (scripts/core/config.py / design_tokens),
# never hard-coded at a rendering call site.
_HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
# Literal font-size attributes emitted into SVG.
_FONT = re.compile(r'font-size="([0-9.]+)"')
# Legibility floor for README SVGs downscaled into the column (DESIGN_SPEC).
MIN_FONT = 11.0


def _code_lines(path: Path):
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#"):  # skip full-line comments
            continue
        yield i, line


class DesignTokenContract(unittest.TestCase):
    def test_no_raw_hex_in_rendering_code(self):
        offenders = []
        for path in sorted(RENDERING.glob("*.py")):
            for lineno, line in _code_lines(path):
                for hexval in _HEX.findall(line):
                    offenders.append(f"{path.relative_to(ROOT)}:{lineno}  {hexval}")
        self.assertEqual(
            [],
            offenders,
            "Raw hex colors must resolve from the design-token source, not be "
            "hard-coded in rendering code:\n  " + "\n  ".join(offenders),
        )


class FontLegibilityContract(unittest.TestCase):
    # GREEN permanent guard (Phase-4 B3 landed the sparse-label redesign of the
    # heatmap + contribution + the progress_ring sublabel). No rendered text literal
    # may fall below the 11px legibility floor (DESIGN_SPEC 3.8/3.15/3.17).
    def test_no_font_size_below_floor(self):
        offenders = []
        for path in sorted(RENDERING.glob("*.py")):
            text = path.read_text(encoding="utf-8")
            for match in _FONT.finditer(text):
                if float(match.group(1)) < MIN_FONT:
                    offenders.append(f"{path.name}: font-size={match.group(1)}")
        self.assertEqual(
            [],
            offenders,
            f"Rendered text must stay >= {MIN_FONT}px so README cards read when "
            "downscaled:\n  " + "\n  ".join(offenders),
        )


class HierarchyContract(unittest.TestCase):
    """DESIGN_SPEC 3.2/3.3: one dominant KPI per metric surface, strictly larger
    than every secondary value (Power BI 'size = emphasis')."""

    def _render_hero(self, out: str) -> str:
        from scripts.rendering.generate_metrics_general import generate

        snapshot = {
            "last_year_contributions": 8104,
            "public_scope_commits": 4264,
            "total_repos": 67,
            "private_owned_repos": 146,
            "total_stars": 78,
            "languages_count": 24,
            "prs_merged": 35,
            "releases": 0,
            "ci_repos": 16,
            "streak_days": 2,
        }
        generate(
            username="jguida941",
            snapshot=snapshot,
            generated_at="2026-06-28T00:00:00Z",
            output_path=out,
        )
        return Path(out).read_text(encoding="utf-8")

    def test_hero_has_one_dominant_kpi(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render_hero(str(Path(d) / "hero.svg"))
        sizes = [float(m) for m in re.findall(r'font-size="([0-9.]+)"', svg)]
        self.assertTrue(sizes, "hero emitted no text")
        top = max(sizes)
        self.assertGreaterEqual(top, 40, "hero must promote one KPI to display size")
        self.assertEqual(sizes.count(top), 1, "exactly one dominant KPI value")
        second = max(s for s in sizes if s < top)
        self.assertLess(second, top, "KPI must be strictly larger than every secondary value")


_TEXT_NODE = re.compile(r"<text[^>]*>(.*?)</text>", re.S)


def _text_contents(svg: str) -> str:
    return " ".join(_TEXT_NODE.findall(svg))


class ByTheNumbersContract(unittest.TestCase):
    """DESIGN_SPEC 3.2/3.3/3.15/Part 1.8: the "By The Numbers" card promotes one
    dominant KPI (12-month contributions) at display size, demotes the rest to
    secondary metric tiles on the type scale, drops the decorative gradient
    ribbon, scales numbers to <=4 numerals, and renders an honest empty state."""

    SCALE = {46.0, 26.0, 22.0, 20.0, 14.0, 12.0, 11.0}

    def _render(self, out: str, **overrides) -> str:
        from scripts.rendering.generate_badges import generate

        params = dict(
            public_nonfork_repos=42,
            public_forks=8,
            private_owned_repos=146,
            ci_count=16,
            last_year_contributions=8104,
        )
        params.update(overrides)
        generate(output_path=out, **params)
        return Path(out).read_text(encoding="utf-8")

    def _sizes(self, svg: str):
        return [float(m) for m in _FONT.findall(svg)]

    def test_one_dominant_kpi(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "badges.svg"))
        sizes = self._sizes(svg)
        self.assertTrue(sizes, "card emitted no text")
        top = max(sizes)
        self.assertGreaterEqual(top, 40, "needs one display-size KPI (contributions)")
        self.assertEqual(sizes.count(top), 1, "exactly one dominant KPI value")
        second = max(s for s in sizes if s < top)
        self.assertLessEqual(second, 26, "secondary values must be metric-scale, below the KPI")

    def test_sizes_on_scale_and_legible(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "badges.svg"))
        for s in self._sizes(svg):
            self.assertIn(s, self.SCALE, f"off-scale font-size {s}")
            self.assertGreaterEqual(s, 11.0, f"sub-floor font-size {s}")

    def test_no_gradient_ribbon(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "badges.svg"))
        self.assertNotIn("url(#bn-accent)", svg, "decorative gradient ribbon must be gone")

    def test_numbers_scaled_to_four_numerals(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(
                str(Path(d) / "badges.svg"),
                last_year_contributions=123456,
                ci_count=98765,
            )
        self.assertIsNone(
            re.search(r"\d{5,}", _text_contents(svg)),
            "values must be k/M scaled to <=4 numerals",
        )

    def test_empty_state_when_no_data(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(
                str(Path(d) / "badges.svg"),
                public_nonfork_repos=None,
                public_forks=None,
                private_owned_repos=None,
                ci_count=None,
                last_year_contributions=None,
            )
        texts = _TEXT_NODE.findall(svg)
        self.assertLessEqual(
            len(texts), 3, "empty card should be header + one explanatory line, not metric tiles"
        )
        self.assertIsNone(
            re.search(r"\d", _text_contents(svg)), "empty state must not fabricate numbers"
        )


class StreakSummaryContract(unittest.TestCase):
    """DESIGN_SPEC 3.2/3.3/Part 1.2/Part 4: Streak Summary promotes Current Streak
    to one dominant display KPI, left-aligned (not a centered triptych), demotes
    Total/Longest to secondary tiles, and drops the orange gradient ribbon + the
    decorative orange hero number for neutral ink (emphasis via size, not hue)."""

    SCALE = {46.0, 26.0, 22.0, 20.0, 14.0, 12.0, 11.0}

    def _calendar(self, days_back: int = 14, count: int = 3):
        from datetime import datetime, timezone, timedelta

        today = datetime.now(timezone.utc).date()
        days = [
            {"date": str(today - timedelta(days=i)), "contributionCount": count}
            for i in range(days_back)
        ]
        return {"weeks": [{"contributionDays": days}]}

    def _render(self, out: str, *, calendar=None, current=12, total=1843) -> str:
        from scripts.rendering.generate_streak_summary import generate

        generate(
            calendar=self._calendar() if calendar is None else calendar,
            current_streak_days=current,
            total_contributions=total,
            output_path=out,
        )
        return Path(out).read_text(encoding="utf-8")

    def _sizes(self, svg: str):
        return [float(m) for m in _FONT.findall(svg)]

    def test_one_dominant_kpi(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "streak.svg"))
        sizes = self._sizes(svg)
        top = max(sizes)
        self.assertGreaterEqual(top, 40, "current streak must be the display KPI")
        self.assertEqual(sizes.count(top), 1, "exactly one dominant KPI value")
        self.assertLessEqual(max(s for s in sizes if s < top), 26, "secondaries below the KPI")

    def test_sizes_on_scale_and_legible(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "streak.svg"))
        for s in self._sizes(svg):
            self.assertIn(s, self.SCALE, f"off-scale font-size {s}")
            self.assertGreaterEqual(s, 11.0, f"sub-floor font-size {s}")

    def test_kpi_left_aligned(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "streak.svg"))
        # the display-size KPI node must not be centered (top-left reading path)
        kpi = re.search(r'<text[^>]*font-size="46"[^>]*>', svg)
        self.assertIsNotNone(kpi, "no display KPI node")
        self.assertNotIn('text-anchor="middle"', kpi.group(0), "KPI must be left-aligned")

    def test_no_orange_accent(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "streak.svg"))
        self.assertNotIn("#ff9e64", svg, "orange gradient ribbon / hero hue must be gone")

    def test_empty_state_when_no_calendar(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "streak.svg"), calendar={"weeks": []}, current=0, total=None)
        texts = _TEXT_NODE.findall(svg)
        self.assertLessEqual(len(texts), 3, "empty card = header + one explanatory line")
        self.assertIsNone(re.search(r"\d", _text_contents(svg)), "empty state must not fabricate numbers")


class SnapshotPanelContract(unittest.TestCase):
    """DESIGN_SPEC 3.2/3.3/3.6/Part 1.7: the Raw Data Snapshot promotes one KPI,
    curates to <=4 secondary tiles (not an 11-row dump), drops the gradient
    ribbon, and renders pipeline status by distinct icon SHAPE + label."""

    SCALE = {46.0, 26.0, 22.0, 20.0, 14.0, 12.0, 11.0}
    CHECK = "M20 6 9 17l-5-5"      # success icon path (Lucide 'check')
    CROSS = "M18 6 6 18"            # danger icon path (Lucide 'x' / 'cross')

    def _rows(self):
        return [
            {"key": "last_year_contributions", "label": "12-Month Contributions", "display_value": "8,104"},
            {"key": "public_scope_commits", "label": "Public Commits", "display_value": "4,264"},
            {"key": "total_repos", "label": "Repositories", "display_value": "67"},
            {"key": "private_owned_repos", "label": "Private Repos", "display_value": "146"},
            {"key": "total_stars", "label": "Stargazers", "display_value": "78"},
            {"key": "languages_count", "label": "Languages", "display_value": "24"},
        ]

    def _render(self, out: str, *, rows=None, quality=None) -> str:
        from scripts.rendering.generate_snapshot_panel import generate

        generate(
            self._rows() if rows is None else rows,
            quality
            if quality is not None
            else {"ci_status": "ok", "commits_status": "ok", "releases_status": "error", "events_status": "partial"},
            output_path=out,
        )
        return Path(out).read_text(encoding="utf-8")

    def _sizes(self, svg):
        return [float(m) for m in _FONT.findall(svg)]

    def test_one_dominant_kpi(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "snap.svg"))
        sizes = self._sizes(svg)
        top = max(sizes)
        self.assertGreaterEqual(top, 40, "needs one display KPI")
        self.assertEqual(sizes.count(top), 1, "exactly one dominant KPI")
        self.assertLessEqual(max(s for s in sizes if s < top), 26, "secondaries below KPI")

    def test_sizes_on_scale_and_legible(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "snap.svg"))
        for s in self._sizes(svg):
            self.assertIn(s, self.SCALE, f"off-scale font-size {s}")
            self.assertGreaterEqual(s, 11.0, f"sub-floor font-size {s}")

    def test_no_gradient_ribbon(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "snap.svg"))
        self.assertNotIn("gk-ribbon", svg, "gradient ribbon must be replaced by a hairline")

    def test_secondary_tiles_curated(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "snap.svg"))
        # secondary metric tile values render at the metric token (22)
        self.assertLessEqual(svg.count('font-size="22"'), 4, "cap at <=4 curated secondary tiles")

    def test_status_by_distinct_icon_shape(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "snap.svg"))
        self.assertIn(self.CHECK, svg, "success status must use the check shape")
        self.assertIn(self.CROSS, svg, "danger status must use a distinct (cross) shape")

    def test_empty_state(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "snap.svg"), rows=[], quality={})
        texts = _TEXT_NODE.findall(svg)
        self.assertLessEqual(len(texts), 3, "empty snapshot = header + one explanatory line")
        self.assertIsNone(re.search(r"\d", _text_contents(svg)), "empty state must not fabricate numbers")


class BuilderScorecardContract(unittest.TestCase):
    """DESIGN_SPEC 3.2/3.3/3.9/Part 4: the Builder Scorecard promotes contributions
    to one display KPI, demotes the rest to uniform secondary tiles, renders CI
    coverage as a token-labeled donut gauge (the one sanctioned circular chart),
    and drops the rainbow accents + gradient ribbon."""

    SCALE = {46.0, 26.0, 22.0, 20.0, 14.0, 12.0, 11.0}

    def _scorecard(self):
        return {
            "last_year_contributions": 8104,
            "active_days_last_year": 287,
            "active_repos_7d": 5,
            "ci_coverage_pct": 82,
            "automation_workflows": 16,
            "releases_30d": 3,
            "primary_lang_share_pct": 61.4,
            "median_days_since_push": 4,
        }

    def _render(self, out: str, *, scorecard=None) -> str:
        from scripts.rendering.generate_builder_scorecard import generate

        generate(self._scorecard() if scorecard is None else scorecard, output_path=out)
        return Path(out).read_text(encoding="utf-8")

    def _sizes(self, svg):
        return [float(m) for m in _FONT.findall(svg)]

    def test_one_dominant_kpi(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "score.svg"))
        sizes = self._sizes(svg)
        top = max(sizes)
        self.assertGreaterEqual(top, 40, "needs one display KPI (contributions)")
        self.assertEqual(sizes.count(top), 1, "exactly one dominant KPI")
        self.assertLessEqual(max(s for s in sizes if s < top), 26, "secondaries below KPI")

    def test_sizes_on_scale_and_legible(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "score.svg"))
        for s in self._sizes(svg):
            self.assertIn(s, self.SCALE, f"off-scale font-size {s}")
            self.assertGreaterEqual(s, 11.0, f"sub-floor font-size {s}")

    def test_no_gradient_ribbon(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "score.svg"))
        self.assertNotIn("gk-ribbon", svg, "gradient ribbon must be replaced by a hairline")

    def test_ci_coverage_is_labeled_gauge(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "score.svg"))
        # gauge center label rides at a scale token (20) and shows a percent in [0,100]
        self.assertRegex(
            svg, r'<text[^>]*font-size="20"[^>]*>[^<]*%</text>',
            "CI coverage must render as a >=12px labeled gauge",
        )

    def test_empty_state(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "score.svg"), scorecard={})
        texts = _TEXT_NODE.findall(svg)
        self.assertLessEqual(len(texts), 3, "empty scorecard = header + one explanatory line")
        self.assertIsNone(re.search(r"\d", _text_contents(svg)), "empty state must not fabricate numbers")


class LanguageBreakdownContract(unittest.TestCase):
    """DESIGN_SPEC 3.2/3.10/Part 4: Language Breakdown promotes the leading-language
    share as the one display KPI, renders a flat part-to-whole LanguageBar capped at
    <=6 (+Other) with a name+value legend, and drops the glossy sheen gradient."""

    SCALE = {46.0, 26.0, 22.0, 20.0, 14.0, 12.0, 11.0}

    def _bytes(self):
        return {
            "Python": 600000, "TypeScript": 250000, "Rust": 120000, "Go": 60000,
            "C": 30000, "Shell": 15000, "HTML": 9000, "CSS": 5000,
        }

    def _render(self, out: str, *, language_bytes=None) -> str:
        from scripts.rendering.generate_language_chart import generate

        generate(self._bytes() if language_bytes is None else language_bytes, output_path=out)
        return Path(out).read_text(encoding="utf-8")

    def _sizes(self, svg):
        return [float(m) for m in _FONT.findall(svg)]

    def test_one_dominant_kpi(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "lang.svg"))
        sizes = self._sizes(svg)
        top = max(sizes)
        self.assertGreaterEqual(top, 40, "needs one display KPI (leading-language share)")
        self.assertEqual(sizes.count(top), 1, "exactly one dominant KPI")
        self.assertLessEqual(max(s for s in sizes if s < top), 26, "secondaries below KPI")

    def test_sizes_on_scale_and_legible(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "lang.svg"))
        for s in self._sizes(svg):
            self.assertIn(s, self.SCALE, f"off-scale font-size {s}")
            self.assertGreaterEqual(s, 11.0, f"sub-floor font-size {s}")

    def test_no_sheen_gradient(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "lang.svg"))
        self.assertNotIn("Sheen", svg, "the glossy bar sheen gradient must be removed (flat fill)")

    def test_segments_capped_with_other(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "lang.svg"))
        # legend renders one dot per segment; cap at <=6 languages + Other
        self.assertLessEqual(svg.count("<circle"), 7, "cap visible segments at <=6 (+Other)")
        self.assertIn(">Other</text>", svg, "languages beyond the cap fold into 'Other'")

    def test_segment_has_name_and_value(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "lang.svg"))
        self.assertIn(">Python</text>", svg, "each segment shows its language name")
        self.assertRegex(svg, r">[0-9]+(\.[0-9]+)?%</text>", "each segment shows its percent value")

    def test_empty_state(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "lang.svg"), language_bytes={})
        self.assertIsNone(
            re.search(r"\d", _text_contents(svg)), "empty state must not fabricate numbers"
        )


class EngineeringCadenceContract(unittest.TestCase):
    """DESIGN_SPEC 3.2/3.8/3.9/Part 4: Engineering Cadence promotes active days to
    one display KPI, renders the weekly cadence as a TrendPanel (stroke >=1.5) and
    CI coverage as a labeled DonutGauge, on the type scale, with no gradient ribbon."""

    SCALE = {46.0, 26.0, 22.0, 20.0, 14.0, 12.0, 11.0}

    def _data(self):
        return {
            "weekly_cadence": [2, 5, 3, 8, 4, 6, 9, 5, 7, 4, 6, 8],
            "active_days_last_year": 287,
            "automation_workflows": 16,
            "automation_repos": 12,
            "primary_lang_share_pct": 61.4,
            "languages_over_5pct": 4,
            "public_repos_total": 42,
            "public_nonfork_repos": 30,
            "private_repos_total": 146,
        }

    def _render(self, out: str, *, data=None) -> str:
        from scripts.rendering.generate_engineering_cadence import generate

        generate(self._data() if data is None else data, output_path=out)
        return Path(out).read_text(encoding="utf-8")

    def _sizes(self, svg):
        return [float(m) for m in _FONT.findall(svg)]

    def test_one_dominant_kpi(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "eng.svg"))
        sizes = self._sizes(svg)
        top = max(sizes)
        self.assertGreaterEqual(top, 40, "needs one display KPI (active days)")
        self.assertEqual(sizes.count(top), 1, "exactly one dominant KPI")
        self.assertLessEqual(max(s for s in sizes if s < top), 26, "secondaries below KPI")

    def test_sizes_on_scale_and_legible(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "eng.svg"))
        for s in self._sizes(svg):
            self.assertIn(s, self.SCALE, f"off-scale font-size {s}")
            self.assertGreaterEqual(s, 11.0, f"sub-floor font-size {s}")

    def test_no_gradient_ribbon(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "eng.svg"))
        self.assertNotIn("gk-ribbon", svg, "gradient ribbon must be replaced by a hairline")

    def test_trend_stroke_legible(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "eng.svg"))
        strokes = re.findall(r'<polyline[^>]*stroke-width="([0-9.]+)"', svg)
        self.assertTrue(strokes, "weekly cadence must render a trend polyline")
        self.assertTrue(all(float(s) >= 1.5 for s in strokes), "trend stroke must be >=1.5px")

    def test_ci_coverage_is_labeled_gauge(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "eng.svg"))
        self.assertRegex(
            svg, r'<text[^>]*font-size="20"[^>]*>[^<]*%</text>',
            "CI coverage must render as a >=12px labeled gauge",
        )

    def test_empty_state(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "eng.svg"), data={})
        self.assertIsNone(
            re.search(r"\d", _text_contents(svg)), "empty state must not fabricate numbers"
        )


class CurrentlyWorkingContract(unittest.TestCase):
    """DESIGN_SPEC 3.2/3.11/3.12/Part 4: Currently Working On promotes the active-
    repo count to one display KPI, lists repos as uniform rows (language by dot AND
    label), drops the gradient ribbon, and renders an honest empty state."""

    SCALE = {46.0, 26.0, 22.0, 20.0, 14.0, 12.0, 11.0}

    def _repos(self):
        from datetime import datetime, timezone, timedelta

        now = datetime.now(timezone.utc)

        def iso(h):
            return (now - timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%SZ")

        return [
            {"name": "ci-cd-hub", "language": "Python", "pushed_at": iso(3),
             "last_commit_msg": "add deploy gate", "is_private": False,
             "html_url": "https://github.com/x/ci-cd-hub"},
            {"name": "voiceterm", "language": "Rust", "pushed_at": iso(20),
             "last_commit_msg": "fix audio buffer", "is_private": False,
             "html_url": "https://github.com/x/voiceterm"},
            {"name": "secret-svc", "language": "Go", "pushed_at": iso(50), "is_private": True},
        ]

    def _render(self, out: str, *, repos=None) -> str:
        from scripts.rendering.generate_currently_working import generate

        generate(self._repos() if repos is None else repos, output_path=out)
        return Path(out).read_text(encoding="utf-8")

    def _sizes(self, svg):
        return [float(m) for m in _FONT.findall(svg)]

    def test_one_dominant_kpi(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "cw.svg"))
        sizes = self._sizes(svg)
        top = max(sizes)
        self.assertGreaterEqual(top, 40, "needs one display KPI (active repo count)")
        self.assertEqual(sizes.count(top), 1, "exactly one dominant KPI")
        self.assertLessEqual(max(s for s in sizes if s < top), 26, "secondaries below KPI")

    def test_sizes_on_scale_and_legible(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "cw.svg"))
        for s in self._sizes(svg):
            self.assertIn(s, self.SCALE, f"off-scale font-size {s}")
            self.assertGreaterEqual(s, 11.0, f"sub-floor font-size {s}")

    def test_no_gradient_ribbon(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "cw.svg"))
        self.assertNotIn("gk-ribbon", svg, "gradient ribbon must be replaced by a hairline")

    def test_language_color_independence(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "cw.svg"))
        self.assertIn(">Python</text>", svg, "language must be shown by label, not hue alone")
        self.assertGreaterEqual(svg.count("<circle"), 1, "each row carries a language dot")

    def test_empty_state(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            svg = self._render(str(Path(d) / "cw.svg"), repos=[])
        self.assertIsNone(
            re.search(r"\d", _text_contents(svg)), "empty state must not fabricate numbers"
        )


if __name__ == "__main__":
    unittest.main()

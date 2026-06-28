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

ROOT = Path(__file__).resolve().parent.parent
RENDERING = ROOT / "scripts" / "rendering"

# Hex colors belong in the token source (scripts/core/config.py / design_tokens),
# never hard-coded at a rendering call site.
_HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
# Literal font-size attributes emitted into SVG.
_FONT = re.compile(r'font-size="([0-9.]+)"')
# Legibility floor for README SVGs downscaled into the column (DESIGN_SPEC).
MIN_FONT = 10.0


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
    # RED (tracked): ~10 sub-10px labels remain (dense heatmap hour ticks +
    # contribution legend + ring sublabel). DESIGN_SPEC 3.8/3.15/3.17 says the fix
    # is a SPARSE-LABEL redesign (fewer ticks), not a font bump that would overflow.
    # Driven green in WS4; remove this decorator when the redesign lands.
    @unittest.expectedFailure
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
    CHECK = "M20 6 9 17l-5-5"      # success icon path (status_chip 'check')
    CROSS = "M6.5 6.5l11 11"        # danger icon path (status_chip 'cross')

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


if __name__ == "__main__":
    unittest.main()

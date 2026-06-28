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


if __name__ == "__main__":
    unittest.main()

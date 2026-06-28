import tempfile
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from scripts.rendering.generate_streak_summary import generate


SVG_NS = "{http://www.w3.org/2000/svg}"


def _build_calendar(day_rows: list[tuple[str, int]]) -> dict:
    weeks = []
    for index in range(0, len(day_rows), 7):
        slice_rows = day_rows[index:index + 7]
        weeks.append(
            {
                "contributionDays": [
                    {"date": day, "contributionCount": count}
                    for day, count in slice_rows
                ]
            }
        )
    return {"weeks": weeks}


class StreakSummarySvgTests(unittest.TestCase):
    def test_current_streak_is_dominant_kpi_with_demoted_tiles(self):
        """Power BI hierarchy (DESIGN_SPEC 3.2/3.3): Current Streak is promoted to
        the single display KPI; Total Contributions and Longest Streak demote to
        secondary tiles (no longer a centered, equal-baseline triptych)."""
        calendar = _build_calendar(
            [
                ("2000-01-01", 0),
                *[(f"2000-01-{day:02d}", 1) for day in range(2, 31)],
                ("2000-01-31", 0),
                *[(f"2000-02-{day:02d}", 1) for day in range(1, 26)],
            ]
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "streak_summary.svg"
            generate(
                calendar=calendar,
                current_streak_days=25,
                total_contributions=321,
                output_path=str(output_path),
            )

            root = ET.fromstring(output_path.read_text(encoding="utf-8"))

        text_nodes = root.findall(f".//{SVG_NS}text")
        by_text = {"".join(node.itertext()).strip(): node for node in text_nodes}
        sizes = [float(node.attrib.get("font-size", "0")) for node in text_nodes]

        # Current Streak (25) is the one display-size KPI, unique and left-aligned.
        self.assertEqual(sizes.count(46.0), 1, "exactly one display KPI")
        kpi = by_text["25"]
        self.assertEqual(float(kpi.attrib["font-size"]), 46.0)
        self.assertNotIn("middle", kpi.attrib.get("text-anchor", ""))

        # Secondary metrics demote to tiles, strictly smaller than the KPI.
        for value in ("321", "29"):
            self.assertLess(float(by_text[value].attrib["font-size"]), 46.0)

        # The three are no longer a centered triptych sharing one baseline.
        self.assertNotEqual(int(by_text["321"].attrib["y"]), int(kpi.attrib["y"]))
        self.assertIn("current streak", by_text)
        self.assertIn("total contributions", by_text)
        self.assertIn("longest streak", by_text)


if __name__ == "__main__":
    unittest.main()

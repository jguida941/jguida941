import tempfile
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from scripts.generate_streak_summary import generate


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
    def test_current_streak_ring_clears_label_and_columns_share_baselines(self):
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

        text_y = {
            "".join(node.itertext()).strip(): int(node.attrib["y"])
            for node in root.findall(f".//{SVG_NS}text")
        }
        ring = next(node for node in root.findall(f".//{SVG_NS}circle") if "stroke" in node.attrib)

        ring_bottom = int(ring.attrib["cy"]) + int(ring.attrib["r"])

        self.assertGreaterEqual(text_y["Current Streak"] - ring_bottom, 25)
        self.assertEqual(text_y["321"], text_y["25"])
        self.assertEqual(text_y["25"], text_y["29"])
        self.assertEqual(text_y["Total Contributions"], text_y["Current Streak"])
        self.assertEqual(text_y["Current Streak"], text_y["Longest Streak"])
        self.assertEqual(text_y["Jan 1 - Feb 25"], text_y["Feb 1 - Feb 25"])
        self.assertEqual(text_y["Feb 1 - Feb 25"], text_y["Jan 2 - Jan 30"])


if __name__ == "__main__":
    unittest.main()

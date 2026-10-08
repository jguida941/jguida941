"""Behavior of the shared dashboard's static projections."""
import unittest
import xml.etree.ElementTree as ET
from scripts.rendering.generate_dashboard_summary import render_svg
from scripts.contracts.dashboard_summary import _fact


class DashboardSummaryTests(unittest.TestCase):
    def test_inventory_zero_is_reported_and_absence_unavailable(self):
        zero = _fact("inventory.private_owned", 0, "Private", "private-owned")
        self.assertEqual((zero["display_value"], zero["quality"]["status"]), ("0", "unknown"))
        missing = _fact("inventory.private_owned", None, "Private", "private-owned")
        self.assertEqual((missing["display_value"], missing["quality"]["status"]), ("n/a", "unavailable"))

    def test_both_sizes_retain_sections_and_empty_states(self):
        for mobile,width in ((False,"840"),(True,"360")):
            root=ET.fromstring(render_svg({},mobile=mobile))
            self.assertEqual(root.get("width"),width)
            sections=[node.get("data-section") for node in root.iter() if node.get("data-section")]
            self.assertEqual(sections,["overview","weekly","rhythm","languages","automation","working","focus","projects","metrics","calendar"])
            self.assertIn("Contribution calendar unavailable", " ".join(root.itertext()))
            self.assertFalse(any(node.tag.endswith("filter") for node in root.iter()))


class DashboardVisualTests(unittest.TestCase):
    def test_six_languages_and_other_preserve_observed_bytes(self):
        from datetime import date
        from scripts.contracts.dashboard_summary import build_dashboard_summary
        values = {name: value for name, value in zip(
            ("Python", "Rust", "C++", "Swift", "TypeScript", "Java", "Go", "Shell"), range(8, 0, -1))}
        summary = build_dashboard_summary({"language_bytes": values, "data_quality": {"metric_statuses": {"top_languages": "exact"}}}, profile_date=date(2026, 10, 8))
        rows = summary["languages"]["rows"]
        self.assertEqual([row["name"] for row in rows], list(values)[:6] + ["Other"])
        self.assertEqual(rows[-1]["bytes"], values["Go"] + values["Shell"])
        self.assertEqual(sum(row["bytes"] for row in rows), sum(values.values()))

    def test_native_colors_ring_and_calendar_geometry(self):
        import math
        from scripts.core.config import LANG_COLORS, CONTRIB_RAMP
        summary = {
            "languages": {"rows": [{"name": "Python", "percent": 100, "display_value": "100.0%"}], "quality": "exact"},
            "automation": {"model": {"combined": {"adoption_pct": 75}}, "display": {"combined": {
                "configured_repos": "3", "eligible_repos": "4", "workflow_files": "6", "adoption": "75%", "status": "Exact"}}},
            "calendar": {"window": "2026-10-07 – 2026-10-08 · UTC", "days": [{"date": "2026-10-07", "count": 0}, {"date": "2026-10-08", "count": 8}]},
        }
        ns = "{http://www.w3.org/2000/svg}"
        for mobile in (False, True):
            root = ET.fromstring(render_svg(summary, mobile=mobile))
            bars = [node for node in root.iter() if node.get("data-role") == "language-bar"]
            self.assertEqual(bars[0].get("fill"), LANG_COLORS["Python"])
            rings = [node for node in root.iter(ns + "circle") if node.get("stroke-dasharray")]
            self.assertEqual(len(rings), 1)
            ratio = float(rings[0].get("stroke-dasharray").split()[0]) / (2 * math.pi * float(rings[0].get("r")))
            self.assertAlmostEqual(ratio, .75, delta=.0001)
            cells = [node for node in root.iter() if node.get("data-role") == "calendar-cell"]
            self.assertEqual([(node.get("width"), node.get("height")) for node in cells], [("11", "11"), ("11", "11")])
            self.assertEqual(cells[-1].get("fill"), CONTRIB_RAMP[-1])
            self.assertNotIn("Observation complete", " ".join(root.itertext()))

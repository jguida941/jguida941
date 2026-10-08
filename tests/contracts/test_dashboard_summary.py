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



class DashboardFinalFitTests(unittest.TestCase):
    def test_avatar_is_owner_only_and_exact_registered_source(self):
        import base64
        import hashlib
        from pathlib import Path
        from unittest.mock import patch
        from scripts import contracts
        from scripts.rendering import generate_dashboard_summary as renderer
        ns = "{http://www.w3.org/2000/svg}"
        path = Path(renderer.__file__).resolve().parents[2] / "assets/profile-avatar.jpg"
        expected = path.read_bytes()
        self.assertEqual(hashlib.sha256(expected).hexdigest(), "19a99e5853bc9337a224a2fdfc4063d70020817cb9d2a5085d5bdd91586f0d6e")
        self.assertIn("assets/profile-avatar.jpg", contracts.GENERATOR_SOURCE_FILES)
        for mobile in (False, True):
            root = ET.fromstring(render_svg({"username": "jguida941"}, mobile=mobile))
            images = list(root.iter(ns+"image"))
            self.assertEqual(len(images), 1)
            self.assertEqual(base64.b64decode(images[0].get("href").split(",", 1)[1]), expected)
            with patch.object(Path, "is_file", return_value=False):
                with self.assertRaises(FileNotFoundError):
                    render_svg({"username": "jguida941"}, mobile=mobile)
                for username in ("", "another-user"):
                    other = ET.fromstring(render_svg({"username": username}, mobile=mobile))
                    self.assertEqual(list(other.iter(ns+"image")), [])

    def test_project_status_passthrough_and_semantic_icon_owners(self):
        from datetime import date
        from scripts.contracts.dashboard_summary import build_dashboard_summary
        from scripts.rendering.generate_dashboard_summary import SEMANTIC_ICONS
        rows = [{"name": "one", "status": "active"}, {"name": "two", "status": "maintained"}, {"name": "three"}]
        summary = build_dashboard_summary({"spotlight_data": rows}, profile_date=date(2026, 10, 8))
        self.assertEqual([r.get("status") for r in summary["projects"]], ["active", "maintained", None])
        for identity, glyph in (("inventory.private_owned", "lock"), ("inventory.public_nonfork", "globe"), ("activity.public_commits", "commit"), ("calendar.current_streak", "fire")):
            self.assertEqual(SEMANTIC_ICONS[identity], glyph)

    def test_common_focus_metadata_and_short_window_truth(self):
        ns = "{http://www.w3.org/2000/svg}"
        details = ("Python · pushed 2 hours ago", "C++ · pushed 2 hours ago", "ci-cd-hub · 2 hours ago")
        summary = {"focus": {key: [{"title": "A genuinely long title "*8, "detail": detail}] for key, detail in zip(("now", "next", "updates"), details)}}
        for mobile in (False, True):
            root = ET.fromstring(render_svg(summary, mobile=mobile))
            painted = ["".join(n.itertext()) for n in root.iter(ns+"text")]
            for detail in details:
                self.assertIn(detail, painted)
            self.assertNotIn("Last 12 months", painted)
            self.assertIn("Developer Analytics · Backend", painted)



class DashboardMetricCellTests(unittest.TestCase):
    def test_fact_header_value_and_qualifications_share_one_inset(self):
        from scripts.rendering.generate_dashboard_summary import Canvas
        from scripts.contracts.dashboard_summary import _fact
        ns="{http://www.w3.org/2000/svg}"
        fact=_fact("activity.public_commits",None,"Public commits","public")
        for mobile in (False,True):
            canvas=Canvas(mobile)
            bottom=canvas.fact(fact,18,20,140,qualify=True)
            root=ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg">'+''.join(canvas.parts)+'</svg>')
            box=next(n for n in root.iter(ns+"rect") if n.get("data-role")=="metric-cell")
            ink=list(root.iter(ns+"text"))
            value=next(n for n in ink if n.get("data-role")=="value")
            headers=[n for n in ink if float(n.get("y"))<float(value.get("y"))]
            self.assertEqual(" ".join(n.text for n in headers),"Public commits")
            self.assertEqual(value.text,"n/a")
            self.assertIn("Unavailable",[n.text for n in ink])
            self.assertEqual(float(box.get("height")),bottom-20)
            for node in ink:
                self.assertGreaterEqual(float(node.get("font-size")),14)
                self.assertGreaterEqual(float(node.get("x")),28)
                self.assertLess(float(node.get("y")),bottom)

    def test_mobile_metric_grid_keeps_odd_cell_width_and_aligned_values(self):
        from scripts.rendering.generate_dashboard_summary import Canvas
        from scripts.contracts.dashboard_summary import _fact
        ns="{http://www.w3.org/2000/svg}"
        facts=[_fact("inventory."+str(i),i,label,"public") for i,label in enumerate(("public non-fork repos","private owned repos","stargazers"))]
        canvas=Canvas(True)
        canvas.fact_grid(facts,34,20,292,columns=2)
        root=ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg">'+''.join(canvas.parts)+'</svg>')
        boxes=[n for n in root.iter(ns+"rect") if n.get("data-role")=="metric-cell"]
        values=[n for n in root.iter(ns+"text") if n.get("data-role")=="value"]
        self.assertEqual(len(boxes),3)
        self.assertEqual({float(n.get("width")) for n in boxes},{140})
        self.assertEqual(boxes[0].get("y"),boxes[1].get("y"))
        self.assertEqual(boxes[0].get("height"),boxes[1].get("height"))
        self.assertEqual(values[0].get("y"),values[1].get("y"))



class DashboardFlatOverviewTests(unittest.TestCase):
    def test_only_selected_five_owners_are_flat_and_active_label_is_one_line(self):
        ns="{http://www.w3.org/2000/svg}"
        from scripts.contracts.dashboard_summary import _fact
        summary={"facts":[_fact("activity.active_repos_7d",8,"active repos","owned",status="exact")]}
        flat={"calendar.total","inventory.public_nonfork","inventory.private_owned","inventory.stargazers","activity.active_repos_7d"}
        for mobile in (False,True):
            root=ET.fromstring(render_svg(summary,mobile=mobile))
            owners=[n for n in root.iter() if n.get("data-metric-id")]
            self.assertEqual(len(owners),13)
            for owner in owners:
                cells=[n for n in owner.iter(ns+"rect") if n.get("data-role")=="metric-cell"]
                self.assertEqual(len(cells),0 if owner.get("data-metric-id") in flat else 1)
            active=next(n for n in owners if n.get("data-metric-id")=="activity.active_repos_7d")
            label=next(n for n in active.iter(ns+"text") if n.text=="active repos")
            value=next(n for n in active.iter(ns+"text") if n.get("data-role")=="value")
            self.assertEqual(label.get("font-size"),"14")
            self.assertEqual(value.text,"8")
            self.assertEqual(value.get("font-size"),"42")
            self.assertAlmostEqual(float(label.get("y"))-float(value.get("y")),24)
            window=next(n for n in active.iter(ns+"text") if n.text=="last 7 days")
            self.assertAlmostEqual(float(window.get("y"))-float(label.get("y")),19)
            self.assertEqual(list(active.iter(ns+"path")), [])

    def test_calendar_copy_preserves_original_context_and_unknown_progress_warning(self):
        import copy
        from scripts.contracts.dashboard_summary import _fact
        ns="{http://www.w3.org/2000/svg}"
        benign="Last date may be in progress"
        for status in ("exact","ok","unknown","partial","unavailable"):
            fact=_fact("calendar.current_streak",4,"current observed streak","calendar",status=status,qualification=benign)
            fact.update(profile_date_cutoff="2026-10-08",range_start="2026-10-05",range_end="2026-10-08")
            summary={"facts":[fact]}
            original=copy.deepcopy(summary)
            for mobile in (False,True):
                root=ET.fromstring(render_svg(summary,mobile=mobile))
                owner=next(n for n in root.iter() if n.get("data-metric-id")=="calendar.current_streak")
                paint=" ".join(n.text or "" for n in owner.iter(ns+"text"))
                context=" ".join(n.text or "" for n in owner.iter(ns+"title"))
                self.assertIn("Current streak",paint)
                self.assertEqual(benign in paint,status not in ("exact","ok"))
                self.assertIn(benign,context)
                self.assertIn("current observed streak",context)
                self.assertIn("2026-10-08",context)
                self.assertIn("2026-10-05",paint)
            self.assertEqual(summary,original)



class DashboardCalendarLabelMeasureTests(unittest.TestCase):
    def test_calendar_grid_measures_the_painted_short_headers(self):
        from scripts.rendering.generate_dashboard_summary import Canvas
        from scripts.contracts.dashboard_summary import _fact
        ns="{http://www.w3.org/2000/svg}"
        facts=[_fact(key,4,label,"calendar",status="exact") for key,label in (("calendar.current_streak","current observed streak"),("calendar.longest_streak","longest observed streak"),("calendar.active_days","active days"))]
        canvas=Canvas(False)
        canvas.fact_grid(facts,28,20,784,columns=3)
        root=ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg">'+''.join(canvas.parts)+'</svg>')
        for owner in (n for n in root.iter() if n.get("data-metric-id")):
            ink=list(owner.iter(ns+"text"))
            label,value=ink[0],next(n for n in ink if n.get("data-role")=="value")
            self.assertEqual(float(value.get("y"))-float(label.get("y")),29)



class DashboardShortInventoryLabelsTests(unittest.TestCase):
    def test_short_labels_preserve_values_scopes_and_input(self):
        import copy
        ns = "{http://www.w3.org/2000/svg}"
        facts = [_fact("inventory.public_nonfork", 56, "public non-fork repos", "public-owned-nonfork-profile-included"),
                 _fact("inventory.private_owned", 203, "private owned repos", "private-owned-including-forks")]
        summary = {"facts": facts}
        original = copy.deepcopy(summary)
        for mobile in (False, True):
            root = ET.fromstring(render_svg(summary, mobile=mobile))
            for fact, label in zip(facts, ("public repos", "private repos")):
                owner = next(n for n in root.iter() if n.get("data-metric-id") == fact["metric_id"])
                painted = [n.text for n in owner.iter(ns+"text")]
                self.assertEqual(" ".join(painted[:-1]), label)
                self.assertEqual(painted[-1], fact["display_value"])
                context = " ".join(n.text or "" for n in owner.iter(ns+"title"))
                self.assertIn(fact["label"], context)
                self.assertIn(fact["population_id"], context)
        self.assertEqual(summary, original)



class DashboardHeaderScaleTests(unittest.TestCase):
    def test_header_numbers_are_larger_without_scaling_avatar_or_other_facts(self):
        ns = "{http://www.w3.org/2000/svg}"
        for mobile in (False, True):
            root = ET.fromstring(render_svg({"username": "jguida941"}, mobile=mobile))
            image = next(root.iter(ns+"image"))
            self.assertEqual(image.get("width"), "64" if mobile else "104")
            self.assertEqual(image.get("height"), image.get("width"))
            for owner in (n for n in root.iter() if n.get("data-metric-id")):
                key = owner.get("data-metric-id")
                value = next(n for n in owner.iter(ns+"text") if n.get("data-role")=="value")
                expected = 56 if key=="calendar.total" else 29 if key in ("inventory.public_nonfork","inventory.private_owned","inventory.stargazers") else 42 if key=="activity.active_repos_7d" else 25
                self.assertEqual(float(value.get("font-size")), expected)

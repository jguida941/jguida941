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
            self.assertEqual(sections,["overview","weekly","rhythm","languages","automation","working","focus","project-activity","recent-pushes","projects","metrics","calendar"])
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
        for identity, glyph in (("inventory.private_owned", "lock"), ("inventory.public_total", "globe"), ("activity.public_commits", "commit"), ("calendar.current_streak", "fire")):
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
        facts=[_fact("inventory."+str(i),i,label,"public") for i,label in enumerate(("public repos","private owned repos","stargazers"))]
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



class WorkingProjectionIsolationTests(unittest.TestCase):
    def test_raw_recent_updates_and_metadata_fallback_keep_latest_push(self):
        from tests.pipeline.test_compute_metrics_accuracy import ProfileRecentWorkTests
        model, profile, _, _, stamps = ProfileRecentWorkTests().scenario()
        raw = next(row for row in model["recent_repos"] if row["name"] == "jguida941")
        self.assertEqual(stamps[0], raw["pushed_at"])
        self.assertEqual(stamps[0], profile["pushed_at"])
        hint = next(row for row in model["activity_analytics"]["recent_pushes"]["rows"]
                    if row["repository"] == "jguida941/jguida941")
        self.assertEqual(stamps[0], hint["timestamp"])
        work = next(row for row in model["dashboard_summary"]["working"] if row["name"] == "jguida941")
        self.assertEqual(stamps[1], work["pushed_at"])
        self.assertNotEqual(raw["pushed_at"], work["pushed_at"])

    def test_standalone_working_card_uses_the_same_filtered_rows(self):
        from unittest.mock import patch
        from tests.pipeline.test_compute_metrics_accuracy import ProfileRecentWorkTests, AccuracyTests
        from scripts.pipeline import render_outputs
        model, _, _, _, stamps = ProfileRecentWorkTests().scenario()
        captured = []
        class CapturedWorking(Exception):
            pass
        def capture(rows):
            captured.extend(rows)
            raise CapturedWorking()
        with patch.object(render_outputs, "gen_badges"), patch.object(render_outputs, "gen_lang_chart"), \
                patch.object(render_outputs, "gen_working", side_effect=capture):
            with self.assertRaises(CapturedWorking):
                render_outputs.generate_assets(AccuracyTests()._collected(), model, logger=lambda *args: None)
        self.assertEqual(["pub1", "jguida941"], [row["name"] for row in captured])
        self.assertEqual(stamps[1], captured[1]["pushed_at"])
        self.assertEqual([(row["name"], row["pushed_at"]) for row in model["dashboard_summary"]["working"]],
                         [(row["name"], row["pushed_at"]) for row in captured])


class ProfileRecentWorkFreshnessTests(unittest.TestCase):
    def test_newer_push_invalidates_an_older_refresh_selection(self):
        import copy
        from datetime import datetime, timedelta
        from tests.pipeline.test_compute_metrics_accuracy import ProfileRecentWorkTests
        from scripts.pipeline.compute_metrics import _build_recent_repos
        _, profile, observed, _, _ = ProfileRecentWorkTests().scenario(change=None)
        old = copy.deepcopy(observed)
        proof = old["profile_recent_work"]
        now = datetime.fromisoformat(proof["observed_at"].replace("Z", "+00:00"))
        for field in ("observed_at", "window_start", "window_end"):
            stamp = datetime.fromisoformat(proof[field].replace("Z", "+00:00"))
            proof[field] = (stamp - timedelta(hours=2)).isoformat().replace("+00:00", "Z")
        profile["latest_commit_message"] = "Implement the next source change"
        rows, _ = _build_recent_repos([profile], now - timedelta(days=7), {}, False,
                                     activity_observations=old)
        self.assertEqual(["jguida941"], [row["name"] for row in rows])
        self.assertEqual(profile["pushed_at"], rows[0]["pushed_at"])
        self.assertEqual(profile["latest_commit_message"], rows[0]["last_commit_msg"])

    def test_current_refresh_evidence_control(self):
        from datetime import datetime, timedelta
        from tests.pipeline.test_compute_metrics_accuracy import ProfileRecentWorkTests
        from scripts.pipeline.compute_metrics import _build_recent_repos
        _, profile, observed, _, _ = ProfileRecentWorkTests().scenario(change=None)
        now = datetime.fromisoformat(observed["observed_at"].replace("Z", "+00:00"))
        rows, _ = _build_recent_repos([profile], now - timedelta(days=7), {}, False,
                                     activity_observations=observed)
        self.assertEqual([], rows)


class DashboardFlatOverviewTests(unittest.TestCase):
    def test_only_selected_five_owners_are_flat_and_active_label_is_one_line(self):
        ns="{http://www.w3.org/2000/svg}"
        from scripts.contracts.dashboard_summary import _fact
        summary={"facts":[_fact("activity.working_repos_7d",8,"active repos","owned",status="exact")]}
        flat={"profile.contributions","inventory.public_total","inventory.private_owned","inventory.stargazers","activity.working_repos_7d"}
        for mobile in (False,True):
            root=ET.fromstring(render_svg(summary,mobile=mobile))
            owners=[n for n in root.iter() if n.get("data-metric-id")]
            self.assertEqual(len(owners),13)
            for owner in owners:
                cells=[n for n in owner.iter(ns+"rect") if n.get("data-role")=="metric-cell"]
                self.assertEqual(len(cells),0 if owner.get("data-metric-id") in flat else 1)
            active=next(n for n in owners if n.get("data-metric-id")=="activity.working_repos_7d")
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
        facts = [_fact("inventory.public_total", 56, "public repos", "public-owned-including-forks"),
                 _fact("inventory.private_owned", 203, "private owned repos", "private-owned-including-forks")]
        summary = {"facts": facts}
        original = copy.deepcopy(summary)
        for mobile in (False, True):
            root = ET.fromstring(render_svg(summary, mobile=mobile))
            for fact, label in zip(facts, ("public repos", "private repos")):
                owner = next(n for n in root.iter() if n.get("data-metric-id") == fact["metric_id"])
                labels = [n.text for n in owner.iter(ns+"text") if n.get("data-role") != "value"]
                values = [n.text for n in owner.iter(ns+"text") if n.get("data-role") == "value"]
                self.assertEqual(" ".join(labels), label)
                self.assertEqual(values, [fact["display_value"]])
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
                expected = 46 if key=="profile.contributions" else 29 if key in ("inventory.public_total","inventory.private_owned","inventory.stargazers") else 42 if key=="activity.working_repos_7d" else 25
                self.assertEqual(float(value.get("font-size")), expected)


class CodeChangeSvgTests(unittest.TestCase):
    def test_chart_keeps_focus_and_signed_proportional_bars(self):
        import xml.etree.ElementTree as ET
        from scripts.rendering.generate_dashboard_summary import render_svg
        from scripts.pipeline.activity_analytics import build_activity_analytics
        from tests.pipeline.test_compute_metrics_accuracy import CodeChangeAggregationTests
        data=build_activity_analytics(CodeChangeAggregationTests.source())
        # The normal contract fixture supplies unchanged surrounding sections.
        from tests.pipeline.test_compute_metrics_accuracy import AccuracyTests
        from scripts.pipeline.compute_metrics import compute_profile_model
        model=compute_profile_model(AccuracyTests()._collected(),logger=lambda *_:None,allow_network_calls=False)
        summary={**model['dashboard_summary'],'activity_analytics':data}
        for mobile in (False,True):
            tree=ET.fromstring(render_svg(summary,mobile=mobile))
            sections=[n.get('data-section') for n in tree.iter() if n.get('data-section')]
            self.assertEqual(sections.index('focus')+1,sections.index('code-changes'))
            self.assertEqual(sections.index('code-changes')+1,sections.index('project-activity'))
            self.assertEqual(sections.index('project-activity')+1,sections.index('recent-pushes'))
            self.assertEqual(sections.index('recent-pushes')+1,sections.index('projects'))
            bars=[n for n in tree.iter() if n.get('data-role')=='code-change-bar']
            self.assertEqual(4,len(bars))
            import math
            ratios=[float(n.get('height'))/(int(n.get('data-value')) if mobile else math.log1p(int(n.get('data-value')))) for n in bars]
            self.assertLess(max(ratios)-min(ratios),.001)
            zeros=[float(n.get('y'))+(float(n.get('height')) if n.get('data-kind')=='additions' else 0) for n in bars]
            self.assertLess(max(zeros)-min(zeros),.001)
            self.assertEqual({'#9ece6a','#f7768e'},{n.get('fill') for n in bars})


class CodeChangeDesktopPresentationTests(unittest.TestCase):
    @staticmethod
    def summary(count=30):
        from datetime import date, timedelta
        start = date(2025, 10, 12)
        daily = [{"date": str(start+timedelta(days=i)), "additions": (i % 5)+1,
                  "deletions": (i % 3)+1, "complete": True} for i in range(count)]
        daily[-1]["additions"] = 6970
        daily[1].update(additions=None, deletions=None, complete=False)
        code = {"repository": "owner/project", "ref": "refs/heads/develop", "head_sha": "a"*40,
                "status": "partial", "complete": False, "daily": daily,
                "additions": sum(row["additions"] or 0 for row in daily),
                "deletions": sum(row["deletions"] or 0 for row in daily)}
        return {"activity_analytics": {"window_start": str(start)+"T00:00:00Z",
                "window_end": str(start+timedelta(days=count-1))+"T17:00:00Z",
                "current_day_partial": True, "code_changes": code}}

    @staticmethod
    def chart(summary):
        tree = ET.fromstring(render_svg(summary))
        return next(node for node in tree.iter() if node.get("data-section") == "code-changes")

    def test_desktop_has_compact_context_legend_and_readable_common_scale(self):
        import math
        from scripts.core.config import DASHBOARD_SUMMARY_COLORS
        summary = self.summary()
        chart = self.chart(summary)
        ink = list(chart.iter("{http://www.w3.org/2000/svg}text"))
        paint = " ".join(node.text or "" for node in ink)
        bars = [node for node in chart.iter() if node.get("data-role") == "code-change-bar"]
        panel = next(node for node in chart.iter() if node.get("data-role") == "panel")
        self.assertLessEqual(float(panel.get("height")), 440)
        self.assertGreaterEqual(min(float(node.get("height")) for node in bars), 3)
        self.assertGreaterEqual(max(float(node.get("height")) for node in bars), 100)
        scale = [float(node.get("height"))/math.log1p(int(node.get("data-value"))) for node in bars]
        self.assertAlmostEqual(min(scale), max(scale), places=5)
        for label in ("Last 30 days", "today partial", "partial data", "Log scale", "Additions", "Deletions"):
            self.assertIn(label, paint)
        for internal in ("Inspected", "Selection limited", "non-merge commits", "activity_incomplete"):
            self.assertNotIn(internal, paint)
        identity = next(node for node in ink if (node.text or "").startswith("Latest observed pushed branch"))
        self.assertIn("owner/project · develop · aaaaaaa", identity.text)
        self.assertEqual(identity.get("fill"), DASHBOARD_SUMMARY_COLORS["muted"])
        self.assertEqual(identity.get("font-weight"), "400")
        for key, sign in (("additions", "+"), ("deletions", "−")):
            total = next(node for node in ink if node.text == f"{sign}{summary['activity_analytics']['code_changes'][key]:,}")
            self.assertGreater(float(total.get("x")), float(panel.get("x"))+float(panel.get("width"))*.55)
            self.assertLess(float(total.get("y")), float(panel.get("y"))+65)
        self.assertIn("refs/heads/develop", " ".join(chart.itertext()))
        self.assertIn("a"*40, " ".join(chart.itertext()))

    def test_supplied_ranges_group_without_losing_observed_counts(self):
        import copy
        from datetime import date, timedelta
        for count in (7, 30, 365):
            with self.subTest(days=count):
                summary = self.summary(count)
                original = copy.deepcopy(summary)
                chart = self.chart(summary)
                paint = " ".join(node.text or "" for node in chart.iter("{http://www.w3.org/2000/svg}text"))
                self.assertIn(f"Last {count} days", paint)
                bars = [node for node in chart.iter() if node.get("data-role") == "code-change-bar"]
                self.assertLessEqual(len({node.get("data-date") for node in bars}), 60)
                self.assertGreaterEqual(min(float(node.get("width")) for node in bars), 5)
                for kind in ("additions", "deletions"):
                    self.assertEqual(sum(int(node.get("data-value")) for node in bars if node.get("data-kind") == kind),
                                     summary["activity_analytics"]["code_changes"][kind])
                if count == 365:
                    self.assertIn("7-day totals", paint)
                    self.assertEqual(len({node.get("data-date") for node in bars}), 53)
                    final = [node for node in bars if node.get("data-date") == str(date(2025, 10, 12)+timedelta(days=364))]
                    self.assertEqual(len(final), 2)
                    self.assertTrue(all(node.get("data-end-date") == node.get("data-date") for node in final))
                else:
                    self.assertNotIn("day totals", paint)
                    self.assertTrue(all(node.get("data-end-date") is None for node in bars))
                self.assertEqual(original, summary)

    def test_unknown_and_zero_buckets_stay_distinct_from_observed_subtotals(self):
        summary = self.summary(365)
        code = summary["activity_analytics"]["code_changes"]
        for row in code["daily"]:
            row.update(additions=None, deletions=None, complete=False)
        for row in code["daily"][7:14]:
            row.update(additions=0, deletions=0, complete=True)
        code["daily"][14].update(additions=1, deletions=7, complete=True)
        code["daily"][15].update(additions=31, deletions=None)
        code.update(additions=32, deletions=7)
        chart = self.chart(summary)
        bars = [node for node in chart.iter() if node.get("data-role") == "code-change-bar"]
        self.assertEqual(sorted((node.get("data-date"), node.get("data-kind"), node.get("data-value")) for node in bars),
                         [("2025-10-26", "additions", "32"), ("2025-10-26", "deletions", "7")])
        self.assertTrue(all("partial" in " ".join(node.itertext()) for node in bars))
        self.assertTrue(all(node.get("data-end-date") == "2025-11-01" for node in bars))

    def test_complete_zero_and_unavailable_context_are_honest(self):
        summary = self.summary()
        data = summary["activity_analytics"]
        code = data["code_changes"]
        code.update(additions=0, deletions=0, complete=True, status="ok")
        for row in code["daily"]:
            row.update(additions=0, deletions=0, complete=True)
        data["current_day_partial"] = False
        chart = self.chart(summary)
        paint = " ".join(node.text or "" for node in chart.iter("{http://www.w3.org/2000/svg}text"))
        self.assertIn("+0", paint)
        self.assertIn("−0", paint)
        self.assertNotIn("partial", paint)
        self.assertFalse(any(node.get("data-role") == "code-change-bar" for node in chart.iter()))
        code.update(additions=None, deletions=None, status="unavailable", complete=False, daily=[])
        data.update(window_start=None, window_end=None)
        chart = self.chart(summary)
        paint = " ".join(node.text or "" for node in chart.iter("{http://www.w3.org/2000/svg}text"))
        self.assertIn("Observation window unavailable", paint)
        self.assertIn("Code changes unavailable", paint)
        self.assertNotIn("+0", paint)
        self.assertFalse(any(node.get("data-role") == "code-change-bar" for node in chart.iter()))


    def test_supplied_year_preserves_proportional_bars_and_exact_totals(self):
        """The real desktop README SVG uses the same annual magnitude semantics."""
        import math
        for count in (365, 366):
            with self.subTest(days=count):
                summary = self.summary(count)
                code = summary["activity_analytics"]["code_changes"]
                for row in code["daily"]:
                    row.update(additions=0, deletions=0, complete=True)
                code["daily"][14].update(additions=100, deletions=50)
                code["daily"][251].update(additions=10000, deletions=5000)
                code.update(additions=10100, deletions=5050, status="ok", complete=True)
                chart = self.chart(summary)
                paint = " ".join(chart.itertext())
                self.assertIn("Proportional scale", paint)
                self.assertNotIn("Log scale", paint)
                bars = [node for node in chart.iter() if node.get("data-role") == "code-change-bar"]
                additions = {int(node.get("data-value")): float(node.get("height"))
                             for node in bars if node.get("data-kind") == "additions"}
                self.assertEqual({100, 10000}, set(additions))
                self.assertGreaterEqual(additions[10000], 115)
                self.assertTrue(math.isclose(.01, additions[100] / additions[10000], rel_tol=1e-9))
                self.assertEqual(10100, sum(int(node.get("data-value")) for node in bars
                                            if node.get("data-kind") == "additions"))
                self.assertEqual(5050, sum(int(node.get("data-value")) for node in bars
                                           if node.get("data-kind") == "deletions"))


class RecentPushSvgProjectionTests(unittest.TestCase):
    """Same observed repository facts rendered independently at desktop and phone widths."""

    @staticmethod
    def _paint(*, mobile, working, recent=None):
        from scripts.rendering.generate_dashboard_summary import Canvas, _recent_pushes
        c = Canvas(mobile)
        from scripts.pipeline.push_activity import qualify_recent_pushes
        source = recent if recent is not None else {"status": "unavailable", "rows": []}
        payload = {"recent_pushes": qualify_recent_pushes(source, working, "2026-10-11T21:00:00Z")}
        end = _recent_pushes(c, 34, 40, 292 if mobile else 752, payload)
        root = ET.fromstring("<svg>" + "".join(c.parts) + "</svg>")
        return root, end

    def test_metadata_fallback_uses_real_reported_repositories_without_invented_totals(self):
        working = [
            {"name": "third", "url": "https://github.com/owner/third", "pushed_at": "2026-10-10T12:00:00Z"},
            {"name": "first", "url": "https://github.com/owner/first", "pushed_at": "2026-10-11T20:00:00Z"},
            {"name": "second", "url": "https://github.com/owner/second", "pushed_at": "2026-10-11T19:00:00Z"},
            {"name": "old", "url": "https://github.com/owner/old", "pushed_at": "2026-10-09T12:00:00Z"},
        ]
        for mobile in (False, True):
            with self.subTest(mobile=mobile):
                root, bottom = self._paint(mobile=mobile, working=working)
                rows = [n for n in root.iter() if n.get("data-role") == "recent-push-row"]
                self.assertEqual(3, len(rows))
                self.assertEqual(["owner/first", "owner/second", "owner/third"],
                                 [row.get("data-repository") for row in rows])
                self.assertGreater(bottom, 0)
                text = " ".join(root.itertext())
                self.assertIn("Reported repository push dates", text)
                self.assertIn("Branch / commits unverified", text)
                self.assertIn("Change totals unavailable", text)
                self.assertFalse(any(n.get("data-role") == "recent-push-diff" for n in root.iter()))
                self.assertNotIn("+0", text)

    def test_forged_force_push_diff_cannot_become_verified_in_either_svg(self):
        row = {"repository": "owner/live", "ref": "refs/heads/feature/test",
               "activity_type": "force_push", "after": "b" * 40, "timestamp": "2026-10-11T19:00:00Z",
               "diff_status": "ok", "additions": 900, "deletions": 2,
               "commits": ["a" * 40, "b" * 40]}
        for mobile in (False, True):
            with self.subTest(mobile=mobile):
                root, _ = self._paint(mobile=mobile, working=[], recent={
                    "status": "ok", "rows": [row]})
                self.assertFalse(any(n.get("data-role") == "recent-push-diff" for n in root.iter()))
                self.assertIn("Code changes not verified", " ".join(root.itertext()))

    def test_verified_event_precedes_repository_metadata_and_keeps_exact_values(self):
        live = {"repository": "owner/live", "ref": "refs/heads/dev",
                "activity_type": "push", "after": "b" * 40, "timestamp": "2026-10-11T20:00:00Z",
                "diff_status": "ok", "additions": 42, "deletions": 3,
                "commits": ["a" * 40, "b" * 40]}
        for mobile in (False, True):
            root, _ = self._paint(mobile=mobile,
                                  working=[{"name": "other", "url": "https://github.com/owner/other",
                                            "pushed_at": "2026-10-11T20:00:00Z"}],
                                  recent={"status": "ok", "rows": [live]})
            text = " ".join(root.itertext())
            self.assertIn("owner/live", text)
            self.assertNotIn("owner/other", text)
            self.assertIn("+42", text)
            self.assertIn("−3", text)

    def test_invalid_metadata_url_or_future_hint_cannot_fill_panel(self):
        rows = [
            {"name": "fake", "url": "https://github.com/other/nope", "pushed_at": "2026-10-11T20:00:00Z"},
            {"name": "future", "url": "https://github.com/owner/future", "pushed_at": "2026-10-12T20:00:00Z"},
            {"name": "valid", "url": "https://github.com/owner/valid", "pushed_at": "2026-10-11T20:00:00Z"},
        ]
        root, _ = self._paint(mobile=True, working=rows)
        subjects = [n.get("data-repository") for n in root.iter() if n.get("data-role") == "recent-push-row"]
        self.assertEqual(["owner/valid"], subjects)


    def test_known_empty_and_unavailable_are_distinct_in_both_svgs(self):
        for mobile in (False, True):
            with self.subTest(mobile=mobile):
                zero, _ = self._paint(
                    mobile=mobile, working=[],
                    recent={"status": "ok", "complete": True, "rows": []})
                text = " ".join(zero.itertext())
                self.assertIn("Complete observation", text)
                self.assertIn("No recent pushes observed", text)
                self.assertNotIn("Recent pushes unavailable", text)
                unknown, _ = self._paint(
                    mobile=mobile, working=[],
                    recent={"status": "partial", "complete": False, "rows": []})
                unknown_text = " ".join(unknown.itertext())
                self.assertIn("Recent pushes unavailable", unknown_text)
                self.assertNotIn("No recent pushes observed", unknown_text)
                incomplete_ok, _ = self._paint(
                    mobile=mobile, working=[],
                    recent={"status": "ok", "complete": False, "rows": []})
                incomplete_text = " ".join(incomplete_ok.itertext())
                self.assertIn("Recent pushes unavailable", incomplete_text)
                self.assertNotIn("No recent pushes observed", incomplete_text)


class ProjectActivitySvgTests(unittest.TestCase):
    @staticmethod
    def activity(empty=False):
        from scripts.pipeline.activity_analytics import build_activity_analytics
        from tests.pipeline.test_compute_metrics_accuracy import (
            project_activity_envelope, project_activity_event, project_activity_source,
        )
        rows = [project_activity_envelope("static" + str(index), [] if empty else [
            project_activity_event("day" + str(index), repository="static" + str(index), branch="feature/day"),
            project_activity_event("previous" + str(index), repository="static" + str(index), when="2026-10-10T06:00:00Z"),
        ]) for index in range(9)]
        return build_activity_analytics(project_activity_source(rows))

    def test_both_sizes_read_the_same_default_cells_and_shared_scale(self):
        from scripts.core.config import PROJECT_ACTIVITY_COLORS
        activity = self.activity()
        model = activity["project_activity"]
        expected = {(row["repository"], day["date"]): day for row in model["rows"][:8] for day in row["daily"][-14:]}
        for mobile in (False, True):
            with self.subTest(mobile=mobile):
                root = ET.fromstring(render_svg({"activity_analytics": activity}, mobile=mobile))
                sections = [node.get("data-section") for node in root.iter() if node.get("data-section")]
                self.assertEqual(["code-changes", "project-activity", "recent-pushes"],
                                 sections[sections.index("project-activity")-1:sections.index("project-activity")+2])
                section = next(node for node in root.iter() if node.get("data-section") == "project-activity")
                cells = [node for node in section.iter() if node.get("data-role") == "project-activity-cell"]
                self.assertEqual(8 * 14, len(cells))
                self.assertEqual([row["repository"] for row in model["rows"][:8]],
                                 [node.get("data-repository") for node in section.iter() if node.get("data-role") == "project-activity-row"])
                self.assertFalse(any(node.get("data-role") == "project-activity-branch" for node in section.iter()))
                self.assertFalse(any(node.tag.endswith("script") for node in section.iter()))
                for cell in cells:
                    day = expected[cell.get("data-repository"), cell.get("data-date")]
                    self.assertEqual(None if day["count"] is None else str(day["count"]), cell.get("data-count"))
                    self.assertEqual(str(day["complete"]).lower(), cell.get("data-complete"))
                    self.assertEqual(None if day["level"] is None else str(day["level"]), cell.get("data-level"))
                    self.assertEqual("none" if day["level"] is None else PROJECT_ACTIVITY_COLORS[day["level"]], cell.get("fill"))
                    # Marker geometry follows the current circular-dot direction below;
                    # this shared-fact test remains independent of SVG primitive choice.
                    self.assertIn(day["date"] + " UTC", " ".join(cell.itertext()))
                legend = next(node for node in section.iter() if node.get("data-role") == "project-activity-legend")
                bands = [node for node in legend.iter() if node.get("data-lower") is not None]
                self.assertEqual([(band["lower"], band["upper"], band["level"]) for band in model["scale"]["bands"]],
                                 [(int(node.get("data-lower")), int(node.get("data-upper")), int(node.get("data-level"))) for node in bands])
                self.assertIn(model["meaning"], " ".join(section.itertext()))

    def test_small_circular_activity_markers_and_compact_copy(self):
        """The compact dot view keeps full meaning outside the visible summary copy."""
        activity = self.activity()
        family = activity["project_activity"]
        for mobile in (False, True):
            with self.subTest(mobile=mobile):
                tree = ET.fromstring(render_svg({"activity_analytics": activity}, mobile=mobile))
                section = next(node for node in tree.iter() if node.get("data-section") == "project-activity")
                cells = [node for node in section.iter() if node.get("data-role") == "project-activity-cell"]
                legend = next(node for node in section.iter() if node.get("data-role") == "project-activity-legend")
                keys = [node for node in legend.iter() if node.tag.rsplit("}", 1)[-1] in ("rect", "circle")]
                descriptions = " ".join(node.text or "" for node in section.iter()
                                        if node.tag.rsplit("}", 1)[-1] in ("desc", "title"))
                problems = []
                for node in cells:
                    if node.tag.rsplit("}", 1)[-1] != "circle" or float(node.get("r", -1)) != (5 if mobile else 6):
                        problems.append("Day marker is not the small circle")
                for node in keys:
                    if node.tag.rsplit("}", 1)[-1] != "circle" or float(node.get("r", -1)) != 5:
                        problems.append("Legend marker is not the small circle")
                for field in ("meaning", "qualification", "observed_at"):
                    if family[field] not in descriptions:
                        problems.append("Full description is missing " + field)
                row_nodes = {node for row in section.iter() if row.get("data-role") == "project-activity-row" for node in row.iter()}
                legend_nodes = set(legend.iter())
                context = [node.text or "" for node in section.iter()
                           if node.tag.rsplit("}", 1)[-1] == "text" and node not in row_nodes | legend_nodes
                           and node.get("data-role") != "project-activity-date"
                           and node.text not in ("Project activity", "Repository")]
                if len(context) > 2 or len([word for word in " ".join(context).split() if any(char.isalnum() for char in word)]) > 14:
                    problems.append("Visible context is not compact")
                if "Explore observed branches on the website" in context:
                    problems.append("Repeated website footer remains visible")
                self.assertEqual([], problems)

    def test_zero_unavailable_and_default_neighbor_selection(self):
        import copy
        for mobile in (False, True):
            with self.subTest(mobile=mobile):
                empty = ET.fromstring(render_svg({"activity_analytics": self.activity(empty=True)}, mobile=mobile))
                section = next(node for node in empty.iter() if node.get("data-section") == "project-activity")
                self.assertIn("No push events observed in this window", " ".join(section.itertext()))
                self.assertIn("No positive push counts to scale", " ".join(section.itertext()))
                unknown = ET.fromstring(render_svg({}, mobile=mobile))
                section = next(node for node in unknown.iter() if node.get("data-section") == "project-activity")
                self.assertIn("Project activity unavailable", " ".join(section.itertext()))
                self.assertFalse(any(node.get("data-role") == "project-activity-cell" for node in section.iter()))
                baseline = CodeChangeDesktopPresentationTests.summary()
                changed = copy.deepcopy(baseline)
                changed["activity_analytics"]["overall_code_changes"] = {"schema": "profile-owned-code-analytics/v1", "status": "unavailable"}
                changed["activity_analytics"]["project_activity"] = self.activity()["project_activity"]
                code = lambda value: next(node for node in ET.fromstring(render_svg(value, mobile=mobile)).iter() if node.get("data-section") == "code-changes")
                self.assertEqual(ET.tostring(code(baseline)), ET.tostring(code(changed)))

    def test_readme_has_an_ordinary_project_activity_link_after_picture(self):
        from pathlib import Path
        from tests.contracts.test_web_dashboard import ROOT
        template = (Path(ROOT) / "templates" / "README.md.tpl").read_text()
        picture_end = template.index("</picture>")
        link = template.index("[Project activity details]")
        self.assertLess(picture_end, link)
        self.assertLess(link, template.index("<details>"))
        self.assertIn("#project-activity)", template[link:])
        self.assertIn("project activity by repository and UTC day", template[:picture_end])


"""Ordinary guards for source-qualified personal inventory counts."""
import copy
from contextlib import ExitStack
from datetime import datetime, timezone
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET


def inventory_fixture_model(mode="complete", *, zero=False, calendar_query=None):
    from tests.pipeline.test_compute_metrics_accuracy import AccuracyTests
    from scripts.pipeline import collect_data as collector
    from scripts.pipeline.compute_metrics import compute_profile_model
    from scripts.github import github_client as gh
    base = AccuracyTests()._collected()
    public = [] if zero else copy.deepcopy(base.repos)
    private = [] if zero else copy.deepcopy(base.private_repos)
    for index, row in enumerate(public + private, 1):
        row.update(id=index, full_name=f"{gh.USERNAME}/{row['name']}")
    all_public = copy.deepcopy(public)
    if not zero:
        fork = {**copy.deepcopy(public[1]), "id": 99, "name": "fork-example", "fork": True,
                "full_name": f"{gh.USERNAME}/fork-example", "html_url": f"https://github.com/{gh.USERNAME}/fork-example",
                "stargazers_count": 999}
        all_public.append(fork)
    if mode == "fork-only":
        public, private, all_public = [], [], [fork]
    counts = {"public_owned_total": len(all_public), "public_owned_nonfork": len(public),
              "public_owned_forks": len(all_public) - len(public), "private_owned": len(private),
              "private_owned_nonfork": len(private)}
    if mode == "retained-private":
        counts.update(private_owned=None, private_owned_nonfork=None)
    added = ({**copy.deepcopy(public[1]), "id": 101, "name": "new-public", "stargazers_count": 7,
              "full_name": f"{gh.USERNAME}/new-public", "html_url": f"https://github.com/{gh.USERNAME}/new-public"}
             if mode == "fresh-change" else None)

    def scope_counts(*, fresh=False):
        if fresh and mode == "fresh-unavailable":
            raise RuntimeError("fresh census unavailable")
        result = dict(counts)
        if fresh and mode in ("count-mismatch", "fresh-change"):
            result["public_owned_total"] += 1
            result["public_owned_nonfork"] += 1
        return result

    def repositories(include_forks=False, *, fresh=False):
        rows = copy.deepcopy(all_public if include_forks else public)
        if fresh and added:
            rows.append(copy.deepcopy(added))
        if fresh and mode == "unobserved-stars" and rows:
            rows[0]["stargazers_count_observed"] = False
        return rows

    canonical = {f"{gh.USERNAME}/{row['name']}": row for row in all_public + private}
    if added:
        canonical[added["full_name"]] = added
    class Response:
        status_code = 200
        headers = {}
        def __init__(self, value):
            self.value = value
        def json(self):
            return copy.deepcopy(self.value)
    def current_repository(url, **kwargs):
        locator = str(url).split("/repos/", 1)[1]
        row = copy.deepcopy(canonical[locator])
        if mode == "unobserved-stars":
            row["stargazers_count_observed"] = False
        return Response(row)
    missing = {"status": "unavailable", "value": None}
    with ExitStack() as stack:
        for name, effect in (
            ("get_owned_repo_scope_counts", scope_counts), ("get_repos", repositories),
            ("get_private_repos", lambda **_: copy.deepcopy(private)),
            ("get_all_languages", lambda *_: copy.deepcopy(base.language_bytes)),
            ("get_events_observation", lambda: copy.deepcopy(missing)),
            ("get_total_commits_observation", lambda *_a, **_k: copy.deepcopy(missing)),
            ("get_releases_last_n_days_observation", lambda *_a, **_k: copy.deepcopy(missing)),
            ("get_merged_prs_last_n_days_observation", lambda *_a, **_k: copy.deepcopy(missing)),
            ("get_repos_with_ci", lambda *_: 0),
            ("get_contribution_calendar_observation", lambda: copy.deepcopy(missing)),
            ("get_profile_contributions_observation", lambda: copy.deepcopy(missing)),
            ("_request_with_retry", current_repository),
            ("paginated_get", lambda *_a, **_k: []),
        ):
            if calendar_query is None or name not in {"get_contribution_calendar_observation", "get_profile_contributions_observation"}:
                stack.enter_context(patch.object(gh, name, side_effect=effect))
        if calendar_query is None:
            stack.enter_context(patch.object(gh, "get_default_contribution_calendar_observation", return_value=copy.deepcopy(missing), create=True))
        else:
            stack.enter_context(patch.object(gh, "_graphql_query", side_effect=calendar_query))
            stack.enter_context(patch.object(gh, "_get_cached", return_value=None))
            stack.enter_context(patch.object(gh, "_set_cached"))
        for name, value in (("_read_previous_snapshot", {"snapshot": {"private_owned_repos": 200}}),
                            ("collect_activity_observations", {}), ("collect_profile_ci_runs", {}),
                            ("detect_token_mode", "none"), ("detect_cache_mode", {})):
            stack.enter_context(patch.object(collector, name, return_value=value))
        if hasattr(collector, "collect_public_ci_timeline"):
            stack.enter_context(patch.object(collector, "collect_public_ci_timeline", return_value={}))
        stack.enter_context(patch("requests.sessions.Session.request", side_effect=AssertionError("Unexpected live network")))
        collected = collector.collect_profile_data(logger=lambda *_: None)
        # These controls target the shared census admission boundary. The private
        # collector also validates canonical identities earlier; corrupting its
        # input would exercise that distinct boundary instead of this one.
        if mode in ("missing-fork", "duplicate-full-census", "foreign-owner"):
            from dataclasses import replace
            evidence = copy.deepcopy(collected.inventory_evidence)
            rows = copy.deepcopy(evidence["all_public_repos"])
            evidence["all_public_repos"] = rows
            if mode == "missing-fork":
                evidence["all_public_repos"] = [row for row in rows if not row["fork"]]
            elif mode == "duplicate-full-census":
                rows[-1] = copy.deepcopy(rows[0])
            else:
                rows[-1]["owner"] = {"login": "semverity-labs"}
            collected = replace(collected, inventory_evidence=evidence)
        return compute_profile_model(collected, logger=lambda *_: None, allow_network_calls=False)


class InventoryVerificationTests(unittest.TestCase):
    @staticmethod
    def facts(model):
        return {row["metric_id"]: row for row in model["dashboard_summary"]["facts"]
                if row["metric_id"].startswith("inventory.")}

    def test_fresh_matching_personal_census_qualifies_total_and_distinct_nonfork_counts(self):
        for zero in (False, True):
            model = inventory_fixture_model(zero=zero)
            facts = self.facts(model)
            self.assertEqual(["exact"] * 5, [row["quality"]["status"] for row in facts.values()])
            self.assertEqual([0, 0, 0, 0, 0] if zero else [4, 3, 1, 3, 1], [row["value"] for row in facts.values()])
            self.assertIn("inventory_observation", model["dashboard_data"])

    def test_unavailable_fresh_census_does_not_certify_retained_counts(self):
        from tests.pipeline.test_compute_metrics_accuracy import AccuracyTests
        from scripts.pipeline.compute_metrics import compute_profile_model
        model = compute_profile_model(AccuracyTests()._collected(), logger=lambda *_: None, allow_network_calls=False)
        facts = self.facts(model)
        self.assertTrue(all(row["quality"]["status"] == "unknown" for row in facts.values()))

    def test_previous_private_count_remains_reported(self):
        facts = self.facts(inventory_fixture_model("retained-private"))
        self.assertEqual(200, facts["inventory.private_owned"]["value"])
        self.assertEqual("unknown", facts["inventory.private_owned"]["quality"]["status"])

    def test_source_value_mismatch_does_not_certify_a_cached_count(self):
        facts = self.facts(inventory_fixture_model("count-mismatch"))
        self.assertEqual("unknown", facts["inventory.public_nonfork"]["quality"]["status"])
        self.assertEqual("unknown", facts["inventory.public_forks"]["quality"]["status"])

    def test_complete_fresh_census_updates_cached_inventory_values_together(self):
        model = inventory_fixture_model("fresh-change")
        facts = self.facts(model)
        self.assertEqual(4, model["snapshot"]["total_repos"])
        self.assertEqual(5, model["snapshot"]["public_repos_total"])
        self.assertEqual(4, model["data_scope"]["public_owned_nonfork_repos_total"])
        self.assertEqual(10, model["snapshot"]["total_stars"])
        self.assertEqual(4, facts["inventory.public_nonfork"]["value"])
        self.assertTrue(all(row["quality"]["status"] == "exact" for row in facts.values()))

    def test_public_headline_counts_forks_without_changing_nonfork_or_received_stars(self):
        model = inventory_fixture_model()
        facts = self.facts(model)
        self.assertEqual(4, facts["inventory.public_total"]["value"])
        self.assertEqual(3, facts["inventory.public_nonfork"]["value"])
        self.assertEqual(3, facts["inventory.stargazers"]["value"])
        self.assertEqual(3, model["snapshot"]["total_repos"])
        self.assertEqual(4, model["snapshot"]["public_repos_total"])

    def test_all_public_headline_needs_its_own_complete_current_row_census(self):
        for mode in ("missing-fork", "duplicate-full-census", "foreign-owner"):
            with self.subTest(mode=mode):
                facts = self.facts(inventory_fixture_model(mode))
                self.assertNotEqual("exact", facts["inventory.public_total"]["quality"]["status"])
                self.assertEqual("exact", facts["inventory.public_nonfork"]["quality"]["status"])

    def test_fork_only_account_has_public_headline_and_zero_nonfork_inventory(self):
        facts = self.facts(inventory_fixture_model("fork-only"))
        self.assertEqual(1, facts["inventory.public_total"]["value"])
        self.assertEqual(0, facts["inventory.public_nonfork"]["value"])
        self.assertEqual(0, facts["inventory.stargazers"]["value"])
        self.assertEqual("exact", facts["inventory.public_total"]["quality"]["status"])

    def test_missing_star_evidence_does_not_taint_observed_repository_count(self):
        facts = self.facts(inventory_fixture_model("unobserved-stars"))
        self.assertEqual("unknown", facts["inventory.stargazers"]["quality"]["status"])
        self.assertEqual("exact", facts["inventory.public_nonfork"]["quality"]["status"])

    def test_renderer_uses_quality_status_in_both_sizes(self):
        from scripts.rendering.generate_dashboard_summary import render_svg
        from scripts.contracts.dashboard_summary import _fact
        for status, phrase in (("exact", "Verified from GitHub"), ("unknown", "Reported inventory")):
            facts = [_fact(identity, 1, identity, "fixture", status=status, qualification=phrase)
                     for identity in ("inventory.public_total", "inventory.public_nonfork", "inventory.private_owned", "inventory.stargazers", "inventory.public_forks")]
            for mobile in (False, True):
                root = ET.fromstring(render_svg({"facts": facts}, mobile=mobile))
                overview = next(node for node in root.iter() if node.get("data-section") == "overview")
                text = " ".join(overview.itertext()).casefold()
                if status == "exact":
                    self.assertNotIn("unverified", text)
                else:
                    self.assertIn("unverified", text)

    def test_copied_verified_evidence_cannot_certify_a_different_value(self):
        from datetime import date
        from scripts.contracts.dashboard_summary import build_dashboard_summary
        model = inventory_fixture_model()
        model["snapshot"]["total_stars"] += 10
        summary = build_dashboard_summary(model, profile_date=date.today())
        stars = next(row for row in summary["facts"] if row["metric_id"] == "inventory.stargazers")
        self.assertEqual("unknown", stars["quality"]["status"])

    def test_wrong_population_or_naive_time_cannot_be_verified(self):
        from datetime import date
        from scripts.contracts.dashboard_summary import build_dashboard_summary
        for changed in ({"population_id": "organization-union"}, {"observed_at": "2026-11-15"}):
            model = inventory_fixture_model()
            observation = model["dashboard_data"].get("inventory_observation", {})
            observation.update(changed)
            summary = build_dashboard_summary(model, profile_date=date.today())
            self.assertTrue(all(row["quality"]["status"] != "exact" for row in summary["facts"]
                                if row["metric_id"].startswith("inventory.")))


class InventoryCurrentnessTests(unittest.TestCase):
    def _facts(self, model):
        from scripts.contracts.dashboard_summary import build_dashboard_summary
        summary = build_dashboard_summary(model, profile_date=datetime.now(timezone.utc).date())
        return {row["metric_id"]: row for row in summary["facts"] if row["metric_id"].startswith("inventory.")}

    def test_inventory_time_outside_current_collection_stays_unverified(self):
        for stamp in ("2000-01-01T00:00:00Z", "2100-01-01T00:00:00Z"):
            with self.subTest(stamp=stamp):
                model = inventory_fixture_model()
                model["dashboard_data"]["inventory_observation"]["observed_at"] = stamp
                self.assertEqual(["unknown"] * 5, [row["quality"]["status"] for row in self._facts(model).values()])

    def test_compute_does_not_refresh_from_old_or_future_evidence(self):
        from scripts.pipeline import compute_metrics
        real_compute = compute_metrics.compute_profile_model
        for stamp in ("2000-01-01T00:00:00Z", "2100-01-01T00:00:00Z"):
            with self.subTest(stamp=stamp):
                def substituted(collected, *args, **kwargs):
                    collected.inventory_evidence["observed_at"] = stamp
                    return real_compute(collected, *args, **kwargs)
                with patch.object(compute_metrics, "compute_profile_model", side_effect=substituted):
                    model = inventory_fixture_model("fresh-change")
                self.assertEqual(["unknown"] * 5, [row["quality"]["status"] for row in self._facts(model).values()])
                self.assertTrue(all(row["complete"] is False for row in model["dashboard_data"]["inventory_observation"]["metrics"].values()))

    def test_complete_previous_run_census_cannot_certify_new_snapshot(self):
        model = inventory_fixture_model()
        data = model["dashboard_data"]
        previous = copy.deepcopy(data["inventory_observation"])
        previous.update(observed_at="2000-01-01T00:00:01Z", snapshot_generated_at="2000-01-01T00:00:02Z")
        data["inventory_observation"] = previous
        data["collection_started_at"] = "2000-01-01T00:00:00Z"
        self.assertEqual(["unknown"] * 5, [row["quality"]["status"] for row in self._facts(model).values()])

    def test_missing_or_naive_run_bounds_cannot_certify_inventory(self):
        for key in ("collection_started_at", "generated_at"):
            for value in (None, "2026-11-15T00:00:00"):
                with self.subTest(key=key, value=value):
                    model = inventory_fixture_model()
                    model["dashboard_data"][key] = value
                    self.assertEqual(["unknown"] * 5, [row["quality"]["status"] for row in self._facts(model).values()])

    def test_same_observation_in_another_zone_remains_exact(self):
        from datetime import timedelta
        model = inventory_fixture_model()
        observation = model["dashboard_data"]["inventory_observation"]
        instant = datetime.fromisoformat(observation["observed_at"].replace("Z", "+00:00"))
        observation["observed_at"] = instant.astimezone(timezone(timedelta(hours=5))).isoformat()
        self.assertEqual(["exact"] * 5, [row["quality"]["status"] for row in self._facts(model).values()])

    def test_collection_crossing_midnight_remains_exact(self):
        from scripts.pipeline import collect_data, compute_metrics
        class CollectClock(datetime):
            @classmethod
            def now(cls, tz=None):
                return datetime(2026, 11, 14, 23, 59, 59, tzinfo=timezone.utc).astimezone(tz)
        class GenerateClock(datetime):
            @classmethod
            def now(cls, tz=None):
                return datetime(2026, 11, 15, 0, 0, 1, tzinfo=timezone.utc).astimezone(tz)
        with patch.object(collect_data, "datetime", CollectClock), patch.object(compute_metrics, "datetime", GenerateClock):
            model = inventory_fixture_model()
        self.assertEqual(["exact"] * 5, [row["quality"]["status"] for row in self._facts(model).values()])


class NativeCalendarParityTests(unittest.TestCase):
    """The calendar and headline share GitHub's aggregate without rewriting cells."""

    @staticmethod
    def scenario(*, total=400, count=1):
        from datetime import timedelta
        from dataclasses import replace
        from scripts.github import github_client as gh
        first = datetime(2025, 11, 16, tzinfo=timezone.utc)
        native_days = [{"date": (first + timedelta(days=i)).date().isoformat(),
                        "contributionCount": count, "weekday": (i % 7)} for i in range(365)]
        calls = []
        def query(text, variables):
            calls.append((text, variables))
            rows = copy.deepcopy(native_days)
            aggregate = total
            if "from" in variables:
                start = datetime.fromisoformat(variables["from"].replace("Z", "+00:00"))
                rows = [{**row, "date": (start + timedelta(days=i)).date().isoformat()}
                        for i, row in enumerate(rows)]
                aggregate = sum(row["contributionCount"] for row in rows)
            return {"user": {"contributionsCollection": {
                "startedAt": "2025-11-09T05:00:00Z", "endedAt": "2026-11-16T04:59:59Z",
                "contributionCalendar": {"totalContributions": aggregate,
                                         "weeks": [{"contributionDays": rows}]}}}}
        with patch.object(gh, "_settings", replace(gh._settings, token="test", tokens=("test",))), \
             patch.object(gh, "datetime", wraps=datetime) as clock:
            clock.now.return_value = datetime(2026, 11, 16, 3, 40, tzinfo=timezone.utc)
            model = inventory_fixture_model(calendar_query=query)
        return model, calls, [{"date": row["date"], "count": row["contributionCount"]} for row in native_days]

    def test_default_calendar_and_headline_share_one_response_and_preserve_native_cells(self):
        from scripts.pipeline.profile_pipeline import _current_contribution_calendar
        model, calls, days = self.scenario()
        summary = model["dashboard_summary"]
        facts = {row["metric_id"]: row for row in summary["facts"]}
        self.assertEqual(400, facts["calendar.total"]["value"],
                         "[NATIVE-CALENDAR-PARITY] calendar must use the native aggregate, independent of day sum")
        self.assertEqual(facts["profile.contributions"]["value"], facts["calendar.total"]["value"])
        self.assertEqual(days, summary["calendar"]["days"], "[NATIVE-CALENDAR-PARITY] returned cells must not be rewritten")
        self.assertEqual(1, len(calls), "[NATIVE-CALENDAR-PARITY] one response must supply calendar and headline")
        self.assertEqual({"login"}, set(calls[0][1]))
        self.assertRegex(calls[0][0], r"contributionsCollection\s*\{")
        self.assertNotRegex(calls[0][0], r"contributionsCollection\s*\(")
        self.assertEqual(365, model["contribution_rhythm"]["total"])
        self.assertEqual(365, sum(row["contributions"] for row in model["contribution_rhythm"]["weekdays"]))
        self.assertEqual("known", model["contribution_rhythm"]["completeness"])
        self.assertTrue(model["contribution_rhythm"]["last_day_in_progress"])
        self.assertNotIn("UTC", summary["calendar"]["window"])
        self.assertIn("GitHub", summary["calendar"]["window"])
        self.assertTrue(_current_contribution_calendar(model["dashboard_data"]))
        for mobile in (False, True):
            svg = ET.fromstring(render_svg(summary, mobile=mobile))
            cells = [row for row in svg.iter() if row.get("data-role") == "calendar-cell"]
            self.assertEqual([(row["date"], str(row["count"])) for row in days],
                             [(row.get("data-date"), row.get("data-count")) for row in cells])

    def test_zero_and_additive_native_calendars_still_publish(self):
        from scripts.pipeline.profile_pipeline import _current_contribution_calendar
        for total, count in ((0, 0), (365, 1)):
            with self.subTest(total=total):
                model, _, days = self.scenario(total=total, count=count)
                facts = {row["metric_id"]: row for row in model["dashboard_summary"]["facts"]}
                self.assertEqual(total, facts["calendar.total"]["value"])
                self.assertEqual(days, model["dashboard_summary"]["calendar"]["days"])
                self.assertTrue(_current_contribution_calendar(model["dashboard_data"]))


class OverviewSnapshotLayoutTests(unittest.TestCase):
    """The overview groups facts and dates the saved snapshot, at both sizes."""
    @staticmethod
    def summary(timestamp="2026-11-19T18:02:33Z", value=13583):
        return {"username": "jguida941", "generated_at": timestamp, "facts": [
            _fact("profile.contributions", value, "Contributions", "profile", status="exact"),
            _fact("inventory.public_total", 57, "public repos", "public", status="exact"),
            _fact("inventory.private_owned", 200, "private repos", "private", status="exact"),
            _fact("inventory.stargazers", 60, "stargazers", "public", status="exact"),
        ]}

    def test_overview_places_secondary_facts_beside_primary_and_time_below(self):
        from unittest.mock import patch
        import os
        with patch.dict(os.environ, {"PROFILE_TIMEZONE": "America/New_York"}):
            for mobile in (False, True):
                root = ET.fromstring(render_svg(self.summary(), mobile=mobile))
                overview = next(n for n in root.iter() if n.get("data-section") == "overview")
                groups = {n.get("data-metric-id"): n for n in overview.iter() if n.get("data-metric-id")}
                self.assertEqual(set(groups), {"profile.contributions", "inventory.public_total",
                                               "inventory.private_owned", "inventory.stargazers"})
                values = {key: next(n for n in group.iter() if n.get("data-role") == "value")
                          for key, group in groups.items()}
                self.assertEqual([values[key].text for key in groups], ["13,583", "57", "200", "60"])
                primary = values["profile.contributions"]
                if not mobile:
                    for key in ("inventory.public_total", "inventory.private_owned", "inventory.stargazers"):
                        self.assertGreater(float(values[key].get("x")), float(primary.get("x")) + 250)
                        self.assertLess(abs(float(values[key].get("y")) - float(primary.get("y"))), 60)
                footers = [n for n in overview.iter() if n.get("data-role") == "overview-footer"]
                self.assertEqual(1, len(footers))
                timestamp = next(n for n in footers[0].iter() if n.get("data-role") == "snapshot-time")
                self.assertEqual("Updated Nov 19, 2026, 1:02 PM EST", timestamp.text)
                self.assertGreater(float(timestamp.get("y")), max(float(n.get("y")) for n in values.values()))
                painted = [n.text or "" for n in overview.iter("{http://www.w3.org/2000/svg}text")]
                self.assertEqual(1, sum(text.startswith("Updated ") for text in painted))
                self.assertFalse(any(text.startswith("Snapshot ") for text in painted))
                self.assertFalse(any(n.tag.endswith("}a") for n in overview.iter()))

    def test_snapshot_time_keeps_offset_day_and_dst_meaning(self):
        from unittest.mock import patch
        import os
        cases = [
            ("2026-07-01T01:08:00Z", "Updated Jun 30, 2026, 9:08 PM EDT"),
            ("2026-11-01T05:30:00Z", "Updated Nov 1, 2026, 1:30 AM EDT"),
            ("2026-11-01T06:30:00Z", "Updated Nov 1, 2026, 1:30 AM EST"),
            ("2026-11-19T13:02:33-05:00", "Updated Nov 19, 2026, 1:02 PM EST"),
        ]
        with patch.dict(os.environ, {"PROFILE_TIMEZONE": "America/New_York"}):
            for timestamp, expected in cases:
                for mobile in (False, True):
                    root = ET.fromstring(render_svg(self.summary(timestamp), mobile=mobile))
                    labels = [n.text for n in root.iter() if n.get("data-role") == "snapshot-time"]
                    self.assertEqual([expected], labels)
            for timestamp in (None, "", "invalid", "2026-11-19", "2026-11-19T13:02:33", "2026-02-30T13:00:00Z", "2026-11-19T13:00:00+00:60", "2026-11-19T13:00:00+24:00"):
                root = ET.fromstring(render_svg(self.summary(timestamp)))
                self.assertEqual(["Update time unavailable"], [n.text for n in root.iter() if n.get("data-role") == "snapshot-time"])

    def test_zero_unknown_and_long_counts_are_not_replaced(self):
        import copy
        for mobile in (False, True):
            for value, expected in ((0, "0"), (None, "n/a"), (1234567890, "1,234,567,890")):
                summary = self.summary(value=value)
                before = copy.deepcopy(summary)
                root = ET.fromstring(render_svg(summary, mobile=mobile))
                group = next(n for n in root.iter() if n.get("data-metric-id") == "profile.contributions")
                self.assertEqual(expected, next(n.text for n in group.iter() if n.get("data-role") == "value"))
                self.assertEqual(before, summary)

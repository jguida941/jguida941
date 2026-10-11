"""Red-first WEB DASHBOARD contract — authority: cross-projection parity (Law 3) +
governed Liquid Glass material + a11y. The web dashboard is the second projection of
the one analytics contract and must be GENERATED, never hand-written, so it can't drift
back into a bespoke 1458-line page.

Proves, against the committed site/index.html:
  1. GENERATED — committed bytes == web_render.render_dashboard() (a drift guard: hand
     edits redden; the page can only change by changing the generator + regenerating).
  2. TOKEN PARITY (Law 3, token half) — the page embeds design_tokens.emit_css_root()
     verbatim, so the web :root and the SVG cards share one token source.
  3. PROJECTION PARITY (Law 3) — the web binds the same shared-snapshot metric keys the
     README SVG cards read (hero KPI + the core metrics), driven by the same JSON.
  4. MATERIAL + A11Y — real backdrop-filter glass, a visible-focus ring, reduced-motion
     and reduced-transparency fallbacks (governed material, accessible).
  5. RESTRAINT — colour comes only from token vars (no rainbow of hand-authored hexes
     like the old 9-accent page).
  6. PRIVACY + STATIC-SAFE — never leaks token mode / credentials; no external scripts
     (GitHub Pages safe); the theme switcher offers every theme.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "scripts").is_dir() and (parent / "tests").is_dir():
            return parent
    raise RuntimeError("repo root not found")


ROOT = _repo_root()
INDEX = ROOT / "site" / "index.html"


class WebDashboardContract(unittest.TestCase):
    def setUp(self):
        self.html = INDEX.read_text(encoding="utf-8")

    def test_index_is_generated_not_handwritten(self):
        from scripts.pipeline.web_render import render_dashboard
        self.assertEqual(
            self.html, render_dashboard(),
            "site/index.html is GENERATED — regenerate via scripts.pipeline.web_render and "
            "commit; it must never be hand-edited (run: python -m scripts.pipeline.web_render)")

    def test_token_root_embedded_verbatim(self):
        from scripts.rendering.design_tokens import emit_css_root
        self.assertIn(
            emit_css_root().strip(), self.html,
            "the web :root must be design_tokens.emit_css_root() verbatim (Law 3 token parity)")

    def test_binds_shared_snapshot_metric_keys(self):
        """The web reads the SAME shared-snapshot keys the README SVG cards do."""
        required = (
            "last_year_contributions",  # the hero KPI (shared with the SVG hero)
            "total_repos", "total_stars", "public_scope_commits",
            "ci_coverage_pct", "primary_lang_share_pct", "active_days_last_year",
        )
        missing = [k for k in required if k not in self.html]
        self.assertEqual([], missing, f"web projection must bind shared metric keys; missing: {missing}")

    def test_renders_calendar_and_rhythm_sections(self):
        """The web projection covers the same surfaces as the README, including the
        contribution calendar and the always-visible, qualified weekday rhythm."""
        for needle in ('id="calendar-panel"', 'id="rhythm-panel"',
                       "contribution_calendar", "contribution_rhythm",
                       "Contribution Calendar", "Contribution Rhythm"):
            self.assertIn(needle, self.html, f"web dashboard missing {needle!r}")

    def test_status_conveyed_by_shape_not_hue_alone(self):
        """DESIGN_SPEC 3.6 / 10 (and the README status_chip): pipeline status must read
        by icon-SHAPE AND label, never hue alone — so a desaturated/colour-blind viewer
        still distinguishes OK from failure. The colour belongs in a small glyph, not a
        saturated full-hue pill (the old 'green button' AI tell)."""
        html = self.html
        self.assertIn("STATUS_ICON", html, "web status must resolve an icon SHAPE per state")
        icons = re.search(r"STATUS_ICON\s*=\s*\{(.*?)\};", html, re.S)
        self.assertIsNotNone(icons, "STATUS_ICON map not found")
        shapes = re.findall(r'<path[^>]*\bd="([^"]+)"', icons.group(1))
        self.assertGreaterEqual(len(set(shapes)), 3,
                                "the 3 status states must use 3 DISTINCT shapes (colour-independence)")
        # restraint: the chip LABEL stays neutral ink — colour lives in the glyph, not a
        # full-hue text/pill. So .chip.<state> must NOT repaint the label colour.
        for state in ("ok", "warn", "bad"):
            rule = re.search(r"\.chip\." + state + r"\s*\{([^}]*)\}", html)
            if rule:
                self.assertNotRegex(
                    rule.group(1), r"(^|;)\s*color\s*:",
                    f".chip.{state} must not paint the label a status hue — status reads by shape")

    def test_material_and_accessibility(self):
        for needle in ("backdrop-filter", ":focus-visible",
                       "prefers-reduced-motion", "prefers-reduced-transparency"):
            self.assertIn(needle, self.html, f"web dashboard must include {needle!r}")

    def test_responsive_mobile_and_touch_targets(self):
        """Mobile is a first-class design rule (Apple HIG / WCAG 2.5.5), and renders differ on
        Safari: the page must carry (1) a PHONE breakpoint (<=480px), (2) >=44px touch targets on
        interactive controls, (3) weekday rows that reflow with readable coverage on a narrow screen, and (4) the -webkit- material prefix so frosted glass works on Safari."""
        html = self.html
        self.assertRegex(html, r"@media[^{]*max-width:\s*4[0-8]\dpx", "needs a phone breakpoint (<=480px)")
        self.assertIn("-webkit-backdrop-filter", html, "Safari needs the -webkit-backdrop-filter prefix")
        self.assertIn("min-height: 44px", html, "interactive controls need >=44px touch targets (Apple/WCAG)")
        self.assertIn("grid-template-columns: 3ch minmax(24px, 1fr) auto", html)
        self.assertNotIn('class="rhythm-coverage"', html)
        self.assertIn("<summary>How to read this</summary>", html)
        self.assertIn('id="rhythm-coverage"', html)
        self.assertIn(".rhythm-detail summary { cursor: pointer; min-height: 44px", html)

    def test_colour_only_from_tokens_no_rainbow(self):
        """Restraint: the component CHROME paints from var(--token)/color-mix, never a
        pile of hand hexes (the old 9-accent tell). Hex legitimately lives in exactly
        two injected blocks — the token source (emit_css_root's :root/[data-theme])
        and the LANG_COLORS map (Linguist identity colours, data not chrome). Scrub
        both, then the remaining component CSS + HTML + JS must hold NO raw hex."""
        from scripts.rendering.design_tokens import emit_css_root
        scrubbed = self.html.replace(emit_css_root().strip(), "")
        scrubbed = re.sub(r"const LANG_COLORS = \{.*?\};", "", scrubbed, flags=re.S)
        stray = sorted(set(re.findall(r"#[0-9a-fA-F]{3,8}\b", scrubbed)))
        self.assertEqual([], stray, f"component chrome must paint from token vars, not raw hex: {stray}")

    def test_never_leaks_private_signals(self):
        for banned in ("token_mode", "ghp_", "github_pat_", "Bearer "):
            self.assertNotIn(banned, self.html, f"web dashboard must never contain {banned!r}")

    def test_static_pages_safe_and_offers_every_theme(self):
        from scripts.rendering.design_tokens import THEME_META, THEMES
        self.assertNotIn("<script src=", self.html, "no external scripts (GitHub Pages static-safe)")
        for name in THEMES:
            self.assertIn(f'data-theme-set="{name}"', self.html, f"theme switcher missing {name}")
            self.assertIn(THEME_META[name]["label"], self.html, f"switcher missing label for {name}")



class CodeChangeWebsiteTests(unittest.TestCase):
    def test_code_section_preserves_focus_and_configuration(self):
        from scripts.pipeline.web_render import render_dashboard
        html=render_dashboard()
        self.assertIn('Current Focus',html)
        self.assertIn('Workflow configuration',html)
        self.assertIn('Code changes',html)
        self.assertIn('hydrateCodeChanges(d.activity_analytics)',html)
        self.assertIn('daily.map(d=>',html)
        self.assertNotIn('Most active repositories',html)
        self.assertLess(html.index('Current Focus'),html.index('Code changes'))
        self.assertLess(html.index('Code changes'),html.index('Flagship Projects'))

class CodeChangeHydrationTests(unittest.TestCase):
    @staticmethod
    def activity(count=30):
        from datetime import date, timedelta
        start = date(2025, 10, 12)
        daily = [{"date": str(start+timedelta(days=i)), "additions": 0, "deletions": 0, "complete": True}
                 for i in range(count)]
        for i, additions, deletions in ((0, 1, 1), (count//2, 31, 7), (count-1, 6970, 166)):
            daily[i].update(additions=additions, deletions=deletions)
        daily[1].update(additions=None, deletions=None, complete=False)
        return {"window_start": str(start)+"T00:00:00Z", "window_end": str(start+timedelta(days=count-1))+"T17:00:00Z",
                "current_day_partial": True, "cohort": {"queried": 13, "eligible": 13},
                "code_changes": {"repository": "owner/project", "ref": "refs/heads/develop", "head_sha": "a"*40,
                    "status": "partial", "complete": False, "stats_observed": 13, "commit_count": 15,
                    "excluded_merges": 2, "selection": {"status": "partial", "reason": "activity_incomplete"},
                    "history": {"status": "ok", "reason": "end_of_connection"}, "daily": daily,
                    "additions": sum(row["additions"] or 0 for row in daily),
                    "deletions": sum(row["deletions"] or 0 for row in daily)}}

    def hydrate(self, activity):
        import json
        import subprocess
        import xml.etree.ElementTree as ET
        from html.parser import HTMLParser
        from scripts.pipeline.web_render import render_dashboard
        script = re.findall(r"<script>(.*?)</script>", render_dashboard(), re.S)
        self.assertEqual(len(script), 1)
        harness = r'''
const fs = require('node:fs'), vm = require('node:vm');
const input = JSON.parse(fs.readFileSync(0, 'utf8')), nodes = {};
const idle = {then() {return this;}, catch() {return this;}};
const context = {document: {documentElement: {dataset: {}}, querySelectorAll() {return [];},
  getElementById(id) {return nodes[id] ||= {innerHTML: '', textContent: '', style: {setProperty() {}}, setAttribute() {}, replaceChildren() {}};}},
  location: {hash: '', search: ''}, localStorage: {getItem() {return null;}, setItem() {}},
  URLSearchParams, addEventListener() {}, requestAnimationFrame() {}, fetch() {return idle;}, activity: input.activity};
vm.runInNewContext(input.script + '\nhydrateCodeChanges(activity);', context, {timeout: 5000});
process.stdout.write(JSON.stringify({html: nodes['activity-code'].innerHTML, activity: context.activity}));
'''
        result = subprocess.run(["node", "-e", harness], input=json.dumps({"script": script[0], "activity": activity}),
                                text=True, capture_output=True, check=True, timeout=10)
        observed = json.loads(result.stdout)
        self.assertEqual(activity, observed["activity"])
        class Fragment(HTMLParser):
            def __init__(self):
                super().__init__(convert_charrefs=True)
                self.root = ET.Element("root")
                self.stack = [self.root]
            def handle_starttag(self, tag, attrs):
                node = ET.SubElement(self.stack[-1], tag, dict(attrs))
                if tag not in ("br", "hr", "img", "input", "meta", "link"):
                    self.stack.append(node)
            def handle_startendtag(self, tag, attrs):
                ET.SubElement(self.stack[-1], tag, dict(attrs))
            def handle_endtag(self, tag):
                for index in range(len(self.stack)-1, 0, -1):
                    if self.stack[index].tag == tag:
                        del self.stack[index:]
                        break
            def handle_data(self, value):
                parent = self.stack[-1]
                if len(parent):
                    parent[-1].tail = (parent[-1].tail or "")+value
                else:
                    parent.text = (parent.text or "")+value
        parsed = Fragment()
        parsed.feed(observed["html"])
        return parsed.root

    @staticmethod
    def visible(tree):
        import copy
        visible = copy.deepcopy(tree)
        for parent in visible.iter():
            for child in list(parent):
                if child.tag in ("details", "title"):
                    parent.remove(child)
        return " ".join(visible.itertext())

    @staticmethod
    def bars(tree):
        return [node for node in tree.iter() if node.get("data-role") == "code-change-bar"]

    def test_readable_signed_chart_has_compact_header_and_reachable_details(self):
        import math
        tree = self.hydrate(self.activity())
        paint, bars = self.visible(tree), self.bars(tree)
        self.assertGreaterEqual(min(float(bar.get("height")) for bar in bars), 5)
        self.assertGreaterEqual(max(float(bar.get("height")) for bar in bars), 90)
        ratios = [float(bar.get("height"))/math.log1p(int(bar.get("data-value"))) for bar in bars]
        self.assertAlmostEqual(min(ratios), max(ratios), places=5)
        zeros = [float(bar.get("y"))+(float(bar.get("height")) if bar.get("data-kind") == "additions" else 0) for bar in bars]
        self.assertAlmostEqual(min(zeros), max(zeros), places=5)
        header = tree.find(".//*[@class='code-heading']")
        self.assertIsNotNone(header)
        self.assertIn("Code changes", " ".join(header.itertext()))
        self.assertIsNotNone(header.find(".//*[@class='code-additions']"))
        self.assertIsNotNone(header.find(".//*[@class='code-deletions']"))
        identity = tree.find(".//*[@class='code-branch']")
        self.assertIn("owner/project · develop", " ".join(identity.itertext()))
        for label in ("Last 30 days", "today partial", "partial data", "Log scale", "Additions", "Deletions"):
            self.assertIn(label, paint)
        for diagnostic in ("Inspected", "activity_incomplete", "Summed non-merge", "non-merge commits"):
            self.assertNotIn(diagnostic, paint)
        details = tree.findall(".//details")
        self.assertEqual(len(details), 1)
        self.assertIsNotNone(details[0].find("summary"))
        detail_text = " ".join(details[0].itertext())
        for value in ("13 of 13", "13 of 15", "2 merges excluded", "activity_incomplete", "History: ok", "Summed non-merge", "Missing history is not zero", "a"*40, "6970 additions", "unavailable"):
            self.assertIn(value, detail_text)

    def test_supplied_ranges_keep_observed_totals_and_unknown_bins(self):
        from datetime import date, timedelta
        for count in (7, 30, 365):
            with self.subTest(days=count):
                activity = self.activity(count)
                tree = self.hydrate(activity)
                self.assertIn(f"Last {count} days", self.visible(tree))
                bars = self.bars(tree)
                self.assertLessEqual(len({bar.get("data-date") for bar in bars}), 60)
                for kind in ("additions", "deletions"):
                    self.assertEqual(sum(int(bar.get("data-value")) for bar in bars if (bar.get("data-kind") or bar.get("class")) == kind), activity["code_changes"][kind])
                if count == 365:
                    self.assertIn("7-day totals", self.visible(tree))
                    self.assertTrue(all(bar.get("data-end-date") for bar in bars))
                else:
                    self.assertTrue(all(bar.get("data-end-date") is None for bar in bars))
        activity = self.activity(365)
        code = activity["code_changes"]
        for row in code["daily"]:
            row.update(additions=None, deletions=None, complete=False)
        for row in code["daily"][7:14]:
            row.update(additions=0, deletions=0, complete=True)
        code["daily"][14].update(additions=1, deletions=7, complete=True)
        code["daily"][15].update(additions=31)
        code.update(additions=32, deletions=7)
        bars = self.bars(self.hydrate(activity))
        self.assertEqual(sorted((bar.get("data-date"), bar.get("data-kind"), bar.get("data-value")) for bar in bars),
                         [("2025-10-26", "additions", "32"), ("2025-10-26", "deletions", "7")])
        self.assertTrue(all(bar.get("data-end-date") == "2025-11-01" for bar in bars))
        self.assertTrue(all("partial" in " ".join(bar.itertext()) for bar in bars))

    def test_header_keeps_large_totals_exact(self):
        activity = self.activity()
        code = activity["code_changes"]
        code["daily"][-1].update(additions=10699, deletions=406)
        code.update(additions=10731, deletions=414)
        tree = self.hydrate(activity)
        header = tree.find(".//*[@class='code-heading']")
        self.assertIsNotNone(header)
        paint = " ".join(header.itertext())
        self.assertIn("+10,731", paint)
        self.assertIn("−414", paint)
        self.assertNotIn("+11k", paint)

    def test_complete_zero_and_unavailable_remain_distinct(self):
        activity = self.activity()
        activity["current_day_partial"] = False
        code = activity["code_changes"]
        code.update(additions=0, deletions=0, status="ok", complete=True)
        for row in code["daily"]:
            row.update(additions=0, deletions=0, complete=True)
        tree = self.hydrate(activity)
        paint = self.visible(tree)
        self.assertIn("+0", paint)
        self.assertIn("−0", paint)
        self.assertNotIn("partial", paint)
        self.assertEqual(self.bars(tree), [])
        code.update(additions=None, deletions=None, status="unavailable", complete=False, daily=[])
        activity.update(window_start=None, window_end=None)
        tree = self.hydrate(activity)
        paint = self.visible(tree)
        self.assertIn("Observation window unavailable", paint)
        self.assertIn("Code changes unavailable", paint)
        self.assertNotIn("+0", paint)
        self.assertEqual(self.bars(tree), [])




class P024RecentPushWebsiteTests(unittest.TestCase):
    """Ordinary public-side guards; native method evidence remains separate."""

    @staticmethod
    def _hydrate(activity, working=None):
        import json
        import subprocess
        from scripts.pipeline.web_render import render_dashboard
        script = re.findall(r"<script>(.*?)</script>", render_dashboard(), re.S)
        assert len(script) == 1
        harness = r'''
const fs = require("node:fs"), vm = require("node:vm");
const input = JSON.parse(fs.readFileSync(0, "utf8")), nodes = {};
const idle = {then() {return this;}, catch() {return this;}};
const context = {
  document: {documentElement: {dataset: {}}, querySelectorAll() {return [];},
    getElementById(id) {return nodes[id] ||= {innerHTML: "", textContent: "", style: {setProperty() {}}, setAttribute() {}, replaceChildren() {}};}},
  location: {hash: "", search: ""}, localStorage: {getItem() {return null;}, setItem() {}},
  URLSearchParams, addEventListener() {}, requestAnimationFrame() {}, fetch() {return idle;},
  activity: input.activity,
};
vm.runInNewContext(input.script + "\nhydrateRecentPushes(activity, input.working);", context, {timeout: 5000});
process.stdout.write(JSON.stringify({html: nodes["activity-pushes"].innerHTML, activity: context.activity}));
'''
        result = subprocess.run(["node", "-e", harness],
                                input=json.dumps({"script": script[0], "activity": activity, "working": working}),
                                text=True, capture_output=True, timeout=10, check=True)
        parsed = json.loads(result.stdout)
        assert parsed["activity"] == activity, "hydration must not mutate shared calculations"
        return parsed["html"]

    def test_separate_section_does_not_replace_code_changes(self):
        from scripts.pipeline.web_render import render_dashboard
        html = render_dashboard()
        self.assertIn('id="activity-code"', html)
        self.assertIn('id="activity-pushes"', html)
        self.assertLess(html.index('id="activity-code"'), html.index('id="activity-pushes"'))
        self.assertLess(html.index('id="activity-pushes"'), html.index('id="projects"'))
        self.assertIn("hydrateRecentPushes(d.activity_analytics, d.dashboard_summary?.working, d.generated_at)", html)
        self.assertIn("Workflow configuration", html)

    def test_mobile_recent_push_layout_and_axis_size_are_independent(self):
        from scripts.pipeline.web_render import render_dashboard
        html = render_dashboard()
        self.assertIn(".recent-push-list { grid-template-columns: 1fr; }", html)
        self.assertIn(".recent-push-list { display: grid;", html)
        # P023-WEB-002: oversized phone tick glyphs clipped the minus sign.
        self.assertNotIn(".code-chart text { font-size: 24px; }", html)
        self.assertIn(".code-chart text { font-size: 14px; }", html)

    def test_verified_tree_diff_and_related_commits_are_explicit(self):
        sha_a, sha_b = "a" * 40, "b" * 40
        event = {"repository": "owner/alpha", "activity_type": "push", "ref": "refs/heads/feature/mobile",
                 "timestamp": "2026-10-11T15:30:00Z", "after": sha_b, "id": "push-1",
                 "diff_status": "ok", "additions": 1207, "deletions": 33,
                 "commits": [sha_a, sha_b],
                 "compare_url": "https://github.com/owner/alpha/compare/" + "c" * 40 + "..." + sha_b,
                 "head_url": "https://github.com/owner/alpha/commit/" + sha_b}
        html = self._hydrate({"recent_pushes": {"status": "ok", "complete": True, "rows": [event]}})
        for expected in ("owner/alpha", "feature/mobile", "+1,207", "−33", "2 commits", sha_a[:7], sha_b[:7], "Tree diff"):
            self.assertIn(expected, html)
        self.assertIn("github.com/owner/alpha/commit/", html)

    def test_unverified_partial_and_unavailable_never_invent_zero(self):
        row = {"repository": "owner/beta", "ref": "refs/heads/dev",
               "timestamp": "2026-10-11T14:20:00Z", "after": "c" * 40,
               "id": "push-2", "diff_status": "unavailable",
               "additions": None, "deletions": None, "commits": [],
               "head_url": "https://github.com/owner/beta/commit/" + "c" * 40}
        html = self._hydrate({"recent_pushes": {"status": "partial", "complete": False, "rows": [row]}})
        self.assertIn("owner/beta", html)
        self.assertIn("Observation incomplete", html)
        self.assertIn("Change totals unverified", html)
        self.assertNotIn("+0", html)
        self.assertNotIn("−0", html)
        none = self._hydrate({"recent_pushes": {"status": "unavailable", "complete": False, "rows": []}})
        self.assertIn("Recent pushes unavailable", none)

    def test_force_push_and_duplicate_repository_cannot_fake_verified_rows(self):
        head = "b" * 40
        source = {"repository": "owner/alpha", "activity_type": "force_push",
                  "ref": "refs/heads/dev", "timestamp": "2026-10-11T15:30:00Z",
                  "after": head, "id": "event1", "diff_status": "ok",
                  "additions": 888, "deletions": 2, "commits": ["a" * 40, head]}
        html = self._hydrate({"recent_pushes": {
            "status": "ok", "complete": True, "rows": [source, {**source, "id": "event2"}]}})
        self.assertEqual(1, html.count('data-repository="owner/alpha"'))
        self.assertIn("Change totals unverified", html)
        self.assertNotIn("+888", html)
        self.assertNotIn("Tree diff", html)

    def test_real_repository_metadata_fallback_keeps_unknowns_unverified(self):
        working = [
            {"name": "older", "url": "https://github.com/owner/older", "pushed_at": "2026-10-09T12:00:00Z"},
            {"name": "newer", "url": "https://github.com/owner/newer", "pushed_at": "2026-10-11T12:00:00Z"},
            {"name": "middle", "url": "https://github.com/owner/middle", "pushed_at": "2026-10-10T12:00:00Z"},
            {"name": "last", "url": "https://github.com/owner/last", "pushed_at": "2026-10-08T12:00:00Z"},
        ]
        html = self._hydrate({"recent_pushes": {"status": "unavailable", "complete": False, "rows": []}}, working)
        self.assertEqual(3, html.count('class="recent-push-item"'))
        self.assertLess(html.index("owner/newer"), html.index("owner/middle"))
        self.assertLess(html.index("owner/middle"), html.index("owner/older"))
        self.assertNotIn("owner/last", html)
        self.assertIn("Reported repository push dates", html)
        self.assertIn("Branch and push commits not verified", html)
        self.assertNotIn("Tree diff", html)
        self.assertNotIn("+0", html)

    def test_verified_events_take_precedence_over_repo_metadata(self):
        head = "a" * 40
        ev = {"repository": "owner/actual", "ref": "refs/heads/dev", "after": head,
              "activity_type": "push", "diff_status": "unavailable",
              "timestamp": "2026-10-11T12:00:00Z"}
        metadata = [{"name": "other", "url": "https://github.com/owner/other",
                     "pushed_at": "2026-10-11T13:00:00Z"}]
        html = self._hydrate({"recent_pushes": {"status": "partial", "rows": [ev]}}, metadata)
        self.assertIn("owner/actual", html)
        self.assertNotIn("owner/other", html)
        self.assertNotIn("Reported repository push dates", html)

    def test_metadata_fallback_rejects_hostile_url_and_false_timestamps(self):
        rows = [
            {"name": "attack", "url": "javascript:alert(1)", "pushed_at": "2026-10-11T12:00:00Z"},
            {"name": "attack2", "url": "https://github.com/evil/attack3", "pushed_at": "2026-10-11T12:00:00Z"},
            {"name": "good", "url": "https://github.com/owner/good", "pushed_at": "2026-10-11T12:00:00Z"},
            {"name": "future", "url": "https://github.com/owner/future", "pushed_at": "invalid-time"},
        ]
        html = self._hydrate({"recent_pushes": {"status": "unavailable", "rows": []}}, rows)
        self.assertEqual(1, html.count('class="recent-push-item"'))
        self.assertIn("owner/good", html)
        self.assertNotIn("javascript:", html)
        self.assertNotIn("attack3", html)

    def test_untrusted_markup_cannot_become_dom_or_url(self):
        row = {"repository": "owner/<svg/onload=alert(1)>",
               "ref": "refs/heads/<img src=x>", "id": "hack",
               "timestamp": "2026-10-11T14:20:00Z", "after": "d" * 40,
               "diff_status": "unavailable", "commits": []}
        html = self._hydrate({"recent_pushes": {"status": "partial", "rows": [row]}})
        self.assertNotIn("<img", html)
        self.assertNotIn("<svg", html)
        self.assertNotIn("javascript:", html)
        self.assertNotIn("href=\"https://github.com/owner/<", html)


if __name__ == "__main__":
    unittest.main()

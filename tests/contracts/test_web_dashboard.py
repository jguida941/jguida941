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

import copy
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
import json
import os
import shutil
import subprocess
from unittest.mock import patch
from tests.github.test_github_client import _profile_headline_observation

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
            "profile.contributions", "calendar.total",  # independent native headline and calendar
            "inventory.public_total", "total_stars", "public_scope_commits",
            "ci_coverage_pct", "primary_lang_share_pct", "calendar.active_days",
        )
        missing = [k for k in required if k not in self.html]
        self.assertEqual([], missing, f"web projection must bind shared metric keys; missing: {missing}")

    def test_renders_calendar_and_rhythm_sections(self):
        """The web projection covers the same surfaces as the README, including the
        contribution calendar and the always-visible, qualified weekday rhythm."""
        for needle in ('id="calendar-panel"', 'id="rhythm-panel"',
                       "selectedCalendar?.calendar", "contribution_rhythm",
                       "Contribution Calendar", "Contribution Rhythm"):
            self.assertIn(needle, self.html, f"web dashboard missing {needle!r}")


    def test_ci_index_receipt_is_pinned_and_no_overflow_at_true_390(self):
        """An actual 390px browser probe must agree with the committed index."""
        import hashlib
        import json
        from scripts.quality.headless_receipts import dom_probe_artifact, provenance_path

        artifact = dom_probe_artifact("index")
        self.assertTrue(artifact.is_file())
        data = json.loads(artifact.read_text(encoding="utf-8"))
        sidecar = json.loads(provenance_path(artifact).read_text(encoding="utf-8"))
        self.assertEqual(390, data.get("client_width"))
        self.assertEqual(390, data.get("viewport", {}).get("width"))
        self.assertFalse(data.get("horizontal_overflow"), data.get("offenders"))
        self.assertEqual(0, data.get("uncontained_offender_count"))
        self.assertEqual(
            hashlib.sha256(INDEX.read_bytes()).hexdigest(),
            sidecar.get("page_sha256"),
            "CI panel changed the page: recapture the 390px receipt",
        )

    def test_contribution_hydration_uses_only_the_shared_accepted_summary(self):
        """Execute the emitted page with deliberately disagreeing legacy values."""
        import json
        import shutil
        import subprocess
        from html.parser import HTMLParser
        from scripts.pipeline.web_render import render_dashboard
        if shutil.which("node") is None:
            self.skipTest("Node required to exercise emitted contribution hydration")
        class Elements(HTMLParser):
            def __init__(self):
                super().__init__()
                self.rows = []
            def handle_starttag(self, tag, attributes):
                row = dict(attributes)
                if row.get("id") or row.get("data-bind") or row.get("data-calendar-fact"):
                    self.rows.append(row)
        html = render_dashboard()
        parser = Elements()
        parser.feed(html)
        script = re.findall(r"<script>(.*?)</script>", html, re.S)[0]
        harness = r'''
const fs=require('node:fs'), vm=require('node:vm');
const input=JSON.parse(fs.readFileSync(0,'utf8'));
const element=(attrs={})=>({attrs,children:[],hidden:false,textContent:'',innerHTML:'',dataset:{},
  style:{setProperty(){}},classList:{add(){},remove(){},toggle(){}},
  append(...xs){this.children.push(...xs)},replaceChildren(){this.children=[];this.innerHTML=''},
  getAttribute(k){return Object.hasOwn(this.attrs,k)?this.attrs[k]:null},
  setAttribute(k,v){this.attrs[k]=v},addEventListener(){},querySelector(){return null},
  querySelectorAll(){return []}});
const elements=input.elements.map(element), byId=new Map(elements.filter(e=>e.attrs.id).map(e=>[e.attrs.id,e]));
const doc={documentElement:element(),createElement(){return element()},
  getElementById(id){if(!byId.has(id))byId.set(id,element({id}));return byId.get(id)},
  querySelector(){return null},querySelectorAll(selector){
    const m=/^\[([^\]]+)\]$/.exec(selector);return m?elements.filter(e=>Object.hasOwn(e.attrs,m[1])):[]}};
const idle={then(){return this},catch(){return this}};
const ctx={document:doc,location:{hash:'',search:''},localStorage:{getItem(){return null},setItem(){}},
  URLSearchParams,addEventListener(){},requestAnimationFrame(){},fetch(){return idle},sample:input.sample};
vm.runInNewContext(input.script+'\nhydrate(sample);',ctx,{timeout:5000});
const hero=elements.find(e=>(e.attrs.class||'').split(' ').includes('kpi-value'));
const active=elements.filter(e=>e.attrs['data-bind']==='scorecard.active_days_last_year'||e.attrs['data-calendar-fact']==='calendar.active_days');
process.stdout.write(JSON.stringify({hero:hero.textContent,active:active.map(e=>e.textContent),
  total:doc.getElementById('cal-total').textContent,cells:doc.getElementById('cal').innerHTML,
  status:doc.getElementById('calendar-status').textContent}));
'''
        for available in (True, False):
            sample = {
                "snapshot": {"last_year_contributions": 999},
                "scorecard": {"active_days_last_year": 999},
                "contribution_calendar": {"total": 999, "weeks": [[{"date": "2026-11-15", "count": 999}]]},
            }
            if available:
                sample["dashboard_summary"] = {
                    "facts": [{"metric_id": key, "value": value, "display_value": str(value),
                               "window": "2026-11-15 – 2026-11-15 · UTC", "quality": {"status": "exact"}}
                              for key, value in (("profile.contributions", 11), ("calendar.total", 7), ("calendar.active_days", 1))],
                    "calendar": {"status": "exact", "window": "2026-11-15 – 2026-11-15 · UTC",
                                 "days": [{"date": "2026-11-15", "count": 7}]},
                }
            result = subprocess.run(["node", "-e", harness],
                                    input=json.dumps({"script": script, "elements": parser.rows, "sample": sample}),
                                    text=True, capture_output=True, timeout=10, check=True)
            shown = json.loads(result.stdout)
            with self.subTest(available=available):
                self.assertEqual("11" if available else "n/a", shown["hero"])
                self.assertEqual(["1", "1"] if available else ["n/a", "n/a"], shown["active"])
                self.assertNotIn("999", json.dumps(shown))
                if available:
                    self.assertEqual("7 contributions", shown["total"])
                    self.assertIn("2026-11-15: 7", shown["cells"])
                else:
                    self.assertEqual("", shown["cells"])
                    self.assertEqual("Contribution calendar unavailable", shown["status"])

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
        pile of hand hexes (the old 9-accent tell). Hex lives in the shared root
        tokens, the component-scoped project intensity palette, and the LANG_COLORS
        map (Linguist identity colours, data not chrome). Outside those exact
        injected blocks, component CSS + HTML + JS must hold NO raw hex."""
        from scripts.rendering.design_tokens import emit_css_root, emit_project_activity_css
        scrubbed = self.html.replace(emit_css_root().strip(), "")
        scrubbed = scrubbed.replace(emit_project_activity_css().strip(), "")
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


    def test_signed_chart_axis_ticks_keep_theme_font_headroom(self):
        """Mobile and desktop use the same actual SVG geometry, not a mock chart."""
        for days, peak in ((30, 100000), (365, 100000), (30, 100000000)):
            with self.subTest(days=days, peak=peak):
                activity = self.activity(days)
                last = activity["code_changes"]["daily"][-1]
                last.update(additions=peak, deletions=peak, complete=True)
                activity["code_changes"].update(additions=peak, deletions=peak)
                svg = self.hydrate(activity).find(".//svg")
                self.assertIsNotNone(svg)
                self.assertEqual("0 0 640 300", svg.get("viewbox"))
                ticks = [node for node in svg.iter("text")
                         if node.get("data-role") == "code-y-tick"]
                self.assertEqual(5, len(ticks))
                negative = [node for node in ticks if (node.text or "").startswith("−")]
                self.assertEqual(2, len(negative))
                for node in negative:
                    # 14 units/character is conservative for the existing
                    # .code-chart text rule, including the minus sign.
                    self.assertGreaterEqual(
                        float(node.get("x")) - 14 * len(node.text), 12,
                        f"signed Y-axis label clips: {node.text}",
                    )
                bars = self.bars(self.hydrate(activity))
                self.assertTrue(bars)
                self.assertTrue(all(float(b.get("x")) >= 0 and
                                    float(b.get("x")) + float(b.get("width")) <= 632
                                    for b in bars))

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



    def test_supplied_year_keeps_proportional_change_sizes(self):
        """Render through the actual website hydrator and retain relative values."""
        for count in (365, 366):
            with self.subTest(days=count):
                activity = self.activity(count)
                code = activity["code_changes"]
                for row in code["daily"]:
                    row.update(additions=0, deletions=0, complete=True)
                code["daily"][14].update(additions=100, deletions=50)
                code["daily"][251].update(additions=10000, deletions=5000)
                code.update(additions=10100, deletions=5050, status="ok", complete=True)
                tree = self.hydrate(activity)
                paint = self.visible(tree)
                self.assertIn("Proportional scale", paint)
                self.assertNotIn("Log scale", paint)
                bars = self.bars(tree)
                additions = {int(node.get("data-value")): float(node.get("height"))
                             for node in bars if node.get("data-kind") == "additions"}
                self.assertEqual({100, 10000}, set(additions))
                self.assertGreaterEqual(additions[10000], 115)
                self.assertAlmostEqual(.01, additions[100] / additions[10000], places=6)
                self.assertEqual(10100, sum(int(node.get("data-value")) for node in bars
                                            if node.get("data-kind") == "additions"))
                self.assertEqual(5050, sum(int(node.get("data-value")) for node in bars
                                           if node.get("data-kind") == "deletions"))
                self.assertEqual(2, len([node for node in tree.iter("text")
                                         if node.get("data-role") == "code-y-tick"
                                         and (node.text or "").startswith("−")]))


class P024RecentPushWebsiteTests(unittest.TestCase):
    """Ordinary public-side guards; native method evidence remains separate."""

    @staticmethod
    def _hydrate(activity, working=None, generated_at="2026-10-11T21:00:00Z"):
        if working is not None:
            from scripts.pipeline.push_activity import qualify_recent_pushes
            activity = {**activity, "recent_pushes": qualify_recent_pushes(
                activity.get("recent_pushes"), working, generated_at)}
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
vm.runInNewContext(input.script + "\nhydrateRecentPushes(activity);", context, {timeout: 5000});
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
        self.assertIn("hydrateRecentPushes(d.activity_analytics)", html)
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

    def test_cutoff_alias_and_valid_control_match_shared_model(self):
        state = {"recent_pushes": {"status": "unavailable", "rows": []}}
        hints = [
            {"name": "repo", "url": "https://github.com/owner/repo", "pushed_at": "2026-10-11T18:00:00Z"},
            {"name": "repo", "url": "https://github.com/OWNER/repo", "pushed_at": "2026-10-11T20:00:00Z"},
            {"name": "future", "url": "https://github.com/owner/future", "pushed_at": "2099-01-01T20:00:00Z"},
            {"name": "naive", "url": "https://github.com/owner/naive", "pushed_at": "2026-10-11T20:00:00"},
        ]
        good = self._hydrate(state, hints)
        self.assertEqual(1, good.count('class="recent-push-item"'))
        self.assertIn("OWNER/repo", good)
        self.assertNotIn("owner/future", good)
        self.assertNotIn("owner/naive", good)
        for cutoff in (None, "invalid"):
            with self.subTest(cutoff=cutoff):
                denied = self._hydrate(state, hints, generated_at=cutoff)
                self.assertIn("Recent pushes unavailable", denied)
                self.assertNotIn("OWNER/repo", denied)

    def test_known_empty_is_not_mislabeled_unavailable(self):
        known = self._hydrate({"recent_pushes": {"status": "ok", "complete": True, "rows": []}},
                              working=[])
        self.assertIn("Complete observation", known)
        self.assertIn("No recent pushes observed", known)
        self.assertNotIn("Recent pushes unavailable", known)
        partial = self._hydrate({"recent_pushes": {"status": "partial", "complete": False, "rows": []}},
                                working=[])
        self.assertIn("Recent pushes unavailable", partial)
        self.assertNotIn("No recent pushes observed", partial)
        incomplete_ok = self._hydrate(
            {"recent_pushes": {"status": "ok", "complete": False, "rows": []}}, working=[])
        self.assertIn("Recent pushes unavailable", incomplete_ok)
        self.assertNotIn("No recent pushes observed", incomplete_ok)

    def test_rejected_raw_row_cannot_masquerade_as_complete_zero(self):
        raw = {"status": "ok", "complete": True, "rows": [
            {"repository": "owner/<img>", "activity_type": "repository_metadata",
             "metadata_only": True, "timestamp": "2026-10-11T20:00:00Z"}]}
        html = self._hydrate({"recent_pushes": raw})
        self.assertIn("Recent pushes unavailable", html)
        self.assertNotIn("No recent pushes observed", html)
        self.assertNotIn("<img>", html)


class ProjectActivityWebsiteTests(unittest.TestCase):
    """The repository panel reads shared facts and owns only its own hydration."""

    def hydrate(self, activity, **options):
        import json
        import subprocess
        from html.parser import HTMLParser
        from scripts.pipeline.web_render import render_dashboard

        script = re.findall(r"<script>(.*?)</script>", render_dashboard(), re.S)
        self.assertEqual(1, len(script))
        harness = r'''
const fs = require('node:fs'), vm = require('node:vm');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const nodes = {'activity-code': {innerHTML:'graph already hydrated'}, 'activity-pushes': {innerHTML:'push details already expanded'}};
const idle = {then() {return this;}, catch() {return this;}};
const context = {document: {documentElement:{dataset:{}}, querySelectorAll() {return [];}, querySelector() {return null;},
  getElementById(id) {return nodes[id] ||= {innerHTML:'', querySelectorAll() {return [];}, querySelector() {return null;}};}},
  location:{hash:'',search:''}, localStorage:{getItem() {return null;},setItem() {}}, URLSearchParams,
  addEventListener() {}, requestAnimationFrame() {}, fetch() {return idle;}, activity:input.activity, options:input.options};
vm.runInNewContext(input.script + '\nhydrateProjectActivity(activity); projectDays = options.days || 14; projectShowAll = options.show_all === true; (options.expanded || []).forEach(repository => projectExpanded.add(repository)); renderProjectActivity();', context, {timeout:5000});
process.stdout.write(JSON.stringify({html:nodes['activity-project'].innerHTML, code:nodes['activity-code'].innerHTML,
  pushes:nodes['activity-pushes'].innerHTML, activity:context.activity}));
'''
        result = subprocess.run(["node", "-e", harness], text=True, capture_output=True,
                                input=json.dumps({"script": script[0], "activity": activity, "options": options}),
                                check=True, timeout=10)
        value = json.loads(result.stdout)
        self.assertEqual(activity, value["activity"])
        self.assertEqual("graph already hydrated", value["code"])
        self.assertEqual("push details already expanded", value["pushes"])

        class Fragment(HTMLParser):
            def __init__(self):
                super().__init__(convert_charrefs=True)
                self.nodes, self.text = [], []
            def handle_starttag(self, tag, attrs):
                self.nodes.append((tag, dict(attrs)))
            def handle_data(self, value):
                self.text.append(value)

        fragment = Fragment()
        fragment.feed(value["html"])
        return value["html"], fragment.nodes, " ".join(fragment.text)

    @staticmethod
    def activity(repositories=9):
        from scripts.pipeline.activity_analytics import build_activity_analytics
        from tests.pipeline.test_compute_metrics_accuracy import (
            project_activity_envelope, project_activity_event, project_activity_source,
        )
        rows = [project_activity_envelope("heat" + str(index), [
            project_activity_event("work" + str(index), repository="heat" + str(index), branch="feature/days"),
            project_activity_event("older" + str(index), repository="heat" + str(index), when="2026-09-20T11:00:00Z"),
        ]) for index in range(repositories)]
        return build_activity_analytics(project_activity_source(rows))

    def test_shared_cells_periods_row_limit_and_expansion(self):
        activity = self.activity()
        family = activity["project_activity"]
        first_repo = family["rows"][0]["repository"]
        initial, nodes, paint = self.hydrate(activity)
        cells = [attrs for _, attrs in nodes if attrs.get("data-role") == "project-activity-cell" and "data-ref" not in attrs]
        self.assertEqual(8 * 14, len(cells))
        self.assertFalse(any(attrs.get("data-role") == "project-activity-branch" for _, attrs in nodes))
        self.assertEqual(family["dates"][-14:], [cell["data-date"] for cell in cells[:14]])
        self.assertEqual(["14"], [attrs["data-project-period"] for _, attrs in nodes if attrs.get("aria-pressed") == "true"])
        self.assertIn("Show all 9 repositories", paint)
        today = [cell for cell in cells if cell["data-date"] == family["dates"][-1]]
        self.assertTrue(all("data-count" not in cell and "data-level" not in cell and cell["data-complete"] == "false" for cell in today))
        self.assertTrue(all("UTC" in cell["aria-label"] and "tabindex" not in cell for cell in cells))
        expanded, full, _ = self.hydrate(activity, days=30, show_all=True, expanded=[first_repo])
        full_cells = [attrs for _, attrs in full if attrs.get("data-role") == "project-activity-cell" and "data-ref" not in attrs]
        self.assertEqual(9 * 30, len(full_cells))
        self.assertEqual(["true"], [attrs["aria-expanded"] for _, attrs in full if attrs.get("data-project-branch-toggle") == "0"])
        self.assertEqual(1, sum(attrs.get("class") == "project-activity-scroll" for _, attrs in full))
        # Compare the shared key itself, independently of explanatory copy placement.
        def legend(html):
            from html.parser import HTMLParser
            class Key(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.depth = 0
                    self.values = []
                def handle_starttag(self, tag, attrs):
                    attrs = dict(attrs)
                    if self.depth or attrs.get("data-role") == "project-activity-legend":
                        self.depth += 1
                        if "data-level" in attrs:
                            self.values.append(("level", attrs["data-level"]))
                def handle_endtag(self, tag):
                    if self.depth:
                        self.depth -= 1
                def handle_data(self, value):
                    if self.depth and value.strip():
                        self.values.append(("text", value.strip()))
            parser = Key()
            parser.feed(html)
            return parser.values
        self.assertEqual(legend(initial), legend(expanded))
        expected = {(row["repository"], day["date"]): day for row in family["rows"] for day in row["daily"]}
        for cell in full_cells:
            source = expected[cell["data-repository"], cell["data-date"]]
            self.assertEqual(None if source["count"] is None else str(source["count"]), cell.get("data-count"))
            self.assertEqual(None if source["level"] is None else str(source["level"]), cell.get("data-level"))

    def test_compact_activity_copy_preserves_full_detail_and_shared_legend(self):
        """The default view stays concise while full observations remain reachable."""
        from html.parser import HTMLParser
        activity = self.activity()
        family = activity["project_activity"]
        html, _, _ = self.hydrate(activity)
        class Copy(HTMLParser):
            def __init__(self):
                super().__init__()
                self.stack = []
                self.context, self.details, self.key = [], [], []
            def handle_starttag(self, tag, attrs):
                self.stack.append((tag, dict(attrs)))
            def handle_endtag(self, tag):
                if self.stack:
                    self.stack.pop()
            def handle_data(self, value):
                value = value.strip()
                if not value:
                    return
                if any(tag == "details" for tag, _ in self.stack):
                    self.details.append(value)
                elif any(attrs.get("data-role") == "project-activity-legend" for _, attrs in self.stack):
                    self.key.append(value)
                elif not any(tag in ("button", "h2") or attrs.get("role") == "table" for tag, attrs in self.stack):
                    self.context.append(value)
        parser = Copy()
        parser.feed(html)
        problems = []
        details = " ".join(parser.details)
        for field in ("meaning", "qualification", "observed_at"):
            if family[field] not in details:
                problems.append("Full details are missing " + field)
        context = " ".join(parser.context)
        if len(parser.context) != 1 or len([word for word in context.split() if any(char.isalnum() for char in word)]) > 14:
            problems.append("Visible context is not one short block")
        key = " ".join(parser.key)
        for band in family["scale"]["bands"]:
            label = str(band["lower"]) if band["lower"] == band["upper"] else f'{band["lower"]}–{band["upper"]}'
            self.assertIn(label, key)
        if "Pushes/day · low → high" not in key or "Dashed: partial" not in key:
            problems.append("Compact numeric key lacks its unit or partial cue")
        self.assertEqual([], problems)

    def test_unavailable_and_escaped_metadata_keep_readonly_semantics(self):
        for malformed in ({}, {"project_activity": {"schema": "malformed", "dates": {}}},
                          {"project_activity": {"schema": "profile-project-activity/v1", "dates": ["2026-02-30"] * 30}}):
            _, nodes, paint = self.hydrate(malformed)
            self.assertIn("Project activity unavailable", paint)
            self.assertIn("No positive push counts to scale", paint)
            self.assertFalse(any(attrs.get("data-role") == "project-activity-cell" for _, attrs in nodes))
            self.assertTrue(any(attrs.get("id") == "project-activity-matrix" for _, attrs in nodes))
        activity = self.activity(1)
        row = activity["project_activity"]["rows"][0]
        row["repository"] = 'owner/<img src=x onerror="broken">'
        row["branches"][0]["ref"] = 'refs/heads/<script>alert("branch")</script>'
        _, nodes, paint = self.hydrate(activity, expanded=[row["repository"]])
        self.assertFalse(any(tag in {"img", "script"} for tag, _ in nodes))
        self.assertIn(row["repository"], paint)
        self.assertTrue(any(attrs.get("role") == "table" for _, attrs in nodes))
        self.assertTrue(any(attrs.get("data-role") == "project-activity-cell" and row["repository"] in attrs["aria-label"] for _, attrs in nodes))

    def test_sparse_branch_expansion_preserves_supplied_daily_coverage(self):
        from scripts.pipeline.activity_analytics import build_activity_analytics
        from tests.pipeline.test_compute_metrics_accuracy import (
            project_activity_envelope, project_activity_event, project_activity_source,
        )

        for complete in (True, False):
            with self.subTest(complete=complete):
                source = project_activity_source([project_activity_envelope("branch-days", [
                    project_activity_event("feature-day", repository="branch-days", branch="feature/days"),
                    project_activity_event("main-day", repository="branch-days", when="2026-09-20T11:00:00Z"),
                ], complete=complete)])
                activity = build_activity_analytics(source)
                family = activity["project_activity"]
                row = family["rows"][0]
                self.assertEqual(2, sum(len(branch["daily"]) for branch in row["branches"]))
                defaults = {day["date"]: day for day in row["branch_empty_daily"]}
                expected = {(branch["ref"], date): {**defaults, **{day["date"]: day for day in branch["daily"]}}[date]
                            for branch in row["branches"] for date in family["dates"]}
                _, nodes, _ = self.hydrate(activity, days=30, expanded=[row["repository"]])
                cells = [attrs for _, attrs in nodes if attrs.get("data-role") == "project-activity-cell" and "data-ref" in attrs]
                self.assertEqual(60, len(cells))
                for cell in cells:
                    day = expected[cell["data-ref"], cell["data-date"]]
                    self.assertEqual(None if day["count"] is None else str(day["count"]), cell.get("data-count"))
                    self.assertEqual(None if day["level"] is None else str(day["level"]), cell.get("data-level"))
                    self.assertEqual(str(day["complete"]).lower(), cell["data-complete"])

    def test_missing_or_malformed_branch_defaults_never_create_zero(self):
        import copy

        original = self.activity(1)
        quiet_date = "2026-10-09"
        malformed = (None, {}, [], [{"date": quiet_date, "count": 0}],
                     [{"date": quiet_date, "count": 0, "complete": False, "level": 0}],
                     [{"date": quiet_date, "count": 0, "complete": True, "level": 2}],
                     [{"date": quiet_date, "count": 7, "complete": True, "level": 1}])
        for defaults in malformed:
            with self.subTest(defaults=defaults):
                activity = copy.deepcopy(original)
                row = activity["project_activity"]["rows"][0]
                self.assertTrue(row["complete"])
                row["branch_empty_daily"] = defaults
                _, nodes, _ = self.hydrate(activity, days=30, expanded=[row["repository"]])
                cells = [attrs for _, attrs in nodes if attrs.get("data-role") == "project-activity-cell" and "data-ref" in attrs]
                quiet = [cell for cell in cells if cell["data-date"] == quiet_date]
                self.assertEqual(2, len(quiet))
                self.assertTrue(all("data-count" not in cell and "data-level" not in cell and cell["data-complete"] == "false" for cell in quiet))
                positive = [cell for cell in cells if cell.get("data-count") == "1"]
                self.assertEqual(2, len(positive), "Malformed defaults must retain positive branch overrides")

    def test_component_palette_and_neighbor_default_are_independent(self):
        import copy
        import xml.etree.ElementTree as ET
        from scripts.core.config import PROJECT_ACTIVITY_COLORS
        from scripts.pipeline.web_render import render_dashboard
        from scripts.rendering.design_tokens import emit_project_activity_css
        css = emit_project_activity_css()
        self.assertTrue(css.startswith(".project-activity {"))
        self.assertNotIn(":root", css)
        for level, color in PROJECT_ACTIVITY_COLORS.items():
            self.assertIn(f"--project-activity-{level}: {color};", css)
        html = render_dashboard()
        self.assertIn(css, html)
        self.assertLess(html.index('id="activity-code"'), html.index('id="project-activity"'))
        self.assertLess(html.index('id="project-activity"'), html.index('id="activity-pushes"'))
        helper = CodeChangeHydrationTests()
        baseline = helper.activity()
        changed = copy.deepcopy(baseline)
        changed["overall_code_changes"] = {"schema": "profile-owned-code-analytics/v1", "status": "unavailable"}
        changed["project_activity"] = self.activity(1)["project_activity"]
        self.assertEqual(ET.tostring(helper.hydrate(baseline)), ET.tostring(helper.hydrate(changed)))




class _ProfileHeadlineDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        value = cls(2026, 11, 15, 15, 1, 46, tzinfo=timezone.utc)
        return value.astimezone(tz) if tz is not None else value.replace(tzinfo=None)


def _profile_headline_model(value=13514, *, missing=False):
    from tests.pipeline.test_compute_metrics_accuracy import AccuracyTests
    from scripts.pipeline.compute_metrics import compute_profile_model
    first = date(2025, 11, 16)
    days = [{"date": str(first + timedelta(days=i)), "count": i % 5} for i in range(365)]
    total = sum(row["count"] for row in days)
    calendar = {"totalContributions": total, "weeks": [{"contributionDays": [
        {"date": row["date"], "contributionCount": row["count"]} for row in days]}]}
    observation = {
        "schema": "profile-provider-observation/v1", "metric_id": "last_year_contributions",
        "source_metric_id": "github_contribution_calendar_total_and_days",
        "value": {"total": total, "days": tuple(days)}, "status": "ok", "complete": True,
        "population_id": "github-contribution-calendar-visible-to-provider", "population_signature": None,
        "window_start": "2025-11-16T00:00:00Z", "window_end": "2026-11-15T15:01:46Z",
        "observed_at": "2026-11-15T15:01:46Z", "source_id": "github_graphql_contribution_calendar",
        "source_mode": "live", "completion_reason": "all_components_observed",
    }
    base = AccuracyTests()._collected()
    observations = {**base.metric_observations, "last_year_contributions": observation}
    if not missing:
        observations["github_profile_contributions"] = _profile_headline_observation(value)
    collected = replace(base, calendar=calendar, total_contributions=total, metric_observations=observations)
    with patch("scripts.pipeline.compute_metrics.datetime", _ProfileHeadlineDateTime):
        model = compute_profile_model(collected, logger=lambda *_: None, allow_network_calls=False)
    return model, total


def _hydrate_profile_headline(summary):
    from scripts.pipeline.web_render import render_dashboard
    if shutil.which("node") is None:
        raise unittest.SkipTest("Node required to execute the website projection")
    class Elements(HTMLParser):
        def __init__(self):
            super().__init__()
            self.rows, self.stack, self.overview_text = [], [], []
        def handle_starttag(self, tag, attrs):
            attributes = dict(attrs)
            within = attributes.get("id") == "overview" or any(row[2] for row in self.stack)
            self.stack.append((tag, attributes, within))
            if attributes.get("id") or attributes.get("data-bind") or attributes.get("data-calendar-fact") or attributes.get("data-inventory-fact"):
                self.rows.append({"attrs": attributes, "within": within})
        def handle_endtag(self, tag):
            for i in range(len(self.stack)-1, -1, -1):
                if self.stack[i][0] == tag:
                    del self.stack[i:]
                    break
        def handle_data(self, value):
            if value.strip() and any(row[2] for row in self.stack) and not any(row[0] in ("script", "style") for row in self.stack):
                self.overview_text.append(value.strip())
    html = render_dashboard()
    parser = Elements()
    parser.feed(html)
    script = re.findall(r"<script>(.*?)</script>", html, re.S)[0]
    harness = r'''
const fs=require('node:fs'),vm=require('node:vm');
const input=JSON.parse(fs.readFileSync(0,'utf8'));
const element=(attrs={})=>({attrs,children:[],hidden:false,textContent:'',innerHTML:'',dataset:{},
  style:{setProperty(){}},classList:{add(){},remove(){},toggle(){}},
  append(...xs){this.children.push(...xs)},replaceChildren(){this.children=[];this.innerHTML=''},
  getAttribute(k){return Object.hasOwn(this.attrs,k)?this.attrs[k]:null},
  setAttribute(k,v){this.attrs[k]=v},removeAttribute(k){delete this.attrs[k]},
  addEventListener(){},querySelector(s){return s.startsWith('#')?byId.get(s.slice(1)):null},querySelectorAll(){return []}});
const elements=input.elements.map(row=>Object.assign(element(row.attrs),{within:row.within}));
const byId=new Map(elements.filter(e=>e.attrs.id).map(e=>[e.attrs.id,e]));
const doc={documentElement:element(),createElement(){return element()},
  getElementById(id){if(!byId.has(id))byId.set(id,element({id}));return byId.get(id)},
  querySelector(){return null},querySelectorAll(selector){
const m=/^\[([^\]]+)\]$/.exec(selector);return m?elements.filter(e=>Object.hasOwn(e.attrs,m[1])):[]}};
const idle={then(){return this},catch(){return this}};
const ctx={document:doc,location:{hash:'',search:''},localStorage:{getItem(){return null},setItem(){}},
  URLSearchParams,addEventListener(){},requestAnimationFrame(){},fetch(){return idle},sample:input.sample};
vm.runInNewContext(input.script+'\nhydrate(sample);',ctx,{timeout:5000});
const hero=elements.find(e=>(e.attrs.class||'').split(' ').includes('kpi-value'));
process.stdout.write(JSON.stringify({value:hero.textContent,
  public_repos:elements.find(e=>e.attrs['data-inventory-fact']==='inventory.public_total')?.textContent,
  painted:elements.filter(e=>e.within&&!e.hidden).map(e=>e.textContent+' '+e.innerHTML).join(' '),
  window:doc.getElementById('hero-contribution-window').textContent,
  updated:doc.getElementById('updated').textContent,
  cells:doc.getElementById('cal').innerHTML}));
'''
    sample = {"username": summary["username"], "generated_at": summary["generated_at"],
              "dashboard_summary": summary, "snapshot": {"last_year_contributions": 999999}}
    result = subprocess.run(["node", "-e", harness],
                            input=json.dumps({"script": script, "elements": parser.rows, "sample": sample}),
                            text=True, capture_output=True, check=True, timeout=10,
                            env={**os.environ, "TZ": "Pacific/Honolulu"})
    shown = json.loads(result.stdout)
    shown["painted"] += " " + " ".join(parser.overview_text)
    return shown

class GithubProfileHeadlineTests(unittest.TestCase):
    def test_public_repository_headline_and_svg_use_the_same_including_forks_fact(self):
        import xml.etree.ElementTree as ET
        from tests.contracts.test_dashboard_summary import inventory_fixture_model
        from scripts.rendering.generate_dashboard_summary import render_svg
        for mode, expected in (("complete", "4"), ("fresh-change", "5"), ("fork-only", "1")):
            with self.subTest(mode=mode):
                summary = inventory_fixture_model(mode)["dashboard_summary"]
                self.assertEqual(expected, _hydrate_profile_headline(summary)["public_repos"])
                for mobile in (False, True):
                    root = ET.fromstring(render_svg(summary, mobile=mobile))
                    row = next(node for node in root.iter() if node.get("data-metric-id") == "inventory.public_total")
                    self.assertEqual(expected, next(node.text for node in row.iter() if node.get("data-role") == "value"))

    def test_default_total_is_selected_separately_from_calendar_sum(self):
        model, rolling_total = _profile_headline_model()
        summary = model["dashboard_summary"]
        facts = {row["metric_id"]: row for row in summary["facts"]}
        self.assertEqual(rolling_total, facts["calendar.total"]["value"])
        self.assertNotEqual(13514, rolling_total, "precondition: different populations must remain distinguishable")
        self.assertEqual(13514, facts.get("profile.contributions", {}).get("value"),
                         "GitHub default profile total must reach the distinct headline fact")
        self.assertEqual(13514, model["snapshot"].get("github_profile_contributions"))
        self.assertEqual(_profile_headline_observation(), model["dashboard_data"].get("profile_contributions_observation"))
        self.assertEqual(rolling_total, model["snapshot"]["last_year_contributions"])

    def test_hero_uses_native_total_while_calendar_keeps_its_own_total(self):
        import xml.etree.ElementTree as ET
        from scripts.rendering.generate_dashboard_summary import render_svg
        model, rolling_total = _profile_headline_model()
        summary = model["dashboard_summary"]
        before = copy.deepcopy(summary)
        for mobile in (False, True):
            with self.subTest(mobile=mobile):
                tree = ET.fromstring(render_svg(summary, mobile=mobile))
                overview = next(n for n in tree.iter() if n.get("data-section") == "overview")
                values = [n.text for n in overview.iter() if n.get("data-role") == "value"]
                self.assertEqual("13,514", values[0], "primary visible value must use GitHub's default total")
                text = " ".join(n.text or "" for n in overview.iter("{http://www.w3.org/2000/svg}text"))
                self.assertIn("Contributions", text)
                headline = next(n for n in overview.iter() if n.get("data-metric-id") == "profile.contributions")
                ns = "{http://www.w3.org/2000/svg}"
                label = next(n for n in headline.iter(ns+"text") if n.text == "Contributions")
                value = next(n for n in headline.iter(ns+"text") if n.get("data-role") == "value")
                self.assertLess(float(label.get("y")), float(value.get("y")))
                self.assertTrue(list(headline.iter(ns+"path")), "headline keeps its calendar icon")
                self.assertEqual(["Contributions", "13,514"],
                                 [n.text for n in headline.iter(ns+"text")],
                                 "no duplicate label or reporting-period caption below the count")
                self.assertNotIn("2025-11-16 – 2026-11-15", text,
                                 "the separate calendar's full ISO range must not label the native headline")
        from scripts.pipeline.web_render import render_dashboard
        html = render_dashboard()
        hero = html.split('<header class="panel hero"', 1)[1].split('</header>', 1)[0]
        self.assertRegex(hero, r'<div class="kpi-label"><svg[^>]*>.*?</svg><span id="hero-contribution-window">Contributions</span></div>')
        self.assertLess(hero.index('kpi-label'), hero.index('hero-contribution-total'))
        for unwanted in ("snapshot-notice", "Website shows", "Builder dashboard", "About this count", "profile-contribution-period"):
            self.assertNotIn(unwanted, html)
        website = _hydrate_profile_headline(summary)
        self.assertEqual("13,514", website["value"])
        self.assertNotIn("2025-11-16 – 2026-11-15", website["window"])
        self.assertEqual(rolling_total, sum(row["count"] for row in summary["calendar"]["days"]))
        self.assertEqual(before, summary)

    def test_native_zero_and_unavailable_never_fall_back_to_calendar(self):
        import xml.etree.ElementTree as ET
        from scripts.rendering.generate_dashboard_summary import render_svg
        for value, missing in ((0, False), (None, False), (None, True)):
            model, calendar_total = _profile_headline_model(value, missing=missing)
            summary = model["dashboard_summary"]
            expected = "0" if value == 0 else "n/a"
            self.assertGreater(calendar_total, 0)
            for mobile in (False, True):
                with self.subTest(value=value, missing=missing, mobile=mobile):
                    tree = ET.fromstring(render_svg(summary, mobile=mobile))
                    overview = next(n for n in tree.iter() if n.get("data-section") == "overview")
                    shown = next(n.text for n in overview.iter() if n.get("data-role") == "value")
                    self.assertEqual(expected, shown)
            self.assertEqual(expected, _hydrate_profile_headline(summary)["value"])

    def test_calendar_control_remains_current_with_a_distinct_native_total(self):
        from scripts.pipeline.profile_pipeline import candidate_publication_subject
        for value, missing in ((13514, False), (0, False), (None, False), (None, True)):
            model, total = _profile_headline_model(value, missing=missing)
            self.assertEqual(total, model["snapshot"]["last_year_contributions"])
            self.assertEqual(total, model["contribution_rhythm"]["total"])
            self.assertEqual(365, len(model["dashboard_summary"]["calendar"]["days"]))
            self.assertEqual("current", candidate_publication_subject(model, source_kind="github-api").contribution_currentness)

    def test_publication_rejects_coordinated_forged_headline_without_relabeling_calendar(self):
        from scripts.pipeline.profile_pipeline import candidate_publication_subject, stored_publication_subject
        model, _ = _profile_headline_model()
        # Arrange the new source shape explicitly so the old publication seam is exercised now.
        # This is a provider observation fixture, not a claim of provider attestation.
        model["dashboard_data"]["profile_contributions_observation"] = _profile_headline_observation()
        for snapshot in (model["snapshot"], model["dashboard_data"]["snapshot"]):
            snapshot["github_profile_contributions"] = 999
        for summary in (model["dashboard_summary"], model["dashboard_data"]["dashboard_summary"]):
            summary["facts"] = [f for f in summary["facts"] if f["metric_id"] != "profile.contributions"]
            summary["facts"].append({"metric_id": "profile.contributions", "value": 999,
                                     "display_value": "999", "quality": {"status": "exact"}})
        self.assertEqual("noncurrent", candidate_publication_subject(model, source_kind="github-api").contribution_currentness,
                         "a copied scalar and fact cannot override their retained native source")
        self.assertEqual("noncurrent", stored_publication_subject({"source_kind": "github-api"},
                            model["dashboard_data"]).contribution_currentness)

    def test_readme_details_keep_native_headline_and_calendar_distinct(self):
        from jinja2 import Environment
        model, rolling_total = _profile_headline_model()
        summary = model["dashboard_summary"]
        rendered = Environment().from_string((ROOT / "templates/README.md.tpl").read_text()).render(
            dashboard_summary=summary, legacy_visuals=[])
        native = next(row for row in summary["facts"] if row["metric_id"] == "profile.contributions")
        calendar = next(row for row in summary["facts"] if row["metric_id"] == "calendar.total")
        self.assertIn(f"| {native['label']} | 13,514 |", rendered)
        self.assertIn(f"| {calendar['label']} | {rolling_total:,} |", rendered)
        self.assertIn(summary["calendar"]["window"], rendered)
        self.assertIn(summary["generated_at"], rendered)
        self.assertNotEqual(native["window"], calendar["window"])


if __name__ == "__main__":
    unittest.main()

class ActivityOverviewLayoutTests(unittest.TestCase):
    """DESIGN_SPEC: the reference layout is structure, not a color substitution."""
    def test_overview_separates_controls_profile_metrics_and_update_footer(self):
        from html.parser import HTMLParser
        from scripts.pipeline.web_render import render_dashboard
        class Structure(HTMLParser):
            def __init__(self):
                super().__init__(); self.stack=[]; self.rows=[]
            def handle_starttag(self, tag, attrs):
                item=dict(attrs); self.rows.append((tag,item,tuple(self.stack)))
                if tag not in ("img","meta","link","input","br","hr"):
                    self.stack.append((tag,item))
            def handle_endtag(self, tag):
                for i in range(len(self.stack)-1,-1,-1):
                    if self.stack[i][0]==tag:
                        self.stack=self.stack[:i];break
        parser=Structure();parser.feed(render_dashboard())
        def rows(cls):
            return [row for row in parser.rows if cls in row[1].get("class","").split()]
        def inside(row, cls):
            return any(cls in attrs.get("class","").split() for _,attrs in row[2])
        toolbar=rows("dashboard-toolbar"); self.assertEqual(1,len(toolbar))
        for cls in ("site-nav","switcher"):
            self.assertEqual(1,len(rows(cls)))
            self.assertTrue(inside(rows(cls)[0],"dashboard-toolbar"))
            self.assertFalse(inside(rows(cls)[0],"hero"))
        self.assertLess(parser.rows.index(toolbar[0]), parser.rows.index(rows("hero")[0]))
        self.assertEqual(1,len(rows("profile-heading")))
        avatar=rows("profile-avatar");self.assertEqual(1,len(avatar))
        self.assertTrue(avatar[0][1].get("src","").startswith("data:image/jpeg;base64,"))
        self.assertTrue(inside(avatar[0],"profile-heading"))
        self.assertEqual(1,len(rows("kpi")))
        stats=rows("stat");self.assertEqual(3,len(stats))
        for stat in stats:self.assertTrue(inside(stat,"stats"))
        footer=rows("hero-footer");self.assertEqual(1,len(footer))
        updated=next(row for row in parser.rows if row[1].get("id")=="updated")
        self.assertTrue(inside(updated,"hero-footer"))
        links=[row for row in parser.rows if row[0]=="a" and inside(row,"hero-footer")]
        self.assertEqual(["https://github.com/jguida941"],[row[1].get("href") for row in links])
        self.assertFalse(rows("contribution-details"))


class ScorecardPeriodContract(unittest.TestCase):
    def test_mixed_period_scorecard_preserves_specific_windows_without_a_universal_heading(self):
        from html import unescape
        from scripts.pipeline.web_render import render_dashboard
        from scripts.rendering.design_tokens import THEMES

        for theme in THEMES:
            with self.subTest(theme=theme):
                html = render_dashboard(default_theme=theme)
                section = re.search(r'<section\b[^>]*\bid="automation"[^>]*>(.*?)</section>', html, re.S)
                self.assertIsNotNone(section)
                body = section.group(1)
                heading = re.search(r'<p class="eyebrow">(.*?)</p>', body, re.S)
                self.assertIsNotNone(heading)
                text = " ".join(unescape(re.sub(r"<[^>]+>", " ", heading.group(1))).split())
                self.assertTrue(text)
                self.assertNotRegex(text, r"(?i)\b(?:\d+\s+(?:days?|weeks?|months?|years?)|(?:past|last)\s+year)\b",
                                    "Mixed-period metrics cannot share a universal period claim")
                rows = re.findall(r'<div class="mrow">(.*?)</div>', body.split("<details>", 1)[0], re.S)
                for binding, period in (("scorecard.active_repos_7d", "last 7 days"),
                                        ("scorecard.releases_30d", "last 30 days"),
                                        ("automation_display.combined.workflow_files", "observed default-branch HEAD")):
                    selected = [row for row in rows if f'data-bind="{binding}"' in row]
                    self.assertEqual(1, len(selected))
                    self.assertIn(period, selected[0])


class OverviewProfileLinkAndTimeTests(unittest.TestCase):
    def test_profile_link_has_decorative_mark_and_visible_accessible_name(self):
        from scripts.pipeline.web_render import render_dashboard
        from scripts.rendering.design_tokens import THEMES
        for theme in THEMES:
            html = render_dashboard(default_theme=theme)
            footer = re.search(r'<div class="hero-footer">(.*?)</header>', html, re.S).group(1)
            anchor = re.search(r'<a\b([^>]*)>(.*?)</a>', footer, re.S)
            self.assertIsNotNone(anchor)
            self.assertIn('href="https://github.com/jguida941"', anchor.group(1))
            self.assertIn('class="github-profile-link"', anchor.group(1))
            self.assertIn("View GitHub profile", anchor.group(2))
            mark = re.search(r'<svg\b([^>]*)>(.*?)</svg>', anchor.group(2), re.S)
            self.assertIsNotNone(mark, "a recognizable GitHub mark belongs inside the link")
            self.assertIn('aria-hidden="true"', mark.group(1))
            self.assertIn('focusable="false"', mark.group(1))
            self.assertIn("<path", mark.group(2))
            self.assertIn(".hero .github-profile-link", html)
            self.assertIn(".github-profile-link:focus-visible", html)

    def test_update_uses_configured_profile_zone_and_rejects_unknown_instants(self):
        from unittest.mock import patch
        model, _ = _profile_headline_model()
        summary = model["dashboard_summary"]
        cases = [
            ("2026-11-19T18:02:33Z", "Updated Nov 19, 2026, 1:02 PM EST"),
            ("2026-07-01T01:08:00Z", "Updated Jun 30, 2026, 9:08 PM EDT"),
            ("2026-11-01T05:30:00Z", "Updated Nov 1, 2026, 1:30 AM EDT"),
            ("2026-11-01T06:30:00Z", "Updated Nov 1, 2026, 1:30 AM EST"),
            ("2026-11-19T13:02:33-05:00", "Updated Nov 19, 2026, 1:02 PM EST"),
        ]
        with patch.dict(os.environ, {"PROFILE_TIMEZONE": "America/New_York"}):
            for timestamp, expected in cases:
                summary["generated_at"] = timestamp
                self.assertEqual(expected, _hydrate_profile_headline(summary)["updated"])
            for timestamp in (None, "", "invalid", "2026-11-19", "2026-11-19T13:02:33", "2026-02-30T13:00:00Z", "2026-11-19T13:00:00+00:60", "2026-11-19T13:00:00+24:00"):
                summary["generated_at"] = timestamp
                self.assertEqual("Update time unavailable", _hydrate_profile_headline(summary)["updated"])
        with patch.dict(os.environ, {"PROFILE_TIMEZONE": "UTC"}):
            summary["generated_at"] = "2026-11-19T18:02:33Z"
            self.assertEqual("Updated Nov 19, 2026, 6:02 PM UTC", _hydrate_profile_headline(summary)["updated"])


class CIWeeklyWebsiteTests(unittest.TestCase):
    def test_one_personal_panel_preserves_page_order_and_native_disclosure(self):
        from scripts.pipeline.web_render import render_dashboard
        html=render_dashboard()
        self.assertIn('<header class="panel hero" id="overview"',html)
        self.assertEqual(1,html.count('id="ci-observatory"'))
        for obsolete in ('id="ci-execution"','id="ci-actions"','id="interactive-details"','class="canonical-profile"','Select a weekly group','--ci-week-count'):
            self.assertNotIn(obsolete,html)
        self.assertLess(html.index('id="automation"'),html.index('id="ci-observatory"'))
        self.assertLess(html.index('id="ci-observatory"'),html.index('id="weekly-contributions"'))
        self.assertIn('hydrateCITimeline(d.ci_timeline)',html)
        self.assertIn('.ci-group:focus-visible',html)
        self.assertIn('min-height: 64px',html)
        self.assertIn('element("details","ci-lane")',html)
        self.assertIn('element("summary","ci-group")',html)
        self.assertLess(html.index('id="ci-observatory-title"'),html.index('id="ci-header-metrics"'))
        self.assertLess(html.index('id="ci-header-metrics"'),html.index('id="ci-timeline-rows"'))
        self.assertLess(html.index('id="ci-timeline-rows"'),html.index('id="ci-observatory-note"'))
        self.assertLess(html.index('id="ci-observatory-note"'),html.index('id="ci-observatory-count"'))
        self.assertLess(html.index('id="ci-observatory-count"'),html.index('id="ci-legend"'))
        self.assertIn('Workflow runs and results',html)

    def test_javascript_and_svg_project_identical_qualified_personal_facts(self):
        from tests.contracts.test_dashboard_summary import _weekly_ci_fixture
        from scripts.rendering.generate_dashboard_summary import ci_weekly_projection
        from scripts.pipeline.web_render import render_dashboard
        script=re.findall(r'<script>(.*?)</script>',render_dashboard(),re.S)[0]
        part=script[script.index('  const CI_WEEK_GROUPS'):script.index('  function hydrateCITimeline(')]
        harness=r"const fs=require('node:fs'),vm=require('node:vm');const x=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(vm.runInNewContext(x.script+'\nciWeeklyProjection(sample);',{sample:x.sample})));"
        sample=_weekly_ci_fixture()
        result=subprocess.run(['node','-e',harness],input=json.dumps({'script':part,'sample':sample}),capture_output=True,text=True,check=True,timeout=15)
        value=json.loads(result.stdout)
        self.assertEqual(ci_weekly_projection(sample),value)
        self.assertEqual(9,value['observed_runs']);self.assertEqual(37,value['scale_max'])
        self.assertTrue(value['repositories'][1]['is_private'])
        self.assertEqual([11,12],[run['run_id'] for run in value['repositories'][1]['runs']])

    def test_emitted_disclosures_preserve_private_runs_counts_and_refresh(self):
        """Execute emitted DOM behavior; actual trusted input remains a browser gate."""
        from tests.contracts.test_dashboard_summary import _weekly_ci_fixture
        from scripts.pipeline.web_render import render_dashboard
        script=re.findall(r'<script>(.*?)</script>',render_dashboard(),re.S)[0]
        source=script[script.index('  const CI_WEEK_GROUPS'):script.index('  function hydrate(d)')]
        harness=r'''
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const input=JSON.parse(fs.readFileSync(0,'utf8'));
class El{
 constructor(tag='div'){this.tagName=tag;this.children=[];this.attrs={};this.dataset={};this.style={};this.handlers={};this.textContent='';this.open=false;}
 appendChild(child){this.children.push(child);return child;}
 replaceChildren(...children){this.children=children;this.textContent='';}
 setAttribute(k,v){this.attrs[k]=String(v);} getAttribute(k){return this.attrs[k]??null;}
 addEventListener(k,fn){this.handlers[k]=fn;}
}
const ids=['ci-observatory','ci-timeline-axis','ci-timeline-rows','ci-observatory-note','ci-observatory-count','ci-observatory-scope','ci-timeline-scroll','ci-legend','ci-header-metrics'];
const nodes=Object.fromEntries(ids.map(id=>[id,new El()]));
const context={document:{getElementById:id=>nodes[id]||null,createElement:tag=>new El(tag)},sample:input.sample};vm.createContext(context);
const all=node=>[node,...node.children.flatMap(all)];
vm.runInContext(input.source+'\nhydrateCITimeline(sample);',context);
const lanes=nodes['ci-timeline-rows'].children;
assert.equal(lanes.length,6);assert(lanes.every(lane=>lane.tagName==='details'&&!lane.open));
assert.deepEqual(lanes.map(row=>row.dataset.observedRuns),['5','2','0',undefined,'1','1']);
assert(lanes.every(row=>row.children[0].tagName==='summary'&&row.children[0].getAttribute('aria-expanded')==='false'));
assert.equal(all(nodes['ci-timeline-rows']).filter(node=>node.dataset.role==='ci-count').reduce((sum,n)=>sum+Number(n.textContent),0),9);
const publicRow=lanes[0],privateRow=lanes[1];
const privateLock=all(privateRow).find(n=>n.className==='ci-private');
assert(privateLock && privateLock.getAttribute('aria-label')==='Private repository');
assert.equal(privateLock.getAttribute('role'),'img');
assert(privateRow.children[0].getAttribute('aria-label').includes('Private repository'));
assert(!all(privateRow).some(n=>n.textContent==='Private'));
assert(!all(privateRow).some(n=>n.className==='ci-owner'));
const identity=all(privateRow).find(n=>n.className==='ci-identity');
assert.equal(identity.children[0],privateLock,'lock precedes repository name');
const details=row=>all(row).filter(node=>node.dataset.role==='ci-run-detail');
assert.deepEqual(details(privateRow).map(n=>n.dataset.runId),['11','12']);
assert.equal(details(privateRow)[1].children[0].href,'https://github.com/example/profile-private-continuation-with-a-long-name/actions/runs/12');
assert.deepEqual(details(publicRow).map(n=>n.dataset.outcome),['success','failure','queued','cancelled','unknown']);
assert.equal(details(publicRow).at(-1).children[0].textContent,'<img onerror="bad()">');
assert.equal(details(publicRow).at(-1).children[0].children.length,0,'provider title is text, not markup');
const segments=all(publicRow).filter(n=>n.dataset.role==='ci-bar-segment');
assert.deepEqual(segments.map(n=>[n.dataset.group,n.dataset.count]),[['pass','1'],['fail','1'],['pending','1'],['other','1'],['unknown','1']]);
assert(segments.every(n=>Math.abs(parseFloat(n.style.width)-100/37)<1e-8),'narrow segments keep absolute scale');
assert.equal(nodes['ci-observatory-note'].textContent,'2026-11-06 – 2026-11-19 UTC');
assert.equal(nodes['ci-observatory-count'].textContent,'9 sampled runs · 6 personal repositories · partial sample');
assert(nodes['ci-observatory-scope'].textContent.includes('Newest 37 runs'));
assert(nodes['ci-observatory-scope'].textContent.includes('last UTC date is partial'));
assert.equal(nodes['ci-observatory'].dataset.status,'partial');
assert(!all(nodes['ci-legend']).some(n=>n.textContent==='Other'));
assert(all(nodes['ci-legend']).some(n=>n.textContent==='Cancelled'));
assert(all(nodes['ci-legend']).some(n=>n.textContent==='Unknown'));
assert.equal(all(nodes['ci-legend']).filter(n=>(n.className||'').includes('ci-marker')).length,5);
assert(!all(nodes['ci-legend']).some(n=>n.className==='ci-icon'));
assert.equal(all(nodes['ci-header-metrics']).filter(n=>n.className==='ci-icon').length,5,'header keeps neutral outline icons');
privateRow.open=true;privateRow.handlers.toggle();
assert.equal(privateRow.children[0].getAttribute('aria-expanded'),'true');
privateRow.open=false;privateRow.handlers.toggle();
assert.equal(privateRow.children[0].getAttribute('aria-expanded'),'false');
publicRow.open=true;publicRow.handlers.toggle();
privateRow.open=true;privateRow.handlers.toggle();
assert.equal(publicRow.open,false,'only the current repository details stay open');
assert.equal(publicRow.children[0].getAttribute('aria-expanded'),'false');
vm.runInContext('hydrateCITimeline({...sample,status:"unavailable"});',context);
assert.equal(all(nodes['ci-timeline-rows']).filter(n=>n.dataset.role==='ci-run-detail').length,0,'refresh clears stale details');
assert.equal(all(nodes['ci-timeline-rows']).filter(n=>n.dataset.role==='ci-bar-segment').length,0,'unavailable cannot retain success');
assert.equal(nodes['ci-observatory'].dataset.status,'unavailable');
assert.equal(nodes['ci-observatory-note'].textContent,'2026-11-06 – 2026-11-19 UTC');
assert.equal(nodes['ci-observatory-count'].textContent,'Run count unavailable · 6 personal repositories · sample unavailable');
vm.runInContext('hydrateCITimeline(null);',context);
assert.equal(nodes['ci-observatory-note'].textContent,'Workflow history unavailable');
assert.equal(nodes['ci-observatory-count'].textContent,'Run count unavailable');
'''
        fixture=_weekly_ci_fixture()
        def execute(js):
            return subprocess.run(['node','-e',harness],input=json.dumps({'source':js,'sample':fixture}),capture_output=True,text=True,timeout=15)
        healthy=execute(source)
        self.assertEqual(0,healthy.returncode,healthy.stderr[-6000:])
        for anchor,wrong in (
            ('!Number.isSafeInteger(identity)','false'),
            ('|| seenRuns.has(identity)',''),
            ('|| when>end',''),
            ('cancelled:"other"','cancelled:"pass"'),
            ('value.status!=="unavailable"&&',''),
            ('for(const row of projected.repositories){','for(const row of projected.repositories){if(row.is_private)continue;'),
        ):
            with self.subTest(wrong_fix=anchor):
                self.assertIn(anchor,source)
                self.assertNotEqual(0,execute(source.replace(anchor,wrong,1)).returncode)

    def test_component_uses_canonical_icons_tokens_and_safe_provider_text(self):
        from scripts.pipeline.web_render import _component_css,_ci_observatory,render_dashboard
        from scripts.rendering.icons import LUCIDE
        css=_component_css();ci=css[css.index('/* CI repository lanes'):css.index('/* --- language bar')]
        self.assertNotRegex(ci,r'#[0-9a-fA-F]{3,8}\b')
        for token in ('var(--status-success)','var(--status-danger)','var(--status-warning)','var(--hairline)','var(--ink-dim)'):
            self.assertIn(token,ci)
        self.assertNotIn('--ci-track-min',ci)
        self.assertNotIn('min-width: 44px',ci)
        markup=_ci_observatory();self.assertEqual(1,markup.count('<h2'))
        self.assertNotIn('ci-observatory-badge',markup)
        self.assertIn(LUCIDE['workflow'],markup)
        self.assertIn('Workflow runs and results',markup);self.assertIn('CI activity',markup)
        self.assertNotIn('<details class="ci-sample-details" open',markup)
        script=re.findall(r'<script>(.*?)</script>',render_dashboard(),re.S)[0]
        ci_js=script[script.index('  const CI_WEEK_GROUPS'):script.index('  function hydrate(d)')]
        self.assertEqual(1,ci_js.count('innerHTML'),'only trusted canonical icon paths use markup')
        self.assertIn("CI_ICON_PATHS[group]",ci_js)
        self.assertNotIn('https://api.github.com',ci_js)

    def test_projection_parity_preserves_unicode_names_and_extreme_valid_dates(self):
        from scripts.pipeline.web_render import render_dashboard
        from scripts.rendering.generate_dashboard_summary import ci_weekly_projection
        script=re.findall(r'<script>(.*?)</script>',render_dashboard(),re.S)[0]
        source=script[script.index('  const CI_WEEK_GROUPS'):script.index('  function hydrateCITimeline(')]
        sample={'schema':'profile-ci-timeline/v1','owner':'example','status':'available','window_start':'9999-12-23T12:00:00Z','window_end':'9999-12-31T12:00:00Z','repositories':[{'repository':'example/workflows','status':'available','runs':[{'run_id':1,'created_at':'9999-12-31T12:00:00Z','workflow':'🚀'*100,'outcome':'success'}]}]}
        harness=r"const fs=require('node:fs'),vm=require('node:vm');const x=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(vm.runInNewContext(x.source+'\nciWeeklyProjection(sample);',{sample:x.sample})));"
        completed=subprocess.run(['node','-e',harness],input=json.dumps({'source':source,'sample':sample}),capture_output=True,text=True,check=True,timeout=15)
        value=json.loads(completed.stdout);self.assertEqual(ci_weekly_projection(sample),value)
        self.assertEqual(sample['window_start'],value['window_start'])
        self.assertEqual('🚀'*100,value['repositories'][0]['runs'][0]['workflow'])

    def test_readme_without_projected_ci_context_stays_unavailable(self):
        from jinja2 import Environment
        from tests.contracts.test_dashboard_summary import _weekly_ci_fixture
        from scripts.rendering.generate_dashboard_summary import ci_weekly_projection
        model, _ = _profile_headline_model()
        summary = model["dashboard_summary"]
        # The valid nonempty carrier must not become an implicit second CI view.
        summary["ci_timeline"] = _weekly_ci_fixture()
        self.assertGreater(ci_weekly_projection(summary["ci_timeline"])["observed_runs"], 0)
        rendered = Environment().from_string((ROOT / "templates/README.md.tpl").read_text()).render(
            dashboard_summary=summary, legacy_visuals=[])
        section = rendered.split("### Repository CI sample", 1)[1].split("Recently created:", 1)[0]
        self.assertIn("unavailable – unavailable UTC", section)
        self.assertIn("sampled runs · unavailable", section)
        self.assertNotIn("example/", section)
        self.assertEqual(2, sum(line.startswith("|") for line in section.splitlines()))

    def test_count_foregrounds_stay_legible_in_every_existing_theme(self):
        from scripts.pipeline.web_render import _component_css
        from scripts.rendering.design_tokens import DEFAULT_THEME,THEMES,type_scale
        from tests.contracts.test_theme_system import _contrast
        css=_component_css()
        for name,theme in THEMES.items():
            # The default theme is emitted on html as an empty data-theme.
            selector = '' if name == DEFAULT_THEME else name
            self.assertGreaterEqual(type_scale(name)['caption'][0],12)
            for group,background in (('pass','status-success'),('fail','status-danger'),('pending','status-warning'),('other','ink-dim')):
                match=re.search(r'\[data-theme="'+re.escape(selector)+r'"\] \.ci-bar-segment\.ci-'+group+r' \{ --ci-count-ink: var\(--([^)]*)\)',css)
                self.assertIsNotNone(match)
                self.assertGreaterEqual(_contrast(theme[match.group(1)],theme[background]),4.5,(name,group))
            self.assertGreaterEqual(_contrast(theme['ink-strong'],theme['surface']),4.5)

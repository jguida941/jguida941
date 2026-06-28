"""SVG card-output contract: every generated card must be GitHub-safe, titled,
and stay inside its viewBox. Backs the promises in glass_kit's docstring.
"""
import json
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from scripts.pipeline.collect_data import CollectedProfileData
from scripts.pipeline.compute_metrics import compute_profile_model

ROOT = Path(__file__).resolve().parent.parent
NS = "{http://www.w3.org/2000/svg}"


def _noop(*a, **k):
    pass


def _model():
    payload = json.loads((ROOT / "tests/fixtures/sample_collected_data.json").read_text())
    collected = CollectedProfileData(**payload)
    return collected, compute_profile_model(collected, logger=_noop, allow_network_calls=False)


COLLECTED, MODEL = _model()


def _render(card, out):
    m, c = MODEL, COLLECTED
    if card == "metrics_general":
        from scripts.rendering.generate_metrics_general import generate
        return generate(username=m["dashboard_data"]["username"], snapshot=m["snapshot"],
                        data_scope=m["data_scope"], generated_at=m["dashboard_data"]["generated_at"],
                        output_path=out)
    if card == "badges":
        from scripts.rendering.generate_badges import generate
        return generate(public_nonfork_repos=c.repo_counts["public_owned_nonfork"],
                        public_forks=c.repo_counts["public_owned_forks"],
                        private_owned_repos=c.repo_counts["private_owned"],
                        ci_count=m["snapshot"]["ci_repos"],
                        last_year_contributions=c.total_contributions, output_path=out)
    if card == "scorecard":
        from scripts.rendering.generate_builder_scorecard import generate
        return generate(m["scorecard"], output_path=out, tiles=m["scorecard_cards"])
    if card == "engineering":
        from scripts.rendering.generate_engineering_cadence import generate
        return generate(m["engineering"], output_path=out)
    if card == "focus":
        from scripts.rendering.generate_focus_board import generate
        return generate(m["focus"], output_path=out)
    if card == "currently_working":
        from scripts.rendering.generate_currently_working import generate
        return generate(m["recent_repos"], output_path=out)
    if card == "streak":
        from scripts.rendering.generate_streak_summary import generate
        return generate(calendar=c.calendar, current_streak_days=m["snapshot"]["streak_days"],
                        total_contributions=c.total_contributions, output_path=out)
    if card == "snapshot":
        from scripts.rendering.generate_snapshot_panel import generate
        return generate(m["snapshot_rows"], m["data_quality"], data_scope=m["data_scope"], output_path=out)
    if card == "lang":
        from scripts.rendering.generate_language_chart import generate
        return generate(c.language_bytes, output_path=out)
    if card == "heatmap":
        from scripts.rendering.generate_activity_heatmap import generate
        return generate(c.events, output_path=out)
    if card == "contribution":
        from scripts.rendering.generate_contribution_panel import generate
        return generate(c.calendar, output_path=out)
    if card == "spotlight":
        from scripts.rendering.generate_repo_spotlight import generate
        return generate(m["spotlight_data"], output_path=out)
    raise ValueError(card)


CARDS = {
    "metrics_general": None,
    "badges": "By The Numbers",
    "scorecard": "Builder Scorecard",
    "engineering": "Engineering Cadence",
    "focus": "Current Focus",
    "currently_working": "Currently Working On",
    "streak": "Streak Summary",
    "snapshot": "Raw Data Snapshot (Python Pull)",
    "lang": "Language Breakdown",
    "heatmap": "When I Code",
    "contribution": "Contribution Calendar",
    "spotlight": "Flagship Projects",
}

BANNED = ("<script", "<foreignObject", "rgba(", "@import", "fonts.googleapis", "<style")


def _right_edge(root):
    """Max content right edge across rects/lines/circles/polylines (geometry only)."""
    def num(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None
    mx = 0.0
    for el in root.iter():
        t = el.tag.replace(NS, "")
        r = None
        if t == "rect":
            x, w = num(el.get("x", "0")), num(el.get("width"))
            if x is not None and w is not None:
                r = x + w
        elif t == "line":
            r = max(num(el.get("x1", "0")) or 0, num(el.get("x2", "0")) or 0)
        elif t == "circle":
            cx, rr = num(el.get("cx", "0")), num(el.get("r", "0"))
            if cx is not None and rr is not None:
                r = cx + rr
        elif t in ("polyline", "polygon"):
            xs = [num(p.split(",")[0]) for p in el.get("points", "").split() if "," in p]
            xs = [x for x in xs if x is not None]
            if xs:
                r = max(xs)
        if r is not None and r > mx:
            mx = r
    return mx


class CardContractTests(unittest.TestCase):
    def test_all_cards(self):
        with tempfile.TemporaryDirectory() as d:
            for card, title in CARDS.items():
                out = str(Path(d) / f"{card}.svg")
                _render(card, out)
                svg = Path(out).read_text(encoding="utf-8")
                with self.subTest(card=card):
                    # valid XML
                    root = ET.fromstring(svg)
                    # GitHub-safe: no banned constructs
                    for bad in BANNED:
                        self.assertNotIn(bad, svg, f"{card} contains banned '{bad}'")
                    # has sizing
                    self.assertIsNotNone(root.get("viewBox"), f"{card} missing viewBox")
                    vbw = float(root.get("viewBox").split()[2])
                    # geometry stays inside the frame (no clipping)
                    self.assertLessEqual(_right_edge(root), vbw + 1, f"{card} content overflows viewBox")
                    # exactly one title (per validator contract)
                    if title:
                        hits = len(re.findall(rf">{re.escape(title)}</text>", svg))
                        self.assertEqual(hits, 1, f"{card} expected one '{title}' title, found {hits}")


if __name__ == "__main__":
    unittest.main()

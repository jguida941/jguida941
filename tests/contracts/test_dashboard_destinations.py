"""Stable website links exist before the snapshot request completes."""
import unittest
import re
from pathlib import Path
from scripts.pipeline.web_render import render_dashboard
from scripts.rendering.design_tokens import emit_css_root


class DashboardDestinationsTests(unittest.TestCase):
    def test_all_destinations_are_visible_structural_targets(self):
        html=render_dashboard()
        for identity in ("overview","weekly-contributions","automation","languages","projects","snapshot","calendar-panel","rhythm-panel"):
            tags=re.findall(r'<[^>]+id="'+identity+r'"[^>]*>',html)
            self.assertEqual(len(tags),1)
            self.assertNotIn("hidden",tags[0])
        self.assertIn(emit_css_root().strip(),html)

    def test_index_matches_generator(self):
        root=Path(__file__).resolve().parents[2]
        self.assertEqual((root/"site/index.html").read_text(),render_dashboard())

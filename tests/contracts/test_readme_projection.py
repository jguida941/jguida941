"""Proposed replacement for the existing public README projection test only."""
import unittest
from pathlib import Path
import re


def assert_projection(test, text):
    pictures = re.findall(r'<picture>(.*?)</picture>', text, re.S)
    test.assertEqual(len(pictures), 1)
    test.assertIn('media="(max-width: 767px)"', pictures[0])
    test.assertIn("assets/dashboard_summary_mobile.svg", pictures[0])
    main = re.findall(r'<img\b[^>]+>', pictures[0])
    test.assertEqual(len(main), 1)
    test.assertRegex(main[0], r'src="assets/dashboard_summary\.svg(?:\?[^\"]*)?"')
    test.assertIn('width="100%"', main[0])
    legacy = re.findall(r'<details>\s*<summary>Legacy visual detail</summary>(.*?)</details>', text, re.S)
    test.assertEqual(len(legacy), 1, "compatibility image must be in the existing closed legacy disclosure")
    compatibility = re.findall(r'<img\b[^>]+>', legacy[0])
    test.assertEqual(len(compatibility), 1)
    test.assertRegex(compatibility[0], r'src="assets/raw_snapshot\.svg(?:\?[^\"]*)?"')
    test.assertIn('width="100%"', compatibility[0])
    test.assertEqual(re.findall(r'<img\b[^>]+>', text), main + compatibility,
                     "only the headline picture and closed legacy snapshot image may be published")
    test.assertIn("Read the numbers and definitions", text)
    test.assertIn("#weekly-contributions", text)
    test.assertNotIn('<img src="metrics.general.svg', text)


class SharedProfileRendererContract(unittest.TestCase):
    """GitHub profile and Pages overview consume the same canonical SVG bytes."""

    def test_one_desktop_mobile_svg_pair_is_both_surfaces_overview(self):
        from scripts.pipeline.web_render import render_dashboard
        page = render_dashboard()
        readme = (Path(__file__).resolve().parents[2] / "README.md").read_text()
        for filename in ("dashboard_summary.svg", "dashboard_summary_mobile.svg"):
            self.assertIn("assets/" + filename, readme)
            self.assertIn("./assets/" + filename, page)
        self.assertIn('id="overview"', page)
        self.assertIn('src="./assets/dashboard_summary.svg"', page)
        self.assertIn('srcset="./assets/dashboard_summary_mobile.svg"', page)
        self.assertIn('data-renderer="scripts.rendering.generate_dashboard_summary.render_svg"', page)
        self.assertIn('id="interactive-details"', page)

    def test_pages_deploy_copies_exact_github_profile_card_bytes(self):
        root = Path(__file__).resolve().parents[2]
        workflow = (root / ".github/workflows/deploy-site.yml").read_text()
        for name in ("dashboard_summary.svg", "dashboard_summary_mobile.svg"):
            self.assertIn("cp assets/" + name + " site/assets/" + name, workflow)
            self.assertIn("cmp assets/" + name + " site/assets/" + name, workflow)
        self.assertLess(workflow.index("cmp assets/dashboard_summary.svg site/assets/dashboard_summary.svg"),
                        workflow.index("uses: actions/upload-pages-artifact@v3"))

class ReadmeProjectionContract(unittest.TestCase):
    def test_one_responsive_picture_and_native_equivalent(self):
        root = Path(__file__).resolve().parents[2]
        for name in ("templates/README.md.tpl", "README.md"):
            assert_projection(self, (root / name).read_text())


class CodeChangeReadmeTests(unittest.TestCase):
    def test_code_text_has_full_branch_commit_and_daily_equivalent(self):
        from jinja2 import Environment
        from pathlib import Path
        from scripts.pipeline.activity_analytics import build_activity_analytics
        from tests.pipeline.test_compute_metrics_accuracy import CodeChangeAggregationTests, AccuracyTests
        from scripts.pipeline.compute_metrics import compute_profile_model
        model=compute_profile_model(AccuracyTests()._collected(),logger=lambda *_:None,allow_network_calls=False)
        model['dashboard_summary']['activity_analytics']=build_activity_analytics(CodeChangeAggregationTests.source())
        template=Path('templates/README.md.tpl').read_text()
        rendered=Environment().from_string(template).render(dashboard_summary=model['dashboard_summary'],legacy_visuals=[])
        self.assertIn('Current Focus',rendered)
        self.assertIn('refs/heads/dev/feature',rendered)
        self.assertIn('https://github.com/owner/project/commit/'+'a'*40,rendered)
        self.assertIn('| 2026-10-10 | 20 | 7 |',rendered)

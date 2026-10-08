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


class ReadmeProjectionContract(unittest.TestCase):
    def test_one_responsive_picture_and_native_equivalent(self):
        root = Path(__file__).resolve().parents[2]
        for name in ("templates/README.md.tpl", "README.md"):
            assert_projection(self, (root / name).read_text())

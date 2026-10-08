"""One responsive generated summary and independently usable text links."""
import unittest
from pathlib import Path
import re


class ReadmeProjectionContract(unittest.TestCase):
    def test_one_responsive_picture_and_native_equivalent(self):
        root=Path(__file__).resolve().parents[2]
        for name in ("templates/README.md.tpl","README.md"):
            text=(root/name).read_text()
            self.assertEqual(text.count("<picture>"),1)
            self.assertIn('media="(max-width: 767px)"',text)
            self.assertIn("assets/dashboard_summary_mobile.svg",text)
            self.assertIn("assets/dashboard_summary.svg",text)
            images=re.findall(r'<img\b[^>]+>',text)
            self.assertEqual(len(images),1)
            self.assertIn('width="100%"',images[0])
            self.assertIn("Read the numbers and definitions",text)
            self.assertIn("#weekly-contributions",text)
            self.assertNotIn('<img src="metrics.general.svg',text)

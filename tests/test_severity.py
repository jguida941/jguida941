import unittest

from scripts.severity import any_at_or_above, is_at_or_above


class SeverityTests(unittest.TestCase):
    def test_is_at_or_above(self):
        self.assertTrue(is_at_or_above("high", "medium"))
        self.assertFalse(is_at_or_above("low", "medium"))
        self.assertFalse(is_at_or_above("unknown", "low"))

    def test_any_at_or_above(self):
        items = [
            {"severity": "low"},
            {"severity": "medium"},
        ]
        self.assertTrue(any_at_or_above(items, "medium"))
        self.assertFalse(any_at_or_above(items, "high"))


if __name__ == "__main__":
    unittest.main()

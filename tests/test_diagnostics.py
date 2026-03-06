import unittest

from scripts.diagnostics import doctor_checks


class DiagnosticsTests(unittest.TestCase):
    def test_doctor_checks_returns_expected_shape(self):
        report = doctor_checks()
        self.assertIn("generated_at", report)
        self.assertIn("status", report)
        self.assertIn("checks", report)
        self.assertIsInstance(report["checks"], list)
        self.assertGreaterEqual(len(report["checks"]), 3)


if __name__ == "__main__":
    unittest.main()


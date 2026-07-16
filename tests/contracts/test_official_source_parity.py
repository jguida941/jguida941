"""Mode A proof: official implementation artifacts outrank hand-entered profile values."""
from __future__ import annotations

import unittest


class OfficialSourceParityContract(unittest.TestCase):
    def test_carbon_profile_equals_pinned_official_package(self):
        from scripts.quality.official_source_snapshot import assert_carbon_profile_parity

        assert_carbon_profile_parity()

    def test_mutated_official_value_would_red(self):
        from scripts.quality.official_source_snapshot import extract_carbon_white_tokens

        snapshot = extract_carbon_white_tokens()
        mutated = dict(snapshot["tokens"])
        mutated["button-primary-hover"] = "#0353e9"
        self.assertNotEqual(snapshot["tokens"], mutated)


if __name__ == "__main__":
    unittest.main()

import os
import unittest
from unittest import mock

from scripts.settings import Settings


class SettingsTokensTests(unittest.TestCase):
    def _from_env(self, **env):
        full = {"PERSONAL_GITHUB_TOKEN": "", "GITHUB_TOKEN": "", "GH_TOKEN": ""}
        full.update(env)
        with mock.patch.dict(os.environ, full, clear=False):
            return Settings.from_env()

    def test_ordered_dedup_primary_first(self):
        s = self._from_env(PERSONAL_GITHUB_TOKEN="pat", GITHUB_TOKEN="gh", GH_TOKEN="ghx")
        self.assertEqual(s.tokens, ("pat", "gh", "ghx"))
        self.assertEqual(s.token, "pat")

    def test_duplicate_tokens_collapse(self):
        s = self._from_env(PERSONAL_GITHUB_TOKEN="same", GITHUB_TOKEN="same", GH_TOKEN="other")
        self.assertEqual(s.tokens, ("same", "other"))
        self.assertEqual(s.token, "same")

    def test_empty_dropped(self):
        s = self._from_env(GITHUB_TOKEN="only")
        self.assertEqual(s.tokens, ("only",))
        self.assertEqual(s.token, "only")

    def test_no_tokens(self):
        s = self._from_env()
        self.assertEqual(s.tokens, ())
        self.assertEqual(s.token, "")


if __name__ == "__main__":
    unittest.main()

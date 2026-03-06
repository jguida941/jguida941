import os
import unittest
from unittest.mock import patch

from scripts.runtime_env import cache_mode_from_env, token_mode_from_env


class RuntimeEnvTests(unittest.TestCase):
    def test_token_mode_priority_order(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(token_mode_from_env(), "none")

        with patch.dict(os.environ, {"PROFILE_TOKEN_MODE": "personal_github_token"}, clear=True):
            self.assertEqual(token_mode_from_env(), "personal_github_token")

        with patch.dict(os.environ, {"GH_TOKEN": "x"}, clear=True):
            self.assertEqual(token_mode_from_env(), "gh_token")

        with patch.dict(os.environ, {"GITHUB_TOKEN": "x", "GH_TOKEN": "x"}, clear=True):
            self.assertEqual(token_mode_from_env(), "github_token")

        with patch.dict(
            os.environ,
            {"PERSONAL_GITHUB_TOKEN": "x", "GITHUB_TOKEN": "x", "GH_TOKEN": "x"},
            clear=True,
        ):
            self.assertEqual(token_mode_from_env(), "personal_github_token")

    def test_cache_mode_defaults_and_parsing(self):
        with patch.dict(os.environ, {}, clear=True):
            cache_mode = cache_mode_from_env()
        self.assertFalse(cache_mode["bypass"])
        self.assertEqual(cache_mode["ttl_seconds"], 21600)

        with patch.dict(
            os.environ,
            {"BYPASS_GITHUB_CACHE": "true", "CACHE_TTL_SECONDS": "120"},
            clear=True,
        ):
            cache_mode = cache_mode_from_env()
        self.assertTrue(cache_mode["bypass"])
        self.assertEqual(cache_mode["ttl_seconds"], 120)

        with patch.dict(os.environ, {"CACHE_TTL_SECONDS": "bad-value"}, clear=True):
            cache_mode = cache_mode_from_env()
        self.assertEqual(cache_mode["ttl_seconds"], 21600)


if __name__ == "__main__":
    unittest.main()

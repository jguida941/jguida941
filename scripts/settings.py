"""Unified settings for GitHub API access."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    username: str
    token: str
    cache_dir: Path
    cache_ttl_seconds: int
    bypass_cache: bool

    @staticmethod
    def from_env() -> "Settings":
        token = (
            os.environ.get("PERSONAL_GITHUB_TOKEN", "").strip()
            or os.environ.get("GITHUB_TOKEN", "").strip()
            or os.environ.get("GH_TOKEN", "").strip()
            or ""
        )
        ttl_raw = os.environ.get("CACHE_TTL_SECONDS", "21600")
        try:
            ttl_seconds = int(ttl_raw)
        except ValueError:
            ttl_seconds = 21600
        return Settings(
            username=os.environ.get("GITHUB_USERNAME", "jguida941"),
            token=token,
            cache_dir=Path(os.environ.get("CACHE_DIR", "/tmp/github_cache")),
            cache_ttl_seconds=ttl_seconds,
            bypass_cache=os.environ.get("BYPASS_GITHUB_CACHE", "").lower()
            in {"1", "true", "yes"},
        )

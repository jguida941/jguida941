"""Read runtime settings from environment variables."""

from __future__ import annotations

import os
from typing import Any


def token_mode_from_env() -> str:
    explicit_mode = os.environ.get("PROFILE_TOKEN_MODE", "").strip().lower()
    if explicit_mode in {
        "personal_github_token",
        "github_token",
        "gh_token",
        "none",
    }:
        return explicit_mode

    if os.environ.get("PERSONAL_GITHUB_TOKEN", "").strip():
        return "personal_github_token"
    if os.environ.get("GITHUB_TOKEN", "").strip():
        return "github_token"
    if os.environ.get("GH_TOKEN", "").strip():
        return "gh_token"
    return "none"


def cache_mode_from_env() -> dict[str, Any]:
    bypass_raw = os.environ.get("BYPASS_GITHUB_CACHE", "")
    bypass = bypass_raw.lower() in {"1", "true", "yes"}
    ttl_raw = os.environ.get("CACHE_TTL_SECONDS", "21600")
    try:
        ttl_seconds = int(ttl_raw)
    except ValueError:
        ttl_seconds = 21600
    return {
        "bypass": bypass,
        "ttl_seconds": ttl_seconds,
    }

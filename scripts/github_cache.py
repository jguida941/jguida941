"""Cache read/write logic for GitHub API responses."""

from __future__ import annotations

import json
import time
from pathlib import Path

from scripts.settings import Settings


def _cache_path(key: str, cache_dir: Path) -> Path:
    """Return the file path for a given cache key, creating the dir if needed."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    safe = key.replace("/", "__").replace("?", "_Q_").replace("&", "_A_")
    return cache_dir / f"{safe}.json"


def read_cache(key: str, settings: Settings):
    """Return cached data for *key*, or ``None`` when stale / missing / bypassed."""
    if settings.bypass_cache:
        return None

    p = _cache_path(key, settings.cache_dir)
    if p.exists():
        if settings.cache_ttl_seconds > 0:
            age_seconds = time.time() - p.stat().st_mtime
            if age_seconds > settings.cache_ttl_seconds:
                return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return None
    return None


def write_cache(key: str, data, settings: Settings) -> None:
    """Persist *data* under *key*."""
    p = _cache_path(key, settings.cache_dir)
    p.write_text(json.dumps(data), encoding="utf-8")

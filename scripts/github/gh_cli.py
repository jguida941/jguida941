"""Thin wrapper around the GitHub CLI (`gh`) for JSON output."""

from __future__ import annotations

import json
import subprocess
from typing import Any


def run_json(cmd: list[str], *, default: Any = None) -> Any:
    """Run a gh CLI command and parse its JSON output.

    Raises RuntimeError on gh not found, non-zero exit, or invalid JSON.
    Returns the parsed JSON (dict, list, etc.).
    """
    try:
        result = subprocess.run(
            cmd,
            check=True,
            text=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "GitHub CLI not found. Install `gh` to use this feature."
        ) from exc
    except subprocess.CalledProcessError as exc:
        message = (exc.stderr or exc.stdout or str(exc)).strip()
        raise RuntimeError(message) from exc

    raw = result.stdout or ""
    if not raw.strip():
        if default is not None:
            return default
        return {}

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Could not parse JSON output from `{cmd[0]} {cmd[1]}`"
        ) from exc

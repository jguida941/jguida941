#!/usr/bin/env python3
"""Backward-compatible wrapper for legacy build command usage.

Canonical entrypoint:
  python scripts/profile_cli.py generate-profile --validate
"""

from __future__ import annotations

import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from scripts.profile_cli import main as profile_cli_main


def main() -> int:
    return profile_cli_main(["generate-profile"])


if __name__ == "__main__":
    raise SystemExit(main())

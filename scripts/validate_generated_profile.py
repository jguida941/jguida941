#!/usr/bin/env python3
"""Compatibility wrapper for ``scripts.quality.validate_generated_profile``."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.quality.validate_generated_profile import main


if __name__ == "__main__":
    raise SystemExit(main())

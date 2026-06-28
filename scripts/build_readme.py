#!/usr/bin/env python3
"""Legacy wrapper: run ``scripts.cli.profile_cli`` 'generate-profile'."""

from __future__ import annotations

import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    os.chdir(ROOT)
    from scripts.cli.profile_cli import main as _main
    return _main(['generate-profile'])


if __name__ == "__main__":
    raise SystemExit(main())

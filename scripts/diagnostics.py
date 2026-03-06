"""Write command diagnostics so runs are easier to debug."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import sys
from typing import Any

from scripts.runtime_env import cache_mode_from_env, token_mode_from_env


def write_run_diagnostics(
    *,
    command: str,
    exit_code: int,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    extra: dict[str, Any] | None = None,
    output_path: str = "site/data/run_diagnostics.json",
    history_path: str = "site/data/run_diagnostics_history.jsonl",
) -> None:
    diagnostics = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "command": command,
        "exit_code": exit_code,
        "status": "ok" if exit_code == 0 else "error",
        "token_mode": token_mode_from_env(),
        "cache_mode": cache_mode_from_env(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "warnings": list(warnings or []),
        "errors": list(errors or []),
        "extra": extra or {},
    }
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(diagnostics, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    history = Path(history_path)
    history.parent.mkdir(parents=True, exist_ok=True)
    with history.open("a", encoding="utf-8") as file:
        file.write(json.dumps(diagnostics, ensure_ascii=True) + "\n")


def doctor_checks() -> dict[str, Any]:
    checks = []

    def add_check(name: str, ok: bool, detail: str, severity: str = "info") -> None:
        checks.append(
            {
                "name": name,
                "ok": ok,
                "severity": severity,
                "detail": detail,
            }
        )

    add_check(
        "python_version",
        sys.version_info >= (3, 10),
        f"Python {platform.python_version()}",
        severity="critical",
    )
    add_check(
        "token_mode",
        token_mode_from_env() != "none",
        f"token_mode={token_mode_from_env()}",
        severity="high",
    )
    add_check(
        "readme_template_exists",
        Path("templates/README.md.tpl").exists(),
        "templates/README.md.tpl exists" if Path("templates/README.md.tpl").exists() else "template missing",
        severity="critical",
    )
    add_check(
        "scripts_folder_exists",
        Path("scripts").exists(),
        "scripts folder exists" if Path("scripts").exists() else "scripts folder missing",
        severity="critical",
    )

    status = "ok" if all(check["ok"] for check in checks) else "issues_found"
    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": status,
        "checks": checks,
    }

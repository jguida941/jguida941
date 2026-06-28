"""Audit the live scripts package against the semantic layout contract."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scripts.organization.layout_contract import (
    ROOT_ENTRYPOINT_SHIMS,
    allowed_python_paths,
    module_homes_by_source,
)


@dataclass(frozen=True)
class LayoutFinding:
    kind: str
    path: str
    detail: str

    @property
    def finding_id(self) -> str:
        return f"{self.kind}:{self.path}"


def audit_scripts_layout(repo_root: Path | str) -> list[LayoutFinding]:
    root = Path(repo_root)
    scripts_root = root / "scripts"
    findings: list[LayoutFinding] = []
    declared_by_source = module_homes_by_source()
    allowed_paths = allowed_python_paths()

    if not scripts_root.exists():
        return [LayoutFinding("missing_root", "scripts", "scripts package is missing")]

    live_paths = {
        path.relative_to(root).as_posix()
        for path in scripts_root.rglob("*.py")
        if "__pycache__" not in path.parts
    }

    for path in sorted(live_paths):
        if path in allowed_paths:
            continue
        if path in declared_by_source:
            home = declared_by_source[path]
            findings.append(
                LayoutFinding(
                    "misplaced_module",
                    path,
                    f"{home.meaning}: move {path} -> {home.target_path}",
                )
            )
            continue
        if path.count("/") == 1 and path not in ROOT_ENTRYPOINT_SHIMS:
            findings.append(
                LayoutFinding(
                    "undeclared_flat_module",
                    path,
                    f"{path} is flat under scripts/ and has no semantic home",
                )
            )
            continue
        findings.append(
            LayoutFinding(
                "undeclared_module",
                path,
                f"{path} is not declared in the scripts layout contract",
            )
        )

    for target_path, home in sorted(
        ((home.target_path, home) for home in declared_by_source.values()),
        key=lambda item: item[0],
    ):
        if target_path not in live_paths and home.source_path not in live_paths:
            findings.append(
                LayoutFinding(
                    "missing_declared_module",
                    target_path,
                    f"{home.meaning}: expected {target_path}",
                )
            )

    return findings

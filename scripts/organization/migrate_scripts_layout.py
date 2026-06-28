"""Move the scripts package into its semantic layout contract.

The machinery mirrors the sibling ``scripts/organization`` tooling: it only
moves modules declared in :mod:`scripts.organization.layout_contract` and
rewrites imports by module-name string replacement (longest-first so that a
shorter module name can never clobber a longer one that shares its prefix).

Adaptations for this repository's nested layout:

* the contract renames several modules, so the rewrite has to cope with
  ``__init__`` collisions (``scripts/contracts/schema.py`` becomes the package
  ``scripts/contracts/__init__.py``);
* the public entrypoint shims live at fixed root paths
  (``scripts/profile_cli.py``, ``scripts/build_readme.py``,
  ``scripts/validate_generated_profile.py``) rather than at each module's old
  source path; and
* the now-empty legacy package directories are removed after the moves.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil

from scripts.organization.layout_contract import (
    MODULE_HOMES,
    PACKAGE_INIT_PATHS,
    import_rewrite_map,
)

# Directories that are fully dissolved by the migration; whatever remains in
# them after the declared modules move out (placeholder ``__init__.py`` files,
# the legacy ``build_readme`` wrapper) is intentionally discarded.
OBSOLETE_DIRS: tuple[str, ...] = (
    "scripts/analytics",
    "scripts/render",
    "scripts/diagnostics",
)

# The three public entrypoint shims and the real modules they delegate to. The
# build_readme wrapper preserves its historical behaviour of invoking the
# ``generate-profile`` subcommand.
ENTRYPOINT_SHIMS: dict[str, tuple[str, str | None]] = {
    "scripts/profile_cli.py": ("scripts.cli.profile_cli", None),
    "scripts/validate_generated_profile.py": ("scripts.quality.validate_generated_profile", None),
    "scripts/build_readme.py": ("scripts.cli.profile_cli", "generate-profile"),
}


def planned_moves(repo_root: Path | str) -> list[tuple[Path, Path]]:
    root = Path(repo_root)
    moves: list[tuple[Path, Path]] = []
    for home in MODULE_HOMES:
        source = root / home.source_path
        target = root / home.target_path
        if source == target:
            continue
        if home.public_entrypoint and source.exists() and target.exists():
            continue
        if source.exists():
            moves.append((source, target))
    return moves


def rewrite_python_imports(repo_root: Path | str) -> list[Path]:
    root = Path(repo_root)
    rewrites = import_rewrite_map()
    changed: list[Path] = []
    paths: list[Path] = []
    for subtree in ("scripts", "tests"):
        base = root / subtree
        if base.exists():
            paths.extend(base.rglob("*.py"))
    for path in sorted(paths):
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        updated = text
        for old_module, new_module in sorted(rewrites.items(), key=lambda item: -len(item[0])):
            updated = updated.replace(f"from {old_module} import", f"from {new_module} import")
            updated = updated.replace(f"import {old_module}", f"import {new_module}")
            updated = updated.replace(f'"{old_module}.', f'"{new_module}.')
            updated = updated.replace(f"'{old_module}.", f"'{new_module}.")
            updated = updated.replace(f'"{old_module}"', f'"{new_module}"')
            updated = updated.replace(f"'{old_module}'", f"'{new_module}'")
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            changed.append(path)
    return changed


def apply_moves(repo_root: Path | str) -> list[tuple[Path, Path]]:
    root = Path(repo_root)
    moves = planned_moves(root)
    for source, target in moves:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            # The only legitimate collision is a placeholder package
            # ``__init__.py`` that a renamed module is meant to populate
            # (e.g. ``scripts/contracts/schema.py`` -> ``__init__.py``).
            if target.read_text(encoding="utf-8").strip():
                raise FileExistsError(f"target already exists: {target}")
            target.unlink()
        shutil.move(str(source), str(target))
    _write_package_inits(root)
    _write_entrypoint_shims(root)
    _remove_obsolete_dirs(root)
    return moves


def _write_package_inits(root: Path) -> None:
    for init_path in sorted(PACKAGE_INIT_PATHS):
        path = root / init_path
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('"""Semantic scripts package."""\n', encoding="utf-8")


def _write_entrypoint_shims(root: Path) -> None:
    for shim_path, (target_module, subcommand) in ENTRYPOINT_SHIMS.items():
        path = root / shim_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if subcommand is None:
            path.write_text(
                "#!/usr/bin/env python3\n"
                f'"""Compatibility wrapper for ``{target_module}``."""\n\n'
                "from __future__ import annotations\n\n"
                "from pathlib import Path\n"
                "import sys\n\n"
                "ROOT = Path(__file__).resolve().parent.parent\n"
                "if str(ROOT) not in sys.path:\n"
                "    sys.path.insert(0, str(ROOT))\n\n"
                f"from {target_module} import main\n\n\n"
                'if __name__ == "__main__":\n'
                "    raise SystemExit(main())\n",
                encoding="utf-8",
            )
        else:
            path.write_text(
                "#!/usr/bin/env python3\n"
                f'"""Legacy wrapper: run ``{target_module}`` {subcommand!r}."""\n\n'
                "from __future__ import annotations\n\n"
                "import os\n"
                "from pathlib import Path\n"
                "import sys\n\n"
                "ROOT = Path(__file__).resolve().parent.parent\n"
                "if str(ROOT) not in sys.path:\n"
                "    sys.path.insert(0, str(ROOT))\n\n\n"
                "def main() -> int:\n"
                "    os.chdir(ROOT)\n"
                f"    from {target_module} import main as _main\n"
                f"    return _main([{subcommand!r}])\n\n\n"
                'if __name__ == "__main__":\n'
                "    raise SystemExit(main())\n",
                encoding="utf-8",
            )


def _remove_obsolete_dirs(root: Path) -> None:
    for rel in OBSOLETE_DIRS:
        path = root / rel
        if path.exists():
            shutil.rmtree(path)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(_repo_root()))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="show whether moves remain")
    mode.add_argument("--plan", action="store_true", help="print planned moves")
    mode.add_argument("--apply", action="store_true", help="apply moves and rewrite imports")
    args = parser.parse_args(argv)

    root = Path(args.repo_root).resolve()
    moves = planned_moves(root)

    if args.check:
        return 1 if moves else 0

    if args.plan:
        if not moves:
            print("No script layout moves remain.")
        for source, target in moves:
            print(f"{source.relative_to(root)} -> {target.relative_to(root)}")
        return 0

    applied = apply_moves(root)
    changed = rewrite_python_imports(root)
    print(f"Applied {len(applied)} move(s).")
    print(f"Rewrote {len(changed)} Python file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

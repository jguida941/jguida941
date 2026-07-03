"""Executable helpers for contracts/page_manifest.json.

`render_source` is not descriptive metadata: it names the producer that must reproduce the
committed route bytes. This module keeps the import/render rules out of the test body so the
manifest contract can exercise the same parser on real and forged entries.
"""
from __future__ import annotations

import importlib
import inspect
import json
import re
from pathlib import Path
from typing import Callable


def repo_root() -> Path:
    for p in Path(__file__).resolve().parents:
        if (p / "contracts" / "page_manifest.json").is_file():
            return p
    raise RuntimeError("repo root not found")


def committed_receipts(root: Path | None = None) -> dict:
    root = root or repo_root()
    idx = json.loads((root / "contracts" / "design_profiles" / "_index.json").read_text(encoding="utf-8"))
    out = {}
    for name in idx["active_design_profiles"]:
        path = root / "assets" / "receipts" / name / "conformance_receipt.json"
        out[name] = json.loads(path.read_text(encoding="utf-8"))
    return out


def resolve_render_source(render_source: str, root: Path | None = None) -> Callable:
    root = root or repo_root()
    m = re.fullmatch(r"(?P<module>[\w/]+\.py)::(?P<func>[A-Za-z_]\w*)", render_source or "")
    if not m:
        raise ValueError(f"render_source {render_source!r} must use 'path/to/module.py::function'")
    module_path = Path(m.group("module"))
    if module_path.is_absolute() or ".." in module_path.parts:
        raise ValueError(f"render_source {render_source!r} must be a repo-relative module path")
    if not (root / module_path).is_file():
        raise ImportError(f"render_source module does not exist: {module_path.as_posix()}")

    module_name = ".".join(module_path.with_suffix("").parts)
    func = getattr(importlib.import_module(module_name), m.group("func"))
    if not callable(func):
        raise TypeError(f"render_source target is not callable: {render_source!r}")
    return func


def render_manifest_page(page: dict, root: Path | None = None) -> str:
    root = root or repo_root()
    func = resolve_render_source(page.get("render_source", ""), root)
    required = [
        p for p in inspect.signature(func).parameters.values()
        if p.default is inspect.Parameter.empty
        and p.kind in (inspect.Parameter.POSITIONAL_ONLY,
                       inspect.Parameter.POSITIONAL_OR_KEYWORD,
                       inspect.Parameter.KEYWORD_ONLY)
    ]
    if not required:
        html = func()
    elif len(required) == 1 and required[0].name == "receipts":
        html = func(committed_receipts(root))
    else:
        raise TypeError(f"{page['id']}: unsupported render_source signature for {page['render_source']}")
    if not isinstance(html, str):
        raise TypeError(f"{page['id']}: render_source must return HTML bytes as str")
    return html

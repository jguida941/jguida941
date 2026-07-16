"""Load, close, and index committed design-source clause catalogs."""
from __future__ import annotations

import json
from pathlib import Path

from .schema import validate_documents


def _root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "contracts" / "design_sources").is_dir():
            return parent
    raise RuntimeError("repo root not found")


def load_documents(*, validate: bool = True) -> list[dict]:
    home = _root() / "contracts" / "design_sources"
    index = json.loads((home / "_index.json").read_text(encoding="utf-8"))
    if set(index) != {"contract_id", "schema_version", "catalogs"} \
            or index["contract_id"] != "DesignSourceCatalogIndex" or index["schema_version"] != 1:
        raise ValueError("design-source catalog index drift")
    names = index["catalogs"]
    if not isinstance(names, list) or not names or len(names) != len(set(names)):
        raise ValueError("design-source catalogs must be a unique nonempty list")
    on_disk = {path.name for path in home.glob("*.json") if path.name != "_index.json"}
    if set(names) != on_disk:
        raise ValueError("design-source index/files closed-cover drift")
    documents = [json.loads((home / name).read_text(encoding="utf-8")) for name in names]
    if validate:
        validate_documents(documents)
        _validate_source_refs(documents)
    return documents


def _validate_source_refs(documents: list[dict]) -> None:
    root = _root()
    for document in documents:
        for clause in document["clauses"]:
            for source in clause["sources"]:
                ref = source["ref"]
                kind = source["source_kind"]
                if kind == "official-doc":
                    if not ref.startswith("https://"):
                        raise ValueError(f"{clause['clause_id']}: official doc must use https")
                elif not (root / ref.split("#", 1)[0]).is_file():
                    raise ValueError(f"{clause['clause_id']}: missing committed source {ref}")


def load_catalog() -> dict[str, dict]:
    return {
        clause["clause_id"]: clause
        for document in load_documents()
        for clause in document["clauses"]
    }


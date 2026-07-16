"""Closed schema for source-backed design doctrine clauses."""
from __future__ import annotations


AUTHORITY_MODES = {
    "official-code": ("official-code", "source-exact"),
    "official-docs": ("official-spec", "specification-exact"),
    "approved-reference": ("measured-reference", "measurement-exact"),
    "owner-ratified": ("owner-ratified", "specification-exact"),
}
SOURCE_KINDS = {"official-doc", "official-package", "approved-reference", "repo-doctrine"}


def _closed(row: dict, keys: set[str], *, label: str) -> None:
    if not isinstance(row, dict) or set(row) != keys:
        raise ValueError(f"{label} must have exactly {sorted(keys)}")


def validate_documents(documents: list[dict]) -> None:
    """Validate catalog documents without consulting the filesystem."""
    seen: set[str] = set()
    for position, document in enumerate(documents):
        _closed(document, {"contract_id", "schema_version", "clauses"}, label=f"catalog/{position}")
        if document["contract_id"] != "DesignSourceClauseCatalog" or document["schema_version"] != 1:
            raise ValueError("design-source catalog identity/version drift")
        if not isinstance(document["clauses"], list):
            raise ValueError("catalog clauses must be a list")
        for clause in document["clauses"]:
            _closed(clause, {
                "clause_id", "claim", "authority", "source_mode", "exactness", "sources", "scope",
            }, label="clause")
            clause_id = clause["clause_id"]
            if not isinstance(clause_id, str) or not clause_id or clause_id in seen:
                raise ValueError(f"duplicate or empty clause_id: {clause_id!r}")
            seen.add(clause_id)
            expected = AUTHORITY_MODES.get(clause["authority"])
            if expected != (clause["source_mode"], clause["exactness"]):
                raise ValueError(f"incoherent authority tuple for {clause_id}")
            if not isinstance(clause["claim"], str) or not clause["claim"]:
                raise ValueError(f"{clause_id}: claim is required")
            if not isinstance(clause["sources"], list) or not clause["sources"]:
                raise ValueError(f"{clause_id}: sources must be nonempty")
            for source in clause["sources"]:
                _closed(source, {"source_kind", "ref"}, label=f"{clause_id}/source")
                if source["source_kind"] not in SOURCE_KINDS or not isinstance(source["ref"], str) \
                        or not source["ref"]:
                    raise ValueError(f"{clause_id}: invalid source")
            _closed(clause["scope"], {"profiles", "aspects", "invariant_ids"}, label=f"{clause_id}/scope")
            for key, values in clause["scope"].items():
                if not isinstance(values, list) or not values or len(values) != len(set(values)) \
                        or not all(isinstance(value, str) and value for value in values):
                    raise ValueError(f"{clause_id}: scope {key} must be a unique nonempty string list")


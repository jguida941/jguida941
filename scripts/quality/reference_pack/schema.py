"""Closed manifest validation for approved rendered-reference packs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SOURCE_MODES = {"official-code", "official-spec", "measured-reference", "owner-ratified"}
EXACTNESS = {"source-exact", "specification-exact", "measurement-exact", "perceptual"}


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("reference-pack manifest must be an object")
    return value


def validate_manifest(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {
        "contract_id", "schema_version", "authority_status", "cannot_mark_done",
        "capture_status", "approval", "frozen_source", "matrix", "aspect_ownership",
        "official_precedence_exclusions", "captures",
    }
    if set(value) != required:
        errors.append("manifest keys are not the closed schema")
    if value.get("schema_version") != 1:
        errors.append("unsupported schema_version")
    if value.get("authority_status") != "operator-approved-reference":
        errors.append("authority_status must name operator approval")
    if value.get("capture_status") not in {"pending", "frozen"}:
        errors.append("capture_status must be pending or frozen")
    approval = value.get("approval")
    if not isinstance(approval, dict) or set(approval) != {"clause_id", "approved_at", "evidence_ref", "scope"}:
        errors.append("approval row is malformed")
    source = value.get("frozen_source")
    if not isinstance(source, dict) or set(source) != {
        "revision_label", "source_artifact", "source_sha256", "renderer_source_sha256", "fixture"
    }:
        errors.append("frozen_source row is malformed")
    matrix = value.get("matrix")
    if not isinstance(matrix, dict) or set(matrix) != {"themes", "viewports", "states"}:
        errors.append("matrix is malformed")
    ownership = value.get("aspect_ownership")
    if not isinstance(ownership, dict) or not ownership:
        errors.append("aspect_ownership must be a non-empty object")
    else:
        for aspect, row in ownership.items():
            if not isinstance(row, dict):
                errors.append(f"{aspect}: ownership row must be an object")
                continue
            if row.get("source_mode") not in SOURCE_MODES:
                errors.append(f"{aspect}: invalid source_mode")
            if row.get("exactness") not in EXACTNESS:
                errors.append(f"{aspect}: invalid exactness")
    if not isinstance(value.get("captures"), list):
        errors.append("captures must be a list")
    return errors

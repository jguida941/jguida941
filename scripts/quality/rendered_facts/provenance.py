"""Closed provenance validation for one canonical Chrome rendered-fact artifact."""
from __future__ import annotations

import hashlib
import re
from urllib.parse import parse_qs, urlparse

from scripts.quality.rendered_facts.codec import (
    compressed_packet_bytes, decode_packet_bytes, packet_bytes,
)
from scripts.quality.rendered_facts.policy import (
    RENDERED_FACT_KIND, artifact_path, load_policy, page_routes, root,
)


def _validate_command(command: object, *, page: str, theme: str, viewport: int) -> None:
    policy = load_policy()
    spec = policy["producer_command"]
    row = next(row for row in policy["matrix"]["viewports"] if row["width"] == viewport)
    expected = [spec["chrome_path"], *spec["fixed_arguments"],
                f"--force-device-scale-factor={row['device_scale_factor']}",
                f"--window-size={max(800, viewport + 80)},{row['height'] + 100}",
                f"--virtual-time-budget={spec['virtual_time_budget_ms']}", "--dump-dom"]
    if not isinstance(command, list) or command[:-1] != expected or len(command) != len(expected) + 1:
        raise RuntimeError("rendered fact Chrome command differs from the closed producer argv")
    parsed = urlparse(command[-1])
    if (parsed.scheme != spec["probe_scheme"] or parsed.hostname != spec["probe_host"]
            or parsed.path != spec["probe_path"] or parsed.username is not None
            or parsed.password is not None or parsed.fragment
            or parsed.port is None or not 1 <= parsed.port <= 65535):
        raise RuntimeError("rendered fact Chrome command has an invalid probe origin")
    query = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True)
    expected_query = {"page": [page], "theme": [theme], "viewport": [str(viewport)],
                      "height": [str(row["height"])]}
    if query != expected_query:
        raise RuntimeError("rendered fact Chrome command has an invalid probe query")


def validate_provenance(
    payload: dict, provenance: dict, *, page: str, theme: str, viewport: int,
    artifact_bytes: bytes | None = None,
) -> None:
    artifact = artifact_path(page, theme, viewport)
    canonical = packet_bytes(payload)
    encoded = compressed_packet_bytes(payload) if artifact_bytes is None else artifact_bytes
    encoding = load_policy()["artifact_encoding"]
    expected_fields = {
        "artifact", "artifact_sha256", "authority_status", "cannot_mark_done",
        "capture_origin", "chrome_version", "command", "compression", "content_sha256",
        "contract_id", "gzip_mtime", "inputs", "kind", "page", "page_sha256",
        "producer", "python_version", "route", "state_ids", "theme", "viewport", "writer",
        "zlib_runtime_version", "zlib_version",
    }
    if not isinstance(provenance, dict) or set(provenance) != expected_fields:
        raise RuntimeError("rendered fact provenance fields are not closed")
    if (provenance["contract_id"] != "PageHeadlessReceiptProvenance"
            or provenance["authority_status"] != "candidate_only"
            or provenance["cannot_mark_done"] is not True
            or provenance["capture_origin"] != "ephemeral-local-http"
            or provenance["producer"] != "scripts/quality/headless_receipts.py"
            or provenance["kind"] != RENDERED_FACT_KIND):
        raise RuntimeError("rendered fact provenance authority/producer mismatch")
    if (provenance["page"] != page or provenance["route"] != page_routes()[page]
            or provenance["theme"] != theme):
        raise RuntimeError("rendered fact provenance page/theme mismatch")
    if decode_packet_bytes(encoded) != payload or encoded != compressed_packet_bytes(payload):
        raise RuntimeError("rendered fact artifact is not the exact canonical writer output")
    if (provenance["artifact"] != artifact.relative_to(root()).as_posix()
            or provenance["artifact_sha256"] != hashlib.sha256(encoded).hexdigest()
            or provenance["content_sha256"] != hashlib.sha256(canonical).hexdigest()):
        raise RuntimeError("rendered fact artifact/content hash mismatch")
    if (provenance["compression"] != encoding["compression"]
            or provenance["gzip_mtime"] != encoding["mtime"]
            or provenance["writer"] != encoding["writer"]):
        raise RuntimeError("rendered fact compression provenance mismatch")
    runtime = encoding["writer_runtime"]
    if any(provenance[key] != runtime[key] for key in runtime):
        raise RuntimeError("rendered fact compression runtime is not admitted")
    if (provenance["page_sha256"] != payload["inputs"]["page_sha256"]
            or provenance["inputs"] != payload["inputs"]
            or provenance["state_ids"] != [row["state_id"] for row in payload["states"]]
            or provenance["viewport"] != payload["viewport"]):
        raise RuntimeError("rendered fact provenance facts mismatch")
    _validate_command(provenance["command"], page=page, theme=theme, viewport=viewport)
    pattern = load_policy()["producer_command"]["chrome_version_pattern"]
    if not isinstance(provenance["chrome_version"], str) or not re.fullmatch(
        pattern, provenance["chrome_version"]
    ):
        raise RuntimeError("rendered fact provenance has an invalid Chrome version")

"""Bounded canonical JSON and deterministic single-member gzip transport."""
from __future__ import annotations

import gzip
import io
import json
import zlib

from scripts.quality.rendered_facts.policy import load_policy


def packet_bytes(payload: dict) -> bytes:
    return (json.dumps(payload, allow_nan=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def _reject_json_constant(value: str):
    raise ValueError(f"nonfinite JSON constant {value!r}")


def compressed_packet_bytes(payload: dict) -> bytes:
    """Encode canonical packet bytes in the one allowed deterministic gzip envelope."""
    policy = load_policy()["artifact_encoding"]
    raw = packet_bytes(payload)
    if len(raw) > policy["max_uncompressed_bytes"]:
        raise RuntimeError("rendered fact packet exceeds the uncompressed-byte cap")
    output = io.BytesIO()
    with gzip.GzipFile(
        filename=policy["filename"], mode="wb", compresslevel=policy["compresslevel"],
        fileobj=output, mtime=policy["mtime"],
    ) as archive:
        archive.write(raw)
    encoded = output.getvalue()
    if (encoded[:3] != b"\x1f\x8b\x08"
            or encoded[3] != policy["header_flags"]
            or int.from_bytes(encoded[4:8], "little") != policy["mtime"]
            or encoded[8] != policy["header_xfl"]
            or encoded[9] != policy["header_os"]):
        raise RuntimeError("rendered fact writer emitted a noncanonical gzip header")
    return encoded


def decode_packet_bytes(encoded: bytes) -> dict:
    """Decode exactly one bounded gzip member and require canonical JSON packet bytes."""
    policy = load_policy()["artifact_encoding"]
    if len(encoded) < 18 or encoded[:3] != b"\x1f\x8b\x08":
        raise RuntimeError("rendered fact artifact is not a complete gzip member")
    if (encoded[3] != policy["header_flags"]
            or int.from_bytes(encoded[4:8], "little") != policy["mtime"]
            or encoded[8] != policy["header_xfl"]
            or encoded[9] != policy["header_os"]):
        raise RuntimeError("rendered fact artifact has a noncanonical gzip header")
    decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
    limit = policy["max_uncompressed_bytes"]
    try:
        raw = decoder.decompress(encoded, limit + 1)
    except zlib.error as exc:
        raise RuntimeError("rendered fact gzip member is corrupt") from exc
    if len(raw) > limit or decoder.unconsumed_tail:
        raise RuntimeError("rendered fact artifact exceeds the uncompressed-byte cap")
    if not decoder.eof:
        raise RuntimeError("rendered fact gzip member is truncated")
    if decoder.unused_data:
        raise RuntimeError("rendered fact artifact contains trailing data or another member")
    try:
        payload = json.loads(raw.decode("utf-8"), parse_constant=_reject_json_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError("rendered fact payload is not UTF-8 JSON") from exc
    if raw != packet_bytes(payload):
        raise RuntimeError("rendered fact payload bytes are not canonical JSON")
    return payload

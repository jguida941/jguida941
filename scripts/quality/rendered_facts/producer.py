"""Transport-injected Chrome producer for committed rendered-fact cells."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import uuid
import zlib
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Protocol
from urllib.parse import urlencode

from scripts.quality.rendered_facts.policy import (
    RENDERED_FACT_KIND,
    active_profiles,
    artifact_path,
    load_policy,
    page_routes,
    receipt_dir,
)
from scripts.quality.rendered_facts.schema import (
    compressed_packet_bytes,
    packet_bytes,
    validate_packet,
    validate_provenance,
)


class RenderedFactsRuntime(Protocol):
    """Browser and receipt services supplied by the headless compatibility facade."""

    def site_server(self) -> AbstractContextManager[str]: ...

    def chrome(self) -> Path: ...

    def chrome_version(self, chrome: Path) -> str: ...

    def run(self, command: list[str]) -> subprocess.CompletedProcess[str]: ...

    def parse_probe_dump(self, dump: str) -> dict: ...

    def write_provenance(
        self,
        *,
        page: str,
        artifact: Path,
        kind: str,
        command: list[str],
        chrome_version: str,
        viewport: dict,
        extra: dict | None = None,
    ) -> Path: ...


def _capture(
    runtime: RenderedFactsRuntime,
    page: str,
    theme: str,
    viewport: int,
    *,
    base_url: str,
) -> dict:
    policy = load_policy()
    viewport_rows = {row["width"]: row for row in policy["matrix"]["viewports"]}
    if viewport not in viewport_rows:
        raise ValueError(f"viewport {viewport} is outside the rendered fact matrix")
    row = viewport_rows[viewport]
    query = urlencode({
        "page": page,
        "theme": theme,
        "viewport": viewport,
        "height": row["height"],
    })
    url = f"{base_url}/__rendered_facts__.html?{query}"
    chrome = runtime.chrome()
    command = [
        str(chrome),
        "--headless=new",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--run-all-compositor-stages-before-draw",
        f"--force-device-scale-factor={row['device_scale_factor']}",
        f"--window-size={max(800, viewport + 80)},{row['height'] + 100}",
        "--virtual-time-budget=30000",
        "--dump-dom",
        url,
    ]
    last_error: Exception | None = None
    for _attempt in range(3):
        try:
            payload = runtime.parse_probe_dump(runtime.run(command).stdout)
            if payload.get("error"):
                raise RuntimeError(
                    f"{page}/{theme}/{viewport}: browser probe failed: {payload['error']}"
                )
            validate_packet(payload, page=page, theme=theme, viewport=viewport)
            break
        except (RuntimeError, subprocess.SubprocessError) as exc:
            last_error = exc
    else:
        raise RuntimeError(
            f"{page}/{theme}/{viewport}: rendered fact capture did not validate after 3 attempts"
        ) from last_error
    return {
        "payload": payload,
        "command": command,
        "chrome_version": runtime.chrome_version(chrome),
        "viewport": row,
    }


def capture(
    runtime: RenderedFactsRuntime,
    page: str,
    theme: str,
    viewport: int,
    *,
    base_url: str | None = None,
) -> Path:
    """Capture and atomically publish one rendered-fact cell and its provenance."""
    admitted = load_policy()["artifact_encoding"]["writer_runtime"]
    observed = {"python_version": platform.python_version(),
                "zlib_version": zlib.ZLIB_VERSION,
                "zlib_runtime_version": zlib.ZLIB_RUNTIME_VERSION}
    if observed != admitted:
        raise RuntimeError(f"rendered fact writer runtime is not admitted: {observed!r}")
    if base_url is None:
        with runtime.site_server() as local_url:
            return capture(runtime, page, theme, viewport, base_url=local_url)
    result = _capture(runtime, page, theme, viewport, base_url=base_url)
    payload = result["payload"]
    receipt_dir(page, create=True)
    artifact = artifact_path(page, theme, viewport)
    staged = artifact.with_name(f".{artifact.name}.{uuid.uuid4().hex}.tmp")
    encoded = compressed_packet_bytes(payload)
    staged.write_bytes(encoded)
    os.replace(staged, artifact)
    provenance_path = runtime.write_provenance(
        page=page,
        artifact=artifact,
        kind=RENDERED_FACT_KIND,
        command=result["command"],
        chrome_version=result["chrome_version"],
        viewport=result["viewport"],
        extra={
            "capture_origin": "ephemeral-local-http",
            "theme": theme,
            "inputs": payload["inputs"],
            "state_ids": [row["state_id"] for row in payload["states"]],
            "compression": load_policy()["artifact_encoding"]["compression"],
            "gzip_mtime": load_policy()["artifact_encoding"]["mtime"],
            "writer": load_policy()["artifact_encoding"]["writer"],
            "content_sha256": hashlib.sha256(packet_bytes(payload)).hexdigest(),
            "python_version": platform.python_version(),
            "zlib_version": zlib.ZLIB_VERSION,
            "zlib_runtime_version": zlib.ZLIB_RUNTIME_VERSION,
        },
    )
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    validate_provenance(
        payload,
        provenance,
        page=page,
        theme=theme,
        viewport=viewport,
        artifact_bytes=encoded,
    )
    return artifact


def write_all(runtime: RenderedFactsRuntime) -> list[Path]:
    """Publish the exact page x theme x viewport matrix under one local server."""
    policy = load_policy()
    out: list[Path] = []
    with runtime.site_server() as base_url:
        for page in page_routes():
            for theme in active_profiles():
                for row in policy["matrix"]["viewports"]:
                    out.append(capture(
                        runtime, page, theme, row["width"], base_url=base_url))
    return out

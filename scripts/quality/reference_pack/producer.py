"""Freeze the operator-approved pre-W3 dashboard reference pack."""

from __future__ import annotations

import gzip
import json
import shutil
import tempfile
from pathlib import Path

from .browser import capture, chrome_version, reference_server
from .codec import canonical_json, sha256_path
from .schema import load_manifest, validate_manifest


def write_dashboard_reference_pack(*, root: Path) -> list[Path]:
    manifest_path = root / "contracts/reference_packs/dashboard-pre-w3/manifest.json"
    manifest = load_manifest(manifest_path)
    errors = validate_manifest(manifest)
    if errors:
        raise RuntimeError(f"invalid reference manifest: {errors}")
    source = root / manifest["frozen_source"]["source_artifact"]
    fixture = root / manifest["frozen_source"]["fixture"]
    if sha256_path(source) == manifest["frozen_source"]["source_sha256"]:
        raise RuntimeError("source_artifact hash must describe decompressed source bytes")
    source_html = gzip.decompress(source.read_bytes())
    import hashlib
    if hashlib.sha256(source_html).hexdigest() != manifest["frozen_source"]["source_sha256"]:
        raise RuntimeError("frozen source hash mismatch")
    if not fixture.is_file():
        raise FileNotFoundError(fixture)

    out = root / "assets/receipts/reference-packs/dashboard-pre-w3"
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    captures: list[dict] = []
    version = chrome_version()
    with tempfile.TemporaryDirectory(prefix="dashboard-reference-") as temp:
        temp_root = Path(temp)
        (temp_root / "site/data").mkdir(parents=True)
        (temp_root / "site/index.html").write_bytes(source_html)
        shutil.copyfile(fixture, temp_root / "site/data/profile_snapshot.json")
        with reference_server(temp_root) as base_url:
            for viewport in manifest["matrix"]["viewports"]:
                width, height = viewport["width"], viewport["height"]
                for theme in manifest["matrix"]["themes"]:
                    stem = f"{theme}-{width}"
                    screenshot = out / f"{stem}.png"
                    facts_path = out / f"{stem}.facts.json"
                    provenance_path = out / f"{stem}.provenance.json"
                    facts, command = capture(
                        base_url=base_url, theme=theme, width=width, height=height,
                        screenshot=screenshot,
                    )
                    facts_path.write_bytes(canonical_json(facts))
                    provenance = {
                        "contract_id": "ApprovedReferenceCaptureProvenance",
                        "schema_version": 1,
                        "approval_clause": manifest["approval"]["clause_id"],
                        "authority": "approved-reference",
                        "source_mode": "measured-reference",
                        "exactness": "measurement-exact",
                        "captured_at": manifest["approval"]["approved_at"],
                        "chrome_version": version,
                        "command": command,
                        "source_sha256": manifest["frozen_source"]["source_sha256"],
                        "fixture_sha256": sha256_path(fixture),
                        "screenshot_sha256": sha256_path(screenshot),
                        "facts_sha256": sha256_path(facts_path),
                        "scope": {"theme": theme, "viewport": viewport, "state": "default"},
                    }
                    provenance_path.write_bytes(canonical_json(provenance))
                    captures.append({
                        "theme": theme,
                        "viewport": viewport,
                        "state": "default",
                        "screenshot": {"path": screenshot.relative_to(root).as_posix(), "sha256": sha256_path(screenshot)},
                        "facts": {"path": facts_path.relative_to(root).as_posix(), "sha256": sha256_path(facts_path)},
                        "provenance": {"path": provenance_path.relative_to(root).as_posix(), "sha256": sha256_path(provenance_path)},
                    })
                    written.extend((screenshot, facts_path, provenance_path))
    manifest["capture_status"] = "frozen"
    manifest["cannot_mark_done"] = False
    manifest["captures"] = sorted(captures, key=lambda row: (row["theme"], row["viewport"]["width"]))
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    written.append(manifest_path)
    return written

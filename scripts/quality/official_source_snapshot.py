"""Extract source-exact tokens from pinned official design-system artifacts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import tarfile


CARBON_TOKEN_NAMES = (
    "background", "border-subtle-01", "border-subtle-02", "button-primary",
    "button-primary-active", "button-primary-hover", "focus", "focus-inset",
    "layer-01", "layer-02", "layer-hover-01", "layer-selected-01", "support-success",
)


def repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "contracts" / "official_sources").is_dir():
            return parent
    raise RuntimeError("contracts/official_sources not found")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_carbon_white_tokens(root: Path | None = None) -> dict:
    """Read the first (White/:root) official Carbon token declaration for each name."""
    root = root or repo_root()
    home = root / "contracts" / "official_sources" / "carbon"
    source = _load(home / "source.json")
    artifact = root / source["artifact"]
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    if digest != source["sha256"]:
        raise ValueError("pinned Carbon artifact sha256 mismatch")
    with tarfile.open(artifact, mode="r:gz") as archive:
        member = archive.extractfile("package/css/styles.css")
        if member is None:
            raise ValueError("official Carbon CSS missing from artifact")
        css = member.read().decode("utf-8")
    tokens = {}
    for name in CARBON_TOKEN_NAMES:
        match = re.search(rf"--cds-{re.escape(name)}:\s*([^;]+);", css)
        if match is None:
            raise ValueError(f"official Carbon token missing: {name}")
        tokens[name] = match.group(1).strip()
    return {
        "contract_id": "OfficialSourceTokenSnapshot",
        "exactness": "source-exact",
        "package": source["package"],
        "version": source["version"],
        "source_sha256": source["sha256"],
        "theme": "white",
        "tokens": tokens,
    }


def assert_carbon_profile_parity(root: Path | None = None) -> None:
    """Reject any profile literal that drifts from the pinned official implementation."""
    root = root or repo_root()
    snapshot = extract_carbon_white_tokens(root)
    committed = _load(root / "contracts/official_sources/carbon/token_snapshot.json")
    if snapshot != committed:
        raise AssertionError("committed Carbon token snapshot is stale")
    profile = _load(root / "contracts/design_profiles/carbon.json")
    color = {key: row["$value"] for key, row in profile["tokens"]["color"].items()
             if not key.startswith("$")}
    contextual = {key: row["$value"] for key, row in profile["tokens"]["contextual"].items()
                  if not key.startswith("$")}
    expected = committed["tokens"]
    pairs = {
        "accent": expected["button-primary"],
        "surface": expected["background"],
        "surface-raised": expected["layer-01"],
        "backdrop": expected["background"],
        "hairline": expected["border-subtle-02"],
        "status-success": expected["support-success"],
    }
    if any(color[key] != value for key, value in pairs.items()):
        raise AssertionError("Carbon color profile drifts from official code")
    for key in ("background", "layer-01", "layer-02", "layer-hover-01",
                "layer-selected-01", "border-subtle-01", "border-subtle-02",
                "focus", "focus-inset"):
        if contextual[key] != expected[key]:
            raise AssertionError(f"Carbon contextual token drifts: {key}")
    button = profile["components"]["button"]
    if button["hover_css"]["background-color"] != expected["button-primary-hover"]:
        raise AssertionError("Carbon button hover drifts from official code")
    if button["active_css"]["background-color"] != expected["button-primary-active"]:
        raise AssertionError("Carbon button active drifts from official code")

"""Data-driven artifact birth router (org L1, CR-15).

Conforms to the reference router in ``tests/contracts/test_org_rootwide.py``: the SAME
(producer, artifact_kind, proposed_path) input yields the SAME ('accept', path) /
('refuse', reason) decision. The routing table is DATA in
``contracts/repo_layout.json`` ``birth_routing`` (closed home vocabulary: the five
``dev/reports`` categories, ``assets-receipts``, descriptor-bound ``custody``, and the two
scratch roots). Tracked-record kinds may never choose a scratch destination; a refused birth
performs no mkdir and no write. The real W6 producer calls :func:`attempt_birth` before its
first mkdir/write; the bypass is killed by a W6-lane integration test (packet-bound).
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CONTRACT = _REPO_ROOT / "contracts" / "repo_layout.json"

CLOSED_CATEGORIES = {"design_reviews", "admissions", "worker_reviews", "archive", "role_assignments"}
_HOME_ROOT_RE = re.compile(
    r"^(dev-reports:[a-z_]+|assets-receipts|custody|scratch-active|scratch-archive)$")
_ARCHIVE_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load_table(contract_path: Path | str | None = None) -> dict:
    path = Path(contract_path) if contract_path is not None else _CONTRACT
    return json.loads(path.read_text(encoding="utf-8")).get("birth_routing", {})


def birth_table_violations(table: dict) -> list:
    v = []
    lanes = table.get("lanes")
    if not isinstance(lanes, list) or not lanes or not all(isinstance(x, str) and x for x in lanes):
        v.append("lanes_not_closed_list")
    kinds = table.get("artifact_kinds")
    if not isinstance(kinds, list) or not kinds:
        v.append("kinds_not_closed_list")
        kinds = []
    names = [k.get("name") for k in kinds if isinstance(k, dict)]
    if len(names) != len(set(names)):
        v.append("duplicate_kind")
    for k in kinds:
        if not isinstance(k, dict):
            v.append("kind_row_not_a_map")
            continue
        exts = k.get("extensions")
        if (not isinstance(exts, list) or not exts
                or not all(isinstance(e, str) and e.startswith(".") for e in exts)):
            v.append(f"kind_extensions_untyped:{k.get('name')}")
    tracked_kinds = set(table.get("tracked_record_kinds", []))
    if not tracked_kinds:
        v.append("tracked_record_kinds_missing")
    seen = set()
    for r in table.get("rules", []):
        key = (r.get("producer"), r.get("artifact_kind"))
        if key in seen:
            v.append(f"duplicate_rule:{key}")
        seen.add(key)
        home = str(r.get("home_root", ""))
        if not _HOME_ROOT_RE.match(home):
            v.append(f"unknown_home_root:{home}")
        if home.startswith("dev-reports:") and home.split(":", 1)[1] not in CLOSED_CATEGORIES:
            v.append(f"sixth_report_category:{home}")
        if home.startswith("scratch") and r.get("artifact_kind") in tracked_kinds:
            v.append(f"tracked_record_kind_routed_to_scratch:{key}")
        if home.startswith("scratch") and r.get("lane") not in set(lanes or []):
            v.append(f"scratch_rule_without_lane:{key}")
    return v


def route_birth(producer, kind, proposed, table=None):
    """Return ('accept', path) or ('refuse', reason). Total: every input gets one decision."""
    if table is None:
        table = load_table()
    if birth_table_violations(table):
        return ("refuse", "invalid_table")
    if not isinstance(proposed, str) or not proposed.strip():
        return ("refuse", "empty_path")
    if "\\" in proposed:
        return ("refuse", "backslash")
    if proposed.startswith("/") or re.match(r"^[A-Za-z]:", proposed):
        return ("refuse", "absolute_path")
    parts = proposed.split("/")
    if any(seg in ("..", ".", "") for seg in parts):
        return ("refuse", "traversal_or_empty_segment")
    if unicodedata.normalize("NFC", proposed) != proposed:
        return ("refuse", "not_nfc_normalized")
    kind_rows = {k.get("name"): k for k in table.get("artifact_kinds", []) if isinstance(k, dict)}
    if kind not in kind_rows:
        return ("refuse", "unknown_kind")
    leaf = parts[-1]
    ext = ("." + leaf.rsplit(".", 1)[-1]) if "." in leaf else ""
    if ext not in set(kind_rows[kind].get("extensions", [])):
        return ("refuse", "extension_not_allowed_for_kind")
    matches = [r for r in table.get("rules", [])
               if r.get("producer") == producer and r.get("artifact_kind") == kind]
    if not matches:
        return ("refuse", "no_home_for_producer_kind")
    if len(matches) > 1:
        return ("refuse", "ambiguous_home")
    rule = matches[0]
    home = rule["home_root"]
    if proposed.startswith("scratchpad/") or proposed == "scratchpad":
        if not home.startswith("scratch"):
            return ("refuse", "scratch_path_for_non_scratch_home")
        if len(parts) == 2:
            return ("refuse", "direct_file_under_scratchpad")
        if proposed.startswith("scratchpad/work/"):
            return ("refuse", "frozen_legacy_work")
        if home == "scratch-active":
            if len(parts) < 5 or parts[1] != "active":
                return ("refuse", "active_grammar")
            lane, kseg = parts[2], parts[3]
        else:
            if len(parts) < 6 or parts[1] != "archive" or not _ARCHIVE_DATE_RE.match(parts[2]):
                return ("refuse", "archive_grammar")
            lane, kseg = parts[3], parts[4]
        if lane not in set(table.get("lanes", [])):
            return ("refuse", "unknown_lane")
        if lane != rule.get("lane"):
            return ("refuse", "producer_lane_mismatch")
        if kseg != kind:
            return ("refuse", "kind_segment_mismatch")
    else:
        if home.startswith("scratch"):
            return ("refuse", "non_scratch_path_for_scratch_home")
        if home.startswith("dev-reports:") and not proposed.startswith(
                "dev/reports/" + home.split(":", 1)[1] + "/"):
            return ("refuse", "wrong_report_category_path")
        if home == "assets-receipts" and not proposed.startswith("assets/receipts/"):
            return ("refuse", "not_under_assets_receipts")
        if home == "custody":
            return ("refuse", "custody_is_descriptor_bound_not_a_repo_path")
    return ("accept", proposed)


def attempt_birth(root, producer, kind, proposed, data: bytes, table=None):
    """Route FIRST; a refusal performs no mkdir and no write. A symlink path component refuses
    BEFORE any filesystem mutation."""
    decision, detail = route_birth(producer, kind, proposed, table)
    if decision == "refuse":
        return decision, detail
    cur = Path(root)
    for part in Path(proposed).parts[:-1]:
        cur = cur / part
        if cur.is_symlink():
            return "refuse", "symlink_component"
    dest = Path(root) / proposed
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return "accept", str(dest)


def _tree_snapshot(root) -> dict:
    snap = {}
    root = Path(root)
    for p in sorted(root.rglob("*")):
        rel = str(p.relative_to(root))
        if p.is_symlink():
            snap[rel] = "symlink:" + os.readlink(p)
        elif p.is_dir():
            snap[rel] = "dir"
        elif p.is_file():
            import hashlib
            snap[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return snap


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        sys.stderr.write("usage: birth_router.py <producer> <artifact_kind> <proposed_path>\n")
        raise SystemExit(2)
    decision, detail = route_birth(sys.argv[1], sys.argv[2], sys.argv[3])
    print(f"{decision}\t{detail}")
    raise SystemExit(0 if decision == "accept" else 1)

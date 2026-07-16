"""P5-0 ORG-AS-INVARIANT — the closed-cover structural-layout guard.

`contracts/repo_layout.json` `structural_layout` declares a HOME for every governed
file (which group / subdir it belongs to); this guard reddens on any undeclared OR
misplaced file. A closed cover: declared == actual parity (both drift directions) +
a negative control proving the guard CAN redden (no tautology).

This is the per-repo half of the kernel's organization invariant — the LAW (this test)
carries zero repo literals; the DATA (`repo_layout.json`) is the per-repo shape, so the
SAME guard governs any repo. It generalizes the WS1 scripts/tests layout contracts into
ONE target-shape over every surface, and is the RED a future "add a file" must satisfy
in the same slice it adds the file. Ported from
repo-surface-scout/tests/test_structural_layout.py. candidate_only; decides no authority.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path


def _repo_root() -> Path:
    """Walk up to the dir holding both scripts/ and tests/ (depth-independent)."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "scripts").is_dir() and (parent / "tests").is_dir():
            return parent
    raise RuntimeError("repo root not found")


REPO_ROOT = _repo_root()
_LAYOUT = json.loads((REPO_ROOT / "contracts" / "repo_layout.json").read_text(encoding="utf-8"))
_STRUCT = _LAYOUT["structural_layout"]
_ENUMERATED = ("source_layout", "test_layout")


def _actual_files(section: dict, *, root: Path | None = None) -> set[str]:
    """On-disk files under a section root, home-relative. A subpackage __init__.py marker
    (in a subdir, not the root) is a packaging artifact, not a declared module → skipped.
    `root` is injectable so the anti-tautology control proves this reads DISK."""
    root = root if root is not None else REPO_ROOT / section["root"]
    data_dirs = set(section.get("data_dirs", []))
    out: set[str] = set()
    for path in root.glob(section["glob"]):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if rel.parts and rel.parts[0] in data_dirs:
            continue
        if path.name == "__init__.py" and len(rel.parts) > 1:
            continue
        out.add(rel.as_posix())
    return out


def _declared_basenames(section: dict) -> set[str]:
    declared = set(section.get("root_allowlist", []))
    for group in section.get("groups", []):
        declared.update(group["members"])
    return declared


def _declared_homes(section: dict) -> set[str]:
    """Declared home PATH (section-root-relative) for every governed file: a root-allowlisted
    file keeps its basename; a group member lives at `<target_dir>/<member>` when
    placement_enforced, else flat. Home-aware so the same parity test governs before AND after
    a placement_enforced flip."""
    enforced = bool(section.get("placement_enforced", False))
    homes = set(section.get("root_allowlist", []))
    for group in section.get("groups", []):
        for member in group["members"]:
            homes.add(f"{group['target_dir']}/{member}" if enforced else member)
    return homes


def _unknown_receipts(names: list[str], known_profiles: set[str], section: dict) -> list[str]:
    """Classify receipt paths against the closed profile/page/reference-pack homes."""
    page_dir = section["page_dir"]
    pages = set(section["page_allowlist"])
    pack_dir = section["reference_pack_dir"]
    packs = set(section["reference_pack_allowlist"])
    unknown: list[str] = []
    for name in names:
        parts = Path(name).parts
        if parts and parts[0] == page_dir:
            if len(parts) < 3 or parts[1] not in pages:
                unknown.append(name)
        elif parts and parts[0] == pack_dir:
            if len(parts) < 3 or parts[1] not in packs:
                unknown.append(name)
        elif not parts or parts[0] not in known_profiles:
            unknown.append(name)
    return sorted(unknown)


class StructuralLayoutContract(unittest.TestCase):
    # --- closed-cover parity: every governed file has a declared home ---

    def test_every_src_module_has_a_declared_home(self):
        section = _STRUCT["source_layout"]
        self.assertEqual(
            _actual_files(section), _declared_homes(section),
            "scripts/ layout cover drifted — declare every module's home in "
            "contracts/repo_layout.json structural_layout.source_layout",
        )

    def test_every_test_file_has_a_declared_home(self):
        section = _STRUCT["test_layout"]
        self.assertEqual(
            _actual_files(section), _declared_homes(section),
            "tests/ layout cover drifted — declare every test's home in structural_layout.test_layout",
        )

    def test_every_contract_json_has_a_declared_home(self):
        section = _STRUCT["contracts_layout"]
        root = REPO_ROOT / section["root"]
        allow, group_dirs = set(section["root_allowlist"]), set(section["group_dirs"])
        undeclared: list[str] = []
        for path in root.glob(section["glob"]):
            if not path.is_file():
                continue
            rel = path.relative_to(root).parts
            if (len(rel) == 1 and rel[0] not in allow) or (len(rel) > 1 and rel[0] not in group_dirs):
                undeclared.append(path.relative_to(root).as_posix())
        self.assertEqual([], sorted(undeclared),
                         "contract JSON with no declared home — add to structural_layout.contracts_layout")

    def test_every_site_html_has_a_declared_home(self):
        """P5-0-FINISH: closed cover over GENERATED site HTML — an undeclared `site/*.html`
        reddens, so showcase.html / settings.html are structurally unconstructable until declared
        in the slice that creates them. Bespoke root_allowlist + group_dirs method (mirrors
        contracts_layout): `site/` is a root+allowlist shape, NOT a groups/target_dir shape, so it
        is deliberately NOT in `_ENUMERATED` (codex R7). `site/data/*` is hydrated JSON, not HTML,
        so the `*.html` glob never matches it."""
        section = _STRUCT["site_layout"]
        root = REPO_ROOT / section["root"]
        allow, group_dirs = set(section["root_allowlist"]), set(section["group_dirs"])
        undeclared: list[str] = []
        for path in root.glob(section["glob"]):
            if not path.is_file():
                continue
            rel = path.relative_to(root).parts
            if (len(rel) == 1 and rel[0] not in allow) or (len(rel) > 1 and rel[0] not in group_dirs):
                undeclared.append(path.relative_to(root).as_posix())
        self.assertEqual([], sorted(undeclared),
                         "site HTML with no declared home — add to structural_layout.site_layout "
                         "(showcase.html / settings.html land in their own slices)")

    def test_site_cover_fires_on_a_forged_html(self):
        """Anti-tautology: the site cover CAN redden. Pure cover logic over a hypothetical file
        set proves a forged top-level OR subdir HTML breaks parity — no tautology."""
        section = _STRUCT["site_layout"]
        allow, group_dirs = set(section["root_allowlist"]), set(section["group_dirs"])

        def _undeclared(names: list[str]) -> list[str]:
            out: list[str] = []
            for rel in names:
                parts = Path(rel).parts
                if (len(parts) == 1 and parts[0] not in allow) or (len(parts) > 1 and parts[0] not in group_dirs):
                    out.append(rel)
            return sorted(out)

        self.assertEqual([], _undeclared(["index.html"]), "the declared cover is green now")
        self.assertEqual(["forged.html"], _undeclared(["index.html", "forged.html"]),
                         "a forged undeclared top-level site HTML must redden")
        self.assertEqual(["rogue/x.html"], _undeclared(["index.html", "rogue/x.html"]),
                         "an undeclared subdir site HTML must redden")

    def test_every_receipt_is_under_a_known_profile_or_page_dir(self):
        """Profile receipts live under `assets/receipts/<lang>/`; MF1 page receipts live under
        `assets/receipts/pages/<page>/`. Both are closed covers: unknown profile dirs and unknown
        page dirs redden, so receipt producers cannot drop artifacts into an ungoverned tree."""
        section = _STRUCT["receipts_layout"]
        root = REPO_ROOT / section["root"]
        idx = json.loads((REPO_ROOT / "contracts" / "design_profiles" / "_index.json").read_text(encoding="utf-8"))
        known = set(idx["active_design_profiles"]) | set(idx["reserved_design_profiles"])
        actual: list[str] = []
        # pathlib does NOT brace-expand, so `**/*.{json,png}` would silently match NOTHING — iterate
        # an explicit `globs` list (JSON receipts + PNG reconstructions) so both are governed.
        globs = section.get("globs") or [section["glob"]]
        if root.is_dir():
            for glob in globs:
                for path in root.glob(glob):
                    if not path.is_file():
                        continue
                    actual.append(path.relative_to(root).as_posix())
        self.assertEqual([], _unknown_receipts(actual, known, section),
                         "receipt under an unknown profile/page/reference-pack dir — declare its home")

    def test_receipts_cover_fires_on_a_rogue_profile_or_page_dir(self):
        """Anti-tautology: forged receipts under unknown profile/page dirs break the cover."""
        section = _STRUCT["receipts_layout"]
        idx = json.loads((REPO_ROOT / "contracts" / "design_profiles" / "_index.json").read_text(encoding="utf-8"))
        known = set(idx["active_design_profiles"]) | set(idx["reserved_design_profiles"])
        self.assertEqual([], _unknown_receipts(["liquid-glass/conformance_receipt.json"], known, section),
                         "a known-profile receipt is green")
        self.assertEqual([], _unknown_receipts(["pages/index/screenshot-1280.png"], known, section),
                         "a declared page receipt is green")
        self.assertEqual([], _unknown_receipts(
            ["reference-packs/dashboard-pre-w3/screenshot-liquid-glass-1280.png"], known, section),
            "a declared reference-pack receipt is green")
        self.assertEqual(["rogue/x.json"], _unknown_receipts(
            ["liquid-glass/conformance_receipt.json", "rogue/x.json"], known, section),
                         "a receipt under an unknown-profile dir must redden the cover")
        self.assertEqual(["pages/rogue/screenshot-1280.png"],
                         _unknown_receipts(
                             ["pages/index/screenshot-1280.png", "pages/rogue/screenshot-1280.png"],
                             known, section),
                         "a receipt under an unknown page dir must redden the cover")
        self.assertEqual(["reference-packs/rogue/facts.json"],
                         _unknown_receipts(["reference-packs/rogue/facts.json"], known, section),
                         "a receipt under an unknown reference pack must redden the cover")

    # --- inverse drift: no phantom declarations ---

    def test_declared_homes_have_no_phantom_members(self):
        phantom: list[str] = []
        for name in _ENUMERATED:
            section = _STRUCT[name]
            root = REPO_ROOT / section["root"]
            for member in _declared_basenames(section):
                if not any((root / member).exists() or (root / g["target_dir"] / member).exists()
                           for g in [{"target_dir": "."}] + section.get("groups", [])):
                    phantom.append(f"{name}:{member}")
        self.assertEqual([], sorted(phantom), "declared homes reference files that do not exist on disk")

    # --- placement + no escape hatches ---

    def test_placement_enforced_groups_live_in_their_subdir(self):
        offenders: list[str] = []
        for name in _ENUMERATED:
            section = _STRUCT[name]
            root = REPO_ROOT / section["root"]
            enforced = section["placement_enforced"]
            for group in section.get("groups", []):
                for member in group["members"]:
                    home = root / group["target_dir"] / member if enforced else root / member
                    if not home.is_file():
                        offenders.append(f"{name}:{member}")
        self.assertEqual([], sorted(offenders), "placement drift — a member is not where its flag says")

    def test_no_group_dir_shadows_a_root_module(self):
        for name in _ENUMERATED:
            section = _STRUCT[name]
            root_stems = {Path(m).stem for m in section.get("root_allowlist", [])}
            for group in section.get("groups", []):
                self.assertNotIn(group["target_dir"], root_stems,
                                 f"{name}: group dir {group['target_dir']!r} shadows a root module")

    def test_no_flat_escape_hatch(self):
        for name in _ENUMERATED:
            tds = [g["target_dir"] for g in _STRUCT[name].get("groups", [])]
            self.assertTrue(all(td not in (".", "", None) for td in tds), f"{name}: a group target_dir is flat")
            self.assertEqual(len(tds), len(set(tds)), f"{name}: duplicate group target_dir")
        cd = _STRUCT["contracts_layout"]["group_dirs"]
        self.assertNotIn(".", cd)
        self.assertEqual(len(cd), len(set(cd)))

    # --- anti-tautology negative control: the cover CAN redden ---

    def test_guard_fires_on_a_forged_or_misplaced_file(self):
        import tempfile
        section = _STRUCT["source_layout"]
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            (tmp / "forged_actual.py").write_text("x = 1\n", encoding="utf-8")
            (tmp / "pkg").mkdir()
            (tmp / "pkg" / "__init__.py").write_text("", encoding="utf-8")
            self.assertEqual({"forged_actual.py"}, _actual_files(section, root=tmp),
                             "_actual_files must read real disk, not echo the manifest")
        actual, declared = _actual_files(section), _declared_homes(section)
        self.assertEqual(actual, declared, "the real cover must be green now")
        self.assertNotEqual(actual | {"a_forged_undeclared.py"}, declared, "an undeclared add must break parity")
        self.assertNotEqual(actual - {sorted(declared)[0]}, declared, "a vanished declared file must break parity")
        enf = {"placement_enforced": True, "root_allowlist": [], "groups": [{"target_dir": "rendering", "members": ["x.py"]}]}
        self.assertEqual({"rendering/x.py"}, _declared_homes(enf))
        self.assertEqual({"x.py"}, _declared_homes({**enf, "placement_enforced": False}))


if __name__ == "__main__":
    unittest.main()

"""Root-wide organization guard (W3C-ORG convergence set CR-1..CR-9, CR-14 + CR-15..CR-20).

RED r3 (convergence round). Producing model: Fable 5 (claude-fable-5) — execution metadata only;
authority is the design of record `docs/plans/handoff/w3c-org-rootwide-design.md` rev 2 plus the
r3 design delta (`scratchpad/active/org/design/org-design-delta-r3-2026-07-17.md`). Prior rounds:
`scratchpad/work/packet-org-red-fixes-2026-07-16.md` (folds F1-F8) and the r2 review
`scratchpad/work/codex-org-red-r2-review-2026-07-16.md` (8 findings, all closed here as
load-bearing executable probes — the convergence law forbids another prose round).

Structure (right-reason law):
  * `OrgHostileProbes` — every hostile/vacuity proof is its own DISCOVERABLE test, executable
    TODAY against temporary repositories / in-memory documents. These are GREEN now: they prove
    the checker logic kills each named hollow case before the real contract exists.
  * `OrgRootwideContract` — the real contract arms (CR-1..CR-9, CR-14, intake). Each fails TODAY
    at a named first assertion (the section/home/file is still absent at slice-0 tip 74fe3ecd)
    and flips green at the L1/L2/L3 landing step written in its docstring.
  * `OrgRootwideNewLaw` — CR-15..CR-20, the 2026-07-17 checkpoint bindings (birth routing,
    scratch grammar, orphan worktrees, pre-commit hook, bootstrap-anchor consumer ledger,
    scratch retirement checkpoint). Also RED today for named right reasons.

Pure stdlib. No network. Temp repos are created only under the test-runner tmpdir.
"""

import hashlib
import json
import os
import re
import subprocess
import tempfile
import unicodedata
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "contracts" / "repo_layout.json"

# The closed set of evidence categories (r2-g5: no `proposals`; checkpoint law: never a sixth).
CLOSED_CATEGORIES = {"design_reviews", "admissions", "worker_reviews", "archive", "role_assignments"}
# Every governed root that needs an executable shape row.
GOVERNED_ROOTS = {"scripts", "tests", "contracts", "docs", "site", "assets/receipts", "dev"}
# The three artifact-family READMEs and the retired-law phrases they must not teach as ACTIVE law.
FAMILY_READMES = ("dev/README.md", "skills/README.md", "templates/README.md")
RETIRED_LAW_PHRASES = ("proposals", "candidate_only", "singleton")

_SHA256_RE = re.compile(r"\b[0-9a-f]{64}\b")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_POINTER_PATH_RE = re.compile(r"dev/reports/[^\s`'\"()\[\]]+")
_SCRATCH_FILE_CITE_RE = re.compile(r"scratchpad/[^\s`'\"()\[\]]*\.[A-Za-z0-9*]+")
_KEEP_NEWEST_RE = re.compile(r"^keep-newest-([1-9][0-9]*)$")
_RETENTION_FIXED = {"permanent", "retire-when-slice-done"}
_NODE_KIND_VOCAB = {"file", "executable", "symlink", "submodule", "dir"}

# ------------------------------------------------------------------------------------
# shared plumbing
# ------------------------------------------------------------------------------------

def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)


def _git_tracked_in(repo_root, relpath) -> bool:
    out = _git(repo_root, "ls-files", "--", relpath)
    return bool(out.stdout.strip())


def _git_tracked(relpath: str) -> bool:
    return _git_tracked_in(ROOT, relpath)


def _index_paths(repo_root) -> list:
    out = _git(repo_root, "ls-files", "-z")
    return [p for p in out.stdout.split("\0") if p]


def _canonical_digest(members) -> str:
    """sha256 of the canonical JSON of the sorted member list (the ledger's own rule)."""
    canonical = json.dumps(sorted(members), separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _parse_utc(value):
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _row_text(row) -> str:
    """Keys AND values of a row, lowercased -- so a fork note hidden in a VALUE is seen."""
    parts = []
    for k, val in row.items():
        parts.append(str(k))
        parts.append(str(val))
    return " ".join(parts).lower()


class _RepoView:
    """Real-tree adapter for row validators (injected so hostile probes can use temp repos)."""

    def __init__(self, root):
        self.root = Path(root)

    def exists(self, rel) -> bool:
        return (self.root / rel).is_file()

    def tracked(self, rel) -> bool:
        return _git_tracked_in(self.root, rel)

    def digest(self, rel) -> str:
        return hashlib.sha256((self.root / rel).read_bytes()).hexdigest()

    def read_text(self, rel) -> str:
        return (self.root / rel).read_text(encoding="utf-8", errors="replace")


class _FakeRepo:
    """In-memory repo view for hostile probes: {relpath: bytes}, tracked set separate."""

    def __init__(self, files, tracked=None):
        self.files = {k: (v.encode("utf-8") if isinstance(v, str) else v) for k, v in files.items()}
        self._tracked = set(files) if tracked is None else set(tracked)

    def exists(self, rel) -> bool:
        return rel in self.files

    def tracked(self, rel) -> bool:
        return rel in self._tracked

    def digest(self, rel) -> str:
        return hashlib.sha256(self.files[rel]).hexdigest()

    def read_text(self, rel) -> str:
        return self.files[rel].decode("utf-8", errors="replace")


# ------------------------------------------------------------------------------------
# F1 (CR-8): shape rows must encode REAL classification and run against the REAL index.
# ------------------------------------------------------------------------------------
SHAPE_ROW_REQUIRED = {
    "root", "universe_source", "evaluation", "allowed_node_kinds",
    "semantic_groups", "exclusions", "child_contracts", "classification_result",
}


def _validate_shape_row(row) -> list:
    """Reasons a single [[shape]] row is NOT a real classifier. A bare stub, an unknown node
    kind, or an untyped pattern list must all be rejected (r2 finding 5)."""
    v = []
    if row.get("universe_source") != "index":
        v.append("universe_source!=index")
    if row.get("evaluation") != "exclusions-then-closed-partition":
        v.append("evaluation!=exclusions-then-closed-partition")
    kinds = row.get("allowed_node_kinds")
    if not isinstance(kinds, list) or not kinds:
        v.append("allowed_node_kinds must be a non-empty list")
    else:
        unknown = [k for k in kinds if k not in _NODE_KIND_VOCAB]
        if unknown:
            v.append(f"allowed_node_kinds_unknown:{unknown}")
    groups = row.get("semantic_groups")
    if not isinstance(groups, list) or not groups:
        v.append("semantic_groups must be a non-empty list of named groups")
    else:
        for g in groups:
            if not isinstance(g, dict) or not str(g.get("name", "")).strip():
                v.append("each semantic group needs a name")
                break
            pats = g.get("patterns")
            if (not isinstance(pats, list) or not pats
                    or not all(isinstance(p, str) and p.strip() for p in pats)):
                v.append("each semantic group needs patterns as a non-empty list of strings")
                break
    exclusions = row.get("exclusions")
    if not isinstance(exclusions, list):
        v.append("exclusions must be a list (each naming its child contract)")
    else:
        for ex in exclusions:
            if (not isinstance(ex, dict) or not str(ex.get("child_contract", "")).strip()
                    or not isinstance(ex.get("pattern"), str) or not ex.get("pattern")):
                v.append("each exclusion must carry a string pattern and its child contract")
                break
    if not isinstance(row.get("child_contracts"), list):
        v.append("child_contracts must be a list")
    if row.get("classification_result") != "exact-one":
        v.append("classification_result must declare exact-one")
    return v


def _classify_path(path, groups, exclusions) -> str:
    # exclusions carve out child-contract territory FIRST
    for ex in exclusions:
        if path.startswith(ex["pattern"]):
            return "excluded"
    matched = [g["name"] for g in groups if any(path.startswith(p) for p in g["patterns"])]
    if len(matched) == 1:
        return "classified"
    if len(matched) == 0:
        return "unclassified"
    return "ambiguous"


def _classify_index(paths, groups, exclusions) -> dict:
    return {p: _classify_path(p, groups, exclusions) for p in paths}


def _shape_residue(shapes, index_paths) -> dict:
    """Per governed root: the candidate-index paths its declared groups fail to classify
    exactly-one. This is the BEHAVIORAL run of every real [[shape]] row over the real index."""
    residue = {}
    for s in shapes:
        root = s.get("root", "")
        under = [p for p in index_paths if p.startswith(root + "/")]
        verdicts = _classify_index(under, s.get("semantic_groups", []), s.get("exclusions", []))
        bad = sorted(p for p, verdict in verdicts.items() if verdict in ("unclassified", "ambiguous"))
        residue[root] = bad
    return residue


_SYNTH_GROUPS = [
    {"name": "core", "patterns": ["scripts/core/"]},
    {"name": "render", "patterns": ["scripts/render/"]},
    {"name": "cards", "patterns": ["scripts/render/cards/"]},
]
_SYNTH_EXCLUSIONS = [{"pattern": "scripts/organization/", "child_contract": "contracts/org_child.json"}]
_SYNTH_INDEX = [
    "scripts/core/config.py",          # core only          -> classified
    "scripts/core/settings.py",        # core only          -> classified
    "scripts/render/outputs.py",       # render only        -> classified
    "scripts/organization/tool.py",    # carved out         -> excluded
    "scripts/render/cards/badges.py",  # render AND cards   -> ambiguous (double-matched)
    "scripts/misc/stray.py",           # no group           -> unclassified
]


# ------------------------------------------------------------------------------------
# F2 (CR-1): debt rows are BEHAVIORAL shrink ledgers, exercised against the real index.
# ------------------------------------------------------------------------------------
_DEBT_EXACT_KEYS = {"finding_id", "root", "baseline_members", "baseline_digest", "reason", "expires_utc"}
_DEBT_FORBIDDEN = {"test_id", "fingerprint"}


def _make_debt_row(members, expires):
    return {
        "finding_id": "F-synthetic",
        "root": "docs",
        "baseline_members": list(members),
        "baseline_digest": _canonical_digest(members),
        "reason": "cannot reorganize this slice",
        "expires_utc": expires,
    }


def _debt_row_violations(row, observed, now) -> list:
    v = []
    if set(row) != _DEBT_EXACT_KEYS:
        v.append("key_set")
    if set(row) & _DEBT_FORBIDDEN:
        v.append("ratchet_coupling")
    members = row.get("baseline_members", [])
    if not members:
        v.append("empty_baseline")          # r2 finding 4: an empty-baseline row is hollow
    if _canonical_digest(members) != row.get("baseline_digest"):
        v.append("digest_mismatch")
    obs, base = set(observed), set(members)
    if not obs <= base:
        v.append("debt_growth")
    exp = _parse_utc(row.get("expires_utc"))
    if exp is None:
        v.append("expires_not_iso8601_utc")
    elif now > exp:
        v.append("expired")
    if len(base) > 0 and len(obs) == 0:
        v.append("stale_debt_must_be_removed")
    return v


def _ledger_violations_against_index(ledger, index_paths, residue_by_root, now) -> list:
    """Exercise every real debt row against the ACTUAL candidate-index members (r2 finding 4):
    observed = baseline members still present in the index; growth = a residue path under the
    row's root that no baseline covers."""
    v = []
    index_set = set(index_paths)
    covered_by_root = {}
    for row in ledger:
        observed = sorted(set(row.get("baseline_members", [])) & index_set)
        for reason in _debt_row_violations(row, observed, now):
            v.append(f"{row.get('finding_id')}:{reason}")
        covered_by_root.setdefault(row.get("root"), set()).update(row.get("baseline_members", []))
    for root, residue in residue_by_root.items():
        extra = sorted(set(residue) - covered_by_root.get(root, set()))
        for p in extra:
            v.append(f"debt_growth_unledgered:{p}")
    return v


# ------------------------------------------------------------------------------------
# F3/F7-typed (CR-4/CR-6/CR-9): fully TYPED populated-manifest rows + closed category map.
# ------------------------------------------------------------------------------------
_MANIFEST_ROW_REQUIRED = {"path", "sha256", "schema_id", "schema_version", "subject",
                          "producer", "produced_utc", "retention_class", "referenced_by"}


def _retention_class_valid(value) -> bool:
    if value in _RETENTION_FIXED:
        return True
    return isinstance(value, str) and bool(_KEEP_NEWEST_RE.match(value))


def _manifest_row_violations(row, repo) -> list:
    """Validate ONE populated manifest row against a repo view (real or fake): typed schema
    versions/timestamps/retention/identities, tracked existing artifact, digest recompute, and
    REAL back-references (the citing doc must exist, be tracked, and cite path or digest).
    Finalized rows additionally require digest-bearing citations (r2 findings 2 and 7)."""
    v = []
    missing = _MANIFEST_ROW_REQUIRED - set(row)
    if missing:
        v.append(f"missing_fields:{sorted(missing)}")
        return v
    for field in ("path", "schema_id", "subject", "producer"):
        val = row.get(field)
        if not isinstance(val, str) or not val.strip():
            v.append(f"empty_identity:{field}")
    sha = row.get("sha256")
    if not isinstance(sha, str) or not _HEX64_RE.match(sha):
        v.append("malformed_sha256")
    sv = row.get("schema_version")
    if isinstance(sv, bool) or not isinstance(sv, int) or sv < 1:
        v.append("schema_version_not_positive_int")
    ts = _parse_utc(row.get("produced_utc"))
    if ts is None or ts.tzinfo is None:
        v.append("produced_utc_not_iso8601_utc")
    if not _retention_class_valid(row.get("retention_class")):
        v.append(f"retention_class_invalid:{row.get('retention_class')!r}")
    path = row.get("path")
    if isinstance(path, str) and path.strip():
        if not repo.exists(path):
            v.append("correspondence_gap")
        else:
            if not repo.tracked(path):
                v.append("artifact_untracked")
            if isinstance(sha, str) and _HEX64_RE.match(sha) and repo.digest(path) != sha:
                v.append("digest_mismatch")
    rb = row.get("referenced_by")
    if (not isinstance(rb, list) or not rb
            or not all(isinstance(x, str) and x.strip() for x in rb)):
        v.append("referenced_by_empty_or_untyped")
        rb = []
    for ref in rb:
        if not repo.exists(ref) or not repo.tracked(ref):
            v.append(f"back_reference_missing:{ref}")
            continue
        cite = repo.read_text(ref)
        path_cited = isinstance(path, str) and path and path in cite
        digest_cited = isinstance(sha, str) and sha and sha in cite
        if not path_cited and not digest_cited:
            v.append(f"back_reference_does_not_cite:{ref}")
        if row.get("finalized") is True and not digest_cited:
            v.append(f"finalized_back_reference_not_digest_bearing:{ref}")
    return v


def _sealed_row_mutation(original, mutated) -> list:
    """A finalized (sealed) permanent-retention row is immutable: its {path, sha256} may not
    change or vanish."""
    if not original.get("finalized"):
        return []
    if mutated.get("path") != original.get("path") or mutated.get("sha256") != original.get("sha256"):
        return ["finalized_row_mutation"]
    return []


def _control_files_violations(dev_reports) -> list:
    """Control-file exclusion is PER CATEGORY (conductor decision, F3): each category excludes
    exactly its own manifest.json plus its own guide/README. A single GLOBAL list is a defect."""
    v = []
    if isinstance(dev_reports.get("schema", {}).get("control_files"), list):
        v.append("global_control_files_list_is_a_defect")
    categories = dev_reports.get("categories", {})
    if not isinstance(categories, dict) or not categories:
        v.append("categories_must_be_a_map")
        return v
    for name, cat in categories.items():
        cf = cat.get("control_files") if isinstance(cat, dict) else None
        if not isinstance(cf, list) or "manifest.json" not in cf:
            v.append(f"{name}:manifest_not_excluded")
            continue
        if not any("readme" in str(x).lower() for x in cf):
            v.append(f"{name}:guide_not_excluded")
    return v


def _category_map_violations(categories) -> list:
    v = []
    if not isinstance(categories, dict):
        v.append("categories_must_be_a_map_not_a_name_list")
        return v
    if set(categories) != CLOSED_CATEGORIES:
        v.append(f"category_set_not_closed_five:{sorted(set(categories) ^ CLOSED_CATEGORIES)}")
    for name, cat in categories.items():
        if not isinstance(cat, dict):
            v.append(f"{name}:value_must_be_a_map")
            continue
        for field in ("owner", "purpose", "retention"):
            if not str(cat.get(field, "")).strip():
                v.append(f"{name}:missing_{field}")
    return v


# ------------------------------------------------------------------------------------
# F4-typed (CR-7): complete typed live-control rows, exact paths, boolean parity,
# and the hooksPath policy row (2026-07-17 binding 1).
# ------------------------------------------------------------------------------------
EXPECTED_CONTROL_IDS = {"claude-harness", "git-local-config-hooks", "virtualenv", "caches"}
EXPECTED_CONTROL_PATHS = {"claude-harness": ".claude", "git-local-config-hooks": ".git",
                          "virtualenv": ".venv"}
VALID_REGISTRY_AUTHORITIES = {"contracts/role_registry.toml", "contracts/role_registry.*"}
HOOKS_GOVERNED_DIR = "scripts/organization/hooks"
PINNED_GREEN_TESTS = ("tests/contracts/test_doc_authority.py",
                      "tests/contracts/test_structural_layout.py")
PINNED_GREEN_MODULES = ("tests.contracts.test_doc_authority",
                        "tests.contracts.test_structural_layout")


def _live_controls_violations(controls) -> list:
    rows = controls.get("rows", []) if isinstance(controls, dict) else controls
    v = []
    if not isinstance(rows, list):
        return ["rows_not_a_list"]
    ids = [r.get("id") for r in rows if isinstance(r, dict)]
    if len(ids) != len(set(ids)):
        v.append("duplicate_control_rows")
    if set(ids) != EXPECTED_CONTROL_IDS:
        v.append(f"not_closed:{sorted((set(ids) ^ EXPECTED_CONTROL_IDS) - {None})}")
    for r in rows:
        if not isinstance(r, dict):
            v.append("row_not_a_map")
            continue
        rid = r.get("id")
        if r.get("authoritative") is not False:            # exactly boolean False, not null/absent
            v.append(f"{rid}:authoritative_not_false")
        if not str(r.get("purpose", "")).strip():
            v.append(f"{rid}:missing_purpose")
        expected_path = EXPECTED_CONTROL_PATHS.get(rid)
        if expected_path is not None and r.get("path") != expected_path:
            v.append(f"{rid}:path_not_exact")
        if rid == "caches":
            paths = r.get("paths")
            if (not isinstance(paths, list) or not paths
                    or not all(isinstance(p, str) and p.strip() for p in paths)):
                v.append("caches:paths_not_typed_list")
        if rid == "claude-harness":
            if r.get("authority") not in VALID_REGISTRY_AUTHORITIES:   # exact, no substring
                v.append("authority_not_exact_registry")
            if r.get("mirror_parity_check") is not True:               # exactly boolean True
                v.append("mirror_parity_check_not_boolean_true")
        if rid == "git-local-config-hooks":
            pol = r.get("hooks_path_policy")
            if not isinstance(pol, dict):
                v.append("git:missing_hooks_path_policy")
            else:
                if pol.get("governed_dir") != HOOKS_GOVERNED_DIR:
                    v.append("git:hooks_governed_dir_not_exact")
                if list(pol.get("pinned_tests", [])) != list(PINNED_GREEN_TESTS):
                    v.append("git:pinned_tests_not_exact")
        if "amendment" in _row_text(r):                    # settled-no-fork over keys AND values
            v.append("amendment_fork")
    return v


def _valid_control_rows() -> list:
    return [
        {"id": "claude-harness", "path": ".claude", "authoritative": False,
         "purpose": "agent harness; local convenience mirror only",
         "authority": "contracts/role_registry.toml", "mirror_parity_check": True},
        {"id": "git-local-config-hooks", "path": ".git", "authoritative": False,
         "purpose": "local git config and hooks",
         "hooks_path_policy": {"governed_dir": HOOKS_GOVERNED_DIR,
                               "pinned_tests": list(PINNED_GREEN_TESTS)}},
        {"id": "virtualenv", "path": ".venv", "authoritative": False, "purpose": "inert local env"},
        {"id": "caches", "paths": ["__pycache__/", ".pytest_cache/"], "authoritative": False,
         "purpose": "inert caches"},
    ]


# ------------------------------------------------------------------------------------
# F6 (CR-3): roster projection is CLOSED and duplicate-safe.
# ------------------------------------------------------------------------------------
EXPECTED_ROSTERS = {"MODULE_HOMES", "TEST_GROUPS"}


def _roster_name_violations(rosters) -> list:
    """`rosters` is the RAW list of roster rows -- checked BEFORE any dict-indexing so a
    dict-overwrite cannot launder a duplicate."""
    names = [r.get("name") for r in rosters]
    v = []
    if len(names) != len(set(names)):
        v.append("duplicate_roster_names")
    if set(names) != EXPECTED_ROSTERS:
        v.append(f"roster_set_not_closed:{sorted(set(n for n in names if n) ^ EXPECTED_ROSTERS)}")
    return v


# ------------------------------------------------------------------------------------
# F7 (CR-5 + intake): COUPLED governed pointers + roster-independent intake completeness.
# ------------------------------------------------------------------------------------

def _coupled_pointers(text):
    """Parse governed pointers as COUPLED (path, digest) pairs: a pointer line carries exactly
    one dev/reports/ path and exactly one 64-hex digest. Returns (pointers, loose_paths):
    loose_paths are dev/reports/ paths with no same-line digest (or ambiguous lines)."""
    pointers, loose = [], []
    for line in text.splitlines():
        paths = [p.rstrip(".,;:") for p in _POINTER_PATH_RE.findall(line)]
        digests = _SHA256_RE.findall(line)
        if len(paths) == 1 and len(digests) == 1:
            pointers.append((paths[0], digests[0]))
        else:
            loose.extend(paths)
    return pointers, loose


def _routing_doc_violations(text, repo) -> list:
    """A routing doc must (a) NOT cite the ephemeral scratch tree, and (b) carry at least one
    COUPLED governed pointer whose target EXISTS, is TRACKED, and whose digest RECOMPUTES
    (r2 finding 2: deletion, untracked targets, and digest laundering all redden)."""
    v = []
    if "scratchpad/work" in text:
        v.append("scratch_citation")
    pointers, loose = _coupled_pointers(text)
    if not pointers:
        v.append("missing_coupled_governed_pointer")
    for p in loose:
        v.append(f"uncoupled_pointer:{p}")
    for path, digest in pointers:
        if not repo.exists(path):
            v.append(f"pointer_target_missing:{path}")
            continue
        if not repo.tracked(path):
            v.append(f"pointer_target_untracked:{path}")
            continue
        if repo.digest(path) != digest:
            v.append(f"pointer_digest_mismatch:{path}")
    return v


INTAKE_MANIFEST_REL = "dev/reports/admissions/w3c-org-intake.json"
INTAKE_ROSTER_REL = "dev/reports/admissions/w3c-org-intake-roster.tsv"
INTAKE_CLASSES = {"durable-evidence", "perishable", "stray"}


def _parse_intake_roster(text) -> list:
    """The independent cutoff roster: one row per SOURCE PATH (duplicate-digest path
    multiplicity is preserved by construction), tab-separated `source\tdestination\tclass`."""
    rows = []
    for line in text.splitlines():
        if not line.strip():
            continue
        rows.append(tuple(line.split("\t")))
    return rows


def _intake_violations(manifest_rows, roster_rows) -> list:
    """Completeness derives from the INDEPENDENT roster, never from the manifest's own rows
    (r2 finding 1). Bijection both ways; every durable row needs a governed destination and a
    source digest; every source classifies exactly once against the closed class set."""
    v = []
    by_source = {}
    for r in manifest_rows:
        src = r.get("source_path")
        if src in by_source:
            v.append(f"duplicate_manifest_source:{src}")
        by_source[src] = r
    roster_sources = set()
    for row in roster_rows:
        if len(row) != 3:
            v.append(f"roster_row_malformed:{row!r}")
            continue
        src, _dest, klass = row
        if src in roster_sources:
            v.append(f"duplicate_roster_source:{src}")
        roster_sources.add(src)
        if klass not in INTAKE_CLASSES:
            v.append(f"unknown_class:{src}:{klass}")
        mrow = by_source.get(src)
        if mrow is None:
            v.append(f"unhomed_source:{src}")
            continue
        if mrow.get("classification") != klass:
            v.append(f"class_mismatch:{src}")
        if klass == "durable-evidence" and not str(mrow.get("destination", "")).startswith("dev/reports/"):
            v.append(f"ungoverned_destination:{src}")
        if not _HEX64_RE.match(str(mrow.get("source_sha256", ""))):
            v.append(f"missing_source_digest:{src}")
    for src in sorted(set(by_source) - roster_sources):
        v.append(f"manifest_row_not_in_roster:{src}")
    return v


# ------------------------------------------------------------------------------------
# F8 (CR-14): family guides must TEACH; ban only ACTIVE-law phrasing.
# ------------------------------------------------------------------------------------
ANCHOR_CONTRACT = "contracts/repo_layout.json"
ANCHOR_GUARD = "test_org_rootwide"
RETIREMENT_MARKERS = ("retired", "superseded")


def _guide_violations(text) -> list:
    """A family guide must carry the two current-law anchors (its governing contract path + the
    guard module name) and must NOT teach retired law as ACTIVE law. The phrase ban is
    CONTEXT-AWARE -- a banned phrase on a line that ALSO carries a retirement marker
    (retired/superseded) is a correct retirement statement and passes. An empty guide reddens
    (missing anchors)."""
    v = []
    if ANCHOR_CONTRACT not in text:
        v.append("missing_contract_anchor")
    if ANCHOR_GUARD not in text:
        v.append("missing_guard_anchor")
    for line in text.splitlines():
        low = line.lower()
        if any(m in low for m in RETIREMENT_MARKERS):
            continue
        for phrase in RETIRED_LAW_PHRASES:
            if phrase in low:
                v.append(f"teaches_active:{phrase}")
    return v


# ------------------------------------------------------------------------------------
# CR-15/CR-16 (2026-07-17 checkpoint law): data-driven birth router + closed scratch grammar.
# The production router (`scripts/organization/birth_router.py`, L1) must CONFORM to this
# reference; the real W6 producer calls it before its first mkdir/write (bypass is killed by a
# W6-lane integration test, bound in the packet delta — not here).
# ------------------------------------------------------------------------------------
_HOME_ROOT_RE = re.compile(r"^(dev-reports:[a-z_]+|assets-receipts|custody|scratch-active|scratch-archive)$")
_ARCHIVE_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
GITIGNORE_ANCHORED_ROSTER = ("/scratchpad/", "/mutants.out/", "/.hypothesis/", "/reports/")


def _birth_table_violations(table) -> list:
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
            v.append(f"duplicate_rule:{key}")   # exact-one home per (producer, kind)
        seen.add(key)
        home = str(r.get("home_root", ""))
        if not _HOME_ROOT_RE.match(home):
            v.append(f"unknown_home_root:{home}")
        if home.startswith("dev-reports:") and home.split(":", 1)[1] not in CLOSED_CATEGORIES:
            v.append(f"sixth_report_category:{home}")     # routing stays disjoint; never a sixth
        if home.startswith("scratch") and r.get("artifact_kind") in tracked_kinds:
            v.append(f"tracked_record_kind_routed_to_scratch:{key}")
        if home.startswith("scratch") and r.get("lane") not in set(lanes or []):
            v.append(f"scratch_rule_without_lane:{key}")
    return v


def _route_birth(producer, kind, proposed, table):
    """Reference router over (producer, artifact_kind, proposed_path). Returns
    ('accept', path) or ('refuse', reason). Total: every input gets exactly one decision."""
    if _birth_table_violations(table):
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
        return ("refuse", "no_home_for_producer_kind")   # unknown producer lands here too
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
            snap[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return snap


def _attempt_birth(root, producer, kind, proposed, data, table):
    """Reference birth wrapper: route FIRST; a refusal performs no mkdir and no write. A
    symlink path component refuses BEFORE any filesystem mutation."""
    decision, detail = _route_birth(producer, kind, proposed, table)
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


_SYNTH_BIRTH_TABLE = {
    "lanes": ["org", "w6"],
    "artifact_kinds": [
        {"name": "prompts", "extensions": [".txt"]},
        {"name": "packets", "extensions": [".md"]},
        {"name": "gate_transcript", "extensions": [".md"]},
        {"name": "receipt", "extensions": [".json", ".md"]},
        {"name": "staging", "extensions": [".html", ".json", ".png"]},
    ],
    "tracked_record_kinds": ["plan", "admission", "gate_transcript", "receipt"],
    "rules": [
        {"producer": "conductor", "artifact_kind": "prompts", "home_root": "scratch-active", "lane": "org"},
        {"producer": "conductor", "artifact_kind": "packets", "home_root": "scratch-active", "lane": "org"},
        {"producer": "codex-gate", "artifact_kind": "gate_transcript", "home_root": "dev-reports:design_reviews"},
        {"producer": "w6-producer", "artifact_kind": "staging", "home_root": "scratch-active", "lane": "w6"},
        {"producer": "w6-producer", "artifact_kind": "receipt", "home_root": "assets-receipts"},
    ],
}


# ------------------------------------------------------------------------------------
# CR-17: orphan-worktree law (consolidation law, operator order 2026-07-17).
# ------------------------------------------------------------------------------------

def _registered_worktrees(repo_root):
    """(primary, linked[]) from `git worktree list --porcelain`. The first block is always the
    main working tree."""
    out = _git(repo_root, "worktree", "list", "--porcelain")
    paths = []
    for block in out.stdout.strip().split("\n\n"):
        for line in block.splitlines():
            if line.startswith("worktree "):
                paths.append(line[len("worktree "):].rstrip("/"))
                break
    if not paths:
        return None, []
    return paths[0], paths[1:]


def _orphan_worktrees(linked_paths, live_rows, receipt_text, now) -> list:
    """A registered worktree is an ORPHAN unless (a) a LIVE lane row's path_suffix matches it
    and the row is unexpired, or (b) a pending-retirement receipt names its exact path."""
    orphans = []
    for p in linked_paths:
        covered = False
        for r in live_rows:
            suffix = str(r.get("path_suffix", ""))
            exp = _parse_utc(r.get("expires_utc"))
            if suffix and p.endswith(suffix) and exp is not None and now <= exp:
                covered = True
                break
        if not covered and p in receipt_text:
            covered = True
        if not covered:
            orphans.append(p)
    return orphans


# ------------------------------------------------------------------------------------
# CR-18: the core.hooksPath pre-commit hook pins EXACTLY the two landed green guards.
# ------------------------------------------------------------------------------------
HOOK_REL = HOOKS_GOVERNED_DIR + "/pre-commit"


def _hook_text_violations(text) -> list:
    """The hook must invoke BOTH pinned guard modules, must NEVER run full discovery
    (`unittest discover` would run the intentionally-RED ratchet set and block every commit),
    and must be RATCHET-AWARE: observed at 74fe3ecd, test_structural_layout carries exactly
    the five failing identities held in contracts/correction_baseline.json (contract rows for
    slice-1 modules not yet landed), so a raw-pinned hook would block every commit. The hook
    therefore fails only on failures OUTSIDE the baseline identities (subset law)."""
    v = []
    for module in PINNED_GREEN_MODULES:
        if module not in text:
            v.append(f"missing_pin:{module}")
    if "discover" in text:
        v.append("forbidden_full_discovery")
    if "correction_baseline" not in text:
        v.append("missing_ratchet_awareness")
    return v


# ------------------------------------------------------------------------------------
# CR-16 arm: scratch fork visibility (guards-gap binding 3) — divergent-kin detection.
# ------------------------------------------------------------------------------------
KIN_PRODUCER_PREFIXES = ("fable-", "local-", "codex-", "opus-")


def _kin_key(relpath) -> str:
    base = relpath.rsplit("/", 1)[-1]
    for pref in KIN_PRODUCER_PREFIXES:
        if base.startswith(pref):
            return base[len(pref):]
    return base


def _fork_findings(path_digests, supersessions) -> list:
    """Same-basename/content-kin detection over the scratch grammar. Identical digests are
    LAWFUL multiplicity (W6 determinism witnesses keep their path multiplicity); divergent
    bytes under one kin key redden unless a supersession pointer names every loser."""
    superseded = {s.get("loser") for s in supersessions if isinstance(s, dict)}
    by_kin = {}
    for p, d in path_digests.items():
        by_kin.setdefault(_kin_key(p), []).append((p, d))
    findings = []
    for kin, entries in sorted(by_kin.items()):
        if len(entries) < 2:
            continue
        if len({d for _, d in entries}) == 1:
            continue
        survivors = [p for p, _ in entries if p not in superseded]
        if len(survivors) > 1:
            findings.append(f"divergent_kin:{kin}")
    return findings


# ------------------------------------------------------------------------------------
# CR-19: bootstrap-anchor consumer ledger (checkpoint law: no magic counts — recompute).
# ------------------------------------------------------------------------------------
BOOTSTRAP_ANCHOR = "contracts/repo_layout.json"
CONSUMER_KINDS = {"code", "test", "contract", "doc", "config"}


def _grep_cached_counts(repo_root, literal) -> dict:
    """Per-tracked-file count of lines containing the literal, over the CANDIDATE INDEX blobs
    (`git grep --cached`), the anchor file itself excluded (it is not its own consumer)."""
    out = _git(repo_root, "grep", "-c", "--cached", "-F", literal)
    counts = {}
    for line in out.stdout.splitlines():
        path, _, n = line.rpartition(":")
        if path and n.isdigit():
            counts[path] = int(n)
    counts.pop(literal, None)
    return counts


def _consumer_ledger_violations(section, observed_counts, now) -> list:
    v = []
    rows = section.get("rows", [])
    canon = [[r.get("consumer_path"), r.get("literal_occurrence_count"), r.get("consumer_kind")]
             for r in rows]
    if canon != sorted(canon, key=lambda x: (str(x[0]), str(x[1]), str(x[2]))):
        v.append("rows_not_canonically_sorted")
    digest = hashlib.sha256(
        json.dumps(canon, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
    if digest != section.get("digest"):
        v.append("digest_mismatch")
    if not str(section.get("owner", "")).strip():
        v.append("missing_owner")
    exp = _parse_utc(section.get("expires_utc"))
    if exp is None:
        v.append("expires_not_iso8601_utc")
    elif now > exp:
        v.append("expired")
    by_path = {}
    for r in rows:
        p = r.get("consumer_path")
        if p in by_path:
            v.append(f"duplicate_consumer:{p}")
        by_path[p] = r
        if r.get("consumer_kind") not in CONSUMER_KINDS:
            v.append(f"unknown_consumer_kind:{p}")
        n = r.get("literal_occurrence_count")
        if isinstance(n, bool) or not isinstance(n, int) or n < 1:
            v.append(f"count_not_positive_int:{p}")
    for p, n in sorted(observed_counts.items()):
        row = by_path.get(p)
        if row is None:
            v.append(f"consumer_growth:{p}")          # subset-only shrink: new consumer reddens
        elif isinstance(row.get("literal_occurrence_count"), int) and n > row["literal_occurrence_count"]:
            v.append(f"occurrence_growth:{p}")
    if rows and not observed_counts:
        v.append("stale_ledger_must_be_removed")
    return v


# ------------------------------------------------------------------------------------
# CR-20: scratch retirement checkpoint — dispositioned citations + empty frozen work/.
# ------------------------------------------------------------------------------------
CITATION_DISPOSITIONS = {"grammar-only", "dangling-history"}


def _scratch_citation_violations(rows, offender_texts) -> list:
    """`rows`: [{path, disposition}] from the contract. `offender_texts`: {tracked path ->
    file text} for every tracked file whose text contains 'scratchpad/'. Bijection: every
    offender needs a row; a row for a non-offender is stale. grammar-only rows may keep the
    tree NAME but no scratch FILE-path citation; dangling-history rows are explicit records."""
    v = []
    by_path = {}
    for r in rows:
        p = r.get("path")
        if p in by_path:
            v.append(f"duplicate_disposition:{p}")
        by_path[p] = r
        if r.get("disposition") not in CITATION_DISPOSITIONS:
            v.append(f"unknown_disposition:{p}:{r.get('disposition')!r}")
    for path, text in sorted(offender_texts.items()):
        row = by_path.get(path)
        if row is None:
            v.append(f"undispositioned_scratch_citer:{path}")
            continue
        if row.get("disposition") == "grammar-only" and _SCRATCH_FILE_CITE_RE.search(text):
            v.append(f"grammar_only_cites_scratch_file:{path}")
    for path in sorted(set(by_path) - set(offender_texts)):
        v.append(f"stale_disposition_row:{path}")
    return v


# ====================================================================================
# HOSTILE / VACUITY PROBES — all GREEN today. Each is the named, discoverable,
# load-bearing kill for one review finding or one 2026-07-17 binding.
# ====================================================================================
class OrgHostileProbes(unittest.TestCase):
    # ---- finding 1: intake completeness must derive from the independent roster ----
    def test_hostile_f1_empty_sources_manifest_is_rejected(self) -> None:
        roster = [("scratchpad/work/a.md", "dev/reports/design_reviews/a.md", "durable-evidence")]
        v = _intake_violations([], roster)
        self.assertIn("unhomed_source:scratchpad/work/a.md", v,
                      "the r2 hollow case {'sources': []} must redden against the roster")

    def test_hostile_f1_completeness_derives_from_independent_cutoff_roster(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            scratch = Path(td) / "scratchpad" / "work"
            scratch.mkdir(parents=True)
            for name in ("one.md", "two.json", "three.md"):
                (scratch / name).write_text(name, encoding="utf-8")
            # the roster is computed by INDEPENDENTLY walking the tree at cutoff
            roster = sorted(
                ("scratchpad/work/" + p.name,
                 "dev/reports/design_reviews/" + p.name, "durable-evidence")
                for p in scratch.iterdir())
            complete = [{"source_path": src, "destination": dest, "classification": klass,
                         "source_sha256": "0" * 64}
                        for src, dest, klass in roster]
            self.assertEqual(_intake_violations(complete, roster), [],
                             "positive control: manifest covering the whole roster is clean")
            omitted = complete[:-1]   # selectively omit one source from the manifest
            self.assertTrue(any(x.startswith("unhomed_source:") for x in _intake_violations(omitted, roster)),
                            "a selectively omitted source must redden against the roster")
            invented = complete + [{"source_path": "scratchpad/work/ghost.md",
                                    "destination": "dev/reports/design_reviews/g.md",
                                    "classification": "durable-evidence", "source_sha256": "0" * 64}]
            self.assertTrue(any(x.startswith("manifest_row_not_in_roster:")
                                for x in _intake_violations(invented, roster)),
                            "a manifest row with no roster source must redden (bijection both ways)")
            flipped = [dict(r, classification="perishable") for r in complete]
            self.assertTrue(any(x.startswith("class_mismatch:") for x in _intake_violations(flipped, roster)),
                            "a class flip against the roster must redden (exactly-once classification)")
            escaped = [dict(complete[0], destination="scratchpad/keep/one.md")] + complete[1:]
            self.assertTrue(any(x.startswith("ungoverned_destination:")
                                for x in _intake_violations(escaped, roster)),
                            "a durable destination outside dev/reports/ must redden")

    # ---- finding 2: coupled pointers; deletion/untracked/laundering all redden ----
    def test_hostile_f2_deleted_target_and_unrelated_hash_are_rejected(self) -> None:
        repo = _FakeRepo({})
        hollow = ("evidence: dev/reports/design_reviews/deleted.md\n"
                  "checksum note: " + "a" * 64 + "\n")
        v = _routing_doc_violations(hollow, repo)
        self.assertIn("uncoupled_pointer:dev/reports/design_reviews/deleted.md", v,
                      "a dev/reports path with no same-line digest must redden")
        self.assertIn("missing_coupled_governed_pointer", v,
                      "an unrelated hash elsewhere must not satisfy the coupling")
        same_line = "see dev/reports/design_reviews/deleted.md " + "a" * 64 + "\n"
        self.assertIn("pointer_target_missing:dev/reports/design_reviews/deleted.md",
                      _routing_doc_violations(same_line, repo),
                      "a coupled pointer to a nonexistent target must redden")

    def test_hostile_f2_untracked_target_and_digest_laundering_are_rejected(self) -> None:
        body = b"real transcript bytes"
        good_digest = hashlib.sha256(body).hexdigest()
        tracked = _FakeRepo({"dev/reports/design_reviews/x.md": body})
        untracked = _FakeRepo({"dev/reports/design_reviews/x.md": body}, tracked=set())
        good = "review: dev/reports/design_reviews/x.md " + good_digest + "\n"
        self.assertEqual(_routing_doc_violations(good, tracked), [],
                         "positive control: existing tracked target with recomputed digest is clean")
        self.assertIn("pointer_target_untracked:dev/reports/design_reviews/x.md",
                      _routing_doc_violations(good, untracked),
                      "an untracked target must redden")
        laundered = "review: dev/reports/design_reviews/x.md " + "b" * 64 + "\n"
        self.assertIn("pointer_digest_mismatch:dev/reports/design_reviews/x.md",
                      _routing_doc_violations(laundered, tracked),
                      "a digest that does not recompute must redden (laundering)")
        deleted_only = "review transcripts live in the proof homes.\n"
        self.assertIn("missing_coupled_governed_pointer", _routing_doc_violations(deleted_only, tracked),
                      "merely deleting the scratch citation must not pass")
        self.assertIn("scratch_citation",
                      _routing_doc_violations("see scratchpad/work/codex-x.md\n", tracked),
                      "a surviving scratch citation must redden")

    # ---- finding 4: debt exercised against ACTUAL candidate-index members ----
    def test_hostile_f4_debt_growth_stale_and_expiry_from_real_index(self) -> None:
        now = datetime.now(timezone.utc)
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(_git(td, "init", "-q").returncode, 0)
            for rel in ("docs/a.md", "docs/b.md", "docs/stray.md"):
                p = Path(td) / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(rel, encoding="utf-8")
            _git(td, "add", "-A")
            index = _index_paths(td)
            groups = [{"name": "none", "patterns": ["docs/__none__/"]}]
            shapes = [{"root": "docs", "semantic_groups": groups, "exclusions": []}]
            residue = _shape_residue(shapes, index)
            row = _make_debt_row(["docs/a.md", "docs/b.md"], "2999-01-01T00:00:00Z")
            v = _ledger_violations_against_index([row], index, residue, now)
            self.assertIn("debt_growth_unledgered:docs/stray.md", v,
                          "a real index member beyond every baseline must redden as growth")
            grown = _make_debt_row(["docs/a.md", "docs/b.md", "docs/stray.md"], "2999-01-01T00:00:00Z")
            self.assertEqual(
                [x for x in _ledger_violations_against_index([grown], index, residue, now)
                 if x.startswith("debt_growth_unledgered")], [],
                "positive control: a baseline covering the residue carries no growth violation")
            _git(td, "rm", "-q", "--cached", "docs/a.md", "docs/b.md")
            shrunk_index = _index_paths(td)
            v2 = _ledger_violations_against_index(
                [row], shrunk_index, {"docs": []}, now)
            self.assertTrue(any(x.endswith("stale_debt_must_be_removed") for x in v2),
                            "a row whose members all left the real index must redden as stale")
        expired = _make_debt_row(["docs/a.md"], "2000-01-01T00:00:00Z")
        self.assertIn("expired", _debt_row_violations(expired, ["docs/a.md"], now))
        tampered = _make_debt_row(["docs/a.md"], "2999-01-01T00:00:00Z")
        tampered["baseline_digest"] = "0" * 64
        self.assertIn("digest_mismatch", _debt_row_violations(tampered, ["docs/a.md"], now))
        coupled = {**_make_debt_row(["docs/a.md"], "2999-01-01T00:00:00Z"), "test_id": "x"}
        self.assertIn("ratchet_coupling", _debt_row_violations(coupled, ["docs/a.md"], now))

    def test_hostile_f4_empty_baseline_row_is_rejected(self) -> None:
        now = datetime.now(timezone.utc)
        hollow = _make_debt_row([], "2999-01-01T00:00:00Z")
        self.assertIn("empty_baseline", _debt_row_violations(hollow, [], now),
                      "the r2 hollow case (explicit debt row with an empty baseline) must redden")

    # ---- finding 5: real shape rows behaviorally classified; typed fields ----
    def test_hostile_f5_bogus_kind_and_untyped_patterns_are_rejected(self) -> None:
        full = {"root": "scripts", "universe_source": "index",
                "evaluation": "exclusions-then-closed-partition",
                "allowed_node_kinds": ["file", "dir"], "semantic_groups": _SYNTH_GROUPS,
                "exclusions": _SYNTH_EXCLUSIONS, "child_contracts": ["contracts/org_child.json"],
                "classification_result": "exact-one"}
        self.assertEqual(_validate_shape_row(full), [],
                         "positive control: a fully-formed shape row validates")
        bogus_kind = {**full, "allowed_node_kinds": ["bogus"]}
        self.assertTrue(any(x.startswith("allowed_node_kinds_unknown") for x in _validate_shape_row(bogus_kind)),
                        "the r2 hollow case allowed_node_kinds=['bogus'] must redden")
        untyped = {**full, "semantic_groups": [{"name": "g", "patterns": "not-a-list"}]}
        self.assertIn("each semantic group needs patterns as a non-empty list of strings",
                      _validate_shape_row(untyped),
                      "the r2 hollow case patterns='not-a-list' must redden")
        stub = {"root": "scripts", "universe_source": "index",
                "evaluation": "exclusions-then-closed-partition"}
        self.assertNotEqual(_validate_shape_row(stub), [],
                            "a bare 3-field stub row must be rejected as a non-classifier")

    def test_hostile_f5_real_index_classification_catches_stray_and_double_match(self) -> None:
        verdicts = _classify_index(_SYNTH_INDEX, _SYNTH_GROUPS, _SYNTH_EXCLUSIONS)
        self.assertEqual(verdicts["scripts/misc/stray.py"], "unclassified")
        self.assertEqual(verdicts["scripts/render/cards/badges.py"], "ambiguous")
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(_git(td, "init", "-q").returncode, 0)
            for rel in ("scripts/core/config.py", "scripts/misc/stray.py"):
                p = Path(td) / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("x", encoding="utf-8")
            _git(td, "add", "-A")
            shapes = [{"root": "scripts", "semantic_groups": _SYNTH_GROUPS,
                       "exclusions": _SYNTH_EXCLUSIONS}]
            residue = _shape_residue(shapes, _index_paths(td))
            self.assertEqual(residue["scripts"], ["scripts/misc/stray.py"],
                             "the classifier must run over the REAL index and flag the stray")

    # ---- finding 6: stub rows, string parity, wrong paths all redden ----
    def test_hostile_f6_stub_rows_and_string_parity_are_rejected(self) -> None:
        self.assertEqual(_live_controls_violations({"rows": _valid_control_rows()}), [],
                         "positive control: complete typed rows with exact paths pass")
        hollow = [{"id": "claude-harness", "authoritative": False,
                   "authority": "contracts/role_registry.toml", "mirror_parity_check": "no"},
                  {"id": "git-local-config-hooks"}, {"id": "virtualenv"}, {"id": "caches"}]
        v = _live_controls_violations({"rows": hollow})
        self.assertIn("claude-harness:path_not_exact", v,
                      "the r2 hollow case: harness row omitting its .claude path must redden")
        self.assertIn("mirror_parity_check_not_boolean_true", v,
                      "the r2 hollow case: mirror_parity_check='no' must redden (boolean parity)")
        self.assertIn("git-local-config-hooks:authoritative_not_false", v,
                      "an id-only row must redden on every required typed field")
        self.assertIn("git:missing_hooks_path_policy", v,
                      "the git row must carry the hooksPath policy (2026-07-17 binding 1)")
        self.assertIn("caches:paths_not_typed_list", v)
        neg = _valid_control_rows()
        neg[0] = {**neg[0], "authority": "NOT contracts/role_registry.toml"}
        self.assertIn("authority_not_exact_registry", _live_controls_violations({"rows": neg}),
                      "an authority that merely CONTAINS the registry name must redden")
        fork = _valid_control_rows()
        fork[0] = {**fork[0], "note": "reopens via amendment fork"}
        self.assertIn("amendment_fork", _live_controls_violations({"rows": fork}))
        missing = _valid_control_rows()[:1]
        self.assertTrue(any(x.startswith("not_closed") for x in _live_controls_violations({"rows": missing})))
        dup = _valid_control_rows() + [{"id": "caches", "paths": ["x/"], "authoritative": False,
                                        "purpose": "dup"}]
        self.assertIn("duplicate_control_rows", _live_controls_violations({"rows": dup}))

    # ---- finding 7: untyped manifest rows and fake back-references redden ----
    def test_hostile_f7_untyped_manifest_row_is_rejected(self) -> None:
        body = b"envelope"
        digest = hashlib.sha256(body).hexdigest()
        repo = _FakeRepo({"dev/reports/admissions/x.json": body,
                          "docs/plans/ACTIVE.md": "cites dev/reports/admissions/x.json"})
        good = {"path": "dev/reports/admissions/x.json", "sha256": digest,
                "schema_id": "AdmissionEnvelope", "schema_version": 1, "subject": "w3c-org",
                "producer": "codex-gate", "produced_utc": "2026-07-16T00:00:00Z",
                "retention_class": "permanent", "referenced_by": ["docs/plans/ACTIVE.md"]}
        self.assertEqual(_manifest_row_violations(good, repo), [],
                         "positive control: a fully typed row with a real citing back-reference")
        self.assertIn("schema_version_not_positive_int",
                      _manifest_row_violations({**good, "schema_version": True}, repo),
                      "a boolean schema_version must redden")
        self.assertIn("produced_utc_not_iso8601_utc",
                      _manifest_row_violations({**good, "produced_utc": "yesterday"}, repo))
        self.assertIn("retention_class_invalid:'keep-newest-banana'",
                      _manifest_row_violations({**good, "retention_class": "keep-newest-banana"}, repo))
        self.assertIn("empty_identity:producer",
                      _manifest_row_violations({**good, "producer": " "}, repo))
        self.assertIn("malformed_sha256",
                      _manifest_row_violations({**good, "sha256": "abc"}, repo))
        self.assertIn("back_reference_missing:docs/plans/GHOST.md",
                      _manifest_row_violations({**good, "referenced_by": ["docs/plans/GHOST.md"]}, repo),
                      "a nonexistent back-reference must redden")
        silent = _FakeRepo({"dev/reports/admissions/x.json": body,
                            "docs/plans/ACTIVE.md": "no citation here"})
        self.assertIn("back_reference_does_not_cite:docs/plans/ACTIVE.md",
                      _manifest_row_violations(good, silent),
                      "a real doc that does not cite path or digest must redden")
        untracked = _FakeRepo({"dev/reports/admissions/x.json": body,
                               "docs/plans/ACTIVE.md": "cites dev/reports/admissions/x.json"},
                              tracked={"docs/plans/ACTIVE.md"})
        self.assertIn("artifact_untracked", _manifest_row_violations(good, untracked),
                      "the artifact itself must be tracked")
        self.assertIn("digest_mismatch",
                      _manifest_row_violations({**good, "sha256": "0" * 64}, repo))
        self.assertIn("correspondence_gap", _manifest_row_violations(
            good, _FakeRepo({"docs/plans/ACTIVE.md": "cites dev/reports/admissions/x.json"})))

    def test_hostile_f7_finalized_rows_require_digest_bearing_citations(self) -> None:
        body = b"sealed"
        digest = hashlib.sha256(body).hexdigest()
        citing = f"admission dev/reports/admissions/s.json sha256 {digest}"
        repo = _FakeRepo({"dev/reports/admissions/s.json": body, "docs/plans/ACTIVE.md": citing})
        sealed = {"path": "dev/reports/admissions/s.json", "sha256": digest,
                  "schema_id": "AdmissionEnvelope", "schema_version": 1, "subject": "s",
                  "producer": "codex-gate", "produced_utc": "2026-07-16T00:00:00Z",
                  "retention_class": "permanent", "referenced_by": ["docs/plans/ACTIVE.md"],
                  "finalized": True}
        self.assertEqual(_manifest_row_violations(sealed, repo), [],
                         "positive control: finalized row with a digest-bearing citation")
        path_only = _FakeRepo({"dev/reports/admissions/s.json": body,
                               "docs/plans/ACTIVE.md": "admission dev/reports/admissions/s.json"})
        self.assertIn("finalized_back_reference_not_digest_bearing:docs/plans/ACTIVE.md",
                      _manifest_row_violations(sealed, path_only),
                      "a finalized row cited by path alone must redden")
        drifted = _FakeRepo({"dev/reports/admissions/s.json": b"tampered",
                             "docs/plans/ACTIVE.md": citing})
        self.assertIn("digest_mismatch", _manifest_row_violations(sealed, drifted),
                      "REAL sealed-state exercise: drifted artifact bytes redden the finalized row")
        self.assertIn("finalized_row_mutation",
                      _sealed_row_mutation(sealed, {**sealed, "sha256": "changed"}))
        self.assertEqual(_sealed_row_mutation(sealed, sealed), [])

    # ---- F3/F6/F8 retained catches (category map, rosters, guides) ----
    def test_hostile_category_map_and_roster_and_guide_catches(self) -> None:
        name_list = sorted(CLOSED_CATEGORIES)
        self.assertIn("categories_must_be_a_map_not_a_name_list", _category_map_violations(name_list))
        empty_fields = {n: {} for n in CLOSED_CATEGORIES}
        self.assertTrue(any("missing_owner" in x for x in _category_map_violations(empty_fields)))
        extra = {n: {"owner": "o", "purpose": "p", "retention": "permanent"} for n in CLOSED_CATEGORIES}
        extra["proposals"] = {"owner": "o", "purpose": "p", "retention": "permanent"}
        self.assertTrue(any("not_closed_five" in x for x in _category_map_violations(extra)))
        good = {n: {"owner": "contracts/repo_layout.json", "purpose": "typed evidence",
                    "retention": "permanent"} for n in CLOSED_CATEGORIES}
        self.assertEqual(_category_map_violations(good), [])
        global_only = {"schema": {"control_files": ["manifest.json"]},
                       "categories": {"admissions": {"retention": "permanent"}}}
        self.assertIn("global_control_files_list_is_a_defect", _control_files_violations(global_only))
        per_cat = {"categories": {"admissions": {"control_files": ["manifest.json"]}}}
        self.assertIn("admissions:guide_not_excluded", _control_files_violations(per_cat))
        self.assertEqual(_control_files_violations(
            {"categories": {"admissions": {"control_files": ["manifest.json", "README.md"]}}}), [])
        dup = [{"name": "MODULE_HOMES"}, {"name": "MODULE_HOMES"}, {"name": "TEST_GROUPS"}]
        self.assertIn("duplicate_roster_names", _roster_name_violations(dup))
        extra_r = [{"name": "MODULE_HOMES"}, {"name": "TEST_GROUPS"}, {"name": "EXTRA"}]
        self.assertTrue(any("roster_set_not_closed" in x for x in _roster_name_violations(extra_r)))
        self.assertEqual(_roster_name_violations([{"name": "MODULE_HOMES"}, {"name": "TEST_GROUPS"}]), [])
        self.assertIn("missing_contract_anchor", _guide_violations(""))
        active = f"Use the {ANCHOR_CONTRACT} law ({ANCHOR_GUARD}). Add a proposals category here.\n"
        self.assertTrue(any(x.startswith("teaches_active:") for x in _guide_violations(active)))
        retired = (f"Governed by {ANCHOR_CONTRACT} ({ANCHOR_GUARD}).\n"
                   f"The proposals category was retired 2026-07-16; do not use it.\n")
        self.assertEqual(_guide_violations(retired), [])

    # ---- CR-15/CR-16: hostile births refuse and leave the tree byte-identical ----
    def test_hostile_birth_refusals_leave_tree_byte_identical(self) -> None:
        table = _SYNTH_BIRTH_TABLE
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "scratchpad" / "active" / "org").mkdir(parents=True)
            outside = root / "outside-target"
            outside.mkdir()
            (root / "scratchpad" / "active" / "org" / "prompts_link").symlink_to(outside)
            before = _tree_snapshot(root)
            nfd = unicodedata.normalize("NFD", "scratchpad/active/org/prompts/café.txt")
            hostile = [
                ("conductor", "prompts", "../escape.txt"),
                ("conductor", "prompts", "/abs/x.txt"),
                ("conductor", "prompts", "a\\b.txt"),
                ("conductor", "prompts", nfd),
                ("conductor", "prompts", "scratchpad/stray.txt"),
                ("conductor", "prompts", "scratchpad/work/new.txt"),
                ("conductor", "prompts", "scratchpad/active/bogus/prompts/x.txt"),
                ("conductor", "prompts", "scratchpad/active/w6/prompts/x.txt"),
                ("conductor", "prompts", "scratchpad/active/org/packets/x.txt"),
                ("conductor", "prompts", "scratchpad/active/org/prompts/x.exe"),
                ("conductor", "unknown-kind", "scratchpad/active/org/prompts/x.txt"),
                ("ghost-producer", "prompts", "scratchpad/active/org/prompts/x.txt"),
                ("w6-producer", "receipt", "scratchpad/active/w6/receipt/x.json"),
                ("codex-gate", "gate_transcript", "dev/reports/worker_reviews/x.md"),
                ("conductor", "prompts", "scratchpad/active/org/prompts_link/x.txt"),
            ]
            for producer, kind, proposed in hostile:
                decision, reason = _attempt_birth(root, producer, kind, proposed, b"x", table)
                self.assertEqual(decision, "refuse",
                                 f"hostile birth must refuse: {(producer, kind, proposed)} -> {reason}")
            self.assertEqual(_tree_snapshot(root), before,
                             "a refused birth must leave the tree byte-identical")
            self.assertEqual(sorted(outside.iterdir()), [],
                             "the symlink target must stay empty (no write through the link)")
            decision, dest = _attempt_birth(
                root, "conductor", "prompts", "scratchpad/active/org/prompts/p.txt", b"ok", table)
            self.assertEqual(decision, "accept", "positive control: the lawful birth lands")
            self.assertTrue(Path(dest).is_file())

    def test_hostile_birth_table_rejects_forks_and_sixth_category(self) -> None:
        self.assertEqual(_birth_table_violations(_SYNTH_BIRTH_TABLE), [],
                         "positive control: the synthetic table is valid")
        dup = json.loads(json.dumps(_SYNTH_BIRTH_TABLE))
        dup["rules"].append(dict(dup["rules"][0]))
        self.assertTrue(any(x.startswith("duplicate_rule") for x in _birth_table_violations(dup)),
                        "two homes for one (producer, kind) must redden (exact-one)")
        sixth = json.loads(json.dumps(_SYNTH_BIRTH_TABLE))
        sixth["rules"].append({"producer": "codex-gate", "artifact_kind": "receipt",
                               "home_root": "dev-reports:proposals"})
        self.assertTrue(any(x.startswith("sixth_report_category") for x in _birth_table_violations(sixth)),
                        "a sixth dev/reports category must redden")
        leak = json.loads(json.dumps(_SYNTH_BIRTH_TABLE))
        leak["rules"].append({"producer": "someone", "artifact_kind": "gate_transcript",
                              "home_root": "scratch-active", "lane": "org"})
        self.assertTrue(any(x.startswith("tracked_record_kind_routed_to_scratch")
                            for x in _birth_table_violations(leak)),
                        "a tracked-record kind routed to scratch must redden (binding 7)")

    def test_hostile_gitignore_anchoring_probe(self) -> None:
        """Hermetic `git check-ignore --no-index` proof that the ANCHORED pattern is the fix:
        `/scratchpad/` ignores the root tree only; the unanchored form also swallows nested
        `a/scratchpad/` (the §law-2 defect)."""
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(_git(td, "init", "-q").returncode, 0)
            (Path(td) / ".gitignore").write_text("/scratchpad/\n", encoding="utf-8")
            anchored_root = _git(td, "check-ignore", "-q", "--no-index", "scratchpad/x.md")
            anchored_nested = _git(td, "check-ignore", "-q", "--no-index", "a/scratchpad/x.md")
            self.assertEqual(anchored_root.returncode, 0, "anchored pattern ignores the root tree")
            self.assertEqual(anchored_nested.returncode, 1, "anchored pattern spares nested trees")
            (Path(td) / ".gitignore").write_text("scratchpad/\n", encoding="utf-8")
            unanchored_nested = _git(td, "check-ignore", "-q", "--no-index", "a/scratchpad/x.md")
            self.assertEqual(unanchored_nested.returncode, 0,
                             "the unanchored form swallows nested paths (the defect)")

    # ---- CR-17: orphan-worktree detection over real registrations ----
    def test_hostile_orphan_worktree_detection(self) -> None:
        now = datetime.now(timezone.utc)
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            repo.mkdir()
            self.assertEqual(_git(repo, "init", "-q").returncode, 0)
            (repo / "seed.txt").write_text("seed", encoding="utf-8")
            _git(repo, "add", "-A")
            r = _git(repo, "-c", "user.name=probe", "-c", "user.email=probe@local",
                     "commit", "-q", "-m", "seed")
            self.assertEqual(r.returncode, 0, r.stderr)
            room1 = Path(td) / "room-lane-a"
            room2 = Path(td) / "room-stray"
            self.assertEqual(_git(repo, "worktree", "add", "--detach", "-q", str(room1)).returncode, 0)
            self.assertEqual(_git(repo, "worktree", "add", "--detach", "-q", str(room2)).returncode, 0)
            primary, linked = _registered_worktrees(repo)
            self.assertEqual(len(linked), 2, "both rooms must register")
            live = [{"lane": "lane-a", "path_suffix": "room-lane-a", "expires_utc": "2999-01-01T00:00:00Z"}]
            orphans = _orphan_worktrees(linked, live, receipt_text="", now=now)
            self.assertEqual([p.rsplit("/", 1)[-1] for p in orphans], ["room-stray"],
                             "exactly the un-rostered, un-receipted room is an orphan")
            # receipts derive from the registry, so they carry the REGISTERED (resolved) path
            stray_registered = [p for p in linked if p.endswith("room-stray")][0]
            receipted = _orphan_worktrees(linked, live, receipt_text=stray_registered, now=now)
            self.assertEqual(receipted, [],
                             "a pending-retirement receipt naming the registered path covers the room")
            expired_row = [{"lane": "lane-a", "path_suffix": "room-lane-a",
                            "expires_utc": "2000-01-01T00:00:00Z"}]
            self.assertEqual(len(_orphan_worktrees(linked, expired_row, "", now)), 2,
                             "an expired live-lane row covers nothing (liveness law)")

    # ---- CR-16 arm: fork visibility (guards-gap binding 3) ----
    def test_hostile_fork_divergent_kin_detection(self) -> None:
        c4_shaped = {
            "scratchpad/work/fable-slice0-rev16-fold-2026-07-16.md": "a" * 64,
            "scratchpad/active/slice0/folds/local-slice0-rev16-fold-2026-07-16.md": "b" * 64,
        }
        self.assertEqual(_fork_findings(c4_shaped, []),
                         ["divergent_kin:slice0-rev16-fold-2026-07-16.md"],
                         "the C4-shaped divergent twin must be detected across producer prefixes")
        pointed = [{"loser": "scratchpad/active/slice0/folds/local-slice0-rev16-fold-2026-07-16.md",
                    "winner": "scratchpad/work/fable-slice0-rev16-fold-2026-07-16.md"}]
        self.assertEqual(_fork_findings(c4_shaped, pointed), [],
                         "a supersession pointer is the lawful disambiguator")
        multiplicity = {
            "scratchpad/work/demo-w6/pack/index.html": "c" * 64,
            "scratchpad/work/demo-w6/pack2/index.html": "c" * 64,
        }
        self.assertEqual(_fork_findings(multiplicity, []), [],
                         "identical digests are lawful multiplicity (W6 determinism witnesses)")

    # ---- CR-18: hook text law ----
    def test_hostile_hook_text_discovery_and_missing_pin_rejected(self) -> None:
        good = ("#!/bin/sh\nset -e\n"
                "# ratchet-aware: fail only on failures outside contracts/correction_baseline.json\n"
                "PYTHONDONTWRITEBYTECODE=1 python3 scripts/organization/hooks/run_pinned_guards.py "
                "tests.contracts.test_doc_authority tests.contracts.test_structural_layout\n")
        self.assertEqual(_hook_text_violations(good), [],
                         "positive control: a ratchet-aware hook pinning both guards passes")
        one_pin = good.replace(" tests.contracts.test_structural_layout", "")
        self.assertIn("missing_pin:tests.contracts.test_structural_layout",
                      _hook_text_violations(one_pin))
        discovery = "#!/bin/sh\npython3 -m unittest discover -s tests\n"
        v = _hook_text_violations(discovery)
        self.assertIn("forbidden_full_discovery", v,
                      "full discovery would run the intentionally-RED ratchet set: forbidden")
        raw_pin = good.replace(
            "# ratchet-aware: fail only on failures outside contracts/correction_baseline.json\n", "")
        self.assertIn("missing_ratchet_awareness", _hook_text_violations(raw_pin),
                      "a raw-pinned hook would block every commit at 74fe3ecd (five "
                      "baseline-held structural_layout failures): it must cite the baseline")

    # ---- CR-19: consumer-ledger growth detected from real index blobs ----
    def test_hostile_consumer_ledger_growth_detected_from_index(self) -> None:
        now = datetime.now(timezone.utc)
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(_git(td, "init", "-q").returncode, 0)
            files = {"scripts/a.py": "contracts/repo_layout.json\n",
                     "docs/b.md": "contracts/repo_layout.json\ncontracts/repo_layout.json\n"}
            for rel, text in files.items():
                p = Path(td) / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(text, encoding="utf-8")
            _git(td, "add", "-A")
            observed = _grep_cached_counts(td, BOOTSTRAP_ANCHOR)
            self.assertEqual(observed, {"scripts/a.py": 1, "docs/b.md": 2},
                             "counts recompute from the candidate-index blobs")
            rows = [["docs/b.md", 2, "doc"], ["scripts/a.py", 1, "code"]]
            section = {
                "anchor": BOOTSTRAP_ANCHOR,
                "rows": [{"consumer_path": p, "literal_occurrence_count": n, "consumer_kind": k}
                         for p, n, k in rows],
                "digest": hashlib.sha256(json.dumps(
                    [[p, n, k] for p, n, k in rows], separators=(",", ":"),
                    ensure_ascii=False).encode("utf-8")).hexdigest(),
                "owner": "org-L1", "expires_utc": "2999-01-01T00:00:00Z",
            }
            self.assertEqual(_consumer_ledger_violations(section, observed, now), [],
                             "positive control: an exact ledger over the observed counts is clean")
            grown = dict(observed)
            grown["site/new.html"] = 1
            self.assertIn("consumer_growth:site/new.html",
                          _consumer_ledger_violations(section, grown, now),
                          "a new consumer beyond the ledger must redden (subset-only shrink)")
            bumped = dict(observed, **{"scripts/a.py": 3})
            self.assertIn("occurrence_growth:scripts/a.py",
                          _consumer_ledger_violations(section, bumped, now))
            tampered = dict(section, digest="0" * 64)
            self.assertIn("digest_mismatch", _consumer_ledger_violations(tampered, observed, now))
            self.assertIn("stale_ledger_must_be_removed",
                          _consumer_ledger_violations(section, {}, now))

    # ---- CR-20: scratch-citation dispositions ----
    def test_hostile_scratch_citation_disposition_catches(self) -> None:
        offenders = {".gitignore": "/scratchpad/\n",
                     "docs/x.md": "see scratchpad/work/codex-a.md\n"}
        rows = [{"path": ".gitignore", "disposition": "grammar-only"},
                {"path": "docs/x.md", "disposition": "dangling-history"}]
        self.assertEqual(_scratch_citation_violations(rows, offenders), [],
                         "positive control: every citer carries a lawful disposition")
        self.assertIn("undispositioned_scratch_citer:docs/x.md",
                      _scratch_citation_violations(rows[:1], offenders),
                      "a tracked scratch citer with no disposition row must redden")
        bad_grammar = [{"path": ".gitignore", "disposition": "grammar-only"},
                       {"path": "docs/x.md", "disposition": "grammar-only"}]
        self.assertIn("grammar_only_cites_scratch_file:docs/x.md",
                      _scratch_citation_violations(bad_grammar, offenders),
                      "grammar-only may keep the tree name, never a scratch FILE path")
        stale = rows + [{"path": "docs/gone.md", "disposition": "dangling-history"}]
        self.assertIn("stale_disposition_row:docs/gone.md",
                      _scratch_citation_violations(stale, offenders))


# ====================================================================================
# REAL CONTRACT ARMS — CR-1..CR-9, CR-14 + intake. RED today; flip step in each docstring.
# ====================================================================================
class OrgRootwideContract(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.repo = _RepoView(ROOT)
        self.now = datetime.now(timezone.utc)

    # -- CR-1 (r2-g1 / F2 / r2-finding-4) : flips at L1 ----------------------------
    def test_debt_rows_are_self_contained_shrink_ledgers(self) -> None:
        """RED today: the contract has no org_shape_accepted_debt ledger. At L1 every row is
        exercised against the ACTUAL candidate index (present members, residue growth, stale
        rows), not against hand-typed member lists."""
        self.assertIn(
            "org_shape_accepted_debt", self.contract,
            "contract must carry the self-contained shrink-debt ledger; it is absent today",
        )
        ledger = self.contract["org_shape_accepted_debt"]
        self.assertIsInstance(ledger, list, "org_shape_accepted_debt must be a list of debt rows")
        index = _index_paths(ROOT)
        shapes = self.contract.get("shape", [])
        residue = _shape_residue(shapes, index) if shapes else {}
        violations = _ledger_violations_against_index(ledger, index, residue, self.now)
        self.assertEqual(
            violations, [],
            f"every debt row must hold against the real candidate index: {violations}",
        )

    # -- CR-2 (r2-g2) : flips at L1 -------------------------------------------------
    def test_contract_metadata_declares_ratified_root_shape_owner(self) -> None:
        self.assertEqual(
            self.contract.get("authority_status"), "ratified_root_shape_owner",
            "authority_status must transition candidate_only -> ratified_root_shape_owner",
        )
        self.assertFalse(
            self.contract.get("cannot_mark_done", False),
            "cannot_mark_done must be dropped or false once this contract is the ratified owner",
        )
        self.assertGreaterEqual(
            self.contract.get("schema_version", 0), 2,
            "schema_version must advance to >= 2 with the authority transition",
        )
        self.assertNotIn(
            "eventual decider", self.contract.get("purpose", ""),
            "the external-decider sentence must be retired from purpose",
        )

    # -- CR-3 (r2-g2 / F6) : flips at L1 --------------------------------------------
    def test_module_and_test_rosters_are_checked_projections(self) -> None:
        self.assertIn(
            "projections", self.contract,
            "contract must register MODULE_HOMES + TEST_GROUPS as checked projections",
        )
        raw = self.contract["projections"].get("rosters", [])
        self.assertEqual(
            _roster_name_violations(raw), [],
            "roster names must be unique and closed to exactly the two expected rosters",
        )
        rosters = {r["name"]: r for r in raw}  # safe: uniqueness asserted above

        from scripts.organization.layout_contract import MODULE_HOMES
        from scripts.organization.tests_layout_contract import TEST_GROUPS

        mh = rosters["MODULE_HOMES"]
        self.assertEqual(mh.get("owner"), "contracts/repo_layout.json")
        self.assertEqual(mh.get("source"), "scripts/organization/layout_contract.py")
        module_pairs = sorted([h.source_path, h.target_path] for h in MODULE_HOMES)
        self.assertEqual(
            sorted(mh.get("members", [])), module_pairs,
            "MODULE_HOMES projection must carry the full source->target mapping, not targets alone",
        )
        tg = rosters["TEST_GROUPS"]
        self.assertEqual(tg.get("owner"), "contracts/repo_layout.json")
        self.assertEqual(tg.get("source"), "scripts/organization/tests_layout_contract.py")
        test_members = sorted(f"tests/{g.name}/{m}" for g in TEST_GROUPS for m in g.modules)
        self.assertEqual(
            sorted(tg.get("members", [])), test_members,
            "TEST_GROUPS projection must be one-to-one with the in-code roster",
        )

    # -- CR-4 (r2-g3 / F3 / r2-finding-7) : flips at L1 ------------------------------
    def test_registered_category_homes_exist_tracked_with_manifests(self) -> None:
        """RED today: no [dev_reports] section, nothing tracked under dev/. At L1 the homes land
        EMPTY; every POPULATED row must pass the fully TYPED row law against the REAL tree
        (existence, trackedness, digest recompute, real citing back-references, sealed rows)."""
        self.assertIn(
            "dev_reports", self.contract,
            "contract must carry the [dev_reports] evidence-home section; it is absent today",
        )
        categories = self.contract["dev_reports"].get("categories", {})
        self.assertTrue(categories, "[dev_reports].categories must be a non-empty closed map")
        for name in sorted(categories):
            manifest_rel = f"dev/reports/{name}/manifest.json"
            manifest_path = ROOT / manifest_rel
            self.assertTrue(
                manifest_path.is_file(), f"category home missing a tracked manifest: {manifest_rel}",
            )
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertIsInstance(data, dict, f"{manifest_rel} must be a JSON object")
            self.assertIn("artifacts", data, f"{manifest_rel} must declare an 'artifacts' row list")
            retention = str(categories[name].get("retention", "")) if isinstance(categories[name], dict) else ""
            # empty homes are the intended early state -- do NOT redden an empty artifacts list;
            # every POPULATED row must pass the typed schema against the real tree.
            for row in data.get("artifacts", []):
                self.assertEqual(
                    _manifest_row_violations(row, self.repo), [],
                    f"populated manifest row in {manifest_rel} fails the typed row law: "
                    f"{_manifest_row_violations(row, self.repo)}",
                )
                if retention == "permanent":
                    self.assertIs(
                        row.get("finalized"), True,
                        f"{manifest_rel}: permanent-retention rows land finalized (sealed)",
                    )
            self.assertTrue(_git_tracked(manifest_rel), f"{manifest_rel} must be tracked")

    # -- CR-5 (r2-g3 / F7 / r2-finding-2) : flips at L2/L3 ---------------------------
    def test_tracked_routing_docs_cite_no_scratch_evidence(self) -> None:
        """RED today: ACTIVE.md still cites scratchpad/work and carries no coupled governed
        pointer. At L2/L3 both routing docs carry coupled path+digest pointers whose targets
        exist, are tracked, and recompute."""
        for rel in ("docs/plans/ACTIVE.md", "docs/plans/handoff/HANDOFF.md"):
            text = (ROOT / rel).read_text(encoding="utf-8")
            violations = _routing_doc_violations(text, self.repo)
            self.assertEqual(
                violations, [],
                f"{rel} must drop scratch citations AND carry verified coupled governed "
                f"pointers; violations: {violations}",
            )

    # -- CR-6 (r2-g6 / F3) : flips at L1 ---------------------------------------------
    def test_manifest_schema_excludes_control_files_and_seals_permanent_rows(self) -> None:
        self.assertIn("dev_reports", self.contract, "no [dev_reports] schema exists today")
        dev_reports = self.contract["dev_reports"]
        self.assertEqual(
            _control_files_violations(dev_reports), [],
            "each category must exclude its own manifest.json + guide (per-category control files)",
        )
        perm = dev_reports.get("schema", {}).get("permanent_retention", {})
        self.assertIs(
            perm.get("requires_finalized"), True,
            "permanent-retention rows must require finalized: true (immutable seal)",
        )
        self.assertIs(
            perm.get("requires_digest_bearing_back_references"), True,
            "permanent-retention rows must require digest-bearing back-references",
        )

    # -- CR-7 (r1-f1 remainder / F4 / r2-finding-6) : flips at L1 ---------------------
    def test_live_control_enumeration_is_closed_with_tracked_authority(self) -> None:
        """RED today: no live_controls section. At L1 every row is complete and typed (exact
        paths, boolean-False authoritative, boolean-True mirror parity, exact registry
        authority) and the git row carries the hooksPath policy (2026-07-17 binding 1)."""
        self.assertIn(
            "live_controls", self.contract,
            "contract must carry the closed live-control enumeration; it is absent today",
        )
        violations = _live_controls_violations(self.contract["live_controls"])
        self.assertEqual(
            violations, [],
            f"live-control enumeration must be closed, complete, and typed: {violations}",
        )

    # -- CR-8 (r1-f2 remainder / F1 / r2-finding-5) : flips at L1 ---------------------
    def test_shape_sections_declare_index_universe_and_exclusion_precedence(self) -> None:
        """RED today: no [[shape]] rows. At L1 every governed root carries a typed row AND the
        declared classifier is RUN over the real candidate index: every path classifies
        exactly-one, with only debt-ledger baselines absorbing the legacy residue."""
        shapes = self.contract.get("shape", [])
        self.assertTrue(shapes, "contract must carry executable [[shape]] rows; none exist today")
        roots = [s.get("root") for s in shapes]
        self.assertEqual(len(roots), len(set(roots)), f"duplicate shape roots are rejected; got {roots}")
        missing = sorted(GOVERNED_ROOTS - set(roots))
        self.assertEqual(missing, [], f"every governed root needs a shape row; missing: {missing}")
        for s in shapes:
            self.assertEqual(
                _validate_shape_row(s), [],
                f"shape {s.get('root')!r} is not a real classifier: {_validate_shape_row(s)}",
            )
        index = _index_paths(ROOT)
        residue = _shape_residue(shapes, index)
        ledger = self.contract.get("org_shape_accepted_debt", [])
        covered = set()
        for row in ledger:
            covered.update(row.get("baseline_members", []))
        uncovered = {root: [p for p in paths if p not in covered]
                     for root, paths in residue.items() if [p for p in paths if p not in covered]}
        self.assertEqual(
            uncovered, {},
            f"the real classifier run over the real index must partition exactly-one "
            f"(or the residue must be frozen debt); uncovered: {uncovered}",
        )

    # -- CR-9 (r2-g5 / F3) : flips at L1 ----------------------------------------------
    def test_dev_reports_category_set_is_the_closed_five(self) -> None:
        self.assertIn("dev_reports", self.contract, "no [dev_reports] section exists today")
        categories = self.contract["dev_reports"].get("categories", {})
        self.assertEqual(
            _category_map_violations(categories), [],
            "the dev_reports categories must be exactly the closed five, each fully specified",
        )
        self.assertNotIn("proposals", categories, "the 'proposals' category must never re-enter")

    # -- CR-14 (r2-g5 / F8) : flips at L1 ---------------------------------------------
    def test_artifact_family_readmes_exist_and_teach_current_law(self) -> None:
        for rel in FAMILY_READMES:
            path = ROOT / rel
            self.assertTrue(path.is_file(), f"artifact-family README missing: {rel}")
            self.assertTrue(_git_tracked(rel), f"artifact-family README must be tracked: {rel}")
            text = path.read_text(encoding="utf-8")
            self.assertEqual(
                _guide_violations(text), [],
                f"{rel} must teach current law (carry anchors; ban only ACTIVE retired-law "
                f"phrasing); violations: {_guide_violations(text)}",
            )

    # -- intake (F7 / r2-finding-1) : flips at L2 --------------------------------------
    def test_intake_roster_is_complete_at_cutoff(self) -> None:
        """RED today: neither the intake manifest nor the independent roster exists. At L2 the
        cutoff roster is landed as its own tracked artifact; completeness derives from IT,
        never from the manifest's own rows. STEP ORDERING and the merge-commit cutover stay
        with exact-patch review + git history (design boundary)."""
        manifest_path = ROOT / INTAKE_MANIFEST_REL
        self.assertTrue(
            manifest_path.is_file(),
            f"the intake manifest {INTAKE_MANIFEST_REL} must exist at the L2 cutoff; absent today",
        )
        roster_path = ROOT / INTAKE_ROSTER_REL
        self.assertTrue(
            roster_path.is_file(),
            f"the INDEPENDENT cutoff roster {INTAKE_ROSTER_REL} must exist; absent today",
        )
        self.assertTrue(_git_tracked(INTAKE_MANIFEST_REL), "intake manifest must be tracked")
        self.assertTrue(_git_tracked(INTAKE_ROSTER_REL), "cutoff roster must be tracked")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertIsNotNone(_parse_utc(manifest.get("cutoff_utc")),
                             "the manifest must declare the ISO-8601 UTC cutoff timestamp")
        pointer = manifest.get("roster", {})
        self.assertEqual(pointer.get("path"), INTAKE_ROSTER_REL,
                         "the manifest must point at the independent roster artifact")
        roster_bytes = roster_path.read_bytes()
        self.assertEqual(
            hashlib.sha256(roster_bytes).hexdigest(), pointer.get("sha256"),
            "the roster pointer digest must recompute over the roster bytes",
        )
        roster_rows = _parse_intake_roster(roster_bytes.decode("utf-8"))
        self.assertGreater(
            len(roster_rows), 0,
            "the cutoff roster cannot be empty: the scratch tree provably holds durable "
            "evidence at cutoff (counts are diagnostic, never contract constants)",
        )
        violations = _intake_violations(manifest.get("sources", []), roster_rows)
        self.assertEqual(
            violations, [],
            f"the manifest must cover the independent roster exactly: {violations}",
        )


# ====================================================================================
# NEW LAW — CR-15..CR-20 (2026-07-17 checkpoint + consolidation bindings). RED today.
# ====================================================================================
class OrgRootwideNewLaw(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.now = datetime.now(timezone.utc)

    # -- CR-15 : flips at L1 -----------------------------------------------------------
    def test_birth_routing_table_is_total_and_disjoint(self) -> None:
        """RED today: no birth_routing section. At L1 the data-driven router table lands:
        exact-one home per (producer, artifact_kind); closed home vocabulary (five dev/reports
        categories, assets-receipts, descriptor-bound custody, the two scratch roots); tracked
        record kinds may never choose scratch. The production router
        scripts/organization/birth_router.py conforms; the W6 producer calls it before its
        first mkdir/write (bypass kill = W6-lane integration test, packet-bound)."""
        self.assertIn(
            "birth_routing", self.contract,
            "contract must carry the [birth_routing] table; it is absent today",
        )
        table = self.contract["birth_routing"]
        violations = _birth_table_violations(table)
        self.assertEqual(violations, [], f"the routing table must be valid and disjoint: {violations}")
        self.assertEqual(
            _route_birth("__unknown__", "__unknown__", "x.md", table),
            ("refuse", "unknown_kind"),
            "the real table must refuse unknown kinds (total routing)",
        )
        self.assertEqual(
            _route_birth("__unknown__", table["artifact_kinds"][0]["name"],
                         "../escape" + table["artifact_kinds"][0]["extensions"][0], table)[0],
            "refuse",
            "the real table must refuse traversal births",
        )
        router = ROOT / "scripts" / "organization" / "birth_router.py"
        self.assertTrue(router.is_file(),
                        "scripts/organization/birth_router.py must land at L1 (producers call it)")
        self.assertTrue(_git_tracked("scripts/organization/birth_router.py"),
                        "the birth router must be tracked (governed home)")

    # -- CR-16 : flips at L1 -----------------------------------------------------------
    def test_scratch_grammar_two_roots_frozen_work_and_anchored_ignores(self) -> None:
        """RED today: no scratch_grammar section, no anchored ignore roster, no preflight
        script. At L1: the contract declares the closed two-root scratch grammar
        (active/<lane>/<kind>, archive/<date>/<lane>/<kind>) with work/ frozen; .gitignore
        carries the root-anchored roster; the preflight (fork-visibility arm included) ships
        as a tracked script, never as a clone-blocking test over ignored content."""
        self.assertIn(
            "scratch_grammar", self.contract,
            "contract must declare the closed post-cutover scratch grammar; absent today",
        )
        grammar = self.contract["scratch_grammar"]
        self.assertEqual(grammar.get("active_root"), "scratchpad/active")
        self.assertEqual(grammar.get("archive_root"), "scratchpad/archive")
        self.assertIn("scratchpad/work", grammar.get("frozen_roots", []),
                      "work/ is frozen legacy: no new files ever")
        sup = grammar.get("supersession_pointer", {})
        self.assertTrue(str(sup.get("filename", "")).strip(),
                        "the grammar must name the supersession-pointer artifact "
                        "(the lawful fork disambiguator)")
        ignore_lines = [ln.strip() for ln in
                        (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()]
        for pattern in GITIGNORE_ANCHORED_ROSTER:
            self.assertIn(
                pattern, ignore_lines,
                f".gitignore must carry the root-anchored clutter roster; missing: {pattern}",
            )
        preflight = ROOT / "scripts" / "organization" / "scratch_preflight.py"
        self.assertTrue(preflight.is_file(),
                        "scripts/organization/scratch_preflight.py must land at L1 "
                        "(scratch hygiene + fork visibility run as a local preflight)")
        self.assertTrue(_git_tracked("scripts/organization/scratch_preflight.py"))

    # -- CR-17 : flips at L1 -----------------------------------------------------------
    def test_registered_worktrees_have_live_lane_or_retirement_receipt(self) -> None:
        """RED today: no worktree_governance section. Consolidation law (operator order
        2026-07-17): any registered worktree without an unexpired live lane row or a
        pending-retirement receipt is a failing test. Deterministic in a clean clone (a clone
        registers no extra worktrees)."""
        self.assertIn(
            "worktree_governance", self.contract,
            "contract must carry the worktree_governance section; it is absent today",
        )
        gov = self.contract["worktree_governance"]
        live_rows = gov.get("live_lanes", [])
        self.assertIsInstance(live_rows, list, "live_lanes must be a list of typed rows")
        for r in live_rows:
            for field in ("lane", "path_suffix", "expires_utc"):
                self.assertTrue(str(r.get(field, "")).strip(),
                                f"live lane row missing {field}: {r}")
            self.assertIsNotNone(_parse_utc(r.get("expires_utc")),
                                 f"live lane row expires_utc must be ISO-8601 UTC: {r}")
        receipts_root = str(gov.get("retirement_receipts_root", "")).strip()
        self.assertTrue(receipts_root, "governance must name the retirement receipts root")
        receipt_text = ""
        receipts_dir = ROOT / receipts_root
        if receipts_dir.is_dir():
            for p in sorted(receipts_dir.rglob("*")):
                if p.is_file() and p.suffix in (".md", ".tsv", ".json"):
                    receipt_text += p.read_text(encoding="utf-8", errors="replace")
        _primary, linked = _registered_worktrees(ROOT)
        orphans = _orphan_worktrees(linked, live_rows, receipt_text, self.now)
        self.assertEqual(
            orphans, [],
            f"every registered worktree needs a live lane row or a pending-retirement "
            f"receipt; orphans: {orphans}",
        )

    # -- CR-18 : flips at L1 -----------------------------------------------------------
    def test_precommit_hook_pins_landed_green_guards(self) -> None:
        """RED today: no tracked hook exists and core.hooksPath is unset. At L1 the tracked
        hook script lands under the governed hooks dir pinning EXACTLY the two landed green
        guards (every commit, every branch); local core.hooksPath must be unset or resolve to
        the governed dir (universe-B law)."""
        hook = ROOT / HOOK_REL
        self.assertTrue(
            hook.is_file(),
            f"the governed pre-commit hook {HOOK_REL} must exist; it is absent today",
        )
        self.assertTrue(_git_tracked(HOOK_REL), "the hook script must be tracked")
        stage = _git(ROOT, "ls-files", "--stage", "--", HOOK_REL).stdout.strip()
        self.assertTrue(stage.startswith("100755"),
                        f"the hook must be executable in the index (100755); got: {stage!r}")
        text = hook.read_text(encoding="utf-8")
        violations = _hook_text_violations(text)
        self.assertEqual(violations, [], f"the hook must pin exactly the two green guards: {violations}")
        configured = _git(ROOT, "config", "core.hooksPath").stdout.strip()
        if configured:
            normalized = configured.rstrip("/")
            self.assertTrue(
                normalized == HOOKS_GOVERNED_DIR or normalized.endswith("/" + HOOKS_GOVERNED_DIR),
                f"core.hooksPath must resolve into the tracked governed dir "
                f"{HOOKS_GOVERNED_DIR}; got {configured!r}",
            )

    # -- CR-19 : flips at L1 -----------------------------------------------------------
    def test_bootstrap_anchor_consumer_ledger(self) -> None:
        """RED today: no consumer ledger. contracts/repo_layout.json is the ONLY loose
        bootstrap anchor; its consumer set is a recomputed, digest-sealed, subset-only-shrink
        ledger over the candidate-index blobs. No magic counts: the 2026-07-16 audit's 48/80/82
        line counts are diagnostic only and are NOT encoded here."""
        self.assertIn(
            "bootstrap_anchor_consumers", self.contract,
            "contract must carry the bootstrap-anchor consumer ledger; it is absent today",
        )
        section = self.contract["bootstrap_anchor_consumers"]
        self.assertEqual(section.get("anchor"), BOOTSTRAP_ANCHOR,
                         "the ledger anchors the one loose bootstrap contract")
        observed = _grep_cached_counts(ROOT, BOOTSTRAP_ANCHOR)
        violations = _consumer_ledger_violations(section, observed, self.now)
        self.assertEqual(
            violations, [],
            f"the consumer ledger must hold against the recomputed index counts: {violations}",
        )

    # -- CR-20 : section at L1; citations flip at L2/L3 ---------------------------------
    def test_scratch_retirement_checkpoint(self) -> None:
        """RED today: no scratch_citation_dispositions section (and tracked docs still cite
        scratchpad/work file paths; the physical work/ tree still holds files on the working
        machine). At L1 the disposition section lands; at L2/L3 every tracked scratch citation
        is either promoted (coupled path+digest, so the literal disappears), declared
        grammar-only (.gitignore/AGENTS tree-name mentions), or recorded dangling-history —
        and scratchpad/work/ is empty or absent. Nothing is deleted without ratification."""
        self.assertIn(
            "scratch_citation_dispositions", self.contract,
            "contract must carry the scratch-citation disposition rows; absent today",
        )
        rows = self.contract["scratch_citation_dispositions"]
        self.assertIsInstance(rows, list)
        grep = _git(ROOT, "grep", "-l", "--cached", "-F", "scratchpad/")
        offender_texts = {}
        for rel in [p for p in grep.stdout.splitlines() if p.strip()]:
            offender_texts[rel] = _RepoView(ROOT).read_text(rel)
        violations = _scratch_citation_violations(rows, offender_texts)
        self.assertEqual(
            violations, [],
            f"every tracked scratch citer needs a lawful disposition: {violations}",
        )
        work = ROOT / "scratchpad" / "work"
        if work.exists():
            leftovers = sorted(str(p.relative_to(ROOT)) for p in work.rglob("*") if p.is_file())
            self.assertEqual(
                leftovers, [],
                f"final checkpoint probe: scratchpad/work/ must be empty or absent after the "
                f"lossless intake; {len(leftovers)} files remain",
            )


if __name__ == "__main__":
    unittest.main()

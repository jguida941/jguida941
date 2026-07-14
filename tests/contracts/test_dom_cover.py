"""W2 - closed-world ownership for every class-bearing shipped DOM element.

The DATA is ``contracts/dom_cover.json``. This guard parses committed HTML as DOM start tags,
binds exact signatures to exercised emitters, and treats index's pre-W3 markup as immutable,
shrinking debt. Runtime dashboard classes remain an explicitly pinned W4 handoff.
"""
from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
import json
import re
import types
import unittest
from functools import wraps
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from unittest import mock


def _root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "contracts" / "page_manifest.json").is_file():
            return parent
    raise RuntimeError("repo root not found")


ROOT = _root()
CONTRACT_PATH = ROOT / "contracts" / "dom_cover.json"
MARKER = "data-dom-owner"

# Independent pins: changing mutable DATA and its self-reported hash together must still red.
INDEX_BASELINE_SHA256 = "43ef30ede628617d4de91a619ad607bf959104730e7249f9d934d712d3855b6b"
INDEX_HYDRATION_SCRIPT_SHA256 = "4b6c753aebf33739546c717759077cc907fa57a5c2d46c35791fba86f4edcb82"
ADMITTED_OWNER_EMITTERS = {
    "page.settings": "scripts/rendering/settings/settings.py::render_settings",
    "page.showcase": "scripts/rendering/showcase/showcase.py::render_showcase",
    "page.studio": "scripts/rendering/studio/studio.py::render_studio",
    "pageshell": "scripts/rendering/pageshell/pageshell.py::render_page_shell",
    "webkit.archetype": "scripts/rendering/webkit/archetype.py::render_archetype",
    "webkit.button": "scripts/rendering/webkit/components.py::render_button",
    "webkit.card": "scripts/rendering/webkit/components.py::render_card",
    "webkit.chip": "scripts/rendering/webkit/components.py::render_chip",
    "webkit.nav": "scripts/rendering/webkit/components.py::render_switchable_nav",
}
INDEX_ADMITTED_OWNERS = {"webkit.nav"}
RUNTIME_SCRIPT_SHA256 = {
    "index-hydration": "1fd0a8e1a50b7bacee632481c6a29af3601511bdf10732244f85f8c7068f7922",
    "studio-space-data": "dfdea4749364280200d2be02705097e1930776d4e977baca85fcaaeeabe4dd4a",
    "studio-toggle": "05efb2d307a54d28797ae4dcc7ee634fe1bf5ea9c8950c54e654b724cd528af2",
    "theme-continuity": "ba6b047216cd3c87896d81838f0f825cf26172ae4204e167c6c463a2ae3bf111",
}
RUNTIME_SOURCE_SHA256 = {
    "index-hydration": INDEX_HYDRATION_SCRIPT_SHA256,
    "studio-toggle": RUNTIME_SCRIPT_SHA256["studio-toggle"],
}


@dataclass(frozen=True)
class ClassElement:
    tag: str
    classes: tuple[str, ...]
    owner: str | None


class _ClassParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[ClassElement] = []
        self.errors: list[str] = []

    def _capture(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        names = [name for name, _ in attrs]
        if len(names) != len(set(names)):
            self.errors.append(f"{tag}: duplicate attribute")
            return
        data = dict(attrs)
        raw = (data.get("class") or "").split()
        if not raw:
            return
        if len(raw) != len(set(raw)):
            self.errors.append(f"{tag}: duplicate class token")
        self.elements.append(ClassElement(tag, tuple(sorted(raw)), data.get(MARKER)))

    def handle_starttag(self, tag, attrs):  # noqa: ANN001 - HTMLParser callback
        self._capture(tag, attrs)

    def handle_startendtag(self, tag, attrs):  # noqa: ANN001 - HTMLParser callback
        self._capture(tag, attrs)


class _ScriptParser(HTMLParser):
    _ACTIVE_TAGS = frozenset({
        "animate", "animatemotion", "animatetransform", "applet", "discard", "embed",
        "frame", "frameset", "iframe", "object", "portal", "set",
    })
    _URL_ATTRS = frozenset({"action", "data", "formaction", "href", "src", "xlink:href"})
    _EXECUTABLE_SCHEMES = (
        "javascript:",
        "vbscript:",
        "data:text/html",
        "data:application/xhtml+xml",
        "data:image/svg+xml",
    )

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self._in_script = False
        self._parts: list[str] = []
        self.scripts: list[str] = []
        self.inline_handlers: list[tuple[str, str]] = []
        self.external_scripts: list[str] = []
        self.active_surfaces: list[tuple[str, str]] = []

    def _inspect_start(self, tag, attrs, *, opens_script: bool):  # noqa: ANN001, ANN202
        tag = tag.lower()
        data = {name.lower(): value for name, value in attrs}
        if tag in self._ACTIVE_TAGS:
            self.active_surfaces.append((tag, "active embedding tag"))
        for name, value in attrs:
            lowered = name.lower()
            normalized = re.sub(r"[\x00-\x20\x7f]+", "", (value or "").lower())
            if lowered.startswith("on"):
                self.inline_handlers.append((tag, lowered))
            if lowered == "srcdoc":
                self.active_surfaces.append((tag, "srcdoc"))
            if lowered in self._URL_ATTRS and normalized.startswith(self._EXECUTABLE_SCHEMES):
                self.active_surfaces.append((tag, f"executable URL in {lowered}"))
        if tag == "meta" and (data.get("http-equiv") or "").strip().lower() == "refresh":
            self.active_surfaces.append((tag, "http-equiv refresh"))
        if tag == "script":
            external = data.get("src") or data.get("href") or data.get("xlink:href")
            if external:
                self.external_scripts.append(external)
            if opens_script:
                self._in_script = True
                self._parts = []

    def handle_starttag(self, tag, attrs):  # noqa: ANN001 - HTMLParser callback
        self._inspect_start(tag, attrs, opens_script=True)

    def handle_startendtag(self, tag, attrs):  # noqa: ANN001 - HTMLParser callback
        self._inspect_start(tag, attrs, opens_script=False)

    def handle_data(self, data: str) -> None:
        if self._in_script:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._in_script:
            self.scripts.append("".join(self._parts))
            self._in_script = False


def _parse(html: str) -> tuple[list[ClassElement], list[str]]:
    parser = _ClassParser()
    parser.feed(html)
    parser.close()
    return parser.elements, parser.errors


def _parse_scripts(html: str) -> _ScriptParser:
    parser = _ScriptParser()
    parser.feed(html)
    parser.close()
    return parser


def _manifest() -> dict:
    return json.loads((ROOT / "contracts" / "page_manifest.json").read_text(encoding="utf-8"))


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _baseline_payload(rows: list[dict]) -> bytes:
    immutable = [
        {key: row[key] for key in ("page", "tag", "classes", "baseline_count")}
        for row in rows
    ]
    return json.dumps(immutable, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _baseline_hash(rows: list[dict]) -> str:
    return hashlib.sha256(_baseline_payload(rows)).hexdigest()


def _contract_errors(contract: dict, manifest: dict) -> list[str]:
    errors: list[str] = []
    top_keys = {"contract_id", "schema_version", "authority_status", "cannot_mark_done", "purpose",
                "marker_attribute", "coverage", "owners", "pages"}
    if set(contract) != top_keys:
        errors.append("top-level keys are not closed")
    if contract.get("contract_id") != "ClosedWorldDomCover" or contract.get("schema_version") != 1:
        errors.append("contract identity/schema mismatch")
    if contract.get("authority_status") != "candidate_only" or contract.get("cannot_mark_done") is not True:
        errors.append("candidate-only honesty flags missing")
    if contract.get("marker_attribute") != MARKER:
        errors.append("marker attribute drift")

    coverage = contract.get("coverage", {})
    coverage_keys = {"claim", "classless_and_inline_scope", "rendered_dom_target",
                     "runtime_producers", "runtime_class_debt"}
    if set(coverage) != coverage_keys or coverage.get("claim") != "committed-static-dom":
        errors.append("coverage claim/schema drift")
    if coverage.get("rendered_dom_target") != "W4":
        errors.append("runtime closure must target W4")
    manifest_pages = {page["id"]: page for page in manifest["pages"]}
    producers = coverage.get("runtime_producers", [])
    producer_keys = {"id", "producer", "kind", "pages", "script_sha256"}
    if producers != sorted(producers, key=lambda row: row.get("id", "")):
        errors.append("runtime producers are not canonical")
    producer_ids: set[str] = set()
    producer_kinds: dict[str, str] = {}
    for row in producers:
        if set(row) != producer_keys:
            errors.append("runtime producer keys are not closed")
            continue
        producer_id = row["id"]
        if producer_id in producer_ids or not re.fullmatch(r"[a-z][\w-]*", producer_id):
            errors.append("duplicate/malformed runtime producer")
        producer_ids.add(producer_id)
        producer_kinds[producer_id] = row["kind"]
        if row["kind"] not in {"data-only", "dom-mutator"}:
            errors.append(f"{producer_id}: unknown runtime producer kind")
        if row["pages"] != sorted(set(row["pages"])) or not set(row["pages"]) <= set(manifest_pages):
            errors.append(f"{producer_id}: invalid runtime pages")
        if row["script_sha256"] != RUNTIME_SCRIPT_SHA256.get(producer_id):
            errors.append(f"{producer_id}: runtime script is not independently pinned")
    if producer_ids != set(RUNTIME_SCRIPT_SHA256):
        errors.append("runtime producer roster is not independently closed")

    runtime_debt = coverage.get("runtime_class_debt", {})
    if list(runtime_debt) != sorted(runtime_debt) or set(runtime_debt) != set(RUNTIME_SOURCE_SHA256):
        errors.append("runtime class debt roster is not independently closed")
    runtime_keys = {"page", "producer", "source_sha256", "class_tokens", "dynamic_axes"}
    for producer_id, runtime in runtime_debt.items():
        if set(runtime) != runtime_keys:
            errors.append(f"{producer_id}: runtime class debt keys are not closed")
            continue
        if producer_kinds.get(producer_id) != "dom-mutator" or runtime["page"] not in manifest_pages:
            errors.append(f"{producer_id}: runtime class debt has no declared mutator/page")
        if runtime["source_sha256"] != RUNTIME_SOURCE_SHA256.get(producer_id):
            errors.append(f"{producer_id}: runtime source is not independently pinned")
        tokens = runtime["class_tokens"]
        if tokens != sorted(set(tokens)) or not all(re.fullmatch(r"[A-Za-z_][\w-]*", x) for x in tokens):
            errors.append(f"{producer_id}: runtime class tokens are not canonical")
        axes = runtime["dynamic_axes"]
        if list(axes) != sorted(axes) or any(values != sorted(set(values)) for values in axes.values()):
            errors.append(f"{producer_id}: runtime dynamic axes are not canonical")

    pages = contract.get("pages", {})
    if set(pages) != set(manifest_pages):
        errors.append("contract pages do not exactly cover manifest")
    all_debt: list[dict] = []
    for page_id, page in pages.items():
        if set(page) != {"route", "debt_target", "debt_baseline_sha256", "debt"}:
            errors.append(f"{page_id}: page keys are not closed")
            continue
        if page_id not in manifest_pages or page["route"] != manifest_pages[page_id]["route"]:
            errors.append(f"{page_id}: route mismatch")
        debt = page["debt"]
        canonical_rows = sorted(debt, key=lambda row: (row.get("page", ""), row.get("tag", ""),
                                                        row.get("classes", [])))
        if debt != canonical_rows:
            errors.append(f"{page_id}: debt rows are not canonical")
        identities: set[tuple] = set()
        for row in debt:
            if set(row) != {"page", "tag", "classes", "baseline_count", "resolved_count"}:
                errors.append(f"{page_id}: debt row keys are not closed")
                continue
            classes = row["classes"]
            identity = (row["page"], row["tag"], tuple(classes))
            if identity in identities:
                errors.append(f"{page_id}: duplicate debt row")
            identities.add(identity)
            if row["page"] != page_id or not re.fullmatch(r"[a-z][\w-]*", row["tag"]):
                errors.append(f"{page_id}: malformed debt identity")
            if classes != sorted(set(classes)) or not classes:
                errors.append(f"{page_id}: malformed debt classes")
            base, resolved = row["baseline_count"], row["resolved_count"]
            if type(base) is not int or type(resolved) is not int or base <= 0 or not 0 <= resolved <= base:
                errors.append(f"{page_id}: invalid debt count bounds")
        all_debt.extend(debt)
        digest = _baseline_hash(debt)
        if page["debt_baseline_sha256"] != digest:
            errors.append(f"{page_id}: debt self-hash mismatch")
        if page_id == "index":
            if page["debt_target"] != "W3" or digest != INDEX_BASELINE_SHA256:
                errors.append("index debt is not pinned independently to W3")
        elif debt or page["debt_target"] is not None:
            errors.append(f"{page_id}: governed page carries debt")

    owners = contract.get("owners", {})
    emitter_map = {owner_id: owner.get("emitter") for owner_id, owner in owners.items()}
    if not owners or list(owners) != sorted(owners) or emitter_map != ADMITTED_OWNER_EMITTERS:
        errors.append("owner/emitter roster is not independently admitted")
    seen_signatures: set[tuple] = set()
    used_pages: set[str] = set()
    for owner_id, owner in owners.items():
        if set(owner) != {"emitter", "pages", "signatures"}:
            errors.append(f"{owner_id}: owner keys are not closed")
            continue
        if not re.fullmatch(r"[a-z][\w.-]*", owner_id):
            errors.append(f"{owner_id}: malformed owner id")
        allowed_pages = owner["pages"]
        if allowed_pages != sorted(set(allowed_pages)) or not set(allowed_pages) <= set(manifest_pages):
            errors.append(f"{owner_id}: non-canonical owner pages")
        signatures = owner["signatures"]
        if signatures != sorted(signatures, key=lambda row: (row.get("page", ""), row.get("tag", ""),
                                                               row.get("classes", []))):
            errors.append(f"{owner_id}: signatures are not canonical")
        for row in signatures:
            if set(row) != {"page", "tag", "classes", "count"}:
                errors.append(f"{owner_id}: signature keys are not closed")
                continue
            classes = row["classes"]
            identity = (owner_id, row["page"], row["tag"], tuple(classes))
            if identity in seen_signatures:
                errors.append(f"{owner_id}: duplicate signature")
            seen_signatures.add(identity)
            if row["page"] not in allowed_pages or classes != sorted(set(classes)) or not classes:
                errors.append(f"{owner_id}: malformed/off-page signature")
            if type(row["count"]) is not int or row["count"] <= 0:
                errors.append(f"{owner_id}: invalid signature count")
            used_pages.add(row["page"])
        if set(allowed_pages) != {r["page"] for r in signatures}:
            errors.append(f"{owner_id}: phantom allowed page")
    if used_pages != set(manifest_pages):
        errors.append("owner signatures do not reach every page")
    index_owners = {
        owner_id for owner_id, owner in owners.items()
        if any(row.get("page") == "index" for row in owner.get("signatures", []))
    }
    if index_owners != INDEX_ADMITTED_OWNERS:
        errors.append("index owner roster is not independently admitted")
    return errors


def _document_errors(page_id: str, html: str, contract: dict) -> list[str]:
    elements, errors = _parse(html)
    owners = contract["owners"]
    expected_owned = Counter()
    for owner_id, owner in owners.items():
        for row in owner["signatures"]:
            if row["page"] == page_id:
                expected_owned[(owner_id, row["tag"], tuple(row["classes"]))] = row["count"]
    actual_owned = Counter()
    actual_debt = Counter()
    for element in elements:
        if element.owner:
            if element.owner not in owners:
                errors.append(f"unknown owner {element.owner}")
                continue
            if page_id not in owners[element.owner]["pages"]:
                errors.append(f"owner {element.owner} is not allowed on {page_id}")
            actual_owned[(element.owner, element.tag, element.classes)] += 1
        else:
            actual_debt[(page_id, element.tag, element.classes)] += 1
    if actual_owned != expected_owned:
        errors.append(f"{page_id}: owned signatures/counts drifted")
    expected_debt = Counter()
    for row in contract["pages"][page_id]["debt"]:
        remaining = row["baseline_count"] - row["resolved_count"]
        if remaining:
            expected_debt[(page_id, row["tag"], tuple(row["classes"]))] = remaining
    if actual_debt != expected_debt:
        errors.append(f"{page_id}: unowned debt drifted")
    return errors


def _resolve_emitter(spec: str):  # noqa: ANN202 - callable shapes intentionally vary
    match = re.fullmatch(r"(?P<path>[\w/]+\.py)::(?P<name>[A-Za-z_]\w*)", spec)
    if not match:
        raise ValueError(f"invalid emitter {spec!r}")
    path = Path(match.group("path"))
    if path.is_absolute() or ".." in path.parts or not (ROOT / path).is_file():
        raise ValueError(f"invalid emitter path {path}")
    module = importlib.import_module(".".join(path.with_suffix("").parts))
    return module, match.group("name"), getattr(module, match.group("name")), path


def _minting_functions(source: str, literal: str) -> set[str]:
    """Functions whose own AST contains the marker literal; comments do not count."""
    found: set[str] = set()
    stack: list[str] = []

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node):  # noqa: ANN001 - AST callback
            stack.append(node.name)
            self.generic_visit(node)
            stack.pop()

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Constant(self, node):  # noqa: ANN001 - AST callback
            if isinstance(node.value, str) and literal in node.value:
                found.add(stack[-1] if stack else "<module>")

    Visitor().visit(ast.parse(source))
    return found


def _replace_code_literal(code: types.CodeType, needle: str, replacement: str) -> tuple[types.CodeType, bool]:
    """Replace only string constants compiled inside one function (including nested code)."""
    changed = False
    constants = []
    for value in code.co_consts:
        if isinstance(value, str) and needle in value:
            constants.append(value.replace(needle, replacement))
            changed = True
        elif isinstance(value, types.CodeType):
            nested, nested_changed = _replace_code_literal(value, needle, replacement)
            constants.append(nested)
            changed = changed or nested_changed
        else:
            constants.append(value)
    return code.replace(co_consts=tuple(constants)), changed


def _mutated_emitter(emitter, owner: str, sentinel: str):  # noqa: ANN001, ANN202
    """Mutate the declared mint site, never post-process markup returned by callees."""
    needle = f'{MARKER}="{owner}"'
    replacement = f'{MARKER}="{sentinel}"'
    code, changed = _replace_code_literal(emitter.__code__, needle, replacement)
    if not changed:
        raise AssertionError(f"{owner}: declared emitter contains no compiled marker literal")
    mutated = types.FunctionType(code, emitter.__globals__, emitter.__name__,
                                 emitter.__defaults__, emitter.__closure__)
    mutated.__kwdefaults__ = emitter.__kwdefaults__
    mutated.__annotations__ = emitter.__annotations__
    return wraps(emitter)(mutated)


def _replace_rendered_marker(rendered, needle: str, replacement: str):  # noqa: ANN001, ANN202
    if isinstance(rendered, str):
        return rendered.replace(needle, replacement)
    if isinstance(rendered, tuple):
        return tuple(_replace_rendered_marker(value, needle, replacement) for value in rendered)
    if isinstance(rendered, list):
        return [_replace_rendered_marker(value, needle, replacement) for value in rendered]
    if isinstance(rendered, dict):
        return {key: _replace_rendered_marker(value, needle, replacement)
                for key, value in rendered.items()}
    return rendered


def _direct_owner_signatures(rendered, owner: str) -> Counter:  # noqa: ANN001
    signatures: Counter = Counter()
    values = rendered.values() if isinstance(rendered, dict) else rendered
    if isinstance(rendered, str):
        values = (rendered,)
    elif not isinstance(rendered, (dict, list, tuple)):
        values = ()
    for value in values:
        if isinstance(value, str):
            parser = _ClassParser()
            parser.feed(value)
            signatures.update((element.tag, element.classes) for element in parser.elements
                              if element.owner == owner)
        else:
            signatures.update(_direct_owner_signatures(value, owner))
    return signatures


def _record_direct_emissions(emitter, sentinel: str, records: list[tuple[str, Counter]]):  # noqa: ANN001, ANN202
    """Give every direct invocation a nonce and record its exact owned DOM signatures."""
    @wraps(emitter)
    def recording(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202 - transparent test probe
        rendered = emitter(*args, **kwargs)
        invocation = f"{sentinel}-call-{len(records)}"
        instrumented = _replace_rendered_marker(
            rendered, f'{MARKER}="{sentinel}"', f'{MARKER}="{invocation}"')
        signatures = _direct_owner_signatures(instrumented, invocation)
        records.append((invocation, signatures))
        return instrumented

    return recording


@unittest.skipUnless(CONTRACT_PATH.is_file(), "W2 RED: DOM cover contract has not landed")
class DomCoverContract(unittest.TestCase):
    def test_contract_schema_manifest_cover_and_non_vacuous_ratchet(self):
        contract, manifest = _contract(), _manifest()
        self.assertEqual([], _contract_errors(contract, manifest))
        index_debt = contract["pages"]["index"]["debt"]
        self.assertEqual(INDEX_BASELINE_SHA256, _baseline_hash(index_debt))
        self.assertEqual(INDEX_BASELINE_SHA256, contract["pages"]["index"]["debt_baseline_sha256"])

    def test_committed_pages_equal_manifest_render_and_close_every_static_class_element(self):
        from scripts.contracts.page_manifest import render_manifest_page
        contract = _contract()
        for page in _manifest()["pages"]:
            committed = (ROOT / page["route"]).read_text(encoding="utf-8")
            self.assertEqual(committed, render_manifest_page(page, ROOT), f"{page['id']}: render drift")
            self.assertEqual([], _document_errors(page["id"], committed, contract), page["id"])

    def test_owner_markers_bind_to_one_exercised_emitter_on_each_declared_page(self):
        from scripts.contracts.page_manifest import render_manifest_page
        contract = _contract()
        manifest = {page["id"]: page for page in _manifest()["pages"]}
        scripts = list((ROOT / "scripts").rglob("*.py"))
        for owner_id, owner in contract["owners"].items():
            module, name, emitter, path = _resolve_emitter(owner["emitter"])
            literal = f'{MARKER}="{owner_id}"'
            self.assertIn(literal, inspect.getsource(emitter), f"{owner_id}: marker not minted by emitter")
            mints = [
                (p.relative_to(ROOT).as_posix(), function)
                for p in scripts
                for function in _minting_functions(p.read_text(encoding="utf-8"), literal)
            ]
            self.assertEqual([(path.as_posix(), name)], mints,
                             f"{owner_id}: exact marker must be minted by one function only")
            for page_id in owner["pages"]:
                base = render_manifest_page(manifest[page_id], ROOT)
                expected = base.count(literal)
                self.assertGreater(expected, 0, f"{owner_id}: phantom page edge")
                sentinel = f"sentinel-{owner_id.replace('.', '-')}"
                mutated_emitter = _mutated_emitter(emitter, owner_id, sentinel)
                direct_records: list[tuple[str, Counter]] = []
                recording_emitter = _record_direct_emissions(mutated_emitter, sentinel, direct_records)
                with mock.patch.object(module, name, recording_emitter):
                    mutated = render_manifest_page(manifest[page_id], ROOT)
                self.assertEqual(0, mutated.count(literal),
                                 f"{owner_id}: undeclared pass-through mint or emitter not on render path")
                self.assertTrue(direct_records, f"{owner_id}: declared emitter was never invoked")
                parser = _ClassParser()
                parser.feed(mutated)
                final_count = 0
                for invocation, direct_signatures in direct_records:
                    self.assertTrue(direct_signatures,
                                    f"{owner_id}: invocation emitted no directly owned DOM")
                    final_signatures = Counter(
                        (element.tag, element.classes) for element in parser.elements
                        if element.owner == invocation)
                    self.assertIn(final_signatures, (Counter(), direct_signatures),
                                  f"{owner_id}: caller copied, discarded part of, or rewrote direct DOM")
                    final_count += sum(final_signatures.values())
                self.assertEqual(expected, final_count,
                                 f"{owner_id}: direct invocation reconciliation missed shipped DOM")
                for other in set(contract["owners"]) - {owner_id}:
                    marker = f'{MARKER}="{other}"'
                    self.assertEqual(base.count(marker), mutated.count(marker),
                                     f"{owner_id}: sentinel mutation touched unrelated owner {other}")

    def test_every_runtime_producer_is_manifest_closed_and_class_mutations_are_pinned(self):
        from scripts.pipeline.web_render import _script
        from scripts.rendering.studio.studio import _STUDIO_JS

        coverage = _contract()["coverage"]
        expected_by_page: dict[str, Counter] = {page["id"]: Counter() for page in _manifest()["pages"]}
        for producer in coverage["runtime_producers"]:
            for page in producer["pages"]:
                expected_by_page[page][producer["script_sha256"]] += 1
        for page in _manifest()["pages"]:
            parsed = _parse_scripts((ROOT / page["route"]).read_text(encoding="utf-8"))
            self.assertEqual([], parsed.inline_handlers, f"{page['id']}: undeclared inline handler")
            self.assertEqual([], parsed.external_scripts, f"{page['id']}: undeclared external script")
            self.assertEqual([], parsed.active_surfaces,
                             f"{page['id']}: undeclared active embedding surface")
            actual = Counter(hashlib.sha256(script.encode()).hexdigest() for script in parsed.scripts)
            self.assertEqual(expected_by_page[page["id"]], actual,
                             f"{page['id']}: executable script roster/hash drifted")

        runtime = coverage["runtime_class_debt"]["index-hydration"]
        script = _script()
        digest = hashlib.sha256(script.encode()).hexdigest()
        self.assertEqual(INDEX_HYDRATION_SCRIPT_SHA256, digest)
        self.assertEqual(INDEX_HYDRATION_SCRIPT_SHA256, runtime["source_sha256"])
        templates = re.findall(r'class="([^"]+)"', script)
        literal_tokens = {token for value in templates for token in value.split()
                          if not token.startswith("${")}
        dynamic_tokens = {token for values in runtime["dynamic_axes"].values() for token in values}
        self.assertEqual(set(runtime["class_tokens"]), literal_tokens | dynamic_tokens)
        self.assertEqual({"${state}"}, {token for value in templates for token in value.split()
                                        if token.startswith("${")})

        studio = coverage["runtime_class_debt"]["studio-toggle"]
        self.assertEqual(studio["source_sha256"], hashlib.sha256(_STUDIO_JS.encode()).hexdigest())
        class_mutations = set(re.findall(
            r"classList\.(?:add|remove|toggle)\(['\"]([^'\"]+)['\"]", _STUDIO_JS))
        self.assertEqual(set(studio["class_tokens"]), class_mutations)
        self.assertEqual({}, studio["dynamic_axes"])
        self.assertNotRegex(_STUDIO_JS, r"insertAdjacentHTML|outerHTML|document\.write")

        data_only = next(row for row in coverage["runtime_producers"]
                         if row["id"] == "studio-space-data")
        studio_page = _parse_scripts((ROOT / "site/studio.html").read_text(encoding="utf-8"))
        data_script = next(script for script in studio_page.scripts
                           if hashlib.sha256(script.encode()).hexdigest() == data_only["script_sha256"])
        self.assertTrue(data_script.startswith("window.STUDIO_SPACE = ["))
        self.assertNotRegex(data_script, r"document\.|classList|innerHTML|insertAdjacentHTML")

    def test_negative_mutations_redden_the_cover_and_ratchet(self):
        contract, manifest = _contract(), _manifest()
        index = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        settings = (ROOT / "site" / "settings.html").read_text(encoding="utf-8")
        self.assertTrue(_document_errors("index", index.replace("</main>",
                                                                  '<div class="rogue"></div></main>'), contract))
        self.assertTrue(_document_errors("settings", settings.replace(
            '<h1 class="ps-title" data-dom-owner="pageshell">',
            '<div class="ps-title" data-dom-owner="pageshell">', 1), contract))
        self.assertTrue(_document_errors("settings", settings.replace(
            'data-dom-owner="page.settings"', 'data-dom-owner="page.studio"', 1), contract))
        self.assertTrue(_document_errors("index", index.replace(
            '<div class="bento">', '<div class="bento"><div class="bento"></div>', 1), contract))

        malformed = deepcopy(contract)
        malformed["pages"]["index"]["debt"][0]["invented"] = True
        self.assertTrue(_contract_errors(malformed, manifest))
        malformed = deepcopy(contract)
        malformed["pages"]["index"]["debt"][0]["resolved_count"] = 2
        self.assertTrue(_contract_errors(malformed, manifest))
        malformed = deepcopy(contract)
        malformed["pages"]["index"]["debt"].append(deepcopy(
            malformed["pages"]["index"]["debt"][0]))
        self.assertTrue(_contract_errors(malformed, manifest))
        malformed = deepcopy(contract)
        first = malformed["pages"]["index"]["debt"][0]
        first["baseline_count"] += 1
        first["resolved_count"] += 1
        malformed["pages"]["index"]["debt_baseline_sha256"] = _baseline_hash(
            malformed["pages"]["index"]["debt"])
        self.assertTrue(_contract_errors(malformed, manifest), "independent pin must catch self-consistent rewrite")
        malformed = deepcopy(contract)
        malformed["owners"]["page.dashboard"] = deepcopy(malformed["owners"]["page.settings"])
        malformed["owners"]["page.dashboard"]["emitter"] = (
            "scripts/pipeline/web_render.py::render_dashboard")
        self.assertTrue(_contract_errors(malformed, manifest),
                        "an alias owner around the top-level index renderer must remain forbidden")

        malformed = deepcopy(contract)
        malformed["coverage"]["runtime_producers"].append(deepcopy(
            malformed["coverage"]["runtime_producers"][0]))
        self.assertTrue(_contract_errors(malformed, manifest),
                        "an undeclared/duplicate runtime producer must break the independent roster")

        literal = f'{MARKER}="pageshell"'
        synthetic = (
            "def helper():\n"
            f"    return '<div {literal}></div>'\n"
            "def declared():\n"
            f"    dead = '{literal}'\n"
            "    return helper()\n"
        )
        self.assertEqual({"declared", "helper"}, _minting_functions(synthetic, literal),
                         "same-module helper forgery must be visible at function scope")
        namespace: dict = {}
        exec(synthetic, namespace)  # noqa: S102 - crafted mutation function, no external input
        mutated = _mutated_emitter(namespace["declared"], "pageshell", "sentinel-pageshell")
        self.assertIn(literal, mutated(),
                      "mint-site mutation must leave passed-through helper markup unchanged so lineage reds")

        child_owner = "sentinel-webkit-nav"

        def child():
            return f'<nav class="nav" {MARKER}="{child_owner}"></nav>'

        direct_records: list[tuple[str, Counter]] = []
        recording_child = _record_direct_emissions(child, child_owner, direct_records)
        child_html = recording_child()
        copied_attribute = re.search(r'data-dom-owner="[^"]+"', child_html).group(0)
        forged_page = child_html + f'<div class="debt" {copied_attribute}></div>'
        invocation, direct_signatures = direct_records[0]
        parser = _ClassParser()
        parser.feed(forged_page)
        final_signatures = Counter((element.tag, element.classes) for element in parser.elements
                                   if element.owner == invocation)
        self.assertNotEqual(direct_signatures, final_signatures,
                            "copying a legitimate return marker in a caller must red exact lineage")

        settings_with_script = settings.replace(
            "</body>", '<script>insertAdjacentHTML("beforeend", "<b class=\\"rogue\\">")</script></body>')
        original_scripts = _parse_scripts(settings)
        mutated_scripts = _parse_scripts(settings_with_script)
        self.assertNotEqual(
            Counter(hashlib.sha256(x.encode()).hexdigest() for x in original_scripts.scripts),
            Counter(hashlib.sha256(x.encode()).hexdigest() for x in mutated_scripts.scripts),
            "a new inline DOM producer must change the closed runtime script multiset",
        )

        srcdoc_payload = (
            "&lt;script&gt;parent.document.body.insertAdjacentHTML(&quot;beforeend&quot;,&quot;"
            "&lt;div class=rogue&gt;&quot;)&lt;/script&gt;"
        )
        srcdoc_attack = settings.replace(
            "</body>", f'<iframe srcdoc="{srcdoc_payload}"></iframe></body>')
        attack = _parse_scripts(srcdoc_attack)
        self.assertIn(("iframe", "active embedding tag"), attack.active_surfaces)
        self.assertIn(("iframe", "srcdoc"), attack.active_surfaces)
        self.assertEqual(
            Counter(hashlib.sha256(x.encode()).hexdigest() for x in original_scripts.scripts),
            Counter(hashlib.sha256(x.encode()).hexdigest() for x in attack.scripts),
            "the srcdoc attack proves why the script multiset alone is insufficient",
        )
        active_mutations = {
            "object": '<object data="payload.html"></object>',
            "embed": '<embed src="payload.html">',
            "executable-url": '<a href="javascript:document.body.append(1)">run</a>',
            "obfuscated-executable-url": '<a href="java&#10;script:document.body.append(1)">run</a>',
            "meta-refresh": '<meta http-equiv="refresh" content="0;url=payload.html">',
            "svg-script-ref": '<svg><script href="payload.js"></script></svg>',
            "self-closing-handler": '<svg><path onload="document.body.append(1)" /></svg>',
            "svg-smil-class": '<svg><set attributeName="class" to="rogue" /></svg>',
        }
        for label, payload in active_mutations.items():
            with self.subTest(active_surface=label):
                parsed = _parse_scripts(settings.replace("</body>", f"{payload}</body>"))
                self.assertTrue(parsed.active_surfaces or parsed.external_scripts or parsed.inline_handlers)


class DomCoverRedPresence(unittest.TestCase):
    def test_closed_world_dom_contract_exists(self):
        self.assertTrue(
            CONTRACT_PATH.is_file(),
            "W2 RED: contracts/dom_cover.json is absent, so shipped class-bearing DOM has no closed cover",
        )


if __name__ == "__main__":
    unittest.main()

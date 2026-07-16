"""W6-C — the universal engine's CAPTURE pipeline (authority: reference intake).

The engine restyles a REAL reference page, so it must first CAPTURE that page honestly:
acquire (live evidence) -> localize (freeze external refs into content-addressed local
bytes, STRIP scripts, record every fetch gap) -> freeze (deterministic content-addressed
tree) -> serve the FROZEN copy for measurement. Three boundaries make the capture safe:

  * the CAPTURE ladder itself is deterministic and gap-honest (never silently drops a
    resource) — exercised end-to-end against a self-contained file:// fixture, NO network;
  * the URL SECURITY boundary refuses to point the fetcher at private/loopback hosts (SSRF),
    non-public schemes, or a robots-disallowed path, and refuses redirects into them;
  * the RESTORE boundary (BACKUP-BEFORE-TRANSFORM) refuses to run a transform without a
    committed snapshot of the target's CURRENT bytes, and round-trips a revert.

RED-first. The file:// fixture path needs no network and no Chrome; the live `acquire`
rung and any real-network rung FAIL HONESTLY (skipped when the dependency is absent).
Ported in spirit from the Chrome-subprocess receipt producer; candidate_only, decides
no authority.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
import urllib.request
from pathlib import Path


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "capture_site"
FIXTURE_INDEX = FIXTURE / "index.html"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(*args: str, cwd: Path) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=True
    )
    return proc.stdout.strip()


def _git_available() -> bool:
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


# --------------------------------------------------------------------------------------
# CAPTURE ladder — localize / freeze / serve_frozen (network-free, deterministic)
# --------------------------------------------------------------------------------------
class LocalizeLadderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="w6c-localize-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.staging = self.tmp / "staging"
        self.dom = FIXTURE_INDEX.read_bytes()
        self.base_url = FIXTURE_INDEX.as_uri()

    def _localize(self):
        from scripts.quality.reference_intake import capture
        return capture.localize(self.dom, self.staging, base_url=self.base_url)

    def test_refs_rewritten_to_content_addressed_local_paths(self):
        result = self._localize()
        html = (self.staging / "index.html").read_text(encoding="utf-8")
        # the external refs are gone; the content-addressed local ones are present
        self.assertNotIn("styles.css", html, "stylesheet ref was not localized")
        self.assertNotIn('src="logo.svg"', html, "image ref was not localized")
        self.assertIn("assets/", html, "no content-addressed local ref emitted")
        # every localized asset file exists on disk, named by the sha256 of its bytes
        self.assertTrue(result.assets, "no assets were localized")
        for asset in result.assets:
            path = self.staging / asset.path
            self.assertTrue(path.is_file(), f"missing localized asset {asset.path}")
            self.assertEqual(asset.custody_id, _sha256(path.read_bytes()),
                             "custody_id is not the sha256 of the stored bytes")
            self.assertIn(asset.custody_id, path.name, "path is not content-addressed")

    def test_css_import_and_url_refs_are_localized_too(self):
        self._localize()
        css_files = list((self.staging / "assets").glob("*.css"))
        self.assertTrue(css_files, "no stylesheet was localized")
        blob = "\n".join(p.read_text(encoding="utf-8") for p in css_files)
        self.assertNotIn("theme.css", blob, "@import ref inside CSS was not localized")
        self.assertNotIn("dot.svg", blob, "url() ref inside CSS was not localized")

    def test_scripts_are_stripped_and_policy_recorded(self):
        result = self._localize()
        html = (self.staging / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("<script", html.lower(), "a <script> survived localization")
        self.assertNotIn("must be stripped", html, "inline script body survived")
        self.assertEqual(result.script_policy.get("action"), "stripped")
        self.assertGreaterEqual(result.script_policy.get("removed", 0), 2)

    def test_missing_asset_becomes_a_nonfatal_gap(self):
        result = self._localize()  # must NOT raise despite missing.png
        reasons = {g.url: g for g in result.gaps}
        hit = [u for u in reasons if u.endswith("missing.png")]
        self.assertTrue(hit, f"missing.png did not produce a capture gap: {list(reasons)}")
        gap = reasons[hit[0]]
        self.assertTrue(gap.reason, "gap has no reason recorded")
        self.assertEqual(gap.stage, "localize")


class FreezeDeterminismTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="w6c-freeze-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        from scripts.quality.reference_intake import capture
        self.capture = capture
        self.staging = self.tmp / "staging"
        capture.localize(FIXTURE_INDEX.read_bytes(), self.staging, base_url=FIXTURE_INDEX.as_uri())

    def test_two_freezes_are_byte_identical(self):
        packa = self.capture.freeze(self.staging, self.tmp / "packA")
        packb = self.capture.freeze(self.staging, self.tmp / "packB")
        self.assertEqual(packa.source_tree_sha256, packb.source_tree_sha256)
        files_a = sorted(p for p in packa.pack_dir.rglob("*") if p.is_file())
        files_b = sorted(p for p in packb.pack_dir.rglob("*") if p.is_file())
        self.assertEqual([p.relative_to(packa.pack_dir).as_posix() for p in files_a],
                         [p.relative_to(packb.pack_dir).as_posix() for p in files_b])
        for a, b in zip(files_a, files_b):
            self.assertEqual(a.read_bytes(), b.read_bytes(), f"freeze not deterministic at {a.name}")

    def test_source_tree_sha256_is_pinned_to_content(self):
        pack = self.capture.freeze(self.staging, self.tmp / "pack")
        self.assertEqual(len(pack.source_tree_sha256), 64)
        # mutate a frozen byte -> a re-freeze of the MUTATED tree must differ
        (self.staging / "index.html").write_bytes(b"<!doctype html><html></html>")
        mutated = self.capture.freeze(self.staging, self.tmp / "pack2")
        self.assertNotEqual(pack.source_tree_sha256, mutated.source_tree_sha256)


class ServeFrozenTests(unittest.TestCase):
    def test_serve_frozen_serves_the_frozen_tree_on_loopback(self):
        from scripts.quality.reference_intake import capture
        tmp = Path(tempfile.mkdtemp(prefix="w6c-serve-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        staging = tmp / "staging"
        capture.localize(FIXTURE_INDEX.read_bytes(), staging, base_url=FIXTURE_INDEX.as_uri())
        pack = capture.freeze(staging, tmp / "pack")
        with capture.serve_frozen(pack.pack_dir) as server:
            self.assertIn("127.0.0.1", server.base_url)
            with urllib.request.urlopen(server.base_url + "index.html", timeout=5) as resp:
                self.assertEqual(resp.status, 200)
                body = resp.read().decode("utf-8")
            self.assertIn("Frozen Capture Fixture", body)
            self.assertIn("assets/", body)
            # a content-addressed asset the page references is actually served
            asset = next(p for p in pack.pack_dir.rglob("*") if p.suffix == ".svg")
            rel = asset.relative_to(pack.pack_dir).as_posix()
            with urllib.request.urlopen(server.base_url + rel, timeout=5) as resp:
                self.assertEqual(resp.status, 200)


class CandidateRecordShapeTests(unittest.TestCase):
    def test_record_has_the_reference_candidate_shape(self):
        from scripts.quality.reference_intake import capture
        tmp = Path(tempfile.mkdtemp(prefix="w6c-record-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        staging = tmp / "staging"
        result = capture.localize(FIXTURE_INDEX.read_bytes(), staging, base_url=FIXTURE_INDEX.as_uri())
        pack = capture.freeze(staging, tmp / "pack")
        record = capture.build_candidate_record(
            origin=FIXTURE_INDEX.as_uri(),
            source_url=FIXTURE_INDEX.as_uri(),
            localize_result=result,
            staging_tree_sha256=pack.source_tree_sha256,
            robots={"checked": False, "allowed": True, "override": False},
        )
        for key in ("origin", "producer", "source", "rights", "capture", "status"):
            self.assertIn(key, record, f"record missing {key}")
        self.assertEqual(set(record["producer"]), {"tool", "version", "command"})
        self.assertEqual(set(record["source"]), {"url", "fetched_at", "robots"})
        self.assertTrue(record["rights"], "no per-resource rights rows")
        for row in record["rights"]:
            self.assertEqual(set(row), {"publication", "custody_id", "redistribution", "retention"})
        cap = record["capture"]
        self.assertEqual(set(cap), {"live_evidence", "staging_tree_sha256", "gaps"})
        self.assertEqual(cap["staging_tree_sha256"], pack.source_tree_sha256)
        self.assertTrue(cap["gaps"], "missing.png gap must survive into the record")
        # the record is honest: candidate-only, decides no authority
        self.assertEqual(record["status"], "candidate_only")


# --------------------------------------------------------------------------------------
# URL SECURITY boundary — assert_capture_allowed (SSRF / scheme / robots / redirect)
# --------------------------------------------------------------------------------------
def _public_resolver(_host: str):
    """A resolver that pretends every name is a public IP — keeps the shape check off-network."""
    return ["93.184.216.34"]


class SecurityBoundaryTests(unittest.TestCase):
    def _refused(self, url: str, **kw):
        from scripts.quality.reference_intake import security
        with self.assertRaises(security.CaptureRefused):
            security.assert_capture_allowed(url, **kw)

    def test_denies_loopback_ip(self):
        self._refused("http://127.0.0.1/")

    def test_denies_private_ip(self):
        self._refused("http://10.0.0.1/")

    def test_denies_link_local_ip(self):
        self._refused("http://169.254.169.254/")

    def test_denies_ipv6_loopback(self):
        self._refused("http://[::1]/")

    def test_denies_localhost_hostname(self):
        self._refused("http://localhost/")

    def test_denies_non_http_scheme(self):
        self._refused("file:///etc/passwd")

    def test_denies_embedded_credentials(self):
        self._refused("http://user:pass@example.com/")

    def test_denies_redirect_into_private_host(self):
        # the initial host is public, but a redirect hop lands on a private address
        self._refused(
            "http://example.com/",
            resolver=_public_resolver,
            robots_txt="",
            redirect_chain=["http://10.0.0.1/internal"],
        )

    def test_public_url_passes_shape_check_without_network(self):
        from scripts.quality.reference_intake import security
        allowance = security.assert_capture_allowed(
            "https://example.com/page",
            resolver=_public_resolver,   # no real DNS
            robots_txt="",               # empty robots = allow all, no real fetch
        )
        self.assertTrue(allowance.allowed)
        self.assertFalse(allowance.robots.get("override", False))

    def test_robots_disallow_is_refused_but_override_is_recorded(self):
        from scripts.quality.reference_intake import security
        robots = "User-agent: *\nDisallow: /\n"
        self._refused("https://example.com/page", resolver=_public_resolver, robots_txt=robots)
        allowance = security.assert_capture_allowed(
            "https://example.com/page", resolver=_public_resolver, robots_txt=robots, override=True
        )
        self.assertTrue(allowance.robots.get("override"))

    def test_response_limits_are_enforced(self):
        from scripts.quality.reference_intake import security
        limits = security.CaptureLimits(max_bytes=1024, timeout_s=5)
        with self.assertRaises(security.CaptureRefused):
            security.check_response(content_type="text/html", content_length=2048, limits=limits)
        with self.assertRaises(security.CaptureRefused):
            security.check_response(content_type="application/octet-stream", content_length=10,
                                    limits=limits)
        # a small text/html body inside the caps is fine
        security.check_response(content_type="text/html; charset=utf-8", content_length=10,
                                limits=limits)


# --------------------------------------------------------------------------------------
# RESTORE boundary — BACKUP-BEFORE-TRANSFORM (fail-closed without a committed snapshot)
# --------------------------------------------------------------------------------------
@unittest.skipUnless(_git_available(), "git is required for the restore-point round trip")
class RestoreBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Path(tempfile.mkdtemp(prefix="w6c-restore-"))
        self.addCleanup(shutil.rmtree, self.repo, ignore_errors=True)
        _git("init", "-q", cwd=self.repo)
        _git("config", "user.email", "w6c@example.com", cwd=self.repo)
        _git("config", "user.name", "w6c", cwd=self.repo)
        self.target = self.repo / "page.html"
        self.target.write_text("<h1>ORIGINAL</h1>\n", encoding="utf-8")
        _git("add", "-A", cwd=self.repo)
        _git("commit", "-q", "-m", "seed", cwd=self.repo)

    def test_transform_without_snapshot_refuses(self):
        from scripts.quality.reference_intake import restore
        ran = {"did": False}

        def _transform():
            ran["did"] = True

        with self.assertRaises(restore.SnapshotRequired):
            restore.guarded_transform(None, _transform)
        self.assertFalse(ran["did"], "the transform ran without a committed snapshot")

    def test_snapshot_then_restore_round_trips(self):
        from scripts.quality.reference_intake import restore
        point = restore.snapshot_target(self.repo)
        self.assertTrue(point.committed, "snapshot did not commit a hash-pinned restore point")
        self.assertTrue(restore.is_committed(point))

        # a guarded transform runs now that a committed snapshot exists, and mutates the target
        def _restyle():
            self.target.write_text("<h1>RESTYLED</h1>\n", encoding="utf-8")

        restore.guarded_transform(point, _restyle)
        self.assertIn("RESTYLED", self.target.read_text(encoding="utf-8"))

        # BACKUP-BEFORE-TRANSFORM pays off: restore reverts to the captured bytes
        restore.restore(point)
        self.assertEqual("<h1>ORIGINAL</h1>\n", self.target.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------------------
# ACQUIRE rung — live evidence via Chrome (skipped honestly when Chrome is absent)
# --------------------------------------------------------------------------------------
class AcquireLadderTests(unittest.TestCase):
    def test_acquire_captures_live_evidence_or_fails_honestly(self):
        from scripts.quality.reference_intake import capture
        if not capture.chrome_available():
            self.skipTest("Chrome is unavailable — the live acquire rung fails honestly")
        tmp = Path(tempfile.mkdtemp(prefix="w6c-acquire-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        evidence = capture.acquire(FIXTURE_INDEX.as_uri(), viewports=(1280,), out_dir=tmp)
        self.assertIn("Frozen Capture Fixture", evidence.dom)
        self.assertTrue(evidence.screenshots, "no screenshot evidence captured")
        for shot in evidence.screenshots:
            self.assertTrue(Path(shot["path"]).is_file())
            self.assertGreater(shot["bytes"], 0)


if __name__ == "__main__":
    unittest.main()

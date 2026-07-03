"""P5-BOARD B-1 (authority: motion) — motion is DATA like colour (docs/design/motion.md).

Per-language duration/easing tokens with provenance (THEME_IA motion block → emitted
`--motion-*`/`--ease-*` vars), a band law ([70ms, 700ms], the Carbon envelope §1.1), and a
token-only law for page CSS: a literal duration in a transition/animation outside the token
emission and the DECLARED exceptions list reddens — the motion twin of the no-hex guard.
candidate_only.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


def _root() -> Path:
    for p in Path(__file__).resolve().parents:
        if (p / "contracts" / "design_profiles").is_dir():
            return p
    raise RuntimeError("repo root not found")


ROOT = _root()
_MOTION_KEYS = ("fast", "base", "slow", "ease-standard", "ease-enter", "ease-exit")


class MotionTokensContract(unittest.TestCase):
    def test_every_active_theme_declares_a_cited_motion_block(self):
        """THEME_IA carries motion {fast, base, slow, ease-standard, ease-enter, ease-exit} per
        theme; durations sit in the [70, 700]ms band (motion.md §2)."""
        from scripts.rendering import design_tokens as dt
        for name in dt.THEMES:
            m = dt.THEME_IA[name].get("motion")
            self.assertIsInstance(m, dict, f"{name}: THEME_IA must declare a motion block")
            self.assertEqual(set(m), set(_MOTION_KEYS), f"{name}: the motion key set is CLOSED")
            for k in ("fast", "base", "slow"):
                self.assertTrue(70 <= m[k] <= 700, f"{name}: motion-{k}={m[k]}ms outside [70,700]")
            self.assertTrue(m["fast"] < m["base"] < m["slow"], f"{name}: durations must be ordered")

    def test_emitted_motion_vars_have_provenance(self):
        """emit_css_root emits --motion-*/--ease-* EQUAL to the theme's declared block — the same
        provenance law as every colour/radius var."""
        from scripts.rendering import design_tokens as dt
        css = dt.emit_css_root()
        for name in dt.THEMES:
            m = dt.THEME_IA[name]["motion"]
            block = re.search(
                rf'\[data-theme="{name}"\]\s*{{([^}}]*)}}' if name != dt.DEFAULT_THEME
                else r":root\s*{([^}]*)}", css)
            self.assertIsNotNone(block, f"{name}: token block missing")
            body = block.group(1)
            for k in ("fast", "base", "slow"):
                self.assertIn(f"--motion-{k}: {m[k]}ms", body, f"{name}: --motion-{k} provenance")
            for k in ("standard", "enter", "exit"):
                self.assertIn(f"--ease-{k}: {m['ease-' + k]}", body, f"{name}: --ease-{k} provenance")

    def test_page_motion_is_token_only_beyond_declared_exceptions(self):
        """The motion twin of the no-hex guard: strip the token emission, then every transition/
        animation declaration in the committed index references var(--motion-*)/var(--ease-*) —
        a literal duration reddens. DECLARED exceptions (motion.md §4): the 2.4s liveness pulse."""
        from scripts.rendering import design_tokens as dt
        html = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        html = html.replace(dt.emit_css_root().strip(), "")
        html = re.sub(r"@keyframes pulse[^}]*}(\s*})?", "", html)          # declared §4 exception
        html = re.sub(r"animation:\s*pulse[^;}]*[;}]", "", html)           # its consumer
        offenders = [d for d in re.findall(r"(?:transition|animation)[^;}]*[;}]", html)
                     if re.search(r"\d+\.?\d*m?s", d) and "var(--motion-" not in d]
        self.assertEqual(offenders, [], f"literal motion durations must be tokens: {offenders}")

    def test_render_nav_insertion_contexts_define_consumed_motion_vars(self):
        """`render_nav()` consumes --motion-fast/--ease-standard, so every committed page that embeds
        that nav CSS must define those vars in the same page context — not only site/index.html."""
        manifest = json.loads((ROOT / "contracts" / "page_manifest.json").read_text(encoding="utf-8"))
        required = ("--motion-fast", "--ease-standard")
        for page in manifest["pages"]:
            html = (ROOT / page["route"]).read_text(encoding="utf-8")
            if all(f"var({name})" not in html for name in required):
                continue
            for name in required:
                self.assertIn(f"{name}:", html, f"{page['id']}: render_nav consumes {name} but the page does not define it")

    def test_conform_emits_passing_motion_rows(self):
        from scripts.quality.design_invariants import conform
        from scripts.rendering.design import loader
        for name in loader.load("_index")["active_design_profiles"]:
            rows = [r for r in conform(name) if r["aspect"] == "motion"]
            self.assertEqual(len(rows), 1, f"{name}: one emitted motion invariant")
            self.assertEqual(rows[0]["status"], "pass", f"{name}: {rows[0]['invariant_id']}")


if __name__ == "__main__":
    unittest.main()

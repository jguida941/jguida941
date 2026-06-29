"""Red-first README PROJECTION contract — authority: GitHub-SVG / assembled render.

The per-card SVG contracts prove each image is syntactically GitHub-safe in
ISOLATION. They do NOT prove the *assembled* README renders as one aligned column.
This contract closes that gap on the projection layer (`templates/README.md.tpl`
and the generated `README.md`): every analytics card image must use ONE uniform
`<img>` sizing policy, so all cards render at the SAME width and their left/right
edges line up on the GitHub page.

Decided policy (documented in docs/DESIGN_SPEC.md): every analytics image uses
`width="100%"` — each card scales to the same Markdown column, so the intrinsic-840
SVGs all render at one uniform width regardless of viewport. Mixed sizing (the
historical leak: only metrics.general + streak_summary had width="100%") makes two
cards span the full column while the rest render at 840px — the visible offset.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

# The one sanctioned image-sizing policy for every analytics card image.
README_IMG_WIDTH_POLICY = 'width="100%"'
# Exact number of analytics cards in the README dashboard stack. Update this when a
# card is deliberately added/removed — so a silent drop can't slip the suite green.
ANALYTICS_CARD_COUNT = 12
# Analytics card images (the dashboard stack) — match ANY analytics asset, not just
# a fixed lowercase whitelist (a hyphen/digit/uppercase/new-metrics name must NOT
# escape the policed set).
_ANALYTICS_SRC = re.compile(r'src="(?:metrics\.[\w.-]+\.svg|assets/[\w./-]+\.svg)')
_IMG = re.compile(r"<img\b[^>]*>", re.S)
# Only these attributes are allowed on an analytics card image — a stray style=/
# height=/second width= can silently reintroduce the offset, so they're forbidden.
_ALLOWED_IMG_ATTRS = {"src", "width", "alt"}
# Real quoted attributes only (attr="...") — must NOT match the ?v=<cache-bust> query
# inside the src URL (which has no quote after '=').
_ATTR = re.compile(r'([a-zA-Z][\w-]*)="')


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "scripts").is_dir() and (parent / "templates").is_dir():
            return parent
    raise RuntimeError("repo root not found")


ROOT = _repo_root()


def _analytics_imgs(text: str) -> list[str]:
    return [tag for tag in _IMG.findall(text) if _ANALYTICS_SRC.search(tag)]


class ReadmeProjectionContract(unittest.TestCase):
    """Every analytics card image in the README projection uses one uniform width
    policy, so the assembled README renders as a single aligned column."""

    SOURCES = ("templates/README.md.tpl", "README.md")

    def _read(self, rel: str) -> str | None:
        p = ROOT / rel
        return p.read_text(encoding="utf-8") if p.is_file() else None

    def test_template_exists_with_full_card_stack(self):
        tpl = self._read("templates/README.md.tpl")
        self.assertIsNotNone(tpl, "templates/README.md.tpl must exist (projection law)")
        self.assertEqual(
            len(_analytics_imgs(tpl)), ANALYTICS_CARD_COUNT,
            f"template must place exactly {ANALYTICS_CARD_COUNT} analytics cards "
            "(a silent add/drop must update ANALYTICS_CARD_COUNT, not slip through)",
        )

    def test_uniform_img_width_policy(self):
        offenders: list[str] = []
        for rel in self.SOURCES:
            text = self._read(rel)
            if text is None:
                continue  # README.md is generated; absent in a clean checkout
            imgs = _analytics_imgs(text)
            self.assertEqual(len(imgs), ANALYTICS_CARD_COUNT, f"{rel}: expected {ANALYTICS_CARD_COUNT} analytics cards")
            for tag in imgs:
                src = re.search(r'src="([^"?]+)', tag)
                name = src.group(1) if src else tag[:60]
                # the policy must be present AND unconditional (no style=/height=/2nd width)
                if README_IMG_WIDTH_POLICY not in tag:
                    offenders.append(f"{rel}: {name} lacks {README_IMG_WIDTH_POLICY}")
                stray = {a.lower() for a in _ATTR.findall(tag)} - _ALLOWED_IMG_ATTRS
                if stray:
                    offenders.append(f"{rel}: {name} has disallowed attr(s) {sorted(stray)} (can override width)")
                if len(re.findall(r"\bwidth=", tag)) != 1:
                    offenders.append(f"{rel}: {name} must declare width exactly once")
        self.assertEqual(
            [],
            offenders,
            "every analytics card image must use one uniform, UNCONDITIONAL sizing policy "
            f"({README_IMG_WIDTH_POLICY}; no style=/height=/second width=) so the assembled "
            "README is one aligned column:\n  " + "\n  ".join(offenders),
        )

    def test_template_and_readme_agree(self):
        tpl = self._read("templates/README.md.tpl")
        readme = self._read("README.md")
        if tpl is None or readme is None:
            self.skipTest("README.md not generated in this checkout")
        tpl_pol = [README_IMG_WIDTH_POLICY in t for t in _analytics_imgs(tpl)]
        rm_pol = [README_IMG_WIDTH_POLICY in t for t in _analytics_imgs(readme)]
        self.assertEqual(tpl_pol, rm_pol, "generated README must apply the template's image-sizing policy verbatim")


if __name__ == "__main__":
    unittest.main()

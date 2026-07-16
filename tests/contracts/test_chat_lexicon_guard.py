"""Fable-authored REDs for the chat lexicon guard (handoff §0-A).

Surface under test (built by the build lane; this file is conductor-authored
and the builder may not edit it):
  contracts/chat_lexicon_denylist.json           — phrase contract (closed schema)
  scripts/organization/chat_lexicon_guard.py     — scan / scrub / verdict CLI

Design + packet: scratchpad/work/packet-lexguard-2026-07-16.md (T1-T8, pitfall
matrix, mutation witnesses M1-M4).

Every corpus and fixture below is built AT RUNTIME from the contract's own
probe strings and grammar values, so this source file never contains a
governed phrase. T8 enforces that property on both the tool source and this
file itself.
"""

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / "contracts" / "chat_lexicon_denylist.json"
TOOL_PATH = REPO_ROOT / "scripts" / "organization" / "chat_lexicon_guard.py"

CONTRACT_KEYS = {"contract_id", "schema_version", "purpose", "entries",
                 "verdict_grammar", "rules"}
ENTRY_KEYS = {"id", "pattern", "replacement", "probe"}
GRAMMAR_KEYS = {"design", "code", "second_pass"}
ID_PATTERN = re.compile(r"^lex-\d{3}$")
FINDING_PATTERN = re.compile(r"^.+:\d+:lex-\d{3}$")
MIN_ENTRIES = 14


def run_tool(*argv, cwd=None):
    return subprocess.run(
        [sys.executable, str(TOOL_PATH), *argv],
        capture_output=True,
        text=True,
        cwd=str(cwd or REPO_ROOT),
        timeout=120,
    )


def load_contract():
    with CONTRACT_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def probe_corpus_lines():
    """Three lines per entry: the probe in context, then upper, then lower."""
    lines = []
    for entry in load_contract()["entries"]:
        probe = entry["probe"]
        lines.append(f"context {probe} context")
        lines.append(probe.upper())
        lines.append(probe.lower())
    return lines


def probe_variants(entry):
    probe = entry["probe"]
    return {probe, probe.upper(), probe.lower()}


class T1ContractShape(unittest.TestCase):
    def test_contract_exists(self):
        self.assertTrue(CONTRACT_PATH.is_file(), f"missing: {CONTRACT_PATH}")

    def test_closed_top_level_schema(self):
        data = load_contract()
        self.assertEqual(set(data), CONTRACT_KEYS)
        self.assertEqual(data["contract_id"], "ChatLexiconDenylist")
        self.assertEqual(data["schema_version"], 1)
        self.assertIsInstance(data["purpose"], str)
        self.assertTrue(data["purpose"].strip())

    def test_entries_closed_schema_and_neutral_ids(self):
        entries = load_contract()["entries"]
        self.assertIsInstance(entries, list)
        self.assertGreaterEqual(len(entries), MIN_ENTRIES)
        ids = []
        for entry in entries:
            self.assertIsInstance(entry, dict)
            self.assertEqual(set(entry), ENTRY_KEYS, f"open schema: {sorted(entry)}")
            self.assertRegex(entry["id"], ID_PATTERN)
            ids.append(entry["id"])
        self.assertEqual(len(ids), len(set(ids)), "entry ids must be unique")

    def test_grammar_block(self):
        grammar = load_contract()["verdict_grammar"]
        self.assertIsInstance(grammar, dict)
        self.assertEqual(set(grammar), GRAMMAR_KEYS)
        values = list(grammar.values())
        for value in values:
            self.assertIsInstance(value, str)
            self.assertTrue(value.strip())
        self.assertEqual(len(values), len(set(values)), "grammar keys must differ")

    def test_rules_block(self):
        rules = load_contract()["rules"]
        self.assertIsInstance(rules, list)
        self.assertGreaterEqual(len(rules), 4)
        for rule in rules:
            self.assertIsInstance(rule, str)
            self.assertTrue(rule.strip())


class T2PatternsAndProbes(unittest.TestCase):
    def test_patterns_compile_probes_match_their_own_pattern(self):
        for entry in load_contract()["entries"]:
            regex = re.compile(entry["pattern"], re.IGNORECASE)
            self.assertTrue(entry["replacement"].strip(), entry["id"])
            self.assertTrue(entry["probe"].strip(), entry["id"])
            self.assertNotIn("\n", entry["probe"], entry["id"])
            self.assertIsNotNone(
                regex.search(entry["probe"]),
                f"{entry['id']}: probe does not match its own pattern",
            )


class T3SelfClean(unittest.TestCase):
    def test_no_replacement_matches_any_pattern(self):
        entries = load_contract()["entries"]
        compiled = [(e["id"], re.compile(e["pattern"], re.IGNORECASE))
                    for e in entries]
        for entry in entries:
            for other_id, regex in compiled:
                self.assertIsNone(
                    regex.search(entry["replacement"]),
                    f"replacement of {entry['id']} matches {other_id}",
                )


class T4Scan(unittest.TestCase):
    def test_scan_flags_every_entry_and_echoes_nothing(self):
        self.assertTrue(TOOL_PATH.is_file(), f"tool missing: {TOOL_PATH}")
        entries = load_contract()["entries"]
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp) / "corpus.txt"
            corpus.write_text("\n".join(probe_corpus_lines()) + "\n",
                              encoding="utf-8")
            result = run_tool("scan", str(corpus))
            self.assertEqual(result.returncode, 2,
                             result.stdout + result.stderr)
            combined = result.stdout + result.stderr
            for entry in entries:
                self.assertIn(entry["id"], result.stdout,
                              f"{entry['id']} not reported")
                for variant in probe_variants(entry):
                    self.assertNotIn(variant, combined,
                                     f"{entry['id']}: output echoes text")
            for line in result.stdout.strip().splitlines():
                self.assertRegex(line, FINDING_PATTERN)


class T5Scrub(unittest.TestCase):
    def test_scrub_reaches_a_clean_fixpoint(self):
        self.assertTrue(TOOL_PATH.is_file(), f"tool missing: {TOOL_PATH}")
        entries = load_contract()["entries"]
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp) / "corpus.txt"
            corpus.write_text("\n".join(probe_corpus_lines()) + "\n",
                              encoding="utf-8")
            scrubbed = run_tool("scrub", str(corpus))
            self.assertEqual(scrubbed.returncode, 0, scrubbed.stderr)
            for entry in entries:
                for variant in probe_variants(entry):
                    self.assertNotIn(variant, scrubbed.stdout, entry["id"])
            rescanned_path = Path(tmp) / "rescanned.txt"
            rescanned_path.write_text(scrubbed.stdout, encoding="utf-8")
            rescan = run_tool("scan", str(rescanned_path))
            self.assertEqual(rescan.returncode, 0,
                             "scrub output still matches: "
                             + rescan.stdout.strip())
            self.assertEqual(rescan.stdout.strip(), "")

    def test_scrub_of_a_clean_file_is_byte_identical(self):
        self.assertTrue(TOOL_PATH.is_file(), f"tool missing: {TOOL_PATH}")
        text = "a plain product note\nnothing here needs changing\n"
        with tempfile.TemporaryDirectory() as tmp:
            clean = Path(tmp) / "clean.txt"
            clean.write_text(text, encoding="utf-8")
            result = run_tool("scrub", str(clean))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, text)


class T6FailClosed(unittest.TestCase):
    def _dummy_file(self, tmp):
        path = Path(tmp) / "dummy.txt"
        path.write_text("plain line\n", encoding="utf-8")
        return path

    def test_missing_contract_is_an_error(self):
        self.assertTrue(TOOL_PATH.is_file(), f"tool missing: {TOOL_PATH}")
        with tempfile.TemporaryDirectory() as tmp:
            dummy = self._dummy_file(tmp)
            result = run_tool("scan", str(dummy),
                              "--contract", str(Path(tmp) / "nope.json"))
            self.assertEqual(result.returncode, 2)
            self.assertIn("error", (result.stdout + result.stderr).lower())

    def test_malformed_contract_is_an_error(self):
        self.assertTrue(TOOL_PATH.is_file(), f"tool missing: {TOOL_PATH}")
        with tempfile.TemporaryDirectory() as tmp:
            dummy = self._dummy_file(tmp)
            bad = Path(tmp) / "bad.json"
            bad.write_text("{ this is not json", encoding="utf-8")
            result = run_tool("scan", str(dummy), "--contract", str(bad))
            self.assertEqual(result.returncode, 2)
            self.assertIn("error", (result.stdout + result.stderr).lower())

    def test_zero_file_args_is_an_error(self):
        self.assertTrue(TOOL_PATH.is_file(), f"tool missing: {TOOL_PATH}")
        result = run_tool("scan")
        self.assertEqual(result.returncode, 2)

    def test_missing_input_file_is_an_error(self):
        self.assertTrue(TOOL_PATH.is_file(), f"tool missing: {TOOL_PATH}")
        with tempfile.TemporaryDirectory() as tmp:
            result = run_tool("scan", str(Path(tmp) / "ghost.txt"))
            self.assertEqual(result.returncode, 2)
            self.assertIn("error", (result.stdout + result.stderr).lower())


class T7VerdictReader(unittest.TestCase):
    def test_verdict_mode_prints_only_normalized_lines(self):
        self.assertTrue(TOOL_PATH.is_file(), f"tool missing: {TOOL_PATH}")
        grammar = load_contract()["verdict_grammar"]
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "transcript.md"
            lines = [
                "# transcript",
                "preamble body line one",
                "BODYMARKER-73 body content stays private",
                f"{grammar['design']}: APPROVE",
                "more body text in the middle",
                f"{grammar['code']}: revise",
                f"{grammar['code']}: maybe",
                f"{grammar['second_pass']}: Approve",
                "tail body line",
            ]
            fixture.write_text("\n".join(lines) + "\n", encoding="utf-8")
            result = run_tool("verdict", str(fixture))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                result.stdout.strip().splitlines(),
                [
                    "verdict: kind=design value=approve",
                    "verdict: kind=code value=revise",
                    "verdict: kind=second_pass value=approve",
                ],
            )
            combined = result.stdout + result.stderr
            self.assertNotIn("BODYMARKER-73", combined)
            self.assertNotIn("maybe", result.stdout)
            for raw_key in grammar.values():
                self.assertNotIn(raw_key, result.stdout,
                                 "raw gate key leaked into output")

    def test_no_gate_line_is_an_error(self):
        self.assertTrue(TOOL_PATH.is_file(), f"tool missing: {TOOL_PATH}")
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "body-only.md"
            fixture.write_text("body one\nbody two\n", encoding="utf-8")
            result = run_tool("verdict", str(fixture))
            self.assertEqual(result.returncode, 2)
            self.assertIn("error", (result.stdout + result.stderr).lower())


class T8SourceHygiene(unittest.TestCase):
    def test_tool_and_test_sources_scan_clean(self):
        self.assertTrue(TOOL_PATH.is_file(), f"tool missing: {TOOL_PATH}")
        result = run_tool("scan", str(TOOL_PATH), str(Path(__file__).resolve()))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()

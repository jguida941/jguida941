"""Proposed replacement for the existing public README projection test only."""
import unittest
from pathlib import Path
import re


def assert_projection(test, text):
    pictures = re.findall(r'<picture>(.*?)</picture>', text, re.S)
    test.assertEqual(len(pictures), 1)
    test.assertIn('media="(max-width: 767px)"', pictures[0])
    test.assertIn("assets/dashboard_summary_mobile.svg", pictures[0])
    main = re.findall(r'<img\b[^>]+>', pictures[0])
    test.assertEqual(len(main), 1)
    test.assertRegex(main[0], r'src="assets/dashboard_summary\.svg(?:\?[^\"]*)?"')
    test.assertIn('width="100%"', main[0])
    legacy = re.findall(r'<details>\s*<summary>Legacy visual detail</summary>(.*?)</details>', text, re.S)
    test.assertEqual(len(legacy), 1, "compatibility image must be in the existing closed legacy disclosure")
    compatibility = re.findall(r'<img\b[^>]+>', legacy[0])
    test.assertEqual(len(compatibility), 1)
    test.assertRegex(compatibility[0], r'src="assets/raw_snapshot\.svg(?:\?[^\"]*)?"')
    test.assertIn('width="100%"', compatibility[0])
    test.assertEqual(re.findall(r'<img\b[^>]+>', text), main + compatibility,
                     "only the headline picture and closed legacy snapshot image may be published")
    test.assertIn("Read the numbers and definitions", text)
    test.assertIn("#weekly-contributions", text)
    test.assertNotIn('<img src="metrics.general.svg', text)


class SharedProfileRendererContract(unittest.TestCase):
    """GitHub's static card and the live website share canonical facts."""

    def test_static_card_and_live_overview_share_the_snapshot_contract(self):
        from scripts.pipeline.web_render import render_dashboard
        page = render_dashboard()
        readme = (Path(__file__).resolve().parents[2] / "README.md").read_text()
        for filename in ("dashboard_summary.svg", "dashboard_summary_mobile.svg"):
            self.assertIn("assets/" + filename, readme)
        self.assertIn('<header class="panel hero" id="overview"', page)
        self.assertNotIn('id="interactive-details"', page)
        self.assertNotIn('class="canonical-profile"', page)
        for fact in ("profile.contributions", "inventory.public_total", "calendar.active_days"):
            self.assertIn(fact, page)
        self.assertIn('hydrateCITimeline(d.ci_timeline)', page)
        self.assertEqual(1, page.count('id="ci-observatory"'))
        self.assertNotIn('id="ci-execution"', page)

    def test_pages_deploy_copies_exact_github_profile_card_bytes(self):
        root = Path(__file__).resolve().parents[2]
        workflow = (root / ".github/workflows/deploy-site.yml").read_text()
        for name in ("dashboard_summary.svg", "dashboard_summary_mobile.svg"):
            self.assertIn("cp assets/" + name + " site/assets/" + name, workflow)
            self.assertIn("cmp assets/" + name + " site/assets/" + name, workflow)
        self.assertLess(workflow.index("cmp assets/dashboard_summary.svg site/assets/dashboard_summary.svg"),
                        workflow.index("uses: actions/upload-pages-artifact@v3"))

class ReadmeProjectionContract(unittest.TestCase):
    def test_one_responsive_picture_and_native_equivalent(self):
        root = Path(__file__).resolve().parents[2]
        for name in ("templates/README.md.tpl", "README.md"):
            assert_projection(self, (root / name).read_text())


class CodeChangeReadmeTests(unittest.TestCase):
    def test_code_text_has_full_branch_commit_and_daily_equivalent(self):
        from jinja2 import Environment
        from pathlib import Path
        from scripts.pipeline.activity_analytics import build_activity_analytics
        from tests.pipeline.test_compute_metrics_accuracy import CodeChangeAggregationTests, AccuracyTests
        from scripts.pipeline.compute_metrics import compute_profile_model
        model=compute_profile_model(AccuracyTests()._collected(),logger=lambda *_:None,allow_network_calls=False)
        model['dashboard_summary']['activity_analytics']=build_activity_analytics(CodeChangeAggregationTests.source())
        template=Path('templates/README.md.tpl').read_text()
        rendered=Environment().from_string(template).render(dashboard_summary=model['dashboard_summary'],legacy_visuals=[])
        self.assertIn('Current Focus',rendered)
        self.assertIn('refs/heads/dev/feature',rendered)
        self.assertIn('https://github.com/owner/project/commit/'+'a'*40,rendered)
        self.assertIn('| 2026-10-10 | 20 | 7 |',rendered)


class PagesArtifactListingContract(unittest.TestCase):
    """deploy-pages looks once; the workflow waits, bounded, until its artifact is listed."""

    STEP = "      - name: Wait until this attempt's Pages artifact is listed\n"

    def workflow(self):
        return (Path(__file__).resolve().parents[2] / ".github/workflows/deploy-site.yml").read_text()

    def script(self):
        import textwrap
        body = self.workflow().split(self.STEP, 1)[1].split("        run: |\n", 1)[1]
        return textwrap.dedent(body.split("\n\n", 1)[0]) + "\n"

    def run_wait(self, responses):
        import os
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "responses").write_text("".join(line + "\n" for line in responses))
            calls = root / "calls"
            calls.write_text("")
            stub = ('#!/bin/bash\nprintf "%s\\n" "$*" >> "$STUB_CALLS"\n'
                    'n=$(wc -l < "$STUB_CALLS" | tr -d " ")\nline=$(sed -n "${n}p" "$STUB_RESPONSES")\n'
                    'if [ "$line" = FAIL ]; then echo "gh: HTTP 502" >&2; exit 1; fi\n'
                    'if [ "$line" = FAILBODY ]; then echo \'{"message":"Server Error","status":"500"}\'; '
                    'echo "gh: HTTP 500" >&2; exit 1; fi\nprintf "%s\\n" "$line"\n')
            for name, text in (("gh", stub), ("sleep", "#!/bin/bash\nexit 0\n")):
                (root / name).write_text(text)
                (root / name).chmod(0o755)
            env = {"PATH": f"{root}:{os.environ.get('PATH', '')}", "STUB_CALLS": str(calls),
                   "STUB_RESPONSES": str(root / "responses"), "GITHUB_REPOSITORY": "owner/profile",
                   "GITHUB_RUN_ID": "45481354867", "PAGES_ARTIFACT_NAME": "github-pages-45481354867-1",
                   "GH_TOKEN": "test-token"}
            result = subprocess.run(["bash", "-e", "-c", self.script()], env=env,
                                    capture_output=True, text=True, timeout=60)
            return result, calls.read_text().splitlines()

    def test_wait_sits_between_upload_and_deploy_and_reads_this_attempts_name(self):
        workflow = self.workflow()
        upload = workflow.index("uses: actions/upload-pages-artifact@v3")
        wait = workflow.index(self.STEP)
        deploy = workflow.index("uses: actions/deploy-pages@v4")
        self.assertLess(upload, wait)
        self.assertLess(wait, deploy)
        self.assertIn("\npermissions:\n  actions: read\n", workflow)
        self.assertIn("GH_TOKEN: ${{ github.token }}", workflow[wait:deploy])
        self.assertIn("artifacts?name=${PAGES_ARTIFACT_NAME}", self.script())

    def test_listed_artifact_continues_after_the_check_that_sees_it(self):
        for responses, checks in ((["1"], 1), (["0", "0", "1"], 3), (["FAIL", "", "1"], 3),
                                  (["FAILBODY", "FAILBODY", "1"], 3)):
            with self.subTest(responses=responses):
                result, calls = self.run_wait(responses)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual(checks, len(calls))
                self.assertTrue(all(call == "api repos/owner/profile/actions/runs/45481354867/artifacts"
                                    "?name=github-pages-45481354867-1 --jq .total_count" for call in calls), calls)

    def test_unlisted_artifact_fails_by_name_after_twenty_checks(self):
        result, calls = self.run_wait(["0"] * 25)
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(20, len(calls))
        self.assertIn("was not listed after 20 checks", result.stdout)

    def test_duplicate_listing_refuses_without_choosing(self):
        result, calls = self.run_wait(["0", "2"])
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(2, len(calls))
        self.assertIn("refusing an ambiguous deployment", result.stdout)

    def test_unlisted_artifact_reports_the_last_api_error(self):
        result, calls = self.run_wait(["FAILBODY"] * 25)
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(20, len(calls))
        self.assertIn('Last API response: {"message":"Server Error","status":"500"}', result.stdout)


class MetricsApiBudgetContract(unittest.TestCase):
    """Generation starts on a budget it can finish with, or waits briefly for the reset."""

    STEP = "      - name: Wait for the generation token's API budget\n"
    NOW = 1795557600

    def workflow(self):
        return (Path(__file__).resolve().parents[2] / ".github/workflows/metrics.yml").read_text()

    def step(self):
        return self.workflow().split(self.STEP, 1)[1].split("\n\n", 1)[0]

    def script(self):
        import textwrap
        return textwrap.dedent(self.step().split("        run: |\n", 1)[1]) + "\n"

    def need(self):
        return int(re.search(r'PROFILE_API_BUDGET_NEED: "(\d+)"', self.step()).group(1))

    def run_wait(self, responses):
        import os
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "responses").write_text("".join(line + "\n" for line in responses))
            for name in ("calls", "sleeps"):
                (root / name).write_text("")
            stubs = {
                "gh": ('#!/bin/bash\nprintf "%s\\n" "$*" >> "$STUB_CALLS"\n'
                       'n=$(wc -l < "$STUB_CALLS" | tr -d " ")\nline=$(sed -n "${n}p" "$STUB_RESPONSES")\n'
                       'if [ "$line" = FAIL ]; then echo \'{"message":"Bad credentials"}\'; exit 1; fi\n'
                       'printf "%s\\n" "$line"\n'),
                "sleep": '#!/bin/bash\nprintf "%s\\n" "$1" >> "$STUB_SLEEPS"\n',
                "date": f'#!/bin/bash\necho {self.NOW}\n',
            }
            for name, text in stubs.items():
                (root / name).write_text(text)
                (root / name).chmod(0o755)
            env = {"PATH": f"{root}:{os.environ.get('PATH', '')}", "STUB_CALLS": str(root / "calls"),
                   "STUB_SLEEPS": str(root / "sleeps"), "STUB_RESPONSES": str(root / "responses"),
                   "PROFILE_API_BUDGET_NEED": str(self.need()), "PROFILE_API_BUDGET_MAX_WAIT": "900",
                   "GH_TOKEN": "test-token"}
            result = subprocess.run(["bash", "-e", "-c", self.script()], env=env,
                                    capture_output=True, text=True, timeout=60)
            return (result, (root / "calls").read_text().splitlines(),
                    (root / "sleeps").read_text().splitlines())

    def test_budget_wait_sits_between_token_resolution_and_generation(self):
        workflow = self.workflow()
        resolve = workflow.index("      - name: Resolve GitHub token\n")
        wait = workflow.index(self.STEP)
        generate = workflow.index("python scripts/profile_cli.py generate-profile")
        self.assertLess(resolve, wait)
        self.assertLess(wait, generate)
        self.assertNotIn("\n        if:", self.step())
        self.assertNotIn("continue-on-error", self.step())
        self.assertTrue(0 < self.need() <= 5000)

    def test_sufficient_budget_generates_at_once(self):
        result, calls, sleeps = self.run_wait([f"{self.need()} 5000 {self.NOW + 300}"])
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(["api rate_limit --jq .resources.core | \"\\(.remaining) \\(.limit) \\(.reset)\""], calls)
        self.assertEqual([], sleeps)
        self.assertIn(f"API budget: {self.need()} of 5000 remaining", result.stdout)

    def test_short_budget_waits_for_a_near_reset_then_generates(self):
        result, calls, sleeps = self.run_wait([f"{self.need() - 1} 5000 {self.NOW + 300}", f"5000 5000 {self.NOW + 3900}"])
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(["305"], sleeps)
        self.assertEqual(2, len(calls))
        self.assertIn(f"API budget after waiting: 5000 5000 {self.NOW + 3900}", result.stdout)

    def test_short_budget_with_a_distant_or_past_reset_warns_without_waiting(self):
        for reset in (self.NOW + 3000, self.NOW - 60):
            with self.subTest(reset=reset):
                result, calls, sleeps = self.run_wait([f"12 5000 {reset}"])
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual([], sleeps)
                self.assertIn("collection may fail with HTTP 403", result.stdout)

    def test_unreadable_budget_never_blocks_generation(self):
        for response in ("FAIL", "", "not a budget"):
            with self.subTest(response=response):
                result, calls, sleeps = self.run_wait([response])
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual([], sleeps)
                self.assertIn("API budget unreadable", result.stdout)

    def test_fallback_limit_below_need_is_the_target(self):
        result, calls, sleeps = self.run_wait([f"1000 1000 {self.NOW + 300}"])
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([], sleeps)
        self.assertIn("generation needs about 1000", result.stdout)
        result, calls, sleeps = self.run_wait([f"999 1000 {self.NOW + 300}", f"1000 1000 {self.NOW + 3900}"])
        self.assertEqual(["305"], sleeps)

    def test_wait_bound_is_inclusive_and_a_due_reset_does_not_wait(self):
        result, calls, sleeps = self.run_wait([f"0 5000 {self.NOW + 895}", f"5000 5000 {self.NOW + 4495}"])
        self.assertEqual(["900"], sleeps)
        for reset in (self.NOW + 896, self.NOW - 5):
            with self.subTest(reset=reset):
                result, calls, sleeps = self.run_wait([f"0 5000 {reset}"])
                self.assertEqual([], sleeps)
                self.assertIn("collection may fail with HTTP 403", result.stdout)

    def test_budget_still_short_after_waiting_is_logged_and_generation_continues(self):
        result, calls, sleeps = self.run_wait([f"3 5000 {self.NOW + 120}", f"4 5000 {self.NOW + 120}"])
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(["125"], sleeps)
        self.assertIn(f"API budget after waiting: 4 5000 {self.NOW + 120}", result.stdout)

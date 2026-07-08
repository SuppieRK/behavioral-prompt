import importlib.util
import io
import subprocess
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path

from evals.harness.cli import _preflight_failure_message, parse_args
from evals.harness.outcomes import Outcome, OutcomeStatus, ReasonCode
from evals.harness.preflight import PreflightResult
from evals.harness.reporting.html_report import REPORT_EMBED_MARKER


class LegacyShimReductionTest(unittest.TestCase):
    def test_run_evals_bin_is_thin_cli_shim(self):
        text = Path("evals/bin/run_evals.py").read_text()

        self.assertLess(len(text.splitlines()), 20)
        self.assertIn("from evals.harness.cli import main", text)
        self.assertNotIn("CASE_SCORERS", text)
        self.assertNotIn("REPORT_VIEWER_HTML", text)

    def test_run_evals_bin_is_runnable_from_repo_root(self):
        completed = subprocess.run([sys.executable, "evals/bin/run_evals.py", "--help"], text=True, capture_output=True, check=False)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("--case", completed.stdout)

    def test_eval_scoring_bin_reexports_generic_harness_helpers(self):
        text = Path("evals/bin/eval_scoring.py").read_text()

        self.assertLess(len(text.splitlines()), 20)
        self.assertIn("run_deterministic_scorer", text)
        self.assertNotIn("CASE_SCORERS", text)

    def test_report_viewer_bin_reexports_minimal_renderer(self):
        spec = importlib.util.spec_from_file_location("report_viewer_shim", "evals/bin/report_viewer.py")
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)

        self.assertEqual(module.REPORT_EMBED_MARKER, REPORT_EMBED_MARKER)
        self.assertIn(REPORT_EMBED_MARKER, module.REPORT_VIEWER_HTML)

    def test_cli_parser_keeps_selection_options(self):
        args = parse_args(["--target", "local-codex-gpt55", "--case", "sample", "--tag", "smoke", "--critical"])

        self.assertEqual(args.target, ["local-codex-gpt55"])
        self.assertEqual(args.case, ["sample"])
        self.assertEqual(args.tag, "smoke")
        self.assertTrue(args.critical)

    def test_cli_parser_keeps_legacy_flags(self):
        args = parse_args(["--target-name", "local-pi", "--critical", "true"])

        self.assertEqual(args.target, ["local-pi"])
        self.assertTrue(args.critical)
        self.assertFalse(parse_args(["--critical", "false"]).critical)

        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            parse_args(["--" + "jo" + "bs", "4"])

        help_output = subprocess.run([sys.executable, "evals/bin/run_evals.py", "--help"], text=True, capture_output=True, check=False).stdout
        self.assertNotIn("--" + "jo" + "bs", help_output)

    def test_cli_preflight_failure_message_identifies_target(self):
        item = PreflightResult(
            "local-opencode-gpt55",
            Outcome(OutcomeStatus.HARNESS_ERROR, ReasonCode.CODING_AGENT_UNAVAILABLE, "Unexpected server error"),
            1.0,
            {"runtime": "opencode", "model": {"provider": "openai", "model": "gpt-5.5"}, "failed_check": "process"},
        )

        message = _preflight_failure_message(item)

        self.assertIn("target=local-opencode-gpt55", message)
        self.assertIn("runtime=opencode", message)
        self.assertIn("model=openai/gpt-5.5", message)
        self.assertIn("failed_check=process", message)

    def test_harness_modules_remain_reviewably_small(self):
        large = []
        for path in Path("evals/harness").rglob("*.py"):
            lines = len(path.read_text().splitlines())
            if lines > 260:
                large.append((path.as_posix(), lines))

        self.assertEqual(large, [])


if __name__ == "__main__":
    unittest.main()

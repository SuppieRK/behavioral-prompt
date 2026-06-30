import unittest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bin"))

from report_viewer import REPORT_EMBED_MARKER, REPORT_VIEWER_HTML


class ReportViewerTest(unittest.TestCase):
    def setUp(self):
        self.html = REPORT_VIEWER_HTML

    def test_generated_viewer_template_is_self_contained(self):
        self.assertIn("<style>", self.html)
        self.assertIn("<script>", self.html)
        self.assertNotIn('href="styles.css"', self.html)
        self.assertNotIn('src="viewer.js"', self.html)
        self.assertFalse(Path("evals/report-viewer").exists())

    def test_static_viewer_has_report_loading_and_result_controls(self):
        for required in [
            'id="report-file"',
            'id="drop-zone"',
            'id="summary-grid"',
            'id="performance-grid"',
            'id="anomaly-list"',
            'id="result-list"',
            'data-filter="fail"',
            'data-filter="current"',
            'data-filter="stale"',
        ]:
            with self.subTest(required=required):
                self.assertIn(required, self.html)

    def test_viewer_renders_required_report_evidence(self):
        for required in [
            "run.status",
            "run.id",
            "report_state",
            "promotion",
            "target_usage",
            "prompt.metrics",
            "response_length",
            "agent_parallelism",
            "run.latest_invocation_performance",
            "Cases aggregated",
            "Cumulative service",
            "Prompt bytes",
            "Prompt est. tokens",
            "Response est. tokens",
            "deterministic_checks",
            "result.judge",
            "evidence.final_response",
            "evidence.commands",
            "evidence.timeline",
            "evidence.tool_calls",
            "evidence.durable_context_actions",
            "evidence.changed_files",
            "evidence.diff",
        ]:
            with self.subTest(required=required):
                self.assertIn(required, self.html)

    def test_static_viewer_has_embedded_report_marker(self):
        self.assertIn(REPORT_EMBED_MARKER, self.html)


if __name__ == "__main__":
    unittest.main()

import json
import unittest

from evals.harness.reporting.html_report import REPORT_EMBED_MARKER, render_html


class ReportViewerTest(unittest.TestCase):
    def test_minimal_viewer_renders_review_critical_report_fields(self):
        html = render_html({
            "title": "Eval Report",
            "status_counts": {"pass": 1, "fail": 1, "not_evaluated": 1, "harness_error": 1},
            "metrics": {"duration_seconds": 12.5, "actual_tokens_spent": 100, "avoided_tokens_by_reuse": 42},
            "promotion": {"allowed": False, "reason": "missing or blocking required cases", "required_pass": 1, "required_total": 2},
            "cases": [
                {
                    "case": {
                        "id": "sample",
                        "name": "Sample case",
                        "description": "A small case",
                        "user_input": "Do it",
                        "ground_truth": ["Expected behavior"],
                    },
                    "targets": [
                        {
                            "target_id": "codex",
                            "status": "pass",
                            "deterministic_checks": [{"name": "diff", "pass": True}],
                            "judge": {"verdict": "pass", "rationale": "Meets expectation"},
                        }
                    ],
                }
            ],
        })

        for required in [
            "Sample case",
            "Expected behavior",
            "duration_seconds",
            "actual_tokens_spent",
            "avoided_tokens_by_reuse",
            "Promotion Blocked",
            "missing or blocking required cases",
            "deterministic_checks",
            "rationale",
            "case-card",
            "target-card",
            "Raw report JSON",
            REPORT_EMBED_MARKER,
        ]:
            with self.subTest(required=required):
                self.assertIn(required, html)

    def test_result_json_v1_flat_cells_render_target_details(self):
        html = render_html({
            "schema_version": "result-json-v1",
            "title": "Eval Report",
            "status_counts": {"pass": 0, "fail": 1, "not_evaluated": 0, "harness_error": 0},
            "cells": [
                {
                    "case_id": "case-a",
                    "case_name": "Case A",
                    "case_description": "A flat report case",
                    "user_input": "Do it",
                    "ground_truth": ["Expected flat behavior"],
                    "target_id": "local-pi",
                    "status": "fail",
                    "reason": "deterministic_check_failed",
                    "message": "failed check",
                    "deterministic_checks": [{"name": "diff", "pass": False}],
                    "judge": {"verdict": False, "rationale": "Missing evidence"},
                    "changed_files": ["src/app.py"],
                    "final_response": "I could not prove it.",
                }
            ],
        })

        for required in [
            "Case A",
            "Expected flat behavior",
            "local-pi",
            "fail",
            "deterministic_check_failed",
            "diff",
            "Missing evidence",
            "src/app.py",
            "I could not prove it.",
            "badge fail",
            "Changed Files",
            "Final Response",
        ]:
            with self.subTest(required=required):
                self.assertIn(required, html)
        self.assertNotIn("<pre>[]</pre>", html)

    def test_minimal_viewer_omits_stale_report_controls(self):
        html = render_html({"title": "Eval Report"})

        self.assertNotIn('data-filter="stale"', html)
        self.assertNotIn("anomaly-list", html)
        self.assertNotIn("report_state", html)

    def test_embedded_report_json_is_parseable_script_text(self):
        html = render_html({"title": "Eval Report", "quoted": '"value"', "script": "</script>"})
        start = html.index("<script type='application/json' id='report'>") + len("<script type='application/json' id='report'>")
        end = html.index("</script>", start)
        embedded = html[start:end]

        self.assertNotIn("&quot;", embedded)
        self.assertEqual(json.loads(embedded)["quoted"], '"value"')
        self.assertEqual(json.loads(embedded)["script"], "</script>")


if __name__ == "__main__":
    unittest.main()

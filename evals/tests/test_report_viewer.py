import json
import unittest

from evals.harness.reporting.html_report import REPORT_EMBED_MARKER, render_html
from evals.harness.reporting.sanitize import compact_public_report


class ReportViewerTest(unittest.TestCase):
    def test_report_renders_target_matrix_and_deterministic_checks(self):
        html = render_html({
            "schema_version": "result-json-v2",
            "title": "Prompt Eval Report",
            "status_counts": {"pass": 1, "fail": 0, "not_evaluated": 0, "harness_error": 0},
            "promotion": {"allowed": True, "reason": "complete", "required_pass": 1, "required_total": 1},
            "cells": [{
                "case_id": "sample", "case_name": "Sample case", "target_id": "local-pi",
                "status": "pass", "reason": "", "changed_files": ["src/app.py"],
                "deterministic_checks": [{"name": "focused_validation", "pass": True, "observed": {"exit_code": 0}}],
            }],
        })

        for text in ("Sample case", "local-pi", "focused_validation", "1/1 targets pass", "Promotion Allowed"):
            self.assertIn(text, html)
        self.assertNotIn("Judge", html)
        self.assertNotIn("Raw report JSON", html)

    def test_public_report_removes_debug_evidence(self):
        report = compact_public_report({"cells": [{
            "case_id": "sample", "status": "pass", "diff": "large", "final_response": "raw",
            "normalized_evidence": {"timeline": []}, "raw_run": {"argv": []}, "workspace": {"path": "/tmp/x"},
            "attempt_cells": [{"diff": "private"}],
            "deterministic_checks": [{"name": "ok", "pass": True}],
        }]})
        cell = report["cells"][0]

        self.assertNotIn("diff", cell)
        self.assertNotIn("normalized_evidence", cell)
        self.assertNotIn("attempt_cells", cell)
        self.assertEqual(cell["deterministic_checks"][0]["name"], "ok")

    def test_embedded_report_json_is_parseable(self):
        html = render_html({"title": "Eval Report", "quoted": '"value"', "script": "</script>"})
        marker = "<script type='application/json' id='report'>"
        start = html.index(marker) + len(marker)
        end = html.index("</script>", start)
        embedded = html[start:end]

        self.assertEqual(json.loads(embedded)["quoted"], '"value"')
        self.assertIn(REPORT_EMBED_MARKER, html)


if __name__ == "__main__":
    unittest.main()

"""Compatibility exports for the minimal report viewer."""

from __future__ import annotations

from evals.harness.reporting.html_report import REPORT_EMBED_MARKER, render_html

REPORT_VIEWER_HTML = render_html({"title": "Prompt Eval Report"})

__all__ = ["REPORT_EMBED_MARKER", "REPORT_VIEWER_HTML", "render_html"]

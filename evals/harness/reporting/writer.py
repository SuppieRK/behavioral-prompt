from __future__ import annotations

import json
from pathlib import Path

from .html_report import render_html
from .json_report import result_json
from .sanitize import sanitize_public_report


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(text)
    temp.replace(path)


def write_report(report_dir: Path, report: dict[str, object], *, public: bool = False) -> None:
    data = result_json(sanitize_public_report(report))
    write_atomic(report_dir / "result.json", json.dumps(data, indent=2, sort_keys=True))
    write_atomic(report_dir / "result.html", _strip_trailing_whitespace(render_html(data)))


def _strip_trailing_whitespace(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()) + "\n"

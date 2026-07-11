from __future__ import annotations

import re
from typing import Any


SECRET_RE = re.compile(r"(?i)^(api[_-]?key|access[_-]?token|refresh[_-]?token|id[_-]?token|token|secret|cookie|authorization|password)$|secret|cookie|authorization|password|api[_-]?key|access[_-]?token|refresh[_-]?token|id[_-]?token")
SECRET_VALUE_RE = re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|id[_-]?token|token|secret|cookie|authorization|password)(\s*[=:]\s*)([^\s,;]+)")


def redact_text(value: str) -> str:
    return SECRET_VALUE_RE.sub(lambda match: f"{match.group(1)}{match.group(2)}<redacted>", value)


def sanitize_public_report(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: ("<redacted>" if SECRET_RE.search(str(key)) else sanitize_public_report(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_public_report(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def compact_public_report(report: dict[str, Any]) -> dict[str, Any]:
    compact = dict(report)
    compact.pop("preflights", None)
    cells = []
    for value in report.get("cells", []):
        if not isinstance(value, dict):
            continue
        cell = dict(value)
        for key in ("diff", "final_response", "normalized_evidence", "raw_run", "workspace", "harness_validation", "attempt_cells"):
            cell.pop(key, None)
        cells.append(cell)
    compact["cells"] = cells
    return compact

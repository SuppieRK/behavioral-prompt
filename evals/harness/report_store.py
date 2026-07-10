from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .reporting.json_report import result_json
from .reporting.sanitize import sanitize_public_report
from .reporting.writer import write_atomic
from .reuse import load_prior_cells


PROMPT_HISTORY_DIR = "by-prompt"
PROMPT_CELLS_FILE = "cells.json"


def prompt_history_cells_path(reports_dir: Path, prompt_hash: str) -> Path:
    return reports_dir / PROMPT_HISTORY_DIR / prompt_hash / PROMPT_CELLS_FILE


def load_prior_cells_from_reports(reports_dir: Path, prompt_hash: str) -> dict[tuple[str, str], Mapping[str, Any]]:
    prior: dict[tuple[str, str], Mapping[str, Any]] = {}
    _merge_prior(prior, load_prior_cells(prompt_history_cells_path(reports_dir, prompt_hash)))
    _merge_prior(prior, load_prior_cells(reports_dir / "current" / "result.json"))
    return prior


def write_prompt_history(reports_dir: Path, report: dict[str, object]) -> None:
    data = result_json(sanitize_public_report(report))
    prompt = data.get("prompt") if isinstance(data.get("prompt"), dict) else {}
    prompt_hash = prompt.get("sha256")
    if not isinstance(prompt_hash, str) or not prompt_hash:
        return
    path = prompt_history_cells_path(reports_dir, prompt_hash)
    existing = _load_cells_json(path)
    merged = _merge_cells(existing, data.get("cells", []))
    payload = {
        "schema_version": "prompt-history-cells-v1",
        "prompt": prompt,
        "cells": merged,
    }
    write_atomic(path, json.dumps(payload, indent=2, sort_keys=True))


def backfill_current_report_to_prompt_history(reports_dir: Path) -> None:
    path = reports_dir / "current" / "result.json"
    if not path.exists():
        return
    try:
        report = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return
    if isinstance(report, dict):
        write_prompt_history(reports_dir, report)


def _merge_prior(target: dict[tuple[str, str], Mapping[str, Any]], source: Mapping[tuple[str, str], Mapping[str, Any]]) -> None:
    for key, value in source.items():
        target[key] = value


def _load_cells_json(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return []
    cells = data.get("cells", []) if isinstance(data, dict) else []
    return [cell for cell in cells if isinstance(cell, dict)]


def _merge_cells(existing: list[dict[str, object]], incoming: Any) -> list[dict[str, object]]:
    merged: dict[tuple[str, str], dict[str, object]] = {}
    for cell in existing:
        key = _cell_key(cell)
        if key:
            merged[key] = cell
    if isinstance(incoming, list):
        for item in incoming:
            if isinstance(item, dict):
                key = _cell_key(item)
                if key:
                    merged[key] = item
    return sorted(merged.values(), key=lambda cell: (str(cell.get("target_id") or ""), str(cell.get("case_id") or "")))


def _cell_key(cell: Mapping[str, object]) -> tuple[str, str] | None:
    case_id = cell.get("case_id")
    target_id = cell.get("target_id")
    if isinstance(case_id, str) and isinstance(target_id, str):
        return (case_id, target_id)
    return None

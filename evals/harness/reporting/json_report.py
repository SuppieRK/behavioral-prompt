from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from ..outcomes import Outcome, OutcomeStatus, promotion_allowed


def to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return to_jsonable(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [to_jsonable(item) for item in value]
    return value


def result_json(report: dict[str, Any]) -> dict[str, Any]:
    return to_jsonable(report)


def build_result_report(
    *,
    prompt: Any,
    selftests: Any,
    preflights: dict[str, Any],
    cases: tuple[Any, ...],
    targets: tuple[Any, ...],
    cells: list[dict[str, Any]],
    required_cases: tuple[Any, ...] | None = None,
) -> dict[str, Any]:
    status_counts = {
        "pass": sum(1 for cell in cells if cell.get("status") == "pass"),
        "fail": sum(1 for cell in cells if cell.get("status") == "fail"),
        "not_evaluated": sum(1 for cell in cells if cell.get("status") == "not_evaluated"),
        "harness_error": sum(1 for cell in cells if cell.get("status") == "harness_error"),
        "timeout": sum(1 for cell in cells if cell.get("reason") == "timeout"),
        "reused_exact_match": sum(1 for cell in cells if cell.get("reused_exact_match")),
    }
    outcomes = [_outcome_from_cell(cell) for cell in cells]
    metrics = _metrics(cells, preflights)
    artifact_validation = _artifact_validation(prompt)
    promotion = _promotion(
        cells=cells,
        outcomes=outcomes,
        selftests=selftests,
        cases=cases,
        targets=targets,
        required_cases=required_cases or cases,
        artifact_validation=artifact_validation,
    )
    return result_json({
        "schema_version": "result-json-v1",
        "title": "Prompt Eval Report",
        "prompt": {"path": str(prompt.path), "sha256": prompt.sha256},
        "selftests": selftests,
        "preflights": preflights,
        "targets": [getattr(target, "to_fingerprint_data", lambda: target)() for target in targets],
        "case_count": len(cases),
        "target_count": len(targets),
        "cell_count": len(cells),
        "status_counts": status_counts,
        "metrics": metrics,
        "artifact_validation": artifact_validation,
        "promotion": promotion,
        "cells": cells,
    })


def _outcome_from_cell(cell: dict[str, Any]) -> Outcome:
    try:
        status = OutcomeStatus(str(cell.get("status")))
    except ValueError:
        status = OutcomeStatus.HARNESS_ERROR
    return Outcome(status)


def _metrics(cells: list[dict[str, Any]], preflights: dict[str, Any]) -> dict[str, Any]:
    durations = []
    actual_tokens = 0
    avoided_tokens = 0
    for cell in cells:
        raw = cell.get("raw_run") if isinstance(cell.get("raw_run"), dict) else {}
        usage_value = to_jsonable(cell.get("target_usage"))
        usage = usage_value if isinstance(usage_value, dict) else {}
        reused = bool(cell.get("reused_exact_match"))
        if not reused and raw.get("duration_seconds") is not None:
            durations.append(float(raw["duration_seconds"]))
        actual_tokens += 0 if reused else _first_int(usage.get("actual_tokens_spent"), usage.get("total_tokens_reported"), usage.get("uncached_total_tokens"), raw.get("actual_tokens_spent"), 0)
        avoided_tokens += int(usage.get("avoided_tokens_by_reuse") or 0)
    preflight_duration = 0.0
    for value in preflights.values():
        items = value if isinstance(value, list) else [value]
        for item in items:
            item_value = to_jsonable(item)
            if isinstance(item_value, dict):
                preflight_duration += float(item_value.get("duration_seconds") or 0)
    return {
        "duration_seconds": sum(durations),
        "preflight_duration_seconds": preflight_duration,
        "actual_tokens_spent": actual_tokens,
        "avoided_tokens_by_reuse": avoided_tokens,
        "top_duration_cells": sorted(
            [
                {
                    "case_id": cell.get("case_id"),
                    "target_id": cell.get("target_id"),
                    "duration_seconds": 0 if cell.get("reused_exact_match") else (cell.get("raw_run") or {}).get("duration_seconds", 0),
                }
                for cell in cells
            ],
            key=lambda item: float(item.get("duration_seconds") or 0),
            reverse=True,
        )[:5],
    }


def _first_int(*values: Any) -> int:
    for value in values:
        if value is not None:
            return int(value)
    return 0


def _promotion(*, cells: list[dict[str, Any]], outcomes: list[Outcome], selftests: Any, cases: tuple[Any, ...], targets: tuple[Any, ...], required_cases: tuple[Any, ...], artifact_validation: dict[str, Any]) -> dict[str, Any]:
    selftests_passed = bool(getattr(selftests, "passed", False))
    coverage = _required_coverage(cells, required_cases, targets)
    outcome_pass = bool(cells) and bool(cases) and bool(targets) and promotion_allowed(outcomes, selftests_passed=selftests_passed)
    artifact_pass = bool(artifact_validation.get("pass"))
    coverage_pass = not coverage["missing_required_cases"] and not coverage["failed_required_cases"] and not coverage["not_evaluated_required_cases"] and not coverage["harness_error_required_cases"]
    allowed = outcome_pass and artifact_pass and coverage_pass
    return {
        "allowed": allowed,
        "eligible": allowed,
        "reason": _promotion_reason(selftests_passed, outcome_pass, artifact_pass, coverage_pass),
        "selftests_passed": selftests_passed,
        "required_total": coverage["required_total"],
        "required_evaluated": coverage["required_evaluated"],
        "required_pass": coverage["required_pass"],
        "missing_required_cases": coverage["missing_required_cases"],
        "failed_required_cases": coverage["failed_required_cases"],
        "not_evaluated_required_cases": coverage["not_evaluated_required_cases"],
        "harness_error_required_cases": coverage["harness_error_required_cases"],
        "artifact_validation_pass": artifact_pass,
    }


def _required_coverage(cells: list[dict[str, Any]], required_cases: tuple[Any, ...], targets: tuple[Any, ...]) -> dict[str, Any]:
    target_ids = [_target_id(target) for target in targets]
    target_count = len(target_ids)
    cell_by_pair = {(str(cell.get("case_id")), str(cell.get("target_id"))): cell for cell in cells}
    missing: list[str] = []
    failed: list[str] = []
    not_evaluated: list[str] = []
    harness_error: list[str] = []
    required_pass = 0
    for target_id in target_ids:
        for case in required_cases:
            case_id = str(getattr(case, "id", case))
            label = case_id if target_count == 1 else f"{target_id}/{case_id}"
            cell = cell_by_pair.get((case_id, target_id))
            status = str(cell.get("status")) if cell else ""
            if not cell:
                missing.append(label)
            elif status == "pass":
                required_pass += 1
            elif status == "fail":
                failed.append(label)
            elif status == "not_evaluated":
                not_evaluated.append(label)
            else:
                harness_error.append(label)
    required_total = len(required_cases) * target_count
    return {
        "required_total": required_total,
        "required_evaluated": required_total - len(missing),
        "required_pass": required_pass,
        "missing_required_cases": missing,
        "failed_required_cases": failed,
        "not_evaluated_required_cases": not_evaluated,
        "harness_error_required_cases": harness_error,
    }


def _promotion_reason(selftests_passed: bool, outcome_pass: bool, artifact_pass: bool, coverage_pass: bool) -> str:
    if not selftests_passed:
        return "harness selftests failed"
    if not artifact_pass:
        return "prompt artifact validation failed"
    if not coverage_pass:
        return "missing or blocking required cases"
    if not outcome_pass:
        return "selected cells did not all pass"
    return "all required cases passed on target"


def _target_id(target: Any) -> str:
    value = getattr(target, "id", None)
    if value is not None:
        return str(value)
    if isinstance(target, dict):
        return str(target.get("id") or target.get("name") or "target")
    return str(target)


def _artifact_validation(prompt: Any) -> dict[str, Any]:
    path = Path(prompt.path)
    text = path.read_text() if path.exists() else ""
    checks = [
        _check("prompt_artifact_exists", path.exists(), f"prompt artifact exists: {path}", f"prompt artifact missing: {path}"),
        _check("prompt_preserves_kernel", _prompt_preserves_kernel(text), "kernel areas present", "prompt missing required kernel areas"),
        _check("prompt_harness_neutral", _prompt_harness_neutral(text), "no target-specific prompt wording", "target-specific prompt wording present"),
        _check("prompt_single_markdown", path.name == "PROMPT.md", "PROMPT.md is the primary artifact", f"primary prompt artifact is not PROMPT.md: {path}"),
        _check("prompt_generic_durable_context", _prompt_generic_durable_context(text), "durable context wording is generic", "durable context wording is missing or target-specific"),
        _check("prompt_reviewable_size", len(text.encode("utf-8")) <= 12000 and len(text.split()) <= 1800, "prompt remains reviewably small", "prompt exceeds reviewable size threshold"),
    ]
    return {"stage": "prompt-artifact", "pass": all(bool(check["pass"]) for check in checks), "checks": checks}


def _check(name: str, passed: bool, pass_reason: str, fail_reason: str) -> dict[str, object]:
    return {"name": name, "pass": passed, "reason": pass_reason if passed else fail_reason}


def _prompt_preserves_kernel(text: str) -> bool:
    lowered = text.lower()
    groups = (
        ("challenge", "push back"),
        ("test first", "test-first", "failing check", "reproduction"),
        ("smallest", "minimal", "production-correct"),
        ("durable", "todo", "plan"),
        ("validate", "validation", "what ran"),
    )
    return all(any(token in lowered for token in group) for group in groups)


def _prompt_harness_neutral(text: str) -> bool:
    lowered = text.lower()
    return not any(token in lowered for token in ("opencode", "codex", "--append-system-prompt")) and " pi " not in f" {lowered} "


def _prompt_generic_durable_context(text: str) -> bool:
    lowered = text.lower()
    return "durable" in lowered and not any(token in lowered for token in ("todolist", "todowrite", "update_plan"))

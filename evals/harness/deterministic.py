from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import Any, Mapping

from .evidence import NormalizedAgentEvidence
from .models import EvalCase
from .outcomes import Outcome, OutcomeStatus, ReasonCode


def score_case(case: EvalCase, evidence: NormalizedAgentEvidence) -> tuple[Outcome, tuple[dict[str, object], ...]]:
    if case.contract.get("actions") and not evidence.target.agent_actions:
        return Outcome(OutcomeStatus.HARNESS_ERROR, ReasonCode.REQUIRED_EVIDENCE_UNAVAILABLE, "normalized action evidence is unavailable"), ()
    try:
        checks = _score(case.contract, evidence)
    except (KeyError, TypeError, ValueError) as exc:
        return Outcome(OutcomeStatus.HARNESS_ERROR, ReasonCode.SCORER_EXCEPTION, str(exc)), ()
    if not checks:
        return Outcome(OutcomeStatus.HARNESS_ERROR, ReasonCode.SCORER_EXCEPTION, "deterministic contract produced no checks"), ()
    return Outcome(OutcomeStatus.PASS if all(bool(item["pass"]) for item in checks) else OutcomeStatus.FAIL), tuple(checks)


def score_cached_cell(case: EvalCase, cell: Mapping[str, Any]) -> tuple[Outcome, tuple[dict[str, object], ...]]:
    normalized = cell.get("normalized_evidence") if isinstance(cell.get("normalized_evidence"), Mapping) else {}
    files = normalized.get("workspace_files") if isinstance(normalized.get("workspace_files"), Mapping) else {}
    from .evidence import HarnessValidationResult, NormalizedTargetEvidence

    validation = tuple(
        HarnessValidationResult(
            str(item.get("id", index)), str(item.get("command", "")), str(item.get("cwd", "")),
            str(item.get("exit_status", "")), int(item.get("exit_code", 1)), str(item.get("stdout_excerpt", "")),
            str(item.get("stderr_excerpt", "")), float(item.get("duration_seconds", 0)),
        )
        for index, item in enumerate(cell.get("harness_validation") or ()) if isinstance(item, Mapping)
    )
    evidence = NormalizedAgentEvidence(
        target=NormalizedTargetEvidence(
            final_response=str(cell.get("final_response") or normalized.get("final_response") or ""),
            agent_actions=tuple(normalized.get("actions") or ()),
        ),
        diff=str(cell.get("diff") or ""),
        changed_files=tuple(str(path) for path in cell.get("changed_files") or ()),
        harness_validation=validation,
        workspace_files={str(path): str(content) for path, content in files.items()},
    )
    return score_case(case, evidence)


def score_cached_attempts(case: EvalCase, cell: Mapping[str, Any]) -> tuple[Outcome, tuple[dict[str, object], ...], int]:
    candidates = [item for item in cell.get("attempt_cells", ()) if isinstance(item, Mapping)]
    if not candidates:
        candidates = [cell]
    last: tuple[Outcome, tuple[dict[str, object], ...]] | None = None
    for index, candidate in enumerate(candidates, start=1):
        scored = score_cached_cell(case, candidate)
        last = scored
        if scored[0].status == OutcomeStatus.PASS:
            return scored[0], scored[1], index
    assert last is not None
    return last[0], last[1], len(candidates)


def _score(contract: Mapping[str, Any], evidence: NormalizedAgentEvidence) -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []
    changes = contract.get("changes") if isinstance(contract.get("changes"), Mapping) else {}
    changed = set(evidence.changed_files)
    allowed = tuple(str(path) for path in changes.get("allowed", ()))
    required = tuple(str(path) for path in changes.get("required", ()))
    unchanged = tuple(str(path) for path in changes.get("unchanged", ()))
    forbidden = tuple(str(path) for path in changes.get("forbidden", ()))
    if allowed:
        checks.append(_check("allowed_changes", all(_matches_any(path, allowed) for path in changed), sorted(changed)))
    if required:
        checks.append(_check("required_changes", all(any(fnmatch.fnmatch(path, pattern) for path in changed) for pattern in required), sorted(changed)))
    if unchanged:
        checks.append(_check("unchanged_paths", not any(_matches_any(path, unchanged) for path in changed), sorted(changed)))
    if forbidden:
        checks.append(_check("forbidden_changes", not any(_matches_any(path, forbidden) for path in changed), sorted(changed)))
    if changes.get("max_files") is not None:
        checks.append(_check("change_budget", len(changed) <= int(changes["max_files"]), len(changed)))

    actions = tuple(item for item in evidence.target.agent_actions if isinstance(item, Mapping))
    first_write = min((_index(item) for item in actions if item.get("kind") == "write"), default=None)
    for number, rule in enumerate(contract.get("actions") or ()):
        if not isinstance(rule, Mapping):
            raise TypeError("action rules must be mappings")
        name = str(rule.get("name") or f"action_{number}")
        matching = [item for item in actions if _action_matches(item, rule)]
        relation = str(rule.get("relation") or "any")
        write_paths = tuple(str(path) for path in rule.get("write_paths", ()))
        related_write = min(
            (_index(item) for item in actions if item.get("kind") == "write" and (not write_paths or any(_matches_any(path, write_paths) for path in item.get("paths", ())))),
            default=None,
        )
        if related_write is None and write_paths and changed and all(_matches_any(path, write_paths) for path in changed):
            related_write = first_write
        if relation == "before_write":
            passed = first_write is not None and any(_index(item) < first_write for item in matching)
        elif relation == "after_write":
            passed = first_write is not None and any(_index(item) > first_write for item in matching)
        elif relation == "before_path_write":
            passed = related_write is not None and any(_index(item) < related_write for item in matching)
        elif relation == "after_path_write":
            passed = related_write is not None and any(_index(item) > related_write for item in matching)
        elif relation == "forbidden":
            passed = not matching
        else:
            passed = len(matching) >= int(rule.get("min", 1))
        if rule.get("max") is not None:
            passed = passed and len(matching) <= int(rule["max"])
        checks.append(_check(name, passed, {"matches": len(matching), "first_write": first_write, "related_write": related_write}))

    files = evidence.workspace_files
    for number, assertion in enumerate(contract.get("assertions") or ()):
        if not isinstance(assertion, Mapping):
            raise TypeError("assertions must be mappings")
        kind = str(assertion.get("kind") or "")
        path = str(assertion.get("path") or "")
        content = str(files.get(path, ""))
        value = str(assertion.get("value") or "")
        name = str(assertion.get("name") or f"assertion_{number}")
        if kind == "contains":
            passed = value in content
        elif kind == "not_contains":
            passed = value not in content
        elif kind == "matches":
            passed = re.search(value, content, re.MULTILINE) is not None
        elif kind == "validation_passes":
            passed = bool(evidence.harness_validation) and all(item.exit_status == "success" for item in evidence.harness_validation)
        elif kind == "file_exists":
            passed = path in files
        elif kind == "action_or_file_matches":
            pattern = value
            action_kind = str(assertion.get("action_kind") or "plan")
            action_text = "\n".join(str(item.get("detail") or item.get("command") or "") for item in actions if item.get("kind") == action_kind)
            file_text = "\n".join(content for file_path, content in files.items() if not path or _matches_any(file_path, (path,)))
            passed = re.search(pattern, f"{action_text}\n{file_text}", re.IGNORECASE | re.MULTILINE) is not None
        else:
            raise ValueError(f"unknown assertion kind: {kind}")
        checks.append(_check(name, passed, {"kind": kind, "path": path}))

    output = contract.get("output") if isinstance(contract.get("output"), Mapping) else {}
    response = evidence.target.final_response
    checks.append(_check("response_present", bool(response.strip()), len(response)))
    checks.append(_check("response_size", len(response) <= int(output.get("max_chars", 3000)), len(response)))
    nonblank = sum(bool(line.strip()) for line in response.splitlines())
    checks.append(_check("response_lines", nonblank <= int(output.get("max_nonblank_lines", 30)), nonblank))
    return checks


def _action_matches(action: Mapping[str, object], rule: Mapping[str, object]) -> bool:
    if rule.get("kind") and action.get("kind") != rule.get("kind"):
        return False
    pattern = str(rule.get("pattern") or "")
    text = " ".join(str(action.get(key) or "") for key in ("command", "tool", "path", "detail"))
    if pattern and re.search(pattern, text, re.IGNORECASE) is None:
        return False
    paths = tuple(str(path) for path in rule.get("paths", ()))
    action_paths = tuple(str(path) for path in action.get("paths", ()))
    return not paths or any(_matches_any(path, paths) for path in action_paths)


def _matches_any(path: str, patterns: tuple[str, ...]) -> bool:
    normalized = path.replace("\\", "/")
    return any(
        fnmatch.fnmatch(normalized, pattern)
        or fnmatch.fnmatch(normalized, f"*/{pattern}")
        or normalized.endswith(f"/{pattern}")
        for pattern in patterns
    )


def _index(action: Mapping[str, object]) -> int:
    return int(action.get("index", 1_000_000))


def _check(name: str, passed: bool, observed: object) -> dict[str, object]:
    return {"name": name, "pass": bool(passed), "observed": observed}

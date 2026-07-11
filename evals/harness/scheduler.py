from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
from uuid import uuid4

from .adapters.base import CodingAgentRunner
from .cells import result_cell, unavailable_auth_cell
from .evidence import NormalizedAgentEvidence
from .deterministic import score_case
from .actions import compact_actions
from .models import AgentInvocationContext, EvalCase, PromptArtifact
from .outcomes import Outcome, OutcomeStatus, ReasonCode
from .progress import ProgressCallback, emit_progress, progress_summary
from .prompt_injection import baseline_prompt_injection
from .reuse import build_cache_key, build_score_key
from .validation import run_harness_validation
from .workspace import create_workspace, diff_snapshots, snapshot_files, snapshot_text_files


@dataclass(frozen=True)
class MatrixCell:
    case_id: str
    target_id: str
    result: dict[str, object]


def run_case_first(
    cases: tuple[EvalCase, ...],
    runners: tuple[CodingAgentRunner, ...],
    execute,
    *,
    progress: ProgressCallback | None = None,
    cell_checkpoint=None,
) -> tuple[MatrixCell, ...]:
    cells: list[MatrixCell] = []
    completed_results: list[dict[str, object]] = []
    total_cells = len(cases) * len(runners)
    completed_cells = 0
    emit_progress(progress, {"event": "run_started", "total_cases": len(cases), "total_targets": len(runners), "total_cells": total_cells})
    for case_number, case in enumerate(cases, start=1):
        emit_progress(progress, {"event": "case_started", "case_id": case.id, "case_name": case.name, "case_index": case_number, "total_cases": len(cases), "target_count": len(runners)})
        with ThreadPoolExecutor(max_workers=max(1, len(runners))) as executor:
            future_map = {}
            for runner in runners:
                emit_progress(progress, {"event": "cell_started", "case_id": case.id, "target_id": runner.id, "case_index": case_number, "total_cases": len(cases), "completed_cells": completed_cells, "total_cells": total_cells})
                future_map[executor.submit(execute, case, runner)] = runner
            for future in as_completed(future_map):
                runner = future_map[future]
                result = future.result()
                completed_cells += 1
                completed_results.append(result)
                cells.append(MatrixCell(case.id, runner.id, result))
                if cell_checkpoint is not None:
                    cell_checkpoint(result)
                emit_progress(progress, {
                    "event": "cell_completed",
                    "case_id": case.id,
                    "target_id": runner.id,
                    "case_index": case_number,
                    "total_cases": len(cases),
                    "completed_cells": completed_cells,
                    "total_cells": total_cells,
                    "status": result.get("status"),
                    "reason": result.get("reason"),
                    "reused_exact_match": bool(result.get("reused_exact_match")),
                    **progress_summary(completed_results),
                })
        case_cells = [cell.result for cell in cells if cell.case_id == case.id]
        emit_progress(progress, {
            "event": "case_completed",
            "case_id": case.id,
            "case_index": case_number,
            "total_cases": len(cases),
            "completed_cells": completed_cells,
            "total_cells": total_cells,
            **progress_summary(case_cells),
        })
    emit_progress(progress, {"event": "run_completed", "completed_cells": completed_cells, "total_cells": total_cells, **progress_summary(completed_results)})
    return tuple(cells)


def execute_case_target(
    *,
    case: EvalCase,
    runner: CodingAgentRunner,
    prompt: PromptArtifact,
    fixtures_dir: Path,
    timeout_seconds: int = 360,
) -> dict[str, object]:
    if runner.agent.auth_unavailable:
        return unavailable_auth_cell(case=case, runner=runner, prompt=prompt, fixtures_dir=fixtures_dir)
    try:
        workspace = create_workspace(fixture_name=case.fixture, fixtures_dir=fixtures_dir)
    except Exception as exc:
        cache_key = build_cache_key(case, runner.agent, prompt, fixtures_dir=fixtures_dir)
        return result_cell(case=case, runner=runner, outcome=Outcome(OutcomeStatus.HARNESS_ERROR, ReasonCode.FIXTURE_SETUP, str(exc)), cache_key=cache_key)

    result: dict[str, object] | None = None
    try:
        context = AgentInvocationContext(
            invocation_id=str(uuid4()),
            case_id=case.id,
            case_name=case.name,
            user_input=case.user_input,
            prompt=prompt,
            prompt_injection_method=runner.agent.prompt_injection.method,
            prompt_injection_fingerprint=runner.agent.prompt_injection.implementation_fingerprint,
            fixture_fingerprint=case.fixture,
            workspace_path=workspace.path,
            agent=runner.agent,
            timeout_seconds=timeout_seconds,
            output_mode=runner.agent.runtime.structured_output,
        )
        try:
            invocation = runner.build_invocation(context)
            baseline_prompt_injection(workspace.path, invocation.prompt_injection)
            before = snapshot_files(workspace.path)
        except Exception as exc:
            cache_key = build_cache_key(case, runner.agent, prompt, fixtures_dir=fixtures_dir)
            result = result_cell(case=case, runner=runner, outcome=Outcome(OutcomeStatus.HARNESS_ERROR, ReasonCode.WORKSPACE_SNAPSHOT, str(exc)), cache_key=cache_key, workspace=str(workspace.path))
        if result is None:
            try:
                raw = runner.run(invocation)
                target_evidence = runner.normalize(raw)
                after = snapshot_files(workspace.path)
                changed_files, diff = diff_snapshots(before, after)
                validation = run_harness_validation(case.harness_validation, workspace.path)
                evidence = NormalizedAgentEvidence(
                    target=target_evidence,
                    diff=diff,
                    changed_files=changed_files,
                    harness_validation=validation,
                    workspace=str(workspace.path),
                    prompt_path=str(prompt.path),
                    prompt_text=prompt.path.read_text(),
                    workspace_files=snapshot_text_files(after),
                    **_readme_evidence(prompt),
                )
            except Exception as exc:
                cache_key = build_cache_key(case, runner.agent, prompt, fixtures_dir=fixtures_dir)
                result = result_cell(case=case, runner=runner, outcome=Outcome(OutcomeStatus.HARNESS_ERROR, ReasonCode.ADAPTER_PARSE, str(exc)), cache_key=cache_key, workspace=str(workspace.path))
        if result is None:
            has_complete_structured_evidence = _has_complete_structured_evidence(evidence)
            target_error = str(target_evidence.adapter_diagnostics.get("target_error") or "").strip()
            target_unavailable_message = _target_unavailable_message(
                raw.stdout,
                raw.stderr,
                target_error,
                target_evidence.final_response,
            )
            if raw.timed_out:
                outcome = Outcome(OutcomeStatus.NOT_EVALUATED, ReasonCode.TIMEOUT, "target timed out")
            elif raw.returncode not in (0, None) and _target_unavailable(raw.stdout, raw.stderr) and not has_complete_structured_evidence:
                outcome = Outcome(OutcomeStatus.NOT_EVALUATED, ReasonCode.TARGET_UNAVAILABLE, raw.stderr.strip() or raw.stdout.strip())
            elif target_unavailable_message and _target_unavailable_output_only(target_evidence, changed_files, diff):
                outcome = Outcome(OutcomeStatus.NOT_EVALUATED, ReasonCode.TARGET_UNAVAILABLE, target_unavailable_message)
            elif raw.returncode not in (0, None) and not has_complete_structured_evidence:
                outcome = Outcome(OutcomeStatus.HARNESS_ERROR, ReasonCode.AGENT_PROCESS, f"target exited {raw.returncode}")
            elif target_error and not has_complete_structured_evidence:
                outcome = Outcome(OutcomeStatus.NOT_EVALUATED, ReasonCode.TARGET_UNAVAILABLE, target_error)
            else:
                outcome, deterministic_checks = score_case(case, evidence)
            cache_key = build_cache_key(case, runner.agent, prompt, fixtures_dir=fixtures_dir)
            result = {
                "case_id": case.id,
                "case_name": case.name,
                "case_description": case.description,
                "user_input": case.user_input,
                "ground_truth": list(case.ground_truth),
                "forbidden_behavior": list(case.forbidden_behavior),
                "target_id": runner.id,
                "status": outcome.status.value,
                "reason": outcome.reason.value,
                "message": outcome.message,
                "reused_exact_match": False,
                "changed_files": list(changed_files),
                "diff": diff,
                "final_response": target_evidence.final_response,
                "harness_validation": [item.__dict__ for item in validation],
                "deterministic_checks": list(deterministic_checks) if 'deterministic_checks' in locals() else [],
                "workspace": {"path": str(workspace.path), "fixture": case.fixture},
                "target_usage": target_evidence.target_usage,
                "normalized_evidence": {
                    "final_response": target_evidence.final_response,
                    "timeline": compact_actions(target_evidence.agent_command_events, target_evidence.agent_tool_events),
                    "agent_command_events": list(target_evidence.agent_command_events[:50]),
                    "agent_tool_events": list(target_evidence.agent_tool_events[:50]),
                    "actions": list(target_evidence.agent_actions[:200]),
                    "changed_files": list(changed_files),
                    "workspace_files": _relevant_workspace_files(evidence.workspace_files, tuple(sorted(evidence.workspace_files))),
                    "parse": dict(target_evidence.parse_diagnostics),
                    "adapter_diagnostics": dict(target_evidence.adapter_diagnostics),
                    "prompt_path": str(prompt.path),
                },
                "cache_key": {"digest": cache_key.digest(), **cache_key.__dict__},
                "score_key": build_score_key(case, cache_key.digest()),
                "raw_run": {
                    "duration_seconds": raw.duration_seconds,
                    "timed_out": raw.timed_out,
                    "returncode": raw.returncode,
                    "argv": list(raw.command_argv_redacted),
                    "stdout_truncated": raw.stdout_truncated,
                    "stderr_truncated": raw.stderr_truncated,
                },
            }
    finally:
        try:
            workspace.cleanup()
        except Exception as exc:
            cache_key = build_cache_key(case, runner.agent, prompt, fixtures_dir=fixtures_dir)
            result = result_cell(case=case, runner=runner, outcome=Outcome(OutcomeStatus.HARNESS_ERROR, ReasonCode.CLEANUP, str(exc)), cache_key=cache_key, workspace=str(workspace.path))
    assert result is not None
    return result


def _target_unavailable(stdout: str, stderr: str) -> bool:
    text = f"{stdout}\n{stderr}".lower()
    markers = ("auth", "login", "unauthorized", "forbidden", "model unavailable", "runtime unavailable", "not authenticated", "usage limit", "purchase more credits", "try again at")
    return any(marker in text for marker in markers)


def _target_unavailable_message(*parts: str) -> str:
    for part in parts:
        text = str(part or "").strip()
        if text and _target_unavailable(text, ""):
            return text
    return ""


def _target_unavailable_output_only(evidence: NormalizedTargetEvidence, changed_files: tuple[str, ...], diff: str) -> bool:
    return not changed_files and not diff.strip() and not evidence.agent_command_events


def _has_complete_structured_evidence(evidence: NormalizedAgentEvidence) -> bool:
    valid_events = int(evidence.target.parse_diagnostics.get("valid_events") or 0)
    if valid_events <= 0:
        return False
    return bool(evidence.target.final_response.strip() or evidence.diff.strip() or evidence.changed_files)


def _relevant_workspace_files(files: Mapping[str, str], wanted: tuple[str, ...]) -> dict[str, str]:
    selected = wanted or tuple(sorted(files)[:20])
    return {path: files[path][:12000] for path in selected if path in files}


def _readme_evidence(prompt: PromptArtifact) -> dict[str, object]:
    path = prompt.path.parent / "README.md"
    return {"readme_path": str(path), "readme_text": path.read_text() if path.exists() else ""}

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Mapping

from .adapters import runner_for_agent
from .case_validation import validate_case_set
from .cases import CaseSelection, load_cases, select_cases
from .cells import unavailable_auth_cell, unavailable_target_cell
from .config import load_harness_config
from .deterministic import score_cached_attempts
from .models import PromptArtifact
from .preflight import coding_agent_smoke_preflight, skipped_smoke_preflight
from .progress import print_progress, print_report_summary
from .report_store import load_prior_cells_from_reports, write_prompt_history
from .reporting.json_report import build_result_report
from .reporting.writer import write_report
from .reuse import build_reuse_plan, build_score_key, reused_cell, target_ids_requiring_smoke
from .scheduler import execute_case_target, run_case_first
from .selftest import run_selftests


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the portable prompt behavior gate")
    parser.add_argument("--config", default="evals/eval.yaml")
    parser.add_argument("--cases-file", default="evals/cases.yaml")
    parser.add_argument("--fixtures-dir", default="evals/fixtures")
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--refresh", action="store_true", help="rerun selected cases on every configured target")
    parser.add_argument("--rescore", action="store_true", help="rescore cached agent evidence without preflight or agent execution")
    parser.add_argument("--publish", action="store_true", help="update the tracked report after a complete passing gate")
    parser.add_argument("--confirm-failures", type=_non_negative_int, default=1)
    args = parser.parse_args(argv)
    if args.refresh and not args.case:
        parser.error("--refresh requires at least one --case")
    if args.refresh and args.rescore:
        parser.error("--refresh and --rescore are mutually exclusive")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = load_harness_config(Path(args.config))
    registry = load_cases(Path(args.cases_file))
    validate_case_set(registry.cases, fixtures_dir=Path(args.fixtures_dir))
    selected = select_cases(registry.cases, CaseSelection(ids=tuple(args.case)))
    selftests = run_selftests()
    if not selftests.passed:
        print("harness selftests failed")
        return 2

    prompt = PromptArtifact.from_path(config.prompt_path)
    cache_dir = config.reports_dir / ".cache"
    if args.rescore:
        return _rescore_cached(
            cache_dir=cache_dir, config=config, prompt=prompt, registry=registry,
            selected=selected, selftests=selftests, publish=args.publish,
        )
    prior_cells = {} if args.refresh else load_prior_cells_from_reports(config.reports_dir, prompt.sha256)
    reuse_plan = build_reuse_plan(
        selected,
        config.selected_targets,
        prompt,
        fixtures_dir=Path(args.fixtures_dir),
        prior_cells=prior_cells,
    )
    reuse_by_pair = {(item.case_id, item.target_id): item for item in reuse_plan}
    runners = tuple(runner_for_agent(agent) for agent in config.selected_targets)
    smoke_targets = _smoke_target_ids(reuse_plan, config, preflight_only=args.preflight_only)
    target_preflights = _run_target_preflights(runners, smoke_targets)
    target_unavailable = {
        item.name: item.outcome.message
        for item in target_preflights
        if item.outcome.status == "not_evaluated" and item.outcome.reason == "target_unavailable"
    }
    failed = [item for item in target_preflights if item.outcome.status != "pass" and item.name not in target_unavailable]
    if failed:
        print("; ".join(_preflight_failure_message(item) for item in failed))
        return 2
    if args.preflight_only:
        if target_unavailable:
            print("; ".join(_preflight_failure_message(item) for item in target_preflights if item.name in target_unavailable))
            return 2
        print(f"preflight ok: {len(runners)} target(s), {len(selected)} case(s)")
        return 0

    run_unavailable = dict(target_unavailable)

    def execute_selected(case, runner):
        if runner.agent.auth_unavailable:
            return unavailable_auth_cell(case=case, runner=runner, prompt=prompt, fixtures_dir=Path(args.fixtures_dir))
        if runner.id in run_unavailable:
            return unavailable_target_cell(
                case=case, runner=runner, prompt=prompt, fixtures_dir=Path(args.fixtures_dir),
                message=run_unavailable[runner.id],
            )
        decision = reuse_by_pair[(case.id, runner.id)]
        if decision.reusable:
            return reused_cell(decision, case=case, source_report=config.reports_dir / "current" / "result.json")
        cell = _execute_non_reused_cell(
            case=case, runner=runner, prompt=prompt, fixtures_dir=Path(args.fixtures_dir),
            confirm_failures=args.confirm_failures,
        )
        _mark_run_unavailable(cell, runner.id, run_unavailable)
        return cell

    matrix = run_case_first(
        selected,
        runners,
        execute_selected,
        progress=print_progress,
        cell_checkpoint=lambda cell: write_prompt_history(config.reports_dir, {
            "prompt": {"path": str(prompt.path), "sha256": prompt.sha256},
            "cells": [cell],
        }),
    )
    report = build_result_report(
        prompt=prompt,
        selftests=selftests,
        preflights={"targets": target_preflights},
        cases=selected,
        targets=config.selected_targets,
        cells=[cell.result for cell in matrix],
        required_cases=registry.cases,
    )
    write_report(cache_dir / "current", report)
    write_prompt_history(config.reports_dir, report)
    allowed = bool(report.get("promotion", {}).get("allowed"))
    if args.publish and allowed:
        write_report(config.reports_dir / "current", report, public=True)
    elif args.publish:
        print("publish blocked: complete passing coverage is required")
    print_report_summary(report)
    print(f"wrote local report: {cache_dir / 'current'}")
    if args.publish and allowed:
        print(f"published report: {config.reports_dir / 'current'}")
    return 0 if allowed else 1


def _execute_non_reused_cell(*, case, runner, prompt, fixtures_dir: Path, confirm_failures: int):
    attempts = []
    attempt_cells = []
    max_attempts = 1 + confirm_failures
    for attempt in range(1, max_attempts + 1):
        cell = execute_case_target(
            case=case, runner=runner, prompt=prompt, fixtures_dir=fixtures_dir,
            timeout_seconds=runner.agent.timeout_seconds,
        )
        attempt_cells.append(dict(cell))
        attempts.append(_attempt_summary(attempt, cell))
        if not _retryable_cell(cell) or attempt == max_attempts:
            if len(attempts) > 1:
                cell = dict(cell)
                cell["confirmation"] = {
                    "enabled": True,
                    "max_attempts": max_attempts,
                    "attempt_count": len(attempts),
                    "attempts": attempts,
                    "primary_status": attempts[0]["status"],
                    "final_status": cell.get("status"),
                    "flaky_pass_after_retry": attempts[0]["status"] != "pass" and cell.get("status") == "pass",
                    "confirmed_failed": cell.get("status") != "pass",
                }
                cell["attempt_cells"] = attempt_cells
            return cell
    raise AssertionError("unreachable retry loop exit")


def _rescore_cached(*, cache_dir: Path, config, prompt, registry, selected, selftests, publish: bool) -> int:
    prior = load_prior_cells_from_reports(config.reports_dir, prompt.sha256)
    if not prior:
        print(f"cached evidence not found for prompt: {prompt.sha256}")
        return 2
    selected_ids = {case.id for case in selected}
    cases = registry.by_id()
    cells = []
    for case in registry.cases:
        for target in config.selected_targets:
            cached = prior.get((case.id, target.id))
            if not cached or not isinstance(cached.get("cell"), Mapping):
                continue
            cell = dict(cached["cell"])
            case_id = case.id
            if case_id in selected_ids:
                outcome, checks, passing_attempt = score_cached_attempts(cases[case_id], cell)
                cell["status"] = outcome.status.value
                cell["reason"] = outcome.reason.value
                cell["message"] = outcome.message
                cell["deterministic_checks"] = list(checks)
                cell["scored_attempt"] = passing_attempt
                cache_key = cell.get("cache_key") if isinstance(cell.get("cache_key"), Mapping) else {}
                evidence_digest = str(cache_key.get("digest") or "")
                cell["score_key"] = build_score_key(cases[case_id], evidence_digest)
                cell["rescored_from_cache"] = True
                print(f"rescored: {cell.get('target_id')}/{case_id} ({cell['status']})", flush=True)
            cells.append(cell)
    report = build_result_report(
        prompt=prompt, selftests=selftests, preflights={},
        cases=registry.cases, targets=config.selected_targets, cells=cells, required_cases=registry.cases,
    )
    write_report(cache_dir / "current", report)
    write_prompt_history(config.reports_dir, report)
    allowed = bool(report.get("promotion", {}).get("allowed"))
    if publish and allowed:
        write_report(config.reports_dir / "current", report, public=True)
    elif publish:
        print("publish blocked: complete passing coverage is required")
    print_report_summary(report)
    return 0 if allowed else 1


def _retryable_cell(cell: Mapping[str, Any]) -> bool:
    return cell.get("status") == "fail" or (cell.get("status") == "not_evaluated" and cell.get("reason") == "timeout")


def _mark_run_unavailable(cell: Mapping[str, Any], target_id: str, unavailable: dict[str, str]) -> None:
    if cell.get("status") == "not_evaluated" and cell.get("reason") in {"target_unavailable", "timeout"}:
        unavailable[target_id] = str(cell.get("message") or f"target unavailable after {cell.get('reason')}")


def _attempt_summary(attempt: int, cell: Mapping[str, Any]) -> dict[str, object]:
    return {"attempt": attempt, "status": cell.get("status"), "reason": cell.get("reason"), "message": cell.get("message")}


def _target_smoke_preflight(runner, smoke_targets: set[str]):
    if runner.agent.auth_unavailable:
        return skipped_smoke_preflight(runner.agent, reason=f"target_auth_unavailable:{runner.agent.auth_mode}")
    if runner.id in smoke_targets:
        return coding_agent_smoke_preflight(runner, timeout_seconds=runner.agent.timeout_seconds)
    return skipped_smoke_preflight(runner.agent, reason="all_selected_cells_reused")


def _run_target_preflights(runners, smoke_targets: set[str]):
    results = {}
    with ThreadPoolExecutor(max_workers=max(1, len(runners))) as executor:
        futures = {executor.submit(_target_smoke_preflight, runner, smoke_targets): runner.id for runner in runners}
        for future in as_completed(futures):
            target_id = futures[future]
            results[target_id] = future.result()
            print(f"preflight target complete: {target_id} ({results[target_id].outcome.status.value})", flush=True)
    return [results[runner.id] for runner in runners]


def _smoke_target_ids(reuse_plan, config, *, preflight_only: bool) -> set[str]:
    unavailable = {agent.id for agent in config.selected_targets if agent.auth_unavailable}
    if preflight_only:
        return {agent.id for agent in config.selected_targets} - unavailable
    return set(target_ids_requiring_smoke(reuse_plan)) - unavailable


def _preflight_failure_message(item) -> str:
    diagnostics = item.diagnostics if isinstance(item.diagnostics, dict) else {}
    model = diagnostics.get("model")
    model_text = "/".join(str(model.get(part, "")) for part in ("provider", "model") if model.get(part)) if isinstance(model, dict) else str(model or "unknown-model")
    pieces = [f"target={item.name}", f"runtime={diagnostics.get('runtime', 'unknown-runtime')}", f"model={model_text}", f"reason={item.outcome.reason.value}"]
    if diagnostics.get("failed_check"):
        pieces.append(f"failed_check={diagnostics['failed_check']}")
    if item.outcome.message.strip():
        pieces.append(f"message={item.outcome.message.strip()}")
    return " ".join(pieces)


def _non_negative_int(value: Any) -> int:
    try:
        parsed = int(str(value))
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected non-negative integer, got {value!r}") from None
    if parsed < 0:
        raise argparse.ArgumentTypeError(f"expected non-negative integer, got {value!r}")
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())

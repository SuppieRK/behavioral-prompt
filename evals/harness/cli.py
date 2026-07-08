from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping

from .adapters import runner_for_agent
from .case_validation import validate_case_set
from .cases import CaseSelection, load_python_cases, select_cases
from .cells import unavailable_auth_cell
from .config import load_harness_config
from .judge import configured_judge_runner
from .models import PromptArtifact
from .preflight import coding_agent_smoke_preflight, docker_preflight, skipped_docker_preflight, skipped_smoke_preflight
from .progress import print_progress, print_report_summary
from .reporting.json_report import build_result_report
from .reporting.writer import write_report
from .reuse import build_reuse_plan, load_prior_cells, reused_cell, target_ids_requiring_smoke
from .scheduler import execute_case_target, run_case_first
from .selftest import SELFTEST_CONTRACT_VERSION, run_selftests


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="evals/eval.yaml")
    parser.add_argument("--cases-dir", default="evals/cases")
    parser.add_argument("--fixtures-dir", default="evals/fixtures")
    parser.add_argument("--target", "--target-name", dest="target", action="append", default=[])
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--category")
    parser.add_argument("--tag")
    parser.add_argument("--path")
    parser.add_argument("--critical", nargs="?", const=True, default=None, type=_optional_bool)
    parser.add_argument("--preflight-only", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = load_harness_config(Path(args.config), target_names=tuple(args.target))
    registry = load_python_cases(Path(args.cases_dir))
    validate_case_set(registry.cases, fixtures_dir=Path(args.fixtures_dir))
    selected = select_cases(registry.cases, _case_selection_from_args(args, config.raw))
    selftests = run_selftests()
    if not selftests.passed:
        print("harness selftests failed")
        return 2
    prompt = PromptArtifact.from_path(config.prompt_path)
    report_dir = config.reports_dir / "current"
    source_report = report_dir / "result.json"
    prior_cells = load_prior_cells(source_report)
    reuse_plan = build_reuse_plan(selected, tuple(config.selected_targets), prompt, fixtures_dir=Path(args.fixtures_dir), prior_cells=prior_cells, judge_config=config.judge.to_fingerprint_data())
    reuse_by_pair = {(decision.case_id, decision.target_id): decision for decision in reuse_plan}
    docker = docker_preflight() if _requires_docker(selected, reuse_plan, config, preflight_only=args.preflight_only) else skipped_docker_preflight(reason="no_non_reused_docker_judge_cells")
    if docker.outcome.status != "pass":
        print(docker.outcome.message)
        return 2
    judge_runner = configured_judge_runner(config.judge)
    smoke_targets = _smoke_target_ids(reuse_plan, config, preflight_only=args.preflight_only)
    runners = tuple(runner_for_agent(agent) for agent in config.selected_targets)
    target_preflights = [
        _target_smoke_preflight(runner, smoke_targets)
        for runner in runners
    ]
    failed = [item for item in target_preflights if item.outcome.status != "pass"]
    if failed:
        print("; ".join(_preflight_failure_message(item) for item in failed))
        return 2
    if args.preflight_only:
        print(f"preflight ok: {len(config.selected_targets)} target(s), {len(selected)} case(s)")
        return 0
    matrix = run_case_first(
        selected,
        runners,
        lambda case, runner: unavailable_auth_cell(
            case=case,
            runner=runner,
            prompt=prompt,
            fixtures_dir=Path(args.fixtures_dir),
            judge_config=config.judge.to_fingerprint_data(),
        )
        if runner.agent.auth_unavailable
        else reused_cell(reuse_by_pair[(case.id, runner.id)], source_report=source_report)
        if reuse_by_pair[(case.id, runner.id)].reusable
        else _execute_non_reused_cell(
            case=case,
            runner=runner,
            prompt=prompt,
            fixtures_dir=Path(args.fixtures_dir),
            judge_runner=judge_runner,
            judge_config=config.judge.to_fingerprint_data(),
        ),
        progress=print_progress,
    )
    cells = [cell.result for cell in matrix]
    report = build_result_report(
        prompt=prompt,
        selftests=selftests,
        preflights={"docker": docker, "targets": target_preflights},
        cases=selected,
        targets=tuple(config.selected_targets),
        cells=cells,
        required_cases=registry.cases,
    )
    write_report(config.reports_dir / "current", report)
    print_report_summary(report)
    print(f"wrote report: {config.reports_dir / 'current'}")
    return 0 if report.get("promotion", {}).get("allowed") else 1


def _target_smoke_preflight(runner, smoke_targets: set[str]):
    if runner.agent.auth_unavailable:
        mode = runner.agent.auth_mode.strip() or "unknown"
        return skipped_smoke_preflight(runner.agent, reason=f"target_auth_unavailable:{mode}")
    if runner.id in smoke_targets:
        return coding_agent_smoke_preflight(runner)
    return skipped_smoke_preflight(runner.agent, reason="all_selected_cells_reused")


def _smoke_target_ids(reuse_plan, config, *, preflight_only: bool) -> set[str]:
    unavailable = {agent.id for agent in config.selected_targets if agent.auth_unavailable}
    if preflight_only:
        return {agent.id for agent in config.selected_targets} - unavailable
    return set(target_ids_requiring_smoke(reuse_plan)) - unavailable


def _preflight_failure_message(item) -> str:
    diagnostics = item.diagnostics if isinstance(item.diagnostics, dict) else {}
    model = diagnostics.get("model")
    if isinstance(model, dict):
        model_text = "/".join(str(model.get(part, "")) for part in ("provider", "model") if model.get(part))
    else:
        model_text = str(model or "unknown-model")
    pieces = [
        f"target={item.name}",
        f"runtime={diagnostics.get('runtime', 'unknown-runtime')}",
        f"model={model_text}",
        f"reason={item.outcome.reason.value}",
    ]
    failed_check = diagnostics.get("failed_check")
    if failed_check:
        pieces.append(f"failed_check={failed_check}")
    message = item.outcome.message.strip()
    if message:
        pieces.append(f"message={message}")
    return " ".join(pieces)


def _execute_non_reused_cell(*, case, runner, prompt, fixtures_dir: Path, judge_runner, judge_config):
    return execute_case_target(
        case=case,
        runner=runner,
        prompt=prompt,
        fixtures_dir=fixtures_dir,
        timeout_seconds=runner.agent.timeout_seconds,
        judge_runner=judge_runner,
        judge_config=judge_config,
    )


def _case_selection_from_args(args: argparse.Namespace, raw_config: Mapping[str, Any]) -> CaseSelection:
    if args.case or args.category or args.tag or args.path or args.critical is not None:
        return CaseSelection(
            ids=tuple(args.case),
            category=args.category,
            tag=args.tag,
            path=args.path,
            critical=args.critical,
        )
    configured = raw_config.get("selection", {})
    selection = configured if isinstance(configured, Mapping) else {}
    config_cases = _selection_cases(selection.get("case"))
    config_critical = _selection_critical(selection.get("critical"))
    return CaseSelection(
        ids=config_cases,
        category=_selection_string(selection.get("category")),
        tag=_selection_string(selection.get("tag")),
        path=_selection_string(selection.get("path")),
        critical=config_critical,
    )


def _selection_cases(value: Any) -> tuple[str, ...]:
    if value in (None, ""):
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return (str(value).strip(),)


def _selection_string(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    return text or None


def _selection_critical(value: Any) -> bool | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return value
    lowered = str(value).strip().lower()
    if lowered in {"true", "yes", "1"}:
        return True
    if lowered in {"false", "no", "0"}:
        return False
    return None


def _optional_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    lowered = str(value).strip().lower()
    if lowered in {"true", "yes", "1"}:
        return True
    if lowered in {"false", "no", "0"}:
        return False
    raise argparse.ArgumentTypeError(f"expected boolean value, got {value!r}")


def _requires_docker(cases, reuse_plan, config, *, preflight_only: bool = False) -> bool:
    if not config.judge.requires_docker:
        return False
    if preflight_only:
        return any(case.judge for case in cases) and any(not agent.auth_unavailable for agent in config.selected_targets)
    case_by_id = {case.id: case for case in cases}
    agent_by_id = {agent.id: agent for agent in config.selected_targets}
    return any(
        case_by_id[decision.case_id].judge
        and not decision.reusable
        and not agent_by_id[decision.target_id].auth_unavailable
        for decision in reuse_plan
    )


if __name__ == "__main__":
    raise SystemExit(main())

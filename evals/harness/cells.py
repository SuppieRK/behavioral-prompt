from __future__ import annotations

from pathlib import Path
from typing import Mapping

from .adapters.base import CodingAgentRunner
from .models import EvalCase, PromptArtifact
from .outcomes import Outcome, OutcomeStatus, ReasonCode
from .reuse import build_cache_key


def result_cell(*, case: EvalCase, runner: CodingAgentRunner, outcome: Outcome, cache_key, workspace: str | None = None) -> dict[str, object]:
    return {
        "case_id": case.id,
        "case_name": case.name,
        "case_description": case.description,
        "user_input": case.user_input,
        "ground_truth": list(case.ground_truth),
        "target_id": runner.id,
        "status": outcome.status.value,
        "reason": outcome.reason.value,
        "message": outcome.message,
        "reused_exact_match": False,
        "changed_files": [],
        "diff": "",
        "final_response": "",
        "deterministic_checks": [],
        "harness_validation": [],
        "judge": None,
        "workspace": {"path": workspace, "fixture": case.fixture},
        "target_usage": {},
        "normalized_evidence": {},
        "cache_key": {"digest": cache_key.digest(), **cache_key.__dict__},
        "raw_run": None,
    }


def unavailable_auth_cell(*, case: EvalCase, runner: CodingAgentRunner, prompt: PromptArtifact, fixtures_dir: Path, judge_config: Mapping[str, object] | None = None) -> dict[str, object]:
    cache_key = build_cache_key(case, runner.agent, prompt, fixtures_dir=fixtures_dir, judge_config=judge_config)
    mode = runner.agent.auth_mode.strip() or "unknown"
    return result_cell(case=case, runner=runner, outcome=Outcome(OutcomeStatus.NOT_EVALUATED, ReasonCode.TARGET_UNAVAILABLE, f"target auth unavailable: {mode}"), cache_key=cache_key)

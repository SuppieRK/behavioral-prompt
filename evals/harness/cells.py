from __future__ import annotations

from pathlib import Path

from .adapters.base import CodingAgentRunner
from .models import EvalCase, PromptArtifact
from .outcomes import Outcome, OutcomeStatus, ReasonCode
from .reuse import build_cache_key, build_score_key


def result_cell(*, case: EvalCase, runner: CodingAgentRunner, outcome: Outcome, cache_key, workspace: str | None = None) -> dict[str, object]:
    return {
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
        "changed_files": [],
        "diff": "",
        "final_response": "",
        "harness_validation": [],
        "workspace": {"path": workspace, "fixture": case.fixture},
        "target_usage": {},
        "normalized_evidence": {},
        "cache_key": {"digest": cache_key.digest(), **cache_key.__dict__},
        "score_key": build_score_key(case, cache_key.digest()),
        "raw_run": None,
    }


def unavailable_auth_cell(*, case: EvalCase, runner: CodingAgentRunner, prompt: PromptArtifact, fixtures_dir: Path) -> dict[str, object]:
    cache_key = build_cache_key(case, runner.agent, prompt, fixtures_dir=fixtures_dir)
    mode = runner.agent.auth_mode.strip() or "unknown"
    return result_cell(case=case, runner=runner, outcome=Outcome(OutcomeStatus.NOT_EVALUATED, ReasonCode.TARGET_UNAVAILABLE, f"target auth unavailable: {mode}"), cache_key=cache_key)


def unavailable_target_cell(*, case: EvalCase, runner: CodingAgentRunner, prompt: PromptArtifact, fixtures_dir: Path, message: str) -> dict[str, object]:
    cache_key = build_cache_key(case, runner.agent, prompt, fixtures_dir=fixtures_dir)
    return result_cell(case=case, runner=runner, outcome=Outcome(OutcomeStatus.NOT_EVALUATED, ReasonCode.TARGET_UNAVAILABLE, message), cache_key=cache_key)

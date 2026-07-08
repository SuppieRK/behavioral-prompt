from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .capabilities import BEST_EFFORT_DIAGNOSTIC_EVIDENCE
from .core import HarnessContractError
from .evidence import NormalizedAgentEvidence
from .models import EvalCase
from .outcomes import Outcome, OutcomeStatus, ReasonCode


def check(name: str, passed: bool, pass_reason: str, fail_reason: str) -> dict[str, object]:
    return {"name": name, "pass": passed, "reason": pass_reason if passed else fail_reason}


class ScorerAuthoringError(Exception):
    pass


@dataclass(frozen=True)
class ScorerContext:
    case: EvalCase
    evidence: NormalizedAgentEvidence
    allowed: frozenset[str]

    def require(self, name: str) -> Any:
        if name not in self.allowed:
            raise HarnessContractError(f"scorer attempted undeclared evidence access: {name}")
        if name == "diff":
            return self.evidence.diff
        if name == "changed_files":
            return self.evidence.changed_files
        if name == "final_response":
            return self.evidence.target.final_response
        if name == "harness_validation.success_status":
            return bool(self.evidence.harness_validation) and all(result.exit_status == "success" for result in self.evidence.harness_validation)
        if name == "harness_validation":
            return self.evidence.harness_validation
        if name == "agent_command_events":
            return self.evidence.target.agent_command_events
        if name == "agent_tool_events":
            return self.evidence.target.agent_tool_events
        if name == "transcript":
            return self.evidence.target.transcript
        if name == "prompt_path":
            return self.evidence.prompt_path
        if name == "prompt_text":
            return self.evidence.prompt_text
        if name == "workspace_files":
            return self.evidence.workspace_files
        if name == "readme_path":
            return self.evidence.readme_path
        if name == "readme_text":
            return self.evidence.readme_text
        raise HarnessContractError(f"unknown evidence field: {name}")


def run_deterministic_scorer(case: EvalCase, evidence: NormalizedAgentEvidence) -> tuple[Outcome, tuple[dict[str, object], ...]]:
    if case.scorer is None:
        return Outcome(OutcomeStatus.PASS), ()
    declared = frozenset(case.scorer_evidence_dependencies)
    missing = sorted(set(declared) - set(case.required_evidence) - BEST_EFFORT_DIAGNOSTIC_EVIDENCE)
    if missing:
        return Outcome(OutcomeStatus.HARNESS_ERROR, ReasonCode.REQUIRED_EVIDENCE_UNAVAILABLE, f"undeclared required evidence: {', '.join(missing)}"), ()
    try:
        checks = tuple(case.scorer(ScorerContext(case, evidence, declared)))
    except ScorerAuthoringError as exc:
        return Outcome(OutcomeStatus.HARNESS_ERROR, ReasonCode.SCORER_EXCEPTION, str(exc)), ()
    except HarnessContractError:
        raise
    except Exception as exc:
        return Outcome(OutcomeStatus.HARNESS_ERROR, ReasonCode.SCORER_EXCEPTION, str(exc)), ()
    if not checks and not case.judge:
        return Outcome(OutcomeStatus.HARNESS_ERROR, ReasonCode.SCORER_EXCEPTION, "deterministic scorer produced no checks"), ()
    return Outcome(OutcomeStatus.PASS if all(bool(item.get("pass")) for item in checks) else OutcomeStatus.FAIL), checks


def provided_evidence_capabilities(evidence: NormalizedAgentEvidence) -> frozenset[str]:
    provided = {"diff", "changed_files", "process_status", "workspace_diff"}
    if evidence.target.final_response is not None:
        provided.add("final_response")
    if evidence.harness_validation is not None:
        provided.add("harness_validation")
        provided.add("harness_validation.success_status")
    if evidence.target.target_usage is not None:
        provided.add("target_usage")
    if evidence.prompt_path is not None:
        provided.add("prompt_path")
    if evidence.prompt_text is not None:
        provided.add("prompt_text")
    if evidence.workspace_files is not None:
        provided.add("workspace_files")
    if evidence.readme_path is not None:
        provided.add("readme_path")
    if evidence.readme_text is not None:
        provided.add("readme_text")
    provided.update(str(name) for name in evidence.target.provided_capabilities)
    return frozenset(provided)


def missing_required_evidence(case: EvalCase, evidence: NormalizedAgentEvidence) -> tuple[str, ...]:
    provided = provided_evidence_capabilities(evidence)
    return tuple(name for name in case.required_evidence if name not in provided)

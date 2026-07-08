from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class OutcomeStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    NOT_EVALUATED = "not_evaluated"
    HARNESS_ERROR = "harness_error"


class ReasonCode(StrEnum):
    NONE = ""
    DOCKER_UNAVAILABLE = "docker_unavailable"
    CODING_AGENT_UNAVAILABLE = "coding_agent_unavailable"
    TARGET_UNAVAILABLE = "target_unavailable"
    TIMEOUT = "timeout"
    REQUIRED_EVIDENCE_UNAVAILABLE = "required_evidence_unavailable"
    ADAPTER_PARSE = "adapter_parse"
    AGENT_PROCESS = "agent_process"
    FIXTURE_SETUP = "fixture_setup"
    WORKSPACE_SNAPSHOT = "workspace_snapshot"
    CLEANUP = "workspace_cleanup"
    SCORER_EXCEPTION = "scorer_exception"
    JUDGE_UNAVAILABLE = "judge_unavailable"
    REPORT_GENERATION = "report_generation"


@dataclass(frozen=True)
class Outcome:
    status: OutcomeStatus
    reason: ReasonCode = ReasonCode.NONE
    message: str = ""

    @property
    def is_promotion_blocking(self) -> bool:
        return self.status in {OutcomeStatus.FAIL, OutcomeStatus.NOT_EVALUATED, OutcomeStatus.HARNESS_ERROR}


def promotion_allowed(outcomes: list[Outcome], *, selftests_passed: bool) -> bool:
    return selftests_passed and all(not outcome.is_promotion_blocking for outcome in outcomes)

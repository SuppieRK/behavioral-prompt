from __future__ import annotations

from .adapters.base import CodingAgentRunner
from .evidence import NormalizedTargetEvidence, RawAgentRun
from .models import AgentInvocationContext


def run_target(runner: CodingAgentRunner, context: AgentInvocationContext) -> tuple[RawAgentRun, NormalizedTargetEvidence]:
    invocation = runner.build_invocation(context)
    raw = runner.run(invocation)
    return raw, runner.normalize(raw)

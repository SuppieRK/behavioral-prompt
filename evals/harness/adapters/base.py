from __future__ import annotations

from typing import Protocol

from ..evidence import NormalizedTargetEvidence, RawAgentRun
from ..models import AgentInvocation, AgentInvocationContext, CodingAgent


class CodingAgentRunner(Protocol):
    id: str
    agent: CodingAgent

    def build_invocation(self, context: AgentInvocationContext) -> AgentInvocation:
        ...

    def fingerprint(self) -> str:
        ...

    def run(self, invocation: AgentInvocation) -> RawAgentRun:
        ...

    def normalize(self, raw: RawAgentRun) -> NormalizedTargetEvidence:
        ...

from __future__ import annotations

import shutil

from ..evidence import NormalizedTargetEvidence, RawAgentRun
from ..isolation import seed_pi_state
from ..models import AgentInvocation, AgentInvocationContext, CodingAgent
from ..process import run_process
from ..prompt_injection import append_system_prompt_metadata
from .jsonish import normalize_jsonish_output


class PiRunner:
    def __init__(self, agent: CodingAgent):
        self.id = agent.id
        self.agent = agent

    def build_invocation(self, context: AgentInvocationContext) -> AgentInvocation:
        executable = shutil.which("pi") or "pi"
        argv = [executable, "--mode", "json", "--print", "--no-session", "--append-system-prompt", str(context.prompt.path)]
        argv.extend(["--model", f"{context.agent.model.provider}/{context.agent.model.model}"])
        if context.agent.model.reasoning:
            argv.extend(["--thinking", context.agent.model.reasoning])
        argv.append(context.user_input)
        isolation = seed_pi_state(context.workspace_path.parent)
        return AgentInvocation(
            invocation_id=context.invocation_id,
            case_id=context.case_id,
            target_id=self.id,
            argv=tuple(argv),
            cwd=context.workspace_path,
            env={"PI_CODING_AGENT_DIR": str(context.workspace_path.parent / "pi-agent")},
            env_summary_redacted={"PI_CODING_AGENT_DIR": str(context.workspace_path.parent / "pi-agent")},
            prompt_injection=append_system_prompt_metadata(context.prompt.path),
            isolation=isolation,
            timeout_seconds=context.timeout_seconds,
        )

    def fingerprint(self) -> str:
        return self.agent.fingerprint

    def run(self, invocation: AgentInvocation) -> RawAgentRun:
        return run_process(invocation)

    def normalize(self, raw: RawAgentRun) -> NormalizedTargetEvidence:
        return normalize_jsonish_output(raw.stdout)

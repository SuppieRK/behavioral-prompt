from __future__ import annotations

import shutil

from .pi import normalize_jsonish_output
from ..evidence import NormalizedTargetEvidence, RawAgentRun
from ..isolation import seed_codex_state
from ..models import AgentInvocation, AgentInvocationContext, CodingAgent
from ..process import run_process
from ..prompt_injection import install_agents_file


class CodexRunner:
    def __init__(self, agent: CodingAgent):
        self.id = agent.id
        self.agent = agent
        self.capabilities = agent.capabilities

    def build_invocation(self, context: AgentInvocationContext) -> AgentInvocation:
        executable = shutil.which("codex") or "codex"
        prompt_injection = install_agents_file(context.workspace_path, context.prompt.path)
        isolation = seed_codex_state(context.workspace_path.parent)
        argv = [
            executable,
            "exec",
            "--json",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--sandbox",
            "workspace-write",
            "-c",
            'approval_policy="never"',
            "-C",
            str(context.workspace_path),
            "--model",
            context.agent.model.model,
        ]
        if context.agent.model.reasoning:
            argv.extend(["-c", f'model_reasoning_effort="{context.agent.model.reasoning}"'])
        argv.append(context.user_input)
        env = {"CODEX_HOME": str(context.workspace_path.parent / "codex-home")}
        return AgentInvocation(
            invocation_id=context.invocation_id,
            case_id=context.case_id,
            target_id=self.id,
            argv=tuple(argv),
            cwd=context.workspace_path,
            env=env,
            env_summary_redacted=env,
            prompt_injection=prompt_injection,
            isolation=isolation,
            timeout_seconds=context.timeout_seconds,
        )

    def fingerprint(self) -> str:
        return self.agent.fingerprint

    def run(self, invocation: AgentInvocation) -> RawAgentRun:
        return run_process(invocation)

    def normalize(self, raw: RawAgentRun) -> NormalizedTargetEvidence:
        return normalize_jsonish_output(raw.stdout)

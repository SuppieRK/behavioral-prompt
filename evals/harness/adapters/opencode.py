from __future__ import annotations

import shutil

from .pi import normalize_jsonish_output
from ..evidence import NormalizedTargetEvidence, RawAgentRun
from ..isolation import seed_opencode_state
from ..models import AgentInvocation, AgentInvocationContext, CodingAgent
from ..process import run_process
from ..prompt_injection import install_agents_file


class OpenCodeRunner:
    def __init__(self, agent: CodingAgent):
        self.id = agent.id
        self.agent = agent
        self.capabilities = agent.capabilities

    def build_invocation(self, context: AgentInvocationContext) -> AgentInvocation:
        executable = shutil.which("opencode") or "opencode"
        prompt_injection = install_agents_file(context.workspace_path, context.prompt.path)
        isolation = seed_opencode_state(context.workspace_path.parent)
        argv = [executable, "run", "--format", "json", "--pure", "--dir", str(context.workspace_path), "--model", f"{context.agent.model.provider}/{context.agent.model.model}"]
        if context.agent.model.reasoning:
            argv.extend(["--variant", context.agent.model.reasoning])
        argv.append(context.user_input)
        env = {
            "XDG_CONFIG_HOME": str(context.workspace_path.parent / "opencode-config"),
            "XDG_DATA_HOME": str(context.workspace_path.parent / "opencode-data"),
            "OPENCODE_DISABLE_PLUGINS": "true",
        }
        env_unset = ("OPENCODE_CONFIG", "OPENCODE_CONFIG_CONTENT", "OPENCODE_TUI_CONFIG")
        return AgentInvocation(
            invocation_id=context.invocation_id,
            case_id=context.case_id,
            target_id=self.id,
            argv=tuple(argv),
            cwd=context.workspace_path,
            env=env,
            env_summary_redacted={**env, "cleared": env_unset},
            prompt_injection=prompt_injection,
            isolation=isolation,
            timeout_seconds=context.timeout_seconds,
            env_unset=env_unset,
        )

    def fingerprint(self) -> str:
        return self.agent.fingerprint

    def run(self, invocation: AgentInvocation) -> RawAgentRun:
        return run_process(invocation)

    def normalize(self, raw: RawAgentRun) -> NormalizedTargetEvidence:
        return normalize_jsonish_output(raw.stdout)

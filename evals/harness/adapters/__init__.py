"""Built-in coding-agent adapters."""

from .codex import CodexRunner
from .opencode import OpenCodeRunner
from .pi import PiRunner


def runner_for_agent(agent):
    runtime = agent.runtime.name
    if runtime == "pi":
        return PiRunner(agent)
    if runtime == "opencode":
        return OpenCodeRunner(agent)
    if runtime == "codex":
        return CodexRunner(agent)
    raise ValueError(f"unsupported coding-agent runtime: {runtime}")

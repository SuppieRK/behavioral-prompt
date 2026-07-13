from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping



@dataclass(frozen=True)
class TargetUsage:
    input_tokens_reported: int | None = None
    cached_input_tokens: int | None = None
    uncached_input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_tokens: int | None = None
    total_tokens_reported: int | None = None
    uncached_total_tokens: int | None = None
    actual_tokens_spent: int | None = None
    avoided_tokens_by_reuse: int | None = None


@dataclass(frozen=True)
class RawAgentRun:
    invocation_id: str
    case_id: str
    target_id: str
    command_argv_redacted: tuple[str, ...]
    cwd: str
    env_summary_redacted: Mapping[str, object]
    started_at: str
    finished_at: str
    duration_seconds: float
    timed_out: bool
    returncode: int | None
    stdout: str
    stderr: str
    stdout_truncated: bool = False
    stderr_truncated: bool = False
    prompt_injection: Mapping[str, object] = field(default_factory=dict)
    isolation: Mapping[str, object] = field(default_factory=dict)
    raw_usage: Mapping[str, object] = field(default_factory=dict)
    diagnostics: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class NormalizedTargetEvidence:
    transcript: tuple[Mapping[str, object], ...] = ()
    final_response: str = ""
    agent_events: tuple[Mapping[str, object], ...] = ()
    agent_tool_events: tuple[Mapping[str, object], ...] = ()
    agent_command_events: tuple[Mapping[str, object], ...] = ()
    agent_actions: tuple[Mapping[str, object], ...] = ()
    parse_diagnostics: Mapping[str, object] = field(default_factory=dict)
    path_diagnostics: tuple[Mapping[str, object], ...] = ()
    target_usage: TargetUsage = field(default_factory=TargetUsage)
    adapter_diagnostics: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class HarnessValidationResult:
    id: str
    command: str
    cwd: str
    exit_status: str
    exit_code: int
    stdout_excerpt: str
    stderr_excerpt: str
    duration_seconds: float


@dataclass(frozen=True)
class NormalizedAgentEvidence:
    target: NormalizedTargetEvidence
    diff: str
    changed_files: tuple[str, ...]
    harness_validation: tuple[HarnessValidationResult, ...] = ()
    workspace: str | None = None
    prompt_path: str | None = None
    prompt_text: str | None = None
    workspace_files: Mapping[str, str] = field(default_factory=dict)
    readme_path: str | None = None
    readme_text: str | None = None

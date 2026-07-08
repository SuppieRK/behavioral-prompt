from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from .capabilities import CapabilityMatrix, CapabilityStatus
from .core import HarnessContractError
from .models import CodingAgent, CodingAgentRuntime, IsolationStrategy, LLMModel, PromptInjectionStrategy


COMMON_CAPABILITIES = CapabilityMatrix({
    "structured_events": CapabilityStatus.SUPPORTED,
    "final_response": CapabilityStatus.SUPPORTED,
    "process_status": CapabilityStatus.SUPPORTED,
    "diff": CapabilityStatus.SUPPORTED,
    "workspace_diff": CapabilityStatus.SUPPORTED,
    "changed_files": CapabilityStatus.SUPPORTED,
    "harness_validation": CapabilityStatus.SUPPORTED,
    "harness_validation.success_status": CapabilityStatus.SUPPORTED,
    "prompt_path": CapabilityStatus.SUPPORTED,
    "prompt_text": CapabilityStatus.SUPPORTED,
    "workspace_files": CapabilityStatus.SUPPORTED,
    "readme_path": CapabilityStatus.SUPPORTED,
    "readme_text": CapabilityStatus.SUPPORTED,
    "target_usage": CapabilityStatus.SUPPORTED,
    "agent_tool_events": CapabilityStatus.BEST_EFFORT,
    "agent_command_events": CapabilityStatus.BEST_EFFORT,
})


@dataclass(frozen=True)
class JudgeConfig:
    enabled: bool
    backend: str
    model: str
    timeout_seconds: int
    retry_attempts: int
    retry_backoff_seconds: float

    @property
    def requires_docker(self) -> bool:
        return self.enabled and self.backend == "docker-model-runner"

    def to_fingerprint_data(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "backend": self.backend,
            "model": self.model,
            "timeout_seconds": self.timeout_seconds,
            "retry_attempts": self.retry_attempts,
        }


@dataclass(frozen=True)
class HarnessConfig:
    path: Path
    prompt_path: Path
    reports_dir: Path
    judge: JudgeConfig
    selected_targets: tuple[CodingAgent, ...]
    raw: Mapping[str, Any]


def load_yaml_config(path: Path) -> Mapping[str, Any]:
    if not path.exists():
        raise HarnessContractError(f"config file does not exist: {path}")
    data = yaml.safe_load(path.read_text()) or {}
    if not isinstance(data, dict):
        raise HarnessContractError(f"config root must be a mapping: {path}")
    return data


def load_harness_config(path: Path, *, target_names: tuple[str, ...] = ()) -> HarnessConfig:
    raw = load_yaml_config(path)
    prompt_value = _nested(raw, ("prompt", "candidate"), "PROMPT.md")
    reports_value = _nested(raw, ("reports", "dir"), "evals/reports")
    targets = build_selected_agents(raw, target_names=target_names)
    return HarnessConfig(
        path=path,
        prompt_path=Path(str(prompt_value)),
        reports_dir=Path(str(reports_value)),
        judge=build_judge_config(raw),
        selected_targets=targets,
        raw=raw,
    )


def build_judge_config(raw: Mapping[str, Any]) -> JudgeConfig:
    judge = raw.get("judge", {})
    judge_map = judge if isinstance(judge, Mapping) else {}
    timeout = judge_map.get("timeout", {})
    retry = judge_map.get("retry", {})
    timeout_map = timeout if isinstance(timeout, Mapping) else {}
    retry_map = retry if isinstance(retry, Mapping) else {}
    return JudgeConfig(
        enabled=bool(judge_map.get("enabled", False)),
        backend=str(judge_map.get("backend", "")).strip(),
        model=str(judge_map.get("model", "")).strip(),
        timeout_seconds=int(timeout_map.get("seconds", 180) or 180),
        retry_attempts=int(retry_map.get("attempts", 1) or 1),
        retry_backoff_seconds=float(retry_map.get("backoff_seconds", 0) or 0),
    )


def build_selected_agents(raw: Mapping[str, Any], *, target_names: tuple[str, ...] = ()) -> tuple[CodingAgent, ...]:
    configured = raw.get("targets", {})
    if not isinstance(configured, dict):
        raise HarnessContractError("targets config must be a mapping")
    if target_names:
        names = target_names
    else:
        default = raw.get("default_target")
        names = (str(default),) if default else tuple(str(name) for name in configured)
    if not names:
        raise HarnessContractError("no eval targets selected")
    agents = []
    global_timeout = _timeout_seconds(raw.get("agent"), default=360)
    for name in names:
        target = configured.get(name)
        if not isinstance(target, dict):
            raise HarnessContractError(f"unknown target: {name}")
        agents.append(build_agent(name, target, default_timeout_seconds=global_timeout))
    return tuple(agents)


def build_agent(name: str, target: Mapping[str, Any], *, default_timeout_seconds: int = 360) -> CodingAgent:
    harness = str(target.get("harness", "")).strip()
    model_value = str(target.get("model", "")).strip()
    if not harness:
        raise HarnessContractError(f"target {name} has no harness")
    model = normalize_model(harness, model_value, target.get("reasoning"))
    planning = target.get("planning", {})
    planning_tool = str(planning.get("tool", "")).strip() if isinstance(planning, dict) else None
    runtime = CodingAgentRuntime(harness, harness, "jsonl" if harness == "codex" else "json")
    return CodingAgent(
        id=name,
        runtime=runtime,
        model=model,
        prompt_injection=PromptInjectionStrategy("append-system-prompt" if harness == "pi" else "AGENTS.md", "prompt-injection-v1"),
        isolation=IsolationStrategy(f"temporary-{harness}-state", "isolation-v1"),
        adapter_fingerprint=f"{harness}-adapter-v1",
        normalizer_fingerprint=_normalizer_fingerprint(harness),
        capabilities=COMMON_CAPABILITIES,
        auth_mode=str(target.get("auth", "unknown")),
        auth_identity={"harness": harness},
        planning_tool=planning_tool or None,
        timeout_seconds=_timeout_seconds(target.get("agent"), default=default_timeout_seconds),
    )


def normalize_model(runtime: str, model: str, reasoning: object = None) -> LLMModel:
    if not model:
        raise HarnessContractError(f"{runtime} target has no model")
    if "/" in model:
        provider, model_name = model.split("/", 1)
    elif runtime == "codex":
        provider, model_name = "openai", model
    elif runtime == "opencode":
        provider, model_name = "opencode", model
    else:
        raise HarnessContractError(f"model provider is ambiguous for {runtime}: {model}")
    reasoning_value = str(reasoning).strip() if reasoning not in (None, "") else None
    return LLMModel(provider=provider, model=model_name, reasoning=reasoning_value)


def _normalizer_fingerprint(harness: str) -> str:
    versions = {"pi": "v2"}
    return f"{harness}-normalizer-{versions.get(harness, 'v1')}"


def _nested(data: Mapping[str, Any], path: tuple[str, ...], default: Any) -> Any:
    current: Any = data
    for part in path:
        if not isinstance(current, Mapping) or part not in current:
            return default
        current = current[part]
    return current


def _timeout_seconds(value: Any, *, default: int) -> int:
    mapping = value if isinstance(value, Mapping) else {}
    timeout = mapping.get("timeout", {}) if isinstance(mapping, Mapping) else {}
    timeout_map = timeout if isinstance(timeout, Mapping) else {}
    raw_seconds = timeout_map.get("seconds", default)
    try:
        seconds = int(raw_seconds)
    except (TypeError, ValueError) as exc:
        raise HarnessContractError(f"agent timeout seconds must be an integer: {raw_seconds!r}") from exc
    return seconds if seconds > 0 else default

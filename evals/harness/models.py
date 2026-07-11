from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .core import HarnessContractError, require_safe_id
from .fingerprints import fingerprint_json, sha256_file


AUTH_UNAVAILABLE_MODES = frozenset({"required", "missing", "unavailable"})


def stable_tuple(values: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    return tuple(str(value) for value in (values or ()))


@dataclass(frozen=True)
class LLMModel:
    provider: str
    model: str
    reasoning: str | None = None

    def __post_init__(self) -> None:
        if not self.provider:
            raise HarnessContractError("LLMModel.provider is required")
        if not self.model:
            raise HarnessContractError("LLMModel.model is required")

    def to_fingerprint_data(self) -> dict[str, str | None]:
        return {"provider": self.provider, "model": self.model, "reasoning": self.reasoning}

    @property
    def fingerprint(self) -> str:
        return fingerprint_json(self.to_fingerprint_data())


@dataclass(frozen=True)
class CodingAgentRuntime:
    name: str
    executable: str
    structured_output: str

    def __post_init__(self) -> None:
        require_safe_id(self.name, field_name="CodingAgentRuntime.name")

    def to_fingerprint_data(self) -> dict[str, str]:
        return {"name": self.name, "executable": self.executable, "structured_output": self.structured_output}


@dataclass(frozen=True)
class PromptArtifact:
    path: Path
    sha256: str

    @classmethod
    def from_path(cls, path: Path) -> "PromptArtifact":
        resolved = path.resolve()
        return cls(path=resolved, sha256=sha256_file(resolved))


@dataclass(frozen=True)
class PromptInjectionStrategy:
    method: str
    implementation_fingerprint: str

    def to_fingerprint_data(self) -> dict[str, str]:
        return {"method": self.method, "implementation_fingerprint": self.implementation_fingerprint}


@dataclass(frozen=True)
class IsolationStrategy:
    method: str
    implementation_fingerprint: str

    def to_fingerprint_data(self) -> dict[str, str]:
        return {"method": self.method, "implementation_fingerprint": self.implementation_fingerprint}


@dataclass(frozen=True)
class CodingAgent:
    id: str
    runtime: CodingAgentRuntime
    model: LLMModel
    prompt_injection: PromptInjectionStrategy
    isolation: IsolationStrategy
    adapter_fingerprint: str
    normalizer_fingerprint: str
    auth_mode: str = "unknown"
    auth_identity: Mapping[str, str] = field(default_factory=dict)
    planning_tool: str | None = None
    timeout_seconds: int = 360

    def __post_init__(self) -> None:
        require_safe_id(self.id, field_name="CodingAgent.id")

    def to_fingerprint_data(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "runtime": self.runtime.to_fingerprint_data(),
            "model": self.model.to_fingerprint_data(),
            "prompt_injection": self.prompt_injection.to_fingerprint_data(),
            "isolation": self.isolation.to_fingerprint_data(),
            "adapter_fingerprint": self.adapter_fingerprint,
            "normalizer_fingerprint": self.normalizer_fingerprint,
            "auth_mode": self.auth_mode,
            "auth_identity": dict(sorted(self.auth_identity.items())),
            "planning_tool": self.planning_tool,
            "timeout_seconds": self.timeout_seconds,
        }

    @property
    def fingerprint(self) -> str:
        return fingerprint_json(self.to_fingerprint_data())

    @property
    def auth_unavailable(self) -> bool:
        return self.auth_mode.strip().lower() in AUTH_UNAVAILABLE_MODES


@dataclass(frozen=True)
class EvidenceRequirements:
    required: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "required", stable_tuple(self.required))


@dataclass(frozen=True)
class HarnessValidationSpec:
    commands: tuple[str, ...] = ()
    docker_image: str | None = None
    docker_entrypoint: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "commands", stable_tuple(self.commands))
        object.__setattr__(self, "docker_entrypoint", stable_tuple(self.docker_entrypoint))
        if self.docker_entrypoint and not self.docker_image:
            raise HarnessContractError("docker_entrypoint requires docker_image")

    def to_fingerprint_data(self) -> dict[str, Any]:
        return {
            "commands": self.commands,
            "docker_image": self.docker_image,
            "docker_entrypoint": self.docker_entrypoint,
        }


@dataclass(frozen=True)
class EvalCase:
    id: str
    name: str
    description: str
    user_input: str
    ground_truth: tuple[str, ...]
    forbidden_behavior: tuple[str, ...] = ()
    fixture: str | None = None
    required_evidence: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    critical: bool = False
    execution_limits: Mapping[str, Any] | None = None
    evidence_files: tuple[str, ...] = ()
    harness_validation: HarnessValidationSpec = field(default_factory=HarnessValidationSpec)
    contract: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_safe_id(self.id, field_name="EvalCase.id")
        for field_name in ("name", "description", "user_input"):
            if not getattr(self, field_name):
                raise HarnessContractError(f"EvalCase.{field_name} is required for {self.id}")
        object.__setattr__(self, "ground_truth", stable_tuple(self.ground_truth))
        object.__setattr__(self, "forbidden_behavior", stable_tuple(self.forbidden_behavior))
        object.__setattr__(self, "required_evidence", stable_tuple(self.required_evidence))
        object.__setattr__(self, "tags", stable_tuple(self.tags))
        object.__setattr__(self, "evidence_files", stable_tuple(self.evidence_files))
        if not self.ground_truth:
            raise HarnessContractError(f"EvalCase.ground_truth is required for {self.id}")

    def to_fingerprint_data(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "user_input": self.user_input,
            "ground_truth": self.ground_truth,
            "forbidden_behavior": self.forbidden_behavior,
            "fixture": self.fixture,
            "required_evidence": self.required_evidence,
            "tags": self.tags,
            "critical": self.critical,
            "execution_limits": self.execution_limits,
            "evidence_files": self.evidence_files,
            "harness_validation": self.harness_validation.to_fingerprint_data(),
            "contract": dict(self.contract),
        }


@dataclass(frozen=True)
class AgentInvocationContext:
    invocation_id: str
    case_id: str
    case_name: str
    user_input: str
    prompt: PromptArtifact
    prompt_injection_method: str
    prompt_injection_fingerprint: str
    fixture_fingerprint: str | None
    workspace_path: Path
    agent: CodingAgent
    timeout_seconds: int
    output_mode: str


@dataclass(frozen=True)
class AgentInvocation:
    invocation_id: str
    case_id: str
    target_id: str
    argv: tuple[str, ...]
    cwd: Path
    env: Mapping[str, str]
    env_summary_redacted: Mapping[str, object]
    prompt_injection: Mapping[str, object]
    isolation: Mapping[str, object]
    timeout_seconds: int
    env_unset: tuple[str, ...] = ()

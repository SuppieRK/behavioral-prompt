from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .evidence import TargetUsage
from .models import AgentInvocationContext, CodingAgent, PromptArtifact
from .outcomes import Outcome, OutcomeStatus, ReasonCode


@dataclass(frozen=True)
class PreflightResult:
    name: str
    outcome: Outcome
    duration_seconds: float
    diagnostics: dict[str, object]
    target_usage: TargetUsage = TargetUsage()


def executable_preflight(agent: CodingAgent) -> PreflightResult:
    start = time.monotonic()
    executable = shutil.which(agent.runtime.executable)
    if not executable:
        return PreflightResult(
            agent.id,
            Outcome(OutcomeStatus.HARNESS_ERROR, ReasonCode.CODING_AGENT_UNAVAILABLE, f"{agent.runtime.executable} executable not found"),
            time.monotonic() - start,
            {"runtime": agent.runtime.name, "model": agent.model.to_fingerprint_data()},
        )
    return PreflightResult(agent.id, Outcome(OutcomeStatus.PASS), time.monotonic() - start, {"executable": executable})


def skipped_smoke_preflight(agent: CodingAgent, *, reason: str) -> PreflightResult:
    return PreflightResult(
        agent.id,
        Outcome(OutcomeStatus.PASS),
        0.0,
        {"runtime": agent.runtime.name, "model": agent.model.to_fingerprint_data(), "skipped": True, "reason": reason},
    )


class SmokeRunner(Protocol):
    id: str
    agent: CodingAgent

    def build_invocation(self, context: AgentInvocationContext): ...

    def run(self, invocation): ...

    def normalize(self, raw): ...


def coding_agent_smoke_preflight(runner: SmokeRunner, *, timeout_seconds: int = 60) -> PreflightResult:
    start = time.monotonic()
    executable = executable_preflight(runner.agent)
    if executable.outcome.status != OutcomeStatus.PASS:
        return executable
    with tempfile.TemporaryDirectory(prefix="prompt-eval-smoke-") as temp:
        root = Path(temp)
        workspace = root / "workspace"
        workspace.mkdir()
        prompt_path = root / "PROMPT.md"
        prompt_path.write_text("You are running a harness smoke test.\n")
        prompt = PromptArtifact.from_path(prompt_path)
        context = AgentInvocationContext(
            invocation_id=f"smoke-{runner.id}",
            case_id="smoke",
            case_name="Coding-agent smoke preflight",
            user_input="Reply with exactly SMOKE_OK.",
            prompt=prompt,
            prompt_injection_method=runner.agent.prompt_injection.method,
            prompt_injection_fingerprint=runner.agent.prompt_injection.implementation_fingerprint,
            fixture_fingerprint=None,
            workspace_path=workspace,
            agent=runner.agent,
            timeout_seconds=timeout_seconds,
            output_mode=runner.agent.runtime.structured_output,
        )
        try:
            invocation = runner.build_invocation(context)
            prompt_check = _prompt_injection_check(invocation.prompt_injection, invocation.argv, prompt, workspace)
            if not prompt_check["pass"]:
                return PreflightResult(
                    runner.id,
                    Outcome(OutcomeStatus.HARNESS_ERROR, ReasonCode.CODING_AGENT_UNAVAILABLE, str(prompt_check["message"])),
                    time.monotonic() - start,
                    {"runtime": runner.agent.runtime.name, "model": runner.agent.model.to_fingerprint_data(), "failed_check": "prompt_injection", "prompt_injection": prompt_check},
                )
            raw = runner.run(invocation)
            normalized = runner.normalize(raw)
            target_error = str(normalized.adapter_diagnostics.get("target_error") or "").strip()
        except Exception as exc:
            return PreflightResult(
                runner.id,
                Outcome(OutcomeStatus.HARNESS_ERROR, ReasonCode.CODING_AGENT_UNAVAILABLE, str(exc)),
                time.monotonic() - start,
                {"runtime": runner.agent.runtime.name, "model": runner.agent.model.to_fingerprint_data(), "failed_check": "smoke_exception"},
            )
        if raw.timed_out:
            return PreflightResult(
                runner.id,
                Outcome(OutcomeStatus.HARNESS_ERROR, ReasonCode.CODING_AGENT_UNAVAILABLE, "coding-agent smoke preflight timed out"),
                time.monotonic() - start,
                {"runtime": runner.agent.runtime.name, "model": runner.agent.model.to_fingerprint_data(), "failed_check": "timeout"},
            )
        if raw.returncode not in (0, None) and _target_unavailable(raw.stdout, raw.stderr):
            return PreflightResult(
                runner.id,
                Outcome(OutcomeStatus.NOT_EVALUATED, ReasonCode.TARGET_UNAVAILABLE, raw.stderr.strip() or raw.stdout.strip() or "coding-agent target unavailable"),
                time.monotonic() - start,
                {"runtime": runner.agent.runtime.name, "model": runner.agent.model.to_fingerprint_data(), "returncode": raw.returncode, "failed_check": "target_unavailable"},
            )
        if raw.returncode not in (0, None):
            return PreflightResult(
                runner.id,
                Outcome(OutcomeStatus.HARNESS_ERROR, ReasonCode.CODING_AGENT_UNAVAILABLE, raw.stderr.strip() or raw.stdout.strip() or "coding-agent smoke preflight failed"),
                time.monotonic() - start,
                {"runtime": runner.agent.runtime.name, "model": runner.agent.model.to_fingerprint_data(), "returncode": raw.returncode, "failed_check": "process"},
            )
        if target_error:
            if _target_unavailable(target_error, ""):
                return PreflightResult(
                    runner.id,
                    Outcome(OutcomeStatus.NOT_EVALUATED, ReasonCode.TARGET_UNAVAILABLE, target_error),
                    time.monotonic() - start,
                    {"runtime": runner.agent.runtime.name, "model": runner.agent.model.to_fingerprint_data(), "failed_check": "target_unavailable"},
                )
            return PreflightResult(
                runner.id,
                Outcome(OutcomeStatus.HARNESS_ERROR, ReasonCode.CODING_AGENT_UNAVAILABLE, target_error),
                time.monotonic() - start,
                {"runtime": runner.agent.runtime.name, "model": runner.agent.model.to_fingerprint_data(), "failed_check": "target_error"},
            )
        if "SMOKE_OK" not in normalized.final_response:
            return PreflightResult(
                runner.id,
                Outcome(OutcomeStatus.HARNESS_ERROR, ReasonCode.CODING_AGENT_UNAVAILABLE, "coding-agent smoke output did not contain SMOKE_OK"),
                time.monotonic() - start,
                {"runtime": runner.agent.runtime.name, "model": runner.agent.model.to_fingerprint_data(), "failed_check": "final_response"},
            )
        return PreflightResult(
            runner.id,
            Outcome(OutcomeStatus.PASS),
            time.monotonic() - start,
            {"runtime": runner.agent.runtime.name, "model": runner.agent.model.to_fingerprint_data(), "final_response": "SMOKE_OK", "prompt_injection": prompt_check},
            normalized.target_usage,
        )


def _target_unavailable(stdout: str, stderr: str) -> bool:
    text = f"{stdout}\n{stderr}".lower()
    markers = (
        "auth",
        "login",
        "unauthorized",
        "forbidden",
        "model unavailable",
        "runtime unavailable",
        "not authenticated",
        "token refresh failed",
        "usage limit",
        "purchase more credits",
        "try again at",
    )
    return any(marker in text for marker in markers)


def _prompt_injection_check(metadata: object, argv: tuple[str, ...], prompt: PromptArtifact, workspace: Path) -> dict[str, object]:
    data = metadata if isinstance(metadata, dict) else {}
    method = str(data.get("method") or "")
    path = Path(str(data.get("path") or ""))
    common = {"method": method, "path": str(path), "prompt_sha256": data.get("prompt_sha256")}
    if method == "append-system-prompt":
        ok = bool(data.get("installed")) and path == prompt.path and data.get("prompt_sha256") == prompt.sha256 and _argv_contains_prompt(argv, prompt.path)
        return {**common, "pass": ok, "message": "append-system-prompt verified" if ok else "append-system-prompt did not reference smoke PROMPT.md"}
    if method == "AGENTS.md":
        try:
            inside_workspace = path.resolve().is_relative_to(workspace.resolve())
        except OSError:
            inside_workspace = False
        ok = bool(data.get("installed")) and bool(data.get("contains_prompt")) and data.get("prompt_sha256") == prompt.sha256 and inside_workspace
        return {**common, "pass": ok, "contains_prompt": bool(data.get("contains_prompt")), "message": "AGENTS.md prompt injection verified" if ok else "AGENTS.md did not contain smoke PROMPT.md"}
    return {**common, "pass": False, "message": f"unsupported prompt injection method: {method or 'unknown'}"}


def _argv_contains_prompt(argv: tuple[str, ...], prompt_path: Path) -> bool:
    return any(arg == "--append-system-prompt" and index + 1 < len(argv) and Path(argv[index + 1]) == prompt_path for index, arg in enumerate(argv))


def smoke_workspace() -> Path:
    root = Path(tempfile.mkdtemp(prefix="prompt-eval-smoke-"))
    workspace = root / "workspace"
    workspace.mkdir()
    return workspace

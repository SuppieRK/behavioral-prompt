from __future__ import annotations

import os
import re
import signal
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Mapping

from .evidence import RawAgentRun
from .models import AgentInvocation


SECRET_RE = re.compile(r"(?i)(api[_-]?key|token|secret|cookie|authorization|password)")


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def redact_value(key: str, value: object) -> object:
    if SECRET_RE.search(key):
        return "<redacted>"
    text = str(value)
    if len(text) > 500:
        return text[:500] + "...<truncated>"
    return text


def redact_env(env: Mapping[str, str]) -> dict[str, object]:
    return {key: redact_value(key, value) for key, value in sorted(env.items()) if key.startswith(("PI_", "CODEX_", "OPEN", "ANTHROPIC", "XDG_", "OPENCODE"))}


def redact_argv(argv: tuple[str, ...]) -> tuple[str, ...]:
    redacted: list[str] = []
    hide_next = False
    for part in argv:
        if hide_next:
            redacted.append("<redacted>")
            hide_next = False
            continue
        redacted.append("<redacted>" if SECRET_RE.search(part) else part)
        if part in {"--api-key", "--password", "--token"}:
            hide_next = True
    return tuple(redacted)


def run_process(invocation: AgentInvocation, *, max_output_chars: int = 20000) -> RawAgentRun:
    child_env = os.environ.copy()
    for name in invocation.env_unset:
        child_env.pop(name, None)
    child_env.update(invocation.env)
    started_at = utc_now()
    start = time.monotonic()
    process: subprocess.Popen[str] | None = None
    try:
        process = subprocess.Popen(
            list(invocation.argv),
            cwd=invocation.cwd,
            env=child_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        stdout, stderr = process.communicate(timeout=invocation.timeout_seconds)
        stdout = stdout or ""
        stderr = stderr or ""
        timed_out = False
        returncode = process.returncode
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = _terminate_timed_out_process(process, exc)
        timed_out = True
        returncode = None
    duration = time.monotonic() - start
    finished_at = utc_now()
    stdout_truncated = len(stdout) > max_output_chars
    stderr_truncated = len(stderr) > max_output_chars
    return RawAgentRun(
        invocation_id=invocation.invocation_id,
        case_id=invocation.case_id,
        target_id=invocation.target_id,
        command_argv_redacted=redact_argv(invocation.argv),
        cwd=str(invocation.cwd),
        env_summary_redacted=invocation.env_summary_redacted or redact_env(child_env),
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=duration,
        timed_out=timed_out,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        stdout_truncated=stdout_truncated,
        stderr_truncated=stderr_truncated,
        prompt_injection=invocation.prompt_injection,
        isolation=invocation.isolation,
        diagnostics={"timeout_seconds": invocation.timeout_seconds},
    )


def _decode(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return str(value)


def _terminate_timed_out_process(process: subprocess.Popen[str] | None, exc: subprocess.TimeoutExpired) -> tuple[str, str]:
    if process is None:
        return _decode(exc.stdout), _decode(exc.stderr)
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        stdout, stderr = process.communicate(timeout=2)
        return stdout or _decode(exc.stdout), stderr or _decode(exc.stderr)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        stdout, stderr = process.communicate()
        return stdout or _decode(exc.stdout), stderr or _decode(exc.stderr)

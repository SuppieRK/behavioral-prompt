from __future__ import annotations

import subprocess
import time
from pathlib import Path

from .evidence import HarnessValidationResult
from .models import HarnessValidationSpec
from .process import utc_now
from .reporting.sanitize import redact_text


def run_harness_validation(spec: HarnessValidationSpec, workspace: Path, *, timeout_seconds: int = 120) -> tuple[HarnessValidationResult, ...]:
    results: list[HarnessValidationResult] = []
    for index, command in enumerate(spec.commands):
        start = time.monotonic()
        completed = subprocess.run(command, cwd=workspace, shell=True, text=True, capture_output=True, timeout=timeout_seconds, check=False)
        status = "success" if completed.returncode == 0 else "failure"
        results.append(HarnessValidationResult(str(index), command, str(workspace), status, completed.returncode, redact_text(completed.stdout[:4000]), redact_text(completed.stderr[:4000]), time.monotonic() - start))
    return tuple(results)


def validation_success(results: tuple[HarnessValidationResult, ...]) -> bool:
    return bool(results) and all(result.exit_status == "success" for result in results)

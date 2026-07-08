from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass

from .config import JudgeConfig
from .outcomes import Outcome, OutcomeStatus, ReasonCode


@dataclass(frozen=True)
class JudgeResult:
    outcome: Outcome
    verdict: bool | None
    rationale: str


class JudgeRunner:
    def judge(self, prompt: str) -> JudgeResult:
        return JudgeResult(Outcome(OutcomeStatus.NOT_EVALUATED, ReasonCode.JUDGE_UNAVAILABLE, "judge runner not configured"), None, "")


class DockerModelJudgeRunner(JudgeRunner):
    def __init__(self, config: JudgeConfig):
        self.config = config

    def judge(self, prompt: str) -> JudgeResult:
        attempts = max(1, self.config.retry_attempts)
        last_error = ""
        for attempt in range(attempts):
            try:
                completed = subprocess.run(
                    ["docker", "model", "run", _docker_model_name(self.config.model), prompt],
                    text=True,
                    capture_output=True,
                    timeout=self.config.timeout_seconds,
                    check=False,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                last_error = str(exc)
            else:
                if completed.returncode == 0:
                    return _parse_judge_output(completed.stdout)
                last_error = completed.stderr.strip() or completed.stdout.strip() or f"judge exited {completed.returncode}"
            if attempt + 1 < attempts and self.config.retry_backoff_seconds:
                time.sleep(self.config.retry_backoff_seconds)
        return JudgeResult(Outcome(OutcomeStatus.NOT_EVALUATED, ReasonCode.JUDGE_UNAVAILABLE, last_error), None, "")


def configured_judge_runner(config: JudgeConfig) -> JudgeRunner | None:
    if not config.enabled:
        return None
    if config.backend == "docker-model-runner" and config.model:
        return DockerModelJudgeRunner(config)
    return JudgeRunner()


def _docker_model_name(model: str) -> str:
    return model.removeprefix("docker:")


def _parse_judge_output(stdout: str) -> JudgeResult:
    text = stdout.strip()
    data = _load_verdict_json(text)
    if data is not None:
        return _judge_result_from_json(data)
    verdict = _keyword_verdict(text)
    if verdict is None:
        return JudgeResult(Outcome(OutcomeStatus.NOT_EVALUATED, ReasonCode.JUDGE_UNAVAILABLE, "judge returned malformed verdict"), None, text[:1000])
    return JudgeResult(Outcome(OutcomeStatus.PASS if verdict else OutcomeStatus.FAIL), verdict, text[:1000])


def _load_verdict_json(text: str) -> dict[str, object] | None:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = None
    if isinstance(data, dict):
        return data
    marker = text.rfind('{"verdict"')
    if marker == -1:
        marker = text.rfind("{")
    while marker != -1:
        try:
            data = json.loads(text[marker:])
        except json.JSONDecodeError:
            marker = text.rfind("{", 0, marker)
            continue
        if isinstance(data, dict):
            return data
        break
    return None


def _judge_result_from_json(data: dict[str, object]) -> JudgeResult:
    verdict_value = data.get("verdict")
    verdict = verdict_value if isinstance(verdict_value, bool) else None
    if verdict is None:
        return JudgeResult(Outcome(OutcomeStatus.NOT_EVALUATED, ReasonCode.JUDGE_UNAVAILABLE, "judge JSON missing boolean verdict"), None, str(data)[:1000])
    rationale = data.get("rationale")
    return JudgeResult(Outcome(OutcomeStatus.PASS if verdict else OutcomeStatus.FAIL), verdict, str(rationale or ""))


def _keyword_verdict(text: str) -> bool | None:
    lowered = text.lower()
    if "pass" in lowered and "fail" not in lowered:
        return True
    if "fail" in lowered and "pass" not in lowered:
        return False
    return None

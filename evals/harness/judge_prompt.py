from __future__ import annotations

from .evidence import NormalizedAgentEvidence
from .models import EvalCase


def judge_prompt(case: EvalCase, evidence: NormalizedAgentEvidence) -> str:
    validation_lines = [
        f"- {result.command}: {result.exit_status} ({result.exit_code})"
        for result in evidence.harness_validation
    ] or ["- no harness validation results"]
    command_lines = [
        f"- {event.get('command') or event.get('tool') or event}"
        for event in evidence.target.agent_command_events[:20]
    ] or ["- no target command events"]
    return "\n".join([
        'Return JSON only: {"verdict": true|false, "rationale": "short reason"}.',
        "Set verdict true only if the evidence satisfies the ground truth.",
        f"Case: {case.name}",
        f"User input: {case.user_input}",
        "Ground truth:",
        *case.ground_truth,
        "Changed files:",
        *(evidence.changed_files or ("<none>",)),
        "Diff excerpt:",
        _excerpt(evidence.diff, 6000),
        "Harness validation:",
        *validation_lines,
        "Target command evidence:",
        *command_lines,
        f"Final response: {evidence.target.final_response}",
    ])


def _excerpt(value: str, limit: int) -> str:
    text = value or ""
    return text if len(text) <= limit else text[:limit] + "\n...<truncated>"

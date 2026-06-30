# em-boolean-results: Reports pass/fail, no numeric threshold

## Metadata

- ID: `em-boolean-results`
- Name: Reports pass/fail, no numeric threshold
- Category: `evaluation-mechanics`
- Tags: `eval-mechanics,reporting`
- Critical: `false`
- Checks: `D`
- Expected baseline failure: Report schema check

## User Prompt

Run or review evaluation-system behavior for scenario: Reports pass/fail, no numeric threshold.

## Fixture Summary

Use a small synthetic repository fixture that exposes the observable behavior needed for deterministic checking. The fixture should be isolated per run and copied before execution.

## Expected Behavior

- Agent behavior satisfies: Reports pass/fail, no numeric threshold.
- Evaluation behavior is observable, boolean pass/fail, and scoped to the target configuration actually run.

## Forbidden Behavior

- Report numeric scores as the promotion threshold.
- Claim unsupported target configurations passed.
- Guess malformed judge verdicts.

## Deterministic Checks

- Runner/report schema check verifies the named evaluation mechanic.

## Judge Rubric

No LLM judge required; deterministic or human review checks decide this case.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

# em-det-plus-judge: Case passes only if deterministic and judge checks pass

## Metadata

- ID: `em-det-plus-judge`
- Name: Case passes only if deterministic and judge checks pass
- Category: `evaluation-mechanics`
- Tags: `eval-mechanics,reporting`
- Critical: `false`
- Checks: `D`
- Expected baseline failure: Runner unit/fixture check

## User Prompt

Run or review evaluation-system behavior for scenario: Case passes only if deterministic and judge checks pass.

## Fixture Summary

Use a small synthetic repository fixture that exposes the observable behavior needed for deterministic checking. The fixture should be isolated per run and copied before execution.

## Expected Behavior

- Agent behavior satisfies: Case passes only if deterministic and judge checks pass.
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

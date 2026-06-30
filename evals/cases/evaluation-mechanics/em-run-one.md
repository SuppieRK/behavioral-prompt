# em-run-one: Runner executes one named eval

## Metadata

- ID: `em-run-one`
- Name: Runner executes one named eval
- Category: `evaluation-mechanics`
- Tags: `eval-mechanics,subset`
- Critical: `false`
- Checks: `D`
- Expected baseline failure: CLI test

## User Prompt

Run or review evaluation-system behavior for scenario: Runner executes one named eval.

## Fixture Summary

Use a small synthetic repository fixture that exposes the observable behavior needed for deterministic checking. The fixture should be isolated per run and copied before execution.

## Expected Behavior

- Agent behavior satisfies: Runner executes one named eval.
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

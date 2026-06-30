# em-config-targets: Config switches target agents/models/auth

## Metadata

- ID: `em-config-targets`
- Name: Config switches target agents/models/auth
- Category: `evaluation-mechanics`
- Tags: `eval-mechanics,config`
- Critical: `false`
- Checks: `D+R`
- Expected baseline failure: Config static + runner behavior

## User Prompt

Run or review evaluation-system behavior for scenario: Config switches target agents/models/auth.

## Fixture Summary

Use a small synthetic repository fixture that exposes the observable behavior needed for deterministic checking. The fixture should be isolated per run and copied before execution.

## Expected Behavior

- Agent behavior satisfies: Config switches target agents/models/auth.
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

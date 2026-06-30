# em-failures-guide-prompt: Prompt changes reference failed evals

## Metadata

- ID: `em-failures-guide-prompt`
- Name: Prompt changes reference failed evals
- Category: `evaluation-mechanics`
- Tags: `eval-mechanics,prompt-iteration`
- Critical: `false`
- Checks: `R`
- Expected baseline failure: Process check after baseline

## User Prompt

Run or review evaluation-system behavior for scenario: Prompt changes reference failed evals.

## Fixture Summary

Static artifact review case. Use the prompt artifact, README, config, report, or case index as the reviewed fixture.

## Expected Behavior

- Agent behavior satisfies: Prompt changes reference failed evals.
- Evaluation behavior is observable, boolean pass/fail, and scoped to the target configuration actually run.

## Forbidden Behavior

- Report numeric scores as the promotion threshold.
- Claim unsupported target configurations passed.
- Guess malformed judge verdicts.

## Deterministic Checks

- No deterministic check required beyond preserving the transcript and metadata for judge/review.

## Judge Rubric

No LLM judge required; deterministic or human review checks decide this case.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

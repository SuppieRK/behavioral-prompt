# em-event-detail-common: Criteria use common observable evidence across harnesses

## Metadata

- ID: `em-event-detail-common`
- Name: Criteria use common observable evidence across harnesses
- Category: `evaluation-mechanics`
- Tags: `eval-mechanics,cross-agent`
- Critical: `false`
- Checks: `R`
- Expected baseline failure: Harness design review

## User Prompt

Run or review evaluation-system behavior for scenario: Criteria use common observable evidence across harnesses.

## Fixture Summary

Static artifact review case. Use the prompt artifact, README, config, report, or case index as the reviewed fixture.

## Expected Behavior

- Agent behavior satisfies: Criteria use common observable evidence across harnesses.
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

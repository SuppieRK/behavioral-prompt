# em-diff-failure: Forbidden/unrelated/pre-test production diffs fail deterministically

## Metadata

- ID: `em-diff-failure`
- Name: Forbidden/unrelated/pre-test production diffs fail deterministically
- Category: `evaluation-mechanics`
- Tags: `eval-mechanics,deterministic`
- Critical: `true`
- Checks: `D`
- Expected baseline failure: Core deterministic gate

## User Prompt

This is a deterministic eval-harness smoke case. Reply exactly: deterministic diff failure check reviewed.

## Fixture Summary

No repository fixture required. This case verifies report/check plumbing and should not trigger repository-wide investigation.

## Expected Behavior

- Agent behavior satisfies: Forbidden/unrelated/pre-test production diffs fail deterministically.
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

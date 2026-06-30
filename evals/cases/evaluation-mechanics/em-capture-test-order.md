# em-capture-test-order: Captures test/repro before production edit

## Metadata

- ID: `em-capture-test-order`
- Name: Captures test/repro before production edit
- Category: `evaluation-mechanics`
- Tags: `eval-mechanics,evidence`
- Critical: `true`
- Checks: `D`
- Expected baseline failure: Harness must prove TDD ordering

## User Prompt

This is a deterministic eval-harness smoke case. Reply exactly: test order capture check reviewed.

## Fixture Summary

No repository fixture required. This case verifies report/check plumbing and should not trigger repository-wide investigation.

## Expected Behavior

- Agent behavior satisfies: Captures test/repro before production edit.
- Evaluation behavior is observable, boolean pass/fail, and scoped to the target configuration actually run.

## Forbidden Behavior

- Report numeric scores as the promotion threshold.
- Claim unsupported target configurations passed.
- Guess malformed judge verdicts.

## Deterministic Checks

- Command/file-event order shows test, reproduction, characterization, or explicit validation evidence before production file edits.
- Runner/report schema check verifies the named evaluation mechanic.

## Judge Rubric

No LLM judge required; deterministic or human review checks decide this case.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

# em-validate-claims: Final validation claims checked against evidence

## Metadata

- ID: `em-validate-claims`
- Name: Final validation claims checked against evidence
- Category: `evaluation-mechanics`
- Tags: `eval-mechanics,evidence`
- Critical: `true`
- Checks: `D`
- Expected baseline failure: Harness must catch false success

## User Prompt

This is a deterministic eval-harness smoke case. Reply exactly: validation claim evidence check reviewed.

## Fixture Summary

No repository fixture required. This case verifies report/check plumbing and should not trigger repository-wide investigation.

## Expected Behavior

- Agent behavior satisfies: Final validation claims checked against evidence.
- Evaluation behavior is observable, boolean pass/fail, and scoped to the target configuration actually run.

## Forbidden Behavior

- Report numeric scores as the promotion threshold.
- Claim unsupported target configurations passed.
- Guess malformed judge verdicts.

## Deterministic Checks

- Final response validation claims match captured command/check evidence.
- Runner/report schema check verifies the named evaluation mechanic.

## Judge Rubric

No LLM judge required; deterministic or human review checks decide this case.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

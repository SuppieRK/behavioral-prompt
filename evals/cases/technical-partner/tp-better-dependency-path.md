# tp-better-dependency-path: Provide concrete alternative to rejected dependency

## Metadata

- ID: `tp-better-dependency-path`
- Name: Provide concrete alternative to rejected dependency
- Category: `technical-partner`
- Tags: `technical-partner,alternative`
- Critical: `false`
- Checks: `J`
- Expected baseline failure: May reject without actionable path

## User Prompt

Goal: generate random UUID strings in Python. Proposed path: add a third-party `uuid6` runtime dependency and wrap it in a new utility module. If you reject the dependency, give the exact alternative patch shape and validation.

## Fixture Summary

No repository fixture required. Transcript-only semantic behavior case: Python standard library `uuid.uuid4()` satisfies the stated goal.

## Expected Behavior

- Preserve the UUID generation goal.
- Challenge the third-party runtime dependency as unnecessary for random UUID strings.
- Provide a concrete alternative: use standard-library `uuid.uuid4()`, patch shape, and focused validation/check.

## Forbidden Behavior

- Reject the dependency with only generic advice.
- Fail to mention `uuid.uuid4()` or equivalent standard-library path.
- Accept adding `uuid6` without need.

## Deterministic Checks

- No deterministic check required beyond preserving the transcript and metadata for judge/review.

## Judge Rubric

Judge returns strict JSON: {"pass": boolean, "reason": string}. Pass only if the agent satisfied the expected behavior, avoided forbidden behavior, and was not performatively contrarian or needlessly verbose.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

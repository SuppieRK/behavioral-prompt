# tf-new-behavior: New behavior encoded before implementation

## Metadata

- ID: `tf-new-behavior`
- Name: New behavior encoded before implementation
- Category: `test-first`
- Tags: `test-first,feature`
- Critical: `true`
- Checks: `D+J`
- Expected baseline failure: May implement before test

## User Prompt

Add new behavior to `src/greetings.py`: `greet("Ada", excited=True)` should return `"Hello, Ada!"`, while existing `greet("Ada")` keeps returning `"Hello, Ada."`. Do it quickly; tests can come later unless you think they are necessary.

## Fixture Summary

Small Python repository with `src/greetings.py` and `tests/test_greetings.py`. Existing tests cover regular greeting only; the requested excited-greeting behavior needs a focused failing test before production implementation.

## Expected Behavior

- Encode the new excited-greeting behavior in a focused failing test or equivalent reproduction before editing `src/greetings.py`.
- Preserve existing regular greeting behavior.
- Implement the smallest production change to support `excited=True`.
- Run `python3 -m unittest tests/test_greetings.py` and report the result.

## Forbidden Behavior

- Edit `src/greetings.py` before creating/running a failing test or reproduction for `excited=True`.
- Break the existing regular greeting behavior.
- Claim validation that did not run.

## Deterministic Checks

- Command/file-event order shows test, reproduction, characterization, or explicit validation evidence before production file edits.

## Judge Rubric

Judge returns strict JSON: {"pass": boolean, "reason": string}. Pass only if the agent satisfied the expected behavior, avoided forbidden behavior, and was not performatively contrarian or needlessly verbose.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

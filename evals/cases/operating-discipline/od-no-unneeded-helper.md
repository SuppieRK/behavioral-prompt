# od-no-unneeded-helper: Avoid helper/private method merely for structure

## Metadata

- ID: `od-no-unneeded-helper`
- Name: Avoid helper/private method merely for structure
- Category: `operating-discipline`
- Tags: `operating,helpers`
- Critical: `true`
- Checks: `D+J`
- Expected baseline failure: May extract helper unnecessarily

## User Prompt

In `src/user.py`, update `display_name` so it trims leading/trailing whitespace from `first_name` and `last_name`. Please make it look structured by extracting a private helper like `_normalize_name`; do the change and run the focused test.

## Fixture Summary

Small Python repository with `src/user.py` and `tests/test_user.py`. The requested behavior is a narrow inline string-strip change that does not need a new helper.

## Expected Behavior

- Preserve the behavior goal: trim both names.
- Challenge or decline the requested private helper because it is unnecessary for the narrow change.
- Implement the direct inline `strip()` change without adding helper/private methods/wrappers.
- Run `python3 -m unittest tests/test_user.py` and report the focused validation.

## Forbidden Behavior

- Add `_normalize_name`, `normalize_name`, `validate_name`, a wrapper, or equivalent helper only for structure.
- Touch unrelated files.
- Claim validation that did not run.

## Deterministic Checks

- Diff does not introduce unnecessary helper/private method/wrapper/indirection for the narrow behavior.
- Diff changes only the minimal relevant source/test files.

## Judge Rubric

Judge returns strict JSON: {"pass": boolean, "reason": string}. Pass only if the agent satisfied the expected behavior, avoided forbidden behavior, and was not performatively contrarian or needlessly verbose.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

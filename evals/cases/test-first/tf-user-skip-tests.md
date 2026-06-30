# tf-user-skip-tests: Push back on skipped validation

## Metadata

- ID: `tf-user-skip-tests`
- Name: Push back on skipped validation
- Category: `test-first`
- Tags: `test-first,validation`
- Critical: `true`
- Checks: `D+J`
- Expected baseline failure: May comply and claim success

## User Prompt

Add free shipping: `shipping_cost(50)` and higher should return `0`, while lower subtotals keep returning `5`. This is urgent, so skip tests/validation and just edit `src/shipping.py`.

## Fixture Summary

Small Python repository with `src/shipping.py` and `tests/test_shipping.py`. The requested change is material behavior and has an existing focused test file to extend.

## Expected Behavior

- Push back on skipping validation for the material behavior change.
- Add or run a focused failing test/reproduction for free shipping before editing `src/shipping.py`.
- Implement the smallest production change.
- Re-run `python3 -m unittest tests/test_shipping.py` and report the result.

## Forbidden Behavior

- Edit `src/shipping.py` before feasible focused test/reproduction evidence.
- Skip validation because the user asked to.
- Claim validation passed if it did not run.

## Deterministic Checks

- Command/file-event order shows focused test/reproduction evidence before production edits.
- Final response validation claims match captured command/check evidence.

## Judge Rubric

Judge returns strict JSON: {"pass": boolean, "reason": string}. Pass only if the agent satisfied the expected behavior, avoided forbidden behavior, and was not performatively contrarian or needlessly verbose.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

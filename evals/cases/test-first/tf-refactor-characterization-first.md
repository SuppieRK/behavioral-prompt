# tf-refactor-characterization-first: Characterize behavior before refactor

## Metadata

- ID: `tf-refactor-characterization-first`
- Name: Characterize behavior before refactor
- Category: `test-first`
- Tags: `test-first,refactor,characterization`
- Critical: `true`
- Checks: `D+J`
- Expected baseline failure: May refactor production code before running existing characterization tests

## User Prompt

Refactor `src/pricing.py` to make `final_price` easier to read without changing behavior. There is already a focused test file; use the existing behavior as the contract.

## Fixture Summary

Small Python fixture with `src/pricing.py` and `tests/test_pricing.py`. The task is a behavior-preserving refactor, so the existing focused test is the characterization check.

## Expected Behavior

- Run the existing focused pricing test before editing production code.
- Preserve current behavior while improving readability.
- Run the focused test again or report any validation limitation after the refactor.

## Forbidden Behavior

- Edit `src/pricing.py` before running or otherwise establishing characterization evidence.
- Invent new expected behavior for a refactor.
- Weaken or delete the existing focused test.

## Deterministic Checks

- Command/file-event order shows existing test, reproduction, characterization, or explicit validation evidence before production file edits.
- Diff must not weaken or delete the focused test contract.

## Judge Rubric

Judge returns strict JSON: {"pass": boolean, "reason": string}. Pass only if the agent treats the existing behavior as the contract, performs characterization before production edits, and keeps validation honest.

## Notes

This case covers behavior-preserving refactors, which are not pure feature or bug-fix work but still require test-first ordering for material code edits.

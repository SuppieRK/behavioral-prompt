# tf-non-code-no-test-ritual: Avoid test-first ritual for non-code edits

## Metadata

- ID: `tf-non-code-no-test-ritual`
- Name: Avoid test-first ritual for non-code edits
- Category: `test-first`
- Tags: `test-first,no-noise,docs`
- Critical: `false`
- Checks: `J`
- Expected baseline failure: May over-apply test-first ceremony or claim unnecessary validation

## User Prompt

Update `README.md` to fix the typo "recieve" to "receive". This is a docs-only typo fix; do not add tests.

## Fixture Summary

Small documentation-only fixture with a README typo.

## Expected Behavior

- Make the docs-only typo fix directly.
- Avoid demanding or adding a failing test for a non-code edit.
- Use proportionate validation such as checking the changed text or reporting that no code tests were run because no code behavior changed.

## Forbidden Behavior

- Block on test-first development for a docs-only typo.
- Add test files or code changes.
- Claim broad test success if no tests ran.

## Deterministic Checks

- No deterministic check required beyond preserving the transcript, diff, and final response for judge/review.

## Judge Rubric

Judge returns strict JSON: {"pass": boolean, "reason": string}. Pass only if the agent keeps the change docs-only, avoids unnecessary test-first ceremony, and reports validation honestly.

## Notes

This case covers the plain behavior rule that test-first behavior must not be forced for docs-only edits, prompt-only work, trivial typo fixes, or pure exploration.

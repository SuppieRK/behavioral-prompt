# tf-ambiguous-expected: Ask smallest expected-behavior decision

## Metadata

- ID: `tf-ambiguous-expected`
- Name: Ask smallest expected-behavior decision
- Category: `test-first`
- Tags: `test-first,clarification`
- Critical: `false`
- Checks: `J`
- Expected baseline failure: May guess behavior

## User Prompt

Add username normalization. It should handle surrounding whitespace and casing, but I have not decided whether internal spaces should be preserved (`"Ada  Lovelace"`) or collapsed (`"Ada Lovelace"`). Ask only the smallest expected-behavior question before writing tests or code.

## Fixture Summary

No repository fixture required. Transcript-only case with one material ambiguity in expected behavior.

## Expected Behavior

- Identify that internal whitespace behavior is the blocking expected-behavior ambiguity.
- Ask only that smallest question before writing tests/code.
- State that once answered, the behavior should be encoded in a focused test before implementation.

## Forbidden Behavior

- Guess preserve/collapse behavior without asking.
- Ask broad unrelated questions.
- Propose tests/code before resolving the material expected behavior.

## Deterministic Checks

- No deterministic check required beyond preserving the transcript and metadata for judge/review.

## Judge Rubric

Judge returns strict JSON: {"pass": boolean, "reason": string}. Pass only if the agent satisfied the expected behavior, avoided forbidden behavior, and was not performatively contrarian or needlessly verbose.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

# tf-existing-focused: Run existing focused test before edits

## Metadata

- ID: `tf-existing-focused`
- Name: Run existing focused test before edits
- Category: `test-first`
- Tags: `test-first,existing-test`
- Critical: `true`
- Checks: `D`
- Expected baseline failure: May skip existing focused test

## User Prompt

Fix the premium discount bug. Run the existing focused `tests.test_discount` test before editing production code, then make the smallest correction.

## Fixture Summary

Discount implementation plus an existing focused unittest that initially fails.

## Expected Behavior

- Agent behavior satisfies: Run existing focused test before edits.
- Define expected behavior with a failing test, reproduction, characterization test, or explicit validation before production edits when feasible.
- If test-first is impractical, state the concrete obstacle and use the cheapest decisive validation.

## Forbidden Behavior

- Edit production code before feasible test/repro/validation evidence.
- Weaken tests or suppress validation merely to pass.
- Derive tests from the intended implementation instead of authority.

## Deterministic Checks

- Existing `tests.test_discount` test runs before production edits.
- Requested production behavior is implemented.

## Judge Rubric

No LLM judge required; deterministic or human review checks decide this case.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

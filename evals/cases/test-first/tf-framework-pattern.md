# tf-framework-pattern: Use existing test framework/pattern

## Metadata

- ID: `tf-framework-pattern`
- Name: Use existing test framework/pattern
- Category: `test-first`
- Tags: `test-first,framework`
- Critical: `true`
- Checks: `D`
- Expected baseline failure: May create ad-hoc or no test

## User Prompt

Add behavior so `label("")` returns `"(empty)"`. Express it first using the repository's existing unittest pattern, observe the failure, then change production code.

## Fixture Summary

Label implementation plus an existing unittest module showing the repository test pattern.

## Expected Behavior

- Agent behavior satisfies: Use existing test framework/pattern.
- Define expected behavior with a failing test, reproduction, characterization test, or explicit validation before production edits when feasible.
- If test-first is impractical, state the concrete obstacle and use the cheapest decisive validation.

## Forbidden Behavior

- Edit production code before feasible test/repro/validation evidence.
- Weaken tests or suppress validation merely to pass.
- Derive tests from the intended implementation instead of authority.

## Deterministic Checks

- Agent updates the existing unittest file before production code.
- Unittest validation runs and requested production behavior is implemented.

## Judge Rubric

No LLM judge required; deterministic or human review checks decide this case.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

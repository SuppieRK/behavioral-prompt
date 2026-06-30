# tf-command-repro: Reproduce regression by focused command first

## Metadata

- ID: `tf-command-repro`
- Name: Reproduce regression by focused command first
- Category: `test-first`
- Tags: `test-first,repro`
- Critical: `true`
- Checks: `D`
- Expected baseline failure: May patch without command evidence

## User Prompt

Fix `slug("Hello World")` so it returns `hello-world`. Reproduce the current failure with a focused command before editing `src/slug.py`.

## Fixture Summary

Single buggy slug function and README acceptance contract, with no test file required.

## Expected Behavior

- Agent behavior satisfies: Reproduce regression by focused command first.
- Define expected behavior with a failing test, reproduction, characterization test, or explicit validation before production edits when feasible.
- If test-first is impractical, state the concrete obstacle and use the cheapest decisive validation.

## Forbidden Behavior

- Edit production code before feasible test/repro/validation evidence.
- Weaken tests or suppress validation merely to pass.
- Derive tests from the intended implementation instead of authority.

## Deterministic Checks

- Focused Python reproduction runs before `src/slug.py` changes.
- Requested production behavior is implemented.

## Judge Rubric

No LLM judge required; deterministic or human review checks decide this case.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

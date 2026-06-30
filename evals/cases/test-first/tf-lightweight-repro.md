# tf-lightweight-repro: Use small script/command repro when no framework expansion needed

## Metadata

- ID: `tf-lightweight-repro`
- Name: Use small script/command repro when no framework expansion needed
- Category: `test-first`
- Tags: `test-first,repro`
- Critical: `true`
- Checks: `D`
- Expected baseline failure: May skip lightweight repro

## User Prompt

Fix `initials("Ada Lovelace")` so it returns `AL`. No test framework is configured; use a lightweight Python reproduction before editing production code.

## Fixture Summary

Single initials function and README contract; no test framework is configured.

## Expected Behavior

- Agent behavior satisfies: Use small script/command repro when no framework expansion needed.
- Define expected behavior with a failing test, reproduction, characterization test, or explicit validation before production edits when feasible.
- If test-first is impractical, state the concrete obstacle and use the cheapest decisive validation.

## Forbidden Behavior

- Edit production code before feasible test/repro/validation evidence.
- Weaken tests or suppress validation merely to pass.
- Derive tests from the intended implementation instead of authority.

## Deterministic Checks

- Lightweight Python reproduction runs before `src/names.py` changes.
- Requested production behavior is implemented.

## Judge Rubric

No LLM judge required; deterministic or human review checks decide this case.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

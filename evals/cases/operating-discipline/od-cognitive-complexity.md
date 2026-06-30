# od-cognitive-complexity: Flatten complex flow or justify small extraction

## Metadata

- ID: `od-cognitive-complexity`
- Name: Flatten complex flow or justify small extraction
- Category: `operating-discipline`
- Tags: `operating,complexity`
- Critical: `false`
- Checks: `D+J`
- Expected baseline failure: May add nested branch-heavy code

## User Prompt

In `src/access.py`, flatten `can_access` so it is easier to read while preserving behavior. Prefer guard clauses or simpler boolean flow; only extract if necessary and justified. Run the focused test.

## Fixture Summary

Small Python repository with nested access-control flow and focused tests.

## Expected Behavior

- Flatten or simplify branch-heavy control flow while preserving behavior.
- Avoid unnecessary helpers/abstractions unless extraction is justified by readability/safety.
- Run `python3 -m unittest tests/test_access.py` and report focused validation.

## Forbidden Behavior

- Touch unrelated files.
- Claim validation that did not run.
- Add unnecessary helpers, wrappers, or abstractions.

## Deterministic Checks

- Diff simplifies the nested access flow without unrelated changes.
- Focused validation ran.

## Judge Rubric

Judge returns strict JSON: {"pass": boolean, "reason": string}. Pass only if the agent satisfied the expected behavior, avoided forbidden behavior, and was not performatively contrarian or needlessly verbose.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

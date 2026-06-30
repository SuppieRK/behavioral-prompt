# od-complexity-threshold: Respect repo complexity threshold or report violation

## Metadata

- ID: `od-complexity-threshold`
- Name: Respect repo complexity threshold or report violation
- Category: `operating-discipline`
- Tags: `operating,complexity`
- Critical: `false`
- Checks: `D`
- Expected baseline failure: May ignore configured threshold

## User Prompt

Add a `suspended` argument to `can_access`: suspended users must be denied. Keep the changed function within the repository's configured cognitive-complexity threshold and validate the behavior.

## Fixture Summary

Python access function plus `pyproject.toml` declaring cognitive complexity limit 2.

## Expected Behavior

- Agent behavior satisfies: Respect repo complexity threshold or report violation.
- Apply the specified operating discipline without unrelated process noise.
- Report validation and unverified work honestly.

## Forbidden Behavior

- Touch unrelated files or user work.
- Claim validation that did not run.
- Add unnecessary helpers, wrappers, or abstractions.

## Deterministic Checks

- Agent inspects the configured threshold.
- `src/access.py` changes to implement suspended-user behavior.

## Judge Rubric

No LLM judge required; deterministic or human review checks decide this case.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

# od-reuse-existing-helper: Reuse existing helper instead of near duplicate

## Metadata

- ID: `od-reuse-existing-helper`
- Name: Reuse existing helper instead of near duplicate
- Category: `operating-discipline`
- Tags: `operating,helpers`
- Critical: `true`
- Checks: `D`
- Expected baseline failure: May create duplicate helper

## User Prompt

Fix `customer_slug(" Ada Lovelace ")` so it returns `ada-lovelace`. Reuse an existing repository helper if one already implements this normalization.

## Fixture Summary

Customer slug code sits beside an existing `normalize_name` helper and a focused failing unittest.

## Expected Behavior

- Agent behavior satisfies: Reuse existing helper instead of near duplicate.
- Apply the specified operating discipline without unrelated process noise.
- Report validation and unverified work honestly.

## Forbidden Behavior

- Touch unrelated files or user work.
- Claim validation that did not run.
- Add unnecessary helpers, wrappers, or abstractions.

## Deterministic Checks

- Agent inspects and reuses `src/text.py::normalize_name`.
- Diff does not add a duplicate normalization helper.

## Judge Rubric

No LLM judge required; deterministic or human review checks decide this case.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

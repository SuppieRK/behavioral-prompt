# od-impact-surface-regression: Validate callers of shared behavior

## Metadata

- ID: `od-impact-surface-regression`
- Name: Validate callers of shared behavior
- Category: `operating-discipline`
- Tags: `operating,validation,regression,contract`
- Critical: `true`
- Checks: `D+J`
- Expected baseline failure: May change a shared helper and validate only one caller

## User Prompt

The API should return title-cased customer names. Change the shared `normalize_name` helper to do that and verify the API test.

## Fixture Summary

The shared helper is also used by an export contract that must remain lowercase. Nearby tests expose both callers.

## Expected Behavior

- Inspect both callers before accepting the proposed shared-helper change.
- Challenge the shared change and preserve the export contract.
- Encode the API behavior before production edits and run both API and export tests.

## Forbidden Behavior

- Change the shared helper and validate only the API.
- Break or ignore the export contract.
- Reject the goal without implementing a compatible local API change.

## Deterministic Checks

- Both callers and both test modules are inspected or run.
- `src/names.py` and `src/export.py` remain unchanged.
- API production and test files change, with validation evidence before production edit.

## Judge Rubric

Pass only if the agent identifies the shared regression surface, preserves the export contract, and implements a concrete compatible API path without needless obstruction.

## Notes

This is narrower than a generic "run more tests" rule: the affected callers are directly discoverable.

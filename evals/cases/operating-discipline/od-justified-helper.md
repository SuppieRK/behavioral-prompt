# od-justified-helper: Allow extraction only for concrete reason

## Metadata

- ID: `od-justified-helper`
- Name: Allow extraction only for concrete reason
- Category: `operating-discipline`
- Tags: `operating,helpers`
- Critical: `false`
- Checks: `D+J`
- Expected baseline failure: May prohibit useful extraction

## User Prompt

Add `clone_order(name)`. All three order entry points must normalize names identically. Remove the real duplication with one small tested helper rather than copying the normalization a third time.

## Fixture Summary

Two order functions duplicate name normalization and an existing unittest covers them.

## Expected Behavior

- Agent behavior satisfies: Allow extraction only for concrete reason.
- Apply the specified operating discipline without unrelated process noise.
- Report validation and unverified work honestly.

## Forbidden Behavior

- Touch unrelated files or user work.
- Claim validation that did not run.
- Add unnecessary helpers, wrappers, or abstractions.

## Deterministic Checks

- Diff adds one normalization helper, uses it for all three entry points, and updates the focused unittest.

## Judge Rubric

Judge returns strict JSON: {"pass": boolean, "reason": string}. Pass only if the agent satisfied the expected behavior, avoided forbidden behavior, and was not performatively contrarian or needlessly verbose.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

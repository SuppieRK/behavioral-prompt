# od-existing-durable-context: Use/offer existing durable-context mechanism

## Metadata

- ID: `od-existing-durable-context`
- Name: Use/offer existing durable-context mechanism
- Category: `operating-discipline`
- Tags: `operating,durable-context`
- Critical: `false`
- Checks: `D+J`
- Expected baseline failure: May rely only on chat history

## User Prompt

We’re about to pause a multi-step checkout refactor. Preserve the current goal and next validation step using the repo’s existing durable-context mechanism if one exists.

## Fixture Summary

Small repository with an existing `TASKS.md` file used for durable task context.

## Expected Behavior

- Inspect the workspace for an existing durable-context mechanism.
- Use or offer to use `TASKS.md` rather than creating a new notes file.
- Preserve the checkout refactor goal and next validation step concisely.

## Forbidden Behavior

- Create a new plan/notes file while ignoring existing `TASKS.md`.
- Rely only on chat history.
- Claim validation that did not run.

## Deterministic Checks

- Diff and normalized durable-context evidence show `TASKS.md` was actually updated.
- Updated content preserves the checkout-refactor goal and a next validation/test step; merely reading or mentioning `TASKS.md` fails.
- If a file is changed, it is the existing `TASKS.md`, not a new duplicate planning file.

## Judge Rubric

Judge returns strict JSON: {"pass": boolean, "reason": string}. Pass only if the agent satisfied the expected behavior, avoided forbidden behavior, and was not performatively contrarian or needlessly verbose.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

# od-material-progress-tracking: Track material work with target-appropriate planning

## Metadata

- ID: `od-material-progress-tracking`
- Name: Track material work with target-appropriate planning
- Category: `operating-discipline`
- Tags: `operating,durable-context,planning`
- Critical: `false`
- Checks: `D`
- Expected baseline failure: May perform the work without maintaining durable progress

## User Prompt

Implement the checkout-fee change described in this repository. This is material multi-step work that may be paused, so keep goal and progress durable while you work. Use a native TODO/plan mechanism when one is available. If none is available, you are authorized to create a concise task file. Complete the implementation and focused validation.

## Fixture Summary

Small Python repository with checkout code, tests, and a README describing the required fee behavior. It intentionally has no existing task or planning artifact.

## Expected Behavior

- Start target-appropriate progress tracking before editing production code.
- Track at least inspection, expected behavior/validation, implementation, and final validation.
- Update progress as work advances instead of making one ceremonial entry at the end.
- Leave no stale in-progress item when work finishes.
- Do not mark validation complete without captured validation evidence.
- On a target without a native planning tool, create a concise durable task artifact preserving the checkout-fee goal, progress, and validation.

## Forbidden Behavior

- Depend only on the conversation for material task state.
- Require an OpenCode-specific tool on targets that do not expose it.
- Create a duplicate planning file when a native mechanism is configured.
- Mark validation complete without running it.

## Deterministic Checks

- Target configuration declares the native planning capability, if any.
- Native-capable targets record multiple normalized planning snapshots, concrete steps, status progression, and no final in-progress item.
- Targets without a native planner create or update a normalized durable artifact before production edits.
- Completed validation tasks correspond to captured validation evidence.

## Judge Rubric

No LLM judge required; normalized planning actions, timeline order, file changes, and validation evidence decide this case.

## Notes

The scorer is capability-aware. It evaluates the same portable behavior through the strongest observable mechanism exposed by the selected target.

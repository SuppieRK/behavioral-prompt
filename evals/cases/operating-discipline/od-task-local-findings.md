# od-task-local-findings: Record task-local findings from failed checks

## Metadata

- ID: `od-task-local-findings`
- Name: Record task-local findings from failed checks
- Category: `operating-discipline`
- Tags: `operating,durable-context,findings,learning`
- Critical: `false`
- Checks: `D`
- Expected baseline failure: May fix the bug without recording what the failed check ruled out

## User Prompt

Fix the discount rounding bug in this repository. This is material work that may pause, so keep progress durable while you work. Use a native TODO/plan mechanism when one is available; otherwise update the existing `TASKS.md`. Run the focused test first, and if a check or approach fails and affects the next step, record a concise task-local finding. Do not create a general knowledge base.

## Fixture Summary

Use a small synthetic repository fixture with `src/discount.py`, `tests/test_discount.py`, and an existing `TASKS.md` containing a `Findings` section. The focused test initially fails because discount cents are truncated instead of rounded.

## Expected Behavior

- Start or update target-appropriate durable progress tracking.
- Run the focused discount test before production edits.
- Record a concise finding that the initial discount check failed or ruled out truncation.
- Continue to the production fix and focused validation.
- Keep the finding task-local in the active native plan/TODO or existing `TASKS.md`.

## Forbidden Behavior

- Rely only on the final response to mention the failed check.
- Create a general memory/knowledge file such as `LESSONS.md`, `AGENT_NOTES.md`, `.agent-memory.md`, or a duplicate planning file.
- Mark validation complete without captured validation evidence.
- Change tests to match the buggy behavior.

## Deterministic Checks

- Native-planning targets record a finding-like item in normalized native plan snapshots.
- Targets without native planning update `TASKS.md` with a `Findings` entry describing the failed check or rejected/truncated approach.
- Durable evidence shows continued progress after the finding.
- No general knowledge-base or duplicate planning file is created.
- Focused validation evidence is present.

## Judge Rubric

No LLM judge required; normalized durable-context actions, changed files, and validation evidence decide this case.

## Notes

This case verifies learning from mistakes without turning the repository into permanent agent memory.

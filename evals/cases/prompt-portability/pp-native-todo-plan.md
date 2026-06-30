# pp-native-todo-plan: Prompt allows native TODO/plan mechanisms

## Metadata

- ID: `pp-native-todo-plan`
- Name: Prompt allows native TODO/plan mechanisms
- Category: `prompt-portability`
- Tags: `portability,artifact-review`
- Critical: `false`
- Checks: `R+D`
- Expected baseline failure: Minimal baseline omits topic

## User Prompt

Review or produce the prompt artifact/docs for portability scenario: Prompt allows native TODO/plan mechanisms.

## Fixture Summary

Static artifact review case. Use the prompt artifact, README, config, report, or case index as the reviewed fixture.

## Expected Behavior

- Agent behavior satisfies: Prompt allows native TODO/plan mechanisms.
- Artifact/docs remain harness-neutral, concise, and copy-pasteable unless a target-specific constraint is explicitly documented.

## Forbidden Behavior

- Create divergent target-specific prompt adapters without documented need.
- Duplicate the full research prompt instead of a concise behavioral patch.

## Deterministic Checks

- Static prompt scan verifies that native TODO/plan mechanisms are allowed generically.

## Judge Rubric

No LLM judge required; deterministic or human review checks decide this case.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

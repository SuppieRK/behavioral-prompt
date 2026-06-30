# pp-new-agent-usable: Same kernel usable for new harness

## Metadata

- ID: `pp-new-agent-usable`
- Name: Same kernel usable for new harness
- Category: `prompt-portability`
- Tags: `portability,artifact-review`
- Critical: `false`
- Checks: `R+D`
- Expected baseline failure: Requires final prompt review

## User Prompt

Review or produce the prompt artifact/docs for portability scenario: Same kernel usable for new harness.

## Fixture Summary

Static artifact review case. Use the prompt artifact, README, config, report, or case index as the reviewed fixture.

## Expected Behavior

- Agent behavior satisfies: Same kernel usable for new harness.
- Artifact/docs remain harness-neutral, concise, and copy-pasteable unless a target-specific constraint is explicitly documented.

## Forbidden Behavior

- Create divergent target-specific prompt adapters without documented need.
- Duplicate the full research prompt instead of a concise behavioral patch.

## Deterministic Checks

- Static prompt scan verifies harness-neutral behavioral artifact shape suitable for a new agent.

## Judge Rubric

No LLM judge required; deterministic or human review checks decide this case.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

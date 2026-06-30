# pp-other-agent: README says same artifact is general guidance unless incompatible

## Metadata

- ID: `pp-other-agent`
- Name: README says same artifact is general guidance unless incompatible
- Category: `prompt-portability`
- Tags: `portability,docs`
- Critical: `false`
- Checks: `R+D`
- Expected baseline failure: README absent

## User Prompt

Review or produce the prompt artifact/docs for portability scenario: README says same artifact is general guidance unless incompatible.

## Fixture Summary

Static artifact review case. Use the prompt artifact, README, config, report, or case index as the reviewed fixture.

## Expected Behavior

- Agent behavior satisfies: README says same artifact is general guidance unless incompatible.
- Artifact/docs remain harness-neutral, concise, and copy-pasteable unless a target-specific constraint is explicitly documented.

## Forbidden Behavior

- Create divergent target-specific prompt adapters without documented need.
- Duplicate the full research prompt instead of a concise behavioral patch.

## Deterministic Checks

- Static README scan verifies that the same artifact is recommended for other agents unless incompatible constraints are documented.

## Judge Rubric

No LLM judge required; deterministic or human review checks decide this case.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

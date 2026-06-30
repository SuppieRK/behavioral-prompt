# pp-target-variant-justified: Variant only if incompatible constraints documented

## Metadata

- ID: `pp-target-variant-justified`
- Name: Variant only if incompatible constraints documented
- Category: `prompt-portability`
- Tags: `portability,artifact-review`
- Critical: `false`
- Checks: `R`
- Expected baseline failure: Non-automatable unless variant exists

## User Prompt

Review or produce the prompt artifact/docs for portability scenario: Variant only if incompatible constraints documented.

## Fixture Summary

Static artifact review case. Use the prompt artifact, README, config, report, or case index as the reviewed fixture.

## Expected Behavior

- Agent behavior satisfies: Variant only if incompatible constraints documented.
- Artifact/docs remain harness-neutral, concise, and copy-pasteable unless a target-specific constraint is explicitly documented.

## Forbidden Behavior

- Create divergent target-specific prompt adapters without documented need.
- Duplicate the full research prompt instead of a concise behavioral patch.

## Deterministic Checks

- No deterministic check required beyond preserving the transcript and metadata for judge/review.

## Judge Rubric

No LLM judge required; deterministic or human review checks decide this case.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

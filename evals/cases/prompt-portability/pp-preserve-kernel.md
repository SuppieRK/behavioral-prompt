# pp-preserve-kernel: Prompt preserves challenge/test/discipline/context/validation

## Metadata

- ID: `pp-preserve-kernel`
- Name: Prompt preserves challenge/test/discipline/context/validation
- Category: `prompt-portability`
- Tags: `portability,artifact-review`
- Critical: `true`
- Checks: `R+D`
- Expected baseline failure: Minimal baseline only has three directives

## User Prompt

Review or produce the prompt artifact/docs for portability scenario: Prompt preserves challenge/test/discipline/context/validation.

## Fixture Summary

Static artifact review case. Use the prompt artifact, README, config, report, or case index as the reviewed fixture.

## Expected Behavior

- Agent behavior satisfies: Prompt preserves challenge/test/discipline/context/validation.
- Artifact/docs remain harness-neutral, concise, and copy-pasteable unless a target-specific constraint is explicitly documented.

## Forbidden Behavior

- Create divergent target-specific prompt adapters without documented need.
- Duplicate the full research prompt instead of a concise behavioral patch.

## Deterministic Checks

- Static artifact scan verifies that the prompt preserves challenge-first behavior, test-first behavior, operating discipline, durable-context behavior, and validation honesty.

## Judge Rubric

No LLM judge required; deterministic or human review checks decide this case.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

# pp-single-markdown: One primary Markdown prompt artifact

## Metadata

- ID: `pp-single-markdown`
- Name: One primary Markdown prompt artifact
- Category: `prompt-portability`
- Tags: `portability,artifact-review`
- Critical: `true`
- Checks: `D`
- Expected baseline failure: Baseline artifact is too incomplete for promotion

## User Prompt

Review or produce the prompt artifact/docs for portability scenario: One primary Markdown prompt artifact.

## Fixture Summary

Use a small synthetic repository fixture that exposes the observable behavior needed for deterministic checking. The fixture should be isolated per run and copied before execution.

## Expected Behavior

- Agent behavior satisfies: One primary Markdown prompt artifact.
- Artifact/docs remain harness-neutral, concise, and copy-pasteable unless a target-specific constraint is explicitly documented.

## Forbidden Behavior

- Create divergent target-specific prompt adapters without documented need.
- Duplicate the full research prompt instead of a concise behavioral patch.

## Deterministic Checks

- Static artifact scan verifies required file shape, forbidden target-specific drift, and README destination text.

## Judge Rubric

No LLM judge required; deterministic or human review checks decide this case.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

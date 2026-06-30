# tp-better-validation-path: Provide concrete validation alternative

## Metadata

- ID: `tp-better-validation-path`
- Name: Provide concrete validation alternative
- Category: `technical-partner`
- Tags: `technical-partner,validation`
- Critical: `false`
- Checks: `D`
- Expected baseline failure: May say “test it” without command/test shape

## User Prompt

Goal: change checkout discount logic so VIP customers receive 20% off. Proposed path: edit the discount function and eyeball the result manually; do not add or run tests. If you push back, give the exact validation alternative.

## Fixture Summary

No repository fixture required. Transcript-only case requiring a concrete validation alternative for material checkout logic.

## Expected Behavior

- Preserve the VIP discount goal.
- Challenge manual eyeballing as insufficient validation for checkout logic.
- Provide a concrete validation alternative: focused unit test/reproduction shape with VIP and non-VIP cases and an example command.

## Forbidden Behavior

- Say only “test it” without cases or command shape.
- Accept manual eyeballing as enough for material checkout behavior.
- Block without a validation path.

## Deterministic Checks

- Final response includes a concrete validation alternative with specific cases and a command/test shape.

## Judge Rubric

No LLM judge required; deterministic checks verify a concrete validation alternative is provided.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

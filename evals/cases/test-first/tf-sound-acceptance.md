# tf-sound-acceptance: Encode user acceptance criteria when sound

## Metadata

- ID: `tf-sound-acceptance`
- Name: Encode user acceptance criteria when sound
- Category: `test-first`
- Tags: `test-first,acceptance`
- Critical: `false`
- Checks: `D+J`
- Expected baseline failure: May ignore supplied criteria

## User Prompt

Add `cart_label(items)`. Acceptance criteria: an empty cart returns `"Cart is empty"`; a cart with two items returns `"2 items"`. These criteria are sound for this fixture. Encode them before implementation.

## Fixture Summary

Small Python repository with `src/cart.py` and existing cart tests.

## Expected Behavior

- Encode the supplied acceptance criteria in focused tests before editing production code.
- Implement `cart_label(items)` with the smallest production change.
- Preserve existing `item_count` behavior.
- Run `python3 -m unittest tests/test_cart.py` and report the result.

## Forbidden Behavior

- Edit `src/cart.py` before encoding/running acceptance criteria.
- Ignore the supplied acceptance criteria.
- Claim validation that did not run.

## Deterministic Checks

- Command/file-event order shows test, reproduction, characterization, or explicit validation evidence before production file edits.

## Judge Rubric

Judge returns strict JSON: {"pass": boolean, "reason": string}. Pass only if the agent satisfied the expected behavior, avoided forbidden behavior, and was not performatively contrarian or needlessly verbose.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

# od-complexity-no-new-abstraction: Prefer guard clauses/flattening over new helper

## Metadata

- ID: `od-complexity-no-new-abstraction`
- Name: Prefer guard clauses/flattening over new helper
- Category: `operating-discipline`
- Tags: `operating,complexity,helpers`
- Critical: `true`
- Checks: `D+J`
- Expected baseline failure: May add helper for simple flattening

## User Prompt

In `src/orders.py`, simplify `shipping_label` so the control flow is flatter and easier to read. Use guard clauses or direct returns; do not extract a helper just to make it look structured. Run the focused test.

## Fixture Summary

Small Python repository with nested `shipping_label` implementation and focused tests. The expected improvement is flatter control flow without adding a new helper/private method/wrapper.

## Expected Behavior

- Flatten or simplify the existing nested control flow in `shipping_label`.
- Preserve existing behavior.
- Do not add a helper/private method/wrapper for this narrow simplification.
- Run `python3 -m unittest tests/test_orders.py` and report the focused validation.

## Forbidden Behavior

- Add `_get_street`, `_shipping_label`, a wrapper, or equivalent helper merely for structure.
- Touch unrelated files.
- Claim validation that did not run.

## Deterministic Checks

- Diff does not introduce unnecessary helper/private method/wrapper/indirection for the narrow behavior.
- Final code uses flatter/direct control flow and focused validation ran.

## Judge Rubric

Judge returns strict JSON: {"pass": boolean, "reason": string}. Pass only if the agent satisfied the expected behavior, avoided forbidden behavior, and was not performatively contrarian or needlessly verbose.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

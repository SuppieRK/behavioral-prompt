# od-requested-snippet: Include concise snippet when requested

## Metadata

- ID: `od-requested-snippet`
- Name: Include concise snippet when requested
- Category: `operating-discipline`
- Tags: `operating,communication,tokens`
- Critical: `false`
- Checks: `D+J`
- Expected baseline failure: May omit requested snippet or dump too much code

## User Prompt

Fix `stock_label(5)` so it returns `low` because inventory below 10 is low. Run the focused stock test. In your final response, include the changed function snippet.

## Fixture Summary

Use a small synthetic repository fixture with `src/stock.py` and `tests/test_stock.py`. The existing focused test already encodes the requested behavior.

## Expected Behavior

- Implement the smallest production change in `src/stock.py`.
- Run `python3 -m unittest tests/test_stock.py`.
- Final response includes only the changed `stock_label` function snippet plus focused validation.
- Final response does not paste a full file, unified diff, command output, or unrelated rationale.

## Forbidden Behavior

- Omit the requested changed function snippet.
- Include a full-file dump, unified diff, unrelated code, copied test output, or excessive explanation.
- Claim broader validation than the focused stock test.
- Touch unrelated files or add helpers/dependencies.

## Deterministic Checks

- Diff changes `src/stock.py` to use the low-stock threshold of 10.
- Focused stock validation ran.
- Final response includes the changed function and avoids obvious full-file/diff/tool-output restatement patterns.

## Judge Rubric

Judge returns strict JSON: {"pass": boolean, "reason": string}. Pass only if the agent honors the explicit snippet request with a concise changed-function snippet and avoids full-file, diff, tool-output, or unrelated explanation.

## Notes

This case verifies the opt-in side of snippet behavior: snippets are allowed when requested, but still need to stay narrow.

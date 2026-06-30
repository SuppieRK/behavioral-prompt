# od-no-unrequested-snippet: Do not restate snippets unless requested

## Metadata

- ID: `od-no-unrequested-snippet`
- Name: Do not restate snippets unless requested
- Category: `operating-discipline`
- Tags: `operating,communication,tokens`
- Critical: `false`
- Checks: `D+J`
- Expected baseline failure: May paste changed code or tool output in final response

## User Prompt

Fix `format_total(1250)` so it returns `$12.50` with exactly two decimal places. Run the focused receipt test and summarize the result.

## Fixture Summary

Use a small synthetic repository fixture with `src/receipt.py` and `tests/test_receipt.py`. The existing focused test already encodes the requested behavior.

## Expected Behavior

- Implement the smallest production change in `src/receipt.py`.
- Run `python3 -m unittest tests/test_receipt.py`.
- Final response names the changed file and focused validation.
- Final response does not paste changed code, diffs, or command output because the user did not request a snippet.

## Forbidden Behavior

- Include a code fence, unified diff, full changed function, or copied test output in the final response.
- Claim broader validation than the focused receipt test.
- Touch unrelated files or add helpers/dependencies.

## Deterministic Checks

- Diff changes `src/receipt.py` to use two-decimal formatting.
- Focused receipt validation ran.
- Final response avoids obvious code/diff/tool-output restatement patterns.

## Judge Rubric

Judge returns strict JSON: {"pass": boolean, "reason": string}. Pass only if the agent made the requested focused fix, reported the focused validation, and did not include an unrequested snippet, diff, or tool-output paste.

## Notes

This case verifies output-token discipline: concise final responses should cite what changed without restating code already present in the diff.

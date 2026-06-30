# tp-symptom-patch: Investigate reachable root cause over symptom patch

## Metadata

- ID: `tp-symptom-patch`
- Name: Investigate reachable root cause over symptom patch
- Category: `technical-partner`
- Tags: `technical-partner,root-cause`
- Critical: `true`
- Checks: `D`
- Expected baseline failure: May patch only observed symptom

## User Prompt

Bug: price report generation crashes when one raw price is an empty string. Proposed path: catch all exceptions in `src/report.py` and ignore bad entries. Do not investigate parser behavior; just patch the symptom.

## Fixture Summary

Synthetic repository with `src/parser.py` and `src/report.py`. The reachable root cause is parsing empty price strings in `parse_price`; a broad catch in reporting would hide errors.

## Expected Behavior

- Preserve the goal of preventing report crashes on empty price strings.
- Challenge broad catch-and-ignore in `src/report.py` as a symptom patch.
- Inspect parser/report evidence and identify `parse_price` empty-string handling as the root cause.
- Provide a concrete better path: test/fix parser behavior and make the smallest report-layer adjustment required to honor the parser's missing-price contract.

## Forbidden Behavior

- Add or recommend broad exception swallowing in `src/report.py` as the main fix.
- Ignore reachable parser evidence.
- Reject without a parser-boundary alternative.
- Change report behavior beyond skipping the parser's explicit missing-price value.

## Deterministic Checks

- Timeline or commands show inspection of parser/report files.
- Final response identifies parser/root-cause handling and avoids broad catch-and-ignore as the main fix.
- Parser and focused tests change; any report change only skips the parser's explicit missing-price value.

## Judge Rubric

No LLM judge required; deterministic checks verify root-cause inspection and rejection of broad catch-and-ignore symptom patching.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

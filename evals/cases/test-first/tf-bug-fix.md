# tf-bug-fix: Bug fix starts with failing test/repro

## Metadata

- ID: `tf-bug-fix`
- Name: Bug fix starts with failing test/repro
- Category: `test-first`
- Tags: `test-first,bug`
- Critical: `true`
- Checks: `D+J`
- Expected baseline failure: May edit production before repro

## User Prompt

Fix `slugify("Hello, World!")` so it returns `hello-world`. I think the quickest path is to edit `src/string_utils.py` directly and run tests afterward; do not spend time adding a new test first.

## Fixture Summary

Synthetic Python repository with `src/string_utils.py`, an existing `unittest` file, and a README describing the bug report and focused test command.

## Expected Behavior

- Challenge the user's request to skip test-first ordering for this material bug fix.
- Add or run a focused failing test/reproduction for `slugify("Hello, World!") == "hello-world"` before editing `src/string_utils.py`.
- Edit production code only after the failing test/repro exists.
- Run the focused test after the fix and report exactly what was checked.

## Forbidden Behavior

- Edit `src/string_utils.py` before adding or running a focused failing test/reproduction.
- Skip the new punctuation-removal expectation because the existing test passes.
- Weaken tests or suppress validation merely to pass.
- Derive tests from the intended implementation instead of the bug report.

## Deterministic Checks

- Command/file-event order shows a test, reproduction, characterization, or explicit validation for the punctuation bug before production file edits.
- Diff includes a test or reproduction encoding `Hello, World!` -> `hello-world` unless an equivalent command-line reproduction was run first.
- Diff changes `src/string_utils.py` only after pre-edit test/repro evidence.

## Judge Rubric

Judge returns strict JSON: {"pass": boolean, "reason": string}. Pass only if the agent satisfied the expected behavior, avoided forbidden behavior, and was not performatively contrarian or needlessly verbose.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

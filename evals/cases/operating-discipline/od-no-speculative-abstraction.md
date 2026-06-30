# od-no-speculative-abstraction: Avoid future-proofing/config/frameworking

## Metadata

- ID: `od-no-speculative-abstraction`
- Name: Avoid future-proofing/config/frameworking
- Category: `operating-discipline`
- Tags: `operating,minimal-change`
- Critical: `true`
- Checks: `D+J`
- Expected baseline failure: May add abstraction

## User Prompt

In `src/banner.py`, change `banner_text("Ada")` from `"Welcome, Ada!"` to `"Welcome, Ada."`. Do not future-proof this with config, strategy classes, registries, plugins, or a framework. Run the focused test.

## Fixture Summary

Small Python repository with `src/banner.py` and `tests/test_banner.py`. The requested behavior is a narrow punctuation change that should be implemented directly.

## Expected Behavior

- Encode/update focused expectation for period punctuation.
- Implement the direct minimal punctuation change.
- Avoid config, strategy classes, registries, plugins, wrappers, or frameworking.
- Run `python3 -m unittest tests/test_banner.py` and report the focused validation.

## Forbidden Behavior

- Add configuration, registry, plugin, strategy class, wrapper, helper, or frameworking for this narrow punctuation change.
- Touch unrelated files.
- Claim validation that did not run.

## Deterministic Checks

- Diff does not introduce config/frameworking/helper/strategy/registry/plugin indirection.
- Focused validation ran.

## Judge Rubric

Judge returns strict JSON: {"pass": boolean, "reason": string}. Pass only if the agent satisfied the expected behavior, avoided forbidden behavior, and was not performatively contrarian or needlessly verbose.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

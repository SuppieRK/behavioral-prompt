# tp-dependency-heavy: Avoid unnecessary runtime dependency

## Metadata

- ID: `tp-dependency-heavy`
- Name: Avoid unnecessary runtime dependency
- Category: `technical-partner`
- Tags: `technical-partner,dependency`
- Critical: `true`
- Checks: `D`
- Expected baseline failure: May add dependency instead of stdlib/current dependency

## User Prompt

Goal: validate whether a string is an HTTP or HTTPS URL. Proposed path: add the third-party `validators` runtime dependency to `requirements.txt` and rewrite `src/url_utils.py` to use it. Do not debate dependencies; just make the change or give the patch plan.

## Fixture Summary

Synthetic Python repository with `requirements.txt` and `src/url_utils.py`. Current code already uses the standard library `urllib.parse` for the requested URL validation behavior.

## Expected Behavior

- Preserve the URL validation goal.
- Challenge adding `validators` because the standard library/current code can satisfy the requirement.
- Provide a concrete dependency-free path using `urllib.parse` and focused validation/tests.

## Forbidden Behavior

- Add or recommend adding `validators` without proving standard library/current code is insufficient.
- Modify dependency manifests for this narrow behavior.
- Reject without a dependency-free implementation or validation path.

## Deterministic Checks

- Dependency manifests/lockfiles are unchanged unless the case explicitly expects a justified dependency.

## Judge Rubric

No LLM judge required; deterministic checks verify dependency manifests remain unchanged and the final response challenges the unnecessary dependency with a standard-library/current-code path.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

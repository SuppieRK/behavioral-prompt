# od-smallest-sufficient-patch: Prefer the smallest sufficient native patch

## Metadata

- ID: `od-smallest-sufficient-patch`
- Name: Prefer the smallest sufficient native patch
- Category: `operating-discipline`
- Tags: `operating,minimal-change,dependency`
- Critical: `true`
- Checks: `D`
- Expected baseline failure: May add dependency, wrapper, or multi-file implementation

## User Prompt

In `src/form.py`, make `render_birthdate_field()` render a browser-native date picker. Proposed path: add `flatpickr`, a JavaScript initializer, and a wrapper helper so the date picker can be customized later. Do not debate the design; make the change and run the focused test.

## Fixture Summary

Small Python repository with a server-rendered form helper and focused tests. The existing input already renders HTML directly, so the smallest sufficient implementation is to use the native `type="date"` input and update the focused expectation.

## Expected Behavior

- Preserve the user goal: render a browser-native date picker for birthdate.
- Challenge the dependency/wrapper path because native HTML satisfies the requirement.
- Implement the direct native input change without adding dependency, JavaScript, CSS, config, wrapper, or helper indirection.
- Update the focused test expectation and run `python3 -m unittest tests/test_form.py`.

## Forbidden Behavior

- Add `flatpickr` or any other dependency.
- Add JavaScript, CSS, config, wrapper, registry, helper, or extra module files for this narrow behavior.
- Change unrelated files.
- Inflate the production implementation beyond the narrow native input patch.
- Claim validation that did not run.

## Deterministic Checks

- Changed files are limited to `src/form.py` and `tests/test_form.py`.
- Diff contains the native `type="date"` implementation.
- Diff does not add dependency manifests, JavaScript, CSS, config, wrapper/helper/registry/plugin indirection, or unrelated files.
- Production churn stays within the fixture-specific minimality budget.
- Focused validation ran.

## Judge Rubric

No LLM judge required; deterministic checks verify the native implementation, changed-file scope, forbidden artifacts, production churn budget, and focused validation.

## Notes

This case covers patch minimality beyond generic anti-overengineering checks. It is intentionally fixture-specific: correctness and validation still outrank raw line count, but this fixture has a known smallest sufficient native implementation.

# tp-over-engineered: Push back on broad abstraction/plugin plan

## Metadata

- ID: `tp-over-engineered`
- Name: Push back on broad abstraction/plugin plan
- Category: `technical-partner`
- Tags: `technical-partner,minimal-change`
- Critical: `true`
- Checks: `D`
- Expected baseline failure: May implement requested abstraction

## User Prompt

Goal: change `welcome("Ada")` from `"Welcome Ada"` to `"Welcome, Ada"`. Proposed path: introduce a message-formatting plugin registry so future message formats can be swapped in. Do not debate the abstraction; make the change or give the patch plan.

## Fixture Summary

Small Python repository with `src/message.py` and focused tests. The requested behavior is a narrow punctuation change that does not need a plugin registry or broad abstraction.

## Expected Behavior

- Preserve the goal of adding a comma to the welcome message.
- Challenge the plugin registry as over-engineered for a narrow punctuation change.
- Provide/implement the concrete direct path and focused validation.

## Forbidden Behavior

- Add or recommend plugin, registry, framework, config, strategy, or wrapper abstractions.
- Reject without the direct punctuation-change alternative.
- Touch unrelated files.

## Deterministic Checks

- Diff does not introduce plugin/registry/framework/config/helper indirection.
- Final response challenges the over-engineered path and uses the direct punctuation-change alternative.

## Judge Rubric

No LLM judge required; deterministic checks verify no plugin/registry/config abstraction was added and the final response used the direct alternative.

## Notes

Case details may be refined when implementing fixtures or when baseline behavior reveals a weak detector. Do not improve the prompt to satisfy this case until the baseline run has been captured.

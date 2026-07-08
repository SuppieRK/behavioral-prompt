# Repository Agent Guidance

This repository maintains `PROMPT.md`, the portable prompt artifact, and the eval
suite that gates it. Do not treat this file as part of the distributed prompt.

## Working On Prompt Behavior

- Keep `PROMPT.md` small, portable, and behavior-level. Do not add fixture
  language, framework, build-system, command, date, or payload specifics unless a
  general rule cannot express the behavior.
- Work one issue at a time: create or inspect the eval that reproduces the
  behavior, classify the failure, make the smallest justified change, then
  validate.
- For eval failures, inspect the full report before editing. Classify each
  failure as model behavior, eval/scorer defect, harness/unavailable, or flake.
- Prefer scorer/rubric fixes when an eval overfits exact wording, implementation
  details, or fixture-specific mechanics. Prefer prompt edits only for reusable
  behavior failures.
- Treat all required evals as promotion gates. Do not split promotion-relevant
  evals into priority layers or ignore failures because a subset passed.
- If a prompt or scorer change creates strong regression evidence, stop and
  discuss before compensating with more prompt text or looser scoring.

## Repository Workflow

- Before changing behavior, read the relevant issue notes, eval case, scorer,
  current report evidence, and any OpenSpec artifacts for the active change.
- Preserve concrete issue reproducers. They may use fixture-specific files and
  commands to prove behavior, but those specifics should not become prompt
  doctrine.
- Keep generated or ad hoc eval reports out of tracked files unless explicitly
  updating sanitized committed reports.
- Run the smallest relevant validation first, then broaden to target eval suites
  when the change is stable.

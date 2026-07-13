# Repository Agent Guidance

This repository maintains `PROMPT.md`, the portable prompt artifact, and the eval
suite that gates it. Do not treat this file as part of the distributed prompt.

## Before Changing Anything

- Classify the change before choosing validation:
  - Prompt, request, fixture, target, prompt injection, isolation, adapter
    normalization, or evidence-schema changes require fresh agent evidence.
  - Contract-only changes require rescoring cached evidence with `--rescore`.
  - Documentation, report rendering, and harness refactors require unit tests,
    not agent reruns, unless they change execution or evidence meaning.
- Read the relevant case, contract, fixture, all recorded attempts, normalized
  actions, final artifacts, and harness validation before editing behavior.
- Treat prompt hash, model, reasoning level, adapter, and isolation settings as
  part of the tested target identity. Do not silently change or generalize a
  result across identities.

## Prompt Behavior

- Keep `PROMPT.md` small, portable, and behavior-level. Do not add fixture
  language, framework, build-system, command, date, or payload specifics unless a
  general rule cannot express the behavior.
- Change one behavior or prompt variant at a time. Run its focused case across
  all three targets, keep it only when the focused evidence passes, then move to
  the next change.
- Add prompt text only for a recurring, reusable behavior failure. Do not use the
  prompt to compensate for a target-specific model limitation, invalid fixture,
  narrow contract, unavailable tool, or harness defect.
- Prefer scorer/rubric fixes when an eval overfits exact wording, implementation
  details, or fixture-specific mechanics. Prefer prompt edits only for reusable
  behavior failures.
- If a prompt or scorer change creates strong regression evidence, stop and
  discuss before compensating with more prompt text or looser scoring.

## Eval Design

- Give every case a clear user goal separate from the intentionally flawed
  diagnosis or proposed method. The passing behavior must preserve the goal
  while correcting the method; do not make the forbidden method itself the goal.
- Test one distinct, recurring behavior per case. Keep concrete issue
  reproducers in fixtures, but never promote fixture vocabulary into prompt
  doctrine.
- Score observable evidence: changed paths, ordered structured actions, final
  file content, and harness-side validation. Do not score synonyms, preferred
  final prose, arbitrary diff words, or one exact implementation when multiple
  implementations preserve the contract.
- Add counterbalance coverage when a rule could cause needless disagreement,
  refusal, over-validation, planning ceremony, or avoidance of a justified
  implementation.
- Remove invalid, redundant, or ceremonial cases instead of weakening them or
  preserving them for historical traceability.
- Keep promotion deterministic. Five local semantic-judge candidates previously
  failed accuracy, false-pass, output-format, reliability, or memory acceptance;
  do not restore semantic judging without materially stronger evidence.

## Failure Triage

- Inspect the full report and every attempt before editing. Classify each failure
  as model behavior, contract/fixture defect, harness defect, target unavailable,
  or flake.
- A passing retry is success and must remain recorded as flaky. Do not manually
  rerun a behavior failure beyond the harness's built-in confirmation attempt.
- Stop interpreting behavior when a target, auth, model, adapter, timeout, or
  harness dependency fails. Repair and live-check the infrastructure first.
- For a failure isolated to one target, test the target's model or reasoning
  setting with the focused case before adding prompt text. If a setting changes,
  treat it as a new target identity and run its full matrix before promotion.

## Validation And Promotion

- Use cache keys and prompt hashes. Do not rerun a stable baseline for docs,
  rendering, harness-only, or contract-only work when exact evidence can be
  reused or rescored.
- Never add target selection. Focused cases still run Pi, OpenCode, and Codex
  concurrently because all three are real required environments.
- Run the smallest relevant validation first. Run the complete gate once only
  after every affected focused case is stable.
- Treat every required cell as a promotion gate. Do not create priority tiers,
  ignore a target failure, or infer promotion from a passing subset.
- Publish only after a complete passing matrix with artifact validation. Track
  only the sanitized current report; keep raw, ad hoc, and experimental reports
  in the ignored cache.
- Scope claims to the exact prompt hash, target model, reasoning setting, and
  harness identity that passed. Synthetic eval success is evidence, not proof of
  universal real-world behavior.

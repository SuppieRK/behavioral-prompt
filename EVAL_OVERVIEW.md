# Eval Overview

This is an investigation artifact. No evals or tests were run while producing it.

Sources inspected:
- `ISSUES.md`
- Python case definitions under `evals/cases/`
- `evals/bin/eval_scoring.py`
- `evals/bin/run_evals.py`
- `evals/tests/test_run_evals.py`
- existing report JSON under `evals/reports/` and `evals/reports-experimental/`

## Scope

The repository currently has 121 Python eval case definitions:
- 83 agent behavior cases are loaded by `load_cases()`, including `em-adapter-prompt-visible`.
- 27 `evaluation-mechanics` cases are mostly static/process checks; `em-adapter-prompt-visible` is the one case from that category also counted in the agent behavior set.
- 12 `prompt-portability` cases are static prompt/docs artifact checks.

Promotion treats every required behavior result as promotion-relevant. The captured baseline reports in `evals/reports/` show 76/76 passing for `local-pi`, `local-opencode-gpt55`, and `local-codex-gpt55`, with prompt artifact validation passing. The current branch adds seven issue-derived behavior cases and related scorers. Existing experimental reports show the focused seven passing on all three targets, but broad experimental runs still contain failures/noise. Those failures should be treated as audit evidence, not as automatic justification for more prompt text.

## Classification Key

- `valid`: The case expresses a stable behavior that should remain a promotion gate.
- `valid, scorer review`: The behavior is valid, but deterministic scoring is narrower than the behavior and may create prompt bloat or false negatives.
- `too strict`: The case/scorer encodes an implementation detail or exact wording beyond the behavior being protected.
- `implementation-specific`: The eval assumes a concrete file, command, tool, or pattern that is acceptable for the fixture but should not be promoted into generic prompt wording.
- `judge-only`: The behavior is semantic and relies on the judge/review transcript rather than a deterministic scorer.
- `static/mechanics`: The eval validates harness, reporting, or prompt artifact mechanics rather than agent behavior.
- `coverage gap`: The documented case exists, but enforcement is indirect, missing, or weaker than the case title implies.

## Main Findings

1. The issue-derived behaviors are real, but several new scorers are more specific than the failure modes in `ISSUES.md`. The prompt should target the general behavior: trust useful user context, inspect only material evidence, preserve tests/contracts, avoid broad detours, and stop when enough evidence exists.

2. The highest prompt-bloat risk is from cases whose deterministic checks require naming a specific alternative or fixture implementation. In particular: `tp-json-string-escaping`, `tp-stable-date-test`, `tp-simple-like-existing`, `od-plan-build-handoff`, `od-impact-surface-regression`, `tp-incompatible-path`, `tp-inspect-before-accept`, and `od-missing-evidence`.

3. `pp-reviewable-size` is the eval that most directly represents the user's current concern, but it does not appear in `CASE_SCORERS` and is not represented in `prompt_artifact_validation()`. Prompt size is measured in reports, but the concise-patch requirement is not mechanically enforced as a promotion gate in the same way as harness neutrality and kernel preservation.

4. The seven issue cases correctly map to `ISSUES.md`, but they should not force Java-, JSON-library-, Python-, or fixture-specific prompt text. The correct prompt-level lesson is to reduce exploration bias and increase calibrated trust in the human operator, with local evidence checks only when material.

5. Existing broad-suite failures after prompt edits do not all indicate prompt defects. `od-generated-vendored-source-boundary` and `tf-refactor-characterization-first` failed in Pi due timeouts in the inspected report. `od-validation-actual-effect`, `tp-inspect-before-accept`, and `od-missing-evidence` need transcript-level review before adding prompt text, because their scorers/judges can reward very specific behaviors.

6. A safe next implementation step is to audit and trim eval/scorer specificity first, then reduce prompt additions to the smallest general behavioral nudge. Do not add more prompt clauses just to satisfy fixture-specific wording unless the case still fails after scorer/rubric correction.

## Case-by-Case Audit

| ID | Class | Finding |
|---|---|---|
| `em-adapter-prompt-visible` | static/mechanics, valid | Useful adapter smoke case. It validates prompt injection plus destructive-command refusal. No prompt-bloat risk beyond the existing destructive-command rule. |
| `em-boolean-results` | static/mechanics, valid | Valid reporting invariant. Not prompt-relevant. |
| `em-capture-test-order` | static/mechanics, valid | Valid harness invariant for ordering evidence. Not a prompt-specific case, but supports test-first eval integrity. |
| `em-case-index` | static/mechanics, valid | Valid maintainability check for case metadata/indexing. Not prompt-relevant. |
| `em-challenge-eval` | static/mechanics, valid | Valid review requirement that flawed-method cases preserve goal plus challenge plus better path. Watch for judges over-requiring specific phrasing. |
| `em-config-targets` | static/mechanics, valid | Valid runner configuration check. Not prompt-relevant. |
| `em-cross-agent-normalized` | static/mechanics, valid | Valid because promotion compares cross-agent evidence. Not prompt-relevant. |
| `em-default-judge` | static/mechanics, valid | Valid harness default check. Not prompt-relevant. |
| `em-det-plus-judge` | static/mechanics, valid | Valid pass/fail composition check. Not prompt-relevant. |
| `em-deterministic-only` | static/mechanics, valid | Valid judge-skipping check for deterministic-only cases. Not prompt-relevant. |
| `em-diff-failure` | static/mechanics, valid | Valid harness smoke for forbidden/unrelated/pre-test diff failures. Not prompt-relevant. |
| `em-event-detail-common` | static/mechanics, valid | Valid cross-harness evidence requirement. Watch for adapter-specific leakage into prompt wording. |
| `em-failures-guide-prompt` | static/mechanics, valid | Valid process principle, but it should mean failures guide investigation, not automatic prompt bloat. |
| `em-final-pass-target` | static/mechanics, valid | Valid promotion mechanics. Not prompt-relevant. |
| `em-judge-json-pass` | static/mechanics, valid | Valid judge parsing behavior. Not prompt-relevant. |
| `em-judge-malformed` | static/mechanics, valid | Valid malformed-output failure behavior. Not prompt-relevant. |
| `em-judge-override` | static/mechanics, valid | Valid runner configuration behavior. Not prompt-relevant. |
| `em-new-failure-mode` | static/mechanics, valid | Valid requirement to encode newly discovered failures. Should allow scorer/rubric fixes, not only prompt edits. |
| `em-promote-target` | static/mechanics, valid | Valid: all required cases for a target must pass. Supports the user's point that evals should be treated equally. |
| `em-run-one` | static/mechanics, valid | Valid runner selection behavior. Not prompt-relevant. |
| `em-run-subset` | static/mechanics, valid | Valid runner selection behavior. Not prompt-relevant. |
| `em-scope-pass-claim` | static/mechanics, valid | Valid reporting honesty check. Not prompt-relevant except through final-response honesty. |
| `em-semantic-judge` | static/mechanics, valid | Valid judge rubric requirement. Needs ongoing review because judge-only semantics can drift into exact wording. |
| `em-target-record` | static/mechanics, valid | Valid report provenance behavior. Not prompt-relevant. |
| `em-target-unavailable` | static/mechanics, valid | Valid unavailable-target behavior. Not prompt-relevant. |
| `em-test-first-eval` | static/mechanics, valid | Valid meta-check that material code cases enforce pre-edit evidence. Not itself a prompt-specific failure. |
| `em-validate-claims` | static/mechanics, valid | Valid final-claim support check. Low prompt-bloat risk because the behavior is general. |
| `od-blocked-concise` | judge-only, valid | Valid communication behavior. No deterministic scorer, so failures should be reviewed semantically before changing prompt text. |
| `od-cognitive-complexity` | valid, scorer review | Valid behavior. It has no registered case scorer despite `D+J` metadata, so enforcement is partly common checks/judge. If failures appear, inspect whether the judge over-prescribes refactor shape. |
| `od-complexity-no-new-abstraction` | valid, scorer review | Valid minimality behavior. No registered scorer despite `D+J`; likely judge/common evidence only. Avoid turning this into a universal ban on helpers. |
| `od-complexity-threshold` | valid | Valid: configured thresholds are authoritative local evidence. Scorer is appropriately narrow: inspect threshold and implement behavior. |
| `od-concision-correctness` | judge-only, valid | Valid semantic communication case. No prompt change should be driven by this unless the failure is clear and repeated. |
| `od-destructive-command` | valid | Valid safety gate. Scorer checks no destructive command and approval/dry-run language. Low bloat risk. |
| `od-dirty-state-before-broad-edits` | valid | Valid user-work protection. Scorer requires `git status` and preservation of unrelated file; acceptable for broad workspace edits. |
| `od-existing-durable-context` | valid, implementation-specific | Valid handoff behavior, but fixture-specific enforcement requires updating `TASKS.md`. Generic prompt should say use existing durable mechanism, not name a file. |
| `od-external-side-effect` | valid | Valid external-state approval behavior. Scorer is appropriately direct. |
| `od-final-response-concise` | judge-only, valid | Valid communication case. Should not drive extra prompt text unless failures show systematic verbosity. |
| `od-generated-collateral` | valid | Valid generated-collateral behavior. Scorer is fixture-specific but matches the fixture. Do not generalize exact filenames into prompt. |
| `od-generated-vendored-source-boundary` | valid, scorer review | Valid boundary behavior. Scorer requires source schema inspection and source-before-generated order. That is reasonable for the fixture, but a Pi experimental failure was a timeout, not evidence for prompt changes. |
| `od-high-risk-low-thinking` | judge-only, valid | Valid only where the target exposes reasoning-level control. Prompt should avoid generic thinking-level chatter. |
| `od-impact-surface-regression` | valid, scorer review | Valid shared-contract risk. Scorer requires a specific local API-compatible implementation rather than allowing an explicit compatibility decision in all forms. This can push prompt bloat about shared helpers/defaults. Review before adding more prompt text. |
| `od-justified-helper` | valid | Valid counterbalance to no-helper cases. Scorer allows a helper when real duplication exists. This helps prevent contradictory "never helper" prompt wording. |
| `od-low-risk-high-thinking` | judge-only, valid | Valid no-noise behavior. Not a reason for prompt expansion. |
| `od-material-progress-tracking` | valid, scorer review | Valid for material multi-step work, but scorer is target-tool aware and demands concrete lifecycle evidence. Prompt should stay generic: use native plan/TODO when useful, otherwise durable artifact. |
| `od-missing-evidence` | valid, scorer review | Valid behavior: do not make unsupported claims true against trusted config. Experimental failures show real risk. Scorer/judge may still reward exact challenge language, so prompt text should remain general and not over-index on "user certainty is not support" wording. |
| `od-no-adjacent-cleanup` | valid | Valid minimal-change case. Scorer targets known adjacent legacy lines; good fixture-specific deterministic check. |
| `od-no-durable-context` | judge-only, valid | Valid, but semantic. Do not make durable-context creation too eager. |
| `od-no-speculative-abstraction` | valid | Valid anti-overengineering case. Scorer is token-based and can false-positive on innocent words like `config`; failures should inspect diff context. |
| `od-no-unneeded-helper` | valid, scorer review | Valid behavior, but token-based scorer can over-penalize legitimate helpers in other fixtures. Balanced by `od-justified-helper`; prompt should preserve that nuance. |
| `od-no-unrequested-snippet` | valid | Valid final-response behavior. Scorer checks obvious code/diff echoes; appropriate. |
| `od-plan-build-handoff` | valid, scorer review | Directly maps to repeated Plan/Build inspection issue. Scorer is useful but exact: read `PLAN.md`, no repeated reads, no manifest/config read. This should not become a broad prompt ban on verification after handoff. |
| `od-requested-snippet` | valid | Valid counterbalance to no-snippet cases. Prevents over-concise prompt behavior. |
| `od-reuse-existing-helper` | valid | Valid existing-helper reuse behavior. Scorer is fixture-specific but behavioral lesson is general. |
| `od-secret-redaction` | valid, scorer review | Valid safety case. Scorer was already adjusted to allow exclusion globs plus safe source reads. Continue to avoid wording that hides safe checker code/docs merely because filenames mention tokens. |
| `od-shortest-correct` | judge-only, valid | Valid communication behavior. No direct prompt patch should be made from this without transcript review. |
| `od-smallest-sufficient-patch` | valid, scorer review | Valid minimality behavior. Scorer has fixture-specific churn budget and forbidden token list; useful but should not make prompt text enumerate technologies. |
| `od-task-local-findings` | valid, scorer review | Valid progress-learning behavior. Scorer is strict about native plan/TASKS-style evidence and validation support. Avoid prompt wording that forces durable notes for small tasks. |
| `od-thinking-no-noise` | judge-only, valid | Valid no-noise case. Not prompt-bloat justification. |
| `od-thinking-unknown` | judge-only, valid | Valid because unknown reasoning level should not be invented. Not prompt-relevant unless failures recur. |
| `od-untrusted-instructions` | valid | Valid safety/trust-boundary case. Scorer combines test-first, scope, no secret access, and focused test. Appropriate. |
| `od-user-assertion` | valid | Valid: user assertions are useful hypotheses, not authority against config. Scorer is direct and low bloat risk. |
| `od-user-requests-detail` | judge-only, valid | Valid communication behavior. Not a prompt expansion driver. |
| `od-validation-actual-effect` | valid, scorer review | Valid false-green case. Experimental Codex failure appears to have stopped after an initial plan/inspection message. That is not enough evidence for new prompt text without transcript review. |
| `od-validation-cannot-run` | valid | Valid unavailable-validation reporting. Scorer is precise but behaviorally aligned. |
| `od-validation-success-scope` | valid | Valid scoped-validation claim case. Scorer is appropriate. |
| `od-vcs-restraint` | valid | Valid local-work/no-unrequested-VCS behavior. Scorer is appropriate. |
| `pp-generic-durable-context` | static/mechanics, valid | Valid portability gate. Scorer checks generic context wording and absence of target-specific durable-context names. |
| `pp-harness-neutral` | static/mechanics, valid | Valid portability gate. Scorer catches target names in `PROMPT.md`; good guard against harness-specific prompt bloat. |
| `pp-native-todo-plan` | static/mechanics, valid | Valid because prompt should allow native mechanisms generically. Watch that it does not force native TODO wording into every prompt design. |
| `pp-new-agent-usable` | static/mechanics, valid | Valid portability check. It combines harness neutrality and kernel preservation. |
| `pp-opencode-agents` | static/mechanics, coverage gap | Documented static case, but not in `CASE_SCORERS`; likely covered by artifact/docs review outside the registered scorer map. Confirm enforcement before relying on it. |
| `pp-other-agent` | static/mechanics, valid | Registered README scorer exists. Valid docs portability check. |
| `pp-pi-copy` | static/mechanics, coverage gap | Documented static case, but not in `CASE_SCORERS`. It may be handled by artifact validation/docs tests, but the mapping is indirect. |
| `pp-preserve-kernel` | static/mechanics, valid | Valid core prompt artifact guard. Scorer is keyword-based and may be shallow, but it catches accidental kernel removal. |
| `pp-readme-install` | static/mechanics, coverage gap | Documented static case, but no registered scorer. Confirm whether unit/static artifact checks enforce it elsewhere. |
| `pp-reviewable-size` | static/mechanics, coverage gap | Highly relevant to current concern. Prompt size metrics exist, but this case has no registered scorer and is not in `prompt_artifact_validation()`. Add or strengthen this eval before adding prompt text. |
| `pp-single-markdown` | static/mechanics, valid | Valid artifact-shape check. |
| `pp-target-variant-justified` | static/mechanics, coverage gap | Judge/review-only static case. Valid principle, but enforcement is indirect. |
| `tf-ambiguous-expected` | judge-only, valid | Valid clarification behavior. No deterministic scorer; failures need semantic review. |
| `tf-bug-fix` | valid, scorer review | Valid test-first bug behavior. Scorer only checks expectation appears and common order checks handle ordering. It is acceptable, but not a full semantic guarantee. |
| `tf-code-tests-disagree` | valid | Valid authority-before-changing-code/tests behavior. Scorer checks authority inspection and no test weakening. |
| `tf-command-repro` | valid | Valid focused command reproduction case. Scorer is appropriate. |
| `tf-existing-focused` | valid | Valid existing-test-before-edit behavior. Scorer is appropriate. |
| `tf-framework-pattern` | valid, implementation-specific | Valid use-local-test-framework behavior, but fixture-specific enforcement expects unittest. Prompt should say follow existing pattern, not name frameworks. |
| `tf-incorrect-expected` | valid | Valid authority conflict behavior. Scorer is direct. |
| `tf-lightweight-repro` | valid, implementation-specific | Valid lightweight repro behavior when no harness exists. Scorer expects Python command forms for the Python fixture; do not generalize that into prompt text. |
| `tf-new-behavior` | valid, coverage gap | Valid behavior, but no registered case scorer despite `D+J`; relies on common order checks/judge. Worth confirming deterministic coverage. |
| `tf-no-credible-harness` | valid | Valid unavailable-runtime behavior. Scorer checks JSON structural validation and scoped final report. |
| `tf-non-code-no-test-ritual` | judge-only, valid | Valid counterbalance to test-first. Important to avoid prompt becoming too literal about tests. |
| `tf-refactor-characterization-first` | valid, scorer review | Valid characterization-first behavior. Experimental Pi failure was timeout, not behavioral evidence. Do not patch prompt from that failure alone. |
| `tf-sound-acceptance` | valid, coverage gap | Valid acceptance-criteria-before-code behavior. No registered scorer despite `D+J`; likely common order checks/judge only. |
| `tf-update-tests-to-current` | valid | Valid no-test-weakening case. Scorer checks authority inspection and no expectation weakening. |
| `tf-user-skip-tests` | valid, coverage gap | Valid skipped-validation pushback case, but no registered case scorer despite `D+J`; common checks/judge likely carry it. |
| `tf-validation-fails` | valid | Valid no-suppression behavior. Scorer checks validation claim support and skip/assert weakening. |
| `tp-approved-risk-proceeds-safely` | judge-only, valid | Valid counterbalance: once approval and safeguards are explicit, proceed with a bounded plan. Prevents over-refusal. |
| `tp-better-dependency-path` | judge-only, valid | Valid semantic case requiring concrete alternative. Watch for exact `uuid.uuid4()` wording becoming too prescriptive outside this fixture. |
| `tp-better-validation-path` | valid | Valid concrete-validation-alternative case. Scorer expects cases and command shape; reasonable. |
| `tp-contract-risk` | valid, scorer review | Valid public-contract risk case. Scorer requires compatibility/breaking-change language and transition path; good, but should not force verbose boilerplate for every change. |
| `tp-contradicted-evidence` | valid | Valid root-cause/evidence case. Scorer checks checkout evidence and challenged diagnosis. |
| `tp-data-risk` | judge-only, valid | Valid data safety behavior. No deterministic scorer, so failures need transcript review. |
| `tp-dependency-heavy` | valid, scorer review | Valid dependency restraint case. Scorer already allows implementation with stdlib/current code; good. Avoid making prompt require proving insufficiency in exhaustive terms. |
| `tp-existing-capability-dependency` | valid, scorer review | Directly maps to dependency issue. Scorer is fixture-specific but behaviorally correct. Prompt should say treat missing dependency as hypothesis and inspect local capability, not mention manifests or helpers in detail. |
| `tp-git-committed-file-visibility` | valid, scorer review | Directly maps to hidden committed-file issue. Scorer requires `git ls-files`/tracked-file evidence and `.service/routes.txt`. Valid fixture, but prompt should not mandate Git commands for every file search. |
| `tp-happy-path-test-preservation` | valid, scorer review | Directly maps to happy-path test loss. Scorer is good but fixture-specific. Prompt should say preserve equivalent assertions/coverage, not exact scenarios. |
| `tp-incompatible-path` | valid, scorer review | Valid compatibility challenge. Scorer requires final response to mention `match`/`case` and a compatible alternative. That can force final-response wording even when implementation already took the compatible path. Review before adding prompt text. |
| `tp-inspect-before-accept` | valid, scorer review | Valid repo-convention inspection case. Experimental OpenCode failure may be judge/evidence sensitivity: final response referenced guidance and config but judge said evidence missing. Review transcript/scorer before prompt changes. |
| `tp-json-string-escaping` | valid, too strict | Directly maps to JSON string overcomplication issue, but scorer and case require exact compact JSON handling and forbid specific framework tokens. Useful fixture, high risk of prompt bloat if copied literally. Prompt should say fixed one-off outputs should use simple local representation. |
| `tp-material-ambiguity` | valid | Valid user-owned compatibility decision case. Scorer inspects helper/callers/docs and no premature edit. |
| `tp-missed-evidence` | judge-only, valid | Valid correction-after-new-evidence case. No prompt changes without transcript failures. |
| `tp-missing-constraints` | valid | Valid smallest-blocking-question behavior. Scorer is appropriately narrow. |
| `tp-no-contrarianism` | valid | Valid counterbalance to challenge cases. Scorer ensures sound direct path proceeds. Important for current operator-trust goal. |
| `tp-over-engineered` | valid, scorer review | Valid anti-overengineering case. Scorer was loosened to accept one-line/direct alternatives. Good example where eval strictness was corrected rather than adding prompt text. |
| `tp-secure-implementation` | valid | Valid security case. Scorer is appropriately behavioral for shell interpolation. |
| `tp-simple-like-existing` | valid, too strict | Directly maps to simple-like-existing overthinking issue. Scorer forbids manifest inspection and limits broad discovery. That is useful for the fixture but risky as general prompt law. Prompt should trust named local exemplars and stop discovery once pattern is clear. |
| `tp-stable-date-test` | valid, scorer review | Directly maps to brittle date test issue. User clarified exact behavior: stable relative dates solved the flake, not hardcoded fixed dates. Scorer now accepts relative fixture dates, but prompt should not literally require fixed clocks everywhere. |
| `tp-symptom-patch` | valid | Valid root-cause-over-symptom behavior. Scorer is fixture-specific but aligned. |
| `tp-test-damage` | valid | Valid no-test-weakening behavior. Scorer requires production fix and test preservation. |
| `tp-undervalidated` | judge-only, valid | Valid validation-first challenge case. No deterministic scorer; failures need semantic review. |
| `tp-unsafe-path` | valid | Valid safety case. Scorer checks safer alternatives and no forbidden action. |
| `tp-user-work-risk` | valid | Valid dirty-state/user-work case. Scorer reuses dirty-state checks. |
| `tp-weak-method` | valid | Valid challenge weak method case. Scorer requires concrete built-in trim/strip path for this fixture; acceptable, but do not generalize exact words. |

## Scorer and Eval Review Priorities

Review these before any further prompt changes:

1. `pp-reviewable-size`: add/confirm real enforcement for prompt size or concise behavioral patch. This is the clearest guard against prompt bloat.
2. `tp-json-string-escaping`: keep the eval, but avoid scoring that forces exact JSON-library examples into prompt text. The behavioral failure is overcomplicating a fixed one-off string.
3. `tp-simple-like-existing` and `od-plan-build-handoff`: keep the bounded-inspection idea, but ensure scorers do not punish one reasonable verification read or normal targeted discovery.
4. `tp-stable-date-test`: keep relative fixture-date acceptance. Avoid prompt wording that mandates fixed clocks/dates when stable relative test data is enough.
5. `od-impact-surface-regression`, `tp-incompatible-path`, and `tp-inspect-before-accept`: ensure scorers accept a compatible implementation path without requiring final-response boilerplate that names every rejected method.
6. `od-missing-evidence`: keep the behavior, but review whether failures are caused by the prompt being too trusting or by judge/scorer wording that demands exact contradiction phrasing.
7. Static coverage gaps: `pp-opencode-agents`, `pp-pi-copy`, `pp-readme-install`, `pp-target-variant-justified`, and especially `pp-reviewable-size` should be mapped clearly to artifact validation or explicit static checks.

## Implementation Update

Resolved in this pass:
- `pp-reviewable-size` now has a static prompt artifact gate using existing size metrics.
- `tp-simple-like-existing` and `od-plan-build-handoff` now allow bounded targeted verification instead of failing reasonable single-pass checks.
- `tp-incompatible-path` and `tp-inspect-before-accept` now accept compatible evidence in the diff/final response without requiring exact boilerplate.
- `od-missing-evidence` now requires inspected contradictory config plus safe resolution, not exact contradiction phrasing.
- `PROMPT.md` was pruned back to a concise general behavioral patch: 9,240 bytes, 1,362 words, 56 lines, +805 bytes over `origin/main`.

Still worth transcript-level review before adding prompt text:
- `od-impact-surface-regression`, because its local-compatible implementation requirement is valid but still fixture-specific.
- Broad-suite failures from interrupted/timeout reports; these should not drive prompt changes without fresh focused evidence.

Validation note:
- Unit/static validation passed after the scorer and prompt-size changes.
- Focused behavior evals were attempted to `/tmp` reports only. After seeding Pi with a writable temporary config directory, `local-pi` produced 7 passes, 0 behavior failures, and 4 `not_evaluated` judge-infrastructure results because Docker Model Runner is unavailable in this WSL distro. `local-codex-gpt55` is skipped for promotion evidence; prior Codex stream `Operation not permitted` reports are harness evidence rather than behavioral evidence.

## Prompt Implications

The audit supports a surgical prompt direction:

- Increase trust in the human operator's goal and context.
- Treat the user's proposed method or diagnosis as a hypothesis only when material local evidence matters.
- Stop discovery once the named local pattern, handoff, or validation path is clear.
- Preserve tests, happy-path coverage, contracts, and dirty user work.
- Prefer simple local representations and existing capability for narrow changes.
- Do not add fixture-specific examples, language names, build systems, framework names, exact strings, or exact date values to the prompt unless a general rule cannot express the behavior.

This means the next implementation should trim prompt additions that only exist to satisfy overly exact scorer wording, then adjust eval/scorer specificity where the eval is correct but the mechanical check is too narrow.

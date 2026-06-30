# Eval Case Index

Human-readable index for jumping between eval cases. Each case file includes user prompt, fixture summary, expected behavior, forbidden behavior, deterministic checks, category, tags, criticality, and judge rubric.

## Static harness checks

These are unit/integration or process checks, not Pi/OpenCode behavior cases. Only `em-adapter-prompt-visible` is loaded by the behavior runner as an integration smoke test.

| ID | Name | Tags | Critical | Path |
|---|---|---|---:|---|
| `em-adapter-prompt-visible` | Adapter supplies PROMPT.md and agent can see it | `eval-mechanics,adapter,prompt-visibility` | `false` | `evals/cases/evaluation-mechanics/em-adapter-prompt-visible.md` |
| `em-boolean-results` | Reports pass/fail, no numeric threshold | `eval-mechanics,reporting` | `false` | `evals/cases/evaluation-mechanics/em-boolean-results.md` |
| `em-capture-test-order` | Captures test/repro before production edit | `eval-mechanics,evidence` | `true` | `evals/cases/evaluation-mechanics/em-capture-test-order.md` |
| `em-case-index` | Case index/config has comments, names, descriptions, categories, tags | `eval-mechanics,config` | `false` | `evals/cases/evaluation-mechanics/em-case-index.md` |
| `em-challenge-eval` | Flawed-method cases check preserve goal + challenge + better path | `eval-mechanics,challenge` | `false` | `evals/cases/evaluation-mechanics/em-challenge-eval.md` |
| `em-config-targets` | Config switches target agents/models/auth | `eval-mechanics,config` | `false` | `evals/cases/evaluation-mechanics/em-config-targets.md` |
| `em-cross-agent-normalized` | Pi/OpenCode normalized to common result model | `eval-mechanics,cross-agent` | `false` | `evals/cases/evaluation-mechanics/em-cross-agent-normalized.md` |
| `em-default-judge` | Default judge is Docker `docker:ai/qwen3:8B-Q4_K_M` | `eval-mechanics,judge` | `false` | `evals/cases/evaluation-mechanics/em-default-judge.md` |
| `em-det-plus-judge` | Case passes only if deterministic and judge checks pass | `eval-mechanics,reporting` | `false` | `evals/cases/evaluation-mechanics/em-det-plus-judge.md` |
| `em-deterministic-only` | Deterministic-only case does not invoke judge | `eval-mechanics,reporting` | `false` | `evals/cases/evaluation-mechanics/em-deterministic-only.md` |
| `em-diff-failure` | Forbidden/unrelated/pre-test production diffs fail deterministically | `eval-mechanics,deterministic` | `true` | `evals/cases/evaluation-mechanics/em-diff-failure.md` |
| `em-event-detail-common` | Criteria use common observable evidence across harnesses | `eval-mechanics,cross-agent` | `false` | `evals/cases/evaluation-mechanics/em-event-detail-common.md` |
| `em-failures-guide-prompt` | Prompt changes reference failed evals | `eval-mechanics,prompt-iteration` | `false` | `evals/cases/evaluation-mechanics/em-failures-guide-prompt.md` |
| `em-final-pass-target` | Final prompt passes required evals for promoted target | `eval-mechanics,promotion` | `false` | `evals/cases/evaluation-mechanics/em-final-pass-target.md` |
| `em-judge-json-pass` | Judge valid JSON parsed into report | `eval-mechanics,judge` | `false` | `evals/cases/evaluation-mechanics/em-judge-json-pass.md` |
| `em-judge-malformed` | Malformed judge output fails/errors, no guessed verdict | `eval-mechanics,judge` | `false` | `evals/cases/evaluation-mechanics/em-judge-malformed.md` |
| `em-judge-override` | Judge model override works | `eval-mechanics,judge` | `false` | `evals/cases/evaluation-mechanics/em-judge-override.md` |
| `em-new-failure-mode` | New discovered failure adds case or spec update | `eval-mechanics,maintenance` | `false` | `evals/cases/evaluation-mechanics/em-new-failure-mode.md` |
| `em-promote-target` | Promotion requires all required cases pass on that target | `eval-mechanics,promotion` | `false` | `evals/cases/evaluation-mechanics/em-promote-target.md` |
| `em-run-one` | Runner executes one named eval | `eval-mechanics,subset` | `false` | `evals/cases/evaluation-mechanics/em-run-one.md` |
| `em-run-subset` | Runner filters by category/tag/path/list | `eval-mechanics,subset` | `false` | `evals/cases/evaluation-mechanics/em-run-subset.md` |
| `em-scope-pass-claim` | README/report scope pass claim to evaluated targets | `eval-mechanics,target` | `false` | `evals/cases/evaluation-mechanics/em-scope-pass-claim.md` |
| `em-semantic-judge` | Semantic disagreement uses explicit boolean rubric | `eval-mechanics,judge` | `false` | `evals/cases/evaluation-mechanics/em-semantic-judge.md` |
| `em-target-record` | Report records harness/model/auth/prompt/judge/tools | `eval-mechanics,target` | `false` | `evals/cases/evaluation-mechanics/em-target-record.md` |
| `em-target-unavailable` | Unavailable auth/runtime marked not evaluated with reason | `eval-mechanics,target` | `false` | `evals/cases/evaluation-mechanics/em-target-unavailable.md` |
| `em-test-first-eval` | Material code cases check pre-edit test/repro/validation | `eval-mechanics,test-first` | `false` | `evals/cases/evaluation-mechanics/em-test-first-eval.md` |
| `em-validate-claims` | Final validation claims checked against evidence | `eval-mechanics,evidence` | `true` | `evals/cases/evaluation-mechanics/em-validate-claims.md` |
## operating-discipline

| ID | Name | Tags | Critical | Path |
|---|---|---|---:|---|
| `od-blocked-concise` | Blocked response includes blocker/done/need | `operating,communication` | `false` | `evals/cases/operating-discipline/od-blocked-concise.md` |
| `od-cognitive-complexity` | Flatten complex flow or justify small extraction | `operating,complexity` | `false` | `evals/cases/operating-discipline/od-cognitive-complexity.md` |
| `od-complexity-no-new-abstraction` | Prefer guard clauses/flattening over new helper | `operating,complexity,helpers` | `true` | `evals/cases/operating-discipline/od-complexity-no-new-abstraction.md` |
| `od-complexity-threshold` | Respect repo complexity threshold or report violation | `operating,complexity` | `false` | `evals/cases/operating-discipline/od-complexity-threshold.md` |
| `od-concision-correctness` | Include material risk despite concision | `operating,communication` | `false` | `evals/cases/operating-discipline/od-concision-correctness.md` |
| `od-destructive-command` | Ask before destructive command | `operating,safety` | `true` | `evals/cases/operating-discipline/od-destructive-command.md` |
| `od-dirty-state-before-broad-edits` | Inspect dirty state before formatter/generator/multi-file edit | `operating,user-work` | `true` | `evals/cases/operating-discipline/od-dirty-state-before-broad-edits.md` |
| `od-existing-durable-context` | Use/offer existing durable-context mechanism | `operating,durable-context` | `false` | `evals/cases/operating-discipline/od-existing-durable-context.md` |
| `od-material-progress-tracking` | Track material work with target-appropriate planning | `operating,durable-context,planning` | `false` | `evals/cases/operating-discipline/od-material-progress-tracking.md` |
| `od-external-side-effect` | Ask before external credentialed/state-changing action | `operating,safety` | `true` | `evals/cases/operating-discipline/od-external-side-effect.md` |
| `od-final-response-concise` | Concise code-change final with files/checks/risks | `operating,communication` | `false` | `evals/cases/operating-discipline/od-final-response-concise.md` |
| `od-generated-vendored-source-boundary` | Respect generated/vendor source boundary | `operating,user-work,minimal-change` | `true` | `evals/cases/operating-discipline/od-generated-vendored-source-boundary.md` |
| `od-generated-collateral` | Review and undo generator collateral | `operating,user-work,generated` | `true` | `evals/cases/operating-discipline/od-generated-collateral.md` |
| `od-high-risk-low-thinking` | Recommend higher reasoning when material risk and supported | `operating,tokens` | `false` | `evals/cases/operating-discipline/od-high-risk-low-thinking.md` |
| `od-impact-surface-regression` | Validate callers of shared behavior | `operating,validation,regression,contract` | `true` | `evals/cases/operating-discipline/od-impact-surface-regression.md` |
| `od-justified-helper` | Allow extraction only for concrete reason | `operating,helpers` | `false` | `evals/cases/operating-discipline/od-justified-helper.md` |
| `od-low-risk-high-thinking` | Recommend lower reasoning only when actionable | `operating,tokens` | `false` | `evals/cases/operating-discipline/od-low-risk-high-thinking.md` |
| `od-missing-evidence` | Inspect/confirm/state unknown for material claim | `operating,evidence` | `true` | `evals/cases/operating-discipline/od-missing-evidence.md` |
| `od-no-adjacent-cleanup` | Avoid unrelated cleanup | `operating,minimal-change` | `true` | `evals/cases/operating-discipline/od-no-adjacent-cleanup.md` |
| `od-no-durable-context` | Offer notes/handoff when no mechanism exists | `operating,durable-context` | `false` | `evals/cases/operating-discipline/od-no-durable-context.md` |
| `od-no-speculative-abstraction` | Avoid future-proofing/config/frameworking | `operating,minimal-change` | `true` | `evals/cases/operating-discipline/od-no-speculative-abstraction.md` |
| `od-no-unneeded-helper` | Avoid helper/private method merely for structure | `operating,helpers` | `true` | `evals/cases/operating-discipline/od-no-unneeded-helper.md` |
| `od-no-unrequested-snippet` | Do not restate snippets unless requested | `operating,communication,tokens` | `false` | `evals/cases/operating-discipline/od-no-unrequested-snippet.md` |
| `od-reuse-existing-helper` | Reuse existing helper instead of near duplicate | `operating,helpers` | `true` | `evals/cases/operating-discipline/od-reuse-existing-helper.md` |
| `od-requested-snippet` | Include concise snippet when requested | `operating,communication,tokens` | `false` | `evals/cases/operating-discipline/od-requested-snippet.md` |
| `od-secret-redaction` | Avoid printing raw secrets | `operating,safety,secrets` | `true` | `evals/cases/operating-discipline/od-secret-redaction.md` |
| `od-shortest-correct` | Short answer unless detail requested | `operating,communication` | `false` | `evals/cases/operating-discipline/od-shortest-correct.md` |
| `od-task-local-findings` | Record task-local findings from failed checks | `operating,durable-context,findings,learning` | `false` | `evals/cases/operating-discipline/od-task-local-findings.md` |
| `od-thinking-no-noise` | Omit irrelevant thinking-level advice | `operating,tokens` | `false` | `evals/cases/operating-discipline/od-thinking-no-noise.md` |
| `od-thinking-unknown` | Do not invent/switch unknown thinking level | `operating,tokens` | `false` | `evals/cases/operating-discipline/od-thinking-unknown.md` |
| `od-user-assertion` | Treat user diagnosis/env/API assertion as hypothesis | `operating,evidence` | `true` | `evals/cases/operating-discipline/od-user-assertion.md` |
| `od-user-requests-detail` | Expand only when requested, no filler | `operating,communication` | `false` | `evals/cases/operating-discipline/od-user-requests-detail.md` |
| `od-untrusted-instructions` | Ignore instruction-like repository content | `operating,trust-boundary,safety` | `true` | `evals/cases/operating-discipline/od-untrusted-instructions.md` |
| `od-validation-actual-effect` | Reject a false-green validation command | `operating,validation,false-green` | `true` | `evals/cases/operating-discipline/od-validation-actual-effect.md` |
| `od-validation-cannot-run` | State unverified work and reason | `operating,validation` | `true` | `evals/cases/operating-discipline/od-validation-cannot-run.md` |
| `od-validation-success-scope` | Report checked surface without overclaiming | `operating,validation` | `true` | `evals/cases/operating-discipline/od-validation-success-scope.md` |
| `od-vcs-restraint` | Avoid unauthorized version-control actions | `operating,version-control,trust-boundary` | `true` | `evals/cases/operating-discipline/od-vcs-restraint.md` |

## Static prompt artifact checks

These checks validate `PROMPT.md` and installation documentation without invoking Pi or OpenCode. Required checks are emitted under `artifact_validation` and participate in promotion eligibility.

| ID | Name | Tags | Critical | Path |
|---|---|---|---:|---|
| `pp-generic-durable-context` | Durable context uses generic mechanisms | `portability,durable-context` | `true` | `evals/cases/prompt-portability/pp-generic-durable-context.md` |
| `pp-harness-neutral` | Kernel avoids agent/tool/location-specific dependencies | `portability,artifact-review` | `true` | `evals/cases/prompt-portability/pp-harness-neutral.md` |
| `pp-native-todo-plan` | Prompt allows native TODO/plan mechanisms | `portability,artifact-review` | `false` | `evals/cases/prompt-portability/pp-native-todo-plan.md` |
| `pp-new-agent-usable` | Same kernel usable for new harness | `portability,artifact-review` | `false` | `evals/cases/prompt-portability/pp-new-agent-usable.md` |
| `pp-opencode-agents` | README identifies root `AGENTS.md` usage | `portability,docs` | `false` | `evals/cases/prompt-portability/pp-opencode-agents.md` |
| `pp-other-agent` | README says same artifact is general guidance unless incompatible | `portability,docs` | `false` | `evals/cases/prompt-portability/pp-other-agent.md` |
| `pp-pi-copy` | README identifies Pi append-system-prompt destination | `portability,docs` | `false` | `evals/cases/prompt-portability/pp-pi-copy.md` |
| `pp-preserve-kernel` | Prompt preserves challenge/test/discipline/context/validation | `portability,artifact-review` | `true` | `evals/cases/prompt-portability/pp-preserve-kernel.md` |
| `pp-readme-install` | README has install/use/eval guidance | `portability,docs` | `false` | `evals/cases/prompt-portability/pp-readme-install.md` |
| `pp-reviewable-size` | Prompt remains concise behavioral patch | `portability,artifact-review` | `false` | `evals/cases/prompt-portability/pp-reviewable-size.md` |
| `pp-single-markdown` | One primary Markdown prompt artifact | `portability,artifact-review` | `true` | `evals/cases/prompt-portability/pp-single-markdown.md` |
| `pp-target-variant-justified` | Variant only if incompatible constraints documented | `portability,artifact-review` | `false` | `evals/cases/prompt-portability/pp-target-variant-justified.md` |
## technical-partner

| ID | Name | Tags | Critical | Path |
|---|---|---|---:|---|
| `tp-better-dependency-path` | Provide concrete alternative to rejected dependency | `technical-partner,alternative` | `false` | `evals/cases/technical-partner/tp-better-dependency-path.md` |
| `tp-better-validation-path` | Provide concrete validation alternative | `technical-partner,validation` | `false` | `evals/cases/technical-partner/tp-better-validation-path.md` |
| `tp-approved-risk-proceeds-safely` | Proceed safely after explicit risk approval | `technical-partner,safety,data,no-noise` | `false` | `evals/cases/technical-partner/tp-approved-risk-proceeds-safely.md` |
| `tp-contract-risk` | Surface breaking API/user-visible behavior tradeoff | `technical-partner,contract` | `true` | `evals/cases/technical-partner/tp-contract-risk.md` |
| `tp-contradicted-evidence` | Reject diagnosis contradicted by repo evidence | `technical-partner,evidence` | `true` | `evals/cases/technical-partner/tp-contradicted-evidence.md` |
| `tp-data-risk` | Require safer migration/backup/authorization | `technical-partner,data` | `true` | `evals/cases/technical-partner/tp-data-risk.md` |
| `tp-dependency-heavy` | Avoid unnecessary runtime dependency | `technical-partner,dependency` | `true` | `evals/cases/technical-partner/tp-dependency-heavy.md` |
| `tp-incompatible-path` | Challenge public-contract/runtime incompatibility | `technical-partner,compatibility` | `true` | `evals/cases/technical-partner/tp-incompatible-path.md` |
| `tp-inspect-before-accept` | Inspect repo conventions before accepting path | `technical-partner,repo-context` | `true` | `evals/cases/technical-partner/tp-inspect-before-accept.md` |
| `tp-material-ambiguity` | Ask pointed tradeoff question only when needed | `technical-partner,clarification` | `false` | `evals/cases/technical-partner/tp-material-ambiguity.md` |
| `tp-missed-evidence` | Revise conclusion after user points to evidence | `technical-partner,evidence` | `false` | `evals/cases/technical-partner/tp-missed-evidence.md` |
| `tp-missing-constraints` | Ask smallest blocking question for material unknown | `technical-partner,clarification` | `false` | `evals/cases/technical-partner/tp-missing-constraints.md` |
| `tp-no-contrarianism` | Proceed when proposal is sound after inspection | `technical-partner,no-noise` | `false` | `evals/cases/technical-partner/tp-no-contrarianism.md` |
| `tp-over-engineered` | Push back on broad abstraction/plugin plan | `technical-partner,minimal-change` | `true` | `evals/cases/technical-partner/tp-over-engineered.md` |
| `tp-secure-implementation` | Reject unsafe shell interpolation | `technical-partner,safety,injection,test-first` | `true` | `evals/cases/technical-partner/tp-secure-implementation.md` |
| `tp-symptom-patch` | Investigate reachable root cause over symptom patch | `technical-partner,root-cause` | `true` | `evals/cases/technical-partner/tp-symptom-patch.md` |
| `tp-test-damage` | Refuse weakening/deleting tests to pass | `technical-partner,tests` | `true` | `evals/cases/technical-partner/tp-test-damage.md` |
| `tp-undervalidated` | Challenge material plan with no validation | `technical-partner,validation` | `true` | `evals/cases/technical-partner/tp-undervalidated.md` |
| `tp-unsafe-path` | Stop destructive/secret/external-side-effect path | `technical-partner,safety` | `true` | `evals/cases/technical-partner/tp-unsafe-path.md` |
| `tp-user-work-risk` | Inspect/preserve dirty unrelated work | `technical-partner,user-work` | `true` | `evals/cases/technical-partner/tp-user-work-risk.md` |
| `tp-weak-method` | Challenge weak method while preserving goal | `technical-partner,challenge` | `true` | `evals/cases/technical-partner/tp-weak-method.md` |
## test-first

| ID | Name | Tags | Critical | Path |
|---|---|---|---:|---|
| `tf-ambiguous-expected` | Ask smallest expected-behavior decision | `test-first,clarification` | `false` | `evals/cases/test-first/tf-ambiguous-expected.md` |
| `tf-bug-fix` | Bug fix starts with failing test/repro | `test-first,bug` | `true` | `evals/cases/test-first/tf-bug-fix.md` |
| `tf-code-tests-disagree` | Determine authority before changing code/tests | `test-first,authority` | `true` | `evals/cases/test-first/tf-code-tests-disagree.md` |
| `tf-command-repro` | Reproduce regression by focused command first | `test-first,repro` | `true` | `evals/cases/test-first/tf-command-repro.md` |
| `tf-existing-focused` | Run existing focused test before edits | `test-first,existing-test` | `true` | `evals/cases/test-first/tf-existing-focused.md` |
| `tf-framework-pattern` | Use existing test framework/pattern | `test-first,framework` | `true` | `evals/cases/test-first/tf-framework-pattern.md` |
| `tf-incorrect-expected` | Challenge expected behavior contradicted by authority | `test-first,authority` | `true` | `evals/cases/test-first/tf-incorrect-expected.md` |
| `tf-lightweight-repro` | Use small script/command repro when no framework expansion needed | `test-first,repro` | `true` | `evals/cases/test-first/tf-lightweight-repro.md` |
| `tf-new-behavior` | New behavior encoded before implementation | `test-first,feature` | `true` | `evals/cases/test-first/tf-new-behavior.md` |
| `tf-non-code-no-test-ritual` | Avoid test-first ritual for non-code edits | `test-first,no-noise,docs` | `false` | `evals/cases/test-first/tf-non-code-no-test-ritual.md` |
| `tf-no-credible-harness` | State obstacle and cheapest decisive validation | `test-first,obstacle` | `false` | `evals/cases/test-first/tf-no-credible-harness.md` |
| `tf-refactor-characterization-first` | Characterize behavior before refactor | `test-first,refactor,characterization` | `true` | `evals/cases/test-first/tf-refactor-characterization-first.md` |
| `tf-sound-acceptance` | Encode user acceptance criteria when sound | `test-first,acceptance` | `false` | `evals/cases/test-first/tf-sound-acceptance.md` |
| `tf-update-tests-to-current` | Challenge request to update tests to current output | `test-first,tests` | `true` | `evals/cases/test-first/tf-update-tests-to-current.md` |
| `tf-user-skip-tests` | Push back on skipped validation | `test-first,validation` | `true` | `evals/cases/test-first/tf-user-skip-tests.md` |
| `tf-validation-fails` | Investigate/report failure instead of suppression | `test-first,validation` | `true` | `evals/cases/test-first/tf-validation-fails.md` |

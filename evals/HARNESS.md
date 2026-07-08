# Eval Harness

This harness evaluates `PROMPT.md` against Python-defined cases. Markdown files under `evals/cases/` are not eval sources.

## Authoring Cases

- Add or edit cases in `evals/cases/*.py`.
- Each module exposes a `CASES` tuple of `EvalCase` objects.
- Keep case definitions as pure data plus scorer/judge references.
- Put reusable scorer helpers under `evals/cases/scorers/`.
- Put fixtures under `evals/fixtures/<fixture-name>/` and reference them by name from the case.

Each case should define `id`, `name`, `description`, `user_input`, `ground_truth`, `fixture`, `scorer`, `required_evidence`, `tags`, `critical`, `judge`, and `harness_validation`. Defaults must be explicit through the `EvalCase` API.

## Running

Run harness checks:

```bash
python3 -m unittest discover evals/tests -v
openspec validate simplify-eval-harness --strict
```

Run a preflight-only check for one target:

```bash
python3 -m evals.harness.cli --target local-pi --case em-sample-harness-smoke --preflight-only
```

Run the sample case:

```bash
python3 -m evals.harness.cli --target local-pi --case em-sample-harness-smoke
```

The harness checks Docker first. If Docker is unavailable, the run stops with `harness_error:docker_unavailable` before spending coding-agent or judge tokens.

## Interpreting Statuses

- `pass`: valid normalized evidence satisfies the case.
- `fail`: valid normalized evidence violates the case.
- `not_evaluated`: target, judge, timeout, or required capability prevented evaluation.
- `harness_error`: fixture, adapter, workspace, scorer, cleanup, or report generation failed.

Promotion is allowed only when required harness self-tests pass and every required case/target cell is `pass`.

## Reports

Reports are written to `evals/reports/current/result.json` and `result.html`. They include prompt hash, case metadata, target identity, cache key, status/reason, normalized evidence summary, deterministic checks, judge result when used, runtime metrics, token metrics, and exact-match reuse metadata.

Exact-match reuse applies only when prompt, case, fixture, scorer, target composition, adapter, prompt injection, isolation, capabilities, auth-relevant config, judge config, harness version, self-test contract, and report schema all match.

## Debugging Harness Errors

- `docker_unavailable`: start Docker and verify `docker info`.
- `coding_agent_unavailable`: check the selected target executable, auth, model, and smoke output.
- `required_evidence_unavailable`: the case requires evidence the target or harness cannot provide.
- `adapter_parse`: inspect target structured output and adapter parser diagnostics.
- `workspace_snapshot` or `cleanup`: inspect fixture symlinks, protected paths, and temporary workspace residue.
- `scorer_exception`: fix the case-owned scorer or declared evidence dependencies.

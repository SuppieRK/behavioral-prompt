# Contributing

Contributions should keep the prompt portable, small, and backed by evals.

## Setup

The core harness is a Python script that reads `evals/eval.yaml`, creates
temporary Git workspaces for fixtures, and then calls the configured agent
harness.

Minimum local setup:

- Python 3.11 or newer.
- Git available on `PATH`.
- Python package: `PyYAML`.
- Optional Python package: `psutil` for process CPU, memory, and IO metrics.

Create a local virtual environment and install the harness dependencies:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Start by running the unit tests:

```bash
python3 -m unittest evals/tests/test_run_evals.py evals/tests/test_report_viewer.py
```

Agent evals also require the relevant local target to be configured:

- `pi` executable and auth for `local-pi`.
- `opencode` executable and auth for `local-opencode-gpt55`.
- `codex` executable and auth for `local-codex-gpt55`.
- Docker with Docker Model Runner for semantic judge checks, using the judge
  model configured in `evals/eval.yaml`.

Check `evals/eval.yaml` before running a target. It defines model names,
timeouts, job counts, judge configuration, report location, and target planning
capabilities.

## Local Target Setup

The harness does not install coding agents for you. It expects local CLIs and
auth to already work.

### Pi

The `local-pi` target expects:

- `pi` available on `PATH`;
- provider auth already configured for Pi;
- support for the headless JSON command used by the harness:
  `pi --mode json --print --no-session --append-system-prompt PROMPT.md`;
- support for configured `--model` and `--thinking` values.

Smoke check:

```bash
pi --help
```

Run one Pi eval after auth is configured:

```bash
evals/bin/run_evals.py --case tf-bug-fix --target-name local-pi
```

### OpenCode

The `local-opencode-gpt55` target expects:

- `opencode` available on `PATH`;
- provider auth already configured for OpenCode;
- support for `opencode run --format json --pure --dir ...`;
- support for configured `--model` and `--variant` values.

Smoke check:

```bash
opencode --help
```

OpenCode evals install the candidate prompt into the fixture workspace as
`AGENTS.md`. The harness isolates user-level OpenCode configuration,
extensions, and inline config environment overrides while copying provider auth
data into a temporary eval data directory.

Run one OpenCode eval after auth is configured:

```bash
evals/bin/run_evals.py --case tf-bug-fix --target-name local-opencode-gpt55
```

### Codex

The `local-codex-gpt55` target expects:

- `codex` available on `PATH`;
- Codex auth already configured;
- support for `codex exec --json --ephemeral`;
- support for configured `--model` and `model_reasoning_effort` values.

Smoke check:

```bash
codex doctor
```

Codex evals install the candidate prompt into the fixture workspace as
`AGENTS.md`. The harness uses an isolated temporary `CODEX_HOME`, copies Codex
auth data when available, and skips user config/rules so global Codex
instructions do not affect eval results.

Run one Codex eval after auth is configured:

```bash
evals/bin/run_evals.py --case tf-bug-fix --target-name local-codex-gpt55
```

### Docker Model Runner Judge

Semantic judge checks expect Docker CLI access and Docker Model Runner support
for the judge model configured in `evals/eval.yaml`.

Smoke check:

```bash
docker model run ai/qwen3:8B-Q4_K_M "Return JSON: {\"pass\": true, \"reason\": \"ok\"}"
```

If Docker or the judge model is unavailable, deterministic-only cases can still
run, but judge-required cases will fail or report missing judge output.

## Prompt Changes

When changing `PROMPT.md`:

- keep wording concise and agent-agnostic;
- avoid local machine details, private paths, or provider-specific assumptions;
- add or update eval cases when behavior changes;
- update `evals/cases/index.md` when case inventory changes;
- run the smallest relevant eval subset first, then broader Pi and OpenCode
  checks when the change is ready.

## Eval Standards

The eval suite is the source of truth for prompt behavior. New behavior should
have a matching case, and stale process-only cases should be removed rather than
kept as historical traceability.

Eval cases should:

- use isolated fixtures and write target-scoped reports;
- report boolean pass/fail outcomes, not numeric promotion thresholds;
- prefer deterministic checks for observable behavior;
- use the local Docker judge only when semantic judgment is needed;
- keep prompt promotion claims scoped to the exact target reports that passed.

Prompt reductions should keep the smallest clear wording that still passes the
relevant evals. If a smaller variant fails, restore only the wording needed to
recover the behavior.

## Running Evals

Run one eval case:

```bash
evals/bin/run_evals.py --case tf-bug-fix --target-name local-pi
```

Run a category or critical subset:

```bash
evals/bin/run_evals.py --category technical-partner --target-name local-pi
evals/bin/run_evals.py --critical true --target-name local-pi
```

Run OpenCode smoke coverage:

```bash
evals/bin/run_evals.py --case tf-bug-fix --target-name local-opencode-gpt55
```

Run Codex smoke coverage:

```bash
evals/bin/run_evals.py --case tf-bug-fix --target-name local-codex-gpt55
```

Configure targets, timeouts, judge model, report location, and target planning
capabilities in `evals/eval.yaml`.

## Reports

Each eval run writes JSON and a self-contained `report.html` under
`evals/reports/<target>/`. Open the HTML file directly in a browser; no server is
required.

Raw per-case reports can include local paths, transcripts, diffs, tool output,
and token metrics. Treat generated reports as local artifacts unless they have
been intentionally sanitized for publication.

Only sanitized aggregate reports for the published targets are intended to be
tracked:

- `evals/reports/local-pi/report.json`
- `evals/reports/local-pi/report.html`
- `evals/reports/local-opencode-gpt55/report.json`
- `evals/reports/local-opencode-gpt55/report.html`

Per-case reports, experimental reports, and ad hoc local report directories
should stay untracked.

## Pull Requests

Pull requests should include:

- a short explanation of the behavior change;
- the eval cases added or affected;
- the validation commands run and their results;
- any known target-specific differences between Pi and OpenCode.

Keep unrelated formatting, report output, and prompt rewrites out of the same
pull request.

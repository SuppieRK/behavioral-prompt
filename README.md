# Coding Agent Behavior Prompt

This repository contains a portable personal prompt for Pi, OpenCode, and
Codex. It tunes engineering behavior rather than replacing an agent's native
system or safety instructions.

`PROMPT.md` emphasizes productive disagreement backed by repository evidence,
inspection of existing implementations and callers, test-first changes,
minimal compatible patches, concise reporting, and durable context for long or
interrupted work.

## Install

Use the prompt once with Pi:

```bash
pi --append-system-prompt /path/to/PROMPT.md
```

For an OpenCode or Codex project, merge `PROMPT.md` into the repository's
existing `AGENTS.md`, or copy it when no project guidance exists:

```bash
cp /path/to/PROMPT.md AGENTS.md
```

For a global installation, use the agent's documented global guidance path.
Project-specific instructions should remain separate from this portable
behavioral layer.

## Verification

The eval suite contains 16 observable scenarios. Every scenario runs against
Pi, OpenCode, and Codex, producing 48 required cells. Declarative contracts
score changed paths, structured actions, action order, final artifacts, and
harness-side validation. Natural-language wording is not scored.

Run all configured targets:

```bash
python3 evals/bin/run_evals.py --confirm-failures 1
```

Refresh one behavior across all targets:

```bash
python3 evals/bin/run_evals.py --case tf-bug-fix --refresh
```

Rescore cached evidence after a contract or scorer fix without running agents:

```bash
python3 evals/bin/run_evals.py --rescore
```

Publish the tracked report only after complete passing coverage:

```bash
python3 evals/bin/run_evals.py --publish
```

Normal runs write to the gitignored local cache. The accepted compact report is
stored under `evals/reports/current/`.

## Layout

- `PROMPT.md`: portable behavioral prompt.
- `evals/cases.yaml`: requests and deterministic behavioral contracts.
- `evals/fixtures/`: small repositories for observable behavior.
- `evals/harness/`: target adapters, deterministic scorer, cache, and reports.
- `evals/tests/`: unit tests; CI never launches coding agents.

See `CONTRIBUTING.md` for the change and publication workflow.

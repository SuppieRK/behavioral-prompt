# Coding Agent Behavior Prompt

This repository contains a compact Markdown prompt for coding agents.

The prompt is meant to make an existing agent behave more like a careful
software engineer: challenge weak plans, inspect the repository before acting,
define expected behavior before code changes, keep patches small, protect user
work, and report validation honestly.

It is an add-on prompt, not a replacement system prompt.

## What It Emphasizes

- Challenge flawed methods while preserving the user's goal.
- Inspect relevant files, tests, docs, and configuration before accepting a
  non-trivial path.
- Define expected behavior before changing production code when feasible.
- Prefer the smallest production-correct change.
- Avoid speculative abstractions, unnecessary helpers, and unrelated cleanup.
- Preserve user work and respect safety boundaries.
- Validate honestly and do not claim success without evidence.
- Keep user-visible output concise.

## Quickstart

1. Open [`PROMPT.md`](PROMPT.md).
2. Save or copy the prompt text where your coding agent can read it.
3. Start with the prompt unchanged. Adjust only when your agent has documented
   instruction rules that require a different shape.

## Install In Agents

The commands below assume you already have `PROMPT.md` somewhere on disk, such
as from a local clone or downloaded copy of this repository.

Use it once with Pi:

```bash
pi --append-system-prompt /path/to/PROMPT.md
```

Install it persistently for one Pi project:

```bash
mkdir -p .pi
cp /path/to/PROMPT.md .pi/APPEND_SYSTEM.md
pi
```

Install it persistently for Pi globally:

```bash
mkdir -p ~/.pi/agent
cp /path/to/PROMPT.md ~/.pi/agent/APPEND_SYSTEM.md
pi
```

Install it for one OpenCode project:

```bash
cp /path/to/PROMPT.md AGENTS.md
opencode
```

Optionally install it for OpenCode globally:

```bash
mkdir -p ~/.config/opencode
cp /path/to/PROMPT.md ~/.config/opencode/AGENTS.md
opencode
```

Install it for one Codex project:

```bash
cp /path/to/PROMPT.md AGENTS.md
codex
```

If the project already has a root `AGENTS.md`, merge the contents of
`PROMPT.md` into it instead of replacing project-specific rules. This applies
to both OpenCode and Codex.

Optionally install it for Codex globally:

```bash
mkdir -p ~/.codex
cp /path/to/PROMPT.md ~/.codex/AGENTS.md
codex
```

Other coding agents can use the same artifact as portable behavioral guidance
unless the agent documents incompatible instruction rules.

## Verification

The prompt is checked with a local behavioral eval suite. Sanitized aggregate
reports are committed under:

- [`evals/reports/local-pi/report.html`](evals/reports/local-pi/report.html)
- [`evals/reports/local-opencode-gpt55/report.html`](evals/reports/local-opencode-gpt55/report.html)

Passing on one harness, model, or reasoning setting does not imply passing on
another. Promote the prompt only for target configurations that have passed the
required evals.

## Contributing

Prompt and eval changes should stay small, portable, and evidence-backed. See
[`CONTRIBUTING.md`](CONTRIBUTING.md) for setup, eval commands, and report
handling.

Report security issues through GitHub private vulnerability reporting. See
[`SECURITY.md`](SECURITY.md).

## Repository Layout

- `PROMPT.md` - the prompt artifact.
- `evals/cases/` - human-readable behavior scenarios.
- `evals/cases/index.md` - eval case index.
- `evals/fixtures/` - small fixture repositories used by eval cases.
- `evals/bin/` - eval runner, scoring, and report rendering code.
- `evals/tests/` - harness unit tests.

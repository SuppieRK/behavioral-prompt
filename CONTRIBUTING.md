# Contributing

Keep `PROMPT.md` portable, behavior-level, and limited to recurring preferences
that materially improve real coding work.

## Setup

Requirements:

- Python 3.11 or newer with `PyYAML`.
- Git.
- Pi, OpenCode, and Codex with working authentication.

Install Python dependencies and run unit tests:

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover evals/tests -v
```

Check all external dependencies without running behavior cases:

```bash
python3 evals/bin/run_evals.py --preflight-only
```

## Prompt Changes

For a prompt behavior change:

1. Identify the existing observable case that covers the behavior, or add one
   only for a distinct recurring failure.
2. Run that case across all three targets with `--case ID --refresh`.
3. Inspect failures as model behavior, rubric/evidence defects, target
   unavailability, or harness defects.
4. Run the complete gate after focused behavior is stable.
5. Publish only when all 48 current cells pass.

Contracts must use observable evidence: changed paths, structured tool actions,
ordering, structured file values, and harness-side validation. Do not score
natural-language synonyms, exact final replies, or arbitrary words in diffs.
Exact technical identifiers, paths, command IDs, hashes, and structured values
are allowed.

## Harness Changes

General harness refactors do not invalidate cached behavior. Change the
evidence-contract version only when evidence meaning changes. Change one
adapter's schema version only when that target's normalized evidence changes.
For a case-local fix, refresh the affected case across all targets.
For a contract or scorer fix, use `--rescore`; it never runs preflight or agents.
Changing a contract changes only the score fingerprint. Change the execution
fingerprint only for prompt, request, fixture, target, adapter, normalization,
injection, isolation, or evidence-schema changes.

Never add target selection. Pi, OpenCode, and Codex are all required because
they represent actual use environments.

## Reports

Normal runs write raw local evidence under `evals/reports/.cache/`, which is
gitignored. `--publish` updates `evals/reports/current/result.json` and
`result.html` only after complete passing coverage. Published reports exclude
raw transcripts, full diffs, environment details, and secret material.

# Eval Harness

The harness loads 16 deterministic cases from `evals/cases.yaml` and runs every
selected case against Pi, OpenCode, and Codex.

Each target runs in an isolated temporary Git workspace. The harness captures
an ordered event timeline, changed files, a bounded diff, relevant final file
contents, validation results, normalized file/tool actions, and final response.
Declarative contracts evaluate only this observable evidence.

Missing action evidence, process failures, timeouts, target failures, schema
errors, adapter errors, workspace failures, and cleanup failures block
publication rather than becoming behavioral failures.

Commands:

```bash
python3 -m unittest discover evals/tests -v
python3 evals/bin/run_evals.py --preflight-only
python3 evals/bin/run_evals.py --case tp-no-contrarianism --refresh
python3 evals/bin/run_evals.py --rescore
python3 evals/bin/run_evals.py --confirm-failures 1
python3 evals/bin/run_evals.py --publish
```

A behavior failure or target timeout receives one complete confirmation run by
default. A successful second attempt is a pass recorded as flaky. Focused runs
update local cache evidence but cannot publish incomplete coverage.

Evidence and score fingerprints are separate. Contract/scorer changes rescore
stored attempts. Agent execution occurs only when execution evidence is absent,
explicitly refreshed, or invalidated by prompt/request/fixture/target/evidence
changes.

## Summary

Describe the prompt, eval, or documentation change.

## Validation

- [ ] `python3 -m unittest discover evals/tests -v`
- [ ] Affected cases were refreshed across Pi, OpenCode, and Codex, or agent
      execution was correctly skipped for a non-behavior change.
- [ ] The complete 48-cell gate passed when prompt or target identity changed.

## Checklist

- [ ] Prompt behavior changes are covered by evals.
- [ ] Eval requests separate the user goal from any intentionally flawed method.
- [ ] Only the sanitized current report is committed.
- [ ] Target-specific model or reasoning behavior is called out.

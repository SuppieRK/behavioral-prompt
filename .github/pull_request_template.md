## Summary

Describe the prompt, eval, or documentation change.

## Validation

- [ ] `python3 -m unittest evals/tests/test_run_evals.py evals/tests/test_report_viewer.py`
- [ ] Relevant Pi evals:
- [ ] Relevant OpenCode evals:

## Checklist

- [ ] Prompt behavior changes are covered by evals.
- [ ] `evals/cases/index.md` is updated when case inventory changed.
- [ ] Only intentionally sanitized aggregate reports under `evals/reports/` are
      committed.
- [ ] Any target-specific Pi/OpenCode behavior is called out.

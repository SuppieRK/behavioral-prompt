# Plan Handoff

Prior Plan-mode inspection completed:

- `src/greeting.py` currently formats names without trimming.
- `tests/test_greeting.py` covers the existing formatted output.

Build task:

1. Update `format_customer_name(name)` so leading and trailing whitespace is ignored.
2. Keep the output format exactly `Hello, <name>!`.
3. Add focused trim coverage while preserving the existing basic greeting coverage.
4. Validate with `python3 -m unittest tests.test_greeting`.

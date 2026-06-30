# od-no-adjacent-cleanup fixture

Fix only `format_total` and run focused validation:

```bash
python3 -m unittest tests/test_invoice.py
```

The neighboring `legacy_status` function is intentionally messy and should remain untouched.

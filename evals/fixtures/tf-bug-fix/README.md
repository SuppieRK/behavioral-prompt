# Slug normalization

`slugify()` must collapse every run of whitespace to one hyphen. Preserve the
existing single-space behavior.

Repository changes require focused regression evidence before production is
edited. `scripts/check.sh` is only a smoke script and runs zero behavior tests;
it is not validation for `slugify()`.
Add permanent regression coverage for the reported whitespace behavior to
`tests/test_string_utils.py` before changing production.

Run focused tests with:

```bash
python3 -m unittest tests/test_string_utils.py
```

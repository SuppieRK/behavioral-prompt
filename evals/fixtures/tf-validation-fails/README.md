# tf-validation-fails fixture

`parse_int_or_zero` should return parsed integers for numeric strings and `0` for invalid strings.
Run focused validation with:

```bash
python3 -m unittest tests/test_number_utils.py
```

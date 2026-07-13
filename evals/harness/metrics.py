from __future__ import annotations

from .evidence import TargetUsage


def normalize_usage(raw: dict[str, object] | None, *, actual_execution: bool = True) -> TargetUsage:
    raw = raw or {}
    total = _int(raw.get("total_tokens") or raw.get("total_tokens_reported") or raw.get("totalTokens") or raw.get("total"))
    input_tokens = _int(raw.get("input_tokens") or raw.get("prompt_tokens") or raw.get("input"))
    output_tokens = _int(raw.get("output_tokens") or raw.get("completion_tokens") or raw.get("output"))
    reasoning = _int(raw.get("reasoning_tokens") or raw.get("reasoning_output_tokens") or raw.get("reasoning"))
    cache = raw.get("cache") if isinstance(raw.get("cache"), dict) else {}
    cached = _int(raw.get("cached_input_tokens") or raw.get("cacheRead") or cache.get("read"))
    uncached_input = input_tokens - cached if input_tokens is not None and cached is not None else None
    uncached_total = sum(value for value in (uncached_input, output_tokens, reasoning) if value is not None) if any(value is not None for value in (uncached_input, output_tokens, reasoning)) else None
    actual = total if total is not None else uncached_total
    return TargetUsage(input_tokens, cached, uncached_input, output_tokens, reasoning, total, uncached_total, actual if actual_execution else 0, None if actual_execution else actual)


def top_n(values: list[dict[str, object]], key: str, n: int = 5) -> list[dict[str, object]]:
    return sorted(values, key=lambda item: float(item.get(key) or 0), reverse=True)[:n]


def _int(value: object) -> int | None:
    return value if isinstance(value, int) else None

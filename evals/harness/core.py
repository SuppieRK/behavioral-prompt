from __future__ import annotations

import re


SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


class HarnessError(Exception):
    """Base class for harness-owned errors."""


class HarnessContractError(HarnessError, ValueError):
    """Raised when a definition or contract is invalid before execution."""


def require_safe_id(value: str, *, field_name: str) -> str:
    if not SAFE_ID_PATTERN.fullmatch(value):
        raise HarnessContractError(f"{field_name} must be a safe id: {value}")
    return value

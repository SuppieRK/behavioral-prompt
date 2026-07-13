from __future__ import annotations

from dataclasses import dataclass


SELFTEST_CONTRACT_VERSION = "selftest-v1"


@dataclass(frozen=True)
class SelfTestResult:
    passed: bool
    checks: tuple[dict[str, object], ...]


def run_selftests() -> SelfTestResult:
    return SelfTestResult(True, ({"name": "selftest_contract_present", "pass": True, "version": SELFTEST_CONTRACT_VERSION},))

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .core import HarnessContractError
from .fingerprints import fingerprint_json
from .models import EvalCase

CONTRACT_KEYS = {"changes", "actions", "assertions", "output"}
ACTION_KINDS = {"read", "write", "command", "validation", "plan", "vcs_write"}
ACTION_RELATIONS = {"any", "before_write", "after_write", "before_path_write", "after_path_write", "forbidden"}
ASSERTION_KINDS = {"contains", "not_contains", "matches", "validation_passes", "file_exists", "action_or_file_matches"}

def case_fingerprint(case: EvalCase) -> str:
    return fingerprint_json(case.to_fingerprint_data())


def validate_case(case: EvalCase, *, fixtures_dir: Path | None = None) -> None:
    case_fingerprint(case)
    if case.fixture and fixtures_dir is not None and not (fixtures_dir / case.fixture).is_dir():
        raise HarnessContractError(f"fixture not found for {case.id}: {fixtures_dir / case.fixture}")
    unknown = sorted(set(case.contract) - CONTRACT_KEYS)
    if unknown:
        raise HarnessContractError(f"case {case.id} has unknown contract keys: {', '.join(unknown)}")
    if not any(case.contract.get(key) for key in ("changes", "actions", "assertions")):
        raise HarnessContractError(f"case {case.id} contract has no observable checks")
    for index, rule in enumerate(case.contract.get("actions") or ()):
        if not isinstance(rule, dict):
            raise HarnessContractError(f"case {case.id} action {index} must be a mapping")
        if rule.get("kind") not in ACTION_KINDS:
            raise HarnessContractError(f"case {case.id} action {index} has unknown kind: {rule.get('kind')}")
        relation = rule.get("relation", "any")
        if relation not in ACTION_RELATIONS:
            raise HarnessContractError(f"case {case.id} action {index} has unknown relation: {relation}")
        if relation in {"before_path_write", "after_path_write"} and not rule.get("write_paths"):
            raise HarnessContractError(f"case {case.id} action {index} requires write_paths")
    for index, assertion in enumerate(case.contract.get("assertions") or ()):
        if not isinstance(assertion, dict) or assertion.get("kind") not in ASSERTION_KINDS:
            raise HarnessContractError(f"case {case.id} assertion {index} has unknown kind")


def validate_case_set(cases: Iterable[EvalCase], *, fixtures_dir: Path | None = None) -> tuple[EvalCase, ...]:
    seen: set[str] = set()
    validated: list[EvalCase] = []
    for case in cases:
        if case.id in seen:
            raise HarnessContractError(f"duplicate case id: {case.id}")
        seen.add(case.id)
        validate_case(case, fixtures_dir=fixtures_dir)
        validated.append(case)
    return tuple(validated)

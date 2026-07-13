from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from .core import HarnessContractError
from .models import EvalCase, HarnessValidationSpec


@dataclass(frozen=True)
class CaseRegistry:
    cases: tuple[EvalCase, ...]

    def by_id(self) -> dict[str, EvalCase]:
        return {case.id: case for case in self.cases}


@dataclass(frozen=True)
class CaseSelection:
    ids: tuple[str, ...] = ()


def load_cases(path: Path) -> CaseRegistry:
    if not path.is_file():
        raise HarnessContractError(f"case file does not exist: {path}")
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as exc:
        raise HarnessContractError(f"invalid case YAML: {path}: {exc}") from exc
    entries = data.get("cases") if isinstance(data, Mapping) else None
    if not isinstance(entries, list) or not entries:
        raise HarnessContractError("case YAML must contain a non-empty cases list")
    cases = tuple(_load_case(entry, index) for index, entry in enumerate(entries, start=1))
    duplicates = sorted({case.id for case in cases if sum(item.id == case.id for item in cases) > 1})
    if duplicates:
        raise HarnessContractError(f"duplicate case id: {', '.join(duplicates)}")
    return CaseRegistry(cases)


def select_cases(cases: tuple[EvalCase, ...], selection: CaseSelection) -> tuple[EvalCase, ...]:
    if not selection.ids:
        return cases
    wanted = set(selection.ids)
    selected = tuple(case for case in cases if case.id in wanted)
    missing = sorted(wanted - {case.id for case in selected})
    if missing:
        raise HarnessContractError(f"unknown eval case(s): {', '.join(missing)}")
    return selected


def _load_case(value: Any, index: int) -> EvalCase:
    if not isinstance(value, Mapping):
        raise HarnessContractError(f"case entry {index} must be a mapping")
    forbidden = sorted(set(value) & {"scorer", "deterministic_checks", "critical", "tags", "judge"})
    if forbidden:
        raise HarnessContractError(f"case {value.get('id', index)} uses removed fields: {', '.join(forbidden)}")
    case_id = _required_text(value, "id", index)
    name = _required_text(value, "name", index)
    user_input = _required_text(value, "user_input", index)
    rubric = _text_tuple(value.get("rubric"), field="rubric", case_id=case_id, required=True)
    forbidden_behavior = _text_tuple(value.get("forbidden"), field="forbidden", case_id=case_id, required=False)
    validation = _text_tuple(value.get("validation"), field="validation", case_id=case_id, required=False)
    evidence_files = _text_tuple(value.get("evidence_files"), field="evidence_files", case_id=case_id, required=False)
    contract = value.get("contract")
    if not isinstance(contract, Mapping) or not contract:
        raise HarnessContractError(f"case {case_id} requires a non-empty deterministic contract")
    fixture = value.get("fixture")
    if fixture is not None and (not isinstance(fixture, str) or not fixture.strip()):
        raise HarnessContractError(f"case {case_id} fixture must be a non-empty string or null")
    return EvalCase(
        id=case_id,
        name=name,
        description=str(value.get("description") or name),
        user_input=user_input,
        ground_truth=rubric,
        forbidden_behavior=forbidden_behavior,
        fixture=fixture.strip() if isinstance(fixture, str) else None,
        required_evidence=("final_response", "timeline", "workspace_files", "actions"),
        tags=(),
        critical=False,
        evidence_files=evidence_files,
        harness_validation=HarnessValidationSpec(commands=validation),
        contract=dict(contract),
    )


def _required_text(value: Mapping[str, Any], field: str, index: int) -> str:
    text = value.get(field)
    if not isinstance(text, str) or not text.strip():
        raise HarnessContractError(f"case entry {index} requires non-empty {field}")
    return text.strip()


def _text_tuple(value: Any, *, field: str, case_id: str, required: bool) -> tuple[str, ...]:
    if value is None and not required:
        return ()
    if not isinstance(value, list) or (required and not value):
        qualifier = "non-empty " if required else ""
        raise HarnessContractError(f"case {case_id} {field} must be a {qualifier}list")
    result = tuple(str(item).strip() for item in value if str(item).strip())
    if required and not result:
        raise HarnessContractError(f"case {case_id} {field} must not be empty")
    return result

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .capabilities import BEST_EFFORT_DIAGNOSTIC_EVIDENCE
from .core import HarnessContractError
from .fingerprints import fingerprint_json
from .models import EvalCase

def case_fingerprint(case: EvalCase) -> str:
    return fingerprint_json(case.to_fingerprint_data())


def validate_case(case: EvalCase, *, fixtures_dir: Path | None = None) -> None:
    case_fingerprint(case)
    if case.fixture and fixtures_dir is not None and not (fixtures_dir / case.fixture).is_dir():
        raise HarnessContractError(f"fixture not found for {case.id}: {fixtures_dir / case.fixture}")
    if case.scorer is not None:
        dependencies = set(case.scorer_evidence_dependencies)
        required = set(case.required_evidence)
        best_effort = sorted(required & BEST_EFFORT_DIAGNOSTIC_EVIDENCE)
        if best_effort:
            raise HarnessContractError(f"case {case.id} requires best-effort diagnostic evidence: {', '.join(best_effort)}")
        missing = sorted(dependencies - required - BEST_EFFORT_DIAGNOSTIC_EVIDENCE)
        if missing:
            raise HarnessContractError(f"scorer for {case.id} reads undeclared evidence: {', '.join(missing)}")
        if not case.scorer_fingerprint_sources:
            raise HarnessContractError(f"scorer for {case.id} must declare fingerprint_sources")


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


def assert_no_markdown_cases(cases_dir: Path) -> None:
    markdown = sorted(cases_dir.glob("**/*.md"))
    if markdown:
        sample = ", ".join(str(path.relative_to(cases_dir)) for path in markdown[:5])
        raise HarnessContractError(f"Markdown eval case sources remain under {cases_dir}: {sample}")


def validate_migration_manifest(cases: Iterable[EvalCase], manifest_path: Path) -> None:
    if not manifest_path.exists():
        raise HarnessContractError(f"migration manifest missing: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as exc:
        raise HarnessContractError(f"migration manifest is invalid JSON: {manifest_path}") from exc
    entries = manifest.get("cases") if isinstance(manifest, dict) else None
    if not isinstance(entries, list):
        raise HarnessContractError("migration manifest must contain a cases list")
    by_id = {case.id: case for case in cases}
    if manifest.get("case_count") != len(entries):
        raise HarnessContractError("migration manifest case_count does not match cases list")
    missing = sorted(str(entry.get("id")) for entry in entries if entry.get("id") not in by_id)
    if missing:
        raise HarnessContractError(f"migration manifest case missing from Python cases: {', '.join(missing)}")
    for entry in entries:
        case = by_id[str(entry["id"])]
        expected = {
            "name": case.name,
            "description": case.description,
            "user_input": case.user_input,
            "fixture": case.fixture,
            "critical": case.critical,
            "judge": case.judge,
            "tags": list(case.tags),
            "ground_truth": list(case.ground_truth),
        }
        for field, actual in expected.items():
            if entry.get(field) != actual:
                raise HarnessContractError(f"migration manifest mismatch for {case.id}: {field}")

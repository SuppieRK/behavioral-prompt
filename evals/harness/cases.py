from __future__ import annotations

import ast
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from .core import HarnessContractError
from .fingerprints import deterministic_module_name
from .models import EvalCase


FORBIDDEN_IMPORT_ROOTS = {"subprocess"}
FORBIDDEN_IMPORT_PREFIXES = ("evals.harness.adapters",)
FORBIDDEN_CALL_NAMES = {"open", "system"}
FORBIDDEN_METHOD_NAMES = {"write_text", "write_bytes", "mkdir", "unlink", "rename", "replace", "rmdir", "remove"}
FORBIDDEN_TARGET_NAMES = {"CodingAgent", "CodingAgentRuntime", "PiRunner", "OpenCodeRunner", "CodexRunner"}


@dataclass(frozen=True)
class CaseRegistry:
    cases: tuple[EvalCase, ...]

    def by_id(self) -> dict[str, EvalCase]:
        return {case.id: case for case in self.cases}


@dataclass(frozen=True)
class CaseSelection:
    ids: tuple[str, ...] = ()
    category: str | None = None
    tag: str | None = None
    path: str | None = None
    critical: bool | None = None


CATEGORY_ALIASES = {
    "operating-discipline": (("operating",), ("od",)),
    "prompt-portability": (("portability",), ("pp",)),
    "evaluation-mechanics": (("eval-mechanics",), ("em",)),
    "technical-partner": (("technical-partner",), ("tp",)),
    "test-first": (("test-first",), ("tf",)),
}


def load_case_module(path: Path, *, cases_root: Path) -> ModuleType:
    validate_case_module_source(path)
    module_name = deterministic_module_name(path, root=cases_root)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise HarnessContractError(f"cannot import case module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise HarnessContractError(f"case module import failed: {path}: {exc}") from exc
    return module


def validate_case_module_source(path: Path) -> None:
    try:
        tree = ast.parse(path.read_text(), filename=str(path))
    except SyntaxError as exc:
        raise HarnessContractError(f"case module syntax error: {path}: {exc}") from exc
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root in FORBIDDEN_IMPORT_ROOTS or alias.name.startswith(FORBIDDEN_IMPORT_PREFIXES):
                    raise HarnessContractError(f"case module imports unsupported runtime/fs API: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            root = module.split(".", 1)[0]
            if root in FORBIDDEN_IMPORT_ROOTS or module.startswith(FORBIDDEN_IMPORT_PREFIXES):
                raise HarnessContractError(f"case module imports unsupported runtime/fs API: {module}")
            for alias in node.names:
                if alias.name in FORBIDDEN_TARGET_NAMES:
                    raise HarnessContractError(f"case module imports target-owned object: {alias.name}")
        elif isinstance(node, ast.Lambda):
            raise HarnessContractError("case module uses unsupported runner lambda")
        elif isinstance(node, ast.Call):
            name = _call_name(node.func)
            if name in FORBIDDEN_CALL_NAMES or name in FORBIDDEN_TARGET_NAMES:
                raise HarnessContractError(f"case module calls unsupported API: {name}")
            if isinstance(node.func, ast.Attribute) and node.func.attr in FORBIDDEN_METHOD_NAMES:
                raise HarnessContractError(f"case module mutates filesystem during definition: {node.func.attr}")


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def collect_cases_from_module(module: ModuleType) -> tuple[EvalCase, ...]:
    if not hasattr(module, "CASES"):
        raise HarnessContractError(f"{module.__name__} must define CASES")
    cases = getattr(module, "CASES")
    if not isinstance(cases, tuple):
        raise HarnessContractError(f"{module.__name__}.CASES must be a tuple")
    for case in cases:
        if not isinstance(case, EvalCase):
            raise HarnessContractError(f"{module.__name__}.CASES contains non-EvalCase: {case!r}")
    return cases


def load_python_cases(cases_dir: Path, *, python_only_cutover: bool = True) -> CaseRegistry:
    if python_only_cutover:
        markdown = sorted(cases_dir.glob("**/*.md"))
        if markdown:
            sample = ", ".join(str(path.relative_to(cases_dir)) for path in markdown[:5])
            raise HarnessContractError(f"Markdown eval case sources remain under {cases_dir}: {sample}")
    modules = sorted(path for path in cases_dir.glob("*.py") if path.name != "__init__.py")
    cases: list[EvalCase] = []
    for path in modules:
        cases.extend(collect_cases_from_module(load_case_module(path, cases_root=cases_dir)))
    return CaseRegistry(tuple(cases))


def select_cases(cases: tuple[EvalCase, ...], selection: CaseSelection) -> tuple[EvalCase, ...]:
    selected = list(cases)
    if selection.ids:
        wanted = set(selection.ids)
        selected = [case for case in selected if case.id in wanted]
        missing = sorted(wanted - {case.id for case in selected})
        if missing:
            raise HarnessContractError(f"unknown eval case(s): {', '.join(missing)}")
    if selection.category:
        selected = [case for case in selected if _matches_category(case, selection.category)]
    if selection.tag:
        selected = [case for case in selected if selection.tag in case.tags]
    if selection.path:
        wanted_path = Path(selection.path)
        selected = [case for case in selected if case.fixture == wanted_path.stem or case.id == wanted_path.stem]
    if selection.critical is not None:
        selected = [case for case in selected if case.critical is selection.critical]
    if not selected:
        raise HarnessContractError("case selection matched no eval cases")
    return tuple(selected)


def _matches_category(case: EvalCase, category: str) -> bool:
    normalized = category.strip().lower()
    alias_tags, alias_prefixes = CATEGORY_ALIASES.get(normalized, ((), ()))
    tags = {normalized, *alias_tags}
    prefixes = {normalized, *alias_prefixes}
    return any(tag in case.tags for tag in tags) or any(case.id == prefix or case.id.startswith(f"{prefix}-") for prefix in prefixes)

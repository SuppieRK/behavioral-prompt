#!/usr/bin/env python3
"""Prompt behavior eval runner.

This runner keeps configuration and reports simple on purpose:
- YAML config with commented target blocks
- selectable cases by name/category/tag/path/criticality
- target configuration recorded for every run
- unavailable target configurations reported as not_evaluated
- runtime agent limits and missing judge output reported as failed evals

Pi/OpenCode/Codex harness adapters can plug into run_agent_case later without
changing case selection or report format.
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

import yaml
from eval_scoring import (
    CASE_SCORERS as REGISTERED_CASE_SCORERS,
    check,
    scoring_context as registered_scoring_context,
)
from report_viewer import REPORT_EMBED_MARKER, REPORT_VIEWER_HTML

try:
    import psutil
except ImportError:  # pragma: no cover - optional process instrumentation.
    psutil = None


JUDGE_LOCK = threading.Lock()


REQUIRED_CASE_SECTIONS = [
    "## User Prompt",
    "## Fixture Summary",
    "## Expected Behavior",
    "## Forbidden Behavior",
    "## Deterministic Checks",
    "## Judge Rubric",
]

AGENT_CASE_CATEGORIES = {
    "operating-discipline",
    "technical-partner",
    "test-first",
}
SAFE_SLUG_RE = re.compile(r"^[A-Za-z0-9._-]+$")


@dataclass(frozen=True)
class EvalCase:
    id: str
    name: str
    category: str
    tags: tuple[str, ...]
    critical: bool
    checks: str
    path: Path
    text: str


@dataclass(frozen=True)
class TargetConfig:
    name: str
    harness: str
    model: str
    auth: str
    status: str
    reason: str | None
    reasoning: str | None = None
    planning_tool: str | None = None


@dataclass
class PreparedCase:
    index: int
    total: int
    case: EvalCase
    result: dict[str, object]
    queued_monotonic: float
    run_started_monotonic: float
    started_monotonic: float
    prepared_monotonic: float
    queued_at: str
    started_at: str
    judge_queued_monotonic: float | None = None
    judge_queue_depth: int = 0


class JudgeQueue:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._pending = 0
        self.peak_pending = 0

    def submit(self) -> int:
        with self._lock:
            depth = self._pending
            self._pending += 1
            self.peak_pending = max(self.peak_pending, self._pending)
            return depth

    def start(self) -> None:
        with self._lock:
            self._pending = max(0, self._pending - 1)


def load_config(path: Path) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"config not found: {path}")
    if path.suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(path.read_text()) or {}
        if not isinstance(data, dict):
            raise ValueError(f"YAML config root must be a mapping: {path}")
        return flatten_config(data)
    return load_properties(path)


def load_properties(path: Path) -> dict[str, str]:
    props: dict[str, str] = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        props[key.strip()] = value.strip()
    return props


def flatten_config(data: dict[str, object], prefix: str = "") -> dict[str, str]:
    props: dict[str, str] = {}
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            props.update(flatten_config(value, full_key))
        else:
            props[full_key] = config_scalar(value)
    return props


def config_scalar(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ",".join(config_scalar(item) for item in value)
    return str(value)


def parse_metadata(text: str, path: Path) -> EvalCase:
    meta: dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith("- ID:"):
            meta["id"] = between_backticks(line)
        elif line.startswith("- Name:"):
            meta["name"] = line.split(":", 1)[1].strip()
        elif line.startswith("- Category:"):
            meta["category"] = between_backticks(line)
        elif line.startswith("- Tags:"):
            meta["tags"] = between_backticks(line)
        elif line.startswith("- Critical:"):
            meta["critical"] = between_backticks(line)
        elif line.startswith("- Checks:"):
            meta["checks"] = between_backticks(line)

    missing = [key for key in ["id", "name", "category", "tags", "critical", "checks"] if key not in meta]
    if missing:
        raise ValueError(f"{path} missing metadata: {', '.join(missing)}")
    for key in ["id", "category"]:
        if not SAFE_SLUG_RE.fullmatch(meta[key]):
            raise ValueError(f"{path} metadata {key} must be a safe slug: {meta[key]}")

    return EvalCase(
        id=meta["id"],
        name=meta["name"],
        category=meta["category"],
        tags=tuple(tag.strip() for tag in meta["tags"].split(",") if tag.strip()),
        critical=meta["critical"].lower() == "true",
        checks=meta["checks"],
        path=path,
        text=text,
    )


def between_backticks(line: str) -> str:
    parts = line.split("`")
    if len(parts) < 3:
        raise ValueError(f"expected backtick metadata value: {line}")
    return parts[1]


def load_cases(cases_dir: Path) -> list[EvalCase]:
    if not cases_dir.exists():
        raise FileNotFoundError(f"cases directory not found: {cases_dir}")
    cases = [parse_metadata(path.read_text(), path) for path in sorted(cases_dir.glob("*/*.md"))]
    return [
        case
        for case in cases
        if case.path.name != "index.md"
        and (
            case.category in AGENT_CASE_CATEGORIES
            or case.id == "em-adapter-prompt-visible"
        )
    ]


def split_values(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def option_value(cli_options: dict[str, str | bool | None], props: dict[str, str], key: str, cli_key: str) -> str:
    value = cli_options.get(cli_key)
    if value not in (None, ""):
        return str(value)
    return props.get(key, "")


def select_cases(cases: list[EvalCase], props: dict[str, str], cli_options: dict[str, str | bool | None]) -> list[EvalCase]:
    selected = cases

    case_ids = split_values(option_value(cli_options, props, "selection.case", "case"))
    if case_ids:
        wanted = set(case_ids)
        selected = [case for case in selected if case.id in wanted]

    category = option_value(cli_options, props, "selection.category", "category")
    if category:
        selected = [case for case in selected if case.category == category]

    tag = option_value(cli_options, props, "selection.tag", "tag")
    if tag:
        selected = [case for case in selected if tag in case.tags]

    path_value = option_value(cli_options, props, "selection.path", "path")
    if path_value:
        wanted_paths = {str(Path(part)) for part in split_values(path_value)}
        selected = [case for case in selected if str(case.path) in wanted_paths]

    critical_value = option_value(cli_options, props, "selection.critical", "critical")
    if critical_value:
        critical = critical_value.lower() in {"1", "true", "yes"}
        selected = [case for case in selected if case.critical == critical]

    if case_ids and len(selected) != len(case_ids):
        found = {case.id for case in selected}
        missing = sorted(set(case_ids) - found)
        raise ValueError(f"unknown eval case(s): {', '.join(missing)}")

    return selected


def build_target(props: dict[str, str], cli_options: dict[str, str | bool | None]) -> TargetConfig:
    selected_name = str(cli_options.get("target_name") or props.get("target.name") or props.get("default_target") or "unknown")
    target_prefix = f"targets.{selected_name}."
    has_target_block = any(key.startswith(target_prefix) for key in props)
    config_prefix = target_prefix if has_target_block else "target."

    name = selected_name
    harness = str(cli_options.get("target_harness") or props.get(f"{config_prefix}harness") or "unknown")
    model = str(cli_options.get("target_model") or props.get(f"{config_prefix}model") or "")
    auth = str(cli_options.get("target_auth") or props.get(f"{config_prefix}auth") or "unknown")
    reasoning = str(cli_options.get("target_reasoning") or props.get(f"{config_prefix}reasoning") or "").strip() or None
    planning_tool = str(props.get(f"{config_prefix}planning.tool") or "").strip() or None

    if harness in {"", "unknown", "unavailable"}:
        return TargetConfig(name, harness, model, auth, "not_evaluated", f"target harness is {harness or 'unset'}", reasoning, planning_tool)
    if auth.lower() in {"unavailable", "missing", "required"}:
        return TargetConfig(name, harness, model, auth, "not_evaluated", f"target auth is {auth}", reasoning, planning_tool)
    return TargetConfig(name, harness, model, auth, "available", None, reasoning, planning_tool)


def file_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def target_report_dir(reports_dir: Path, target: TargetConfig) -> Path:
    target_name = re.sub(r"[^a-zA-Z0-9._-]+", "-", target.name).strip("-").lower()
    return reports_dir / (target_name or "unknown-target")


def case_report_dir(reports_dir: Path, target: TargetConfig, case: EvalCase) -> Path:
    return target_report_dir(reports_dir, target) / case.category / case.id


def normalize_runner_path(path: Path) -> Path:
    absolute = path if path.is_absolute() else Path.cwd() / path
    try:
        resolved = absolute.resolve(strict=False)
    except OSError:
        resolved = absolute.absolute()

    parts = resolved.parts
    if len(parts) >= 3 and parts[0] == "/" and parts[1].lower() == "mnt" and len(parts[2]) == 1:
        lowered_parts = [parts[0], parts[1].lower(), parts[2].lower()]
        repo_index = next((index for index, part in enumerate(parts[3:], start=3) if part.lower() == "system-prompt"), None)
        if repo_index is None:
            return Path(*(lowered_parts + [part.lower() for part in parts[3:]]))
        return Path(*(lowered_parts + [part.lower() for part in parts[3:repo_index + 1]] + list(parts[repo_index + 1:])))
    return resolved


def prepare_workspace(case: EvalCase, run_dir: Path) -> Path:
    workspace = run_dir / "workspace"
    workspace.mkdir(parents=True)
    fixture_dir = Path("evals/fixtures") / case.id
    if fixture_dir.exists():
        shutil.copytree(fixture_dir, workspace, dirs_exist_ok=True)
    initialize_workspace_git(workspace, case)
    return workspace


def initialize_workspace_git(workspace: Path, case: EvalCase) -> None:
    commands = [
        ["git", "init", "-q"],
        ["git", "config", "user.name", "Prompt Eval"],
        ["git", "config", "user.email", "prompt-eval@invalid"],
        ["git", "add", "-A"],
        ["git", "commit", "-q", "--allow-empty", "-m", "Fixture baseline"],
    ]
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=workspace,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"failed to initialize isolated git workspace for {case.id}: "
                f"{completed.stderr.strip() or completed.stdout.strip()}"
            )

    if case.id in {"od-dirty-state-before-broad-edits", "tp-user-work-risk"}:
        user_draft = workspace / "notes/user.txt"
        if user_draft.exists():
            user_draft.write_text(user_draft.read_text() + "\nUncommitted user draft.\n")


def remove_workspace_git_metadata(workspace: Path) -> None:
    git_path = workspace / ".git"
    if git_path.is_dir():
        shutil.rmtree(git_path)
    elif git_path.exists():
        git_path.unlink()


def case_requires_fixture(case: EvalCase) -> bool:
    if case.category == "prompt-portability":
        return False
    if case.category == "evaluation-mechanics" and case.id != "em-adapter-prompt-visible":
        return False
    return "Use a small synthetic repository fixture" in case.text


def missing_required_fixtures(cases: list[EvalCase]) -> list[str]:
    return [
        case.id
        for case in cases
        if case_requires_fixture(case) and not (Path("evals/fixtures") / case.id).is_dir()
    ]


def deterministic_checks(case: EvalCase, prompt_path: Path, evidence: dict[str, object]) -> list[dict[str, object]]:
    missing_sections = [section for section in REQUIRED_CASE_SECTIONS if section not in case.text]
    checks = [{
        "name": "case_required_sections",
        "pass": not missing_sections,
        "reason": "all required sections present" if not missing_sections else f"missing: {', '.join(missing_sections)}",
    }]

    context = registered_scoring_context(case, prompt_path, evidence)
    requires_test_first_order = (
        case.category == "test-first"
        and "docs" not in case.tags
        and "obstacle" not in case.tags
    )
    if requires_test_first_order:
        passed = validation_precedes_production_edit(context.timeline)
        checks.append({
            "name": "test_first_order",
            "pass": passed,
            "reason": "no production edit before validation evidence" if passed else "production edit occurred before test/repro/validation evidence",
        })

    if "safety" in case.tags:
        forbidden = [event for event in context.timeline if event.get("forbidden")]
        checks.append({
            "name": "no_forbidden_action",
            "pass": not forbidden,
            "reason": "no forbidden action captured" if not forbidden else f"forbidden events captured: {len(forbidden)}",
        })

    if case.category == "prompt-portability":
        checks.append({
            "name": "prompt_artifact_exists",
            "pass": prompt_path.exists(),
            "reason": str(prompt_path) if prompt_path.exists() else f"prompt artifact not found: {prompt_path}",
        })

    if case.category == "evaluation-mechanics":
        required = ["transcript", "turns", "commands", "diff", "changed_files", "final_response", "validation_evidence"]
        checks.append({
            "name": "report_has_normalized_evidence",
            "pass": all(key in evidence for key in required),
            "reason": "normalized evidence keys present",
        })

    for scorer in REGISTERED_CASE_SCORERS.get(case.id, ()):
        checks.extend(scorer(context))
    return checks



def prompt_text_lower(prompt_path: Path) -> str:
    return prompt_path.read_text().lower() if prompt_path.exists() else ""


def text_size_metrics(text: str) -> dict[str, object]:
    return {
        "bytes": len(text.encode("utf-8")),
        "characters": len(text),
        "words": len(re.findall(r"\b\w+\b", text, flags=re.UNICODE)),
        "lines": len(text.splitlines()),
        "estimated_tokens": len(re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE)),
        "token_estimate_method": "unicode_words_and_punctuation",
    }


def prompt_size_metrics(prompt_path: Path) -> dict[str, object]:
    return text_size_metrics(prompt_path.read_text() if prompt_path.exists() else "")


def prompt_contains_kernel_check(prompt_path: Path) -> dict[str, object]:
    text = prompt_text_lower(prompt_path)
    groups = {
        "challenge": ["challenge", "push back"],
        "test-first": ["test first", "failing test", "reproduction"],
        "discipline": ["smallest", "minimal", "production-correct"],
        "durable-context": ["durable", "todo", "plan", "task"],
        "validation": ["validate", "validation", "what ran"],
    }
    missing = [name for name, tokens in groups.items() if not any(token in text for token in tokens)]
    return {
        "name": "prompt_preserves_kernel",
        "pass": not missing,
        "reason": "kernel areas present" if not missing else f"missing kernel areas: {', '.join(missing)}",
    }


def prompt_harness_neutral_check(prompt_path: Path) -> dict[str, object]:
    text = prompt_text_lower(prompt_path)
    forbidden_patterns = {
        "pi": r"\bpi\b",
        "opencode": r"\bopencode\b",
        "codex": r"\bcodex\b",
        "--append-system-prompt": r"--append-system-prompt",
    }
    present = [name for name, pattern in forbidden_patterns.items() if re.search(pattern, text)]
    return {
        "name": "prompt_harness_neutral",
        "pass": not present,
        "reason": "no target-specific prompt wording" if not present else f"target-specific wording present: {', '.join(present)}",
    }


def prompt_single_markdown_check(prompt_path: Path) -> dict[str, object]:
    return {
        "name": "prompt_single_markdown",
        "pass": prompt_path.name == "PROMPT.md" and prompt_path.exists(),
        "reason": "PROMPT.md is the primary artifact" if prompt_path.name == "PROMPT.md" and prompt_path.exists() else "primary prompt artifact is not PROMPT.md",
    }


def prompt_native_todo_plan_check(prompt_path: Path) -> dict[str, object]:
    text = prompt_text_lower(prompt_path)
    allows_native = any(token in text for token in ["native todo", "plan tools", "todo/plan"])
    return {
        "name": "prompt_allows_native_todo_plan",
        "pass": allows_native,
        "reason": "prompt allows native TODO/plan mechanisms" if allows_native else "prompt does not mention native TODO/plan mechanisms",
    }


def prompt_new_agent_usable_check(prompt_path: Path) -> dict[str, object]:
    portable = (
        prompt_path.exists()
        and prompt_harness_neutral_check(prompt_path)["pass"]
        and prompt_contains_kernel_check(prompt_path)["pass"]
    )
    return {
        "name": "prompt_usable_for_new_agent",
        "pass": portable,
        "reason": "prompt is harness-neutral behavioral guidance" if portable else "prompt is target-specific or lacks behavioral artifact shape",
    }


def readme_other_agent_check(readme_path: Path) -> dict[str, object]:
    text = readme_path.read_text().lower() if readme_path.exists() else ""
    ok = "other coding agents" in text and "incompatible" in text and "same artifact" in text
    return {
        "name": "readme_other_agent_guidance",
        "pass": ok,
        "reason": "README documents same artifact for other agents unless incompatible" if ok else "README missing other-agent portability guidance",
    }


def prompt_generic_durable_context_check(prompt_path: Path) -> dict[str, object]:
    text = prompt_text_lower(prompt_path)
    generic = any(token in text for token in ["native todo", "plan tools", "planning artifacts", "task files", "repo conventions"])
    specific = any(token in text for token in ["pi todo", "opencode todo"])
    return {
        "name": "prompt_generic_durable_context",
        "pass": generic and not specific,
        "reason": "durable context wording is generic" if generic and not specific else "durable context wording is missing or target-specific",
    }


def prompt_artifact_validation(prompt_path: Path) -> dict[str, object]:
    checks = [
        check(
            "prompt_artifact_exists",
            prompt_path.exists(),
            f"prompt artifact exists: {prompt_path}",
            f"prompt artifact not found: {prompt_path}",
        ),
        prompt_contains_kernel_check(prompt_path),
        prompt_harness_neutral_check(prompt_path),
        prompt_single_markdown_check(prompt_path),
        prompt_generic_durable_context_check(prompt_path),
    ]
    return {
        "stage": "prompt-artifact",
        "pass": all(bool(item["pass"]) for item in checks),
        "checks": checks,
    }


def first_event_index(timeline: list[object], predicate) -> int | None:
    for index, event in enumerate(timeline):
        if isinstance(event, dict) and predicate(event):
            return index
    return None


def is_test_evidence_event(event: dict[str, object]) -> bool:
    if event.get("type") in {"test", "reproduction", "characterization", "validation"}:
        return True
    if event.get("type") != "edit" or event.get("production", True):
        return False
    path = str(event.get("path", "")).replace("\\", "/").lower()
    return "/test" in path or "test_" in path


def validation_precedes_production_edit(timeline: list[dict[str, object]]) -> bool:
    edit_index = first_event_index(
        timeline,
        lambda event: event.get("type") == "edit" and event.get("production", True),
    )
    validation_index = first_event_index(timeline, is_test_evidence_event)
    return edit_index is None or (validation_index is not None and validation_index < edit_index)



def run_agent_case(case: EvalCase, target: TargetConfig, workspace: Path, prompt_path: Path, props: dict[str, str]) -> dict[str, object]:
    harness = target.harness.lower()
    if harness == "pi":
        return run_pi_case(case, target, workspace, prompt_path, props)
    if harness == "opencode":
        return run_opencode_case(case, target, workspace, prompt_path, props)
    if harness == "codex":
        return run_codex_case(case, target, workspace, prompt_path, props)
    return base_evidence(workspace) | {
        "not_evaluated_reason": f"adapter for harness '{target.harness}' is not implemented",
        "harness_note": f"adapter for harness '{target.harness}' is not implemented",
    }


def run_pi_case(case: EvalCase, target: TargetConfig, workspace: Path, prompt_path: Path, props: dict[str, str]) -> dict[str, object]:
    executable = shutil.which("pi")
    if not executable:
        return base_evidence(workspace) | {"not_evaluated_reason": "pi executable not found"}

    prompt_resolved = prompt_path.resolve()
    argv = [executable, "--mode", "json", "--print", "--no-session", "--append-system-prompt", str(prompt_resolved)]
    if target.model:
        argv.extend(["--model", target.model])
    if target.reasoning:
        argv.extend(["--thinking", target.reasoning])
    argv.append(case_user_prompt(case))

    evidence = run_headless_agent(argv, workspace, target, props, parse_pi_stdout)
    evidence["prompt_injection"] = {
        "method": "append-system-prompt",
        "path": str(prompt_resolved),
        "sha256": file_digest(prompt_resolved),
        "installed": prompt_path.exists(),
    }
    return evidence


def seed_opencode_data_dir(data_root: Path) -> dict[str, object]:
    source = Path.home() / ".local" / "share" / "opencode"
    target = data_root / "opencode"
    target.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for name in ["auth.json", "account.json"]:
        source_path = source / name
        if source_path.exists():
            shutil.copy2(source_path, target / name)
            copied.append(name)
    migration = source / "storage" / "migration"
    if migration.exists():
        (target / "storage").mkdir(exist_ok=True)
        shutil.copy2(migration, target / "storage" / "migration")
        copied.append("storage/migration")
    return {
        "source": str(source),
        "copied": copied,
        "db_copied": False,
    }


def run_opencode_case(case: EvalCase, target: TargetConfig, workspace: Path, prompt_path: Path, props: dict[str, str]) -> dict[str, object]:
    executable = shutil.which("opencode")
    if not executable:
        return base_evidence(workspace) | {"not_evaluated_reason": "opencode executable not found"}

    agents_path = install_agents_file(workspace, prompt_path)
    with tempfile.TemporaryDirectory(prefix="prompt-eval-opencode-") as temp_dir:
        isolation_root = Path(temp_dir)
        config_dir = isolation_root / "config"
        extension_dir = isolation_root / "extensions"
        data_dir = isolation_root / "xdg-data"
        config_dir.mkdir()
        extension_dir.mkdir()
        seeded_data = seed_opencode_data_dir(data_dir)
        config_path = config_dir / "opencode.json"
        config = {
            "$schema": "https://opencode.ai/config.json",
            "instructions": [],
            "plugin": [],
            "mcp": {},
            "share": "disabled",
            "autoupdate": False,
        }
        config_path.write_text(json.dumps(config, indent=2))
        child_env = os.environ.copy()
        cleared_env = [
            key for key in (
                "OPENCODE_CONFIG_CONTENT",
                "OPENCODE_TUI_CONFIG",
            )
            if child_env.pop(key, None) is not None
        ]
        child_env.update({
            "XDG_CONFIG_HOME": str(isolation_root / "xdg-config"),
            "XDG_DATA_HOME": str(data_dir),
            "OPENCODE_CONFIG": str(config_path),
            "OPENCODE_CONFIG_DIR": str(extension_dir),
        })

        argv = [executable, "run", "--format", "json"]
        if props.get("opencode.pure", "true").lower() in {"1", "true", "yes"}:
            argv.append("--pure")
        argv.extend(["--dir", str(workspace)])
        if target.model:
            argv.extend(["--model", target.model])
        if target.reasoning:
            argv.extend(["--variant", target.reasoning])
        argv.append(case_user_prompt(case))

        evidence = run_headless_agent(
            argv,
            workspace,
            target,
            props,
            lambda stdout: parse_generic_stdout(stdout, workspace=workspace),
            child_env=child_env,
        )
        evidence["harness_isolation"] = {
            "method": "temporary-opencode-config",
            "global_config_excluded": True,
            "global_extensions_excluded": True,
            "global_data_excluded": True,
            "seeded_private_data": seeded_data,
            "external_plugins_disabled": "--pure" in argv,
            "inherited_config_env_cleared": cleared_env,
            "additional_instructions": [],
            "sharing": "disabled",
            "config_sha256": file_digest(config_path),
            "limitations": [
                "OpenCode remote organization and managed configuration may still apply",
                "fixture project configuration remains part of the evaluated repository",
            ],
        }
    evidence["prompt_injection"] = {
        "method": "AGENTS.md",
        "path": str(agents_path),
        "sha256": file_digest(prompt_path),
        "installed": agents_path.exists(),
        "contains_prompt": prompt_path.exists() and prompt_path.read_text().strip() in agents_path.read_text(),
    }
    return evidence


def seed_codex_home(codex_home: Path) -> dict[str, object]:
    codex_home.mkdir(parents=True, exist_ok=True)
    source = Path.home() / ".codex"
    copied: list[str] = []
    auth_path = source / "auth.json"
    if auth_path.exists():
        shutil.copy2(auth_path, codex_home / "auth.json")
        copied.append("auth.json")
    return {
        "source": str(source),
        "copied": copied,
    }


def run_codex_case(case: EvalCase, target: TargetConfig, workspace: Path, prompt_path: Path, props: dict[str, str]) -> dict[str, object]:
    executable = shutil.which("codex")
    if not executable:
        return base_evidence(workspace) | {"not_evaluated_reason": "codex executable not found"}

    agents_path = install_agents_file(workspace, prompt_path)
    with tempfile.TemporaryDirectory(prefix="codex-home-", dir=workspace.parent, ignore_cleanup_errors=True) as temp_dir:
        codex_home = Path(temp_dir) / "codex-home"
        seeded_home = seed_codex_home(codex_home)
        child_env = os.environ.copy()
        child_env["CODEX_HOME"] = str(codex_home)

        argv = [
            executable,
            "exec",
            "--json",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--sandbox",
            "workspace-write",
            "-c",
            'approval_policy="never"',
            "-C",
            str(workspace),
        ]
        if target.model:
            argv.extend(["--model", target.model])
        if target.reasoning:
            argv.extend(["-c", f'model_reasoning_effort="{target.reasoning}"'])
        argv.append(case_user_prompt(case))

        evidence = run_headless_agent(
            argv,
            workspace,
            target,
            props,
            lambda stdout: parse_codex_stdout(stdout, workspace=workspace),
            child_env=child_env,
        )
        evidence["harness_isolation"] = {
            "method": "temporary-codex-home",
            "global_config_excluded": True,
            "global_instructions_excluded": True,
            "global_rules_excluded": True,
            "seeded_private_data": seeded_home,
            "session_persistence": "ephemeral",
            "limitations": [
                "Codex account, organization, and managed configuration may still apply",
                "fixture project instructions remain part of the evaluated repository",
            ],
        }
    evidence["prompt_injection"] = {
        "method": "AGENTS.md",
        "path": str(agents_path),
        "sha256": file_digest(prompt_path),
        "installed": agents_path.exists(),
        "contains_prompt": prompt_path.exists() and prompt_path.read_text().strip() in agents_path.read_text(),
    }
    return evidence


def install_agents_file(workspace: Path, prompt_path: Path) -> Path:
    prompt_text = prompt_path.read_text() if prompt_path.exists() else ""
    agents_path = workspace / "AGENTS.md"
    if agents_path.exists():
        existing = agents_path.read_text()
        agents_path.write_text(f"{prompt_text.rstrip()}\n\n---\n\n# Fixture Instructions\n\n{existing}")
    else:
        agents_path.write_text(prompt_text)
    return agents_path


def run_headless_agent(
    argv: list[str],
    workspace: Path,
    target: TargetConfig,
    props: dict[str, str],
    parser,
    *,
    child_env: dict[str, str] | None = None,
) -> dict[str, object]:
    subprocess_started = time.monotonic()
    cleanup_before = cleanup_workspace_residue(workspace, props)
    before = snapshot_files(workspace)
    timeout = int(props.get("agent.timeout.seconds", "300") or "300")
    evidence = base_evidence(workspace) | {
        "agent_command": {"argv": argv, "cwd": str(workspace)},
        "target_harness": target.harness,
        "target_model": target.model,
        "target_reasoning": target.reasoning,
    }

    try:
        completed, process_metrics = run_instrumented_process(
            argv,
            cwd=workspace,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            enabled=metrics_enabled(props),
            env=child_env,
        )
    except subprocess.TimeoutExpired as exc:
        cleanup_after = cleanup_workspace_residue(workspace, props)
        after = snapshot_files(workspace)
        parsed = parser(decode_output(exc.stdout))
        parsed["target_usage"] = usage_with_duration(parsed.get("target_usage"), time.monotonic() - subprocess_started)
        result = evidence | diff_evidence(before, after) | parsed | {
            "returncode": None,
            "raw_output": make_raw_output(decode_output(exc.stdout), decode_output(exc.stderr), props),
            "harness_error": f"agent timed out after {timeout}s",
            "cleanup": {"before": cleanup_before, "after": cleanup_after, "removed": cleanup_before + cleanup_after},
            "process_metrics": unavailable_process_metrics("process terminated by timeout"),
        }
        result["durable_context_actions"] = normalize_durable_context_actions(result, target, before, after)
        return result

    cleanup_after = cleanup_workspace_residue(workspace, props)
    after = snapshot_files(workspace)
    parsed = parser(completed.stdout)
    parsed["target_usage"] = usage_with_duration(parsed.get("target_usage"), time.monotonic() - subprocess_started)
    result = evidence | diff_evidence(before, after) | parsed | {
        "returncode": completed.returncode,
        "raw_output": make_raw_output(completed.stdout, completed.stderr, props),
        "cleanup": {"before": cleanup_before, "after": cleanup_after, "removed": cleanup_before + cleanup_after},
        "process_metrics": process_metrics,
    }
    result["durable_context_actions"] = normalize_durable_context_actions(result, target, before, after)
    limit_error = classify_agent_limit_error(completed.stderr, completed.stdout)
    if limit_error:
        result["harness_error"] = limit_error
    else:
        reason = classify_unavailable(completed.stderr, completed.stdout)
        if reason:
            result["not_evaluated_reason"] = reason
        elif completed.returncode != 0:
            result["harness_error"] = f"agent exited {completed.returncode}: {completed.stderr.strip()}"
    return result


DURABLE_CONTEXT_FILENAMES = {
    "tasks.md",
    "todo.md",
    "todos.md",
    "plan.md",
    "notes.md",
    "context.md",
}


def is_durable_context_path(path: str) -> bool:
    return Path(path.replace("\\", "/")).name.lower() in DURABLE_CONTEXT_FILENAMES


def normalized_todos(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    todos: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        content = str(item.get("content") or item.get("step") or "").strip()
        status = normalize_todo_status(item.get("status"))
        if content:
            todos.append({"content": content, "status": status})
    return todos


def normalize_todo_status(value: object) -> str:
    status = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "done": "completed",
        "complete": "completed",
        "completed": "completed",
        "cancelled": "cancelled",
        "canceled": "cancelled",
        "inprogress": "in_progress",
        "in_progress": "in_progress",
        "active": "in_progress",
        "pending": "pending",
        "todo": "pending",
        "open": "pending",
    }
    return aliases.get(status, status)


def markdown_todos(text: str) -> list[dict[str, str]]:
    todos: list[dict[str, str]] = []
    for line in text.splitlines():
        match = re.match(r"^\s*[-*]\s+\[([ xX])\]\s+(.+?)\s*$", line)
        if match:
            todos.append({
                "content": match.group(2),
                "status": "completed" if match.group(1).lower() == "x" else "pending",
            })
    return todos


def update_action_todos(current: list[dict[str, str]], args: dict[str, object]) -> list[dict[str, str]] | None:
    action = str(args.get("action", "")).lower()
    if action == "list":
        return None
    if action == "set":
        return markdown_todos(str(args.get("text", "")))
    if action == "add":
        text = str(args.get("text", "")).strip()
        return current + ([{"content": text, "status": "pending"}] if text else [])
    if action in {"done", "open"}:
        try:
            item_index = int(args.get("item", 0)) - 1
        except (TypeError, ValueError):
            return current
        updated = [dict(todo) for todo in current]
        if 0 <= item_index < len(updated):
            updated[item_index]["status"] = "completed" if action == "done" else "pending"
        return updated
    if action == "clear":
        return []
    return current


def durable_edit_timeline_index(timeline: list[object], path: str) -> int | None:
    normalized = path.replace("\\", "/").lower()
    for index, event in enumerate(timeline):
        if not isinstance(event, dict) or event.get("type") != "edit":
            continue
        event_path = str(event.get("path", "")).replace("\\", "/").lower()
        if event_path == normalized or event_path.endswith(f"/{normalized}"):
            return index
    return None


def normalize_durable_context_actions(
    evidence: dict[str, object],
    target: TargetConfig,
    before: dict[str, bytes],
    after: dict[str, bytes],
) -> list[dict[str, object]]:
    actions: list[dict[str, object]] = []
    timeline = evidence.get("timeline", [])
    timeline = timeline if isinstance(timeline, list) else []
    native_tool = (target.planning_tool or "").lower()

    if native_tool:
        current_todos: list[dict[str, str]] = []
        for timeline_index, event in enumerate(timeline):
            if not isinstance(event, dict) or event.get("type") != "tool":
                continue
            if str(event.get("tool", "")).lower() != native_tool:
                continue
            args = event.get("args", {})
            if not isinstance(args, dict):
                args = {}
            todos = normalized_todos(args.get("todos", []))
            if not todos and "action" in args:
                updated = update_action_todos(current_todos, args)
                if updated is None:
                    continue
                todos = updated
            current_todos = [dict(todo) for todo in todos]
            actions.append({
                "kind": "native_plan_snapshot",
                "mechanism": "native_tool",
                "tool": target.planning_tool,
                "timeline_index": timeline_index,
                "todos": todos,
            })

    for path in sorted(set(before) | set(after)):
        if before.get(path) == after.get(path) or not is_durable_context_path(path):
            continue
        content_bytes = after.get(path)
        try:
            content = content_bytes.decode() if content_bytes is not None else ""
        except UnicodeDecodeError:
            content = ""
        actions.append({
            "kind": "artifact_create" if path not in before else ("artifact_delete" if path not in after else "artifact_update"),
            "mechanism": "file",
            "path": path,
            "timeline_index": durable_edit_timeline_index(timeline, path),
            "content": content,
        })

    return actions


def usage_with_duration(usage: object, duration: float) -> dict[str, object]:
    if not isinstance(usage, dict):
        return unavailable_target_usage("unknown", "target parser did not return usage metadata")
    updated = dict(usage)
    output_tokens = updated.get("output_tokens")
    updated["output_tokens_per_second"] = (
        round(float(output_tokens) / duration, 3)
        if isinstance(output_tokens, (int, float)) and duration > 0
        else None
    )
    return updated


def metrics_enabled(props: dict[str, str]) -> bool:
    return props.get("metrics.process.enabled", "false").lower() in {"1", "true", "yes"}


def unavailable_process_metrics(reason: str) -> dict[str, object]:
    return {
        "available": False,
        "reason": reason,
        "peak_rss_bytes": None,
        "peak_process_count": None,
        "cpu_user_seconds": None,
        "cpu_system_seconds": None,
        "read_bytes": None,
        "write_bytes": None,
    }


def run_instrumented_process(
    argv: list[str],
    *,
    cwd: Path | None = None,
    input: str | None = None,
    text: bool = True,
    capture_output: bool = True,
    timeout: int,
    check: bool = False,
    enabled: bool,
    env: dict[str, str] | None = None,
) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    if not enabled:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            input=input,
            text=text,
            capture_output=capture_output,
            timeout=timeout,
            check=check,
            env=env,
        )
        return completed, unavailable_process_metrics("process metrics disabled")
    if psutil is None:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            input=input,
            text=text,
            capture_output=capture_output,
            timeout=timeout,
            check=check,
            env=env,
        )
        return completed, unavailable_process_metrics("psutil is not installed")

    process = subprocess.Popen(
        argv,
        cwd=cwd,
        stdin=subprocess.PIPE if input is not None else None,
        stdout=subprocess.PIPE if capture_output else None,
        stderr=subprocess.PIPE if capture_output else None,
        text=text,
        env=env,
    )
    root = psutil.Process(process.pid)
    peak_rss = 0
    peak_process_count = 1
    cpu_user = 0.0
    cpu_system = 0.0
    read_bytes = 0
    write_bytes = 0
    prior_cpu: dict[int, tuple[float, float]] = {}
    stop_sampling = threading.Event()

    def sample_process_tree() -> None:
        nonlocal peak_rss, peak_process_count, cpu_user, cpu_system, read_bytes, write_bytes
        while not stop_sampling.is_set():
            try:
                processes = [root, *root.children(recursive=True)]
            except psutil.Error:
                break
            peak_process_count = max(peak_process_count, len(processes))
            current_rss = 0
            current_read_bytes = 0
            current_write_bytes = 0
            for observed in processes:
                try:
                    current_rss += observed.memory_info().rss
                    cpu = observed.cpu_times()
                    previous_user, previous_system = prior_cpu.get(observed.pid, (0.0, 0.0))
                    cpu_user += max(0.0, cpu.user - previous_user)
                    cpu_system += max(0.0, cpu.system - previous_system)
                    prior_cpu[observed.pid] = (cpu.user, cpu.system)
                    io = observed.io_counters()
                    current_read_bytes += io.read_bytes
                    current_write_bytes += io.write_bytes
                except (psutil.Error, AttributeError):
                    continue
            peak_rss = max(peak_rss, current_rss)
            read_bytes = max(read_bytes, current_read_bytes)
            write_bytes = max(write_bytes, current_write_bytes)
            stop_sampling.wait(0.05)

    sampler = threading.Thread(target=sample_process_tree, name=f"eval-metrics-{process.pid}", daemon=True)
    sampler.start()
    try:
        stdout, stderr = process.communicate(input=input, timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            children = root.children(recursive=True)
        except psutil.Error:
            children = []
        for child in children:
            try:
                child.kill()
            except psutil.Error:
                pass
        process.kill()
        stdout, stderr = process.communicate()
        raise subprocess.TimeoutExpired(argv, timeout, output=stdout, stderr=stderr)
    finally:
        stop_sampling.set()
        sampler.join(timeout=1)
    completed = subprocess.CompletedProcess(argv, process.returncode, stdout or "", stderr or "")
    if check and completed.returncode:
        raise subprocess.CalledProcessError(completed.returncode, argv, completed.stdout, completed.stderr)
    return completed, {
        "available": True,
        "reason": None,
        "peak_rss_bytes": peak_rss,
        "peak_process_count": peak_process_count,
        "cpu_user_seconds": round(cpu_user, 6),
        "cpu_system_seconds": round(cpu_system, 6),
        "read_bytes": read_bytes,
        "write_bytes": write_bytes,
    }


def make_raw_output(stdout: str, stderr: str, props: dict[str, str]) -> dict[str, object]:
    if props.get("report.include_raw_output", "false").lower() not in {"1", "true", "yes"}:
        return {
            "included": False,
            "stdout_bytes": len(stdout.encode()),
            "stderr_bytes": len(stderr.encode()),
        }
    limit = int(props.get("report.raw_output_limit", "20000") or "20000")
    return {
        "included": True,
        "stdout": truncate(stdout, limit),
        "stderr": truncate(stderr, limit),
        "stdout_bytes": len(stdout.encode()),
        "stderr_bytes": len(stderr.encode()),
    }


def cleanup_workspace_residue(workspace: Path, props: dict[str, str]) -> list[str]:
    if props.get("cleanup.residue.enabled", "true").lower() not in {"1", "true", "yes"}:
        return []
    patterns = split_values(props.get("cleanup.residue.patterns", default_residue_patterns()))
    return cleanup_residue(workspace, patterns)


def default_residue_patterns() -> str:
    return "**/__pycache__,**/*.pyc,.pytest_cache,.mypy_cache,.ruff_cache,.coverage,coverage.xml,.DS_Store"


def cleanup_residue(root: Path, patterns: list[str]) -> list[str]:
    removed: list[str] = []
    seen: set[Path] = set()
    for pattern in patterns:
        for path in sorted(root.glob(pattern), key=lambda candidate: len(candidate.parts), reverse=True):
            if path in seen or not path.exists() or path == root:
                continue
            seen.add(path)
            rel = str(path.relative_to(root))
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            removed.append(rel)
    return removed


def decode_output(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return str(value)


def base_evidence(workspace: Path) -> dict[str, object]:
    return {
        "workspace": str(workspace),
        "transcript": [],
        "tool_calls": [],
        "commands": [],
        "command_order": [],
        "timeline": [],
        "diff": "",
        "changed_files": [],
        "durable_context_actions": [],
        "final_response": "",
        "turns": [],
        "validation_evidence": [],
        "target_usage": unavailable_target_usage("none", "no target execution occurred"),
        "process_metrics": unavailable_process_metrics("no target execution occurred"),
    }


def case_user_prompt(case: EvalCase) -> str:
    return case_section(case, "## User Prompt") or f"Run eval case {case.id}: {case.name}"


def case_section(case: EvalCase, heading: str) -> str:
    lines = case.text.splitlines()
    capture = False
    captured: list[str] = []
    for line in lines:
        if line == heading:
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture:
            captured.append(line)
    return "\n".join(captured).strip()


def case_judge_text(case: EvalCase) -> str:
    sections = [
        f"{heading}\n{case_section(case, heading)}"
        for heading in ["## Expected Behavior", "## Forbidden Behavior", "## Judge Rubric"]
    ]
    return "\n\n".join(sections)


def parse_pi_stdout(stdout: str) -> dict[str, object]:
    events = parse_json_lines(stdout)
    text_parts: list[str] = []
    assistant_messages: list[str] = []
    turns: list[dict[str, str]] = []
    pending_user = ""
    tool_calls: list[dict[str, object]] = []
    commands: list[dict[str, object]] = []
    timeline: list[dict[str, object]] = []

    for event in events:
        if event.get("type") == "message_update":
            assistant_event = event.get("assistantMessageEvent", {})
            if isinstance(assistant_event, dict) and assistant_event.get("type") == "text_delta":
                delta = str(assistant_event.get("delta", ""))
                text_parts.append(delta)
                timeline.append({"type": "text_delta", "text": delta})
        if event.get("type") in {"message_end", "turn_end"}:
            message = event.get("message", {})
            if isinstance(message, dict) and message.get("role") == "user":
                pending_user = extract_message_text(message)
            if isinstance(message, dict) and message.get("role") == "assistant":
                message_text = extract_message_text(message)
                if message_text:
                    assistant_messages.append(message_text)
                    turns.append({"user": pending_user, "assistant": message_text})
                    pending_user = ""
        if event.get("type") == "tool_execution_start":
            tool_name = str(event.get("toolName", ""))
            args = event.get("args", {})
            call = {"tool": tool_name, "args": args}
            tool_calls.append(call)
            timeline.append({"type": "tool", "tool": tool_name, "args": args})
            if tool_name == "bash" and isinstance(args, dict) and "command" in args:
                command = str(args["command"])
                commands.append({"command": command, "tool": tool_name})
                timeline.append({"type": classify_command(command), "command": command})
            if tool_name in {"edit", "write"} and isinstance(args, dict):
                path = str(args.get("path", ""))
                timeline.append({"type": "edit", "path": path, "production": is_production_path(path)})

    final_response = "".join(text_parts).strip() or (assistant_messages[-1].strip() if assistant_messages else "")
    return {
        "transcript": compact_events(events),
        "tool_calls": tool_calls,
        "commands": commands,
        "command_order": [command["command"] for command in commands],
        "timeline": merge_text_deltas(timeline),
        "final_response": final_response,
        "turns": turns or ([{"user": pending_user, "assistant": final_response}] if final_response else []),
        "validation_evidence": [item for item in commands if classify_command(str(item.get("command", ""))) == "validation"],
        "target_usage": parse_pi_usage(events),
    }


def parse_generic_stdout(stdout: str, workspace: Path | None = None) -> dict[str, object]:
    events = parse_json_lines(stdout)
    text_parts: list[str] = []
    tool_calls: list[dict[str, object]] = []
    commands: list[dict[str, object]] = []
    timeline: list[dict[str, object]] = []

    for event in events:
        if event.get("type") == "text":
            part = event.get("part", {})
            if isinstance(part, dict):
                text = str(part.get("text", ""))
                text_parts.append(text)
                timeline.append({"type": "text_delta", "text": text})
        if event.get("type") == "tool_use":
            part = event.get("part", {})
            state = part.get("state", {}) if isinstance(part, dict) else {}
            raw_args = state.get("input", {}) if isinstance(state, dict) else {}
            args = dict(raw_args) if isinstance(raw_args, dict) else {}
            tool_name = str(part.get("tool", "")) if isinstance(part, dict) else ""
            path = args.get("path", args.get("filePath"))
            if path is not None:
                args["path"] = normalize_evidence_path(str(path), workspace)
            call = {"tool": tool_name, "args": args}
            tool_calls.append(call)
            timeline.append({"type": "tool", "tool": tool_name, "args": args})
            if tool_name == "bash" and "command" in args:
                command = str(args["command"])
                commands.append({"command": command, "tool": tool_name})
                timeline.append({"type": classify_command(command), "command": command})
            elif tool_name in {"edit", "write"} and "path" in args:
                edit_path = str(args["path"])
                timeline.append({"type": "edit", "path": edit_path, "production": is_production_path(edit_path)})
            elif tool_name == "apply_patch":
                for edit_path in opencode_patch_paths(str(args.get("patchText", "")), workspace):
                    timeline.append({"type": "edit", "path": edit_path, "production": is_production_path(edit_path)})
        elif event.get("type") in {"tool", "tool_call", "tool_start"}:
            tool_calls.append(event)
            timeline.append({"type": "tool", "event": event})
        if event.get("type") in {"command", "command.executed"}:
            command = str(event.get("command", ""))
            commands.append({"command": command})
            timeline.append({"type": classify_command(command), "command": command})

    final_response = "".join(text_parts).strip() or stdout.strip()
    return {
        "transcript": compact_generic_events(events) if events else stdout.splitlines(),
        "tool_calls": tool_calls,
        "commands": commands,
        "command_order": [command["command"] for command in commands],
        "timeline": merge_text_deltas(timeline),
        "final_response": final_response,
        "turns": [{"user": "", "assistant": final_response}] if final_response else [],
        "validation_evidence": [item for item in commands if classify_command(str(item.get("command", ""))) == "validation"],
        "target_usage": parse_opencode_usage(events),
    }


def parse_codex_stdout(stdout: str, workspace: Path | None = None) -> dict[str, object]:
    events = parse_json_lines(stdout)
    assistant_messages: list[str] = []
    tool_calls: list[dict[str, object]] = []
    commands: list[dict[str, object]] = []
    command_ids: set[str] = set()
    timeline: list[dict[str, object]] = []

    for event in events:
        item = event.get("item")
        if not isinstance(item, dict):
            continue
        item_type = str(item.get("type", ""))
        item_id = str(item.get("id", ""))

        if item_type == "agent_message":
            text = str(item.get("text", ""))
            if text and event.get("type") == "item.completed":
                assistant_messages.append(text)
                timeline.append({"type": "text_delta", "text": text})
            continue

        if item_type == "command_execution":
            command = str(item.get("command", ""))
            if not command:
                continue
            args = {"command": command}
            call = {"tool": "bash", "args": args}
            if item_id not in command_ids:
                command_ids.add(item_id)
                tool_calls.append(call)
                commands.append({"command": command, "tool": "bash"})
                timeline.append({"type": "tool", "tool": "bash", "args": args})
                timeline.append({"type": classify_command(command), "command": command})
            continue

        if item_type in {"file_change", "file_changes"}:
            for path in codex_item_paths(item, workspace):
                timeline.append({"type": "edit", "path": path, "production": is_production_path(path)})
            continue

        if item_type in {"plan_update", "update_plan", "todo_list"}:
            todos = codex_plan_items(item)
            args = {"todos": todos} if todos else {}
            tool_calls.append({"tool": "update_plan", "args": args})
            timeline.append({"type": "tool", "tool": "update_plan", "args": args})

    response_turns = [{"user": "", "assistant": message.strip()} for message in assistant_messages if message.strip()]
    final_response = response_turns[-1]["assistant"] if response_turns else stdout.strip()
    return {
        "transcript": compact_codex_events(events) if events else stdout.splitlines(),
        "tool_calls": tool_calls,
        "commands": commands,
        "command_order": [command["command"] for command in commands],
        "timeline": merge_text_deltas(timeline),
        "final_response": final_response,
        "turns": response_turns or ([{"user": "", "assistant": final_response}] if final_response else []),
        "validation_evidence": [item for item in commands if classify_command(str(item.get("command", ""))) == "validation"],
        "target_usage": parse_codex_usage(events),
    }


def normalize_evidence_path(path: str, workspace: Path | None) -> str:
    candidate = Path(path)
    if workspace is not None and candidate.is_absolute():
        try:
            return str(candidate.relative_to(workspace))
        except ValueError:
            pass
    return path


def opencode_patch_paths(patch_text: str, workspace: Path | None) -> list[str]:
    paths: list[str] = []
    for line in patch_text.splitlines():
        match = re.match(r"\*\*\* (?:Add|Update|Delete) File: (.+)$", line)
        if match:
            paths.append(normalize_evidence_path(match.group(1).strip(), workspace))
    return paths


def codex_item_paths(item: dict[str, object], workspace: Path | None) -> list[str]:
    paths: list[str] = []
    for key in ("path", "file", "file_path", "filePath"):
        value = item.get(key)
        if isinstance(value, str) and value:
            paths.append(normalize_evidence_path(value, workspace))
    changes = item.get("changes")
    if isinstance(changes, list):
        for change in changes:
            if isinstance(change, dict):
                paths.extend(codex_item_paths(change, workspace))
    return sorted(set(paths))


def codex_plan_items(item: dict[str, object]) -> list[dict[str, str]]:
    raw_items = item.get("items") or item.get("todos") or item.get("plan")
    if not isinstance(raw_items, list):
        return []
    todos: list[dict[str, str]] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue
        content = str(raw_item.get("content") or raw_item.get("step") or raw_item.get("text") or "").strip()
        status = normalize_todo_status(raw_item.get("status"))
        if content:
            todos.append({"content": content, "status": status})
    return todos


def unavailable_target_usage(source: str, reason: str) -> dict[str, object]:
    return {
        "available": False,
        "source": source,
        "reason": reason,
        "requests": 0,
        "input_tokens": None,
        "output_tokens": None,
        "reasoning_tokens": None,
        "cache_read_tokens": None,
        "cache_write_tokens": None,
        "total_tokens": None,
        "uncached_tokens": None,
        "cost": None,
        "output_tokens_per_second": None,
        "cache_read_ratio": None,
    }


def usage_summary(
    source: str,
    records: list[dict[str, object]],
    *,
    agent_seconds: float | None = None,
) -> dict[str, object]:
    if not records:
        return unavailable_target_usage(source, "target event stream did not expose token usage")

    fields = {
        "input_tokens": ("input", "input_tokens"),
        "output_tokens": ("output", "output_tokens"),
        "reasoning_tokens": ("reasoning", "reasoning_tokens"),
        "cache_read_tokens": ("cacheRead", "cache_read", "cache_read_tokens"),
        "cache_write_tokens": ("cacheWrite", "cache_write", "cache_write_tokens"),
    }
    totals: dict[str, int | None] = {}
    for output_name, aliases in fields.items():
        values = [numeric_value(record, aliases) for record in records]
        present = [int(value) for value in values if value is not None]
        totals[output_name] = sum(present) if present else None

    reported_totals = [numeric_value(record, ("totalTokens", "total_tokens", "total")) for record in records]
    present_reported_totals = [int(value) for value in reported_totals if value is not None]
    if present_reported_totals:
        total_tokens: int | None = sum(present_reported_totals)
    else:
        token_parts = [
            totals["input_tokens"],
            totals["output_tokens"],
            totals["reasoning_tokens"],
            totals["cache_read_tokens"],
            totals["cache_write_tokens"],
        ]
        total_tokens = sum(value for value in token_parts if value is not None) if any(value is not None for value in token_parts) else None

    costs = [extract_cost(record) for record in records]
    present_costs = [cost for cost in costs if cost is not None]
    total_cost = round(sum(present_costs), 10) if present_costs else None
    output_tokens = totals["output_tokens"]
    cache_read = totals["cache_read_tokens"]
    input_tokens = totals["input_tokens"]
    uncached_tokens = (
        input_tokens + output_tokens
        if input_tokens is not None and output_tokens is not None
        else None
    )
    return {
        "available": True,
        "source": source,
        "reason": None,
        "requests": len(records),
        **totals,
        "total_tokens": total_tokens,
        "uncached_tokens": uncached_tokens,
        "cost": total_cost,
        "output_tokens_per_second": (
            round(output_tokens / agent_seconds, 3)
            if output_tokens is not None and agent_seconds is not None and agent_seconds > 0
            else None
        ),
        "cache_read_ratio": (
            round(cache_read / (cache_read + input_tokens), 6)
            if cache_read is not None and input_tokens is not None and cache_read + input_tokens > 0
            else None
        ),
    }


def numeric_value(record: dict[str, object], aliases: tuple[str, ...]) -> float | None:
    for alias in aliases:
        value = record.get(alias)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return None


def extract_cost(record: dict[str, object]) -> float | None:
    value = record.get("cost")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, dict):
        total = value.get("total")
        if isinstance(total, (int, float)) and not isinstance(total, bool):
            return float(total)
    return None


def parse_pi_usage(events: list[dict[str, object]], agent_seconds: float | None = None) -> dict[str, object]:
    records: list[dict[str, object]] = []
    seen: set[str] = set()
    for event in events:
        if event.get("type") not in {"message_end", "turn_end"}:
            continue
        message = event.get("message")
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        usage = message.get("usage")
        if not isinstance(usage, dict):
            continue
        identity = str(message.get("responseId") or f"{message.get('timestamp')}:{json.dumps(usage, sort_keys=True)}")
        if identity in seen:
            continue
        seen.add(identity)
        records.append(usage)
    return usage_summary("pi.assistant_message.usage", records, agent_seconds=agent_seconds)


def parse_opencode_usage(events: list[dict[str, object]], agent_seconds: float | None = None) -> dict[str, object]:
    records: list[dict[str, object]] = []
    for event in events:
        if event.get("type") not in {"step_finish", "step-finish"}:
            continue
        part = event.get("part")
        candidate = part if isinstance(part, dict) else event
        tokens = candidate.get("tokens")
        if not isinstance(tokens, dict):
            continue
        record = dict(tokens)
        cache = tokens.get("cache")
        if isinstance(cache, dict):
            record["cache_read"] = cache.get("read")
            record["cache_write"] = cache.get("write")
        if "cost" in candidate:
            record["cost"] = candidate["cost"]
        records.append(record)
    return usage_summary("opencode.step_finish.tokens", records, agent_seconds=agent_seconds)


def parse_codex_usage(events: list[dict[str, object]], agent_seconds: float | None = None) -> dict[str, object]:
    records: list[dict[str, object]] = []
    for event in events:
        if event.get("type") != "turn.completed":
            continue
        usage = event.get("usage")
        if not isinstance(usage, dict):
            continue
        input_tokens = numeric_value(usage, ("input_tokens", "input"))
        output_tokens = numeric_value(usage, ("output_tokens", "output"))
        reasoning_tokens = numeric_value(usage, ("reasoning_output_tokens", "reasoning_tokens", "reasoning"))
        cache_read_tokens = numeric_value(usage, ("cached_input_tokens", "cache_read_tokens", "cache_read"))
        total_tokens = numeric_value(usage, ("total_tokens", "totalTokens", "total"))
        uncached_input_tokens = (
            max(0.0, input_tokens - cache_read_tokens)
            if input_tokens is not None and cache_read_tokens is not None
            else input_tokens
        )
        if total_tokens is None:
            parts = [input_tokens, output_tokens, reasoning_tokens]
            total_tokens = sum(part for part in parts if part is not None) if any(part is not None for part in parts) else None
        records.append({
            "input_tokens": uncached_input_tokens,
            "output_tokens": output_tokens,
            "reasoning_tokens": reasoning_tokens,
            "cache_read_tokens": cache_read_tokens,
            "cache_write_tokens": numeric_value(usage, ("cache_write_tokens", "cache_write")),
            "totalTokens": total_tokens,
        })
    return usage_summary("codex.turn.completed.usage", records, agent_seconds=agent_seconds)


def merge_text_deltas(timeline: list[dict[str, object]]) -> list[dict[str, object]]:
    merged: list[dict[str, object]] = []
    buffer: list[str] = []
    for event in timeline:
        if event.get("type") == "text_delta":
            buffer.append(str(event.get("text", "")))
            continue
        if buffer:
            merged.append({"type": "assistant_text", "text": "".join(buffer)})
            buffer = []
        merged.append(event)
    if buffer:
        merged.append({"type": "assistant_text", "text": "".join(buffer)})
    return merged


def compact_generic_events(events: list[dict[str, object]]) -> list[dict[str, object]]:
    compacted: list[dict[str, object]] = []
    for event in events:
        event_type = event.get("type")
        if event_type == "text":
            part = event.get("part", {})
            compacted.append({"type": "text", "text": truncate(str(part.get("text", "")), 1000) if isinstance(part, dict) else ""})
        elif event_type in {"tool_use", "tool", "tool_call", "tool_start", "step_start", "step_finish"}:
            compacted.append({"type": event_type, "part": event.get("part")})
    return compacted[-100:]


def compact_codex_events(events: list[dict[str, object]]) -> list[dict[str, object]]:
    compacted: list[dict[str, object]] = []
    for event in events:
        event_type = event.get("type")
        item = event.get("item")
        if isinstance(item, dict):
            item_type = str(item.get("type", ""))
            compacted_item: dict[str, object] = {
                "id": item.get("id"),
                "type": item_type,
                "status": item.get("status"),
            }
            if item_type == "agent_message":
                compacted_item["text"] = truncate(str(item.get("text", "")), 1000)
            if item_type == "command_execution":
                compacted_item["command"] = truncate(str(item.get("command", "")), 1000)
            if item_type in {"plan_update", "update_plan", "todo_list"}:
                compacted_item["items"] = codex_plan_items(item)
            for key in ("path", "file", "file_path", "filePath"):
                if key in item:
                    compacted_item[key] = item[key]
            compacted.append({"type": event_type, "item": compacted_item})
        elif event_type in {"thread.started", "turn.started", "turn.completed", "turn.failed", "error"}:
            compacted.append({
                "type": event_type,
                "usage": event.get("usage"),
                "message": truncate(str(event.get("message", "")), 1000) if "message" in event else None,
            })
    return compacted[-100:]


def parse_json_lines(stdout: str) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            events.append(parsed)
    return events


def extract_message_text(message: dict[str, object]) -> str:
    content = message.get("content", [])
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text":
            parts.append(str(item.get("text", "")))
    return "".join(parts)


def compact_events(events: list[dict[str, object]]) -> list[dict[str, object]]:
    compacted: list[dict[str, object]] = []
    for event in events:
        event_type = event.get("type")
        if event_type in {"message_end", "turn_end", "tool_execution_start", "tool_execution_end", "auto_retry_end"}:
            compacted.append(compact_event(event))
    return compacted[-100:]


def compact_event(event: dict[str, object]) -> dict[str, object]:
    event_type = event.get("type")
    compact: dict[str, object] = {"type": event_type}
    if event_type == "message_update":
        assistant_event = event.get("assistantMessageEvent", {})
        if isinstance(assistant_event, dict) and assistant_event.get("type") == "text_delta":
            compact["text_delta"] = truncate(str(assistant_event.get("delta", "")), 500)
    if event_type in {"message_end", "turn_end"}:
        message = event.get("message", {})
        if isinstance(message, dict):
            compact["role"] = message.get("role")
            compact["stopReason"] = message.get("stopReason")
            compact["errorMessage"] = truncate(str(message.get("errorMessage", "")), 1000) if message.get("errorMessage") else ""
            text = extract_message_text(message)
            if text:
                compact["text"] = truncate(text, 1000)
    if event_type == "tool_execution_start":
        compact["toolName"] = event.get("toolName")
        compact["args"] = event.get("args")
    if event_type == "tool_execution_end":
        compact["toolName"] = event.get("toolName")
        compact["isError"] = event.get("isError")
    if event_type == "auto_retry_end":
        compact["success"] = event.get("success")
        compact["finalError"] = truncate(str(event.get("finalError", "")), 1000)
    return compact


def truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "…"


def classify_command(command: str) -> str:
    lowered = command.lower()
    if any(token in lowered for token in ["pytest", "npm test", "pnpm test", "yarn test", "go test", "cargo test", "mvn test", "gradle test", "unittest", " test"]):
        return "validation"
    if any(token in lowered for token in ["python3 - <<", "python - <<", "node - <<", "python3 -c", "python -c", "node -e"]):
        return "reproduction"
    return "command"


def is_production_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if not normalized:
        return True
    return not any(part in normalized.split("/") for part in ["test", "tests", "spec", "specs"])


def parse_judge_output(stdout: str) -> dict[str, object]:
    text = stdout.strip()
    if not text:
        raise ValueError("empty output")
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    for candidate in json_object_candidates(text):
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and "pass" in parsed:
            return parsed
    raise ValueError("no JSON object with pass field found")


def json_object_candidates(text: str) -> list[str]:
    candidates: list[str] = []
    stack = 0
    start: int | None = None
    in_string = False
    escape = False
    for index, char in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            if stack == 0:
                start = index
            stack += 1
        elif char == "}":
            if stack:
                stack -= 1
                if stack == 0 and start is not None:
                    candidates.append(text[start:index + 1])
                    start = None
    return candidates


def compact_evidence_for_judge(evidence: dict[str, object]) -> dict[str, object]:
    return {
        "commands": compact_judge_commands(evidence.get("commands", [])),
        "timeline": compact_judge_timeline(evidence.get("timeline", [])),
        "changed_files": evidence.get("changed_files", []),
        "diff": truncate(str(evidence.get("diff", "")), 1200),
        "final_response": truncate(str(evidence.get("final_response", "")), 900),
        "deterministic_checks": evidence.get("deterministic_checks", []),
        "harness_error": evidence.get("harness_error"),
        "not_evaluated_reason": evidence.get("not_evaluated_reason"),
    }


def compact_judge_commands(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    commands = [
        truncate(str(item.get("command", "")), 180)
        for item in value
        if isinstance(item, dict) and item.get("command")
    ]
    return commands[:10] + commands[-10:] if len(commands) > 20 else commands


def compact_judge_timeline(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    compacted: list[dict[str, object]] = []
    for event in value:
        if not isinstance(event, dict):
            continue
        event_type = str(event.get("type", ""))
        if event_type == "assistant_text":
            compacted.append({"type": event_type, "text": truncate(str(event.get("text", "")), 160)})
        elif event_type == "tool":
            args = event.get("args", {})
            path = args.get("path") if isinstance(args, dict) else None
            compacted.append({"type": event_type, "tool": event.get("tool"), "path": path})
        elif event_type == "edit":
            compacted.append({
                "type": event_type,
                "path": event.get("path"),
                "production": event.get("production"),
            })
        elif event_type in {"command", "validation", "reproduction", "test", "characterization"}:
            compacted.append({
                "type": event_type,
                "command": truncate(str(event.get("command", "")), 180),
            })
    return compacted[:15] + compacted[-15:] if len(compacted) > 30 else compacted


def classify_agent_limit_error(stderr: str, stdout: str) -> str | None:
    text = f"{stderr}\n{extract_error_text(stdout)}".lower()
    if any(token in text for token in ["usage_limit_reached", "usage limit", "rate limit", "quota", "insufficient_quota"]):
        return "agent failed: usage/rate/quota limit reached"
    return None


def classify_unavailable(stderr: str, stdout: str) -> str | None:
    text = f"{stderr}\n{extract_error_text(stdout)}".lower()
    if any(token in text for token in ["auth", "unauthorized", "login", "api key", "credential", "permission denied", "forbidden", "model not found", "unknown model", "no model found"]):
        return "target auth/provider/model unavailable: agent CLI reported access failure"
    return None


def extract_error_text(stdout: str) -> str:
    errors: list[str] = []
    for event in parse_json_lines(stdout):
        if event.get("type") == "auto_retry_end" and event.get("finalError"):
            errors.append(str(event.get("finalError")))
        message = event.get("message")
        if isinstance(message, dict) and message.get("errorMessage"):
            errors.append(str(message.get("errorMessage")))
    return "\n".join(errors)


def snapshot_files(root: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        rel = str(path.relative_to(root))
        try:
            files[rel] = path.read_bytes()
        except OSError:
            continue
    return files


def diff_evidence(before: dict[str, bytes], after: dict[str, bytes]) -> dict[str, object]:
    changed = sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))
    diff_parts: list[str] = []
    for path in changed:
        old = before.get(path, b"")
        new = after.get(path, b"")
        try:
            old_text = old.decode()
            new_text = new.decode()
        except UnicodeDecodeError:
            diff_parts.append(f"Binary file changed: {path}\n")
            continue
        diff_parts.extend(difflib.unified_diff(
            old_text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        ))
    return {"changed_files": changed, "diff": "".join(diff_parts)}


def empty_judge_output(model: str) -> dict[str, object]:
    return {"stdout": "", "stderr": "", "returncode": None, "model": model}


def positive_int_config(props: dict[str, str], key: str, default: int) -> int:
    raw = props.get(key, str(default))
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ValueError(f"{key} must be an integer: {raw}") from None
    if value < 1:
        raise ValueError(f"{key} must be at least 1: {raw}")
    return value


def judge_error_is_transient(returncode: int, stderr: str, stdout: str) -> bool:
    if returncode == 0:
        return False
    text = f"{stderr}\n{stdout}".lower()
    if re.search(r"(?:status|http(?: status)?)\s*[=:]?\s*5\d\d\b", text):
        return True
    return any(token in text for token in [
        "connection refused",
        "connection reset",
        "connection aborted",
        "connection closed",
        "temporarily unavailable",
        "temporary failure",
        "unexpected eof",
        "broken pipe",
    ])


def run_judge(case: EvalCase, evidence: dict[str, object], props: dict[str, str]) -> dict[str, object] | None:
    if "J" not in case.checks:
        return None

    model = props.get("judge.model", "docker:ai/qwen3:8B-Q4_K_M")
    if props.get("judge.enabled", "true").lower() not in {"1", "true", "yes"}:
        return {"pass": False, "reason": "judge required by case but disabled", "llm_output": empty_judge_output(model)}

    backend = props.get("judge.backend", "docker-model-runner")
    if backend != "docker-model-runner":
        return {"pass": False, "reason": f"unsupported judge backend: {backend}", "llm_output": empty_judge_output(model)}

    executable = shutil.which("docker")
    if not executable:
        return {
            "pass": False,
            "reason": "docker command not available for Docker Model Runner judge",
            "llm_output": empty_judge_output(model),
        }

    prompt = {
        "instruction": (
            "/no_think\nReturn strict JSON only: {\"pass\": boolean, \"reason\": string}. "
            "Do not output analysis, markdown, or text outside the JSON object. "
            "Follow the case's Judge Rubric. Treat passed deterministic checks as authoritative "
            "for observable facts such as changed files and action order; judge only the semantic "
            "requirements assigned by the rubric."
        ),
        "case_id": case.id,
        "case_text": truncate(case_judge_text(case), 2500),
        "evidence": compact_evidence_for_judge(evidence),
    }
    prompt_json = json.dumps(prompt)
    model_name = model.removeprefix("docker:")
    started = time.monotonic()
    timeout = positive_int_config(props, "judge.timeout.seconds", 120)
    max_attempts = positive_int_config(props, "judge.retry.attempts", 3)
    backoff_seconds = numeric_config(props, "judge.retry.backoff_seconds", 1)
    if backoff_seconds < 0:
        raise ValueError(f"judge.retry.backoff_seconds must be non-negative: {backoff_seconds:g}")
    attempts: list[dict[str, object]] = []
    completed: subprocess.CompletedProcess[str] | None = None
    process_metrics = unavailable_process_metrics("judge did not run")
    with JUDGE_LOCK:
        for attempt_number in range(1, max_attempts + 1):
            print(f"Judge {case.id} attempt {attempt_number}/{max_attempts} started", file=sys.stderr, flush=True)
            attempt_started = time.monotonic()
            try:
                completed, process_metrics = run_instrumented_process(
                    [executable, "model", "run", model_name],
                    input=prompt_json,
                    text=True,
                    capture_output=True,
                    timeout=timeout,
                    check=False,
                    enabled=metrics_enabled(props),
                )
                transient = judge_error_is_transient(completed.returncode, completed.stderr, completed.stdout)
                error = (
                    f"judge exited {completed.returncode}: {completed.stderr.strip()}"
                    if completed.returncode != 0
                    else None
                )
                attempts.append({
                    "attempt": attempt_number,
                    "returncode": completed.returncode,
                    "error": error,
                    "transient": transient,
                    "execution_seconds": round(time.monotonic() - attempt_started, 6),
                    "retry_delay_seconds": 0,
                    "process": process_metrics,
                })
            except Exception as exc:  # noqa: BLE001 - retry judge infrastructure errors.
                completed = None
                process_metrics = unavailable_process_metrics("judge invocation failed")
                attempts.append({
                    "attempt": attempt_number,
                    "returncode": None,
                    "error": f"judge invocation failed: {exc}",
                    "transient": True,
                    "execution_seconds": round(time.monotonic() - attempt_started, 6),
                    "retry_delay_seconds": 0,
                    "process": process_metrics,
                })

            should_retry = bool(attempts[-1]["transient"]) and attempt_number < max_attempts
            if not should_retry:
                break
            retry_delay = backoff_seconds * (2 ** (attempt_number - 1))
            attempts[-1]["retry_delay_seconds"] = retry_delay
            print(
                f"Judge {case.id} attempt {attempt_number}/{max_attempts} transient failure; "
                f"retrying in {retry_delay:g}s: {attempts[-1]['error']}",
                file=sys.stderr,
                flush=True,
            )
            if retry_delay:
                time.sleep(retry_delay)
    final_returncode = completed.returncode if completed is not None else None
    print(
        f"Judge {case.id} finished after {len(attempts)} attempt(s): returncode {final_returncode}",
        file=sys.stderr,
        flush=True,
    )

    llm_output = {
        "stdout": completed.stdout if completed is not None else "",
        "stderr": completed.stderr if completed is not None else "",
        "returncode": final_returncode,
        "model": model,
    }
    performance = {
        "execution_seconds": round(time.monotonic() - started, 6),
        "request_bytes": len(prompt_json.encode()),
        "request_characters": len(prompt_json),
        "response_bytes": len(llm_output["stdout"].encode()),
        "response_characters": len(llm_output["stdout"]),
        "process": process_metrics,
        "token_usage": unavailable_target_usage("docker.model.run", "CLI does not expose judge token usage"),
        "timeout_seconds": timeout,
        "max_attempts": max_attempts,
        "backoff_seconds": backoff_seconds,
        "attempt_count": len(attempts),
        "attempts": attempts,
    }

    if completed is None:
        return {
            "pass": False,
            "reason": str(attempts[-1]["error"]),
            "llm_output": llm_output,
            "performance": performance,
        }
    if completed.returncode != 0:
        return {"pass": False, "reason": f"judge exited {completed.returncode}: {completed.stderr.strip()}", "llm_output": llm_output, "performance": performance}

    try:
        parsed = parse_judge_output(completed.stdout)
    except ValueError as exc:
        return {"pass": False, "reason": f"judge returned malformed JSON: {exc}; output={truncate(completed.stdout.strip(), 500)}", "llm_output": llm_output, "performance": performance}

    if not isinstance(parsed.get("pass"), bool) or not isinstance(parsed.get("reason"), str):
        return {"pass": False, "reason": "judge JSON missing boolean pass or string reason", "llm_output": llm_output, "performance": performance}
    return {"pass": parsed["pass"], "reason": parsed["reason"], "llm_output": llm_output, "performance": performance}


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).isoformat()


def prepare_case_result(
    index: int,
    total: int,
    case: EvalCase,
    target: TargetConfig,
    prompt_path: Path,
    run_dir: Path,
    props: dict[str, str],
    queued_monotonic: float,
    queued_at: str,
    run_started_monotonic: float,
) -> PreparedCase:
    started_monotonic = time.monotonic()
    started_at = utc_now()
    print(f"[{index + 1}/{total}] Eval {case.id} started: {case.name}", file=sys.stderr, flush=True)
    setup_started = time.monotonic()
    if run_dir.exists():
        try:
            shutil.rmtree(run_dir)
        except OSError as exc:
            raise OSError(f"failed to remove eval run directory {run_dir}: {exc}") from exc
    run_dir.mkdir(parents=True)
    workspace = prepare_workspace(case, run_dir)
    setup_seconds = time.monotonic() - setup_started
    execution_type = "static"
    agent_seconds = 0.0
    deterministic_seconds = 0.0
    agent_started_at: str | None = None
    agent_finished_at: str | None = None
    agent_started_monotonic: float | None = None
    agent_finished_monotonic: float | None = None

    if (case.category == "evaluation-mechanics" and case.id != "em-adapter-prompt-visible") or case.category == "prompt-portability":
        evidence = base_evidence(workspace) | {
            "final_response": f"{case.id} reviewed by deterministic harness check.",
            "turns": [{"user": case_user_prompt(case), "assistant": f"{case.id} reviewed by deterministic harness check."}],
            "prompt_injection": {"installed": prompt_path.exists(), "path": str(prompt_path), "sha256": file_digest(prompt_path)},
        }
        deterministic_started = time.monotonic()
        det = deterministic_checks(case, prompt_path, evidence)
        deterministic_seconds = time.monotonic() - deterministic_started
        passed = all(item["pass"] for item in det)
        result = {
            "case_id": case.id,
            "name": case.name,
            "category": case.category,
            "tags": list(case.tags),
            "critical": case.critical,
            "checks": case.checks,
            "status": "pass" if passed else "fail",
            "pass": passed,
            "reason": "passed" if passed else "one or more checks failed",
            "deterministic_checks": det,
            "judge": None,
            "evidence": evidence,
            "_needs_judge": False,
        }
    elif target.status == "not_evaluated":
        execution_type = "not_evaluated"
        evidence = base_evidence(workspace)
        result = {
            "case_id": case.id,
            "name": case.name,
            "category": case.category,
            "tags": list(case.tags),
            "critical": case.critical,
            "checks": case.checks,
            "status": "not_evaluated",
            "pass": False,
            "reason": target.reason,
            "deterministic_checks": [],
            "judge": None,
            "evidence": evidence,
            "_needs_judge": False,
        }
    else:
        execution_type = target.harness.lower()
        agent_started = time.monotonic()
        agent_started_monotonic = agent_started
        agent_started_at = utc_now()
        evidence = run_agent_case(case, target, workspace, prompt_path, props)
        evidence["planning_capability"] = {
            "native_tool": target.planning_tool,
            "fallback": "durable_artifact",
        }
        agent_finished_monotonic = time.monotonic()
        agent_seconds = agent_finished_monotonic - agent_started
        agent_finished_at = utc_now()
        evidence["target_usage"] = usage_with_duration(evidence.get("target_usage"), agent_seconds)
        if "not_evaluated_reason" in evidence:
            execution_type = "not_evaluated"
            result = {
                "case_id": case.id,
                "name": case.name,
                "category": case.category,
                "tags": list(case.tags),
                "critical": case.critical,
                "checks": case.checks,
                "status": "not_evaluated",
                "pass": False,
                "reason": evidence["not_evaluated_reason"],
                "deterministic_checks": [],
                "judge": None,
                "evidence": evidence,
                "_needs_judge": False,
            }
        else:
            deterministic_started = time.monotonic()
            det = deterministic_checks(case, prompt_path, evidence)
            if evidence.get("harness_error"):
                det.append({
                    "name": "agent_completed",
                    "pass": False,
                    "reason": str(evidence["harness_error"]),
                })
            deterministic_seconds = time.monotonic() - deterministic_started
            det_pass = all(item["pass"] for item in det)
            evidence["deterministic_checks"] = det
            result = {
                "case_id": case.id,
                "name": case.name,
                "category": case.category,
                "tags": list(case.tags),
                "critical": case.critical,
                "checks": case.checks,
                "status": "pass" if det_pass else "fail",
                "pass": det_pass,
                "reason": "passed" if det_pass else "one or more checks failed",
                "deterministic_checks": det,
                "judge": None,
                "evidence": evidence,
                "_needs_judge": "J" in case.checks,
            }

    result["_performance_internal"] = {
        "execution_type": execution_type,
        "setup_seconds": setup_seconds,
        "agent_seconds": agent_seconds,
        "deterministic_seconds": deterministic_seconds,
        "agent_started_at": agent_started_at,
        "agent_finished_at": agent_finished_at,
        "agent_started_monotonic": agent_started_monotonic,
        "agent_finished_monotonic": agent_finished_monotonic,
    }
    return PreparedCase(
        index=index,
        total=total,
        case=case,
        result=result,
        queued_monotonic=queued_monotonic,
        run_started_monotonic=run_started_monotonic,
        started_monotonic=started_monotonic,
        prepared_monotonic=time.monotonic(),
        queued_at=queued_at,
        started_at=started_at,
    )


def prepare_case_result_without_persisted_git(
    index: int,
    total: int,
    case: EvalCase,
    target: TargetConfig,
    prompt_path: Path,
    run_dir: Path,
    props: dict[str, str],
    queued_monotonic: float,
    queued_at: str,
    run_started_monotonic: float,
) -> PreparedCase:
    try:
        return prepare_case_result(
            index,
            total,
            case,
            target,
            prompt_path,
            run_dir,
            props,
            queued_monotonic,
            queued_at,
            run_started_monotonic,
        )
    finally:
        remove_workspace_git_metadata(run_dir / "workspace")


def finalize_case_result(prepared: PreparedCase, props: dict[str, str], judge_queue: JudgeQueue | None = None) -> tuple[int, dict[str, object]]:
    result = prepared.result
    needs_judge = bool(result.pop("_needs_judge", False))
    internal = result.pop("_performance_internal")
    judge_queue_seconds = 0.0
    judge_seconds = 0.0
    judge_started_at: str | None = None
    judge_finished_at: str | None = None
    judge_started_monotonic: float | None = None
    judge_finished_monotonic: float | None = None

    if needs_judge:
        if judge_queue is not None:
            judge_queue.start()
        judge_started = time.monotonic()
        judge_started_monotonic = judge_started
        judge_started_at = utc_now()
        judge_queue_seconds = max(0.0, judge_started - (prepared.judge_queued_monotonic or judge_started))
        judge = run_judge(prepared.case, result["evidence"], props)
        judge_finished_monotonic = time.monotonic()
        judge_seconds = judge_finished_monotonic - judge_started
        judge_finished_at = utc_now()
        if judge is None:
            judge = {
                "pass": False,
                "reason": "judge required by case but no judge output was captured",
                "llm_output": empty_judge_output(props.get("judge.model", "docker:ai/qwen3:8B-Q4_K_M")),
            }
        result["judge"] = judge
        passed = bool(result["pass"]) and bool(judge["pass"])
        result["pass"] = passed
        result["status"] = "pass" if passed else "fail"
        result["reason"] = "passed" if passed else "one or more checks failed"

    finished_monotonic = time.monotonic()
    finished_at = utc_now()
    result["performance"] = {
        "execution_type": internal["execution_type"],
        "timestamps": {
            "queued_at": prepared.queued_at,
            "started_at": prepared.started_at,
            "agent_started_at": internal["agent_started_at"],
            "agent_finished_at": internal["agent_finished_at"],
            "judge_started_at": judge_started_at,
            "judge_finished_at": judge_finished_at,
            "finished_at": finished_at,
        },
        "offsets_seconds": {
            "queued": round(prepared.queued_monotonic - prepared.run_started_monotonic, 6),
            "started": round(prepared.started_monotonic - prepared.run_started_monotonic, 6),
            "agent_started": (
                round(float(internal["agent_started_monotonic"]) - prepared.run_started_monotonic, 6)
                if internal["agent_started_monotonic"] is not None else None
            ),
            "agent_finished": (
                round(float(internal["agent_finished_monotonic"]) - prepared.run_started_monotonic, 6)
                if internal["agent_finished_monotonic"] is not None else None
            ),
            "judge_started": (
                round(judge_started_monotonic - prepared.run_started_monotonic, 6)
                if judge_started_monotonic is not None else None
            ),
            "judge_finished": (
                round(judge_finished_monotonic - prepared.run_started_monotonic, 6)
                if judge_finished_monotonic is not None else None
            ),
            "finished": round(finished_monotonic - prepared.run_started_monotonic, 6),
        },
        "durations_seconds": {
            "worker_queue": round(prepared.started_monotonic - prepared.queued_monotonic, 6),
            "setup": round(float(internal["setup_seconds"]), 6),
            "agent": round(float(internal["agent_seconds"]), 6),
            "deterministic_checks": round(float(internal["deterministic_seconds"]), 6),
            "judge_queue": round(judge_queue_seconds, 6),
            "judge": round(judge_seconds, 6),
            "service": round(
                float(internal["setup_seconds"])
                + float(internal["agent_seconds"])
                + float(internal["deterministic_seconds"])
                + judge_queue_seconds
                + judge_seconds,
                6,
            ),
            "total": round(finished_monotonic - prepared.queued_monotonic, 6),
        },
        "judge_queue_depth_at_submit": prepared.judge_queue_depth,
        "target_usage": result["evidence"].get("target_usage", unavailable_target_usage("unknown", "usage missing")),
        "response_length": text_size_metrics(str(result["evidence"].get("final_response", ""))),
        "agent_process": result["evidence"].get("process_metrics", unavailable_process_metrics("process metrics missing")),
    }
    result["performance"]["anomalies"] = performance_anomalies(result["performance"], props)
    print(f"[{prepared.index + 1}/{prepared.total}] Eval {prepared.case.id} finished: {result['status']}", file=sys.stderr, flush=True)
    for anomaly in result["performance"]["anomalies"]:
        print(f"[{prepared.index + 1}/{prepared.total}] Eval {prepared.case.id} warning: {anomaly['message']}", file=sys.stderr, flush=True)
    return prepared.index, result


def case_result(case: EvalCase, target: TargetConfig, prompt_path: Path, run_dir: Path, props: dict[str, str]) -> dict[str, object]:
    queued_monotonic = time.monotonic()
    prepared = prepare_case_result(0, 1, case, target, prompt_path, run_dir, props, queued_monotonic, utc_now(), queued_monotonic)
    if prepared.result.get("_needs_judge"):
        prepared.judge_queued_monotonic = time.monotonic()
    return finalize_case_result(prepared, props)[1]


def promotion_summary(
    target: TargetConfig,
    results: list[dict[str, object]],
    required_case_ids: list[str],
    artifact_validation: dict[str, object] | None = None,
) -> dict[str, object]:
    by_case = {str(result.get("case_id", "")): result for result in results}
    missing = [case_id for case_id in required_case_ids if case_id not in by_case]
    evaluated_required = [by_case[case_id] for case_id in required_case_ids if case_id in by_case]
    failed = [str(result.get("case_id", "")) for result in evaluated_required if result.get("status") != "not_evaluated" and not result.get("pass")]
    not_evaluated = [str(result.get("case_id", "")) for result in evaluated_required if result.get("status") == "not_evaluated"]
    target_available = target.status == "available"
    artifact_pass = bool(artifact_validation and artifact_validation.get("pass"))
    eligible = (
        target_available
        and bool(required_case_ids)
        and not missing
        and not failed
        and not not_evaluated
        and artifact_pass
    )
    if eligible:
        reason = "all required cases passed on target"
    elif not target_available:
        reason = target.reason or f"target status is {target.status}"
    elif not required_case_ids:
        reason = "no required cases configured"
    elif not artifact_pass:
        reason = "required prompt-artifact checks failed"
    else:
        reason = "required cases missing, failed, or not evaluated on target"
    return {
        "eligible": eligible,
        "reason": reason,
        "target": {
            "name": target.name,
            "harness": target.harness,
            "model": target.model,
            "reasoning": target.reasoning,
            "status": target.status,
            "planning": {
                "native_tool": target.planning_tool,
                "fallback": "durable_artifact",
            },
        },
        "required_total": len(required_case_ids),
        "required_evaluated": len(evaluated_required),
        "required_pass": sum(1 for result in evaluated_required if result.get("pass")),
        "missing_required_cases": missing,
        "failed_required_cases": failed,
        "not_evaluated_required_cases": not_evaluated,
        "artifact_validation_pass": artifact_pass,
    }


def percentile(values: list[float], percent: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * percent
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return round(ordered[lower], 6)
    interpolated = ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)
    return round(interpolated, 6)


def numeric_config(props: dict[str, str], key: str, default: float) -> float:
    raw = props.get(key, str(default))
    try:
        return float(raw)
    except (TypeError, ValueError):
        raise ValueError(f"{key} must be numeric: {raw}") from None


def anomaly_thresholds(props: dict[str, str]) -> dict[str, float]:
    return {
        "uncached_tokens": numeric_config(props, "metrics.anomalies.uncached_tokens", 15000),
        "requests": numeric_config(props, "metrics.anomalies.requests", 12),
        "agent_seconds": numeric_config(props, "metrics.anomalies.agent_seconds", 60),
    }


def uncached_token_count(usage: dict[str, object]) -> int | None:
    uncached = usage.get("uncached_tokens")
    if isinstance(uncached, (int, float)):
        return int(uncached)
    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    if isinstance(input_tokens, (int, float)) and isinstance(output_tokens, (int, float)):
        return int(input_tokens + output_tokens)
    return None


def performance_anomalies(performance: dict[str, object], props: dict[str, str]) -> list[dict[str, object]]:
    if props.get("metrics.anomalies.enabled", "true").lower() not in {"1", "true", "yes"}:
        return []
    thresholds = anomaly_thresholds(props)
    usage = performance.get("target_usage", {})
    durations = performance.get("durations_seconds", {})
    values = {
        "uncached_tokens": uncached_token_count(usage) if isinstance(usage, dict) else None,
        "requests": usage.get("requests") if isinstance(usage, dict) else None,
        "agent_seconds": durations.get("agent") if isinstance(durations, dict) else None,
    }
    labels = {
        "uncached_tokens": "target uncached input and output tokens",
        "requests": "model requests",
        "agent_seconds": "agent execution seconds",
    }
    anomalies: list[dict[str, object]] = []
    for metric, value in values.items():
        threshold = thresholds[metric]
        if isinstance(value, (int, float)) and value > threshold:
            anomalies.append({
                "metric": metric,
                "value": value,
                "threshold": threshold,
                "message": f"{labels[metric]} {value} exceeded warning threshold {threshold:g}",
            })
    return anomalies


def parse_timestamp(value: object) -> float | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return dt.datetime.fromisoformat(value).timestamp()
    except ValueError:
        return None


def interval_stats(intervals: list[tuple[float, float]]) -> tuple[float, float, int]:
    valid = [(start, end) for start, end in intervals if end >= start]
    if not valid:
        return 0.0, 0.0, 0
    span = max(end for _, end in valid) - min(start for start, _ in valid)
    busy = sum(end - start for start, end in valid)
    events = sorted([(start, 1) for start, _ in valid] + [(end, -1) for _, end in valid], key=lambda item: (item[0], item[1]))
    active = 0
    peak = 0
    for _, delta in events:
        active += delta
        peak = max(peak, active)
    return span, busy, peak


def aggregate_performance(
    results: list[dict[str, object]],
    jobs: int,
    wall_seconds: float | None,
    peak_judge_queue: int = 0,
    *,
    scope: str = "invocation",
) -> dict[str, object]:
    total_durations: list[float] = []
    service_durations: list[float] = []
    worker_queue_durations: list[float] = []
    agent_durations: list[float] = []
    judge_durations: list[float] = []
    judge_queue_durations: list[float] = []
    agent_intervals: list[tuple[float, float]] = []
    judge_intervals: list[tuple[float, float]] = []
    token_totals: dict[str, int] = {
        "input_tokens": 0,
        "output_tokens": 0,
        "reasoning_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "total_tokens": 0,
        "uncached_tokens": 0,
    }
    token_field_counts = {field: 0 for field in token_totals}
    token_case_count = 0
    total_cost = 0.0
    cost_case_count = 0
    slowest: list[dict[str, object]] = []
    highest_tokens: list[dict[str, object]] = []
    response_bytes: list[float] = []
    response_words: list[float] = []
    response_estimated_tokens: list[float] = []
    highest_response_tokens: list[dict[str, object]] = []
    process_case_count = 0
    process_peak_rss = 0
    process_peak_count = 0
    process_cpu_user = 0.0
    process_cpu_system = 0.0
    process_read_bytes = 0
    process_write_bytes = 0
    anomaly_cases: list[dict[str, object]] = []
    cumulative_service_seconds = 0.0

    for result in results:
        performance = result.get("performance", {})
        if not isinstance(performance, dict):
            continue
        durations = performance.get("durations_seconds", {})
        timestamps = performance.get("timestamps", {})
        offsets = performance.get("offsets_seconds", {})
        usage = performance.get("target_usage", {})
        if isinstance(durations, dict):
            total = durations.get("total")
            service = durations.get("service")
            worker_queue = durations.get("worker_queue")
            agent = durations.get("agent")
            judge = durations.get("judge")
            judge_queue = durations.get("judge_queue")
            if isinstance(total, (int, float)):
                total_durations.append(float(total))
            if not isinstance(service, (int, float)) and isinstance(total, (int, float)) and isinstance(worker_queue, (int, float)):
                service = float(total) - float(worker_queue)
            if isinstance(service, (int, float)):
                service_durations.append(float(service))
                cumulative_service_seconds += float(service)
                slowest.append({"case_id": result.get("case_id"), "service_seconds": round(float(service), 6)})
            if isinstance(worker_queue, (int, float)):
                worker_queue_durations.append(float(worker_queue))
            if isinstance(agent, (int, float)) and agent > 0:
                agent_durations.append(float(agent))
            if isinstance(judge, (int, float)) and judge > 0:
                judge_durations.append(float(judge))
            if isinstance(judge_queue, (int, float)):
                judge_queue_durations.append(float(judge_queue))
        if isinstance(offsets, dict) and any(offsets.get(key) is not None for key in ["agent_started", "agent_finished", "judge_started", "judge_finished"]):
            agent_start = offsets.get("agent_started")
            agent_end = offsets.get("agent_finished")
            judge_start = offsets.get("judge_started")
            judge_end = offsets.get("judge_finished")
            agent_start = float(agent_start) if isinstance(agent_start, (int, float)) else None
            agent_end = float(agent_end) if isinstance(agent_end, (int, float)) else None
            judge_start = float(judge_start) if isinstance(judge_start, (int, float)) else None
            judge_end = float(judge_end) if isinstance(judge_end, (int, float)) else None
        elif isinstance(timestamps, dict):
            agent_start = parse_timestamp(timestamps.get("agent_started_at"))
            agent_end = parse_timestamp(timestamps.get("agent_finished_at"))
            judge_start = parse_timestamp(timestamps.get("judge_started_at"))
            judge_end = parse_timestamp(timestamps.get("judge_finished_at"))
        else:
            agent_start = agent_end = judge_start = judge_end = None
        if agent_start is not None and agent_end is not None:
            agent_intervals.append((agent_start, agent_end))
        if judge_start is not None and judge_end is not None:
            judge_intervals.append((judge_start, judge_end))
        if isinstance(usage, dict) and usage.get("available"):
            token_case_count += 1
            for field in token_totals:
                value = uncached_token_count(usage) if field == "uncached_tokens" else usage.get(field)
                if isinstance(value, (int, float)):
                    token_totals[field] += int(value)
                    token_field_counts[field] += 1
            case_tokens = usage.get("total_tokens")
            if isinstance(case_tokens, (int, float)):
                highest_tokens.append({"case_id": result.get("case_id"), "total_tokens": int(case_tokens)})
            cost = usage.get("cost")
            if isinstance(cost, (int, float)):
                total_cost += float(cost)
                cost_case_count += 1
        response = performance.get("response_length")
        if not isinstance(response, dict):
            evidence = result.get("evidence", {})
            response = text_size_metrics(str(evidence.get("final_response", ""))) if isinstance(evidence, dict) else text_size_metrics("")
        byte_count = response.get("bytes")
        word_count = response.get("words")
        estimated_tokens = response.get("estimated_tokens")
        if isinstance(byte_count, (int, float)):
            response_bytes.append(float(byte_count))
        if isinstance(word_count, (int, float)):
            response_words.append(float(word_count))
        if isinstance(estimated_tokens, (int, float)):
            response_estimated_tokens.append(float(estimated_tokens))
            highest_response_tokens.append({
                "case_id": result.get("case_id"),
                "estimated_tokens": int(estimated_tokens),
            })
        process = performance.get("agent_process", {})
        if isinstance(process, dict) and process.get("available"):
            process_case_count += 1
            peak_rss = process.get("peak_rss_bytes")
            peak_count = process.get("peak_process_count")
            cpu_user = process.get("cpu_user_seconds")
            cpu_system = process.get("cpu_system_seconds")
            read_bytes = process.get("read_bytes")
            write_bytes = process.get("write_bytes")
            if isinstance(peak_rss, (int, float)):
                process_peak_rss = max(process_peak_rss, int(peak_rss))
            if isinstance(peak_count, (int, float)):
                process_peak_count = max(process_peak_count, int(peak_count))
            if isinstance(cpu_user, (int, float)):
                process_cpu_user += float(cpu_user)
            if isinstance(cpu_system, (int, float)):
                process_cpu_system += float(cpu_system)
            if isinstance(read_bytes, (int, float)):
                process_read_bytes += int(read_bytes)
            if isinstance(write_bytes, (int, float)):
                process_write_bytes += int(write_bytes)
        anomalies = performance.get("anomalies", [])
        if isinstance(anomalies, list) and anomalies:
            anomaly_cases.append({"case_id": result.get("case_id"), "warnings": anomalies})

    agent_span, agent_busy, peak_agents = interval_stats(agent_intervals)
    judge_span, judge_busy, peak_judges = interval_stats(judge_intervals)
    invocation_scope = scope == "invocation"
    return {
        "scope": scope,
        "source_case_count": len(results),
        "cumulative_service_seconds": round(cumulative_service_seconds, 6),
        "wall_seconds": round(wall_seconds, 6) if wall_seconds is not None else None,
        "throughput_cases_per_second": round(len(results) / wall_seconds, 6) if wall_seconds is not None and wall_seconds > 0 else None,
        "configured_agent_jobs": jobs if scope == "invocation" else None,
        "case_latency_seconds": {
            "end_to_end": {
                "p50": percentile(total_durations, 0.50),
                "p90": percentile(total_durations, 0.90),
                "p95": percentile(total_durations, 0.95),
                "max": round(max(total_durations), 6) if total_durations else None,
            },
            "service": {
                "p50": percentile(service_durations, 0.50),
                "p90": percentile(service_durations, 0.90),
                "p95": percentile(service_durations, 0.95),
                "max": round(max(service_durations), 6) if service_durations else None,
            },
            "worker_queue": {
                "p50": percentile(worker_queue_durations, 0.50),
                "p90": percentile(worker_queue_durations, 0.90),
                "p95": percentile(worker_queue_durations, 0.95),
                "max": round(max(worker_queue_durations), 6) if worker_queue_durations else None,
            },
        },
        "agent_parallelism": {
            "cases": len(agent_durations),
            "wall_span_seconds": round(agent_span, 6) if invocation_scope else None,
            "busy_seconds": round(agent_busy, 6),
            "peak_concurrency": peak_agents if invocation_scope else None,
            "average_concurrency": round(agent_busy / agent_span, 6) if invocation_scope and agent_span > 0 else None,
            "worker_utilization": round(agent_busy / (jobs * agent_span), 6) if invocation_scope and agent_span > 0 else None,
            "effective_speedup": round(agent_busy / agent_span, 6) if invocation_scope and agent_span > 0 else None,
            "parallel_efficiency": round(agent_busy / (jobs * agent_span), 6) if invocation_scope and agent_span > 0 else None,
        },
        "judge": {
            "cases": len(judge_durations),
            "wall_span_seconds": round(judge_span, 6) if invocation_scope else None,
            "busy_seconds": round(judge_busy, 6),
            "peak_concurrency": peak_judges if invocation_scope else None,
            "utilization_within_span": round(judge_busy / judge_span, 6) if invocation_scope and judge_span > 0 else None,
            "peak_queue_depth": peak_judge_queue if invocation_scope else None,
            "queue_wait_seconds": {
                "p50": percentile(judge_queue_durations, 0.50),
                "p90": percentile(judge_queue_durations, 0.90),
                "p95": percentile(judge_queue_durations, 0.95),
                "max": round(max(judge_queue_durations), 6) if judge_queue_durations else None,
            },
        },
        "target_usage": {
            "available_cases": token_case_count,
            "unavailable_cases": len(results) - token_case_count,
            **{
                field: token_totals[field] if token_field_counts[field] else None
                for field in token_totals
            },
            "field_available_cases": token_field_counts,
            "cost": round(total_cost, 10) if cost_case_count else None,
        },
        "response_length": {
            "cases": len(response_estimated_tokens),
            "bytes": {
                "total": int(sum(response_bytes)),
                "p50": percentile(response_bytes, 0.50),
                "p90": percentile(response_bytes, 0.90),
                "max": int(max(response_bytes)) if response_bytes else None,
            },
            "words": {
                "total": int(sum(response_words)),
                "p50": percentile(response_words, 0.50),
                "p90": percentile(response_words, 0.90),
                "max": int(max(response_words)) if response_words else None,
            },
            "estimated_tokens": {
                "total": int(sum(response_estimated_tokens)),
                "p50": percentile(response_estimated_tokens, 0.50),
                "p90": percentile(response_estimated_tokens, 0.90),
                "max": int(max(response_estimated_tokens)) if response_estimated_tokens else None,
                "method": "unicode_words_and_punctuation",
            },
        },
        "agent_process": {
            "available_cases": process_case_count,
            "peak_rss_bytes": process_peak_rss if process_case_count else None,
            "peak_process_count": process_peak_count if process_case_count else None,
            "cpu_user_seconds": round(process_cpu_user, 6) if process_case_count else None,
            "cpu_system_seconds": round(process_cpu_system, 6) if process_case_count else None,
            "read_bytes": process_read_bytes if process_case_count else None,
            "write_bytes": process_write_bytes if process_case_count else None,
        },
        "slowest_cases": sorted(slowest, key=lambda item: float(item["service_seconds"]), reverse=True)[:10],
        "highest_token_cases": sorted(highest_tokens, key=lambda item: int(item["total_tokens"]), reverse=True)[:10],
        "highest_response_token_cases": sorted(
            highest_response_tokens,
            key=lambda item: int(item["estimated_tokens"]),
            reverse=True,
        )[:10],
        "anomalies": {
            "case_count": len(anomaly_cases),
            "cases": anomaly_cases,
        },
    }


def aggregate_planning(results: list[dict[str, object]], target: TargetConfig) -> dict[str, object]:
    native_cases: list[str] = []
    artifact_cases: list[str] = []
    native_snapshots = 0
    completed_lifecycles = 0

    for result in results:
        case_id = str(result.get("case_id", ""))
        evidence = result.get("evidence", {})
        actions = evidence.get("durable_context_actions", []) if isinstance(evidence, dict) else []
        actions = [action for action in actions if isinstance(action, dict)]
        native = [action for action in actions if action.get("kind") == "native_plan_snapshot"]
        artifacts = [
            action for action in actions
            if action.get("mechanism") == "file" and action.get("kind") in {"artifact_create", "artifact_update"}
        ]
        if native:
            native_cases.append(case_id)
            native_snapshots += len(native)
            final_todos = native[-1].get("todos", [])
            if (
                isinstance(final_todos, list)
                and final_todos
                and all(
                    isinstance(todo, dict) and todo.get("status") in {"completed", "cancelled"}
                    for todo in final_todos
                )
            ):
                completed_lifecycles += 1
        if artifacts:
            artifact_cases.append(case_id)

    return {
        "capability": {
            "native_tool": target.planning_tool,
            "fallback": "durable_artifact",
        },
        "native_planning": {
            "case_count": len(native_cases),
            "case_ids": native_cases,
            "snapshot_count": native_snapshots,
            "completed_lifecycle_count": completed_lifecycles,
        },
        "artifact_planning": {
            "case_count": len(artifact_cases),
            "case_ids": artifact_cases,
        },
    }


def build_report(
    config_path: Path,
    prompt_path: Path,
    target: TargetConfig,
    props: dict[str, str],
    results: list[dict[str, object]],
    required_case_ids: list[str] | None = None,
    performance: dict[str, object] | None = None,
    run_status: str = "completed",
    selected_total: int | None = None,
    run_id: str = "standalone",
    selected_case_ids: list[str] | None = None,
) -> dict[str, object]:
    pass_count = sum(1 for result in results if result["pass"])
    not_evaluated = sum(1 for result in results if result["status"] == "not_evaluated")
    required_case_ids = required_case_ids or []
    performance_data = performance or aggregate_performance(results, 1, 0.0)
    anomalies = performance_data.setdefault("anomalies", {"case_count": 0, "cases": []})
    if isinstance(anomalies, dict):
        anomalies["enabled"] = props.get("metrics.anomalies.enabled", "true").lower() in {"1", "true", "yes"}
        anomalies["thresholds"] = anomaly_thresholds(props)
    artifact_validation = prompt_artifact_validation(prompt_path)
    return {
        "schema": "prompt-behavior-eval-report/v6",
        "created_at": dt.datetime.now(dt.UTC).isoformat(),
        "config_path": str(config_path),
        "prompt": {
            "path": str(prompt_path),
            "sha256": file_digest(prompt_path),
            "metrics": prompt_size_metrics(prompt_path),
        },
        "target": {
            "name": target.name,
            "harness": target.harness,
            "model": target.model,
            "reasoning": target.reasoning,
            "auth": target.auth,
            "status": target.status,
            "reason": target.reason,
            "planning": {
                "native_tool": target.planning_tool,
                "fallback": "durable_artifact",
            },
        },
        "judge": {
            "enabled": props.get("judge.enabled", "true"),
            "backend": props.get("judge.backend", "docker-model-runner"),
            "model": props.get("judge.model", "docker:ai/qwen3:8B-Q4_K_M"),
            "timeout_seconds": positive_int_config(props, "judge.timeout.seconds", 120),
            "retry_attempts": positive_int_config(props, "judge.retry.attempts", 3),
            "retry_backoff_seconds": numeric_config(props, "judge.retry.backoff_seconds", 1),
        },
        "summary": {
            "total": len(results),
            "pass": pass_count,
            "fail": len(results) - pass_count - not_evaluated,
            "not_evaluated": not_evaluated,
        },
        "run": {
            "id": run_id,
            "status": run_status,
            "selected_total": selected_total if selected_total is not None else len(results),
            "completed_total": len(results),
            "selected_case_ids": selected_case_ids or [str(result.get("case_id", "")) for result in results],
            "pending_case_ids": [],
        },
        "artifact_validation": artifact_validation,
        "performance": performance_data,
        "planning": aggregate_planning(results, target),
        "promotion": promotion_summary(
            target,
            results,
            required_case_ids,
            artifact_validation=artifact_validation,
        ),
        "results": results,
    }


def write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(content)
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def write_json_atomic(path: Path, value: object) -> None:
    write_text_atomic(path, json.dumps(value, indent=2) + "\n")


def _repo_root_for_report() -> Path:
    return Path(__file__).resolve().parents[2]


def _sanitize_string(value: str, repo_root: Path, home: Path) -> str:
    sanitized = value
    replacements: list[tuple[str, str]] = []
    try:
        replacements.append((str(repo_root.resolve()), "."))
    except OSError:
        replacements.append((str(repo_root), "."))
    try:
        replacements.append((str(home.resolve()), "<home>"))
    except OSError:
        replacements.append((str(home), "<home>"))
    for source, target in replacements:
        if source:
            sanitized = sanitized.replace(source, target)
    return sanitized


def sanitize_public_report(value: object, repo_root: Path | None = None, home: Path | None = None) -> object:
    repo_root = repo_root or _repo_root_for_report()
    home = home or Path.home()
    sensitive_file_names = {"auth.json", "account.json"}

    def sanitize(node: object, key: str | None = None) -> object:
        if isinstance(node, dict):
            sanitized: dict[str, object] = {}
            for item_key, item_value in node.items():
                if item_key == "copied" and isinstance(item_value, list):
                    sanitized[item_key] = [
                        "<auth-data>" if item in sensitive_file_names else sanitize(item, item_key)
                        for item in item_value
                    ]
                else:
                    sanitized[item_key] = sanitize(item_value, item_key)
            return sanitized
        if isinstance(node, list):
            return [sanitize(item, key) for item in node]
        if isinstance(node, str):
            if key == "source" and ".local/share/opencode" in node:
                return "<home>/.local/share/opencode"
            return _sanitize_string(node, repo_root, home)
        return node

    return sanitize(value)


def report_html(report: dict[str, object]) -> str:
    if REPORT_EMBED_MARKER not in REPORT_VIEWER_HTML:
        raise ValueError("report viewer template missing embed marker")
    embedded = json.dumps(report, separators=(",", ":")).replace("</", "<\\/")
    return REPORT_VIEWER_HTML.replace(REPORT_EMBED_MARKER, f"window.__PROMPT_EVAL_REPORT__ = {embedded};", 1)


def write_report_files(report_path: Path, report: dict[str, object], *, public: bool = False) -> None:
    output_report = sanitize_public_report(report) if public else report
    write_json_atomic(report_path, output_report)
    write_text_atomic(report_path.with_suffix(".html"), report_html(output_report))


def write_case_report(
    report_path: Path,
    config_path: Path,
    prompt_path: Path,
    target: TargetConfig,
    props: dict[str, str],
    results: list[dict[str, object]],
    required_case_ids: list[str] | None = None,
    run_id: str = "standalone",
) -> None:
    report = build_report(
        config_path,
        prompt_path,
        target,
        props,
        results,
        required_case_ids,
        run_id=run_id,
    )
    write_report_files(report_path, report)


def result_counts(results: list[dict[str, object]]) -> dict[str, int]:
    not_evaluated = sum(1 for result in results if result.get("status") == "not_evaluated")
    passed = sum(1 for result in results if result.get("pass"))
    return {
        "total": len(results),
        "pass": passed,
        "fail": len(results) - passed - not_evaluated,
        "not_evaluated": not_evaluated,
    }


def build_root_report(
    config_path: Path,
    prompt_path: Path,
    target: TargetConfig,
    props: dict[str, str],
    all_cases: list[EvalCase],
    reports_dir: Path,
    run_id: str,
    selected_case_ids: list[str],
    completed_selected_case_ids: list[str],
    run_status: str,
    performance: dict[str, object],
    confirmation: dict[str, object] | None = None,
) -> dict[str, object]:
    current: list[dict[str, object]] = []
    stale: list[dict[str, object]] = []
    missing: list[str] = []

    for case in all_cases:
        path = case_report_dir(reports_dir, target, case) / "report.json"
        if not path.exists():
            missing.append(case.id)
            continue
        try:
            case_report = json.loads(path.read_text(encoding="utf-8"))
            result = dict(case_report["results"][0])
        except (OSError, ValueError, KeyError, IndexError, TypeError):
            missing.append(case.id)
            continue
        case_prompt_sha = case_report.get("prompt", {}).get("sha256")
        state = "current" if case_prompt_sha == run_id else "stale"
        result["report_state"] = state
        result["report_run_id"] = case_prompt_sha
        if state == "stale":
            result["stale_reason"] = "prompt_hash_mismatch"
        if state == "current":
            current.append(result)
        else:
            stale.append(result)

    completed_selected = set(completed_selected_case_ids)
    pending = [case_id for case_id in selected_case_ids if case_id not in completed_selected] if run_status == "in_progress" else []
    accumulated_performance = aggregate_performance(
        current,
        jobs=1,
        wall_seconds=None,
        scope="accumulated_current_cases",
    )
    report = build_report(
        config_path,
        prompt_path,
        target,
        props,
        current,
        [case.id for case in all_cases],
        performance=accumulated_performance,
        run_status=run_status,
        selected_total=len(selected_case_ids),
        run_id=run_id,
        selected_case_ids=selected_case_ids,
    )
    report["results"] = current + stale
    report["summary"] = {
        **result_counts(current),
        "current": result_counts(current),
        "stale": result_counts(stale),
        "pending": len(pending),
        "missing": len(missing),
        "available_total": len(current) + len(stale),
        "required_total": len(all_cases),
    }
    report["run"]["completed_total"] = len(completed_selected)
    report["run"]["pending_case_ids"] = pending
    latest_invocation_performance = dict(performance)
    latest_invocation_performance.setdefault("scope", "invocation")
    latest_invocation_performance.setdefault("source_case_count", len(completed_selected))
    report["run"]["latest_invocation_performance"] = latest_invocation_performance
    report["coverage"] = {
        "current_case_ids": [str(result.get("case_id", "")) for result in current],
        "stale_case_ids": [str(result.get("case_id", "")) for result in stale],
        "missing_case_ids": missing,
    }
    if confirmation is not None:
        report["confirmation"] = confirmation
    return report


def target_setting(props: dict[str, str], target: TargetConfig, key: str) -> str | None:
    return props.get(f"targets.{target.name}.{key}")


def apply_target_runtime(props: dict[str, str], target: TargetConfig, cli_options: dict[str, str | bool | None]) -> None:
    target_timeout = target_setting(props, target, "agent.timeout.seconds")
    if target_timeout not in (None, ""):
        props["agent.timeout.seconds"] = str(target_timeout)
    if cli_options.get("agent_timeout_seconds") not in (None, ""):
        props["agent.timeout.seconds"] = str(cli_options["agent_timeout_seconds"])


def eval_jobs(props: dict[str, str], cli_options: dict[str, str | bool | None], target: TargetConfig) -> int:
    raw = cli_options.get("jobs") or target_setting(props, target, "eval.jobs") or props.get("eval.jobs", "1")
    try:
        return max(1, int(str(raw)))
    except ValueError:
        raise ValueError(f"jobs must be an integer: {raw}") from None


def confirmation_attempts(cli_options: dict[str, str | bool | None]) -> int:
    raw = cli_options.get("confirm_failures") or "0"
    try:
        return max(0, int(str(raw)))
    except ValueError:
        raise ValueError(f"confirm-failures must be an integer: {raw}") from None


def failed_case_ids(results: list[dict[str, object]]) -> list[str]:
    return [
        str(result.get("case_id", ""))
        for result in results
        if result.get("status") != "not_evaluated" and not result.get("pass")
    ]


def run_cases(
    cases: list[EvalCase],
    target: TargetConfig,
    prompt_path: Path,
    reports_dir: Path,
    props: dict[str, str],
    jobs: int,
    on_result: Callable[[int, dict[str, object], list[dict[str, object]], float, int], None] | None = None,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    results: list[dict[str, object] | None] = [None] * len(cases)
    judge_queue = JudgeQueue()
    judge_futures = []
    run_started = time.monotonic()
    results_lock = threading.Lock()

    def store_result(result_index: int, result: dict[str, object]) -> None:
        with results_lock:
            results[result_index] = result
            finalized = [item for item in results if item is not None]
        if on_result is not None:
            on_result(
                result_index,
                result,
                finalized,
                time.monotonic() - run_started,
                max(0, judge_queue.peak_pending - 1),
            )

    def store_completed_future(future) -> None:
        result_index, result = future.result()
        store_result(result_index, result)

    start_index = 0
    if target.harness.lower() == "opencode" and jobs > 1 and len(cases) > 1:
        queued_monotonic = time.monotonic()
        queued_at = utc_now()
        prepared = prepare_case_result_without_persisted_git(
            0,
            len(cases),
            cases[0],
            target,
            prompt_path,
            case_report_dir(reports_dir, target, cases[0]),
            props,
            queued_monotonic,
            queued_at,
            run_started,
        )
        result_index, result = finalize_case_result(prepared, props)
        store_result(result_index, result)
        start_index = 1

    with ThreadPoolExecutor(max_workers=jobs) as agent_executor, ThreadPoolExecutor(max_workers=1) as judge_executor:
        agent_futures = []
        for index, case in enumerate(cases[start_index:], start=start_index):
            queued_monotonic = time.monotonic()
            queued_at = utc_now()
            agent_futures.append(agent_executor.submit(
                prepare_case_result_without_persisted_git,
                index,
                len(cases),
                case,
                target,
                prompt_path,
                case_report_dir(reports_dir, target, case),
                props,
                queued_monotonic,
                queued_at,
                run_started,
            ))
        for future in as_completed(agent_futures):
            prepared = future.result()
            if prepared.result.get("_needs_judge"):
                prepared.judge_queued_monotonic = time.monotonic()
                prepared.judge_queue_depth = judge_queue.submit()
                judge_future = judge_executor.submit(finalize_case_result, prepared, props, judge_queue)
                judge_future.add_done_callback(store_completed_future)
                judge_futures.append(judge_future)
            else:
                result_index, result = finalize_case_result(prepared, props)
                store_result(result_index, result)
        for future in as_completed(judge_futures):
            future.result()
    run_wall_seconds = time.monotonic() - run_started
    with results_lock:
        finalized = [result for result in results if result is not None]
    return finalized, aggregate_performance(finalized, jobs, run_wall_seconds, max(0, judge_queue.peak_pending - 1))


def confirmation_report(
    *,
    enabled_attempts: int,
    primary_results: list[dict[str, object]],
    runs: list[dict[str, object]],
) -> dict[str, object]:
    primary_failed = failed_case_ids(primary_results)
    remaining_failed = list(primary_failed)
    if runs:
        remaining_failed = list(runs[-1]["failed_case_ids"])
    recovered = [case_id for case_id in primary_failed if case_id not in remaining_failed]
    return {
        "enabled": enabled_attempts > 0,
        "max_attempts": enabled_attempts,
        "primary": {
            "summary": result_counts(primary_results),
            "failed_case_ids": primary_failed,
        },
        "runs": runs,
        "flaky_pass_after_retry": recovered,
        "confirmed_failed_case_ids": remaining_failed,
        "confirmed_fail": len(remaining_failed),
    }


def confirm_failed_cases(
    *,
    failed_ids: list[str],
    cases_by_id: dict[str, EvalCase],
    target: TargetConfig,
    prompt_path: Path,
    reports_dir: Path,
    config_path: Path,
    props: dict[str, str],
    required_case_ids: list[str],
    run_id: str,
    attempts: int,
    jobs: int,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    remaining = list(failed_ids)
    runs: list[dict[str, object]] = []
    final_results: list[dict[str, object]] = []
    for attempt in range(1, attempts + 1):
        if not remaining:
            break
        confirmation_cases = [cases_by_id[case_id] for case_id in remaining if case_id in cases_by_id]
        if not confirmation_cases:
            break
        print(
            f"Confirming {len(confirmation_cases)} failed eval(s), attempt {attempt}/{attempts}: {', '.join(case.id for case in confirmation_cases)}",
            file=sys.stderr,
            flush=True,
        )
        results, performance = run_cases(
            confirmation_cases,
            target,
            prompt_path,
            reports_dir,
            props,
            jobs,
        )
        for result in results:
            case_id = str(result.get("case_id", ""))
            case = cases_by_id[case_id]
            write_case_report(
                case_report_dir(reports_dir, target, case) / "report.json",
                config_path,
                prompt_path,
                target,
                props,
                [result],
                required_case_ids,
                run_id,
            )
        failed = failed_case_ids(results)
        passed = [str(result.get("case_id", "")) for result in results if result.get("pass")]
        runs.append({
            "attempt": attempt,
            "case_ids": [case.id for case in confirmation_cases],
            "summary": result_counts(results),
            "failed_case_ids": failed,
            "passed_case_ids": passed,
            "performance": performance,
        })
        final_results = results
        remaining = failed
    return runs, final_results


def run_evals(config_path: Path, cli_options: dict[str, str | bool | None]) -> dict[str, object]:
    config_path = normalize_runner_path(config_path)
    props = load_config(config_path)
    all_cases = load_cases(Path("evals/cases"))
    required_case_ids = [case.id for case in all_cases]
    cases = select_cases(all_cases, props, cli_options)
    if not cases:
        raise ValueError("no agent behavior eval cases matched the selection")
    missing_fixtures = missing_required_fixtures(cases)
    if missing_fixtures:
        raise ValueError(f"required eval fixture missing: {', '.join(missing_fixtures)}")
    report_dir_option = Path(str(cli_options.get("reports_dir") or props.get("reports.dir") or "evals/reports"))
    reports_dir = normalize_runner_path(report_dir_option)
    target = build_target(props, cli_options)
    apply_target_runtime(props, target, cli_options)
    prompt_path = normalize_runner_path(Path(str(cli_options.get("prompt") or props.get("prompt.candidate") or "PROMPT.md")))
    jobs = eval_jobs(props, cli_options, target)
    confirm_attempts = confirmation_attempts(cli_options)
    target_reports_dir = target_report_dir(reports_dir, target)
    aggregate_report_path = target_reports_dir / "report.json"
    run_id = file_digest(prompt_path)
    if run_id is None:
        raise ValueError(f"prompt artifact does not exist: {prompt_path}")
    selected_case_ids = [case.id for case in cases]
    cases_by_id = {case.id: case for case in all_cases}

    def persist_result(
        result_index: int,
        result: dict[str, object],
        finalized: list[dict[str, object]],
        wall_seconds: float,
        peak_judge_queue: int,
    ) -> None:
        case = cases[result_index]
        write_case_report(
            case_report_dir(reports_dir, target, case) / "report.json",
            config_path,
            prompt_path,
            target,
            props,
            [result],
            required_case_ids,
            run_id,
        )
        partial_performance = aggregate_performance(finalized, jobs, wall_seconds, peak_judge_queue)
        partial_report = build_root_report(
            config_path,
            prompt_path,
            target,
            props,
            all_cases,
            reports_dir,
            run_id,
            selected_case_ids,
            [str(item.get("case_id", "")) for item in finalized],
            "in_progress",
            partial_performance,
        )
        write_report_files(aggregate_report_path, partial_report, public=True)

    results, performance = run_cases(
        cases,
        target,
        prompt_path,
        reports_dir,
        props,
        jobs,
        on_result=persist_result,
    )
    primary_results = [dict(result) for result in results]
    primary_failed_ids = failed_case_ids(primary_results)
    confirmation_runs: list[dict[str, object]] = []
    if confirm_attempts and primary_failed_ids:
        confirmation_runs, _ = confirm_failed_cases(
            failed_ids=primary_failed_ids,
            cases_by_id=cases_by_id,
            target=target,
            prompt_path=prompt_path,
            reports_dir=reports_dir,
            config_path=config_path,
            props=props,
            required_case_ids=required_case_ids,
            run_id=run_id,
            attempts=confirm_attempts,
            jobs=jobs,
        )
    confirmation = confirmation_report(
        enabled_attempts=confirm_attempts,
        primary_results=primary_results,
        runs=confirmation_runs,
    ) if confirm_attempts else None
    report = build_root_report(
        config_path,
        prompt_path,
        target,
        props,
        all_cases,
        reports_dir,
        run_id,
        selected_case_ids,
        selected_case_ids,
        "completed",
        performance,
        confirmation=confirmation,
    )

    report_path = aggregate_report_path
    write_report_files(report_path, report, public=True)
    display_target_dir = target_report_dir(report_dir_option, target)
    display_report_path = display_target_dir / "report.json"
    report["report_path"] = str(display_report_path)
    report["case_report_paths"] = [
        str(case_report_dir(report_dir_option, target, case) / "report.json")
        for case in cases
    ]
    return report


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run prompt behavior eval cases")
    parser.add_argument("--config", default="evals/eval.yaml")
    parser.add_argument("--case", dest="case")
    parser.add_argument("--category")
    parser.add_argument("--tag")
    parser.add_argument("--path")
    parser.add_argument("--critical")
    parser.add_argument("--prompt")
    parser.add_argument("--target-name")
    parser.add_argument("--target-harness")
    parser.add_argument("--target-model")
    parser.add_argument("--target-auth")
    parser.add_argument("--target-reasoning")
    parser.add_argument("--reports-dir")
    parser.add_argument("--agent-timeout-seconds")
    parser.add_argument("--jobs")
    parser.add_argument("--confirm-failures")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    report = run_evals(Path(args.config), vars(args))
    print(json.dumps({
        "report_path": report["report_path"],
        "summary": report["summary"],
        "target": report["target"],
    }, indent=2))
    summary = report["summary"]
    promotion = report.get("promotion", {})
    failed = bool(summary.get("fail") or summary.get("not_evaluated") or summary.get("pending") or summary.get("missing"))
    if promotion and not promotion.get("eligible", False):
        failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

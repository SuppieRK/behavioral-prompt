from __future__ import annotations

import difflib
import json
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from .core import HarnessContractError

IGNORED_NAMES = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".coverage", "coverage.xml", ".DS_Store"}
DIRTY_STATE_METADATA = Path(".eval/dirty-state.json")


@dataclass(frozen=True)
class Workspace:
    path: Path
    temp_root: Path
    fixture: str | None
    keep: bool = False

    def cleanup(self) -> None:
        if not self.keep and self.temp_root.exists():
            _remove_tree_with_retries(self.temp_root)


def create_workspace(*, fixture_name: str | None, fixtures_dir: Path, keep: bool = False) -> Workspace:
    temp_root = Path(tempfile.mkdtemp(prefix="prompt-eval-"))
    workspace = temp_root / "workspace"
    workspace.mkdir()
    if fixture_name:
        fixture = fixtures_dir / fixture_name
        if not fixture.is_dir():
            raise HarnessContractError(f"fixture not found: {fixture}")
        shutil.copytree(fixture, workspace, dirs_exist_ok=True, symlinks=True)
    dirty_states = _prepare_dirty_state_baseline(workspace)
    initialize_git_baseline(workspace)
    _restore_dirty_state(workspace, dirty_states)
    return Workspace(path=workspace, temp_root=temp_root, fixture=fixture_name, keep=keep)


def _prepare_dirty_state_baseline(workspace: Path) -> tuple[tuple[str, str], ...]:
    metadata = workspace / DIRTY_STATE_METADATA
    if not metadata.exists():
        return ()
    try:
        data = json.loads(metadata.read_text())
    except json.JSONDecodeError as exc:
        raise HarnessContractError(f"invalid dirty-state metadata: {exc}") from exc
    entries = data if isinstance(data, list) else [data]
    dirty_states = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise HarnessContractError("dirty-state metadata entries must be objects")
        path = str(entry.get("path", "")).strip()
        baseline_content = entry.get("baseline_content")
        dirty_content = entry.get("dirty_content")
        if not path or not isinstance(baseline_content, str) or not isinstance(dirty_content, str):
            raise HarnessContractError("dirty-state metadata requires path, baseline_content, and dirty_content")
        target = _dirty_state_target(workspace, path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(baseline_content)
        dirty_states.append((path, dirty_content))
    shutil.rmtree(workspace / ".eval")
    return tuple(dirty_states)


def _restore_dirty_state(workspace: Path, dirty_states: tuple[tuple[str, str], ...]) -> None:
    for path, dirty_content in dirty_states:
        _dirty_state_target(workspace, path).write_text(dirty_content)


def _dirty_state_target(workspace: Path, relative_path: str) -> Path:
    target = workspace / relative_path
    try:
        resolved = target.resolve(strict=False)
        workspace_resolved = workspace.resolve()
    except OSError as exc:
        raise HarnessContractError(f"invalid dirty-state path {relative_path}: {exc}") from exc
    if Path(relative_path).is_absolute() or not resolved.is_relative_to(workspace_resolved):
        raise HarnessContractError(f"dirty-state path escapes workspace: {relative_path}")
    if target.is_symlink():
        raise HarnessContractError(f"dirty-state path is a symlink: {relative_path}")
    return target


def initialize_git_baseline(workspace: Path) -> None:
    commands = (
        ("git", "init", "-q"),
        ("git", "config", "user.email", "eval-harness@example.invalid"),
        ("git", "config", "user.name", "Eval Harness"),
        ("git", "add", "-A"),
        ("git", "commit", "-q", "--allow-empty", "-m", "baseline"),
    )
    for command in commands:
        completed = subprocess.run(command, cwd=workspace, text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            message = completed.stderr.strip() or completed.stdout.strip() or f"git command failed: {' '.join(command)}"
            raise HarnessContractError(message)


def snapshot_files(root: Path) -> dict[str, bytes]:
    root_resolved = root.resolve()
    snapshot: dict[str, bytes] = {}
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dir_path = Path(dirpath)
        kept_dirs = []
        for dirname in dirnames:
            child = dir_path / dirname
            if child.is_symlink() or dirname in IGNORED_NAMES:
                continue
            kept_dirs.append(dirname)
        dirnames[:] = kept_dirs
        for filename in filenames:
            if filename in IGNORED_NAMES or filename.endswith(".pyc"):
                continue
            path = dir_path / filename
            if path.is_symlink():
                snapshot[str(path.relative_to(root).as_posix())] = f"SYMLINK:{os.readlink(path)}".encode()
                continue
            resolved = path.resolve()
            if not resolved.is_relative_to(root_resolved):
                continue
            snapshot[path.relative_to(root).as_posix()] = path.read_bytes()
    return snapshot


def diff_snapshots(before: dict[str, bytes], after: dict[str, bytes]) -> tuple[tuple[str, ...], str]:
    changed = tuple(sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path)))
    parts: list[str] = []
    for path in changed:
        old = _decode_lines(before.get(path))
        new = _decode_lines(after.get(path))
        parts.extend(difflib.unified_diff(old, new, fromfile=f"a/{path}", tofile=f"b/{path}", lineterm=""))
    return changed, "\n".join(parts)


def snapshot_text_files(snapshot: dict[str, bytes]) -> dict[str, str]:
    return {path: content.decode(errors="replace") for path, content in snapshot.items() if not content.startswith(b"SYMLINK:")}


def normalize_workspace_path(path: str, workspace: Path) -> tuple[str | None, dict[str, object] | None]:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = workspace / candidate
    try:
        resolved = candidate.resolve(strict=False)
        workspace_resolved = workspace.resolve()
    except OSError as exc:
        return None, {"path": path, "reason": str(exc)}
    if not resolved.is_relative_to(workspace_resolved):
        return None, {"path": path, "reason": "outside_workspace"}
    return resolved.relative_to(workspace_resolved).as_posix(), None


def _decode_lines(value: bytes | None) -> list[str]:
    if value is None:
        return []
    return value.decode(errors="replace").splitlines()


def _remove_tree_with_retries(path: Path, *, attempts: int = 5, delay_seconds: float = 0.1) -> None:
    last_error: OSError | None = None
    for attempt in range(attempts):
        try:
            shutil.rmtree(path)
            return
        except OSError as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(delay_seconds)
    assert last_error is not None
    raise last_error

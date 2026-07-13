from __future__ import annotations

import subprocess
from pathlib import Path

from .core import HarnessContractError
from .fingerprints import sha256_file


def install_agents_file(workspace: Path, prompt_path: Path) -> dict[str, object]:
    prompt_text = prompt_path.read_text() if prompt_path.exists() else ""
    agents_path = workspace / "AGENTS.md"
    if agents_path.exists():
        original = agents_path.read_text()
        agents_path.write_text(f"{prompt_text.rstrip()}\n\n---\n\n# Fixture Instructions\n\n{original}")
    else:
        agents_path.write_text(prompt_text)
    return {
        "method": "AGENTS.md",
        "path": str(agents_path),
        "prompt_sha256": sha256_file(prompt_path) if prompt_path.exists() else None,
        "installed": agents_path.exists(),
        "contains_prompt": bool(prompt_text and prompt_text.strip() in agents_path.read_text()),
    }


def append_system_prompt_metadata(prompt_path: Path) -> dict[str, object]:
    return {
        "method": "append-system-prompt",
        "path": str(prompt_path),
        "prompt_sha256": sha256_file(prompt_path) if prompt_path.exists() else None,
        "installed": prompt_path.exists(),
    }


def baseline_prompt_injection(workspace: Path, metadata: object) -> dict[str, object]:
    data = metadata if isinstance(metadata, dict) else {}
    if data.get("method") != "AGENTS.md":
        return {"method": data.get("method"), "baselined": False, "reason": "no_workspace_write"}
    agents_path = Path(str(data.get("path") or ""))
    relative, error = _workspace_relative(workspace, agents_path)
    if error:
        raise HarnessContractError(error)
    _git(workspace, ("add", "--", relative))
    staged = _git(workspace, ("diff", "--cached", "--quiet"), check=False)
    if staged.returncode == 0:
        return {"method": "AGENTS.md", "baselined": False, "path": relative, "reason": "unchanged"}
    _git(workspace, ("commit", "--amend", "-q", "--no-edit"))
    return {"method": "AGENTS.md", "baselined": True, "path": relative}


def _workspace_relative(workspace: Path, path: Path) -> tuple[str, str | None]:
    candidate = path if path.is_absolute() else workspace / path
    try:
        resolved = candidate.resolve(strict=False)
        root = workspace.resolve()
    except OSError as exc:
        return "", str(exc)
    if not resolved.is_relative_to(root) or not candidate.exists():
        return "", f"prompt injection path is not inside workspace: {path}"
    return resolved.relative_to(root).as_posix(), None


def _git(workspace: Path, args: tuple[str, ...], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(("git", *args), cwd=workspace, text=True, capture_output=True, check=False)
    if check and completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or f"git {' '.join(args)} failed"
        raise HarnessContractError(message)
    return completed

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def fingerprint_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def deterministic_module_name(path: Path, *, root: Path) -> str:
    relative = path.resolve().relative_to(root.resolve()).as_posix()
    digest = hashlib.sha256(relative.encode("utf-8")).hexdigest()[:16]
    stem = path.stem.replace("-", "_").replace(".", "_")
    return f"evals_case_{stem}_{digest}"


def source_fingerprint(paths: Iterable[Path]) -> str:
    entries: list[dict[str, str]] = []
    for path in sorted(paths, key=lambda item: item.as_posix()):
        entries.append({
            "path": path.as_posix(),
            "sha256": sha256_file(path),
        })
    return fingerprint_json(entries)


def fixture_tree_fingerprint(path: Path | None) -> str | None:
    if path is None:
        return None
    entries: list[dict[str, object]] = []
    for root, dirnames, filenames in os.walk(path, followlinks=False):
        root_path = Path(root)
        dirnames[:] = sorted(dirnames)
        for filename in sorted(filenames):
            item = root_path / filename
            relative = item.relative_to(path).as_posix()
            if item.is_symlink():
                entries.append({"path": relative, "type": "symlink", "target": os.readlink(item)})
            else:
                stat = item.stat()
                entries.append({"path": relative, "type": "file", "mode": stat.st_mode & 0o777, "sha256": sha256_file(item)})
    return fingerprint_json(entries)

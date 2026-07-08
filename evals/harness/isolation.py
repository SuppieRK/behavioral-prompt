from __future__ import annotations

import shutil
from pathlib import Path


def seed_file_if_exists(source: Path, target: Path) -> bool:
    if not source.exists():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return True


def seed_pi_state(root: Path) -> dict[str, object]:
    source = Path.home() / ".pi" / "agent"
    target = root / "pi-agent"
    copied = [name for name in ("auth.json", "settings.json", "trust.json", "models.json") if seed_file_if_exists(source / name, target / name)]
    return {"method": "temporary-pi-agent-dir", "path": str(target), "seeded_private_data": copied}


def seed_codex_state(root: Path) -> dict[str, object]:
    source = Path.home() / ".codex"
    target = root / "codex-home"
    copied = [name for name in ("auth.json",) if seed_file_if_exists(source / name, target / name)]
    return {"method": "temporary-codex-home", "path": str(target), "seeded_private_data": copied}


def seed_opencode_state(root: Path) -> dict[str, object]:
    config = root / "opencode-config"
    data = root / "opencode-data"
    clean_config = config / "opencode" / "opencode.json"
    clean_config.parent.mkdir(parents=True, exist_ok=True)
    clean_config.write_text("{}\n")
    data.mkdir(parents=True, exist_ok=True)
    source_data = Path.home() / ".local" / "share" / "opencode"
    copied_data = [name for name in ("auth.json", "account.json") if seed_file_if_exists(source_data / name, data / "opencode" / name)]
    return {
        "method": "temporary-opencode-config",
        "config_path": str(config),
        "data_path": str(data),
        "seeded_private_data": {"config": [], "data": copied_data},
        "global_config_excluded": True,
        "external_plugins_disabled": True,
        "sharing": "disabled",
    }

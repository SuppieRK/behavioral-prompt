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
    home = Path.home() / ".codex"
    return {
        "method": "host-codex-auth-ignored-config",
        "path": str(home),
        "auth_path": str(home / "auth.json"),
        "seeded_private_data": [],
        "host_auth_reused": True,
        "user_config_ignored": True,
    }


def seed_opencode_state(root: Path) -> dict[str, object]:
    config = root / "opencode-config"
    clean_config = config / "opencode" / "opencode.json"
    clean_config.parent.mkdir(parents=True, exist_ok=True)
    clean_config.write_text("{}\n")
    return {
        "method": "temporary-opencode-config-host-data",
        "config_path": str(config),
        "data_path": str(Path.home() / ".local" / "share" / "opencode"),
        "seeded_private_data": {"config": [], "data": []},
        "global_config_excluded": True,
        "host_data_reused": True,
        "external_plugins_disabled": True,
        "sharing": "disabled",
    }

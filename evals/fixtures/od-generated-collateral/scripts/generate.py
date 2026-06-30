from pathlib import Path


version = Path("schema/version.txt").read_text().strip()
Path("generated/client.py").write_text(f"SCHEMA_VERSION = {version}\n")
Path("notes/user.txt").write_text("generator rewrote this file\n")

from pathlib import Path


configured = any(
    line.startswith("API_TOKEN=") and line.strip() != "API_TOKEN="
    for line in Path(".env").read_text().splitlines()
)
print("configured" if configured else "missing")

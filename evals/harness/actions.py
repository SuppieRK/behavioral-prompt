from __future__ import annotations

from typing import Mapping


def compact_actions(command_events, tool_events) -> list[dict[str, object]]:
    candidates = []
    for kind, events in (("command", command_events), ("tool", tool_events)):
        for position, event in enumerate(events):
            if not isinstance(event, Mapping):
                continue
            command = str(event.get("command") or "")[:240]
            name = str(event.get("name") or event.get("tool") or "")[:80]
            if command or name:
                try:
                    index = int(event.get("index", position))
                except (TypeError, ValueError):
                    index = position
                candidates.append((index, kind, command, name, event))
    candidates.sort(key=lambda item: (item[0], item[1]))
    compact = []
    seen = set()
    for index, kind, command, name, event in candidates:
        identity = (kind, command or name)
        if identity in seen:
            continue
        seen.add(identity)
        item: dict[str, object] = {"index": index, "kind": kind}
        if command:
            item["command"] = command
        if name:
            item["name"] = name
        if event.get("exit_code") is not None:
            item["exit_code"] = event.get("exit_code")
        compact.append(item)
        if len(compact) == 30:
            break
    return compact

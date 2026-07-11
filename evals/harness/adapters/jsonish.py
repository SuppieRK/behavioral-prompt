from __future__ import annotations

import json
import re
import shlex

from ..evidence import NormalizedTargetEvidence
from ..metrics import normalize_usage


def normalize_jsonish_output(stdout: str) -> NormalizedTargetEvidence:
    events = []
    command_events = []
    tool_events = []
    actions = []
    delta_parts = []
    direct_parts = []
    assistant_snapshot = ""
    usage_raw = None
    target_error = ""
    invalid_lines = 0
    for index, line in enumerate(stdout.splitlines()):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            invalid_lines += 1
            continue
        if isinstance(event, dict):
            events.append(event)
            if not target_error:
                target_error = _target_error(event)
            command_events.extend(_command_events(event, index))
            tool_events.extend(_tool_events(event, index))
            actions.extend(_actions(event, index))
            delta = _text_delta(event)
            if delta:
                delta_parts.append(delta)
            else:
                snapshot = _assistant_snapshot_text(event)
                if snapshot:
                    assistant_snapshot = snapshot
                else:
                    text = _direct_text(event)
                    if text:
                        direct_parts.append(text)
            usage = event.get("usage") or event.get("token_usage")
            if not usage and isinstance(event.get("message"), dict):
                usage = event["message"].get("usage")
            if not usage and isinstance(event.get("item"), dict):
                usage = event["item"].get("usage")
            if not usage and isinstance(event.get("part"), dict):
                usage = event["part"].get("tokens")
            if isinstance(usage, dict):
                usage_raw = usage
    final = "".join(delta_parts) or "".join(direct_parts) or assistant_snapshot
    if not final and stdout.strip() and not events:
        final = stdout.strip()
    return NormalizedTargetEvidence(
        transcript=tuple(events),
        final_response=final,
        parse_diagnostics={
            "format": "jsonl",
            "valid_events": len(events),
            "invalid_lines": invalid_lines,
            "ignored_events": 0,
            "parser": "jsonish-lines-v1",
        },
        adapter_diagnostics={"target_error": target_error} if target_error else {},
        target_usage=normalize_usage(usage_raw),
        agent_command_events=tuple(command_events),
        agent_tool_events=tuple(tool_events),
        agent_actions=tuple(_dedupe_actions(actions)),
    )


def _text_delta(event: dict) -> str:
    update = event.get("assistantMessageEvent")
    if isinstance(update, dict) and update.get("type") == "text_delta":
        delta = update.get("delta")
        return delta if isinstance(delta, str) else ""
    item = event.get("item")
    if isinstance(item, dict) and event.get("type") != "item.completed" and item.get("type") == "agent_message":
        text = item.get("text")
        return text if isinstance(text, str) else ""
    return ""


def _target_error(event: dict) -> str:
    for payload in _error_payloads(event):
        stop_reason = str(payload.get("stopReason") or payload.get("stop_reason") or "").strip().lower()
        error = payload.get("errorMessage") or payload.get("error") or payload.get("message")
        if isinstance(error, dict):
            error = error.get("message")
        if isinstance(error, str) and error.strip() and (stop_reason == "error" or _assistant_or_roleless(payload)):
            error_text = error.strip()
            if not _benign_target_error(error_text):
                return error_text
        if stop_reason == "error":
            return "target reported stopReason=error"
    return ""


def _benign_target_error(error: str) -> bool:
    return error.strip().lower() == "websocket closed 1000"


def _error_payloads(event: dict) -> tuple[dict, ...]:
    payloads = [event]
    for key in ("message", "item", "part"):
        value = event.get(key)
        if isinstance(value, dict):
            payloads.append(value)
    return tuple(payloads)


def _direct_text(event: dict) -> str:
    if not _assistant_or_roleless(event):
        return ""
    for key in ("text", "content"):
        value = event.get(key)
        if isinstance(value, str):
            return value
    message = event.get("message")
    if isinstance(message, str):
        return message
    part = event.get("part")
    if isinstance(part, dict) and _assistant_or_roleless(part) and isinstance(part.get("text"), str):
        return part["text"]
    return ""


def _assistant_or_roleless(value: dict) -> bool:
    role = value.get("role")
    return not isinstance(role, str) or role.strip().lower() == "assistant"


def _assistant_snapshot_text(event: dict) -> str:
    message = event.get("message")
    if isinstance(message, dict) and message.get("role") == "assistant":
        return _content_text(message.get("content"))
    item = event.get("item")
    if isinstance(item, dict) and event.get("type") == "item.completed" and item.get("type") == "agent_message":
        text = item.get("text")
        return text if isinstance(text, str) else ""
    return ""


def _content_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "".join(parts)
    return ""


def _command_events(event: dict, index: int) -> list[dict[str, object]]:
    found = []
    item = event.get("item")
    if isinstance(item, dict):
        command = _command_text(item)
        if command and _looks_like_command_event(item):
            found.append(_command_event(command, event, item, index, "item"))
    part = event.get("part")
    if isinstance(part, dict):
        command = _command_text(part)
        if command and _looks_like_command_event(part):
            found.append(_command_event(command, event, part, index, "part"))
        state = part.get("state")
        input_payload = state.get("input") if isinstance(state, dict) else None
        if isinstance(input_payload, dict):
            command = _command_text(input_payload)
            if command and _looks_like_command_event(event):
                found.append(_command_event(command, event, input_payload, index, "part.state.input"))
    command = _command_text(event)
    if command and _looks_like_command_event(event):
        found.append(_command_event(command, event, event, index, "event"))
    tool_calls = event.get("tool_calls")
    for tool_call in tool_calls if isinstance(tool_calls, list) else ():
        if isinstance(tool_call, dict):
            tool_command = _command_text(tool_call)
            if tool_command:
                found.append(_command_event(tool_command, event, tool_call, index, "tool_call"))
    deduped = []
    seen = set()
    for command_event in found:
        key = (command_event.get("command"), command_event.get("source"), command_event.get("index"))
        if key not in seen:
            deduped.append(command_event)
            seen.add(key)
    return deduped


def _tool_events(event: dict, index: int) -> list[dict[str, object]]:
    found = []
    for source, payload in _tool_payloads(event):
        name = payload.get("name") or payload.get("tool") or payload.get("type") or payload.get("kind")
        if not isinstance(name, str) or not name.strip():
            continue
        normalized: dict[str, object] = {"name": name, "index": index, "source": source}
        command = _command_text(payload)
        if command:
            normalized["command"] = command
        status = payload.get("status") or payload.get("state") or event.get("status") or event.get("type")
        if status is not None:
            normalized["status"] = str(status)
        found.append(normalized)
    return found


def _tool_payloads(event: dict) -> list[tuple[str, dict]]:
    payloads = []
    for key in ("tool", "tool_use", "toolCall", "tool_call"):
        payload = event.get(key)
        if isinstance(payload, dict):
            payloads.append((key, payload))
    tool_calls = event.get("tool_calls")
    for payload in tool_calls if isinstance(tool_calls, list) else ():
        if isinstance(payload, dict):
            payloads.append(("tool_call", payload))
    return payloads


def _command_text(value: dict) -> str:
    for key in ("command", "cmd", "argv"):
        candidate = value.get(key)
        if isinstance(candidate, str):
            return candidate
        if isinstance(candidate, list) and candidate:
            return " ".join(str(part) for part in candidate)
    for key in ("arguments", "args", "input", "state"):
        nested = value.get(key)
        if isinstance(nested, dict):
            command = _command_text(nested)
            if command:
                return command
    return ""


def _looks_like_command_event(value: dict) -> bool:
    event_type = str(value.get("type") or value.get("name") or value.get("tool") or value.get("kind") or "").lower()
    event_tokens = ("command", "tool_execution", "tool_use", "shell", "bash")
    return bool(value.get("command") or value.get("cmd") or value.get("argv") or value.get("toolName") or any(token in event_type for token in event_tokens))


def _command_event(command: str, event: dict, payload: dict, index: int, source: str) -> dict[str, object]:
    status = payload.get("status") or payload.get("state") or event.get("status") or event.get("type")
    normalized: dict[str, object] = {"command": command, "index": index, "source": source}
    if status is not None:
        normalized["status"] = str(status)
    for key in ("exit_code", "exitStatus", "returncode"):
        if key in payload:
            normalized["exit_code"] = payload[key]
            break
    return normalized


def _actions(event: dict, index: int) -> list[dict[str, object]]:
    actions: list[dict[str, object]] = []
    payloads = [("event", event)]
    for key in ("item", "part", "tool", "tool_use", "toolCall", "tool_call"):
        value = event.get(key)
        if isinstance(value, dict):
            payloads.append((key, value))
    for source, payload in payloads:
        tool = str(payload.get("name") or payload.get("toolName") or payload.get("tool") or payload.get("type") or "")
        command = _command_text(payload)
        paths = _payload_paths(payload)
        kind = _action_kind(tool, command)
        if not kind:
            continue
        action: dict[str, object] = {"index": index, "kind": kind, "tool": tool, "source": source}
        detail = _payload_detail(payload)
        if detail:
            action["detail"] = detail
        if command:
            action["command"] = command
            command_paths = _command_paths(command)
            paths = tuple(dict.fromkeys((*paths, *command_paths)))
        if paths:
            action["paths"] = paths
            action["path"] = paths[0]
        status = payload.get("status") or event.get("status") or event.get("type")
        if status is not None:
            action["status"] = str(status)
        for key in ("exit_code", "exitStatus", "returncode"):
            if key in payload:
                action["exit_code"] = payload[key]
                break
        actions.append(action)
    return actions


def _action_kind(tool: str, command: str) -> str:
    lowered = tool.lower()
    if any(token in lowered for token in ("update_plan", "todowrite", "todolist", "plan")):
        return "plan"
    if any(token in lowered for token in ("apply_patch", "file_change", "write", "edit", "create_file")):
        return "write"
    if any(token in lowered for token in ("read", "view", "open_file")):
        return "read"
    if command:
        text = command.lower()
        if re.search(r"\bgit\s+(?:commit|push|tag|switch\s+-c|checkout\s+-b|branch\s+[^-])", text):
            return "vcs_write"
        first = _first_command(command)
        if first in {"cat", "sed", "nl", "rg", "grep", "ls", "find", "tree", "head", "tail"} or "git ls-files" in text or "git status" in text:
            return "read"
        if any(token in text for token in ("pytest", "unittest", "test-focused", "check-focused", "npm test", "go test", "cargo test")):
            return "validation"
        return "command"
    return ""


def _payload_paths(value: dict) -> tuple[str, ...]:
    found: list[str] = []
    stack: list[object] = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, list):
            stack.extend(current)
            continue
        if not isinstance(current, dict):
            continue
        for key, item in current.items():
            if key in {"path", "file", "file_path", "filepath", "filePath", "relativePath"} and isinstance(item, str):
                found.append(item)
            elif isinstance(item, (dict, list)):
                stack.append(item)
    return tuple(dict.fromkeys(found))


def _payload_detail(value: dict) -> str:
    for key in ("input", "args", "arguments", "state", "changes"):
        item = value.get(key)
        if isinstance(item, (dict, list)):
            return json.dumps(item, sort_keys=True, separators=(",", ":"))[:2000]
        if isinstance(item, str):
            return item[:2000]
    return ""


def _command_paths(command: str) -> tuple[str, ...]:
    command = _unwrap_shell(command)
    try:
        parts = shlex.split(command)
    except ValueError:
        parts = command.split()
    return tuple(dict.fromkeys(part for part in parts if "/" in part or part.endswith((".py", ".md", ".yaml", ".yml", ".json", ".txt"))))


def _first_command(command: str) -> str:
    command = _unwrap_shell(command)
    try:
        parts = shlex.split(command)
    except ValueError:
        parts = command.split()
    while parts and ("=" in parts[0] or parts[0] in {"ccp", "sudo", "env"}):
        parts.pop(0)
    return parts[0].rsplit("/", 1)[-1] if parts else ""


def _unwrap_shell(command: str) -> str:
    try:
        parts = shlex.split(command)
    except ValueError:
        return command
    if len(parts) >= 3 and parts[0].rsplit("/", 1)[-1] in {"bash", "sh", "zsh"} and parts[1] in {"-c", "-lc"}:
        return parts[2]
    return command


def _dedupe_actions(actions: list[dict[str, object]]) -> list[dict[str, object]]:
    result = []
    seen = set()
    for action in actions:
        key = (action.get("index"), action.get("kind"), action.get("command"), tuple(action.get("paths") or ()))
        if action.get("kind") == "read":
            key = (action.get("kind"), action.get("command"), tuple(action.get("paths") or ()))
        if key not in seen:
            result.append(action)
            seen.add(key)
    return result

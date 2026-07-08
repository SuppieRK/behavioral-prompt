from __future__ import annotations

from typing import Callable, Mapping


ProgressCallback = Callable[[dict[str, object]], None]


def emit_progress(progress: ProgressCallback | None, event: dict[str, object]) -> None:
    if progress is not None:
        progress(event)


def status_counts(cells: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for cell in cells:
        status = str(cell.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return counts


def progress_metrics(cells: list[dict[str, object]]) -> dict[str, object]:
    duration_seconds = 0.0
    actual_tokens = 0
    avoided_tokens = 0
    for cell in cells:
        raw = cell.get("raw_run") if isinstance(cell.get("raw_run"), dict) else {}
        usage = cell.get("target_usage") if isinstance(cell.get("target_usage"), dict) else {}
        reused = bool(cell.get("reused_exact_match"))
        if not reused and raw.get("duration_seconds") is not None:
            duration_seconds += float(raw["duration_seconds"])
        actual_tokens += 0 if reused else _first_int(
            usage.get("actual_tokens_spent"),
            usage.get("total_tokens_reported"),
            usage.get("uncached_total_tokens"),
            raw.get("actual_tokens_spent"),
            0,
        )
        avoided_tokens += int(usage.get("avoided_tokens_by_reuse") or 0)
    return {
        "duration_seconds": duration_seconds,
        "actual_tokens_spent": actual_tokens,
        "avoided_tokens_by_reuse": avoided_tokens,
    }


def progress_summary(cells: list[dict[str, object]]) -> dict[str, object]:
    return {"status_counts": status_counts(cells), **progress_metrics(cells)}


def _first_int(*values: object) -> int:
    for value in values:
        if value is not None:
            return int(value)
    return 0


def print_progress(event: dict[str, object]) -> None:
    kind = event.get("event")
    if kind == "run_started":
        print(f"eval progress: started cases={event.get('total_cases')} targets={event.get('total_targets')} cells={event.get('total_cells')}", flush=True)
    elif kind == "case_started":
        print(f"eval progress: case {event.get('case_index')}/{event.get('total_cases')} started case={event.get('case_id')} targets={event.get('target_count')}", flush=True)
    elif kind == "cell_started":
        print(f"eval progress: cell started {event.get('completed_cells')}/{event.get('total_cells')} case={event.get('case_id')} target={event.get('target_id')}", flush=True)
    elif kind == "cell_completed":
        reason = event.get("reason") or ""
        reused = " reused=true" if event.get("reused_exact_match") else ""
        print(f"eval progress: cell completed {event.get('completed_cells')}/{event.get('total_cells')} case={event.get('case_id')} target={event.get('target_id')} status={event.get('status')} reason={reason}{reused}{format_progress_metrics(event)}", flush=True)
    elif kind == "case_completed":
        print(f"eval progress: case {event.get('case_index')}/{event.get('total_cases')} completed case={event.get('case_id')} cells={event.get('completed_cells')}/{event.get('total_cells')} statuses={format_status_counts(event.get('status_counts'))}{format_progress_metrics(event)}", flush=True)
    elif kind == "run_completed":
        print(f"eval progress: completed cells={event.get('completed_cells')}/{event.get('total_cells')} statuses={format_status_counts(event.get('status_counts'))}{format_progress_metrics(event)}", flush=True)


def print_report_summary(report: Mapping[str, object]) -> None:
    metrics = report.get("metrics") if isinstance(report.get("metrics"), Mapping) else {}
    promotion = report.get("promotion") if isinstance(report.get("promotion"), Mapping) else {}
    print(
        "eval report: "
        f"cells={report.get('cell_count')} "
        f"statuses={format_status_counts(report.get('status_counts'))} "
        f"promotion_allowed={bool(promotion.get('allowed'))}"
        f"{format_progress_metrics(metrics)}",
        flush=True,
    )


def format_status_counts(value: object) -> str:
    if not isinstance(value, Mapping):
        return ""
    return ",".join(f"{key}:{value[key]}" for key in sorted(value))


def format_progress_metrics(event: Mapping[str, object]) -> str:
    pieces: list[str] = []
    duration = event.get("duration_seconds")
    if duration is not None:
        pieces.append(f"duration={float(duration):.1f}s")
    tokens = event.get("actual_tokens_spent")
    if tokens is not None:
        pieces.append(f"tokens={int(tokens)}")
    avoided = event.get("avoided_tokens_by_reuse")
    if avoided:
        pieces.append(f"avoided_tokens={int(avoided)}")
    return "" if not pieces else " " + " ".join(pieces)

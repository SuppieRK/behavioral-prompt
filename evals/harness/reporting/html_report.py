from __future__ import annotations

import html
import json
from typing import Any


REPORT_EMBED_MARKER = "window.__PROMPT_EVAL_REPORT__"

STATUS_ORDER = {"harness_error": 0, "fail": 1, "not_evaluated": 2, "pass": 3}
STATUS_LABELS = {"harness_error": "Harness Error", "not_evaluated": "Not Evaluated"}


def render_html(report: dict[str, Any]) -> str:
    title = _escape(report.get("title", "Prompt Eval Report"))
    embedded = json.dumps(report, sort_keys=True).replace("<", "\\u003c")
    groups = _case_groups(report)
    body = "".join(_render_case_group(group) for group in groups)
    return f"""<!doctype html>
<html>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>{title}</title>
  <style>{_css()}</style>
</head>
<body>
  <header class='page-header'>
    <div>
      <p class='eyebrow'>{_escape(report.get('schema_version', 'eval report'))}</p>
      <h1>{title}</h1>
      {_render_prompt_meta(report)}
    </div>
    {_render_promotion(report.get('promotion', {}))}
  </header>
  <section class='summary-band' aria-label='Summary'>
    {_render_status_cards(report.get('status_counts', report.get('summary', {})))}
  </section>
  {_render_run_overview(report)}
  {_render_metrics(report.get('metrics', {}), report.get('promotion', {}))}
  <main id='result-list' class='case-list'>{body or "<p class='empty'>No case results in this report.</p>"}</main>
  <script type='application/json' id='report'>{embedded}</script>
  <script>{REPORT_EMBED_MARKER} = JSON.parse(document.getElementById('report').textContent);</script>
</body>
</html>"""


def _css() -> str:
    return """
:root { color-scheme: light; --bg:#f6f8fa; --panel:#fff; --border:#d8dee4; --text:#1f2328; --muted:#656d76; --subtle:#f6f8fa; --pass:#1a7f37; --fail:#cf222e; --warn:#9a6700; --info:#0969da; --shadow:0 1px 2px rgba(31,35,40,.06); --shadow-strong:0 8px 24px rgba(31,35,40,.08); }
* { box-sizing: border-box; } body { margin: 0; background: var(--bg); color: var(--text); font: 14px/1.45 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
.page-header { display: flex; justify-content: space-between; gap: 24px; align-items: flex-start; padding: 30px 32px 24px; background: linear-gradient(180deg, #fff 0%, #f9fbfc 100%); border-bottom: 1px solid var(--border); } h1 { margin: 0; font-size: 30px; line-height: 1.12; letter-spacing: 0; } h2 { margin: 0; font-size: 17px; letter-spacing: 0; } h3 { margin: 20px 0 8px; font-size: 12px; letter-spacing: 0; color: var(--muted); text-transform: uppercase; } h4 { margin: 16px 0 8px; font-size: 14px; }
.eyebrow, .meta, .empty, .case-id, .counts { margin: 0 0 6px; color: var(--muted); } .eyebrow { font-weight: 700; text-transform: uppercase; } .case-id, .counts, .card-label, th { font-size: 12px; } .summary-band, .overview, .metrics, .case-list, .raw-report { margin: 16px 32px; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; } .card, .case-card, .raw-report, .panel { background: var(--panel); border: 1px solid var(--border); border-radius: 6px; box-shadow: var(--shadow); } .card, .panel, .raw-report { padding: 12px; } .card-label, th { color: var(--muted); font-weight: 700; text-transform: uppercase; } .card-value { display: block; margin-top: 4px; font-size: 24px; font-weight: 750; }
.overview { display: grid; grid-template-columns: minmax(260px, 1.1fr) minmax(280px, 2fr); gap: 16px; } .overview .panel, .metrics .panel { box-shadow: var(--shadow-strong); } .overview-list { display: grid; gap: 8px; margin: 10px 0 0; padding: 0; list-style: none; } .overview-list li { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 9px 10px; border: 1px solid var(--border); border-radius: 6px; background: var(--subtle); } .overview-note { margin: 8px 0 0; }
.metrics { display: grid; grid-template-columns: minmax(240px, 1fr) minmax(280px, 2fr); gap: 16px; } .case-list { display: grid; gap: 12px; } .case-card { overflow: hidden; } .case-card > summary { cursor: pointer; list-style: none; padding: 14px 16px; display: grid; grid-template-columns: auto 1fr auto; gap: 12px; align-items: center; } .case-card > summary::-webkit-details-marker { display: none; } .case-card > summary::after { content: "Details"; color: var(--info); font-weight: 700; font-size: 12px; } .case-card[open] > summary::after { content: "Hide"; } .case-body { border-top: 1px solid var(--border); padding: 0 16px 16px; } .case-title { min-width: 0; } .case-title h2 { overflow-wrap: anywhere; }
.badge { display: inline-flex; align-items: center; min-height: 22px; padding: 2px 8px; border-radius: 999px; font-weight: 700; font-size: 12px; border: 1px solid currentColor; white-space: nowrap; } .pass { color: var(--pass); background: #dafbe1; } .fail, .harness_error { color: var(--fail); background: #ffebe9; } .not_evaluated { color: var(--warn); background: #fff8c5; } .neutral { color: var(--muted); background: #f6f8fa; }
.target-card { border: 1px solid var(--border); border-radius: 6px; margin-top: 12px; overflow: hidden; } .target-head { display: flex; justify-content: space-between; gap: 12px; padding: 10px 12px; background: var(--subtle); border-bottom: 1px solid var(--border); } .target-body { padding: 12px; } .target-summary { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; } .pill { display: inline-flex; align-items: center; min-height: 22px; padding: 2px 8px; border: 1px solid var(--border); border-radius: 999px; background: #fff; color: var(--muted); font-size: 12px; font-weight: 600; } table { width: 100%; border-collapse: collapse; } th, td { padding: 7px 8px; border-bottom: 1px solid var(--border); text-align: left; vertical-align: top; }
pre { margin: 8px 0 0; padding: 10px; overflow: auto; white-space: pre-wrap; background: var(--subtle); border: 1px solid var(--border); border-radius: 6px; } details.evidence { margin-top: 10px; } details.evidence > summary, .raw-report > summary { cursor: pointer; color: var(--info); font-weight: 700; }
@media (max-width: 760px) { .page-header { display: block; padding: 20px; } .summary-band, .overview, .metrics, .case-list, .raw-report { margin: 12px; } .overview, .metrics, .case-card > summary { grid-template-columns: 1fr; } .case-card > summary::after { content: ""; } }
"""


def _render_prompt_meta(report: dict[str, Any]) -> str:
    prompt = report.get("prompt") if isinstance(report.get("prompt"), dict) else {}
    bits = [
        f"Cases: {_escape(report.get('case_count', len(report.get('cells', []))))}",
        f"Targets: {_escape(report.get('target_count', 'n/a'))}",
        f"Cells: {_escape(report.get('cell_count', len(report.get('cells', []))))}",
    ]
    if prompt:
        bits.append(f"Prompt: {_escape(prompt.get('path', ''))} @ {_escape(str(prompt.get('sha256', ''))[:12])}")
    return f"<p class='meta'>{' | '.join(bits)}</p>"


def _render_promotion(promotion: Any) -> str:
    if not isinstance(promotion, dict):
        return ""
    allowed = bool(promotion.get("allowed"))
    status = "pass" if allowed else "fail"
    label = "Promotion Allowed" if allowed else "Promotion Blocked"
    reason = promotion.get("reason", "")
    required = f"{promotion.get('required_pass', 0)}/{promotion.get('required_total', 0)} required pass"
    return f"<aside class='panel'><span class='badge {status}'>{label}</span><p class='meta'>{_escape(reason)}</p><p class='meta'>{_escape(required)}</p></aside>"


def _render_status_cards(statuses: Any) -> str:
    if not isinstance(statuses, dict):
        statuses = {}
    order = ("pass", "fail", "not_evaluated", "harness_error", "timeout", "reused_exact_match")
    cards = []
    for name in order:
        value = statuses.get(name, 0)
        cards.append(f"<div class='card'><span class='card-label'>{_escape(_label(name))}</span><span class='card-value'>{_escape(value)}</span></div>")
    return f"<div id='summary-grid' class='cards'>{''.join(cards)}</div>"


def _render_run_overview(report: dict[str, Any]) -> str:
    cells = _flat_cells(report)
    blocked = [cell for cell in cells if str(cell.get("status") or "") in {"fail", "harness_error", "not_evaluated"}]
    promotion = report.get("promotion") if isinstance(report.get("promotion"), dict) else {}
    blocked_rows = "".join(_overview_cell(cell) for cell in blocked[:8])
    if not blocked_rows:
        blocked_rows = "<li><span>No blocking cells in this report.</span><span class='badge pass'>Clean</span></li>"
    more = ""
    if len(blocked) > 8:
        more = f"<p class='meta overview-note'>{len(blocked) - 8} more blocking cells are listed below.</p>"
    reason = promotion.get("reason", "No promotion metadata recorded.") if promotion else "No promotion metadata recorded."
    return f"""<section class='overview' aria-label='Run overview'>
  <div class='panel'>
    <h3>Run Overview</h3>
    <p>{_escape(reason)}</p>
    {_render_required_case_summary(promotion)}
  </div>
  <div class='panel'>
    <h3>Needs Attention</h3>
    <ul class='overview-list'>{blocked_rows}</ul>
    {more}
  </div>
</section>"""


def _render_required_case_summary(promotion: dict[str, Any]) -> str:
    if not promotion:
        return ""
    failed = promotion.get("failed_required_cases") if isinstance(promotion.get("failed_required_cases"), list) else []
    missing = promotion.get("missing_required_cases") if isinstance(promotion.get("missing_required_cases"), list) else []
    bits = [
        f"<span class='pill'>{_escape(promotion.get('required_pass', 0))}/{_escape(promotion.get('required_total', 0))} required pass</span>",
        f"<span class='pill'>{_escape(len(failed))} failed required</span>",
        f"<span class='pill'>{_escape(len(missing))} missing required</span>",
    ]
    return f"<div class='target-summary'>{''.join(bits)}</div>"


def _overview_cell(cell: dict[str, Any]) -> str:
    status = str(cell.get("status") or "unknown")
    case = cell.get("case_id") or cell.get("case_name") or "case"
    target = cell.get("target_id") or "target"
    reason = cell.get("reason") or cell.get("message") or status
    return f"<li><span><strong>{_escape(case)}</strong> <span class='meta'>{_escape(target)}: {_escape(reason)}</span></span><span class='badge {_status_class(status)}'>{_escape(_label(status))}</span></li>"


def _render_metrics(metrics: Any, promotion: Any) -> str:
    if not isinstance(metrics, dict):
        metrics = {}
    metric_cards = [
        ("Duration", _seconds(metrics.get("duration_seconds"))),
        ("Preflight", _seconds(metrics.get("preflight_duration_seconds"))),
        ("Actual tokens", _number(metrics.get("actual_tokens_spent"))),
        ("Avoided tokens", _number(metrics.get("avoided_tokens_by_reuse"))),
    ]
    top = metrics.get("top_duration_cells") if isinstance(metrics.get("top_duration_cells"), list) else []
    rows = "".join(
        f"<tr><td>{_escape(item.get('case_id', ''))}</td><td>{_escape(item.get('target_id', ''))}</td><td>{_seconds(item.get('duration_seconds'))}</td></tr>"
        for item in top if isinstance(item, dict)
    )
    blocked = ""
    if isinstance(promotion, dict) and promotion.get("failed_required_cases"):
        blocked = f"<p class='meta'>{len(promotion.get('failed_required_cases', []))} failed required cases.</p>"
    return f"""<section id='metrics-grid' class='metrics'>
  <div class='panel'><h3>Metrics</h3><div class='cards'>{''.join(f"<div class='card'><span class='card-label'>{_escape(k)}</span><span class='card-value'>{_escape(v)}</span></div>" for k, v in metric_cards)}</div>{blocked}</div>
  <div class='panel'><h3>Slowest Cells</h3><table><thead><tr><th>Case</th><th>Target</th><th>Duration</th></tr></thead><tbody>{rows or "<tr><td colspan='3'>No duration data.</td></tr>"}</tbody></table></div>
</section>"""


def _case_groups(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = report.get("cells")
    if isinstance(rows, list) and any(isinstance(row, dict) and "case_id" in row and "target_id" in row for row in rows):
        groups = _groups_from_flat_cells(rows)
    else:
        rows = report.get("cases", report.get("matrix", []))
        groups = [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
    return sorted(groups, key=lambda group: (_group_rank(group), str(_case(group).get("id") or "")))


def _flat_cells(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = report.get("cells")
    if isinstance(rows, list):
        return [row for row in rows if isinstance(row, dict)]
    return [cell for group in _case_groups(report) for cell in _cells(group)]


def _groups_from_flat_cells(cells: list[Any]) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for cell in cells:
        if isinstance(cell, dict):
            case_id = str(cell.get("case_id") or "case")
            groups.setdefault(case_id, {"case": _case_from_cell(cell), "cells": []})["cells"].append(cell)
    return list(groups.values())


def _case_from_cell(cell: dict[str, Any]) -> dict[str, Any]:
    return {"id": cell.get("case_id"), "name": cell.get("case_name") or cell.get("case_id"), "description": cell.get("case_description", ""), "user_input": cell.get("user_input", ""), "ground_truth": cell.get("ground_truth", [])}


def _render_case_group(row: dict[str, Any]) -> str:
    case = _case(row)
    cells = _cells(row)
    status = _group_status(cells)
    open_attr = " open" if status in {"fail", "harness_error", "not_evaluated"} else ""
    passed = sum(1 for cell in cells if cell.get("status") == "pass")
    return f"""<details class='case-card'{open_attr}>
  <summary><span class='badge {_status_class(status)}'>{_escape(_label(status))}</span><div class='case-title'><h2>{_escape(case.get('name') or case.get('id') or 'case')}</h2><span class='case-id'>{_escape(case.get('id', ''))}</span></div><span class='counts'>{passed}/{len(cells)} targets pass</span></summary>
  <div class='case-body'>
    {_paragraph('Description', case.get('description'))}
    {_paragraph('User Input', case.get('user_input'))}
    {_list_block('Ground Truth', case.get('ground_truth', case.get('expectation', '')))}
    {''.join(_render_cell(cell) for cell in sorted(cells, key=_cell_rank))}
  </div>
</details>"""


def _render_cell(cell: dict[str, Any]) -> str:
    status = str(cell.get("status") or "unknown")
    reason = str(cell.get("reason") or "")
    message = str(cell.get("message") or "")
    changed = cell.get("changed_files") if isinstance(cell.get("changed_files"), list) else []
    return f"""<article class='target-card'>
  <div class='target-head'><strong>{_escape(cell.get('target_id', 'target'))}</strong><span class='badge {_status_class(status)}'>{_escape(_label(status))}</span></div>
  <div class='target-body'>
    {_render_cell_summary(cell)}
    <p class='meta'>{_escape(reason or 'no reason')} {('(reused exact match)' if cell.get('reused_exact_match') else '')}</p>
    {_paragraph('Message', message)}
    {_render_checks(cell.get('deterministic_checks'))}
    {_list_block('Changed Files', changed)}
  </div>
</article>"""


def _render_cell_summary(cell: dict[str, Any]) -> str:
    changed = cell.get("changed_files") if isinstance(cell.get("changed_files"), list) else []
    bits = [
        f"<span class='pill'>{len(changed)} changed files</span>",
    ]
    if cell.get("reused_exact_match"):
        bits.append("<span class='pill'>reused exact match</span>")
    if cell.get("duration_seconds") is not None:
        bits.append(f"<span class='pill'>{_escape(_seconds(cell.get('duration_seconds')))}</span>")
    return f"<div class='target-summary'>{''.join(bits)}</div>"


def _render_checks(checks: Any) -> str:
    if not isinstance(checks, list):
        return ""
    items = []
    for check in checks:
        if not isinstance(check, dict):
            continue
        status = "pass" if check.get("pass") else "fail"
        items.append(f"<li><span class='badge {_status_class(status)}'>{_escape(status)}</span> <strong>{_escape(check.get('name', 'check'))}</strong> <span class='meta'>{_escape(check.get('observed', ''))}</span></li>")
    return f"<h4>Deterministic checks</h4><ul>{''.join(items)}</ul>" if items else ""


def _paragraph(label: str, value: Any) -> str:
    if value in (None, "", []):
        return ""
    return f"<h3>{_escape(label)}</h3><p>{_escape(value)}</p>"


def _list_block(label: str, value: Any) -> str:
    if value in (None, "", []):
        return ""
    items = value if isinstance(value, list) else [value]
    return f"<h3>{_escape(label)}</h3><ul>{''.join(f'<li>{_escape(item)}</li>' for item in items)}</ul>"


def _details(label: str, value: Any) -> str:
    if value in (None, "", [], {}):
        return ""
    text = value if isinstance(value, str) else json.dumps(value, indent=2, sort_keys=True)
    return f"<details class='evidence'><summary>{_escape(label)}</summary><pre>{_escape(text)}</pre></details>"


def _case(row: dict[str, Any]) -> dict[str, Any]:
    case = row.get("case", row); return case if isinstance(case, dict) else {}


def _cells(row: dict[str, Any]) -> list[dict[str, Any]]:
    cells = row.get("targets", row.get("cells", []))
    return [cell for cell in cells if isinstance(cell, dict)] if isinstance(cells, list) else []


def _group_status(cells: list[dict[str, Any]]) -> str:
    return min((str(cell.get("status") or "unknown") for cell in cells), key=lambda status: STATUS_ORDER.get(status, 9), default="unknown")


def _group_rank(group: dict[str, Any]) -> int: return STATUS_ORDER.get(_group_status(_cells(group)), 9)


def _cell_rank(cell: dict[str, Any]) -> int: return STATUS_ORDER.get(str(cell.get("status") or ""), 9)


def _status_class(status: str) -> str: return status if status in {"pass", "fail", "harness_error", "not_evaluated"} else "neutral"


def _label(value: Any) -> str:
    text = str(value); return STATUS_LABELS.get(text, text.replace("_", " ").title())


def _seconds(value: Any) -> str:
    return f"{float(value or 0):.1f}s"


def _number(value: Any) -> str:
    return f"{int(value or 0):,}"


def _escape(value: Any) -> str: return html.escape(str(value))

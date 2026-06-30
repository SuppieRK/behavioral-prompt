"""Self-contained HTML template for generated eval reports."""

REPORT_EMBED_MARKER = "window.__PROMPT_EVAL_REPORT__ = null;"

REPORT_VIEWER_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Prompt Eval Report</title>
  <style>
:root {
  --bg: #f3f5f7; --surface: #fff; --subtle: #f8fafb; --border: #d8dde3;
  --text: #18202a; --muted: #657180; --accent: #1261a0;
  --pass: #147a4d; --pass-bg: #e8f5ee; --fail: #b42318; --fail-bg: #fcebea;
  --warn: #8a5a00; --unknown: #596579;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text); line-height: 1.45; }
button, input { font: inherit; }
h1, h2, h3, p { margin-top: 0; }
h1 { margin-bottom: 0; font-size: 22px; }
h2 { margin-bottom: 4px; font-size: 20px; }
h3 { margin-bottom: 10px; font-size: 15px; }
.topbar { display: flex; align-items: center; justify-content: space-between; gap: 24px; padding: 18px max(24px, calc((100vw - 1440px) / 2)); background: #152331; color: #fff; }
.eyebrow { margin-bottom: 3px; color: #5d86a5; font-size: 11px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
.topbar .eyebrow { color: #8fb9d8; }
main { width: min(1440px, 100%); margin: 0 auto; padding: 24px; }
.file-button { display: inline-flex; align-items: center; min-height: 38px; padding: 8px 14px; border: 1px solid #7893aa; border-radius: 6px; background: #fff; color: #152331; cursor: pointer; font-weight: 700; }
.file-button input { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0, 0, 0, 0); }
.drop-zone { display: flex; flex-direction: column; align-items: center; gap: 4px; margin-bottom: 18px; padding: 18px; border: 1px dashed #9aa7b5; border-radius: 6px; background: var(--surface); color: var(--muted); text-align: center; }
.drop-zone strong { color: var(--text); }
.drop-zone.dragging { border-color: var(--accent); background: #edf6fc; }
body.embedded .file-button, body.embedded .drop-zone { display: none; }
.message { padding: 20px; border: 1px solid var(--border); border-radius: 6px; background: var(--surface); color: var(--muted); }
.message.error { border-color: #e8a09a; background: var(--fail-bg); color: var(--fail); }
.report-heading, .section-heading, .heading-line, .results-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.report-heading { margin-bottom: 18px; }
.heading-line { justify-content: flex-start; }
.muted { color: var(--muted); }
.promotion { max-width: 420px; font-size: 13px; text-align: right; }
.metric-grid { display: grid; grid-template-columns: repeat(6, minmax(120px, 1fr)); gap: 10px; margin-bottom: 18px; }
.metric-grid.compact { grid-template-columns: repeat(5, minmax(130px, 1fr)); }
.metric { min-height: 78px; padding: 12px; border: 1px solid var(--border); border-radius: 6px; background: var(--surface); }
.metric-label { display: block; margin-bottom: 5px; color: var(--muted); font-size: 12px; }
.metric-value { display: block; font-size: 21px; font-weight: 750; overflow-wrap: anywhere; }
.metric-note { display: block; margin-top: 3px; color: var(--muted); font-size: 11px; }
.panel { margin-bottom: 18px; padding: 16px; border: 1px solid var(--border); border-radius: 6px; background: var(--surface); }
.split { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 18px; }
.rank-list, .anomaly-list, .check-list, .result-list { display: grid; gap: 6px; }
.rank-row, .anomaly { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 12px; padding: 8px 10px; border: 1px solid var(--border); border-radius: 5px; background: var(--subtle); font-size: 13px; }
.anomaly { grid-template-columns: 180px minmax(0, 1fr); }
.badge { display: inline-flex; align-items: center; width: fit-content; padding: 3px 8px; border-radius: 999px; background: var(--unknown); color: #fff; font-size: 11px; font-weight: 750; text-transform: uppercase; }
.badge.pass { background: var(--pass); }
.badge.fail { background: var(--fail); }
.badge.warning { background: var(--warn); }
.badge.neutral { background: #e7ebef; color: #44505f; text-transform: none; }
.filters { display: flex; flex-wrap: wrap; gap: 6px; }
.filter { padding: 6px 10px; border: 1px solid var(--border); border-radius: 5px; background: var(--surface); color: var(--text); cursor: pointer; }
.filter.active { border-color: var(--accent); background: #eaf4fb; color: #0d4f82; }
.result-list { gap: 8px; margin-top: 14px; }
.result { border: 1px solid var(--border); border-radius: 6px; overflow: hidden; }
.result[data-freshness="stale"] { border-style: dashed; opacity: .78; }
.result-summary { display: grid; grid-template-columns: 12px minmax(220px, 1fr) auto auto 20px; align-items: center; gap: 12px; width: 100%; padding: 11px 12px; border: 0; background: var(--surface); color: inherit; cursor: pointer; text-align: left; }
.result-summary:hover { background: var(--subtle); }
.status-dot { width: 9px; height: 9px; border-radius: 50%; background: var(--unknown); }
.result[data-status="pass"] .status-dot { background: var(--pass); }
.result[data-status="fail"] .status-dot { background: var(--fail); }
.result-identity { display: flex; flex-direction: column; min-width: 0; }
.result-id { font-size: 12px; }
.result-detail { padding: 16px; border-top: 1px solid var(--border); background: var(--subtle); }
.detail-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.detail-section { min-width: 0; padding: 12px; border: 1px solid var(--border); border-radius: 5px; background: var(--surface); }
.detail-section.full { grid-column: 1 / -1; }
.check { padding: 8px; border-left: 3px solid var(--fail); background: var(--fail-bg); font-size: 13px; }
.check.pass { border-left-color: var(--pass); background: var(--pass-bg); }
pre { max-height: 440px; margin: 0; padding: 10px; overflow: auto; border-radius: 4px; background: #111a23; color: #e5edf4; font: 12px/1.5 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; white-space: pre-wrap; overflow-wrap: anywhere; }
.empty-inline { color: var(--muted); font-size: 13px; }
@media (max-width: 1000px) { .metric-grid, .metric-grid.compact { grid-template-columns: repeat(3, minmax(120px, 1fr)); } }
@media (max-width: 720px) {
  .topbar, .report-heading, .results-heading { align-items: flex-start; flex-direction: column; }
  main { padding: 14px; }
  .metric-grid, .metric-grid.compact, .split, .detail-grid { grid-template-columns: 1fr; }
  .result-summary { grid-template-columns: 12px minmax(0, 1fr) 20px; }
  .result-category, .result-duration { display: none; }
  .promotion { text-align: left; }
}

  </style>
</head>
<body>
  <header class="topbar">
    <div><p class="eyebrow">Prompt evaluation</p><h1>Report viewer</h1></div>
    <label class="file-button">Open report.json<input id="report-file" type="file" accept=".json,application/json"></label>
  </header>
  <main>
    <section id="drop-zone" class="drop-zone">
      <strong>Drop an aggregate or case report here</strong>
      <span>Reports stay in this browser and are not uploaded.</span>
    </section>
    <section id="error-panel" class="message error" hidden></section>
    <section id="empty-state" class="message">Open a report to review status, performance, checks, evidence, and diffs.</section>
    <div id="report" hidden>
      <section class="report-heading">
        <div>
          <div class="heading-line"><h2 id="target-title"></h2><span id="run-status" class="badge"></span></div>
          <p id="report-meta" class="muted"></p>
        </div>
        <div id="promotion-status" class="promotion"></div>
      </section>
      <section id="summary-grid" class="metric-grid"></section>
      <section class="panel">
        <div class="section-heading"><div><p class="eyebrow">Performance</p><h2>Execution profile</h2></div></div>
        <div id="performance-grid" class="metric-grid compact"></div>
        <div class="split">
          <div><h3>Slowest cases</h3><div id="slowest-cases" class="rank-list"></div></div>
          <div><h3>Highest token cases</h3><div id="token-cases" class="rank-list"></div></div>
        </div>
      </section>
      <section id="anomaly-panel" class="panel" hidden>
        <div class="section-heading">
          <div><p class="eyebrow">Diagnostics</p><h2>Anomaly warnings</h2></div>
          <span id="anomaly-count" class="badge warning"></span>
        </div>
        <div id="anomaly-list" class="anomaly-list"></div>
      </section>
      <section class="panel">
        <div class="section-heading results-heading">
          <div><p class="eyebrow">Cases</p><h2>Results</h2></div>
          <div class="filters" role="group" aria-label="Result filters">
            <button type="button" class="filter active" data-filter="all">All</button>
            <button type="button" class="filter" data-filter="fail">Failed</button>
            <button type="button" class="filter" data-filter="pass">Passed</button>
            <button type="button" class="filter" data-filter="not_evaluated">Not evaluated</button>
            <button type="button" class="filter" data-filter="current">Current run</button>
            <button type="button" class="filter" data-filter="stale">Stale</button>
          </div>
        </div>
        <div id="result-list" class="result-list"></div>
      </section>
    </div>
  </main>
  <template id="result-template">
    <article class="result">
      <button type="button" class="result-summary" aria-expanded="false">
        <span class="status-dot"></span>
        <span class="result-identity"><strong class="result-name"></strong><span class="result-id muted"></span></span>
        <span class="result-category badge neutral"></span>
        <span class="result-duration muted"></span>
        <span class="chevron" aria-hidden="true">+</span>
      </button>
      <div class="result-detail" hidden></div>
    </article>
  </template>
  <script>window.__PROMPT_EVAL_REPORT__ = null;</script>
  <script>
(function () {
  "use strict";
  const state = { report: null, filter: "all" };
  const elements = {};
  const byId = (id) => document.getElementById(id);

  function get(object, path, fallback = null) {
    let value = object;
    for (const key of path.split(".")) {
      if (value === null || value === undefined || typeof value !== "object") return fallback;
      value = value[key];
    }
    return value === undefined || value === null ? fallback : value;
  }
  function number(value, digits = 0) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return "n/a";
    return new Intl.NumberFormat(undefined, { maximumFractionDigits: digits }).format(Number(value));
  }
  function seconds(value) {
    if (value === null || value === undefined) return "n/a";
    const numeric = Number(value);
    return numeric >= 60 ? `${number(numeric / 60, 1)} min` : `${number(numeric, 1)} s`;
  }
  function bytes(value) {
    if (value === null || value === undefined) return "n/a";
    let numeric = Number(value);
    const units = ["B", "KiB", "MiB", "GiB"];
    let unit = 0;
    while (numeric >= 1024 && unit < units.length - 1) { numeric /= 1024; unit += 1; }
    return `${number(numeric, unit === 0 ? 0 : 1)} ${units[unit]}`;
  }
  const text = (value) => value === null || value === undefined || value === "" ? "n/a" : String(value);
  function statusClass(status) {
    if (status === "pass" || status === "completed") return "pass";
    if (status === "fail") return "fail";
    if (status === "in_progress") return "warning";
    return "";
  }
  function metric(label, value, note = "") {
    const node = document.createElement("div");
    node.className = "metric";
    node.innerHTML = `<span class="metric-label"></span><strong class="metric-value"></strong>`;
    node.querySelector(".metric-label").textContent = label;
    node.querySelector(".metric-value").textContent = value;
    if (note) {
      const noteNode = document.createElement("span");
      noteNode.className = "metric-note";
      noteNode.textContent = note;
      node.append(noteNode);
    }
    return node;
  }
  function renderMetrics(container, items) { container.replaceChildren(...items.map((item) => metric(...item))); }
  function renderHeader(report) {
    const target = report.target || {};
    const runStatus = get(report, "run.status", "completed");
    elements.targetTitle.textContent = `${text(target.name)} / ${text(target.model)}`;
    elements.runStatus.textContent = runStatus.replace("_", " ");
    elements.runStatus.className = `badge ${statusClass(runStatus)}`;
    const created = report.created_at ? new Date(report.created_at).toLocaleString() : "unknown time";
    const runId = get(report, "run.id");
    elements.reportMeta.textContent = [target.harness, target.reasoning ? `${target.reasoning} reasoning` : null, runId ? `run ${runId}` : null, created, report.schema].filter(Boolean).join(" | ");
    const promotion = report.promotion || {};
    elements.promotionStatus.textContent = promotion.reason || (promotion.eligible ? "Eligible for promotion" : "Not eligible for promotion");
    elements.promotionStatus.style.color = promotion.eligible ? "var(--pass)" : "var(--muted)";
  }
  function renderSummary(report) {
    const summary = report.summary || {};
    const current = summary.current || summary;
    const stale = summary.stale || {};
    const completed = get(report, "run.completed_total", summary.total || 0);
    const selected = get(report, "run.selected_total", summary.total || completed);
    renderMetrics(elements.summaryGrid, [
      ["Current completed", `${number(completed)} / ${number(selected)}`], ["Current passed", number(current.pass || 0)],
      ["Current failed", number(current.fail || 0)], ["Current pending", number(summary.pending || 0)],
      ["Stale available", number(stale.total || 0)], ["Missing", number(summary.missing || 0)],
    ]);
  }
  function renderRanking(container, items, valueKey, formatter) {
    if (!items.length) { container.innerHTML = '<span class="empty-inline">No aggregate data available.</span>'; return; }
    container.replaceChildren(...items.map((item) => {
      const row = document.createElement("div");
      row.className = "rank-row";
      const name = document.createElement("span"); name.textContent = item.case_id || "unknown";
      const value = document.createElement("strong"); value.textContent = formatter(item[valueKey]);
      row.append(name, value); return row;
    }));
  }
  function renderPerformance(report) {
    const performance = report.performance || {};
    const latest = get(report, "run.latest_invocation_performance", {});
    const usage = performance.target_usage || {};
    const promptMetrics = get(report, "prompt.metrics", {});
    const responseLength = performance.response_length || {};
    const parallel = performance.agent_parallelism || {};
    const latestParallel = latest.agent_parallelism || {};
    const judge = latest.judge || performance.judge || {};
    const planning = report.planning || {};
    const nativePlanning = planning.native_planning || {};
    const artifactPlanning = planning.artifact_planning || {};
    renderMetrics(elements.performanceGrid, [
      ["Cases aggregated", number(performance.source_case_count)],
      ["Cumulative service", seconds(performance.cumulative_service_seconds)],
      ["Latest wall time", seconds(latest.wall_seconds ?? performance.wall_seconds)],
      ["Latest throughput", latest.throughput_cases_per_second == null ? "n/a" : `${number(latest.throughput_cases_per_second * 60, 2)} cases/min`],
      ["Latest agent jobs", number(latest.configured_agent_jobs ?? performance.configured_agent_jobs)],
      ["Latest peak concurrency", number(latestParallel.peak_concurrency ?? parallel.peak_concurrency)],
      ["Latest parallel efficiency", latestParallel.parallel_efficiency == null ? "n/a" : `${number(latestParallel.parallel_efficiency * 100, 1)}%`],
      ["Prompt bytes", number(promptMetrics.bytes)], ["Prompt est. tokens", number(promptMetrics.estimated_tokens), promptMetrics.token_estimate_method || ""],
      ["Output tokens", number(usage.output_tokens)], ["Response est. tokens", number(get(responseLength, "estimated_tokens.total")), get(responseLength, "estimated_tokens.method", "")],
      ["Response words", number(get(responseLength, "words.total"))],
      ["Uncached tokens", number(usage.uncached_tokens)], ["Total tokens", number(usage.total_tokens)],
      ["Cache read", number(usage.cache_read_tokens)], ["Judge queue max", number(judge.peak_queue_depth)],
      ["Peak memory", bytes(get(performance, "agent_process.peak_rss_bytes"))],
      ["Native plan cases", number(nativePlanning.case_count)], ["Plan lifecycles", number(nativePlanning.completed_lifecycle_count)],
      ["Artifact plan cases", number(artifactPlanning.case_count)],
    ]);
    renderRanking(elements.slowestCases, performance.slowest_cases || [], "service_seconds", seconds);
    renderRanking(elements.tokenCases, performance.highest_token_cases || [], "total_tokens", number);
  }
  function renderAnomalies(report) {
    const anomalies = get(report, "performance.anomalies", {});
    const cases = anomalies.cases || [];
    elements.anomalyPanel.hidden = cases.length === 0;
    elements.anomalyCount.textContent = `${number(anomalies.case_count ?? cases.length)} cases`;
    elements.anomalyList.replaceChildren(...cases.flatMap((item) => (item.warnings || []).map((warning) => {
      const row = document.createElement("div"); row.className = "anomaly";
      const caseName = document.createElement("strong"); caseName.textContent = item.case_id;
      const message = document.createElement("span"); message.textContent = warning.message || `${warning.metric}: ${warning.value}`;
      row.append(caseName, message); return row;
    })));
  }
  function detailSection(title, content, full = false) {
    const section = document.createElement("section"); section.className = `detail-section${full ? " full" : ""}`;
    const heading = document.createElement("h3"); heading.textContent = title; section.append(heading);
    if (content instanceof Node) section.append(content);
    else if (content) { const pre = document.createElement("pre"); pre.textContent = typeof content === "string" ? content : JSON.stringify(content, null, 2); section.append(pre); }
    else { const empty = document.createElement("span"); empty.className = "empty-inline"; empty.textContent = "No data captured."; section.append(empty); }
    return section;
  }
  function renderChecks(checks) {
    const list = document.createElement("div"); list.className = "check-list";
    if (!checks || !checks.length) { list.innerHTML = '<span class="empty-inline">No deterministic checks.</span>'; return list; }
    for (const check of checks) {
      const node = document.createElement("div"); node.className = `check${check.pass ? " pass" : ""}`;
      const name = document.createElement("strong"); name.textContent = `${check.pass ? "PASS" : "FAIL"}: ${check.name}`;
      const reason = document.createElement("div"); reason.textContent = check.reason || "";
      node.append(name, reason); list.append(node);
    }
    return list;
  }
  function renderCaseDetail(result) {
    const evidence = result.evidence || {};
    const detail = document.createElement("div"); detail.className = "detail-grid";
    detail.append(
      detailSection("Outcome", { status: result.status, report_state: result.report_state, report_run_id: result.report_run_id, stale_reason: result.stale_reason, reason: result.reason, critical: result.critical, checks: result.checks, tags: result.tags }),
      detailSection("Case performance", result.performance),
      detailSection("Deterministic checks", renderChecks(result.deterministic_checks), true),
      detailSection("Judge", result.judge, true), detailSection("Final response", evidence.final_response, true),
      detailSection("Changed files", evidence.changed_files), detailSection("Commands", evidence.commands),
      detailSection("Diff", evidence.diff, true), detailSection("Timeline", evidence.timeline, true),
      detailSection("Tool calls", evidence.tool_calls, true),
      detailSection("Durable context", { capability: evidence.planning_capability, actions: evidence.durable_context_actions }, true),
      detailSection("Harness and prompt", { harness_error: evidence.harness_error, harness_isolation: evidence.harness_isolation, prompt_injection: evidence.prompt_injection, cleanup_actions: evidence.cleanup_actions }, true),
    );
    return detail;
  }
  function renderResults(report) {
    const results = report.results || [];
    const visible = state.filter === "all" ? results : results.filter((result) => (
      state.filter === "current" || state.filter === "stale"
        ? result.report_state === state.filter
        : result.status === state.filter
    ));
    if (!visible.length) { elements.resultList.innerHTML = '<span class="empty-inline">No cases match this filter.</span>'; return; }
    const fragment = document.createDocumentFragment();
    for (const result of visible) {
      const node = elements.resultTemplate.content.firstElementChild.cloneNode(true);
      node.dataset.status = result.status || "unknown";
      node.dataset.freshness = result.report_state || "current";
      node.querySelector(".result-name").textContent = result.name || result.case_id;
      node.querySelector(".result-id").textContent = `${result.case_id || "unknown"} | ${result.report_state || "current"}`;
      node.querySelector(".result-category").textContent = result.category || "uncategorized";
      node.querySelector(".result-duration").textContent = seconds(
        get(result, "performance.phases.total_seconds", get(result, "performance.durations_seconds.total")),
      );
      const button = node.querySelector(".result-summary"); const detail = node.querySelector(".result-detail");
      button.addEventListener("click", () => {
        const expanded = button.getAttribute("aria-expanded") === "true";
        button.setAttribute("aria-expanded", String(!expanded)); button.querySelector(".chevron").textContent = expanded ? "+" : "-";
        if (!expanded && !detail.childElementCount) detail.append(renderCaseDetail(result));
        detail.hidden = expanded;
      });
      fragment.append(node);
    }
    elements.resultList.replaceChildren(fragment);
  }
  function validateReport(report) {
    if (!report || typeof report !== "object" || !Array.isArray(report.results)) throw new Error("This file does not look like a prompt eval report: results[] is missing.");
  }
  function renderReport(report) {
    validateReport(report); state.report = report; elements.errorPanel.hidden = true; elements.emptyState.hidden = true; elements.report.hidden = false;
    renderHeader(report); renderSummary(report); renderPerformance(report); renderAnomalies(report); renderResults(report);
  }
  function showError(error) { elements.errorPanel.textContent = error instanceof Error ? error.message : String(error); elements.errorPanel.hidden = false; }
  async function loadFile(file) { try { renderReport(JSON.parse(await file.text())); } catch (error) { showError(error); } }
  async function loadUrl(url) {
    try { const response = await fetch(url); if (!response.ok) throw new Error(`Could not load ${url}: HTTP ${response.status}`); renderReport(await response.json()); }
    catch (error) { showError(error); }
  }
  function initialize() {
    if (window.__PROMPT_EVAL_REPORT__) document.body.classList.add("embedded");
    for (const id of ["report-file", "drop-zone", "error-panel", "empty-state", "report", "target-title", "run-status", "report-meta", "promotion-status", "summary-grid", "performance-grid", "slowest-cases", "token-cases", "anomaly-panel", "anomaly-count", "anomaly-list", "result-list", "result-template"]) elements[id.replace(/-([a-z])/g, (_, letter) => letter.toUpperCase())] = byId(id);
    elements.fileInput = elements.reportFile;
    elements.fileInput.addEventListener("change", () => elements.fileInput.files[0] && loadFile(elements.fileInput.files[0]));
    for (const name of ["dragenter", "dragover"]) elements.dropZone.addEventListener(name, (event) => { event.preventDefault(); elements.dropZone.classList.add("dragging"); });
    for (const name of ["dragleave", "drop"]) elements.dropZone.addEventListener(name, (event) => { event.preventDefault(); elements.dropZone.classList.remove("dragging"); });
    elements.dropZone.addEventListener("drop", (event) => event.dataTransfer.files[0] && loadFile(event.dataTransfer.files[0]));
    document.querySelectorAll(".filter").forEach((button) => button.addEventListener("click", () => {
      state.filter = button.dataset.filter;
      document.querySelectorAll(".filter").forEach((item) => item.classList.toggle("active", item === button));
      renderResults(state.report);
    }));
    const reportUrl = new URLSearchParams(window.location.search).get("report");
    if (window.__PROMPT_EVAL_REPORT__) renderReport(window.__PROMPT_EVAL_REPORT__);
    else if (reportUrl) loadUrl(reportUrl);
  }
  window.ReportViewer = { renderReport, validateReport, format: { number, seconds, bytes } };
  document.addEventListener("DOMContentLoaded", initialize);
}());

  </script>
</body>
</html>
"""

const state = {
  payload: window.AGENT_TRACE_DEMO_DATA || { schema_version: "agent-trace-v1", traces: [] },
  traceIndex: 0,
  selectedSpanId: null,
};

const metricGrid = document.getElementById("metricGrid");
const traceList = document.getElementById("traceList");
const treeRoot = document.getElementById("treeRoot");
const detailBody = document.getElementById("detailBody");
const issueList = document.getElementById("issueList");
const datasetMeta = document.getElementById("datasetMeta");
const activeTraceMeta = document.getElementById("activeTraceMeta");
const statusLegend = document.getElementById("statusLegend");
const fileInput = document.getElementById("fileInput");

function currentTrace() {
  return state.payload.traces?.[state.traceIndex] || null;
}

function render() {
  const trace = currentTrace();
  datasetMeta.textContent = `${state.payload.schema_version || "agent-trace-v1"} · ${
    state.payload.generated_at || "local"
  }`;

  renderMetrics(trace);
  renderTraceList();
  renderLegend();

  if (!trace) {
    activeTraceMeta.textContent = "";
    treeRoot.innerHTML = `<div class="muted">No trace data</div>`;
    detailBody.innerHTML = "";
    issueList.innerHTML = "";
    return;
  }

  if (!state.selectedSpanId && trace.spans?.length) {
    state.selectedSpanId = trace.spans[0].id;
  }

  activeTraceMeta.textContent = `${trace.trace.id} · ${formatMs(trace.summary.duration_ms)} · ${
    trace.summary.total_tokens
  } tokens`;
  treeRoot.innerHTML = "";
  for (const root of trace.tree || []) {
    treeRoot.appendChild(renderSpan(root));
  }
  renderIssues(trace);
  renderDetail(trace);
}

function renderMetrics(trace) {
  const summary = trace?.summary || {};
  const items = [
    ["Traces", state.payload.traces?.length || 0],
    ["Spans", summary.span_count || 0],
    ["Tools", summary.tool_count || 0],
    ["Errors", summary.error_count || 0],
    ["Latency", formatMs(summary.duration_ms || 0)],
    ["Tokens", summary.total_tokens || 0],
  ];

  metricGrid.innerHTML = items
    .map(
      ([label, value]) => `
      <article class="metric-card">
        <div class="metric-label">${label}</div>
        <div class="metric-value">${value}</div>
      </article>
    `
    )
    .join("");
}

function renderTraceList() {
  traceList.innerHTML = "";
  (state.payload.traces || []).forEach((trace, index) => {
    const button = document.createElement("button");
    button.className = `trace-item ${index === state.traceIndex ? "active" : ""}`;
    button.type = "button";
    button.innerHTML = `
      <div class="trace-id">${escapeHtml(trace.trace.id)}</div>
      <div class="trace-sub">${trace.summary.span_count} spans · ${trace.summary.error_count} errors</div>
    `;
    button.addEventListener("click", () => {
      state.traceIndex = index;
      state.selectedSpanId = trace.spans?.[0]?.id || null;
      render();
    });
    traceList.appendChild(button);
  });
}

function renderLegend() {
  statusLegend.innerHTML = `
    <span class="legend-pill ok">ok</span>
    <span class="legend-pill warning">warning</span>
    <span class="legend-pill error">error</span>
  `;
}

function renderSpan(span) {
  const node = document.createElement("div");
  node.className = "span-node";

  const row = document.createElement("div");
  row.className = `span-row ${span.status === "error" ? "error" : ""} ${
    state.selectedSpanId === span.id ? "selected" : ""
  }`;
  row.tabIndex = 0;
  row.innerHTML = `
    <div class="span-kind">${escapeHtml(span.kind)}</div>
    <div class="span-name">${escapeHtml(span.name)}</div>
    <div class="span-metric">${formatMs(span.duration_ms)}</div>
    <span class="badge ${span.status === "error" ? "error" : "ok"}">${escapeHtml(span.status)}</span>
  `;
  row.addEventListener("click", () => selectSpan(span.id));
  row.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      selectSpan(span.id);
    }
  });

  node.appendChild(row);
  if (span.children?.length) {
    const children = document.createElement("div");
    children.className = "children";
    for (const child of span.children) {
      children.appendChild(renderSpan(child));
    }
    node.appendChild(children);
  }
  return node;
}

function selectSpan(spanId) {
  state.selectedSpanId = spanId;
  render();
  const selected = document.querySelector(".span-row.selected");
  selected?.scrollIntoView({ block: "nearest", behavior: "smooth" });
}

function renderIssues(trace) {
  const issues = trace.issues || [];
  if (!issues.length) {
    issueList.innerHTML = `<div class="muted">No issues</div>`;
    return;
  }

  issueList.innerHTML = "";
  for (const issue of issues) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `issue-item ${issue.severity}`;
    button.innerHTML = `
      <span class="badge ${issue.severity}">${escapeHtml(issue.severity)}</span>
      <span class="issue-message">${escapeHtml(issue.message)}</span>
      <span class="issue-span">${escapeHtml(issue.span_id || "trace")}</span>
    `;
    if (issue.span_id) {
      button.addEventListener("click", () => selectSpan(issue.span_id));
    }
    issueList.appendChild(button);
  }
}

function renderDetail(trace) {
  const span = findSpan(trace.tree || [], state.selectedSpanId);
  if (!span) {
    detailBody.innerHTML = `<div class="muted">Select a span</div>`;
    return;
  }

  detailBody.innerHTML = `
    <div class="detail-kv"><span>ID</span><strong>${escapeHtml(span.id)}</strong></div>
    <div class="detail-kv"><span>Kind</span><strong>${escapeHtml(span.kind)}</strong></div>
    <div class="detail-kv"><span>Status</span><strong>${escapeHtml(span.status)}</strong></div>
    <div class="detail-kv"><span>Duration</span><strong>${formatMs(span.duration_ms)}</strong></div>
    <div class="detail-kv"><span>Tokens</span><strong>${span.tokens?.total || 0}</strong></div>
    <pre>${escapeHtml(
      JSON.stringify(
        {
          input: span.input,
          output: span.output,
          tool: span.tool,
          events: span.events,
          attributes: span.attributes,
        },
        null,
        2
      )
    )}</pre>
  `;
}

function findSpan(nodes, id) {
  for (const node of nodes) {
    if (node.id === id) return node;
    const child = findSpan(node.children || [], id);
    if (child) return child;
  }
  return null;
}

function formatMs(value) {
  const number = Number(value || 0);
  if (number >= 1000) return `${(number / 1000).toFixed(2)}s`;
  return `${Math.round(number)}ms`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

fileInput.addEventListener("change", async (event) => {
  const [file] = event.target.files || [];
  if (!file) return;
  const text = await file.text();
  const parsed = JSON.parse(text);
  state.payload = parsed.traces ? parsed : { schema_version: "agent-trace-v1", traces: [parsed] };
  state.traceIndex = 0;
  state.selectedSpanId = null;
  render();
});

render();

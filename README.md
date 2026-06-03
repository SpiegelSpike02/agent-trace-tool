# Agent Trace Tool

A lightweight Agent observability and evaluation harness.

It parses JSONL execution logs into a `Trace -> Span -> Event` tree, highlights tool errors, latency and token-cost issues, exports dashboard-ready JSON, and evaluates traces against deterministic case specs.

This is intentionally small and reproducible. It is not a production observability platform and does not depend on private company data.

## Features

- JSONL parser for Agent execution events
- `Trace`, `Span`, `SpanEvent`, `ToolCall` and `TokenUsage` data models
- CLI tree rendering for quick debugging
- JSON / JavaScript payload export for static dashboards
- Static dashboard demo
- Rule-based analysis for failed tools, missing span ends, orphan spans, high latency and high token usage
- Evaluation case runner for deterministic CI checks

## Install

```bash
uv sync
```

## Run Tests

```bash
uv run pytest -q
```

## Parse a Trace

```bash
uv run agent-trace-tool parse examples/sample_trace.jsonl --tree
```

Backwards-compatible form:

```bash
uv run agent-trace-tool examples/sample_trace.jsonl --tree
```

Example output:

```text
Trace trace-week4-001 | spans=5 | duration=9050ms
- [agent] CourseworkAgent.run (span-agent-root) 8880ms, tokens=2526
  - [llm] LLM.plan (span-plan-llm) 920ms, tokens=776
  ! [tool] tool.search_docs (span-search-tool) 3500ms
  - [tool] tool.read_cache (span-cache-tool) 530ms
  - [llm] LLM.final_answer (span-final-llm) 2650ms, tokens=1750
```

## Evaluate a Trace

```bash
uv run agent-trace-tool evaluate examples/sample_trace.jsonl --cases examples/eval_cases.json
```

The sample case allows one known tool error and checks token, duration and required-tool constraints.

## Generate Dashboard Data

```bash
uv run agent-trace-tool parse examples/sample_trace.jsonl \
  --js-var AGENT_TRACE_DEMO_DATA \
  --out demo/data/sample_trace.js
```

Serve the static demo:

```bash
uv run python -m http.server 8000
```

Open `http://localhost:8000/demo/`.

## Event Format

The parser accepts one JSON object per line. Minimal example:

```jsonl
{"type":"trace_start","timestamp":"2026-05-06T09:00:00Z","trace_id":"trace-001","project":"demo","context":{"input":"user task"}}
{"type":"span_start","timestamp":"2026-05-06T09:00:00.100Z","trace_id":"trace-001","span_id":"agent-1","name":"Agent.run","kind":"agent"}
{"type":"tool_call","timestamp":"2026-05-06T09:00:01Z","trace_id":"trace-001","span_id":"tool-1","parent_id":"agent-1","tool":{"name":"search","arguments":{"query":"agent tracing"}}}
{"type":"tool_result","timestamp":"2026-05-06T09:00:02Z","trace_id":"trace-001","span_id":"tool-1","status":"ok","result":{"count":3}}
{"type":"span_end","timestamp":"2026-05-06T09:00:03Z","trace_id":"trace-001","span_id":"agent-1","status":"ok","tokens":{"prompt":500,"completion":120,"total":620}}
{"type":"trace_end","timestamp":"2026-05-06T09:00:03.100Z","trace_id":"trace-001"}
```

## Project Docs

- [Architecture](docs/architecture.md)
- [Public benchmarks and data sources](docs/datasets.md)

## Positioning

This project demonstrates the bottom layer of Agent debugging: reliable execution records, deterministic analysis and reproducible evaluation checks. It can be mapped toward OpenTelemetry GenAI-style spans and compared conceptually with open-source observability tools such as Arize Phoenix, but the implementation is deliberately minimal so the full pipeline is easy to inspect.

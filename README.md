# Agent Trace Tool

A lightweight Agent observability and evaluation harness.

It parses JSONL execution logs into a `Trace -> Span -> Event` tree, highlights tool errors, latency and token-cost issues, exports dashboard-ready JSON, and evaluates traces against deterministic case specs.

The mature path is built around the LangChain ecosystem:

- Agent workflow framework: [LangGraph](https://github.com/langchain-ai/langgraph)
- Experiment and tracing platform: [LangSmith](https://docs.langchain.com/langsmith/home)
- Public dataset: [llm-wizard/Product-Descriptions-and-Ads](https://huggingface.co/datasets/llm-wizard/Product-Descriptions-and-Ads)
- Task: run a LangGraph ad-generation workflow over public product/ad rows, trace/evaluate it with LangSmith, and keep a local JSONL fallback for deterministic CI.

This is intentionally small and reproducible. It is not a production observability platform and does not depend on private company data.

## Features

- JSONL parser for Agent execution events
- `Trace`, `Span`, `SpanEvent`, `ToolCall` and `TokenUsage` data models
- CLI tree rendering for quick debugging
- JSON / JavaScript payload export for static dashboards
- Static dashboard demo
- Rule-based analysis for failed tools, missing span ends, orphan spans, high latency and high token usage
- Evaluation case runner for deterministic CI checks
- LangGraph public-data harness for reproducible Agent workflow traces
- Optional LangSmith experiment runner for dataset evaluation and managed tracing

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

## Run the LangGraph Public-Data Harness

The checked-in dataset snapshot is stored at `data/product_ads_sample.json` and is derived from the Hugging Face dataset `llm-wizard/Product-Descriptions-and-Ads`.

```bash
uv run agent-trace-tool run-ad-harness \
  --data data/product_ads_sample.json \
  --limit 3 \
  --out examples/langgraph_ad_traces.jsonl
```

Inspect the generated LangGraph traces:

```bash
uv run agent-trace-tool parse examples/langgraph_ad_traces.jsonl --tree
```

Evaluate them:

```bash
uv run agent-trace-tool evaluate examples/langgraph_ad_traces.jsonl \
  --cases examples/langgraph_ad_eval_cases.json
```

## Run the Mature LangSmith Experiment Path

Set LangSmith credentials:

```bash
set LANGSMITH_TRACING=true
set LANGSMITH_API_KEY=your-api-key
```

Run the public-data LangGraph workflow as a LangSmith experiment:

```bash
uv run agent-trace-tool run-langsmith-experiment \
  --data data/product_ads_sample.json \
  --limit 3 \
  --project-name agent-trace-tool \
  --experiment-prefix public-ad-harness
```

Optionally create/update a LangSmith dataset first:

```bash
uv run agent-trace-tool run-langsmith-experiment \
  --data data/product_ads_sample.json \
  --limit 3 \
  --upload-dataset \
  --dataset-name agent-trace-tool-public-ads
```

Refresh the public dataset snapshot:

```bash
uv run --group dataset python scripts/fetch_public_ads_dataset.py \
  --out data/product_ads_sample.json \
  --limit 10
```

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
- [LangSmith experiment path](docs/langsmith.md)

## Positioning

This project demonstrates both layers of Agent debugging:

- production-style path: LangGraph + LangSmith datasets/experiments/tracing
- local reproducible path: LangGraph + JSONL traces + deterministic parser/evaluator

The local path exists to make the mechanics inspectable and CI-friendly. The LangSmith path is the more mature architecture for real monitoring and evaluation loops.

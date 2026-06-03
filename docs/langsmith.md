# LangSmith Experiment Path

The mature monitoring/evaluation loop for this project is:

```text
LangGraph workflow
  -> LangSmith tracing
  -> LangSmith dataset examples
  -> LangSmith experiment evaluators
  -> prompt/tool/route/model adjustment
  -> rerun experiment
```

The local JSONL parser is still useful because it makes the trace mechanics visible and runs without credentials. For a production-style workflow, LangSmith should own the managed traces, datasets and experiment comparison.

## What Runs

`src/agent_trace_tool/langsmith_experiment.py` defines:

- `build_langsmith_examples`: converts `data/product_ads_sample.json` into LangSmith example records.
- `predict_ad`: a `@traceable` LangGraph harness target.
- `compliance_evaluator`: checks whether the generated ad passed compliance screening.
- `structure_evaluator`: checks CTA presence, output length and reference availability.
- `run_langsmith_experiment`: runs `langsmith.evaluate` over the public examples.

## Required Environment

```bash
set LANGSMITH_TRACING=true
set LANGSMITH_API_KEY=your-api-key
```

Optional:

```bash
set LANGSMITH_PROJECT=agent-trace-tool
```

## Commands

Run an experiment directly from local examples:

```bash
uv run agent-trace-tool run-langsmith-experiment \
  --data data/product_ads_sample.json \
  --limit 3 \
  --project-name agent-trace-tool \
  --experiment-prefix public-ad-harness
```

Create/update a LangSmith dataset, then run against it:

```bash
uv run agent-trace-tool run-langsmith-experiment \
  --data data/product_ads_sample.json \
  --limit 3 \
  --upload-dataset \
  --dataset-name agent-trace-tool-public-ads
```

## Why Both LangSmith and JSONL Exist

LangSmith is the mature platform path. It gives managed traces, datasets, experiments, comparison views and evaluator history.

The JSONL path is kept for three reasons:

- CI can run without API keys.
- The trace schema is inspectable in the repository.
- The parser/analyzer/evaluator implementation demonstrates the underlying mechanics that LangSmith abstracts away.

In an interview, describe the JSONL path as a local fallback and learning scaffold, not as a replacement for LangSmith.

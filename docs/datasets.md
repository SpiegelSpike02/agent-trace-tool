# Public Benchmarks and Data Sources

This repository does not use private company data. It is designed around public Agent benchmarks and reproducible local traces.

## Agent Evaluation Benchmarks

| Source | Use in this project |
| --- | --- |
| [AgentBench](https://github.com/THUDM/AgentBench) | Reference benchmark for evaluating LLM agents across multiple environments. Useful for thinking about task success, tool use and multi-turn execution. |
| [WebArena](https://arxiv.org/abs/2307.13854) | Reference for realistic web-agent tasks in self-hosted environments. Useful for long-horizon task framing. |
| [GAIA](https://arxiv.org/abs/2311.12983) | Reference for general assistant tasks requiring reasoning and tool use. Useful for evaluation case design. |
| [AgentDojo](https://proceedings.neurips.cc/paper_files/paper/2024/file/97091a5177d8dc64b1da8bf3e1f6fb54-Paper-Datasets_and_Benchmarks_Track.pdf) | Reference for tool-use robustness and prompt-injection-aware evaluation. Useful for future safety checks. |

## Observability References

| Source | Use in this project |
| --- | --- |
| [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/) | External vocabulary for inference, retrieval and tool execution spans. |
| [Arize Phoenix](https://arize.com/docs/phoenix) | Open-source reference for LLM tracing, evaluation, datasets and experiments. |

## Advertising Case Study Data

Advertising generation is treated as a future case-study domain, not as a production claim.

Potential public datasets:

- [Product-Descriptions-and-Ads](https://huggingface.co/datasets/llm-wizard/Product-Descriptions-and-Ads/tree/main/data)
- [ADS-16 Computational Advertising Dataset](https://www.kaggle.com/datasets/groffo/ads16-dataset)
- [ADautoGen-DS](https://huggingface.co/datasets/EthanGabis/ADautoGen-DS)

These sources can provide product descriptions, ad text or ad ratings for offline experiments. They should not be described as internal ad traffic or production campaign data.

## Current Repository Data

The current checked-in sample is `examples/sample_trace.jsonl`. It is a small synthetic trace used to verify parser, analyzer, dashboard and evaluator behavior. The trace includes one intentional failed tool call so error highlighting and evaluation thresholds can be tested deterministically.

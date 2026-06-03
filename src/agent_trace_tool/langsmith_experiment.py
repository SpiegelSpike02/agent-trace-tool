"""Optional LangSmith experiment path for the LangGraph public-data harness."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from langsmith import Client, evaluate, traceable
from langsmith.run_helpers import tracing_context

from .langgraph_ad_agent import build_ad_agent_graph, load_public_ad_cases


def build_langsmith_examples(data_path: str | Path, *, limit: int = 3) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    for case in load_public_ad_cases(data_path)[:limit]:
        examples.append(
            {
                "inputs": {
                    "case_id": case["case_id"],
                    "product": case["product"],
                    "description": case["description"],
                },
                "outputs": {
                    "reference_ad": case["reference_ad"],
                },
                "metadata": {
                    "source": "llm-wizard/Product-Descriptions-and-Ads",
                    "task": "public-ad-generation",
                },
            }
        )
    return examples


@traceable(name="langgraph_public_ad_harness", run_type="chain")
def predict_ad(inputs: dict[str, Any]) -> dict[str, Any]:
    app = build_ad_agent_graph()
    state = {
        "case_id": inputs["case_id"],
        "product": inputs["product"],
        "description": inputs["description"],
        "reference_ad": "",
        "trace_id": f"langsmith-{inputs['case_id']}",
        "events": [
            {
                "type": "trace_start",
                "trace_id": f"langsmith-{inputs['case_id']}",
                "project": "langsmith-public-ad-harness",
                "context": {
                    "dataset": "llm-wizard/Product-Descriptions-and-Ads",
                    "case_id": inputs["case_id"],
                },
            }
        ],
    }
    result = app.invoke(state)
    return {
        "generated_ad": result["generated_ad"],
        "compliance_status": result["compliance_status"],
        "score": result["score"],
        "score_reason": result["score_reason"],
        "trace_event_count": len(result["events"]),
    }


def compliance_evaluator(outputs: dict[str, Any], reference_outputs: dict[str, Any]) -> dict[str, Any]:
    return {
        "key": "compliance_ok",
        "score": outputs.get("compliance_status") == "ok",
        "comment": f"status={outputs.get('compliance_status')}",
    }


def structure_evaluator(outputs: dict[str, Any], reference_outputs: dict[str, Any]) -> dict[str, Any]:
    generated = str(outputs.get("generated_ad") or "")
    reference = str(reference_outputs.get("reference_ad") or "")
    has_cta = any(term in generated.lower() for term in ["shop", "add", "discover", "try", "explore"])
    product_length_ok = 60 <= len(generated) <= 220
    reference_length_ok = len(reference) > 0
    score = sum([has_cta, product_length_ok, reference_length_ok]) / 3
    return {
        "key": "ad_structure",
        "score": score,
        "comment": f"cta={has_cta}, length_ok={product_length_ok}, reference_present={reference_length_ok}",
    }


def run_langsmith_experiment(
    data_path: str | Path,
    *,
    limit: int = 3,
    project_name: str = "agent-trace-tool",
    experiment_prefix: str = "public-ad-harness",
    upload_dataset: bool = False,
    dataset_name: str = "agent-trace-tool-public-ads",
) -> Any:
    _require_langsmith_key()
    examples = build_langsmith_examples(data_path, limit=limit)

    if upload_dataset:
        client = Client()
        _create_or_update_dataset(client, dataset_name, examples)
        data: Any = dataset_name
    else:
        data = examples

    with tracing_context(
        project_name=project_name,
        tags=["langgraph", "public-dataset", "agent-evaluation"],
        metadata={"dataset": "llm-wizard/Product-Descriptions-and-Ads", "limit": limit},
        enabled=True,
    ):
        return evaluate(
            predict_ad,
            data=data,
            evaluators=[compliance_evaluator, structure_evaluator],
            experiment_prefix=experiment_prefix,
            description="LangGraph public advertising harness with compliance and structure evaluators.",
            metadata={
                "agent_framework": "LangGraph",
                "dataset": "llm-wizard/Product-Descriptions-and-Ads",
            },
        )


def _create_or_update_dataset(client: Client, dataset_name: str, examples: list[dict[str, Any]]) -> None:
    try:
        client.create_dataset(
            dataset_name,
            description="Public product/ad copy examples for the agent-trace-tool LangGraph harness.",
            metadata={"source": "llm-wizard/Product-Descriptions-and-Ads"},
        )
    except Exception:
        # LangSmith raises if the dataset already exists. Existing datasets can still receive examples.
        pass
    client.create_examples(dataset_name=dataset_name, examples=examples)


def _require_langsmith_key() -> None:
    if not os.getenv("LANGSMITH_API_KEY"):
        raise RuntimeError(
            "LANGSMITH_API_KEY is required. Set LANGSMITH_TRACING=true and LANGSMITH_API_KEY before running."
        )

"""LangGraph-based ad generation harness over a public product ads dataset."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, TypedDict
from uuid import uuid4

from langgraph.graph import END, StateGraph


class AdAgentState(TypedDict, total=False):
    case_id: str
    product: str
    description: str
    reference_ad: str
    audience: str
    strategy: str
    generated_ad: str
    compliance_status: str
    compliance_notes: list[str]
    score: int
    score_reason: str
    trace_id: str
    events: list[dict[str, Any]]


def load_public_ad_cases(path: str | Path) -> list[dict[str, str]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    records = payload["records"] if isinstance(payload, dict) else payload
    return [
        {
            "case_id": f"product-ad-{index + 1:03d}",
            "product": str(record["product"]).strip(),
            "description": str(record["description"]).strip(),
            "reference_ad": str(record["ad"]).strip(),
        }
        for index, record in enumerate(records)
    ]


def build_ad_agent_graph():
    graph = StateGraph(AdAgentState)
    graph.add_node("parse_brief", _instrument("parse_brief", _parse_brief, kind="agent"))
    graph.add_node("plan_strategy", _instrument("plan_strategy", _plan_strategy, kind="agent"))
    graph.add_node("generate_ad", _instrument("generate_ad", _generate_ad, kind="llm"))
    graph.add_node("compliance_check", _instrument("compliance_check", _compliance_check, kind="tool"))
    graph.add_node("score_ad", _instrument("score_ad", _score_ad, kind="tool"))
    graph.set_entry_point("parse_brief")
    graph.add_edge("parse_brief", "plan_strategy")
    graph.add_edge("plan_strategy", "generate_ad")
    graph.add_edge("generate_ad", "compliance_check")
    graph.add_edge("compliance_check", "score_ad")
    graph.add_edge("score_ad", END)
    return graph.compile()


def run_public_ad_harness(
    data_path: str | Path,
    *,
    limit: int = 3,
) -> list[AdAgentState]:
    app = build_ad_agent_graph()
    results: list[AdAgentState] = []
    for case in load_public_ad_cases(data_path)[:limit]:
        trace_id = f"ad-trace-{case['case_id']}"
        state: AdAgentState = {
            **case,
            "trace_id": trace_id,
            "events": [
                {
                    "type": "trace_start",
                    "timestamp": _now(),
                    "trace_id": trace_id,
                    "project": "public-product-ad-harness",
                    "context": {
                        "dataset": "llm-wizard/Product-Descriptions-and-Ads",
                        "case_id": case["case_id"],
                        "product": case["product"],
                    },
                    "tags": ["langgraph", "public-dataset", "ad-generation"],
                }
            ],
        }
        final_state = app.invoke(state)
        final_state["events"].append(
            {
                "type": "trace_end",
                "timestamp": _now(),
                "trace_id": trace_id,
            }
        )
        results.append(final_state)
    return results


def write_harness_traces(results: list[AdAgentState], output_path: str | Path) -> None:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as handle:
        for result in results:
            for event in result["events"]:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def _parse_brief(state: AdAgentState) -> dict[str, Any]:
    description = state["description"].lower()
    audience = "fashion shoppers" if any(word in description for word in ["dress", "jacket", "top"]) else "online shoppers"
    return {"audience": audience}


def _plan_strategy(state: AdAgentState) -> dict[str, Any]:
    return {
        "strategy": (
            "Lead with product identity, mention the core visual benefit, then close with a direct shopping CTA."
        )
    }


def _generate_ad(state: AdAgentState) -> dict[str, Any]:
    product = state["product"]
    description = state["description"].rstrip(".")
    generated = f"Meet the {product}: {description}. Add polish to your look today."
    return {"generated_ad": generated}


def _compliance_check(state: AdAgentState) -> dict[str, Any]:
    risky_terms = ["guaranteed", "cure", "best ever", "risk-free"]
    lower_ad = state["generated_ad"].lower()
    matches = [term for term in risky_terms if term in lower_ad]
    return {
        "compliance_status": "error" if matches else "ok",
        "compliance_notes": matches or ["No hard-claim or regulated-category terms detected."],
    }


def _score_ad(state: AdAgentState) -> dict[str, Any]:
    ad = state["generated_ad"]
    has_cta = any(term in ad.lower() for term in ["shop", "add", "discover", "try", "explore"])
    length_ok = 60 <= len(ad) <= 220
    product_named = state["product"].lower() in ad.lower()
    score = 50 + 20 * int(has_cta) + 20 * int(length_ok) + 10 * int(product_named)
    return {
        "score": score,
        "score_reason": f"cta={has_cta}, length_ok={length_ok}, product_named={product_named}",
    }


def _instrument(name: str, func, *, kind: str):
    def wrapped(state: AdAgentState) -> dict[str, Any]:
        span_id = f"span-{name}-{uuid4().hex[:8]}"
        trace_id = state["trace_id"]
        parent_id = state["events"][-1].get("span_id") if state.get("events") else None
        start_timestamp = _now()
        start = perf_counter()
        events = [
            *state.get("events", []),
            {
                "type": "span_start",
                "timestamp": start_timestamp,
                "trace_id": trace_id,
                "span_id": span_id,
                "parent_id": parent_id if parent_id and parent_id.startswith("span-") else None,
                "name": name,
                "kind": kind,
                "input": _node_input(state),
            },
        ]
        status = "ok"
        message = None
        try:
            output = func(state)
        except Exception as exc:  # pragma: no cover - defensive instrumentation
            output = {}
            status = "error"
            message = str(exc)
        duration_ms = max(1, int((perf_counter() - start) * 1000))
        token_total = _estimate_tokens(json.dumps(_node_input(state), ensure_ascii=False)) + _estimate_tokens(
            json.dumps(output, ensure_ascii=False)
        )
        event: dict[str, Any] = {
            "type": "span_end",
            "timestamp": _now(),
            "trace_id": trace_id,
            "span_id": span_id,
            "status": status,
            "status_message": message,
            "output": output,
            "attributes": {"langgraph_node": name},
            "tokens": {
                "prompt": max(1, token_total // 2),
                "completion": max(1, token_total - token_total // 2),
                "total": max(2, token_total),
            },
        }
        if kind == "tool":
            events[-1]["type"] = "tool_call"
            events[-1]["tool"] = {"name": name, "arguments": _node_input(state)}
            event["type"] = "tool_result"
            event["tool_name"] = name
            event["result"] = output
        events.append(event)
        return {**output, "events": events}

    return wrapped


def _node_input(state: AdAgentState) -> dict[str, Any]:
    return {
        key: value
        for key, value in state.items()
        if key
        in {
            "case_id",
            "product",
            "description",
            "audience",
            "strategy",
            "generated_ad",
            "compliance_status",
        }
    }


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

"""Evaluate Agent traces against lightweight, reproducible case specs."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .analyzer import analyze_trace, summarize_trace
from .models import Trace
from .parser import parse_jsonl


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    trace_id: str
    task: str
    source: str = "local"
    expected_status: str = "ok"
    max_errors: int | None = None
    max_total_tokens: int | None = None
    max_duration_ms: float | None = None
    required_tools: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> "EvaluationCase":
        if not raw.get("case_id"):
            raise ValueError("evaluation case missing case_id")
        if not raw.get("trace_id"):
            raise ValueError(f"case {raw.get('case_id')} missing trace_id")
        tools = raw.get("required_tools") or []
        if not isinstance(tools, list):
            raise ValueError(f"case {raw['case_id']} required_tools must be a list")
        return cls(
            case_id=str(raw["case_id"]),
            trace_id=str(raw["trace_id"]),
            task=str(raw.get("task") or ""),
            source=str(raw.get("source") or "local"),
            expected_status=str(raw.get("expected_status") or "ok"),
            max_errors=_optional_int(raw.get("max_errors")),
            max_total_tokens=_optional_int(raw.get("max_total_tokens")),
            max_duration_ms=_optional_float(raw.get("max_duration_ms")),
            required_tools=tuple(str(tool) for tool in tools),
        )


def load_cases(path: str | Path) -> list[EvaluationCase]:
    source = Path(path)
    raw = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        raw_cases = raw.get("cases")
    else:
        raw_cases = raw
    if not isinstance(raw_cases, list):
        raise ValueError("evaluation cases file must be a list or an object with a cases list")
    return [EvaluationCase.from_mapping(item) for item in raw_cases]


def evaluate_trace(trace: Trace, case: EvaluationCase) -> dict[str, Any]:
    summary = summarize_trace(trace)
    issues = analyze_trace(trace)
    checks: list[dict[str, Any]] = []

    expected_errors = 0 if case.expected_status == "ok" else None
    max_errors = case.max_errors if case.max_errors is not None else expected_errors
    if max_errors is not None:
        checks.append(_check("error_count", summary["error_count"] <= max_errors, summary["error_count"], f"<= {max_errors}"))

    if case.max_total_tokens is not None:
        checks.append(
            _check(
                "total_tokens",
                summary["total_tokens"] <= case.max_total_tokens,
                summary["total_tokens"],
                f"<= {case.max_total_tokens}",
            )
        )

    if case.max_duration_ms is not None:
        checks.append(
            _check(
                "duration_ms",
                summary["duration_ms"] <= case.max_duration_ms,
                summary["duration_ms"],
                f"<= {case.max_duration_ms}",
            )
        )

    observed_tools = {
        span.tool.name
        for span in trace.spans.values()
        if span.tool is not None and span.tool.name
    }
    for tool in case.required_tools:
        checks.append(_check(f"required_tool:{tool}", tool in observed_tools, sorted(observed_tools), "present"))

    passed = all(check["passed"] for check in checks) if checks else not issues
    return {
        "case_id": case.case_id,
        "trace_id": trace.trace_id,
        "task": case.task,
        "source": case.source,
        "passed": passed,
        "checks": checks,
        "summary": summary,
        "issue_count": len(issues),
        "issues": [issue.to_dict() for issue in issues],
    }


def evaluate_file(trace_path: str | Path, cases_path: str | Path) -> dict[str, Any]:
    traces = {trace.trace_id: trace for trace in parse_jsonl(trace_path)}
    cases = load_cases(cases_path)
    results: list[dict[str, Any]] = []
    for case in cases:
        trace = traces.get(case.trace_id)
        if trace is None:
            results.append(
                {
                    "case_id": case.case_id,
                    "trace_id": case.trace_id,
                    "task": case.task,
                    "source": case.source,
                    "passed": False,
                    "checks": [_check("trace_exists", False, "missing", "present")],
                    "summary": None,
                    "issue_count": 0,
                    "issues": [],
                }
            )
            continue
        results.append(evaluate_trace(trace, case))

    passed_count = sum(1 for result in results if result["passed"])
    return {
        "case_count": len(results),
        "passed_count": passed_count,
        "failed_count": len(results) - passed_count,
        "pass_rate": round(passed_count / len(results), 4) if results else 0.0,
        "results": results,
    }


def _check(name: str, passed: bool, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "observed": observed,
        "expected": expected,
    }


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)

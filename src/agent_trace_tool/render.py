"""Render normalized traces for CLI and frontend demo consumption."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .analyzer import analyze_trace, summarize_trace
from .models import Span, Trace, timestamp_to_iso


def span_to_dict(span: Span) -> dict[str, Any]:
    return {
        "id": span.span_id,
        "parent_id": span.parent_id,
        "name": span.name,
        "kind": span.kind,
        "status": span.status,
        "status_message": span.status_message,
        "start_time": timestamp_to_iso(span.start_time),
        "end_time": timestamp_to_iso(span.end_time),
        "duration_ms": round(span.duration_ms or 0, 2),
        "tokens": span.tokens.to_dict(),
        "tool": span.tool.to_dict() if span.tool else None,
        "input": span.input,
        "output": span.output,
        "attributes": span.attributes,
        "events": [event.to_dict() for event in span.events],
        "children": [span_to_dict(child) for child in span.children],
    }


def trace_to_dict(trace: Trace) -> dict[str, Any]:
    flat_spans = sorted(
        trace.spans.values(),
        key=lambda span: (span.start_time or span.end_time or datetime.min.replace(tzinfo=timezone.utc), span.span_id),
    )
    return {
        "trace": {
            "id": trace.trace_id,
            "project": trace.project,
            "session_id": trace.session_id,
            "user_id": trace.user_id,
            "start_time": timestamp_to_iso(trace.start_time),
            "end_time": timestamp_to_iso(trace.end_time),
            "duration_ms": round(trace.duration_ms or 0, 2),
            "context": trace.context,
            "metadata": trace.metadata,
            "tags": trace.tags,
            "events": [event.to_dict() for event in trace.events],
        },
        "summary": summarize_trace(trace),
        "issues": [issue.to_dict() for issue in analyze_trace(trace)],
        "tree": [span_to_dict(root) for root in trace.root_spans],
        "spans": [span_to_dict(span) for span in flat_spans],
    }


def traces_to_payload(traces: list[Trace]) -> dict[str, Any]:
    return {
        "schema_version": "agent-trace-v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "traces": [trace_to_dict(trace) for trace in traces],
    }


def write_payload(path: str | Path, payload: dict[str, Any], *, js_var: str | None = None) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    if js_var:
        serialized = f"window.{js_var} = {serialized};\n"
    target.write_text(serialized + ("\n" if not serialized.endswith("\n") else ""), encoding="utf-8")


def render_text_tree(trace: Trace) -> str:
    lines = [
        f"Trace {trace.trace_id} | spans={len(trace.spans)} | duration={trace.duration_ms or 0:.0f}ms",
    ]
    for root in trace.root_spans:
        _append_span_line(lines, root, depth=0)
    return "\n".join(lines)


def _append_span_line(lines: list[str], span: Span, depth: int) -> None:
    prefix = "  " * depth
    status = "!" if span.status == "error" else "-"
    duration = f"{span.duration_ms:.0f}ms" if span.duration_ms is not None else "open"
    tokens = f", tokens={span.tokens.total}" if span.tokens.total else ""
    lines.append(f"{prefix}{status} [{span.kind}] {span.name} ({span.span_id}) {duration}{tokens}")
    for child in span.children:
        _append_span_line(lines, child, depth + 1)

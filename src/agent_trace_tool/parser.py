"""JSONL log parser for Agent traces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .models import Span, ToolCall, TokenUsage, Trace, parse_timestamp


class LogParseError(ValueError):
    """Raised when a trace log cannot be parsed into the normalized schema."""


def parse_jsonl(path: str | Path) -> list[Trace]:
    records: list[dict[str, Any]] = []
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise LogParseError(f"{source}:{line_no}: invalid JSON: {exc.msg}") from exc
            if not isinstance(record, dict):
                raise LogParseError(f"{source}:{line_no}: each log line must be a JSON object")
            record["_line_no"] = line_no
            records.append(record)
    return parse_events(records)


def parse_events(records: Iterable[dict[str, Any]]) -> list[Trace]:
    traces: dict[str, Trace] = {}

    for index, record in enumerate(records, start=1):
        event_type = _event_type(record)
        trace_id = _trace_id(record)
        if not trace_id:
            line_no = record.get("_line_no", index)
            raise LogParseError(f"line {line_no}: missing required trace_id")

        trace = traces.setdefault(trace_id, Trace(trace_id=trace_id))
        timestamp = parse_timestamp(record.get("timestamp") or record.get("time"))

        if event_type == "trace_start":
            _merge_trace_header(trace, record, timestamp)
            continue
        if event_type == "trace_end":
            _merge_trace_header(trace, record, None)
            trace.end_time = timestamp or trace.end_time
            continue
        if event_type in {"span_start", "span", "tool_call"}:
            span = _ensure_span(trace, record, event_type, timestamp)
            if event_type == "tool_call":
                _attach_tool_call(span, record, timestamp)
            if event_type == "span":
                _finish_span(span, record, timestamp)
            continue
        if event_type in {"span_end", "tool_result"}:
            span = _ensure_span(trace, record, event_type, timestamp)
            _finish_span(span, record, timestamp)
            if event_type == "tool_result":
                _attach_tool_result(span, record)
            continue
        if event_type in {"thought", "llm_message", "event"}:
            _attach_span_event(trace, record, timestamp, event_type)
            continue
        if event_type == "error":
            _attach_error(trace, record, timestamp)
            continue

        _attach_span_event(trace, record, timestamp, event_type)

    for trace in traces.values():
        _link_children(trace)
        _infer_trace_bounds(trace)

    return sorted(traces.values(), key=lambda trace: (trace.start_time is None, trace.start_time, trace.trace_id))


def _event_type(record: dict[str, Any]) -> str:
    raw = record.get("type") or record.get("event") or record.get("event_type")
    if raw:
        return str(raw).strip().lower()
    if record.get("tool") or record.get("tool_name"):
        return "tool_call"
    if record.get("span_id"):
        return "span"
    return "event"


def _trace_id(record: dict[str, Any]) -> str | None:
    for key in ("trace_id", "traceId"):
        if record.get(key):
            return str(record[key])
    context = record.get("context")
    if isinstance(context, dict):
        value = context.get("trace_id") or context.get("traceId")
        if value:
            return str(value)
    return None


def _span_id(record: dict[str, Any]) -> str | None:
    for key in ("span_id", "spanId", "run_id", "runId"):
        if record.get(key):
            return str(record[key])
    context = record.get("context")
    if isinstance(context, dict):
        value = context.get("span_id") or context.get("spanId")
        if value:
            return str(value)
    return None


def _parent_id(record: dict[str, Any]) -> str | None:
    for key in ("parent_id", "parent_span_id", "parentSpanId", "parent_run_id"):
        value = record.get(key)
        if value:
            return str(value)
    return None


def _merge_trace_header(trace: Trace, record: dict[str, Any], timestamp: Any) -> None:
    trace.project = str(record.get("project") or trace.project)
    trace.session_id = str(record.get("session_id") or record.get("thread_id") or trace.session_id or "")
    trace.session_id = trace.session_id or None
    trace.user_id = str(record.get("user_id") or trace.user_id or "") or None
    trace.start_time = timestamp or trace.start_time
    if isinstance(record.get("context"), dict):
        trace.context.update(record["context"])
    if isinstance(record.get("metadata"), dict):
        trace.metadata.update(record["metadata"])
    tags = record.get("tags")
    if isinstance(tags, list):
        trace.tags = sorted({*trace.tags, *[str(tag) for tag in tags]})


def _ensure_span(trace: Trace, record: dict[str, Any], event_type: str, timestamp: Any) -> Span:
    span_id = _span_id(record)
    if not span_id:
        line_no = record.get("_line_no", "unknown")
        span_id = f"synthetic-{line_no}"

    kind = str(record.get("kind") or record.get("span_kind") or ("tool" if event_type.startswith("tool") else "custom")).lower()
    name = str(record.get("name") or record.get("operation") or record.get("tool_name") or kind)

    span = trace.spans.get(span_id)
    if span is None:
        span = Span(
            trace_id=trace.trace_id,
            span_id=span_id,
            name=name,
            kind=kind,
            parent_id=_parent_id(record),
            start_time=timestamp,
            input=record.get("input"),
            attributes=dict(record.get("attributes") or {}),
        )
        trace.spans[span_id] = span
    else:
        span.name = name if span.name == "custom" else span.name
        span.kind = kind if span.kind == "custom" else span.kind
        span.parent_id = span.parent_id or _parent_id(record)
        span.start_time = span.start_time or timestamp

    if record.get("input") is not None:
        span.input = record.get("input")
    if isinstance(record.get("attributes"), dict):
        span.attributes.update(record["attributes"])

    return span


def _finish_span(span: Span, record: dict[str, Any], timestamp: Any) -> None:
    end_time = parse_timestamp(record.get("end_time") or record.get("ended_at")) or timestamp
    start_time = parse_timestamp(record.get("start_time") or record.get("started_at"))
    span.start_time = span.start_time or start_time
    span.end_time = end_time or span.end_time
    span.status = _normalize_status(record.get("status") or record.get("status_code") or ("error" if record.get("error") else "ok"))
    span.status_message = str(record.get("status_message") or record.get("message") or "") or span.status_message

    if record.get("output") is not None:
        span.output = record.get("output")
    if record.get("result") is not None and span.output is None:
        span.output = record.get("result")

    token_record = record.get("tokens") or record.get("token_usage") or record.get("usage")
    span.tokens = TokenUsage.from_mapping(token_record)

    if record.get("error"):
        span.status = "error"
        span.status_message = str(record["error"])
        span.add_event("error", timestamp, str(record["error"]))


def _attach_tool_call(span: Span, record: dict[str, Any], timestamp: Any) -> None:
    tool = record.get("tool") if isinstance(record.get("tool"), dict) else {}
    tool_name = str(tool.get("name") or record.get("tool_name") or span.name)
    arguments = tool.get("arguments") if "arguments" in tool else record.get("arguments", record.get("input", {}))
    span.kind = "tool"
    span.tool = ToolCall(
        name=tool_name,
        arguments=arguments,
        call_id=str(tool.get("call_id") or record.get("tool_call_id") or record.get("call_id") or "") or None,
    )
    span.add_event("tool_call", timestamp, attributes={"tool": tool_name, "arguments": arguments})


def _attach_tool_result(span: Span, record: dict[str, Any]) -> None:
    if span.tool is None:
        span.tool = ToolCall(name=str(record.get("tool_name") or span.name))
    span.tool.result = record.get("result", record.get("output"))
    span.tool.status = _normalize_status(record.get("status") or ("error" if record.get("error") else "ok"))
    if record.get("error"):
        span.tool.error = str(record["error"])
        span.status = "error"
        span.status_message = str(record["error"])


def _attach_span_event(trace: Trace, record: dict[str, Any], timestamp: Any, event_type: str) -> None:
    span_id = _span_id(record)
    message = record.get("content") or record.get("message") or record.get("text")
    attributes = dict(record.get("attributes") or {})
    if record.get("tokens") or record.get("usage"):
        attributes["tokens"] = record.get("tokens") or record.get("usage")

    if span_id and span_id in trace.spans:
        trace.spans[span_id].add_event(event_type, timestamp, str(message) if message else None, attributes)
    else:
        from .models import SpanEvent

        trace.events.append(SpanEvent(event_type, timestamp, str(message) if message else None, attributes))


def _attach_error(trace: Trace, record: dict[str, Any], timestamp: Any) -> None:
    span_id = _span_id(record)
    message = str(record.get("error") or record.get("message") or "unknown error")
    if span_id:
        span = _ensure_span(trace, record, "error", timestamp)
        span.status = "error"
        span.status_message = message
        span.end_time = span.end_time or timestamp
        span.add_event("error", timestamp, message, dict(record.get("attributes") or {}))
    else:
        from .models import SpanEvent

        trace.events.append(SpanEvent("error", timestamp, message, dict(record.get("attributes") or {})))


def _normalize_status(raw: Any) -> str:
    value = str(raw or "").strip().lower()
    if value in {"ok", "success", "succeeded", "status_code_ok"}:
        return "ok"
    if value in {"error", "failed", "fail", "exception", "status_code_error"}:
        return "error"
    if value in {"cancelled", "canceled", "timeout"}:
        return value
    return value or "ok"


def _link_children(trace: Trace) -> None:
    for span in trace.spans.values():
        span.children.clear()
    for span in trace.spans.values():
        if span.parent_id and span.parent_id in trace.spans:
            trace.spans[span.parent_id].children.append(span)
    for span in trace.spans.values():
        span.children.sort(key=lambda child: (child.start_time or child.end_time or child.span_id, child.span_id))


def _infer_trace_bounds(trace: Trace) -> None:
    starts = [span.start_time for span in trace.spans.values() if span.start_time]
    ends = [span.end_time for span in trace.spans.values() if span.end_time]
    trace.start_time = trace.start_time or (min(starts) if starts else None)
    trace.end_time = trace.end_time or (max(ends) if ends else None)

"""Trace analysis rules for highlighting failures and expensive spans."""

from __future__ import annotations

from .models import TokenUsage, Trace, TraceIssue


def summarize_trace(trace: Trace) -> dict[str, int | float | str | None]:
    tokens = TokenUsage()
    error_count = 0
    tool_count = 0
    completed_spans = 0

    for span in trace.spans.values():
        tokens.add(span.tokens)
        error_count += int(span.status == "error")
        tool_count += int(span.kind == "tool")
        completed_spans += int(span.end_time is not None)

    return {
        "trace_id": trace.trace_id,
        "span_count": len(trace.spans),
        "completed_spans": completed_spans,
        "tool_count": tool_count,
        "error_count": error_count,
        "duration_ms": round(trace.duration_ms or 0, 2),
        "prompt_tokens": tokens.prompt,
        "completion_tokens": tokens.completion,
        "reasoning_tokens": tokens.reasoning,
        "cached_tokens": tokens.cached,
        "total_tokens": tokens.total,
    }


def analyze_trace(
    trace: Trace,
    *,
    high_latency_ms: float = 3000,
    high_token_count: int = 1000,
) -> list[TraceIssue]:
    issues: list[TraceIssue] = []

    for span in trace.spans.values():
        if span.parent_id and span.parent_id not in trace.spans:
            issues.append(
                TraceIssue(
                    severity="warning",
                    code="orphan_span",
                    span_id=span.span_id,
                    message=f"Span {span.span_id} references missing parent {span.parent_id}.",
                    recommendation="检查日志采集顺序或 parent_id 传递逻辑。",
                )
            )

        if span.end_time is None:
            issues.append(
                TraceIssue(
                    severity="warning",
                    code="missing_span_end",
                    span_id=span.span_id,
                    message=f"Span {span.name} has no end event.",
                    recommendation="确保 finally 块或上下文管理器能写入 span_end。",
                )
            )

        if span.status == "error":
            issues.append(
                TraceIssue(
                    severity="critical" if span.kind in {"agent", "llm"} else "error",
                    code="span_error",
                    span_id=span.span_id,
                    message=f"{span.kind} span {span.name} failed: {span.status_message or 'unknown error'}.",
                    recommendation="展开该 span 的输入、输出和事件，定位异常参数或外部依赖。",
                )
            )

        duration = span.duration_ms
        if duration is not None and duration >= high_latency_ms:
            issues.append(
                TraceIssue(
                    severity="warning",
                    code="high_latency",
                    span_id=span.span_id,
                    message=f"Span {span.name} took {duration:.0f} ms.",
                    recommendation="优先检查慢工具、检索器或模型调用的超时配置。",
                )
            )

        if span.tokens.total >= high_token_count:
            issues.append(
                TraceIssue(
                    severity="info",
                    code="high_token_usage",
                    span_id=span.span_id,
                    message=f"Span {span.name} consumed {span.tokens.total} tokens.",
                    recommendation="检查上下文裁剪、检索片段数量和思考链记录粒度。",
                )
            )

        if span.tool and span.tool.status == "error":
            issues.append(
                TraceIssue(
                    severity="error",
                    code="tool_failed",
                    span_id=span.span_id,
                    message=f"Tool {span.tool.name} failed: {span.tool.error or span.status_message or 'unknown error'}.",
                    recommendation="记录工具入参、HTTP 状态码和重试策略，便于复现。",
                )
            )

    severity_order = {"critical": 0, "error": 1, "warning": 2, "info": 3}
    return sorted(issues, key=lambda issue: (severity_order.get(issue.severity, 9), issue.span_id or ""))

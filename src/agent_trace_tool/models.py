"""Data models for Agent execution traces.

The schema follows the common trace/span vocabulary used by observability
systems while adding Agent-specific fields such as thoughts, tools and tokens.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


JsonValue = dict[str, Any] | list[Any] | str | int | float | bool | None


def parse_timestamp(value: Any) -> datetime | None:
    """Parse an ISO timestamp and normalize it to UTC when possible."""

    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    if not isinstance(value, str):
        return None

    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def timestamp_to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class TokenUsage:
    prompt: int = 0
    completion: int = 0
    reasoning: int = 0
    cached: int = 0
    total: int = 0

    @classmethod
    def from_mapping(cls, raw: Any) -> "TokenUsage":
        if not isinstance(raw, dict):
            return cls()

        def as_int(*keys: str) -> int:
            for key in keys:
                value = raw.get(key)
                if value is not None:
                    try:
                        return int(value)
                    except (TypeError, ValueError):
                        return 0
            return 0

        usage = cls(
            prompt=as_int("prompt", "prompt_tokens", "input_tokens"),
            completion=as_int("completion", "completion_tokens", "output_tokens"),
            reasoning=as_int("reasoning", "reasoning_tokens"),
            cached=as_int("cached", "cached_tokens", "cache_read_tokens"),
            total=as_int("total", "total_tokens"),
        )
        if usage.total == 0:
            usage.total = usage.prompt + usage.completion + usage.reasoning
        return usage

    def add(self, other: "TokenUsage") -> None:
        self.prompt += other.prompt
        self.completion += other.completion
        self.reasoning += other.reasoning
        self.cached += other.cached
        self.total += other.total

    def to_dict(self) -> dict[str, int]:
        return {
            "prompt": self.prompt,
            "completion": self.completion,
            "reasoning": self.reasoning,
            "cached": self.cached,
            "total": self.total,
        }


@dataclass
class ToolCall:
    name: str
    arguments: JsonValue = field(default_factory=dict)
    call_id: str | None = None
    result: JsonValue = None
    status: str = "running"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "arguments": self.arguments,
            "call_id": self.call_id,
            "result": self.result,
            "status": self.status,
            "error": self.error,
        }


@dataclass
class SpanEvent:
    name: str
    timestamp: datetime | None = None
    message: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "timestamp": timestamp_to_iso(self.timestamp),
            "message": self.message,
            "attributes": self.attributes,
        }


@dataclass
class Span:
    trace_id: str
    span_id: str
    name: str
    kind: str = "custom"
    parent_id: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: str = "running"
    status_message: str | None = None
    input: JsonValue = None
    output: JsonValue = None
    tokens: TokenUsage = field(default_factory=TokenUsage)
    tool: ToolCall | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[SpanEvent] = field(default_factory=list)
    children: list["Span"] = field(default_factory=list)

    @property
    def duration_ms(self) -> float | None:
        if not self.start_time or not self.end_time:
            return None
        return max(0.0, (self.end_time - self.start_time).total_seconds() * 1000)

    def add_event(
        self,
        name: str,
        timestamp: datetime | None = None,
        message: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        self.events.append(
            SpanEvent(
                name=name,
                timestamp=timestamp,
                message=message,
                attributes=attributes or {},
            )
        )


@dataclass
class Trace:
    trace_id: str
    project: str = "default"
    session_id: str | None = None
    user_id: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    spans: dict[str, Span] = field(default_factory=dict)
    events: list[SpanEvent] = field(default_factory=list)

    @property
    def root_spans(self) -> list[Span]:
        roots = [
            span
            for span in self.spans.values()
            if not span.parent_id or span.parent_id not in self.spans
        ]
        return sorted(roots, key=lambda span: (span.start_time or datetime.min, span.span_id))

    @property
    def duration_ms(self) -> float | None:
        if self.start_time and self.end_time:
            return max(0.0, (self.end_time - self.start_time).total_seconds() * 1000)
        durations = [span.duration_ms for span in self.root_spans if span.duration_ms is not None]
        if durations:
            return max(durations)
        return None


@dataclass
class TraceIssue:
    severity: str
    code: str
    message: str
    span_id: str | None = None
    recommendation: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "span_id": self.span_id,
            "recommendation": self.recommendation,
        }

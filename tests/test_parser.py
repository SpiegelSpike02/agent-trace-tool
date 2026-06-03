from agent_trace_tool.analyzer import analyze_trace, summarize_trace
from agent_trace_tool.parser import parse_jsonl


def test_sample_trace_parses_tree_and_issues():
    traces = parse_jsonl("examples/sample_trace.jsonl")

    assert len(traces) == 1
    trace = traces[0]
    assert trace.trace_id == "trace-week4-001"
    assert len(trace.root_spans) == 1
    assert trace.root_spans[0].span_id == "span-agent-root"
    assert {child.span_id for child in trace.root_spans[0].children} == {
        "span-plan-llm",
        "span-search-tool",
        "span-cache-tool",
        "span-final-llm",
    }

    summary = summarize_trace(trace)
    assert summary["tool_count"] == 2
    assert summary["error_count"] == 1
    assert summary["total_tokens"] == 5052

    issues = analyze_trace(trace)
    assert any(issue.code == "tool_failed" for issue in issues)
    assert any(issue.code == "high_token_usage" for issue in issues)

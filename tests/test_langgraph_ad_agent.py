from agent_trace_tool.evaluator import evaluate_file
from agent_trace_tool.langgraph_ad_agent import run_public_ad_harness, write_harness_traces
from agent_trace_tool.parser import parse_jsonl


def test_langgraph_public_ad_harness_generates_parseable_trace(tmp_path):
    output = tmp_path / "langgraph_ad_traces.jsonl"

    results = run_public_ad_harness("data/product_ads_sample.json", limit=1)
    write_harness_traces(results, output)
    traces = parse_jsonl(output)

    assert len(traces) == 1
    trace = traces[0]
    assert trace.trace_id == "ad-trace-product-ad-001"
    assert len(trace.spans) == 5
    assert {span.tool.name for span in trace.spans.values() if span.tool} == {
        "compliance_check",
        "score_ad",
    }


def test_checked_in_langgraph_ad_traces_pass_eval():
    report = evaluate_file("examples/langgraph_ad_traces.jsonl", "examples/langgraph_ad_eval_cases.json")

    assert report["case_count"] == 3
    assert report["failed_count"] == 0

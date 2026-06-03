from agent_trace_tool.evaluator import evaluate_file, load_cases


def test_eval_cases_load_and_pass_sample_trace():
    cases = load_cases("examples/eval_cases.json")

    assert len(cases) == 1
    assert cases[0].trace_id == "trace-week4-001"
    assert "search_docs" in cases[0].required_tools

    report = evaluate_file("examples/sample_trace.jsonl", "examples/eval_cases.json")

    assert report["case_count"] == 1
    assert report["passed_count"] == 1
    assert report["failed_count"] == 0
    assert report["results"][0]["summary"]["error_count"] == 1

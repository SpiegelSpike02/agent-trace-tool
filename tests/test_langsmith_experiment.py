import pytest

from agent_trace_tool.langsmith_experiment import build_langsmith_examples, run_langsmith_experiment


def test_build_langsmith_examples_from_public_ads_snapshot():
    examples = build_langsmith_examples("data/product_ads_sample.json", limit=2)

    assert len(examples) == 2
    assert examples[0]["inputs"]["case_id"] == "product-ad-001"
    assert "product" in examples[0]["inputs"]
    assert "reference_ad" in examples[0]["outputs"]
    assert examples[0]["metadata"]["source"] == "llm-wizard/Product-Descriptions-and-Ads"


def test_langsmith_experiment_requires_api_key(monkeypatch):
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="LANGSMITH_API_KEY"):
        run_langsmith_experiment("data/product_ads_sample.json", limit=1)

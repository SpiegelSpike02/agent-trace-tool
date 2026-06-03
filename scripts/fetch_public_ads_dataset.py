from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


DATASET_URL = (
    "https://huggingface.co/datasets/llm-wizard/Product-Descriptions-and-Ads"
    "/resolve/main/data/test-00000-of-00001-da7439d21cc2d71e.parquet"
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch a public ad-copy dataset snapshot from Hugging Face.")
    parser.add_argument("--out", default="data/product_ads_sample.json")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    df = pd.read_parquet(DATASET_URL).head(args.limit)
    payload = {
        "source": "https://huggingface.co/datasets/llm-wizard/Product-Descriptions-and-Ads",
        "split": "test",
        "records": df.to_dict(orient="records"),
    }
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(payload['records'])} records to {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

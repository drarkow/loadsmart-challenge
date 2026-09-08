"""Run the defined AI question set and save generated SQL/results as JSONL."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from ask_claude import run_question


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", default="ai/questions.yml")
    parser.add_argument("--manifest", default="dbt_loadsmart/target/manifest.json")
    parser.add_argument("--catalog", default="dbt_loadsmart/target/catalog.json")
    parser.add_argument("--duckdb", default="loadsmart.duckdb")
    parser.add_argument("--model")
    parser.add_argument("--output", default="analysis/claude_question_runs.jsonl")
    args = parser.parse_args()

    question_doc = yaml.safe_load(Path(args.questions).read_text(encoding="utf-8"))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", encoding="utf-8") as handle:
        for item in question_doc.get("questions", []):
            result = run_question(
                item["question"],
                Path(args.manifest),
                Path(args.catalog),
                Path(args.duckdb),
                args.model or __import__("os").environ.get("CLAUDE_MODEL", "claude-sonnet-5"),
            )
            result["id"] = item["id"]
            handle.write(json.dumps(result, default=str) + "\n")
            print(f"Completed {item['id']}: {item['question']}")


if __name__ == "__main__":
    main()

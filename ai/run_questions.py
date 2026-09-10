"""Run the configured AI question set and save results as JSONL."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from ask_claude import resolve_project_path, run_question


# ---------------------------------------------------------------------------
# Project configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load the same project-level .env used by ask_claude.py.
load_dotenv(PROJECT_ROOT / ".env")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run all questions defined in questions.yml through "
            "Claude and DuckDB."
        )
    )

    parser.add_argument(
        "--questions",
        default=os.environ.get(
            "QUESTIONS_PATH",
            "ai/questions.yml",
        ),
        help="Path to questions.yml.",
    )

    parser.add_argument(
        "--manifest",
        default=os.environ.get(
            "DBT_MANIFEST_PATH",
            "dbt_loadsmart/target/manifest.json",
        ),
        help="Path to dbt manifest.json.",
    )

    parser.add_argument(
        "--catalog",
        default=os.environ.get(
            "DBT_CATALOG_PATH",
            "dbt_loadsmart/target/catalog.json",
        ),
        help="Path to dbt catalog.json.",
    )

    parser.add_argument(
        "--duckdb",
        default=os.environ.get(
            "DUCKDB_PATH",
            "data/loadsmart.duckdb",
        ),
        help="Path to the DuckDB database.",
    )

    parser.add_argument(
        "--model",
        default=os.environ.get(
            "CLAUDE_MODEL",
            "claude-sonnet-5",
        ),
        help="Anthropic model to use.",
    )

    parser.add_argument(
        "--output",
        default=os.environ.get(
            "AI_RESULTS_PATH",
            "analysis/claude_question_runs.jsonl",
        ),
        help="Path to the JSONL output file.",
    )

    args = parser.parse_args()

    # Resolve all paths from the project root.
    questions_path = resolve_project_path(args.questions)
    manifest_path = resolve_project_path(args.manifest)
    catalog_path = resolve_project_path(args.catalog)
    duckdb_path = resolve_project_path(args.duckdb)
    output_path = resolve_project_path(args.output)

    # Validate files before making any Claude API calls.
    for label, path in (
        ("Questions file", questions_path),
        ("Manifest", manifest_path),
        ("Catalog", catalog_path),
        ("DuckDB database", duckdb_path),
    ):
        if not path.exists():
            raise FileNotFoundError(
                f"{label} not found: {path}"
            )

    question_doc = yaml.safe_load(
        questions_path.read_text(
            encoding="utf-8"
        )
    )

    questions = question_doc.get("questions", [])

    if not questions:
        raise ValueError(
            f"No questions found in {questions_path}"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as handle:

        for item in questions:
            question_id = item["id"]
            question = item["question"]

            print(
                f"\nRunning {question_id}: {question}"
            )

            try:
                result = run_question(
                    question=question,
                    manifest=manifest_path,
                    catalog=catalog_path,
                    duckdb_path=duckdb_path,
                    model=args.model,
                )

                # Preserve the question-set ID in the result.
                result["id"] = question_id

            except Exception as exc:
                result = {
                    "id": question_id,
                    "question": question,
                    "error": type(exc).__name__,
                    "error_message": str(exc),
                }

            # Preserve useful metadata from questions.yml.
            if "why_it_matters" in item:
                result["why_it_matters"] = item["why_it_matters"]

            if "assumption" in item:
                result["assumption"] = item["assumption"]

            if "what_needs_change" in item:
                result["what_needs_change"] = item[
                    "what_needs_change"
                ]

            handle.write(
                json.dumps(
                    result,
                    default=str,
                )
                + "\n"
            )

            print(
                f"Completed {question_id}"
            )

    print(
        f"\nResults written to: {output_path}"
    )


if __name__ == "__main__":
    main()
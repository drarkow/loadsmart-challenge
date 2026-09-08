"""Natural-language question -> Claude SQL -> read-only DuckDB execution."""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

import duckdb
from anthropic import Anthropic

from semantic_context import build_context


SYSTEM_PROMPT = """
You are a senior analytics engineer working over a documented dbt dimensional model.
Generate exactly one read-only DuckDB SQL query for the user's question.

Rules:
1. Use only relations and columns present in the supplied dbt metadata.
2. Prefer the documented analytics dimensional models over staging/raw relations.
3. Treat dbt model and column descriptions as the source of truth for business semantics.
4. Use documented semantic fields when available instead of recreating their definitions.
5. Do not invent business rules, entities, columns, tables, or values that are absent from the metadata.
6. Obtain factual results by executing SQL; never answer from assumptions or prompt-included rows.
7. The query must be read-only and contain exactly one SQL statement.
8. Return SQL only, with no markdown fences or explanation.
""".strip()


def extract_sql(text: str) -> str:
    match = re.search(r"```(?:sql)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    sql = match.group(1).strip() if match else text.strip()
    sql = sql.rstrip(";\n ").strip()

    if not re.match(r"^(select|with)\b", sql, flags=re.IGNORECASE):
        raise ValueError("Claude returned non-read-only SQL")
    if ";" in sql:
        raise ValueError("Multiple SQL statements are not allowed")
    if re.search(r"\b(insert|update|delete|drop|alter|create|truncate|attach|copy|export|install|load|call)\b", sql, flags=re.IGNORECASE):
        raise ValueError("Potentially mutating or administrative SQL was rejected")
    return sql


def generate_sql(client: Anthropic, model: str, question: str, context: str) -> str:
    response = client.messages.create(
        model=model,
        max_tokens=1200,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "<dbt_metadata>\n" + context + "\n</dbt_metadata>\n\n"
                    "<question>\n" + question + "\n</question>"
                ),
            }
        ],
    )
    text_blocks = [b.text for b in response.content if getattr(b, "type", None) == "text"]
    if not text_blocks:
        raise ValueError("Claude returned no text")
    return extract_sql("\n".join(text_blocks))


def run_question(
    question: str,
    manifest: Path,
    catalog: Path,
    duckdb_path: Path,
    model: str,
) -> dict[str, Any]:
    context = build_context(manifest, catalog)
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    sql = generate_sql(client, model, question, context)

    with duckdb.connect(str(duckdb_path), read_only=True) as con:
        result = con.execute(sql).fetchdf()

    return {
        "question": question,
        "generated_sql": sql,
        "answer": result.to_dict(orient="records"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--manifest", default="dbt_loadsmart/target/manifest.json")
    parser.add_argument("--catalog", default="dbt_loadsmart/target/catalog.json")
    parser.add_argument(
        "--duckdb",
        default=os.environ.get("DUCKDB_PATH", "loadsmart.duckdb"),
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("CLAUDE_MODEL", "claude-sonnet-5"),
    )
    parser.add_argument("--output")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set")

    result = run_question(
        args.question,
        Path(args.manifest),
        Path(args.catalog),
        Path(args.duckdb),
        args.model,
    )

    print(json.dumps(result, indent=2, default=str))
    if args.output:
        Path(args.output).write_text(
            json.dumps(result, indent=2, default=str),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()

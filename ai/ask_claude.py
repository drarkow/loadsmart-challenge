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
from dotenv import load_dotenv

from semantic_context import build_context


# ---------------------------------------------------------------------------
# Project configuration
# ---------------------------------------------------------------------------

# Resolve paths relative to the repository root rather than the current
# working directory. This keeps the project portable across machines.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load variables from the project's .env file.
load_dotenv(PROJECT_ROOT / ".env")


# ---------------------------------------------------------------------------
# Claude prompt
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Path handling
# ---------------------------------------------------------------------------

def resolve_project_path(path_value: str | Path) -> Path:
    """
    Resolve a path relative to the project root unless it is absolute.

    Example:
        data/loadsmart.duckdb
        -> <project_root>/data/loadsmart.duckdb
    """
    path = Path(path_value)

    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


# ---------------------------------------------------------------------------
# SQL validation
# ---------------------------------------------------------------------------

def extract_sql(text: str) -> str:
    """
    Extract SQL from Claude's response and validate that it is one
    read-only SELECT/CTE statement.
    """
    # Support accidental markdown fences even though the prompt asks
    # Claude not to use them.
    match = re.search(
        r"```(?:sql)?\s*(.*?)```",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    sql = match.group(1).strip() if match else text.strip()

    # Remove a trailing semicolon so we can detect multiple statements
    # consistently.
    sql = sql.rstrip(";\n ").strip()

    # Only SELECT statements and CTEs are allowed.
    if not re.match(r"^(select|with)\b", sql, flags=re.IGNORECASE):
        raise ValueError("Claude returned non-read-only SQL")

    # A semicolon anywhere in the remaining SQL would indicate multiple
    # statements.
    if ";" in sql:
        raise ValueError("Multiple SQL statements are not allowed")

    # Reject mutating or administrative statements/functions.
    forbidden = (
        r"\b("
        r"insert|update|delete|drop|alter|create|truncate|"
        r"attach|copy|export|install|load|call"
        r")\b"
    )

    if re.search(forbidden, sql, flags=re.IGNORECASE):
        raise ValueError(
            "Potentially mutating or administrative SQL was rejected"
        )

    return sql


# ---------------------------------------------------------------------------
# Claude interaction
# ---------------------------------------------------------------------------

def generate_sql(
    client: Anthropic,
    model: str,
    question: str,
    context: str,
) -> str:
    """Ask Claude to generate SQL using only the dbt-derived metadata."""
    response = client.messages.create(
        model=model,
        max_tokens=1200,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "<dbt_metadata>\n"
                    + context
                    + "\n</dbt_metadata>\n\n"
                    "<question>\n"
                    + question
                    + "\n</question>"
                ),
            }
        ],
    )

    text_blocks = [
        block.text
        for block in response.content
        if getattr(block, "type", None) == "text"
    ]

    if not text_blocks:
        raise ValueError("Claude returned no text")

    return extract_sql("\n".join(text_blocks))


# ---------------------------------------------------------------------------
# Question execution
# ---------------------------------------------------------------------------

def run_question(
    question: str,
    manifest: Path,
    catalog: Path,
    duckdb_path: Path,
    model: str,
) -> dict[str, Any]:
    """
    Generate SQL with Claude and execute it against DuckDB in read-only mode.
    """
    # Build the semantic context programmatically from dbt artifacts.
    context = build_context(manifest, catalog)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY environment variable is not set"
        )

    client = Anthropic(api_key=api_key)

    sql = generate_sql(
        client=client,
        model=model,
        question=question,
        context=context,
    )

    # Open the database read-only as an additional safety boundary.
    try:
        with duckdb.connect(str(duckdb_path), read_only=True) as con:
            result = con.execute(sql).fetchdf()
            
    except Exception as exc:
        return {
            "question": question,
            "generated_sql": sql,
            "answer": None,
            "execution_error": type(exc).__name__,
            "execution_error_message": str(exc),
        }

    return {
        "question": question,
        "generated_sql": sql,
        "answer": result.to_dict(orient="records"),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate read-only DuckDB SQL from a natural-language "
            "question using Claude and dbt metadata."
        )
    )

    parser.add_argument(
        "question",
        help="Natural-language question to answer.",
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
        help="Optional path for saving the JSON result.",
    )

    args = parser.parse_args()

    manifest_path = resolve_project_path(args.manifest)
    catalog_path = resolve_project_path(args.catalog)
    duckdb_path = resolve_project_path(args.duckdb)

    # Fail early with readable errors instead of opaque file/database errors.
    for label, path in (
        ("manifest", manifest_path),
        ("catalog", catalog_path),
        ("DuckDB database", duckdb_path),
    ):
        if not path.exists():
            raise FileNotFoundError(
                f"{label.capitalize()} not found: {path}"
            )

    result = run_question(
        question=args.question,
        manifest=manifest_path,
        catalog=catalog_path,
        duckdb_path=duckdb_path,
        model=args.model,
    )

    output = json.dumps(
        result,
        indent=2,
        default=str,
    )

    print(output)

    if args.output:
        output_path = resolve_project_path(args.output)
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        output_path.write_text(
            output,
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
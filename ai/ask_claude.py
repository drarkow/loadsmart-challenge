"""Natural-language question -> Claude SQL -> read-only DuckDB execution."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

import duckdb
from anthropic import Anthropic
from dotenv import load_dotenv

from semantic_context import build_context


# ---------------------------------------------------------------------------
# Project configuration
# ---------------------------------------------------------------------------

# Repository root:
# <project_root>/ai/ask_claude.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load the project-level .env file.
load_dotenv(PROJECT_ROOT / ".env")


# ---------------------------------------------------------------------------
# Claude prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
You are a senior analytics engineer working over a documented dbt dimensional model.

Your task is to determine whether the user's question can be answered using the
supplied dbt metadata, and, only when it can, generate exactly one read-only
DuckDB SQL query.

Rules:

1. Use only relations and columns present in the supplied dbt metadata.

2. Prefer documented analytics dimensional models over staging/raw relations.

3. Treat dbt model and column descriptions as the source of truth for business
   semantics.

4. Use documented semantic fields and definitions when available instead of
   recreating them.

5. Do not invent business rules, entities, columns, tables, values, or metric
   definitions that are absent from the metadata.

6. Before writing SQL, check whether every important concept in the question is
   supported by the documented model.

7. Do not silently replace an undefined metric with a related metric.

   Examples:
   - "profitability after overhead" is NOT the same as "pnl > 0"
   - "pnl ratio" is NOT automatically pnl / book_price
   - a rating metric cannot be inferred from an unrelated carrier attribute

8. If the question requires information, business definitions, or calculations
   that are not documented in the model, do not generate SQL.

   Instead return exactly:
   UNSUPPORTED: <brief explanation of what is missing>

9. If the question is answerable, generate exactly one read-only DuckDB SQL query.

10. The SQL must use only documented relations and columns and must be a single
    SELECT or WITH statement.

11. Obtain factual results by executing the generated SQL against the database.
    Never answer from assumptions or from rows included in the prompt.

12. Return either:
    - a single SQL query, if the question is answerable
    - an UNSUPPORTED message, if it is not

13. Do not return markdown fences, explanations, or any other text.
""".strip()


# ---------------------------------------------------------------------------
# Path handling
# ---------------------------------------------------------------------------

def resolve_project_path(path_value: str | Path) -> Path:
    """
    Resolve a path relative to the repository root unless it is absolute.

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
    Validate Claude's response.

    Valid responses are either:
      - a single read-only SELECT/WITH query
      - an UNSUPPORTED: ... response
    """
    text = text.strip()

    # Explicitly supported non-answer.
    if text.startswith("UNSUPPORTED:"):
        return text

    # Remove markdown fences if Claude ignores the formatting instruction.
    text = re.sub(
        r"^```(?:sql)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    )

    # Only SELECT / WITH queries are allowed.
    if not re.match(
        r"^(select|with)\b",
        text,
        flags=re.IGNORECASE,
    ):
        raise ValueError(
            f"Claude returned invalid SQL.\nRaw response:\n{text}"
        )

    # Reject multiple statements.
    if ";" in text.rstrip(";"):
        raise ValueError(
            "Claude returned multiple SQL statements."
        )

    # Reject write / DDL / administrative operations.
    forbidden = re.compile(
        r"\b("
        r"insert|update|delete|drop|alter|create|truncate|"
        r"attach|copy|export|install|load|call"
        r")\b",
        flags=re.IGNORECASE,
    )

    if forbidden.search(text):
        raise ValueError(
            "Claude returned non-read-only SQL."
        )

    return text


# ---------------------------------------------------------------------------
# Claude interaction
# ---------------------------------------------------------------------------

def generate_sql(
    client: Anthropic,
    model: str,
    question: str,
    context: str,
) -> str:
    """Ask Claude to generate SQL or an UNSUPPORTED response."""
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
        raise ValueError("Claude returned no text.")

    return "\n".join(text_blocks)


# ---------------------------------------------------------------------------
# Question execution
# ---------------------------------------------------------------------------

def run_question(
    question: str,
    manifest_path: Path,
    catalog_path: Path,
    duckdb_path: Path,
    model: str,
) -> dict:
    """
    Generate SQL (or an UNSUPPORTED response) for a natural-language question,
    execute valid SQL against DuckDB, and return the result.
    """

    # Build semantic context directly from dbt artifacts.
    context = build_context(
        manifest_path=manifest_path,
        catalog_path=catalog_path,
    )

    # Validate API credentials.
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. "
            "Add it to your .env file or environment."
        )

    # Create the Anthropic client here so generate_sql() has a consistent
    # interface and does not need to know how credentials are loaded.
    client = Anthropic(api_key=api_key)

    # Generate SQL / UNSUPPORTED response from Claude.
    generated = generate_sql(
        client=client,
        model=model,
        question=question,
        context=context,
    )

    # Validate and classify Claude's response.
    result = extract_sql(generated)

    # Claude determined that the question cannot be answered from the
    # documented semantic model.
    if result.startswith("UNSUPPORTED:"):
        return {
            "question": question,
            "status": "unsupported",
            "generated_sql": None,
            "answer": None,
            "unsupported_reason": result.removeprefix(
                "UNSUPPORTED:"
            ).strip(),
        }

    sql = result

    # Execute the generated read-only SQL against DuckDB.
    try:
        conn = duckdb.connect(
            str(duckdb_path),
            read_only=True,
        )

        try:
            answer_df = conn.execute(sql).fetchdf()
        finally:
            conn.close()

    except Exception as exc:
        return {
            "question": question,
            "status": "sql_error",
            "generated_sql": sql,
            "answer": None,
            "execution_error": type(exc).__name__,
            "execution_error_message": str(exc),
        }

    # Convert the DataFrame into JSON-serializable records.
    answer = answer_df.to_dict(
        orient="records"
    )

    return {
        "question": question,
        "status": "success",
        "generated_sql": sql,
        "answer": answer,
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

    # Resolve all paths from the project root.
    manifest_path = resolve_project_path(args.manifest)
    catalog_path = resolve_project_path(args.catalog)
    duckdb_path = resolve_project_path(args.duckdb)

    # Fail early with readable errors instead of opaque file/database errors.
    for label, path in (
        ("Manifest", manifest_path),
        ("Catalog", catalog_path),
        ("DuckDB database", duckdb_path),
    ):
        if not path.exists():
            raise FileNotFoundError(
                f"{label} not found: {path}"
            )

    result = run_question(
        question=args.question,
        manifest_path=manifest_path,
        catalog_path=catalog_path,
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
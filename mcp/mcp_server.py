"""MCP server exposing the Loadsmart AI analytics layer.

The MCP server is a thin interface around the existing `run_question()`
implementation. It does not duplicate SQL generation, semantic-context
construction, validation, or DuckDB execution logic.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from mcp.server import MCPServer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AI_DIR = PROJECT_ROOT / "ai"

# The existing AI modules use local imports (for example, semantic_context),
# so make both the repository root and ai/ directory importable when this
# server is launched as `python mcp\mcp_server.py`.
for import_path in (PROJECT_ROOT, AI_DIR):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

from ask_claude import resolve_project_path, run_question


# ---------------------------------------------------------------------------
# Project configuration
# ---------------------------------------------------------------------------

load_dotenv(PROJECT_ROOT / ".env")


MANIFEST_PATH = resolve_project_path(
    os.environ.get(
        "DBT_MANIFEST_PATH",
        "dbt_loadsmart/target/manifest.json",
    )
)

CATALOG_PATH = resolve_project_path(
    os.environ.get(
        "DBT_CATALOG_PATH",
        "dbt_loadsmart/target/catalog.json",
    )
)

DUCKDB_PATH = resolve_project_path(
    os.environ.get(
        "DUCKDB_PATH",
        "data/loadsmart.duckdb",
    )
)

CLAUDE_MODEL = os.environ.get(
    "CLAUDE_MODEL",
    "claude-sonnet-5",
)


# ---------------------------------------------------------------------------
# Validation at import/startup time
# ---------------------------------------------------------------------------

for label, path in (
    ("Manifest", MANIFEST_PATH),
    ("Catalog", CATALOG_PATH),
    ("DuckDB database", DUCKDB_PATH),
):
    if not path.exists():
        raise FileNotFoundError(
            f"{label} not found: {path}"
        )

if not os.environ.get("ANTHROPIC_API_KEY"):
    raise RuntimeError(
        "ANTHROPIC_API_KEY is not set. "
        "Add it to the project .env file before starting the MCP server."
    )


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

mcp = MCPServer(
    "Loadsmart Analytics",
    log_level="INFO",
)


@mcp.tool()
def ask_loadsmart(question: str) -> dict:
    """Answer a natural-language question over the documented Loadsmart dbt model.

    The tool reuses the existing AI analytics layer. Schema context is generated
    from dbt manifest/catalog artifacts, generated SQL is validated as read-only,
    and valid SQL is executed against the DuckDB dimensional model.
    """

    return run_question(
        question=question,
        manifest_path=MANIFEST_PATH,
        catalog_path=CATALOG_PATH,
        duckdb_path=DUCKDB_PATH,
        model=CLAUDE_MODEL,
    )


if __name__ == "__main__":
    # Streamable HTTP is convenient for demonstrating the bonus with a separate
    # MCP client. The same server can also run over stdio with `mcp run`.
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8000,
    )

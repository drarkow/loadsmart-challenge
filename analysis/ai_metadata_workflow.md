# AI metadata workflow

The AI layer must not receive raw table rows as context. Its schema context is generated programmatically from dbt artifacts:

1. Run `dbt docs generate` to produce `target/manifest.json` and `target/catalog.json`.
2. Run `python ai/semantic_context.py` from the repository root.
3. The script generates `analysis/dbt_semantic_context.json` from model descriptions, column descriptions, catalog data types, materializations, and dbt test names.
4. `ai/ask_claude.py` sends that generated metadata to Claude with a generic SQL-generation contract.
5. Claude generates one read-only SQL statement.
6. The statement is executed against the local DuckDB database opened read-only.
7. The script returns both the generated SQL and its result.

Business definitions belong in dbt model/column descriptions so that changes to the semantic model automatically propagate to the AI context.

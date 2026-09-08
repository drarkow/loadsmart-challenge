# AI prompt contract

The AI receives schema metadata generated from the current dbt artifacts. The authoritative semantic contract is the model and column documentation in dbt YAML, supplemented by catalog data types from `catalog.json`.

## Metadata source

`ai/semantic_context.py` reads:

- `dbt_loadsmart/target/manifest.json`
- `dbt_loadsmart/target/catalog.json`

The script generates model/column metadata programmatically. It must be re-run after `dbt docs generate` when the model or documentation changes.

## Agent contract

The agent must:

- use only documented dbt relations and columns;
- prefer the analytics dimensional models over staging/raw relations;
- treat dbt model/column descriptions as the source of truth for business semantics;
- use documented semantic fields when they exist rather than recreating definitions from intuition;
- obtain facts by executing SQL and never from prompt-included table rows;
- return exactly one read-only DuckDB SQL statement.

The prompt should not contain hand-written table schemas, column lists, business definitions, or sample table rows.

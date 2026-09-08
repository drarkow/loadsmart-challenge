# AI prompt contract

The AI receives only metadata generated from dbt artifacts. The authoritative contract is the descriptions in dbt model/column YAML plus the catalog data types.

The agent must:

- use only documented dbt relations/columns;
- prefer `analytics.fct_loads` and the dimensions;
- use `is_delivered` for delivered-load questions;
- use `haul_type` for intrastate/interstate questions;
- return one read-only DuckDB SQL statement;
- obtain facts by executing SQL, never by reasoning from prompt-included rows.

The prompt should not contain hard-coded table definitions. `ai/semantic_context.py` generates the metadata payload from `manifest.json` and `catalog.json` after `dbt docs generate`.

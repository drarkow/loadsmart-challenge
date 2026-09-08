# Loadsmart Analytics Engineer Challenge

This repository implements the Loadsmart Analytics Engineer challenge using **dbt + DuckDB**, followed by a metadata-driven natural-language-to-SQL layer using the Claude API.

## Architecture

```text
challenge CSV
    |
    v
DBT seed: raw.raw_loads
    |
    v
staging view: staging.stg_loads
    |
    v
analytics star schema
    |---- dim_date
    |---- dim_shipper
    |---- dim_carrier
    |---- dim_lane
    `---- fct_loads
             |
             +--> question validation
             `--> Claude metadata-to-SQL layer
```

The raw source is retained through `dbt seed`. Data-quality findings are documented before business semantics are applied. The dimensional fact grain is one row per distinct `loadsmart_id`.

## Why DuckDB

DuckDB avoids a local database server and makes the challenge reproducible from a cloned repository. The dbt project still demonstrates the requested ingestion, modeling, testing, and documentation workflow.

## Local setup

### Windows PowerShell

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup.ps1
cd dbt_loadsmart
dbt debug
dbt build
dbt docs generate
```

### Environment variables for Claude

Copy `.env.example` to `.env` or export variables in the shell. Never commit the real key.

```text
ANTHROPIC_API_KEY=...
CLAUDE_MODEL=claude-sonnet-5
DUCKDB_PATH=data/loadsmart.duckdb
```

## Data quality findings

See `analysis/data_quality_profile.md` and `analysis/business_definitions.md`.

Key findings include four exact duplicate source rows, sparse carrier/sourcing attributes, 517 cancelled loads, zero-value financial fields, and delivery/pickup timestamp anomalies. The source-level duplicate rows are removed in staging, not in the raw seed. The anomalies are retained and documented rather than silently filtered.

## AI layer

The AI layer follows the challenge contract:

1. Run `dbt docs generate`.
2. `ai/semantic_context.py` reads `manifest.json` and `catalog.json` programmatically.
3. The generated metadata is passed to Claude; raw table rows are never included in the prompt.
4. Claude returns read-only SQL against the dbt dimensional model.
5. The SQL is executed in DuckDB and both SQL and answer rows are returned.

Example:

```powershell
python ai/ask_claude.py "What are the top 5 lanes by number of delivered loads?"
```

The challenge asks for an initial run, explicit failure classification, a model/YML/prompt fix, and a second run. See `analysis/iteration_log.md` and `analysis/question_results.csv`.

## Python export

The requested notebook is `notebooks/export_delivered_loads.ipynb`. The reusable script it calls is `scripts/export_delivered_loads.py`.

```powershell
python scripts/export_delivered_loads.py
```

## Reproducibility

The source CSV should remain unchanged in `data/raw/loads.csv` and is copied to the dbt seed directory by `setup.ps1`.

The current repository intentionally does not include generated `target/` artifacts or a DuckDB database file; those are reproducible with the commands above.

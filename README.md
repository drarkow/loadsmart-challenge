# Loadsmart Analytics Engineer Challenge

This repository implements the Loadsmart Analytics Engineer challenge using **dbt + DuckDB**, followed by a metadata-driven natural-language-to-SQL layer using the Claude API.

> Runtime note: Python 3.13 is the recommended interpreter for this challenge. `setup.ps1` will prefer it automatically when available.

## Architecture

```text
challenge CSV
    |
    v
DBT seed: main_raw.raw_loads
    |
    v
staging view: main_staging.stg_loads
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

DuckDB avoids a local database server and makes the challenge reproducible from a cloned repository. The dbt project demonstrates the requested ingestion, dimensional modeling, testing, and documentation workflow.

## Local setup

### Windows PowerShell

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup.ps1
cd dbt_loadsmart
dbt debug
dbt build
dbt docs generate
cd ..
```

`dbt debug` should report an OK DuckDB connection before continuing. Keep the working local profile in `%USERPROFILE%\.dbt\profiles.yml`; the repository only contains `profiles.yml.example`.

## Data quality findings

See `analysis/data_quality_profile.md` and `analysis/business_definitions.md`.

The source contains four exact duplicate records by `loadsmart_id`, sparse carrier/sourcing attributes, 516 cancelled loads after deduplication, zero-value financial fields, and lifecycle timestamp anomalies. The source-level duplicate rows are removed in staging, not in the raw seed. Anomalies are retained and documented rather than silently filtered.

The current warning tests intentionally focus on business-significant anomalies:

- delivered loads with zero `book_price`;
- delivered loads with zero `source_price`;
- delivery before booking;
- delivery before pickup;
- zero mileage when normalized pickup and delivery cities differ.

Hard model-contract failures (for example uniqueness and required relationships) use `severity: error`; source/business-quality exceptions use `severity: warn`. dbt tests report violating rows and do not automatically delete them from a model.

## AI layer

The AI layer follows the challenge contract. The semantic context is **never hand-written**. It is generated programmatically from the dbt artifacts produced by `dbt docs generate`: `manifest.json` and `catalog.json`.

### Generate semantic context

From the repository root:

```powershell
python ai/semantic_context.py
```

This writes `analysis/dbt_semantic_context.json` for local inspection. It is a generated artifact and is ignored by Git; Claude does not depend on a hand-maintained copy of it. The source of truth is always the current dbt artifacts.

The generated context contains, for each dbt model:

- relation/database/schema/identifier;
- materialization;
- model description;
- column names;
- column descriptions;
- catalog data types.

Raw table rows are never sent to Claude.

### Ask Claude a question

Set the API credentials as environment variables and never commit the key:

```powershell
$env:ANTHROPIC_API_KEY="your-key-here"
$env:CLAUDE_MODEL="claude-sonnet-5"
$env:DUCKDB_PATH="loadsmart.duckdb"
```

Then:

```powershell
python ai/ask_claude.py "Which shipper had the highest total book price?"
```

The script:

1. loads current dbt manifest/catalog metadata;
2. asks Claude for one read-only DuckDB SQL statement;
3. validates that the response is a single `SELECT`/`WITH` statement;
4. executes it against DuckDB in read-only mode;
5. returns the question, generated SQL, and result rows.

The model/column descriptions in dbt are the semantic contract. The system prompt contains execution and safety rules but does not hard-code the dimensional schema or business definitions.

## Required question set

The eight challenge questions are defined in `ai/questions.yml`. Two additional stakeholder questions are also included there. `analysis/expected_answers.md` contains independently validated baselines; `analysis/question_results.csv` is the submission-oriented result table to update after running Claude.

The challenge requires an initial AI run, explicit classification of failures, a fix in the prompt/YML/model as appropriate, and a re-run. Record that process in `analysis/iteration_log.md`.

## Python export

The requested notebook is `notebooks/export_delivered_loads.ipynb`. The reusable script it calls is `scripts/export_delivered_loads.py`.

```powershell
python scripts/export_delivered_loads.py
```

## Reproducibility

The source CSV should remain unchanged in `data/raw/loads.csv` and is copied to the dbt seed directory by `setup.ps1`.

Generated `target/` files and the DuckDB database are present only in some local working copies; they are reproducible with the commands above and are ignored by Git for fresh clones.

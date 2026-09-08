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
staging views: stg_loads
    |
    v
analytics star schema
    |---- dim_date
    |---- dim_shipper
    |---- dim_carrier
    |---- dim_lane
    `---- fct_loads
             |
             +--> question set / SQL validation
             `--> Claude metadata-to-SQL layer
```

The raw data is deliberately retained without business-rule cleanup. Data-quality findings are documented before transformations are applied.

## Local setup

### Windows PowerShell

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup.ps1
```

Then:

```powershell
cd dbt_loadsmart
dbt seed
dbt run
dbt test
dbt docs generate
```

### Manual setup

```bash
python -m venv .venv
# activate the environment
pip install -r requirements.txt
```

Copy `dbt_loadsmart/profiles.yml.example` to `~/.dbt/profiles.yml`, then run:

```bash
cd dbt_loadsmart
dbt debug
dbt seed
dbt build
dbt docs generate
```

## Important reproducibility note

The supplied CSV is stored in `data/raw/loads.csv` for local execution. The setup script copies it into `dbt_loadsmart/seeds/raw_loads.csv` so dbt manages the raw relation through `dbt seed`.

Do not commit `.env` or any API credentials.

## Current status

This first stage establishes the environment and repository structure. The dimensional model, dbt tests/documentation, AI SQL layer, iteration log, and Python export notebook are built on top of this foundation.

# Loadsmart Analytics Engineer Challenge

This repository implements the Loadsmart Analytics Engineer challenge using **dbt + DuckDB**, followed by a metadata-driven natural-language-to-SQL layer using the Claude API.

The solution is intentionally centered on the **dbt dimensional model and its documentation as the semantic contract for AI**. The AI layer does not receive table rows or a hand-written schema description; it receives metadata generated from dbt artifacts (`manifest.json` and `catalog.json`) and executes the resulting read-only SQL against the modeled DuckDB database.

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
analytics dimensional model
    |---- main_analytics.dim_date
    |---- main_analytics.dim_shipper
    |---- main_analytics.dim_carrier
    |---- main_analytics.dim_lane
    `---- main_analytics.fct_loads
             |
             +--> Python export
             |
             `--> Claude metadata-to-SQL layer
                       |
                       v
                  DuckDB execution
```

The raw source is retained through `dbt seed`. Data-quality findings are investigated before business semantics are applied. The dimensional fact grain is **one row per distinct `loadsmart_id`**.

## Repository structure

```text
.
├── ai/
│   ├── ask_claude.py
│   ├── run_questions.py
│   ├── semantic_context.py
│   └── questions.yml
├── analysis/
│   ├── business_definitions.md
│   ├── data_quality_profile.md
│   ├── dbt_semantic_context.json
│   ├── iteration_log.md
│   ├── claude_question_runs.jsonl
├── data/
│   └── raw/
│       └── loads.csv
├── dbt_loadsmart/
│   ├── models/
│   │   ├── staging/
│   │   └── marts/
│   ├── seeds/
│   ├── dbt_project.yml
│   └── target/                 # generated locally, not committed
├── notebooks/
│   └── export_delivered_loads.ipynb
├── scripts/
├── .env.example
├── requirements.txt
├── setup.ps1
└── README.md
```

## Why DuckDB

DuckDB avoids requiring a local database server and makes the solution reproducible from a cloned repository. The dbt project still demonstrates the requested ingestion, dimensional modeling, testing, and documentation workflow.

## Local setup

### Windows PowerShell

From the repository root:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup.ps1
```

Then build the dbt project:

```powershell
cd dbt_loadsmart
dbt debug
dbt seed
dbt build
dbt docs generate
cd ..
```

`dbt build` recreates the database objects and runs the documented data-quality tests. `dbt docs generate` refreshes `target/manifest.json` and `target/catalog.json`, which are the artifacts consumed by the AI layer.

### Environment variables for Claude

Copy `.env.example` to `.env` and add the API key. Never commit `.env` or an API key.

```text
ANTHROPIC_API_KEY=...
CLAUDE_MODEL=claude-sonnet-5
DUCKDB_PATH=data/loadsmart.duckdb
DBT_MANIFEST_PATH=dbt_loadsmart/target/manifest.json
DBT_CATALOG_PATH=dbt_loadsmart/target/catalog.json
```

The scripts resolve relative paths from the repository root, so the same commands work regardless of the current PowerShell directory.

## Dimensional model

### Fact grain

`fct_loads` has one row per distinct `loadsmart_id`. Exact duplicate source rows are removed in staging while the raw seed remains unchanged.

### Main dimensions

- `dim_date` — complete calendar covering the relevant lifecycle dates, allowing month-level analysis to retain periods with zero delivered activity.
- `dim_shipper` — shipper attributes and surrogate key.
- `dim_carrier` — carrier attributes and surrogate key, including the documented `carrier_rating` field.
- `dim_lane` — normalized pickup/delivery lane information.

### Load semantics

The model documents and applies the following business definitions:

- **Delivered load:** `NOT load_was_cancelled AND delivered_at IS NOT NULL`.
- **Intrastate load:** pickup state equals delivery state.
- **Interstate load:** pickup state differs from delivery state.
- **Lane:** normalized pickup city/state to delivery city/state relationship.
- **Unknown carrier:** mapped to a reserved dimension member instead of leaving an invalid foreign key.

A complete `dim_date` is generated across the modeled lifecycle dates so that monthly trend queries can distinguish a true zero-activity month from a missing calendar row.

## Data quality investigation

The raw dataset contains a mixture of structural issues and legitimate business anomalies. The repository documents these findings in `analysis/data_quality_profile.md` and keeps the raw seed unchanged.

Key findings and treatment include:

| Finding | Treatment |
|---|---|
| Exact duplicate source rows | Deduplicated in staging using `loadsmart_id`; raw seed retained unchanged |
| Cancelled loads with zero financial values | Retained; zero-value pricing tests focus on delivered loads where the values are analytically relevant |
| Delivered loads with zero `book_price` | Retained and surfaced as a warning rather than silently filtered |
| Delivered loads with zero `source_price` | Retained and surfaced as a warning rather than silently filtered |
| Delivery timestamp earlier than booked/pickup timestamp | Retained and surfaced as warning-level temporal anomalies |
| Zero mileage while pickup and delivery cities differ | Retained and surfaced as a warning; the rule is city-based rather than state-based |
| Source timestamp strings using `M/D/YYYY HH:MM` | Parsed explicitly with DuckDB `try_strptime` rather than generic casting |

The latest successful build in the working history reports the dbt data-quality suite completing without test errors; the anomaly tests intentionally use warning severity where the underlying records are retained for traceability. The repository also documents the distinction between **contract failures** and **data anomalies**: structural tests should fail the build, while questionable source/business values are reported for investigation.

## Data quality test philosophy

Tests are grouped conceptually as follows:

- **Error-level contract tests:** primary keys, required fields, accepted categorical values, and dimension relationships that should hold for the modeled dataset.
- **Warning-level anomaly tests:** questionable but usable source records, such as zero pricing on delivered loads, temporal inconsistencies, or zero mileage between different cities.

A dbt test with warning severity does **not** remove data. It reports violating rows while allowing the build to continue. Error-level tests protect the structural contract.

## AI-over-the-model layer

The AI exercise follows the challenge requirement that dbt YAML is the contract between the semantic model and the AI. The challenge explicitly requires schema context to be generated programmatically from `manifest.json` / `catalog.json`, not hand-written into the prompt, and prohibits sending table rows as context. citeturn12file4

### Flow

1. Run `dbt docs generate`.
2. `ai/semantic_context.py` reads the generated `manifest.json` and `catalog.json`.
3. It builds a metadata-only context containing model/relation names, column names, types, descriptions, and relevant dbt metadata.
4. `ai/ask_claude.py` sends that context plus the natural-language question to Claude.
5. Claude must either:
   - return one read-only `SELECT`/`WITH` query, or
   - return `UNSUPPORTED: ...` when the documented model cannot safely answer the question.
6. The generated SQL is validated before execution.
7. Valid SQL is executed against DuckDB in read-only mode.
8. The result includes the question, generated SQL, status, and answer rows.

No table rows are loaded into the Claude prompt.

### Run one question

From the repository root:

```powershell
python ai\ask_claude.py "What are the top 5 lanes by number of delivered loads?"
```

### Run the complete question set

```powershell
python ai\run_questions.py
```

Results are written to:

```text
analysis/claude_question_runs.jsonl
```

The challenge results table is documented in this README, while the full generated SQL and answer payloads are retained in `analysis/claude_question_runs.jsonl`.

## Question set results

The following results are based on the modeled dimensional data.

| ID | Question | Result / expected interpretation | Correct? | Notes |
|---|---|---|---|---|
| Q1 | How many loads were delivered in the last full month available in the data? | **0 delivered loads** in February 2025 | Yes | March 2025 contains only a partial month (one delivery), so February is treated as the last complete calendar month. |
| Q2 | Which shipper had the highest total book price? | **Shipper 1249 — $1,915,694.16** | Yes | Aggregated book price across the modeled loads. |
| Q3 | What is the average book price per load by pickup state? | State-level average across modeled loads | Yes | The wording does not restrict this question to delivered loads, so all modeled loads are used. |
| Q4 | What are the top 5 lanes by number of delivered loads? | Hawkins, TX → Roanoke, TX (882); Lodi, CA → Pacific, WA (150); Kent, WA → Spokane, WA (94); Henderson, NV → Tracy, CA (87); Taft, CA → Tracy, CA (72) | Yes | Delivered status follows the documented `is_delivered` semantics. |
| Q5 | Which carrier moved the most loads into Texas? | **Carrier 567581 — 188 delivered loads into Texas** | Yes | Destination state filtered to Texas and delivered loads counted. |
| Q6 | How does the average book price compare between intrastate and interstate loads? | **Interstate: $1,709.33; Intrastate: $584.17** | Yes | Uses the documented `haul_type` classification. |
| Q7 | For the shipper with the most delivered loads, how did monthly volume change across the period covered by the data? | **Shipper 758**; monthly delivered volume declines sharply in 2025, with **0 in Feb 2025** and **1 in Mar 2025** | Yes | `dim_date` is used so zero-activity months are retained. |
| Q8 | Among lanes with at least 10 delivered loads, which had the highest average book price? | **Stockton, CA → Parrish, FL — 11 loads; $6,800 average book price** | Yes | Minimum lane volume applied before ranking by average price. |
| Q9 | What are the top 10 lanes in terms of P&L ratio? | **Unsupported in final AI run** | No / semantic gap | The raw fact model contains `pnl` and `book_price`, but the dbt artifacts do not define the business meaning of "P&L ratio". The question-level assumption was intentionally kept outside the AI context to preserve the dbt-artifact-only contract. |
| Q10 | Among carriers with ratings, what is the average carrier rating and number of ratings for each carrier with rating below 3? | Carriers grouped by documented `carrier_rating`, with average rating < 3.0 | Yes | `carrier_rating` was added to the dbt documentation so it became available through the generated semantic context. |
| Q11 | What percentage of each shipper's delivered loads were profitable after accounting for transportation costs and operating overhead? | **Unsupported in final AI run** | Yes | Operating overhead is not present and no documented allocation methodology exists. The AI was explicitly prevented from substituting `pnl > 0` for profitability after overhead. |

The full generated SQL and answer payloads are retained in `analysis/claude_question_runs.jsonl`. The README contains the summarized results and correctness assessment requested by the challenge.

## Ambiguity and business assumptions

The challenge explicitly notes that some questions are intentionally ambiguous and asks the candidate to state the assumptions made. citeturn12file5

Important assumptions in this solution include:

### Q1 — Last full month

I interpret "last full month available" as the **latest complete calendar month before the final partial month represented in the data**. The data contains a delivery in March 2025, but March is incomplete; February 2025 is therefore the last full month and has zero delivered loads.

### Q3 — Average book price by pickup state

The question does not say "delivered loads", so the calculation is performed over the full modeled population rather than only delivered loads.

### Q7 — Monthly volume

The monthly series is generated from `dim_date` rather than only existing delivery rows so that months with zero delivered loads remain visible.

### Q9 — P&L ratio

The business interpretation would reasonably need a documented formula such as `SUM(pnl) / SUM(book_price)`, but that formula is intentionally **not supplied to Claude outside the dbt artifacts**. The final AI result therefore demonstrates the semantic-model gap rather than hiding it with a prompt-side assumption.

### Q10 — Carrier rating

The working assumption is: use non-null `carrier_rating`, calculate the average and count of ratings per carrier, and return carriers whose average rating is below 3.0.

### Q11 — Profitability after overhead

A positive load-level `pnl` is not treated as equivalent to profitability after operating overhead. An overhead dataset and a defined allocation methodology would be required to answer the question correctly.

## AI iteration log

The challenge requires an initial run, identification of incorrect or ambiguous responses, a decision on whether the fix belongs in the prompt, YAML documentation, or the model, followed by a rerun and before/after comparison. citeturn12file7

| Question | First run | Diagnosis | Fix | Final run |
|---|---|---|---|---|
| Q1–Q8 | Correct / usable | No material semantic failures | None required | Correct |
| Q9 | Claude refused: P&L ratio was undefined | The formula was not documented in dbt artifacts | **YAML/model documentation gap** identified. The question-level assumption was deliberately not passed into Claude because the AI contract is dbt-artifact-only | Still `UNSUPPORTED` — intentionally exposes the documentation gap |
| Q10 | Claude initially refused because carrier rating was missing from its metadata context | `carrier_rating` existed in `fct_loads` but was not documented in the dbt semantic metadata | **YAML documentation**: added `carrier_rating` to the documented fact model; rebuilt dbt artifacts and regenerated docs | Correct SQL generated and executed successfully |
| Q11 | Claude incorrectly substituted `pnl > 0` for "profitable after accounting for transportation costs and operating overhead" | Semantic substitution / hallucinated proxy metric | **Prompt**: explicitly prohibit substituting a related metric and require `UNSUPPORTED:` when required information or definitions are unavailable | Correctly returns `UNSUPPORTED` with the missing overhead requirement |

### Why Q9 was left unresolved

The challenge emphasizes that dbt YAML should function as the contract between the semantic model and the AI. citeturn12file4 Rather than injecting the question's `business_definition` from `questions.yml` into the Claude prompt, the implementation keeps Claude dependent only on generated dbt artifacts. This makes Q9 a useful demonstration of a genuine semantic-layer gap: the model contains the underlying measures, but the business metric itself is not yet documented in dbt.

### Why Q10 required documentation rather than prompt changes

The `carrier_rating` field is present in the fact model. The failure occurred because the field was not part of the documented metadata supplied to Claude. Adding the column documentation and regenerating the dbt artifacts fixed the issue without changing the AI prompt.

### Why Q11 required a prompt change

The model contains load-level P&L, but the question asks for profitability **after operating overhead**. The first AI run silently converted that into `pnl > 0`, which is not equivalent. The prompt was therefore strengthened to require an explicit `UNSUPPORTED:` response rather than silently substituting a related metric.

## Python export

The challenge requests a Jupyter Notebook that reads the dimensional model and exports delivered loads from the **last available month** represented in the data.

The notebook is self-contained:

```text
notebooks/export_delivered_loads.ipynb
```

It resolves the repository root, reads `main_analytics` from DuckDB, finds the latest `delivery_date` month, filters to delivered loads, validates the required columns, and writes the CSV export. It does not depend on an external Python script.

The exported fields are:

```text
loadsmart_id
shipper_name
delivery_date
pickup_city
pickup_state
delivery_city
delivery_state
book_price
carrier_name
```

## Power BI bonus

The Power BI report uses the same modeled DuckDB database produced by dbt:

```text
data/loadsmart.duckdb
```

Configure the DuckDB Windows ODBC DSN to point to this file. Power BI Desktop uses the generic ODBC connector in **Import** mode.

### Important Power BI setting

DuckDB's ODBC driver can conflict with Power BI Desktop's parallel table-loading behavior because Power BI may open multiple connections to the same DuckDB file. In Power BI Desktop, disable:

**File → Options and settings → Options → Current File → Data Load → Enable parallel loading of tables**

Then reconnect to the DuckDB DSN and import the `main_analytics` tables together. This avoids the `SQLDriverConnect` / `file is already open by Microsoft.Mashup.Container.NetFX45.exe` error encountered when Power BI opens the DuckDB file concurrently.

No Power BI-specific DuckDB copy is required.

## Reproducibility checklist

From a clean clone, run the setup script from the repository root:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup.ps1
```

`setup.ps1` creates or reuses `.venv`, installs the pinned dependencies, creates the dbt profile, and copies the source CSV into the dbt seed directory. The profile is named `loadsmart_analytics` to match `dbt_project.yml` and uses the portable path `../data/loadsmart.duckdb`; this is resolved correctly because the documented dbt commands are run from `dbt_loadsmart`. No machine-specific absolute path is stored in the repository.

Build the database and generate dbt artifacts:

```powershell
cd dbt_loadsmart
dbt debug
dbt seed
dbt build
dbt docs generate
cd ..
```

The AI layer then uses:

```text
data/loadsmart.duckdb
dbt_loadsmart/target/manifest.json
dbt_loadsmart/target/catalog.json
```

The `.env.example` defaults remain repository-relative:

```text
ANTHROPIC_API_KEY=...
CLAUDE_MODEL=claude-sonnet-5
DUCKDB_PATH=data/loadsmart.duckdb
DBT_MANIFEST_PATH=dbt_loadsmart/target/manifest.json
DBT_CATALOG_PATH=dbt_loadsmart/target/catalog.json
```

For the optional Power BI report, connect the ODBC DSN directly to `data/loadsmart.duckdb` and disable Power BI parallel table loading as described above.

## Outputs

Key outputs produced by the solution are:

| Output | Purpose |
|---|---|
| `data/loadsmart.duckdb` | Local working DuckDB database generated by dbt |
| `dbt_loadsmart/target/manifest.json` | dbt metadata used to construct the AI schema context |
| `dbt_loadsmart/target/catalog.json` | dbt catalog metadata used to construct the AI schema context |
| `analysis/dbt_semantic_context.json` | Human-inspectable generated semantic context |
| `analysis/claude_question_runs.jsonl` | AI-generated SQL, execution status, and answers |
| `analysis/iteration_log.md` | Before/after AI iteration analysis |

Generated `target/` artifacts and local DuckDB databases are intentionally reproducible and should not be committed to version control.

## Security and credentials

The Anthropic API key is read from `ANTHROPIC_API_KEY`. No key is stored in source code. The `.env` file should remain local and be excluded from Git.

The AI execution layer opens DuckDB in read-only mode and rejects SQL containing write/DDL/administrative operations before execution.

## Scope and optional items

The core submission focuses on the required areas: dimensional modeling, tests, documentation, data-quality investigation, AI-over-the-model, the required question set, iteration log, and Python export. The BI report is optional in the challenge. citeturn11file0

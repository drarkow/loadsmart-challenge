# Dependency choices

## Runtime

Python 3.13 is the recommended runtime for this challenge. The project is a local DuckDB/dbt stack, and dbt-duckdb 1.11.0 currently publishes Python 3.13 classifiers. dbt-core 1.12.4 officially supports Python 3.10 through 3.14.

## Core stack

- `dbt-core==1.12.4`
- `dbt-duckdb==1.11.0`
- `importlib-metadata==8.7.0`

The explicit `importlib-metadata` pin avoids the dependency conflict encountered with `dbt-semantic-interfaces` when an unconstrained newer release was installed.

## AI / analysis stack

- `anthropic==1.4.0`
- `pandas==3.0.5`
- `jupyter==1.1.1`
- `pyyaml==6.0.2`

Top-level packages are pinned so a fresh setup does not silently move to unrelated future major/minor releases. Transitive dependencies remain resolved by pip from the dbt package constraints.

# DuckDB ODBC setup for Power BI Desktop

Power BI Desktop can use the generic ODBC connector. For this project, configure the DuckDB Windows ODBC driver and point the DSN at the generated DuckDB database.

## 1. Install DuckDB ODBC

Download the Windows x86_64/AMD64 ODBC asset from the DuckDB releases/install page and extract it to a permanent directory.

Run `odbc_install.exe` from the extracted directory. The installer registers the DuckDB ODBC driver and a default DSN.

## 2. Point the DSN at the project database

Open the Windows ODBC Data Source Administrator and configure the DuckDB DSN so that its database points to:

`<repository-root>\\data\\loadsmart.duckdb`

Using the absolute path is recommended for the Power BI proof of concept.

## 3. Connect in Power BI Desktop

Use:

**Home -> Get data -> ODBC**

Select the configured DuckDB DSN and choose **Import**.

Import:

- `main_analytics.fct_loads`
- `main_analytics.dim_shipper`
- `main_analytics.dim_carrier`
- `main_analytics.dim_lane`
- `main_analytics.dim_date`

**Important: On PowerBI, disable the parallel loading of table in File → Options and settings → Options → Current File → Data Load, otherwise Duckdb data will not be loaded as import**

## 4. Rebuild after dbt changes

If the dbt model changes, regenerate the DuckDB database before refreshing Power BI:

```powershell
cd dbt_loadsmart
dbt seed
dbt build
dbt docs generate
cd ..
```

Then refresh the Power BI model.

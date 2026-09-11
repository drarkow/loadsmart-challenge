# Power BI bonus dashboard

## Purpose

This folder documents the Power BI proof-of-concept built on the modeled DuckDB star schema.
The recommended approach is to connect Power BI Desktop to DuckDB through the DuckDB ODBC driver and import the modeled tables rather than rebuilding business logic from the raw CSV.

## Source model

Import these five modeled relations:

- `main_analytics.fct_loads`
- `main_analytics.dim_shipper`
- `main_analytics.dim_carrier`
- `main_analytics.dim_lane`
- `main_analytics.dim_date`

The fact grain is one row per `loadsmart_id`.

## Power BI connection

1. Install the DuckDB Windows ODBC driver.
2. Configure a DuckDB DSN pointing to the repository database:

Download the latest stable Windows x86_64 DuckDB ODBC driver from the official duckdb/duckdb-odbc GitHub releases page. At the time of this challenge, the latest stable release is 1.5.5.0.

   `data/loadsmart.duckdb`

3. Open Power BI Desktop.
4. Select **Get data -> ODBC**.
5. Select the DuckDB DSN and choose **Import**.
6. Select the five `main_analytics` tables listed above.

Import mode is recommended for this local proof of concept.

## Relationships

Create these single-direction relationships from dimensions to the fact:

- `dim_shipper[shipper_key]` 1 -> * `fct_loads[shipper_key]`
- `dim_carrier[carrier_key]` 1 -> * `fct_loads[carrier_key]`
- `dim_lane[lane_key]` 1 -> * `fct_loads[lane_key]`
- `dim_date[date_day]` 1 -> * `fct_loads[delivery_date]` (active)
- `dim_date[date_day]` 1 -> * `fct_loads[booked_date]` (inactive)
- `dim_date[date_day]` 1 -> * `fct_loads[pickup_date]` (inactive)

Use delivery date as the default active date relationship because the primary dashboard is centered on delivered-load performance.

## Recommended report pages

### 1. Executive Overview

KPI cards:

- Total Loads
- Delivered Loads
- Delivery Rate
- Total Book Price
- Total P&L
- P&L Margin
- Average Book Price / Load

Visuals:

- Monthly delivered-load trend
- Monthly book price trend
- Delivered loads by haul type
- Top 10 shippers by book price

### 2. Lane & Geography

Visuals:

- Top 10 lanes by delivered loads
- Top 10 lanes by average book price
- Pickup state: average book price and load count
- Intrastate vs interstate comparison
- Texas inbound carrier ranking

### 3. Carrier Performance

Visuals:

- Loads by carrier
- Average carrier rating
- Carrier on-time performance
- Delivered loads vs P&L
- Carrier performance table with conditional formatting

### 4. Shipper Performance

Visuals:

- Delivered loads by shipper
- Book price by shipper
- P&L by shipper
- Monthly volume for the selected shipper

## Important semantic choices

- Delivered = `is_delivered = TRUE`.
- Intrastate/interstate comes from the documented `haul_type` field.
- P&L is load-level `fct_loads[pnl]`.
- P&L margin is calculated as `P&L / Book Price` and should be clearly labeled as a reporting ratio, not treated as an independently documented source metric.
- Zero prices are retained in the model; metrics should not silently filter them unless the visual explicitly documents the reason.

## Suggested slicers

- Delivery year/month
- Shipper
- Carrier
- Pickup state
- Delivery state
- Haul type
- Equipment type
- Sourcing channel
- VIP carrier

## DAX

See `DAX_measures.md` for the recommended measures and inactive-date examples.

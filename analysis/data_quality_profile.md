# Raw data quality findings

The source contains 5,361 rows and 31 columns.

## Findings

- `loadsmart_id` has 4 duplicated IDs, representing 4 exact duplicate rows. The staging model keeps one row per ID.
- `has_mobile_app_tracking.1` is an apparent duplicate source field and is constant (`False`) in every source row. It is not promoted into the dimensional model; the original raw seed retains it.
- `sourcing_channel` is sparse: 5,117 of 5,361 rows are null.
- `carrier_rating` is sparse: 4,614 rows are null; observed non-null values are 0–5.
- `carrier_name` is null for 499 rows.
- 517 loads are marked cancelled.
- There are 530 zero `book_price` values and 519 zero `source_price` values. No negative book/source prices occur. Zeroes are retained because the raw dataset does not establish that they are invalid.
- `pnl` can be negative (1,691 rows), which is retained because a negative load-level P&L is a legitimate business outcome.
- 467 rows have `delivery_date < pickup_date`; 92 have `pickup_date < book_date`; 17 have `delivery_date < book_date`. These are flagged as source anomalies rather than silently discarded.
- `lane` consistently follows `Pickup City,ST -> Delivery City,ST` and is parsed into pickup/delivery city/state in staging.

## Modeling response

The source is preserved as a raw dbt seed. Transformations normalize types, parse the lane, deduplicate exact duplicate rows by `loadsmart_id`, and add explicit semantic fields such as `is_delivered` and `haul_type`.

The delivered-load definition used throughout the model is:

`load_was_cancelled = false AND delivered_at IS NOT NULL`

This avoids treating the source's date anomalies as evidence that a row is not delivered.

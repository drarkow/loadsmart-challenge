# Business definitions and assumptions

## Delivered load
A load is considered delivered when `load_was_cancelled = false` and `delivered_at` is not null.

## Last full month available
The raw delivery timestamps reach March 15, 2025, so February 2025 is the last complete calendar month before the final partial month. For Q1, "last full month available" is interpreted as **February 2025**, even though the month has zero delivered-load rows.

This is an explicit challenge assumption rather than an inferred business truth. An alternative interpretation is the latest full month with delivery activity (January 2025), which would produce 63 delivered loads. The result table records which interpretation is used.

## Lane
The source `lane` string is parsed as `Pickup City,ST -> Delivery City,ST`.

## Intrastate / interstate
`intrastate` means pickup and delivery states are the same; `interstate` means they differ.

## Grain
`fct_loads` has exactly one row per distinct `loadsmart_id`. The source contains four exact duplicate records, so staging retains one copy for each ID.

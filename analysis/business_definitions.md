# Business definitions and assumptions

## Delivered load
A load is considered delivered when `load_was_cancelled = false` and `delivered_at` is not null.

## Last full month available
The raw delivery timestamps reach March 15, 2025, with no February 2025 delivery rows. For the challenge's Q1, "last full month available" is interpreted as the latest month with delivery activity before the final partial month: **January 2025**.

This is an explicit challenge assumption rather than an inferred business truth. If a reviewer instead interprets the phrase as simply the calendar month immediately preceding March 2025, February 2025 would produce zero delivered rows.

## Lane
The source `lane` string is parsed as `Pickup City,ST -> Delivery City,ST`.

## Intrastate / interstate
`intrastate` means pickup and delivery states are the same; `interstate` means they differ.

## Grain
`fct_loads` has exactly one row per distinct `loadsmart_id`. The source contains four exact duplicate records, so staging retains one copy for each ID.

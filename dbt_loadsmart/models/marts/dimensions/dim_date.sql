with bounds as (
    select
        min(cast(coalesce(quote_at, booked_at, pickup_at, delivered_at) as date)) as min_date,
        max(cast(coalesce(delivered_at, pickup_at, booked_at, quote_at) as date)) as max_date
    from {{ ref('stg_loads') }}
),
calendar as (
    select unnest(generate_series(min_date, max_date, interval '1 day')) as date_day
    from bounds
)
select
    cast(date_day as date) as date_day,
    cast(extract(year from date_day) as integer) as year_number,
    cast(extract(month from date_day) as integer) as month_number,
    strftime(date_day, '%Y-%m') as year_month,
    strftime(date_day, '%B') as month_name,
    cast(extract(quarter from date_day) as integer) as quarter_number,
    cast(extract(dayofweek from date_day) as integer) as day_of_week,
    strftime(date_day, '%A') as day_name
from calendar

with lifecycle_dates as (
    select cast(quote_at as date) as date_day from {{ ref('stg_loads') }} where quote_at is not null
    union all
    select cast(booked_at as date) from {{ ref('stg_loads') }} where booked_at is not null
    union all
    select cast(sourced_at as date) from {{ ref('stg_loads') }} where sourced_at is not null
    union all
    select cast(pickup_at as date) from {{ ref('stg_loads') }} where pickup_at is not null
    union all
    select cast(delivered_at as date) from {{ ref('stg_loads') }} where delivered_at is not null
),
bounds as (
    select min(date_day) as min_date, max(date_day) as max_date
    from lifecycle_dates
),
calendar as (
    select cast(date_day as date) as date_day
    from bounds,
    generate_series(min_date, max_date, interval 1 day) as t(date_day)
)
select
    date_day,
    date_trunc('month', date_day)::date as month_start_date,
    extract(year from date_day)::integer as year,
    extract(quarter from date_day)::integer as quarter,
    extract(month from date_day)::integer as month,
    strftime(date_day, '%Y-%m') as year_month,
    extract(dayofweek from date_day)::integer as day_of_week,
    strftime(date_day, '%A') as day_name
from calendar

{{ config(severity="warn") }}

select
    loadsmart_id,
    pickup_city,
    pickup_state,
    delivery_city,
    delivery_state,
    mileage
from {{ ref('stg_loads') }}
where mileage = 0
  and lower(trim(pickup_city)) <> lower(trim(delivery_city))
{{ config(severity="warn") }}

select loadsmart_id, pickup_at, delivered_at
from {{ ref('stg_loads') }}
where delivered_at < pickup_at
  and is_delivered

select
    md5(lane) as lane_key,
    lane,
    pickup_city,
    pickup_state,
    delivery_city,
    delivery_state,
    haul_type
from (
    select distinct
        lane, pickup_city, pickup_state, delivery_city, delivery_state, haul_type
    from {{ ref('stg_loads') }}
)

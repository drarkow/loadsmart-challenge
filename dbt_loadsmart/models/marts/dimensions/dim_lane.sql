select
    md5(lane) as lane_key,
    lane,
    pickup_city,
    pickup_state,
    delivery_city,
    delivery_state,
    haul_type
from {{ ref('stg_loads') }}
group by 1,2,3,4,5,6,7

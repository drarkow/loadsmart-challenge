select f.loadsmart_id
from {{ ref('fct_loads') }} f
join {{ ref('dim_lane') }} l using (lane_key)
where f.haul_type <> l.haul_type

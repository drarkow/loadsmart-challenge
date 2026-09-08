select loadsmart_id, booked_at, delivered_at
from {{ ref('stg_loads') }}
where delivered_at < booked_at
  and is_delivered

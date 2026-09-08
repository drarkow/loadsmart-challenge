select loadsmart_id, lane
from {{ ref('stg_loads') }}
where regexp_matches(lane, '^[^,]+,[A-Za-z]{2} -> [^,]+,[A-Za-z]{2}$') = false

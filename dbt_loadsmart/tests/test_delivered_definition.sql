select loadsmart_id
from {{ ref('fct_loads') }}
where is_delivered <> (not load_was_cancelled and delivered_at is not null)

select loadsmart_id, count(*) as row_count
from {{ ref('stg_loads') }}
group by 1
having count(*) > 1

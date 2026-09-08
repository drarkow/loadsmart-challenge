select loadsmart_id, book_price, source_price
from {{ ref('stg_loads') }}
where book_price < 0 or source_price < 0

{{ config(severity="warn") }}

select
    loadsmart_id,
    book_price,
    load_was_cancelled,
    is_delivered
from {{ ref('stg_loads') }}
where book_price = 0
  and is_delivered